"""Prefect workflow for importing GeoJSON data."""

import json
from pathlib import Path
import polars as pl
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from .config import LEVEL_CONFIGS, LevelConfig, EUROPEAN_COUNTRIES


@task(name="transform_geojson", cache_policy=NO_CACHE)
def transform_geojson_task(
    geojson_file_path: Path, level_config: LevelConfig
) -> pl.DataFrame:
    """
    Transform GeoJSON data into a Polars DataFrame.

    Args:
        geojson_file_path: Path to the GeoJSON file
        level_config: Configuration for the current level

    Returns:
        Polars DataFrame with Name, Code, Geometry, and ParentCode columns
    """
    # Read GeoJSON file
    with open(geojson_file_path, "r") as f:
        geojson_data = json.load(f)

    # Validate it's a FeatureCollection
    if geojson_data.get("type") != "FeatureCollection":
        raise ValueError(f"Expected FeatureCollection, got {geojson_data.get('type')}")

    features = geojson_data.get("features", [])

    # Extract data from each feature
    rows = []
    for feature in features:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Map properties according to configuration
        title = properties.get(level_config.title_property, "")
        code = properties.get(level_config.code_property, "")

        # Get parent code if parent level exists
        parent_code = None
        if level_config.parent_level:
            parent_code_property = level_config.parent_property
            parent_code = properties.get(parent_code_property)

        rows.append(
            {
                "Name": title,
                "Code": code,
                "Geometry": json.dumps(geometry),  # Store geometry as JSON string
                "ParentCode": parent_code,
            }
        )

    return pl.DataFrame(rows)


@task(name="lookup_country", cache_policy=NO_CACHE)
def lookup_country_task(df: pl.DataFrame) -> pl.DataFrame:
    """
    Lookup the country for the actor.
    (right now we just alias the ParentCode to CountryCode)
    """
    return df.with_columns(pl.col("ParentCode").alias("CountryCode"))


@flow(name="import_geojson", persist_result=False)
def import_geojson_flow(level: str, source_dir: Path, dest_dir: Path) -> None:
    """
    Main flow to import GeoJSON data for a specific level.

    Args:
        level: Geographic level name (e.g., "Country", "Region", "PostalCode")
        geojson_file_path: Path to the GeoJSON file (or directory containing files)
        api_token: NocoDB API token for authentication
        data_directory: Optional directory to search for GeoJSON files
    """
    # Get configuration for this level
    if level not in LEVEL_CONFIGS:
        raise ValueError(
            f"Unknown level: {level}. Available levels: {list(LEVEL_CONFIGS.keys())}"
        )

    level_config = LEVEL_CONFIGS[level]

    # Determine GeoJSON file path
    pattern = f"*{level_config.file_suffix}.geojson"
    geojson_files = list(source_dir.glob(pattern))
    if not geojson_files:
        raise FileNotFoundError(f"No GeoJSON file found matching pattern: {pattern}")

    transformed_df = pl.concat(
        [
            transform_geojson_task(
                geojson_file_path=geojson_file, level_config=level_config
            )
            for geojson_file in geojson_files
        ]
    )
    if level != "Country":
        # get CountryCode
        transformed_df = lookup_country_task(transformed_df)
        transformed_df = transformed_df.filter(
            pl.col("CountryCode").is_in(EUROPEAN_COUNTRIES.keys())
        )
    else:
        transformed_df = transformed_df.filter(
            pl.col("Code").is_in(EUROPEAN_COUNTRIES.keys())
        )

    transformed_df.write_ndjson(dest_dir / f"{level}.ndjson")


@flow(name="import_all_geojson", persist_result=False)
def import_all_geojson_flow(data_directory: Path) -> None:
    """
    Orchestrate the import of all GeoJSON data with proper dependencies.
    Country data must be imported before Municipality data.
    """
    logger = get_run_logger()
    source_dir = data_directory / "raw"
    dest_dir = data_directory / "staging"

    # Import Country data first
    logger.info("Starting Country import...")
    import_geojson_flow(level="Country", source_dir=source_dir, dest_dir=dest_dir)

    # Import Municipality data after Country (implicit dependency)
    logger.info("Starting Municipality import...")
    import_geojson_flow(
        level="Municipality",
        source_dir=source_dir,
        dest_dir=dest_dir,
    )

    logger.info("All imports completed successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m extract.geojson <data_directory>")
        sys.exit(1)

    data_directory = Path(sys.argv[1])

    import_all_geojson_flow(
        data_directory=data_directory,
    )
