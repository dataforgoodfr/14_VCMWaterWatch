"""
Prefect workflow for creating distribution zones based on water companies and municipalities.
"""

import json
from pathlib import Path
import polars as pl
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from shapely import unary_union
from shapely.geometry import shape



@task(name="merge_municipalities_geometries", cache_policy=NO_CACHE)
def merge_municipalities_geometries_task(
    water_companies_df: pl.DataFrame, municipalities_df: pl.DataFrame
) -> pl.DataFrame:
    """
    Merge the geometries of the municipalities into a single geometry for each water company.
    Return water_companies_df with an additional column "Geometry" containing the merged geometry.
    """
    geometries = []
    for row in water_companies_df.iter_rows(named=True):
        muni_df = municipalities_df.filter(
            (pl.col("CountryCode") == row["CountryCode"])
            & (pl.col("Code").is_in(row["Municipalities"]))
        )

        # Extract all geometries from municipalities
        muni_geometries = []
        for muni in muni_df.iter_rows(named=True):
            geom_json = json.loads(muni["Geometry"])
            muni_geometries.append(shape(geom_json))

        if muni_geometries:
            merged_geometry = unary_union(muni_geometries)
            geometries.append(json.dumps(merged_geometry.__geo_interface__))
        else:
            geometries.append(None)
    return water_companies_df.with_columns(
        pl.Series(name="Geometry", values=geometries)
    )


@task(name="create_distribution_zones", cache_policy=NO_CACHE)
def create_distribution_zones_task(water_companies_df: pl.DataFrame) -> pl.DataFrame:
    """
    Create distribution zones based on water companies and municipalities.
    Return a dataframe with the following fields:
    - Code: str (from water company name)
    - Name: str (from water company name)
    - CountryCode: str (from water company DF)
    - Geometry: GeoJSON
    - Municipalities: list of municipality codes
    - Type: "Distribution" (literal)
    """
    return water_companies_df.select(
        pl.col("Name").alias("Code"),
        pl.col("Name"),
        pl.col("CountryCode"),
        pl.col("Geometry"),
        pl.col("Municipalities"),
        pl.lit("Distribution").alias("Type"),
    )


@flow(name="create_distribution_zones", persist_result=False)
def create_distribution_zones_flow(data_directory: Path):
    """
    Create distribution zones based on water companies and municipalities.
    """
    water_companies_df = pl.read_ndjson(
        data_directory / "staging" / "WaterCompany*.ndjson"
    )
    municipalities_df = pl.read_ndjson(
        data_directory / "staging" / "Municipality.ndjson"
    )
    water_companies_df = merge_municipalities_geometries_task(
        water_companies_df, municipalities_df
    )
    distribution_zones_df = create_distribution_zones_task(water_companies_df)
    distribution_zones_df.write_ndjson(
        data_directory / "staging" / "DistributionZone_from_water_companies.ndjson"
    )


if __name__ == "__main__":
    create_distribution_zones_flow(Path("data"))
