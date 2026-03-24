"""DuckDB connection management for raw + staging databases.

Provides a single connection that ATTACHes both raw.duckdb and staging.duckdb,
plus helpers to write list[dict] into tables and register temp tables for SQL joins.

Thread safety: DuckDB connections are NOT thread-safe. Do not share a connection
across concurrent tasks (.submit()). Within a synchronous flow, sharing is fine.
"""

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


def get_connection(data_dir: str | Path = "data") -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with raw + staging DBs attached.

    Tables are addressable as ``raw.<table>`` or ``staging.<table>``.
    """
    data_dir = Path(data_dir)
    raw_path = data_dir / "raw" / "raw.duckdb"
    staging_path = data_dir / "staging" / "staging.duckdb"

    # Ensure directories exist
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    staging_path.parent.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect()
    conn.execute(f"ATTACH '{raw_path}' AS raw")
    conn.execute(f"ATTACH '{staging_path}' AS staging")
    return conn


def write_table(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    records: list[dict[str, Any]],
    schema: str = "staging",
) -> None:
    """Write records into ``<schema>.<table_name>``, replacing any existing data."""
    qualified = f'{schema}."{table_name}"'
    if not records:
        conn.execute(f"DROP TABLE IF EXISTS {qualified}")
        return
    _df = pd.DataFrame(records)
    conn.execute(f"CREATE OR REPLACE TABLE {qualified} AS SELECT * FROM _df")


def register_temp(
    conn: duckdb.DuckDBPyConnection,
    name: str,
    records: list[dict[str, Any]],
) -> None:
    """Register a list[dict] as a temporary table for use in SQL joins."""
    if not records:
        conn.execute(f'CREATE OR REPLACE TEMP TABLE "{name}" (dummy INTEGER)')
        return
    _df = pd.DataFrame(records)
    conn.execute(f'CREATE OR REPLACE TEMP TABLE "{name}" AS SELECT * FROM _df')
