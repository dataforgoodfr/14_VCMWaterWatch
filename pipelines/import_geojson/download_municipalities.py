from pathlib import Path
from prefect import flow, task
import pyogrio
from urllib.request import urlretrieve


@task(name="download commune gpkg")
def download_commune_gpkg() -> Path:
    dst = Path("data") / "COMM_RG_01M_2016_2035.gpkg"
    if dst.exists():
        return dst
    source = "https://gisco-services.ec.europa.eu/distribution/v2/communes/gpkg/COMM_RG_01M_2016_3035.gpkg"

    urlretrieve(source, dst)

    return dst


@task(name="convert_gpkg_to_geojson")
def convert_gpkg_to_geojson(gpkg_file: Path, output_path: Path):
    """
    Convert postal codes in GPKG file to GeoJSON.
    """
    if output_path.exists():
        return output_path
    gdf = pyogrio.read_dataframe(gpkg_file)
    gdf = gdf.to_crs(epsg=4326)

    # Replace "UK" with "GB" in CNTR_CODE property if it exists
    if "CNTR_CODE" in gdf.columns:
        gdf["CNTR_CODE"] = gdf["CNTR_CODE"].replace("UK", "GB")

    # Write to GeoJSON using pyogrio
    pyogrio.write_dataframe(gdf, output_path, driver="GeoJSON")

    return output_path


@flow(name="download_municipality")
def download_municipality():
    gpkg = download_commune_gpkg()
    geojson = convert_gpkg_to_geojson(gpkg, Path("data") / "municipalities.geojson")
    return geojson


if __name__ == "__main__":
    download_municipality()
