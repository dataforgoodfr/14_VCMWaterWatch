"""
Prefect workflow for loading water companies from the staging area.

Water companies are linked to the previously created distribution zones, by looking for a
distribution zone with the Water Company name as code prefix.
This should run after all zone data has been loaded.
"""

from pathlib import Path
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
import polars as pl

from pipelines.common import services
from pipelines.common.db_helper import DatabaseHelper


@task(name="load_water_companies", cache_policy=NO_CACHE)
def load_water_companies_task(data_path: Path) -> pl.DataFrame:
    """Load water companies from CSV file"""
    return pl.read_ndjson(data_path / "WaterCompany*.ndjson").with_columns(
        pl.lit("Water Company").alias("Type")
    )


@task(name="lookup_country", cache_policy=NO_CACHE)
def lookup_country_task(df: pl.DataFrame, db_helper: DatabaseHelper) -> pl.DataFrame:
    """Lookup the country for the actor.

    Populate Country_id field in the dataframe and filter out actors without a country.
    """
    countries_df = db_helper.load_all_records(
        table_name="Country", fields=["Code", "Id"]
    )
    countries_df = countries_df.rename({"Id": "Country_id"})
    return df.join(countries_df, left_on="CountryCode", right_on="Code", how="inner")


@task(name="lookup_distribution_zone", cache_policy=NO_CACHE)
def lookup_distribution_zone_task(
    df: pl.DataFrame, db_helper: DatabaseHelper
) -> pl.DataFrame:
    """Lookup the distribution zone for the actor.

    Populate DistributionZone_id field in the dataframe.
    Actors without a distribution zone are not filtered out.
    """
    zones_df = db_helper.load_all_records(
        table_name="DistributionZone", fields=["Code", "Id"]
    )
    zones_df = zones_df.rename({"Id": "DistributionZone_id"})
    return df.join(zones_df, left_on="Name", right_on="Code", how="left")


@task(name="insert_actors", cache_policy=NO_CACHE)
def insert_actors_task(df: pl.DataFrame, db_helper: DatabaseHelper) -> pl.DataFrame:
    """Insert actors into the database.
    Existing actors are not updated.

    Returns df with the Id column populated for all actors.
    """
    logger = get_run_logger()
    existing_df = db_helper.load_all_records(
        table_name="Actor", fields=["Name", "Id"], condition={"Type": "Water Company"}
    )
    df = df.join(existing_df, on="Name", how="left")
    insert_df = df.filter(pl.col("Id").is_null()).select(
        "Name", "Country_id", "Phone", "Email", "Website", "Description", "Source"
    )
    logger.info(f"Inserting {len(insert_df)} actors into the database")
    inserted_df = db_helper.insert_records(insert_df, table_name="Actor")
    # join the inserted actors back to the original dataframe, so we have the Id column
    df = df.with_columns(inserted_df["Id"])
    return df


@task(name="link_actors_to_distribution_zones", cache_policy=NO_CACHE)
def link_actors_to_distribution_zones_task(
    df: pl.DataFrame, db_helper: DatabaseHelper
) -> None:
    """Link actors to distribution zones (m-m link)"""
    db_helper.link_records(
        df,
        table_name="Actor",
        link_field_name="Distribution Zones",
        foreign_key_column="DistributionZone_id",
    )


@flow(name="load_water_companies", persist_result=False)
def load_water_companies(data_path: Path):
    db_helper = services.db_helper()

    df = load_water_companies_task(data_path)
    df = lookup_country_task(df, db_helper)
    df = lookup_distribution_zone_task(df, db_helper)
    df = insert_actors_task(df, db_helper)
    link_actors_to_distribution_zones_task(df, db_helper)


if __name__ == "__main__":
    load_water_companies(data_path=Path("data/staging"))
