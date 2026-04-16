"""
Prefect workflow to export zone data from NocoDB as PMTiles.

Reads zone records (Country, DistributionZone) from NocoDB, produces a GeoJSON
FeatureCollection per table in a staging directory, then converts them to PMTiles
in the destination directory.

Output GeoJSON fields per feature:
 - Geometry (from NocoDB)
 - noco_id (NocoDB primary key)
 - PVC Level
 - VCM Level
 - company_name (DistributionZone only, from linked Actor records)
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services

ZONE_FIELDS = ["Id", "Code", "Name", "Geometry", "PVC Level", "VCM Level", "Map Color"]
# Extra fields per table (e.g. linked record display values)
EXTRA_FIELDS = {"DistributionZone": ["ActorName"]}
ZONE_TABLES = {
    "Country": "data_countries",
    "DistributionZone": "data_distribution_zones",
}


@task(name="export_zones_geojson", cache_policy=NO_CACHE)
def export_zones_geojson_task(table_name: str, output_dir: Path) -> Path:
    """
    Read all records from a zone table and write a GeoJSON FeatureCollection.
    Records without geometry are skipped.
    """
    logger = get_run_logger()
    db_helper = services.db_helper()

    fields = ZONE_FIELDS + EXTRA_FIELDS.get(table_name, [])
    records = db_helper.load_all_records(table_name=table_name, fields=fields)
    logger.info(f"Loaded {len(records)} records from {table_name}")

    features = []
    skipped = 0
    for row in records:
        geometry_str = row.get("Geometry")
        if not geometry_str:
            skipped += 1
            continue
        geometry = json.loads(geometry_str)
        props = {
            "noco_id": row.get("Id"),
            "code": row["Code"],
            "name": row["Name"],
            "pvc_level": row.get("PVC Level"),
            "vcm_level": row.get("VCM Level"),
            "map_color": row.get("Map Color"),
        }
        if table_name == "DistributionZone":
            actor_names = row.get("ActorName")
            if actor_names is not None:
                if isinstance(actor_names, list):
                    company_name = ", ".join(str(n) for n in actor_names if n)
                else:
                    company_name = str(actor_names) if actor_names else None
                if company_name:
                    props["company_name"] = company_name
        feature = {"type": "Feature", "geometry": geometry, "properties": props}
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
    """Convert a GeoJSON file to a PMTiles archive using tippecanoe."""
    logger = get_run_logger()
    output_dir.mkdir(parents=True, exist_ok=True)
    pmtiles_file = output_dir / f"{layer}.pmtiles"

    # Write to a temp file first, then atomically move into place so the
    # destination is never left in a partial/corrupt state.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_file = Path(tmp_dir) / f"{layer}.pmtiles"

        command = [
            "tippecanoe",
            "-zg",
            "--force",
            "-o",
            str(tmp_file),
            "--layer",
            layer,
            "--coalesce-densest-as-needed",
            "--extend-zooms-if-still-dropping",
            str(geojson_file),
        ]

        logger.info(f"Running: {' '.join(command)}")
        subprocess.run(command, check=True)
        shutil.move(str(tmp_file), str(pmtiles_file))

    logger.info(f"Created {pmtiles_file}")
    return pmtiles_file


@flow(name="export_pmtiles", persist_result=False)
def export_pmtiles_flow(destination: Path) -> None:
    """Export zone data from NocoDB to PMTiles.

    Args:
        destination: Directory where .pmtiles files are written directly.
            Intermediate GeoJSON files go to a sibling ``staging/`` directory.
    """
    staging_dir = (destination / "../staging").resolve()
    staging_dir.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)

    for table, layer in ZONE_TABLES.items():
        geojson_path = export_zones_geojson_task(
            table_name=table, output_dir=staging_dir
        )
        create_pmtiles_task(
            geojson_file=geojson_path, layer=layer, output_dir=destination
        )


if __name__ == "__main__":
    destination = Path(os.environ.get("PM_TILES_DIR", "data/export"))
    export_pmtiles_flow(destination=destination)
