"""
Prefect workflow for calculating the geometry of distribution zones that are missing it, based on the
covered municipalities.
"""

import json
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from shapely import unary_union
from shapely.geometry import shape
from pipelines.common import services


@task(name="merge_municipalities_geometries", cache_policy=NO_CACHE)
def merge_municipalities_geometries_task(
    records: list[dict],
) -> list[dict]:
    """
    Merge the geometries of the municipalities into a single geometry for each distribution zone.
    """
    result = []
    for row in records:
        row = dict(row)
        muni_geometries = row.get("Municipality Geometries")
        if muni_geometries:
            shapes = [shape(json.loads(muni)) for muni in muni_geometries]
            merged_geometry = unary_union(shapes)
            row["Geometry"] = json.dumps(merged_geometry.__geo_interface__)
        else:
            row["Geometry"] = None
        result.append(row)
    return result


@task(name="update_distribution_zone", cache_policy=NO_CACHE)
def update_distribution_zone_task(
    records: list[dict], db_helper: services.DatabaseHelper
) -> None:
    """Update the distribution zone with the new geometry."""
    logger = get_run_logger()
    logger.info(f"Updating {len(records)} distribution zones")
    db_helper.update_records(records, table_name="DistributionZone")


@flow(name="calculate_distribution_zone", persist_result=False)
def calculate_distribution_zone_flow():
    """Calculate the geometry of distribution zones that are missing it."""
    db_helper = services.db_helper()
    records = db_helper.load_all_records(
        table_name="DistributionZone",
        fields=["Id", "Geometry", "Municipality Geometries"],
    )
    # Filter to only zones missing geometry
    records = [r for r in records if r.get("Geometry") is None]
    records = merge_municipalities_geometries_task(records)
    records = [r for r in records if r.get("Geometry") is not None]
    update_distribution_zone_task(records, db_helper)


if __name__ == "__main__":
    calculate_distribution_zone_flow()
