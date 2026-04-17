"""
Download and convert the commune GPKG file to GeoJSON.
Produces files data/raw/municipalities.geojson and data/raw/pt_concelhos_municipalities.geojson
"""
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen, urlretrieve

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE


@task(name="download commune gpkg")
def download_commune_gpkg(dest_directory: Path) -> Path:
    dst = dest_directory / "COMM_RG_01M_2016_2035.gpkg"
    if dst.exists():
        return dst
    source = "https://gisco-services.ec.europa.eu/distribution/v2/communes/gpkg/COMM_RG_01M_2016_3035.gpkg"
    urlretrieve(source, dst)
    return dst


@task(name="download LAU population CSV")
def download_lau_population(dest_directory: Path) -> tuple[Path, int]:
    """Download the latest available LAU population CSV from GISCO.

    Tries candidate years newest-first, HEAD-checks each URL, downloads the
    first one that exists.  Returns (local_path, year).
    """
    candidate_years = [2024, 2023, 2022, 2021]
    base_url = "https://gisco-services.ec.europa.eu/distribution/v2/lau/csv/LAU_RG_01M_{year}_4326.csv"

    for year in candidate_years:
        dst = dest_directory / f"lau_population_{year}.csv"
        if dst.exists():
            return dst, year
        url = base_url.format(year=year)
        try:
            req = Request(url, method="HEAD")
            urlopen(req)
        except (HTTPError, URLError):
            continue
        urlretrieve(url, dst)
        return dst, year

    raise RuntimeError(
        f"Could not find a LAU population CSV for any of years: {candidate_years}"
    )


@task(name="download concelhos CSV")
def download_concelhos_csv(dest_directory: Path) -> Path:
    dst = dest_directory / "pt_concelhos.csv"
    if dst.exists():
        return dst
    source = "https://raw.githubusercontent.com/centraldedados/codigos_postais/master/data/concelhos.csv"
    urlretrieve(source, dst)
    return dst


@task(name="load communes to DuckDB", cache_policy=NO_CACHE)
def load_communes_to_duckdb(conn: duckdb.DuckDBPyConnection, gpkg: Path) -> None:
    """Load communes from GPKG into DuckDB, transforming CRS 3035→4326 and normalising CNTR_CODE."""
    conn.sql(f"""
        CREATE TABLE communes AS
        SELECT
            * EXCLUDE (geom, CNTR_CODE),
            ST_Transform(geom, 'EPSG:3035', 'EPSG:4326') AS geom,
            REPLACE(CNTR_CODE, 'UK', 'GB') AS CNTR_CODE
        FROM st_read('{gpkg}')
    """)


@task(name="add population to communes", cache_policy=NO_CACHE)
def add_population_to_communes(
    conn: duckdb.DuckDBPyConnection, lau_csv: Path, year: int
) -> None:
    """Join LAU population data into the communes table.

    Detects the population column name automatically (``POP_<year>`` or ``POP``).
    """
    # Detect the population column name from the CSV header
    desc = conn.sql(
        f"DESCRIBE SELECT * FROM read_csv('{lau_csv}', header=true) LIMIT 0"
    )
    col_names = [row[0] for row in desc.fetchall()]

    pop_col = f"POP_{year}"
    if pop_col not in col_names:
        pop_candidates = [c for c in col_names if c.upper().startswith("POP")]
        if not pop_candidates:
            raise ValueError(
                f"No population column found in {lau_csv}. Available columns: {col_names}"
            )
        pop_col = pop_candidates[0]

    conn.sql("ALTER TABLE communes ADD COLUMN POPULATION BIGINT")
    conn.sql(f"""
        UPDATE communes
        SET POPULATION = lau."{pop_col}"
        FROM read_csv('{lau_csv}', header=true) AS lau
        WHERE communes.NSI_CODE = split_part(lau.GISCO_ID, '_', 2)
          AND communes.CNTR_CODE = lau.CNTR_CODE
    """)


@task(name="dissolve PT concelhos", cache_policy=NO_CACHE)
def dissolve_pt_concelhos(
    conn: duckdb.DuckDBPyConnection,
    concelhos_csv: Path,
) -> None:
    """Dissolve PT parish geometries into municipality (concelho) polygons.

    Reads from the ``communes`` table already loaded in *conn* and writes a
    ``pt_concelhos`` table with dissolved geometries and summed population.
    """
    conn.sql(f"""
        CREATE TABLE pt_concelhos AS
        SELECT
            c.nome_concelho AS COMM_NAME,
            'PT_CONC_' || p.muni_code AS COMM_ID,
            'PT' AS CNTR_CODE,
            ST_Union_Agg(p.geom) AS geom,
            SUM(p.POPULATION)::BIGINT AS POPULATION
        FROM (
            SELECT NSI_CODE[:4] AS muni_code, geom, POPULATION
            FROM communes
            WHERE CNTR_CODE = 'PT' AND NSI_CODE IS NOT NULL
        ) p
        JOIN (
            SELECT CONCAT(cod_distrito, cod_concelho) AS muni_code, nome_concelho
            FROM read_csv('{concelhos_csv}')
        ) c ON c.muni_code = p.muni_code
        GROUP BY p.muni_code, c.nome_concelho
    """)


@task(name="export GeoJSON", cache_policy=NO_CACHE)
def export_geojson(
    conn: duckdb.DuckDBPyConnection, table: str, output_path: Path
) -> Path:
    """Export a DuckDB table to a GeoJSON file via the GDAL driver."""
    conn.sql(f"""
        COPY (SELECT * FROM {table})
        TO '{output_path}'
        WITH (FORMAT GDAL, DRIVER 'GeoJSON')
    """)
    return output_path


@flow(name="download_municipality")
def download_municipality(data_directory: Path):
    raw = data_directory / "raw"
    municipalities_geojson = raw / "municipalities.geojson"
    pt_concelhos_geojson = raw / "pt_concelhos_municipalities.geojson"

    gpkg = download_commune_gpkg(raw)
    lau_csv, year = download_lau_population(raw)
    concelhos_csv = download_concelhos_csv(raw)

    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    try:
        load_communes_to_duckdb(conn, gpkg)
        add_population_to_communes(conn, lau_csv, year)
        dissolve_pt_concelhos(conn, concelhos_csv)
        export_geojson(conn, "communes", municipalities_geojson)
        export_geojson(conn, "pt_concelhos", pt_concelhos_geojson)
    finally:
        conn.close()

    return municipalities_geojson


if __name__ == "__main__":
    download_municipality(Path("data"))
