"""
Prefect workflow for loading water companies from the staging area.

Water companies are linked to the previously created distribution zones, by looking for a
distribution zone with the Water Company name as code prefix.
This should run after all zone data has been loaded.

Expected input fields:
 - CountryCode (required)
 - Name (required)
 - Phone
 - Email
 - Website
 - Description
 - Source
"""

from pathlib import Path
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services, staging_db
from pipelines.common.db_helper import DatabaseHelper


@task(name="load_water_companies", cache_policy=NO_CACHE)
def load_water_companies_task(conn) -> list[dict]:
    """Load water companies from staging DB (all WaterCompany* tables)."""
    tables = conn.sql(
        "SELECT table_catalog, table_name FROM information_schema.tables "
        "WHERE table_name LIKE 'WaterCompany%'"
    ).fetchall()

    if not tables:
        return []

    queries = [f'SELECT * FROM {catalog}."{tn}"' for catalog, tn in tables]
    union_sql = " UNION ALL ".join(queries)
    records = conn.sql(union_sql).fetchdf().to_dict("records")

    for r in records:
        r["Type"] = "Water Company"
    return records


@task(name="lookup_country", cache_policy=NO_CACHE)
def lookup_country_task(records: list[dict], db_helper: DatabaseHelper) -> list[dict]:
    """Lookup country, populate Country_id, filter out actors without a country."""
    countries = db_helper.load_all_records(table_name="Country", fields=["Code", "Id"])
    code_to_id = {r["Code"]: r["Id"] for r in countries}

    result = []
    for r in records:
        country_id = code_to_id.get(r.get("CountryCode"))
        if country_id is not None:
            r = dict(r)
            r["Country_id"] = country_id
            result.append(r)
    return result


@task(name="lookup_distribution_zone", cache_policy=NO_CACHE)
def lookup_distribution_zone_task(
    records: list[dict], db_helper: DatabaseHelper
) -> list[dict]:
    """Lookup distribution zone, populate DistributionZone_id."""
    zones = db_helper.load_all_records(
        table_name="DistributionZone", fields=["Code", "Id"]
    )
    code_to_id = {r["Code"]: r["Id"] for r in zones}

    result = []
    for r in records:
        r = dict(r)
        r["DistributionZone_id"] = code_to_id.get(r.get("Name"))
        result.append(r)
    return result


@task(name="insert_actors", cache_policy=NO_CACHE)
def insert_actors_task(records: list[dict], db_helper: DatabaseHelper) -> list[dict]:
    """Insert actors into NocoDB. Existing actors are not updated."""
    logger = get_run_logger()
    existing = db_helper.load_all_records(
        table_name="Actor", fields=["Name", "Id"], condition={"Type": "Water Company"}
    )
    existing_map = {r["Name"]: r["Id"] for r in existing}

    # Separate new vs existing
    for r in records:
        r["Id"] = existing_map.get(r.get("Name"))

    to_insert = [
        {k: v for k, v in r.items() if k in ("Name", "Type", "Country_id", "Phone", "Email", "Website", "Description", "Source")}
        for r in records if r.get("Id") is None
    ]
    logger.info(f"Inserting {len(to_insert)} actors into the database")

    if to_insert:
        inserted = db_helper.insert_records(to_insert, table_name="Actor")
        # Map inserted IDs back by Name
        inserted_map = {r["Name"]: r["Id"] for r in inserted}
        for r in records:
            if r.get("Id") is None:
                r["Id"] = inserted_map.get(r.get("Name"))

    return records


@task(name="link_actors_to_distribution_zones", cache_policy=NO_CACHE)
def link_actors_to_distribution_zones_task(
    records: list[dict], db_helper: DatabaseHelper
) -> None:
    """Link actors to distribution zones (m-m link)."""
    db_helper.link_records(
        records,
        table_name="Actor",
        link_field_name="Distribution Zones",
        foreign_key_column="DistributionZone_id",
    )


@flow(name="load_water_companies", persist_result=False)
def load_water_companies(data_dir: Path):
    db_helper = services.db_helper()

    conn = staging_db.get_connection(data_dir)
    try:
        records = load_water_companies_task(conn)
    finally:
        conn.close()

    records = lookup_country_task(records, db_helper)
    records = lookup_distribution_zone_task(records, db_helper)
    records = insert_actors_task(records, db_helper)
    link_actors_to_distribution_zones_task(records, db_helper)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python load_water_companies.py <data_directory>")
        sys.exit(1)

    data_directory = Path(sys.argv[1])
    load_water_companies(data_dir=data_directory)
