"""
Prefect workflow for calculating the geometry of distribution zones that are missing it, based on the
covered municipalities.
"""

import json
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from shapely import unary_union
from shapely.geometry import shape
from ..common import services
import polars as pl


@task(name="merge_municipalities_geometries", cache_policy=NO_CACHE)
def merge_municipalities_geometries_task(
    water_companies_df: pl.DataFrame,
) -> pl.DataFrame:
    """
    Merge the geometries of the municipalities into a single geometry for each water company.
    Return water_companies_df with an additional column "Geometry" containing the merged geometry.
    """
    geometries = []
    for row in water_companies_df.iter_rows(named=True):
        # Extract all geometries from municipalities
        muni_geometries = row["Municipality Geometries"]
        if muni_geometries:
            muni_geometries = [shape(json.loads(muni)) for muni in muni_geometries]
            merged_geometry = unary_union(muni_geometries)
            geometries.append(json.dumps(merged_geometry.__geo_interface__))
        else:
            geometries.append(None)
    return water_companies_df.with_columns(
        pl.Series(name="Geometry", values=geometries)
    )


@task(name="update_distribution_zone", cache_policy=NO_CACHE)
def update_distribution_zone_task(
    df: pl.DataFrame, db_helper: services.DatabaseHelper
) -> None:
    """Update the distribution zone with the new geometry."""
    logger = get_run_logger()
    logger.info(f"Updating {len(df)} distribution zones")
    db_helper.update_records(
        df,
        table_name="DistributionZone",
    )


@flow(name="calculate_distribution_zone", persist_result=False)
def calculate_distribution_zone_flow():
    """Calculate the geometry of distribution zones that are missing it, based on the covered municipalities."""
    db_helper = services.db_helper()
    df = db_helper.load_all_records(
        table_name="DistributionZone",
        fields=["Id", "Municipality Geometries"],
        viewName="Missing Geometries",
    )
    df = merge_municipalities_geometries_task(df)
    df = df.filter(pl.col("Geometry").is_not_null())
    update_distribution_zone_task(df, db_helper)


if __name__ == "__main__":
    calculate_distribution_zone_flow()
