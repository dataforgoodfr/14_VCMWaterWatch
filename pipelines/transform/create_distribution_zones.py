"""
Prefect workflow for creating distribution zones based on water companies and municipalities.
Right now this assume a 1:1 relationship between water companies and distribution zones, but
the database allows for a 1:M relationship in case we can gather more specific information about
the water company individual distribution zones.
"""

from pathlib import Path
import polars as pl
from prefect import flow, task
from prefect.cache_policies import NO_CACHE


@task(name="create_distribution_zones", cache_policy=NO_CACHE)
def create_distribution_zones_task(water_companies_df: pl.DataFrame) -> pl.DataFrame:
    """
    Create distribution zones based on water companies and municipalities.
    Return a dataframe with the following fields:
    - Code: str (from water company name)
    - Name: str (from water company name)
    - CountryCode: str (from water company DF)
    - Municipalities: list of municipality codes
    - Type: "Distribution" (literal)
    """
    return water_companies_df.select(
        pl.col("Name").alias("Code"),
        pl.col("Name"),
        pl.col("CountryCode"),
        # we could have this be a list of list, if we want to support the 1:M relationship between
        # water companies and distribution zones, explode() it here and use a counter for the code.
        pl.col("Municipalities"),
        pl.lit("Distribution").alias("Type"),
    )


@flow(name="create_distribution_zones", persist_result=False)
def create_distribution_zones_flow(data_directory: Path):
    """
    Create distribution zones based on water companies and municipalities.
    """
    water_companies_df = pl.read_ndjson(data_directory / "raw" / "WaterCompany*.ndjson")
    distribution_zones_df = create_distribution_zones_task(water_companies_df)
    distribution_zones_df.write_ndjson(
        data_directory / "staging" / "DistributionZone_from_water_companies.ndjson"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_distribution_zones.py <data_directory>")
        sys.exit(1)

    data_directory = Path(sys.argv[1])
    create_distribution_zones_flow(data_directory)
