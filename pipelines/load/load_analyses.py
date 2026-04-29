"""
Prefect workflow for loading France CVM analyses from staging into NocoDB.

Reads all ``staging.Analysis_*`` tables, deduplicates, then bulk-inserts into
the NocoDB ``Analysis`` table linked to ``DistributionZone`` and ``Municipality``.

Dedup key: ``(DistributionZoneCode, Date, round(CVMMeasure, 3), SourceRef)``
Natural key for upsert: ``Description = "{Source}: {SourceRef} @ {Date}"``

Volume note: O(100k–500k) rows expected.  Uses batch_size=500.
Rows whose DistributionZone isn't found in NocoDB are skipped and counted.
"""

from pathlib import Path
from typing import Optional

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services, staging_db

BATCH_SIZE = 500


@task(name="load_analyses_load_staging", cache_policy=NO_CACHE)
def load_staging_analyses(conn) -> list[dict]:
    """Load all Analysis_* tables from staging and return as list[dict]."""
    logger = get_run_logger()
    tables = conn.execute(
        "SELECT table_catalog, table_name FROM information_schema.tables "
        "WHERE table_catalog = 'staging' AND table_name LIKE 'Analysis_%'"
    ).fetchall()
    # Only load final per-country tables (e.g. Analysis_fr, Analysis_de).
    # Intermediate tables like Analysis_fr_dansmoneau have an extra "_" and
    # must be excluded to avoid processing rows ~3× (once from the merged
    # table plus once from each source table).
    tables = [(cat, tn) for cat, tn in tables if tn.count("_") == 1]

    if not tables:
        logger.warning("No Analysis_* tables found in staging")
        return []

    # Collect all columns across tables
    all_columns: dict[str, str] = {}
    for catalog, tn in tables:
        cols = conn.execute(
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_catalog = '{catalog}' AND table_name = '{tn}'"
        ).fetchall()
        for col_name, col_type in cols:
            if col_name not in all_columns:
                all_columns[col_name] = col_type

    col_names = sorted(all_columns.keys())
    queries = []
    for catalog, tn in tables:
        table_cols = {
            r[0]
            for r in conn.execute(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_catalog = '{catalog}' AND table_name = '{tn}'"
            ).fetchall()
        }
        select_parts = [
            f'"{c}"' if c in table_cols else f'NULL AS "{c}"' for c in col_names
        ]
        queries.append(
            f'SELECT {", ".join(select_parts)} FROM {catalog}."{tn}"'
        )

    union_sql = " UNION ALL ".join(queries)
    rows = conn.execute(union_sql).fetchdf().to_dict(orient="records")
    logger.info(f"Loaded {len(rows)} rows from Analysis_* staging tables")
    return rows


@task(name="load_analyses_prefetch_zones", cache_policy=NO_CACHE)
def prefetch_distribution_zones(db_helper, country_code: str = "FR") -> dict[str, str]:
    """Return a Code → Id map for all DistributionZone records for *country_code*."""
    logger = get_run_logger()
    records = db_helper.load_all_records(
        table_name="DistributionZone",
        fields=["Code", "Id"],
        condition={"CountryCode": country_code} if country_code else None,
    )
    code_to_id = {r["Code"]: r["Id"] for r in records if r.get("Code") and r.get("Id")}
    logger.info(f"Prefetched {len(code_to_id)} DistributionZone codes for {country_code}")
    return code_to_id


@task(name="load_analyses_prefetch_municipalities", cache_policy=NO_CACHE)
def prefetch_municipalities(db_helper, country_code: str = "FR") -> dict[str, str]:
    """Return a Code → Id map for all Municipality records for *country_code*."""
    logger = get_run_logger()
    records = db_helper.load_all_records(
        table_name="Municipality",
        fields=["Code", "Id"],
        condition={"CountryCode": country_code} if country_code else None,
    )
    code_to_id = {r["Code"]: r["Id"] for r in records if r.get("Code") and r.get("Id")}
    logger.info(f"Prefetched {len(code_to_id)} Municipality codes for {country_code}")
    return code_to_id


@task(name="load_analyses_prefetch_existing", cache_policy=NO_CACHE)
def prefetch_existing_analyses(db_helper) -> dict[str, str]:
    """Return a Description → Id map for all existing Analysis records."""
    logger = get_run_logger()
    records = db_helper.load_all_records(
        table_name="Analysis",
        fields=["Description", "Id"],
    )
    desc_to_id = {
        r["Description"]: r["Id"]
        for r in records
        if r.get("Description") and r.get("Id")
    }
    logger.info(f"Prefetched {len(desc_to_id)} existing Analysis records")
    return desc_to_id


def _make_description(row: dict) -> str:
    """Build a stable natural key / description string for an analysis row."""
    source = row.get("Source", "")
    source_ref = row.get("SourceRef", "")
    date = row.get("Date", "")
    return f"{source}: {source_ref} @ {date}"


def _round_safe(value, ndigits: int) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None


