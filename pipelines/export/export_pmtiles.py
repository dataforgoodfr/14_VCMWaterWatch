"""
Prefect workflow to export zone data from NocoDB as PMTiles.

Reads zone records (Country, DistributionZone) from NocoDB, produces a GeoJSON
FeatureCollection per table in data/staging, then converts them to PMTiles in
data/export.

Output GeoJSON fields per feature:
 - Geometry (from NocoDB)
 - PVC Level
 - VCM Level
"""

import json
import subprocess
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services

# Fields shared by every zone table we export
ZONE_FIELDS = ["Code", "Name", "Geometry", "PVC Level", "VCM Level"]
ZONE_TABLES = {
    "Country": "data_countries",
}


@task(name="export_zones_geojson", cache_policy=NO_CACHE)
def export_zones_geojson_task(table_name: str, output_dir: Path) -> Path:
    """
    Read all records from a zone table and write a GeoJSON FeatureCollection.

    Records without geometry are skipped.

    Returns:
        Path to the written GeoJSON file.
    """
    logger = get_run_logger()
    db_helper = services.db_helper()

    df = db_helper.load_all_records(table_name=table_name, fields=ZONE_FIELDS)
    logger.info(f"Loaded {len(df)} records from {table_name}")

    features = []
    skipped = 0
    for row in df.iter_rows(named=True):
        geometry_str = row.get("Geometry")
        if not geometry_str:
            skipped += 1
            continue
        geometry = json.loads(geometry_str)
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "code": row["Code"],
                "name": row["Name"],
                "pvc_level": row.get("PVC Level"),
                "vcm_level": row.get("VCM Level"),
            },
        }
        features.append(feature)

    if skipped:
        logger.warning(f"Skipped {skipped} records without geometry")

    collection = {
        "type": "FeatureCollection",
        "features": features,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{table_name}_tile_data.geojson"
    output_path.write_text(json.dumps(collection), encoding="utf-8")
    logger.info(f"Wrote {len(features)} features to {output_path}")
    return output_path


@task(name="create_pmtiles", cache_policy=NO_CACHE)
def create_pmtiles_task(geojson_file: Path, layer: str, output_dir: Path) -> Path:
    """
    Convert a GeoJSON file to a PMTiles archive using tippecanoe.

    Args:
        geojson_file: Path to the input GeoJSON file.
        layer: Layer name for the vector tiles (e.g. "data_countries").
        output_dir: Directory where the .pmtiles file will be written.

    Returns:
        Path to the generated PMTiles file.
    """
    logger = get_run_logger()
    output_dir.mkdir(parents=True, exist_ok=True)
    pmtiles_file = output_dir / f"{layer}.pmtiles"

    command = [
        "tippecanoe",
        "-zg",
        "--force",
        "-o",
        str(pmtiles_file),
        "--layer",
        layer,
        "--coalesce-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        str(geojson_file),
    ]

    logger.info(f"Running: {' '.join(command)}")
    subprocess.run(command, check=True)
    logger.info(f"Created {pmtiles_file}")
    return pmtiles_file


@flow(name="export_pmtiles", persist_result=False)
def export_pmtiles_flow(data_directory: Path) -> None:
    """
    Export zone data from NocoDB to PMTiles.

    Steps:
      1. For each zone table, export a GeoJSON FeatureCollection to data/staging.
      2. Convert the GeoJSON files to PMTiles in data/export.
    """
    staging_dir = data_directory / "staging"
    export_dir = data_directory / "export"

    for table, layer in ZONE_TABLES.items():
        geojson_path = export_zones_geojson_task(
            table_name=table, output_dir=staging_dir
        )
        create_pmtiles_task(
            geojson_file=geojson_path, layer=layer, output_dir=export_dir
        )


if __name__ == "__main__":
    export_pmtiles_flow(data_directory=Path("data"))
