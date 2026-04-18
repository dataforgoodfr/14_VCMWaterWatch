"""
Dissolve municipality geometries into country polygons.

Reads staging.Municipality and raw.Country, writes staging.Country
with Code, Name, and dissolved Geometry (GeoJSON string).

This ensures country borders exactly match zone borders built from
the same municipality geometries.
"""

from pathlib import Path

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db


@task(name="dissolve_countries", cache_policy=NO_CACHE)
def dissolve_countries(conn: duckdb.DuckDBPyConnection) -> None:
    """Dissolve municipality geometries by CountryCode into staging.Country."""
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.execute('''
        CREATE OR REPLACE TABLE staging."Country" AS
        SELECT
            c.Code,
            c.Name,
            ST_AsGeoJSON(
                ST_Union_Agg(ST_GeomFromGeoJSON(m."Geometry"))
            ) AS "Geometry"
        FROM staging."Municipality" m
        JOIN raw."Country" c ON c.Code = m."CountryCode"
        GROUP BY c.Code, c.Name
    ''')


@flow(name="dissolve_countries")
def dissolve_countries_flow(data_directory: Path) -> None:
    """Standalone flow entry point."""
    conn = staging_db.get_connection(data_directory)
    try:
        dissolve_countries(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    dissolve_countries_flow(data_directory)
