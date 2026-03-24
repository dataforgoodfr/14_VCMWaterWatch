"""
Load data into the zone tables: Country, DistributionZone, Municipality.

Countries are loaded first as they have no parent.
Municipalities are linked to the countries as parent.
Distribution zones are linked to the countries as parent, and also have municipalities as children.

Expected input fields:
 - Code
 - Name
 - CountryCode (for DistributionZone and Municipality levels)
 - Municipalities (for DistributionZone level)
"""

from dataclasses import dataclass, field
from pathlib import Path
from prefect import flow, get_run_logger, task
from prefect.cache_policies import INPUTS, NO_CACHE

from pipelines.common import services, staging_db


@dataclass
class LevelConfig:
    table_name: str
    parent_level: str | None = None
    child_level: dict[str, str] = field(default_factory=dict)


LEVEL_CONFIGS = {
    "Country": LevelConfig(
        table_name="Country",
    ),
    "DistributionZone": LevelConfig(
        table_name="DistributionZone",
        parent_level="Country",
        child_level={"Municipality": "Municipalities"},
    ),
    "Municipality": LevelConfig(
        table_name="Municipality", parent_level="Country", child_level={}
    ),
}


def load_existing_data(table_name: str) -> list[dict]:
    """Load existing Code/Id data from NocoDB for this level."""
    if not table_name:
        return []
    db_helper = services.db_helper()
    return db_helper.load_all_records(table_name=table_name, fields=["Code", "Id"])


def load_source_data(conn, level: str) -> list[dict]:
    """Load source data from staging DB.

    Reads all tables matching the level name pattern and unions them.
    """
    # Get all tables in staging schema
    tables = conn.sql(
        "SELECT table_name FROM information_schema.tables WHERE table_catalog = 'staging'"
    ).fetchall()
    table_names = [t[0] for t in tables if t[0].startswith(level)]

    if not table_names:
        return []

    queries = [f"SELECT * FROM staging.\"{tn}\"" for tn in table_names]
    union_sql = " UNION ALL ".join(queries)
    return conn.sql(union_sql).fetchdf().to_dict("records")


def filter_existing_data(records: list[dict], table_name: str) -> list[dict]:
    """Filter out records that already exist in NocoDB."""
    existing = load_existing_data(table_name=table_name)
    existing_codes = {r["Code"] for r in existing}
    return [r for r in records if r.get("Code") not in existing_codes]


@task(name="lookup_parent", cache_policy=INPUTS)
def lookup_parent_task(records: list[dict], level_config: LevelConfig) -> list[dict]:
    """
    Lookup the parent data for the given level.
    Records without a parent are not included in the result.
    """
    parent_level = level_config.parent_level
    if not parent_level:
        return records
    parent_records = load_existing_data(table_name=parent_level)
    parent_map = {r["Code"]: r["Id"] for r in parent_records}

    result = []
    parent_field = f"{parent_level}Code"
    for r in records:
        parent_code = r.get(parent_field)
        if parent_code and parent_code in parent_map:
            r = dict(r)
            r[parent_level] = {"Id": parent_map[parent_code]}
            result.append(r)
    return result


@task(name="load_to_database", cache_policy=NO_CACHE)
def insert_records_task(records: list[dict], table_name: str) -> list[dict]:
    """Insert records into NocoDB."""
    db_helper = services.db_helper()
    logger = get_run_logger()
    logger.info(f"Inserting {len(records)} records")
    return db_helper.insert_records(records, table_name)


@task(name="lookup_children", cache_policy=INPUTS)
def lookup_children_task(
    records: list[dict], child_level: str, child_field_name: str
) -> list[dict]:
    """
    Lookup children IDs from NocoDB and replace code lists with ID lists.
    """
    child_records = load_existing_data(table_name=child_level)
    code_to_id = {r["Code"]: r["Id"] for r in child_records}

    result = []
    for r in records:
        r = dict(r)
        codes = r.get(child_field_name, []) or []
        r[child_field_name] = [code_to_id[c] for c in codes if c in code_to_id]
        result.append(r)
    return result


@task(name="link_children", cache_policy=INPUTS)
def link_children_task(
    records: list[dict], child_field_name: str, table_name: str
) -> None:
    """Create links in NocoDB between parent records and their children."""
    db_helper = services.db_helper()
    logger = get_run_logger()
    logger.info(f"Linking {len(records)} records to {child_field_name}")

    db_helper.link_records(
        records=records,
        table_name=table_name,
        link_field_name=child_field_name,
        foreign_key_column=child_field_name,
    )


@flow(name="load_zones")
def load_zones_flow(level: str, data_directory: Path) -> None:
    """
    Main flow to import processed data for a specific level.

    Args:
        level: Geographic level name (e.g., "Country", "DistributionZone", "Municipality")
        data_directory: Project root data directory (e.g. Path("data"))
    """
    if level not in LEVEL_CONFIGS:
        raise ValueError(
            f"Unknown level: {level}. Available levels: {list(LEVEL_CONFIGS.keys())}"
        )

    level_config = LEVEL_CONFIGS[level]

    conn = staging_db.get_connection(data_directory)
    try:
        source_records = load_source_data(conn, level)
    finally:
        conn.close()

    records = filter_existing_data(source_records, level_config.table_name)
    records = lookup_parent_task(records, level_config)

    # Exclude child link columns from insert — they contain codes, not IDs
    child_field_names = list(level_config.child_level.values()) if level_config.child_level else []
    if child_field_names:
        insert_records = [{k: v for k, v in r.items() if k not in child_field_names} for r in records]
    else:
        insert_records = records

    inserted = insert_records_task(insert_records, level_config.table_name)

    # Restore child columns for link_children (need codes for lookup)
    if child_field_names:
        code_to_children = {r["Code"]: {cf: r.get(cf) for cf in child_field_names} for r in source_records}
        for r in inserted:
            children_data = code_to_children.get(r.get("Code"), {})
            r.update(children_data)

    if level_config.child_level:
        for child_level, child_field_name in level_config.child_level.items():
            link_records = lookup_children_task(inserted, child_level, child_field_name)
            link_children_task(link_records, child_field_name, level_config.table_name)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python load_zones.py <level> <data_directory>")
        sys.exit(1)

    level = sys.argv[1]
    data_directory = Path(sys.argv[2])

    load_zones_flow(level=level, data_directory=data_directory)
