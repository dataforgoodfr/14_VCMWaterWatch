"""
Prefect workflow for transforming GeoJSON data into the zone objects (Country + Municipality)
"""

import json
from pathlib import Path
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db
from pipelines.transform.config import LEVEL_CONFIGS, LevelConfig, EUROPEAN_COUNTRIES


@task(name="transform_geojson", cache_policy=NO_CACHE)
def transform_geojson_task(
    geojson_file_path: Path, level_config: LevelConfig
) -> list[dict]:
    """
    Transform GeoJSON data into a list of dicts.
    """
    with open(geojson_file_path, "r") as f:
        geojson_data = json.load(f)

    if geojson_data.get("type") != "FeatureCollection":
        raise ValueError(f"Expected FeatureCollection, got {geojson_data.get('type')}")

    features = geojson_data.get("features", [])

    rows = []
    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        title = properties.get(level_config.title_property, "")
        code = properties.get(level_config.code_property, "")

        parent_code = None
        if level_config.parent_level:
            parent_code = properties.get(level_config.parent_property)

        rows.append(
            {
                "Name": title,
                "Code": code,
                "Geometry": json.dumps(geometry),
                "ParentCode": parent_code,
            }
        )

    return rows


@task(name="lookup_country", cache_policy=NO_CACHE)
def lookup_country_task(records: list[dict]) -> list[dict]:
    """Alias ParentCode to CountryCode."""
    for r in records:
        r["CountryCode"] = r.get("ParentCode")
    return records


@flow(name="import_geojson", persist_result=False)
def import_geojson_flow(level: str, source_dir: Path, conn=None) -> None:
    """
    Main flow to import GeoJSON data for a specific level.
    """
    if level not in LEVEL_CONFIGS:
        raise ValueError(
            f"Unknown level: {level}. Available levels: {list(LEVEL_CONFIGS.keys())}"
        )

    level_config = LEVEL_CONFIGS[level]

    pattern = f"*{level_config.file_suffix}.geojson"
    geojson_files = list(source_dir.glob(pattern))
    if not geojson_files:
        raise FileNotFoundError(f"No GeoJSON file found matching pattern: {pattern}")

    all_rows: list[dict] = []
    for geojson_file in geojson_files:
        rows = transform_geojson_task(
            geojson_file_path=geojson_file, level_config=level_config
        )
        all_rows.extend(rows)

    if level != "Country":
        all_rows = lookup_country_task(all_rows)
        all_rows = [r for r in all_rows if r.get("CountryCode") in EUROPEAN_COUNTRIES]
    else:
        all_rows = [r for r in all_rows if r.get("Code") in EUROPEAN_COUNTRIES]

    if conn is not None:
        staging_db.write_table(conn, level, all_rows, schema="staging")
    else:
        # Fallback: caller didn't pass conn — shouldn't happen in normal flow
        raise ValueError("conn is required for import_geojson_flow")


@flow(name="import_all_geojson", persist_result=False)
def import_all_geojson_flow(data_directory: Path) -> None:
    """
    Orchestrate the import of all GeoJSON data with proper dependencies.
    """
    logger = get_run_logger()
    source_dir = data_directory / "raw"

    conn = staging_db.get_connection(data_directory)
    try:
        logger.info("Starting Country import...")
        import_geojson_flow(level="Country", source_dir=source_dir, conn=conn)

        logger.info("Starting Municipality import...")
        import_geojson_flow(level="Municipality", source_dir=source_dir, conn=conn)

        logger.info("All imports completed successfully!")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m transform.geojson <data_directory>")
        sys.exit(1)

    data_directory = Path(sys.argv[1])
    import_all_geojson_flow(data_directory=data_directory)
