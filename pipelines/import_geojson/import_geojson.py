"""Prefect workflow for importing GeoJSON data."""

import json
from pathlib import Path
from typing import Optional
import polars as pl
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services
from pipelines.common.db_helper import DatabaseHelper
from .config import LEVEL_CONFIGS, LevelConfig, EUROPEAN_COUNTRIES


@task(name="load_existing_data", cache_policy=NO_CACHE)
def load_existing_data_task(db_helper: DatabaseHelper, level_name: str) -> pl.DataFrame:
    """
    Load existing data from the database for this level.

    Args:
        db_helper: Database helper instance
        table_name: Name of the table for this level

    Returns:
        Polars DataFrame with 'Code' and 'Id' columns
    """
    if not level_name:
        # No parent level, return empty dataframe with correct schema
        return pl.DataFrame(schema={"Code": pl.Utf8, "Id": pl.Int64})
    condition = {"Type": level_name}
    return db_helper.load_all_records(
        table_name="Zone", fields=["Code", "Id"], condition=condition
    )


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


@task(name="lookup_parent", cache_policy=NO_CACHE)
def lookup_parent_task(
    transformed_df: pl.DataFrame, reference_df: pl.DataFrame
) -> pl.DataFrame:
    """
    Use reference data to look up parent IDs.

    Args:
        transformed_df: DataFrame with ParentCode column
        reference_df: DataFrame with code and id columns for parent lookup

    Returns:
        DataFrame with Area_id column added (parent ID)
    """
    if reference_df.is_empty():
        # No parent level, add null Parent column
        return transformed_df.with_columns(
            [pl.lit(None).cast(pl.Int64).alias("Area_id")]
        )

    # Join to get parent ID
    result = transformed_df.join(
        reference_df, left_on="ParentCode", right_on="Code", how="inner"
    ).select(["Name", "Code", "Geometry", pl.col("Id").alias("Area_id")])

    return result


@task(name="load_to_database", cache_policy=NO_CACHE)
def load_to_database_task(
    db_helper: DatabaseHelper, df: pl.DataFrame, table_name: str
) -> None:
    """
    Load the final DataFrame into the database.

    Args:
        db_helper: Database helper instance
        df: DataFrame to load
        table_name: Target table name
    """
    logger = get_run_logger()
    logger.info(f"Inserting {len(df)} records")
    db_helper.insert_records(df, table_name)


@flow(name="import_geojson_level", persist_result=False)
def import_geojson_level_flow(
    level: str, geojson_file_path: Path, data_directory: Optional[Path] = None
) -> None:
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

    # Initialize database helper
    db_helper = services.db_helper()

    # Determine GeoJSON file path
    if data_directory and geojson_file_path.is_dir():
        # Look for file with suffix matching the level config
        pattern = f"*{level_config.file_suffix}.geojson"
        matching_files = list(data_directory.glob(pattern))
        if not matching_files:
            raise FileNotFoundError(
                f"No GeoJSON file found matching pattern: {pattern}"
            )
        geojson_file = matching_files[0]
    elif geojson_file_path.is_file():
        geojson_file = geojson_file_path
    else:
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_file_path}")

    # Get parent table name if parent level exists
    parent_level = level_config.parent_level

    existing_df = load_existing_data_task(
        db_helper=db_helper,
        level_name=level,
    )

    transformed_df = transform_geojson_task(
        geojson_file_path=geojson_file, level_config=level_config
    )
    if level == "Country":
        transformed_df = transformed_df.filter(pl.col("Code").is_in(EUROPEAN_COUNTRIES.keys()))

    reference_df = load_existing_data_task(
        db_helper=db_helper,
        level_name=parent_level or "",
    )

    final_df = lookup_parent_task(
        transformed_df=transformed_df, reference_df=reference_df
    )
    final_df = final_df.with_columns(pl.lit(level).alias("Type"))

    # Filter out records that already exist
    if not existing_df.is_empty():
        existing_codes = existing_df["Code"].to_list()
        final_df = final_df.filter(~pl.col("Code").is_in(existing_codes))

    # Task 5: Load to database
    if not final_df.is_empty():
        load_to_database_task(
            db_helper=db_helper,
            df=final_df.select(["Code", "Name", "Geometry", "Area_id", "Type"]),
            table_name="Zone",
        )
    else:
        print(f"No new records to import for level {level}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python workflow.py <level> <geojson_file_path>")
        sys.exit(1)

    level = sys.argv[1]
    geojson_path = Path(sys.argv[2])

    import_geojson_level_flow(
        level=level,
        geojson_file_path=geojson_path,
    )