@task(name="load_analyses_prepare", cache_policy=NO_CACHE)
def prepare_records(
    rows: list[dict],
    zone_map: dict[str, str],
    muni_map: dict[str, str],
    existing_map: dict[str, str],
) -> tuple[list[dict], list[dict], int]:
    """Split rows into to-insert and to-update lists; return skipped count.

    Returns:
        (to_insert, to_update, skipped_count)
    """
    logger = get_run_logger()
    to_insert: list[dict] = []
    to_update: list[dict] = []
    skipped = 0
    seen_keys: set[tuple] = set()

    for row in rows:
        zone_code = row.get("DistributionZoneCode")
        if not zone_code or zone_code not in zone_map:
            skipped += 1
            continue

        zone_id = zone_map[zone_code]
        muni_code = row.get("MunicipalityCode")
        muni_id = muni_map.get(muni_code) if muni_code else None

        # Dedup key
        dedup_key = (
            zone_code,
            str(row.get("Date", "")),
            _round_safe(row.get("CVMMeasure"), 3),
            row.get("SourceRef", ""),
        )
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        description = _make_description(row)
        record = {
            "Description": description,
            "CVMMeasure": _round_safe(row.get("CVMMeasure"), 6),
            "Date": str(row.get("Date", "")),
            "Source": row.get("Source", ""),
            "_zone_id": zone_id,
            "_muni_id": muni_id,
        }

        if description in existing_map:
            record["Id"] = existing_map[description]
            to_update.append(record)
        else:
            to_insert.append(record)

    logger.info(
        f"prepare_records: {len(to_insert)} to insert, "
        f"{len(to_update)} to update, {skipped} skipped"
    )
    return to_insert, to_update, skipped


@task(name="load_analyses_insert", cache_policy=NO_CACHE)
def insert_analyses(
    records: list[dict],
    db_helper,
) -> list[dict]:
    """Bulk-insert Analysis records and return them with their NocoDB Ids."""
    if not records:
        return []
    logger = get_run_logger()
    logger.info(f"Inserting {len(records)} Analysis records …")

    # Strip internal helper keys before inserting
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    inserted = db_helper.insert_records(clean, table_name="Analysis", batch_size=BATCH_SIZE)

    # Re-attach helper keys
    for orig, ins in zip(records, inserted):
        orig["Id"] = ins.get("Id")

    logger.info(f"Inserted {len(inserted)} Analysis records")
    return records


@task(name="load_analyses_update", cache_policy=NO_CACHE)
def update_analyses(
    records: list[dict],
    db_helper,
) -> None:
    """Bulk-update existing Analysis records."""
    if not records:
        return
    logger = get_run_logger()
    logger.info(f"Updating {len(records)} Analysis records …")
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in records]
    db_helper.update_records(clean, table_name="Analysis", batch_size=BATCH_SIZE)
    logger.info(f"Updated {len(records)} Analysis records")


@task(name="load_analyses_link_zones", cache_policy=NO_CACHE)
def link_to_distribution_zones(records: list[dict], db_helper) -> None:
    """Link inserted Analysis records to their DistributionZone."""
    if not records:
        return
    logger = get_run_logger()
    # Build a flat list with Id + DistributionZoneId
    to_link = [
        {"Id": r["Id"], "DistributionZoneId": r["_zone_id"]}
        for r in records
        if r.get("Id") and r.get("_zone_id")
    ]
    if not to_link:
        return
    logger.info(f"Linking {len(to_link)} analyses to DistributionZone …")
    db_helper.link_records(
        to_link,
        table_name="Analysis",
        link_field_name="DistributionZone",
        foreign_key_column="DistributionZoneId",
    )


@task(name="load_analyses_link_municipalities", cache_policy=NO_CACHE)
def link_to_municipalities(records: list[dict], db_helper) -> None:
    """Link inserted Analysis records to their Municipality."""
    if not records:
        return
    logger = get_run_logger()
    to_link = [
        {"Id": r["Id"], "MunicipalityId": r["_muni_id"]}
        for r in records
        if r.get("Id") and r.get("_muni_id")
    ]
    if not to_link:
        return
    logger.info(f"Linking {len(to_link)} analyses to Municipality …")
    db_helper.link_records(
        to_link,
        table_name="Analysis",
        link_field_name="Municipality",
        foreign_key_column="MunicipalityId",
    )


@flow(name="load_analyses", persist_result=False)
def load_analyses(data_directory: Path = Path("data")) -> None:
    """Load all Analysis_* staging tables into NocoDB Analysis table."""
    logger = get_run_logger()
    db = services.db_helper()
    conn = staging_db.get_connection(data_directory)
    try:
        rows = load_staging_analyses(conn)
    finally:
        conn.close()

    if not rows:
        logger.info("No analysis rows to load")
        return

    zone_map = prefetch_distribution_zones(db)
    muni_map = prefetch_municipalities(db)
    existing_map = prefetch_existing_analyses(db)

    to_insert, to_update, skipped = prepare_records(rows, zone_map, muni_map, existing_map)

    inserted = insert_analyses(to_insert, db)
    update_analyses(to_update, db)

    link_to_distribution_zones(inserted, db)
    link_to_municipalities(inserted, db)

    logger.info(
        f"load_analyses complete: {len(inserted)} inserted, "
        f"{len(to_update)} updated, {skipped} skipped"
    )


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    load_analyses(data_directory)
