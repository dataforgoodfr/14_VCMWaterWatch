"""
Download and convert the commune GPKG file to GeoJSON.
Produces files data/raw/municipalities.geojson and data/raw/pt_concelhos_municipalities.geojson
"""
from pathlib import Path
from prefect import flow, task
import pyogrio
from urllib.request import urlretrieve


@task(name="download commune gpkg")
def download_commune_gpkg(dest_directory: Path) -> Path:
    dst = dest_directory / "COMM_RG_01M_2016_2035.gpkg"
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


@task(name="dissolve PT concelhos")
def dissolve_pt_concelhos(
    municipalities_geojson: Path,
    concelhos_csv: Path,
    output_path: Path,
) -> Path:
    """Dissolve PT parish geometries into municipality (concelho) polygons."""
    if output_path.exists():
        return output_path

    import duckdb

    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.sql(f"""
        CREATE TABLE parishes AS
        SELECT 
            NSI_CODE[:4] AS muni_code,
            geom
        FROM st_read('{municipalities_geojson}')
        WHERE CNTR_CODE = 'PT' AND NSI_CODE IS NOT NULL
    """)

    conn.sql(f"""
        CREATE TABLE concelhos AS
        SELECT 
            CONCAT(cod_distrito, cod_concelho) AS muni_code,
            nome_concelho
        FROM read_csv('{concelhos_csv}')
    """)

    conn.sql("""
        CREATE TABLE dissolved AS
        SELECT
            c.nome_concelho AS COMM_NAME,
            'PT_CONC_' || p.muni_code AS COMM_ID,
            'PT' AS CNTR_CODE,
            ST_Union_Agg(p.geom) AS geom
        FROM parishes p
        JOIN concelhos c ON c.muni_code = p.muni_code
        GROUP BY p.muni_code, c.nome_concelho
    """)

    conn.sql(f"""
        COPY (SELECT * FROM dissolved)
        TO '{output_path}'
        WITH (FORMAT GDAL, DRIVER 'GeoJSON')
    """)

    conn.close()
    return output_path


@task(name="download concelhos CSV")
def download_concelhos_csv(dest_directory: Path) -> Path:
    dst = dest_directory / "pt_concelhos.csv"
    if dst.exists():
        return dst
    source = "https://raw.githubusercontent.com/centraldedados/codigos_postais/master/data/concelhos.csv"
    urlretrieve(source, dst)
    return dst


@flow(name="download_municipality")
def download_municipality(data_directory: Path):
    gpkg = download_commune_gpkg(data_directory / "raw")
    geojson = convert_gpkg_to_geojson(
        gpkg, data_directory / "raw" / "municipalities.geojson"
    )
    # PT concelhos (dissolved from parishes)
    concelhos_csv = download_concelhos_csv(data_directory / "raw")
    dissolve_pt_concelhos(
        geojson,
        concelhos_csv,
        data_directory / "raw" / "pt_concelhos_municipalities.geojson",
    )
    return geojson


if __name__ == "__main__":
    download_municipality(Path("data"))
