"""
Prefect task for deducing the VCM Level per French DistributionZone.

Reads staging.Analysis_fr (produced by fr_build.py) and computes:
  - 'High'    if any sample > 0.5 µg/L
  - 'Low'     if ≥1 sample present and none exceed 0.5
  - 'Unknown' if no samples exist for the zone

Then bulk-updates the corresponding DistributionZone records in NocoDB.
Zones with no samples in staging get 'Unknown' (idempotent reset).
"""

from pathlib import Path

import duckdb
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services, staging_db

# CVM threshold in µg/L above which a zone is classified as High
CVM_THRESHOLD_UGL = 0.5

# Map internal level names to NocoDB SingleSelect option titles
_LEVEL_TO_NOCO = {
    "High": "> 0.5 mcg/L",
    "Low": "< 0.5 mcg/L",
    "Unknown": "Unknown",
}

@task(name="deduce_vcm_level_compute", cache_policy=NO_CACHE)
def compute_vcm_levels(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Compute VCM Level per DistributionZone from staging.Analysis_fr.

    Returns a dict mapping DistributionZoneCode → VCM Level string.
    """
    logger = get_run_logger()

    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_catalog = 'staging' AND table_name = 'Analysis_fr'"
    ).fetchall()

    if not tables:
        logger.warning("staging.Analysis_fr not found; no VCM levels computed")
        return {}

    rows = conn.execute(f"""
        SELECT
            "DistributionZoneCode" AS code,
            CASE
                WHEN max("CVMMeasure") > {CVM_THRESHOLD_UGL} THEN 'High'
                WHEN count(*) > 0            THEN 'Low'
                ELSE                              'Unknown'
            END AS level
        FROM staging."Analysis_fr"
        GROUP BY "DistributionZoneCode"
    """).fetchall()

    level_map = {r[0]: r[1] for r in rows if r[0]}
    logger.info(
        f"VCM levels computed: "
        f"High={sum(1 for v in level_map.values() if v == 'High')}, "
        f"Low={sum(1 for v in level_map.values() if v == 'Low')}, "
        f"zones={len(level_map)}"
    )
    return level_map


@task(name="deduce_vcm_level_fetch_zones", cache_policy=NO_CACHE)
def fetch_fr_distribution_zones(db_helper) -> list[dict]:
    """Fetch all French DistributionZone records (Id, Code, VCM Level)."""
    logger = get_run_logger()
    records = db_helper.load_all_records(
        table_name="DistributionZone",
        fields=["Id", "Code", "VCM Level"],
    )
    logger.info(f"Fetched {len(records)} French DistributionZone records")
    return records


@task(name="deduce_vcm_level_apply", cache_policy=NO_CACHE)
def apply_vcm_levels(
    zones: list[dict],
    level_map: dict[str, str],
) -> list[dict]:
    """Build the update payload for NocoDB.

    Zones with no entry in *level_map* are set to 'Unknown'.
    """
    updates = []
    for zone in zones:
        code = zone.get("Code")
        zone_id = zone.get("Id")
        if not zone_id:
            continue
        new_level = _LEVEL_TO_NOCO.get(level_map.get(code, "Unknown"), "Unknown")
        current_level = zone.get("VCM Level")
        if current_level != new_level:
            updates.append({"Id": zone_id, "VCM Level": new_level})
    return updates


@task(name="deduce_vcm_level_update", cache_policy=NO_CACHE)
def update_vcm_levels(updates: list[dict], db_helper) -> None:
    """Bulk-update VCM Level in NocoDB DistributionZone table."""
    logger = get_run_logger()
    if not updates:
        logger.info("No VCM Level updates needed")
        return
    logger.info(f"Updating VCM Level for {len(updates)} zones …")
    db_helper.update_records(updates, table_name="DistributionZone", batch_size=10)
    logger.info("VCM Level update complete")


@flow(name="deduce_vcm_level", persist_result=False)
def deduce_vcm_level(data_directory: Path = Path("data")) -> None:
    """Compute and write VCM Level for all French DistributionZones."""
    logger = get_run_logger()
    conn = staging_db.get_connection(data_directory)
    try:
        level_map = compute_vcm_levels(conn)
    finally:
        conn.close()

    if not level_map:
        logger.info("No VCM levels to apply")
        return

    db = services.db_helper()
    zones = fetch_fr_distribution_zones(db)
    updates = apply_vcm_levels(zones, level_map)
    update_vcm_levels(updates, db)

    logger.info(
        f"deduce_vcm_level complete: {len(updates)} zones updated out of {len(zones)}"
    )


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    deduce_vcm_level(data_directory)
