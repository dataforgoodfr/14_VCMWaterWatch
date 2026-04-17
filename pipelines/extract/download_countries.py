"""
Download and convert the country GPKG file from GISCO to GeoJSON.

Produces data/raw/countries.geojson with properties compatible with the
transform/geojson.py pipeline (name, ISO3166-1-Alpha-2, ISO3166-1-Alpha-3).

Source: Eurostat GISCO — 1:1M country boundaries, 2024, EPSG:4326.
Eurostat-specific codes are normalised to ISO 3166-1 alpha-2:
  EL → GR  (Greece)
  UK → GB  (United Kingdom)
Disputed/non-sovereign features (CNTR_ID starting with 'X') are excluded.
"""

from pathlib import Path
from urllib.request import urlretrieve

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

COUNTRIES_GPKG_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/countries/gpkg/"
    "CNTR_RG_01M_2024_4326.gpkg"
)


@task(name="download countries gpkg")
def download_countries_gpkg(dest_directory: Path) -> Path:
    dst = dest_directory / "CNTR_RG_01M_2024_4326.gpkg"
    if dst.exists():
        return dst
    urlretrieve(COUNTRIES_GPKG_URL, dst)
    return dst


@task(name="load countries to DuckDB", cache_policy=NO_CACHE)
def load_countries_to_duckdb(conn: duckdb.DuckDBPyConnection, gpkg: Path) -> None:
    """Load countries from GPKG, normalising Eurostat codes, dropping disputed features."""
    conn.sql(f"""
        CREATE TABLE countries AS
        SELECT
            REPLACE(REPLACE(CNTR_ID, 'UK', 'GB'), 'EL', 'GR') AS "ISO3166-1-Alpha-2",
            NAME_ENGL AS name,
            ISO3_CODE AS "ISO3166-1-Alpha-3",
            geom
        FROM st_read('{gpkg}')
        WHERE CNTR_ID NOT LIKE 'X%'
    """)


@task(name="export countries GeoJSON", cache_policy=NO_CACHE)
def export_countries_geojson(
    conn: duckdb.DuckDBPyConnection, output_path: Path
) -> Path:
    conn.sql(f"""
        COPY (SELECT * FROM countries)
        TO '{output_path}'
        WITH (FORMAT GDAL, DRIVER 'GeoJSON')
    """)
    return output_path


@flow(name="download_countries")
def download_countries(data_directory: Path) -> Path:
    raw = data_directory / "raw"
    countries_geojson = raw / "countries.geojson"

    gpkg = download_countries_gpkg(raw)

    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    try:
        load_countries_to_duckdb(conn, gpkg)
        export_countries_geojson(conn, countries_geojson)
    finally:
        conn.close()

    return countries_geojson


if __name__ == "__main__":
    download_countries(Path("data"))
