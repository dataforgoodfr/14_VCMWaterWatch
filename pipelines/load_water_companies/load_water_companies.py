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


@task(name="lookup_country", cache_policy=NO_CACHE)
def lookup_country_task(df: pl.DataFrame, db_helper: DatabaseHelper) -> pl.DataFrame:
    """Lookup the country for the actor.

    Populate Country_id field in the dataframe and filter out actors without a country.
    """
    countries_df = db_helper.load_all_records(
        table_name="Country", fields=["Code", "Id"]
    )
    countries_df = countries_df.rename({"Id": "Country_id"})
    return df.join(countries_df, left_on="Country", right_on="Code", how="inner")


@task(name="create_water_distribution_areas", cache_policy=NO_CACHE)
def create_water_distribution_areas_task(
    df: pl.DataFrame, db_helper: DatabaseHelper
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Initialize water distribution areas for water companies.
    Assume the zone name = the water company name.
    Update the DistributionZone_id field in the Actor dataframe.

    Args:
        df: actors dataframe (Name, Country, Municipalities)
        db_helper: Database helper instance

    Returns:
        modified actors dataframe, and distribution zones dataframe (including new and existing zones)
    """
    # Get the existing distribution zones
    zones_df = db_helper.load_all_records(
        table_name="DistributionZone", fields=["Code", "Id"]
    )
    zones_df = zones_df.rename({"Id": "DistributionZone_id"})
    # Join zones_df with actors to form a dataframe with DistributionZone_id
    df = df.join(zones_df, left_on="Name", right_on="Code", how="left")

    # For the actors without a Zone_id, create a new zone and add to zones_df.
    # Set the Country_id using the actor's Country_id.
    new_zones_df = df.filter(pl.col("DistributionZone_id").is_null()).select(
        pl.col("Name").alias("Code"),
        "Name",
        pl.col("Country_id"),
        pl.lit("Distribution").alias("Type"),
    )

    # load data from new_zones_df into the database
    logger = get_run_logger()
    logger.info(f"Inserting {len(new_zones_df)} new zones into the database")
    new_zones_df = (
        db_helper.insert_records(new_zones_df, table_name="DistributionZone")
        .select("Code", "Id")
        .rename({"Id": "DistributionZone_id"})
    )
    # join again, to add the newly inserted Zone_id to the actors dataframe
    df = df.join(
        new_zones_df, left_on="Name", right_on="Code", how="left"
    ).with_columns(
        pl.coalesce("DistributionZone_id", "DistributionZone_id_right").alias(
            "DistributionZone_id"
        )
    )
    zones_df = zones_df.vstack(new_zones_df)
    return df, zones_df


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
        "Name", "Country_id", "Phone", "Email", "Website", "Description"
    )
    logger.info(f"Inserting {len(insert_df)} actors into the database")
    inserted_df = db_helper.insert_records(insert_df, table_name="Actor")
    # join the inserted actors back to the original dataframe, so we have the Id column
    df = df.join(inserted_df.select("Id", "Name"), on="Name", how="left").with_columns(
        pl.coalesce("Id", "Id_right").alias("Id")
    )
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

def get_municipalities_by_distribution_zone_task(df: pl.DataFrame, db_helper: DatabaseHelper) -> pl.DataFrame:
    """
    Get existing municipalities and link with the "Municipalities" array in df to form a df with
    DistributionZone_id, Municipality_id, Geometry
    """
    raise NotImplementedError("Not implemented")
    # muni_df = db_helper.load_all_records(
    #     table_name="Municipality", fields=["Id", "Geometry", "Country_id"]
    # )
    # df = df.explode("Municipalities")

def link_zones_to_municipalities_task(zones_df: pl.DataFrame, muni_df: pl.DataFrame, db_helper: DatabaseHelper) -> None:
    """
    Given zones_df (DistributionZone_id) and muni_df (DistributionZone_id, Municipality_id, Geometry),
    link the municipalities to the zones, calculate the resulting area for each zone, and update the zones_df with the 
    geometry.
    """

@flow(name="load_water_companies", persist_result=False)
def load_water_companies(data_path: Path):
    db_helper = services.db_helper()

    df = load_water_companies_task(data_path)
    df = lookup_country_task(df, db_helper)
    df, zones_df = create_water_distribution_areas_task(df, db_helper)
    df = insert_actors_task(df, db_helper)
    # TODO link municipalities to distribution zones and calculate distribution zone geometry
    link_actors_to_distribution_zones_task(df, db_helper)
    muni_df = get_municipalities_by_distribution_zone_task(df, db_helper)
    link_zones_to_municipalities_task(zones_df, muni_df, db_helper)

if __name__ == "__main__":
    load_water_companies(data_path=Path("data/water_companies.csv"))
