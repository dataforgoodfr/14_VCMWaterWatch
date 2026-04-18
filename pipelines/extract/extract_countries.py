"""
Write hardcoded European country metadata into raw.Country.

No download required — the country list is maintained in
pipelines.transform.config.EUROPEAN_COUNTRIES.
"""

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipelines.transform.config import EUROPEAN_COUNTRIES


@task(name="extract_countries", cache_policy=NO_CACHE)
def extract_countries(conn: duckdb.DuckDBPyConnection) -> None:
    """Write EUROPEAN_COUNTRIES into raw.Country (Code, Name)."""
    import pandas as pd

    records = [
        {"Code": code, "Name": name} for code, name in EUROPEAN_COUNTRIES.items()
    ]
    conn.register("_countries_tmp", pd.DataFrame(records))
    conn.execute('CREATE OR REPLACE TABLE raw."Country" AS SELECT * FROM _countries_tmp')
    conn.unregister("_countries_tmp")


@flow(name="extract_countries")
def extract_countries_flow(data_directory):
    """Standalone flow entry point."""
    from pathlib import Path
    from pipelines.common import staging_db

    conn = staging_db.get_connection(Path(data_directory))
    try:
        extract_countries(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    extract_countries_flow(data_directory)
