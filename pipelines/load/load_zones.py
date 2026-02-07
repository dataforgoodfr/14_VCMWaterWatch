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
import polars as pl
from prefect import flow, get_run_logger, task
from prefect.cache_policies import INPUTS

from pipelines.common import services


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


def load_existing_data(table_name: str) -> pl.DataFrame:
    """
    Load existing data from the database for this level.

    Args:
        db_helper: Database helper instance
        table_name: Name of the table for this level

    Returns:
        Polars DataFrame with 'Code' and 'Id' columns
    """
    if not table_name:
        # No parent level, return empty dataframe with correct schema
        return pl.DataFrame(schema={"Code": pl.Utf8, "Id": pl.Int64})
    db_helper = services.db_helper()
    return db_helper.load_all_records(table_name=table_name, fields=["Code", "Id"])


def load_source_data(data_directory: Path, level: str) -> pl.DataFrame:
    """
    Load source data from the data directory.
    """
    return pl.read_ndjson(data_directory / f"{level}*.ndjson")


def filter_existing_data(df: pl.DataFrame, table_name: str) -> pl.DataFrame:
    """
    Filter out existing data from the database.
    """
    existing_df = load_existing_data(table_name=table_name)
    return df.join(existing_df, on="Code", how="anti")


@task(name="lookup_parent", cache_policy=INPUTS)
def lookup_parent_task(df: pl.DataFrame, level_config: LevelConfig) -> pl.DataFrame:
    """
    Lookup the parent data for the given level.
    Records without a parent are not included in the result.

    Returns:
        DataFrame with (parent_field) column added (parent ID)
    """
    parent_level = level_config.parent_level
    if not parent_level:
        return df
    parent_field_db = f"{parent_level}_id"
    parent_df = load_existing_data(table_name=parent_level).rename(
        {"Id": parent_field_db}
    )
    parent_field_df = f"{parent_level}Code"
    return df.join(parent_df, left_on=parent_field_df, right_on="Code", how="inner")


@task(name="load_to_database", cache_policy=INPUTS)
def insert_records_task(df: pl.DataFrame, table_name: str) -> pl.DataFrame:
    """
    Load the final DataFrame into the database.

    Args:
        db_helper: Database helper instance
        df: DataFrame to load
        table_name: Target table name

    Returns:
        DataFrame with the inserted records and their IDs
    """
    db_helper = services.db_helper()
    logger = get_run_logger()
    logger.info(f"Inserting {len(df)} records")
    df = db_helper.insert_records(df, table_name)
    return df


@task(name="lookup_children", cache_policy=INPUTS)
def lookup_children_task(
    df: pl.DataFrame, child_level: str, child_field_name: str
) -> pl.DataFrame:
    """
    Lookup the children data for the given level, using the child_field_name column in the source df
    as a list of codes.
    Replaces the child_field_name column with a new column with the children IDs (list of integers)
    """
    child_df = load_existing_data(table_name=child_level)

    # Explode the list column to create one row per child code
    df_exploded = df.select(["Id", child_field_name]).explode(child_field_name)

    # Join with child_df to get the child IDs, using 'inner' to skip any codes not found
    df_with_ids = df_exploded.join(
        child_df.select(["Code", "Id"]),
        left_on=child_field_name,
        right_on="Code",
        how="inner",
    ).select(
        [
            pl.col("Id"),  # Parent ID from df
            pl.col("Id_right").alias("child_id"),  # Child ID from child_df
        ]
    )

    # Group by parent Id and aggregate child IDs into a list
    df_children_ids = df_with_ids.group_by("Id").agg(
        pl.col("child_id").alias(child_field_name)
    )

    # Join back with original df to get all columns, replacing the codes with IDs
    return df.drop(child_field_name).join(
        df_children_ids,
        on="Id",
        how="left",  # Use left join to keep records even if no children found
    )


@task(name="link_children", cache_policy=INPUTS)
def link_children_task(
    df: pl.DataFrame, child_field_name: str, table_name: str
) -> None:
    """
    Create links in the database between parent records and their children.

    Args:
        df: DataFrame with 'Id' column and child_field_name column containing list of child IDs
        child_field_name: Name of the link field in the database (e.g., "Municipalities")
        level: Parent table name (e.g., "DistributionZone")
    """
    db_helper = services.db_helper()
    logger = get_run_logger()
    logger.info(f"Linking {len(df)} records to {child_field_name}")

    db_helper.link_records(
        df=df,
        table_name=table_name,
        link_field_name=child_field_name,
        foreign_key_column=child_field_name,
    )


@flow(name="load_zones")
def load_zones_flow(level: str, data_directory: Path) -> None:
    """
    Main flow to import processed GeoJSON data for a specific level.

    Args:
        level: Geographic level name (e.g., "Country", "DistributionZone", "Municipality")
        data_directory: Source directory for the data
    """
    # Get configuration for this level
    if level not in LEVEL_CONFIGS:
        raise ValueError(
            f"Unknown level: {level}. Available levels: {list(LEVEL_CONFIGS.keys())}"
        )

    level_config = LEVEL_CONFIGS[level]

    df_source = load_source_data(data_directory, level)
    # ideally we should do something where we get the existing id, for the data that is already there,
    # so that we can create new links without having to re-insert the data
    df = filter_existing_data(df_source, level_config.table_name)
    df = lookup_parent_task(df, level_config)
    df = insert_records_task(df, level_config.table_name)
    if level_config.child_level:
        for child_level, child_field_name in level_config.child_level.items():
            df_links = lookup_children_task(df, child_level, child_field_name)
            link_children_task(df_links, child_field_name, level_config.table_name)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python load_zones.py <level> <data_directory>")
        sys.exit(1)

    level = sys.argv[1]
    data_directory = Path(sys.argv[2])

    load_zones_flow(
        level=level,
        data_directory=data_directory,
    )
