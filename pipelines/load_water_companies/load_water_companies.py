"""Prefect workflow for loading water companies from CSV"""

from pathlib import Path
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
import polars as pl

from pipelines.common import services
from pipelines.common.db_helper import DatabaseHelper


@task(name="load_water_companies", cache_policy=NO_CACHE)
def load_water_companies_task(csv_file: Path) -> pl.DataFrame:
    """Load water companies from CSV file"""
    return pl.read_csv(csv_file).with_columns(pl.lit("Water Company").alias("Type"))


@task(name="filter_existing_actors", cache_policy=NO_CACHE)
def filter_existing_actors_task(
    df: pl.DataFrame, db_helper: DatabaseHelper
) -> pl.DataFrame:
    """Filter out existing actors from the dataframe"""
    existing_df = db_helper.load_all_records(table_name="Actor", fields=["Name"])
    return df.join(existing_df, on="Name", how="anti")


@task(name="create_water_distribution_areas", cache_policy=NO_CACHE)
def create_water_distribution_areas_task(
    df: pl.DataFrame, db_helper: DatabaseHelper
) -> pl.DataFrame:
    """
    Initialize water distribution areas for water companies.
    Assume the zone name = the water company name.
    Update the Zone_id field in the Actor dataframe.

    Args:
        df: actors dataframe (Name, Country, Municipalities)
        db_helper: Database helper instance

    Returns:
        modified actors dataframe
    """
    # Create water distribution areas for each water company
    zones_df = db_helper.load_all_records(
        table_name="Zone", fields=["Code", "Id"], condition={"Type": "Distribution"}
    )
    zones_df = zones_df.rename({"Id": "Zone_id"})
    # Join zones_df with actors to form a dataframe with Zone_id
    df = df.join(zones_df, left_on="Name", right_on="Code", how="left")

    # For the actors without a Zone_id, create a new zone and add to zones_df.
    # Set the Area_id using the actor's Country.
    countries_df = db_helper.load_all_records(
        table_name="Zone", fields=["Code", "Id"], condition={"Type": "Country"}
    ).rename({"Id": "Area_id"})
    new_zones_df = (
        df.filter(pl.col("Zone_id").is_null())
        .select(
            pl.col("Name").alias("Code"),
            "Name",
            pl.col("Country"),
            pl.lit("Distribution").alias("Type"),
        )
        .join(countries_df, left_on="Country", right_on="Code", how="inner")
    )

    # load data from new_zones_df into the database
    logger = get_run_logger()
    logger.info(f"Inserting {len(new_zones_df)} new zones into the database")
    new_zones_df = (
        db_helper.insert_records(new_zones_df, table_name="Zone")
        .select("Code", "Id")
        .rename({"Id": "Zone_id"})
    )
    # join again, to add the newly inserted Zone_id to the actors dataframe
    df = df.join(
        new_zones_df, left_on="Name", right_on="Code", how="left"
    ).with_columns(pl.coalesce("Zone_id", "Zone_id_right").alias("Zone_id"))
    return df


@task(name="insert_actors", cache_policy=NO_CACHE)
def insert_actors_task(df: pl.DataFrame, db_helper: DatabaseHelper) -> None:
    """Insert actors into the database"""
    logger = get_run_logger()
    logger.info(f"Inserting {len(df)} actors into the database")
    df = db_helper.insert_records(df, table_name="Actor")
    db_helper.link_records(df, table_name="Actor", link_field_name="Zones", foreign_key_column="Zone_id")


@flow(name="load_water_companies", persist_result=False)
def load_water_companies(data: Path):
    db_helper = services.db_helper()

    df = load_water_companies_task(data)
    df = filter_existing_actors_task(df, db_helper)
    df = create_water_distribution_areas_task(df, db_helper)
    insert_actors_task(df, db_helper)


if __name__ == "__main__":
    load_water_companies(data=Path("data/water_companies.csv"))
