"""Tests for extract_countries."""
import duckdb
from pipelines.extract.extract_countries import extract_countries


def test_extract_countries_writes_raw_table(tmp_path):
    """extract_countries writes Code and Name columns into raw.Country."""
    raw_db = tmp_path / "raw" / "raw.duckdb"
    raw_db.parent.mkdir(parents=True)
    # Create the raw database so ATTACH works
    duckdb.connect(str(raw_db)).close()

    conn = duckdb.connect()
    conn.execute(f"ATTACH '{raw_db}' AS raw")

    extract_countries(conn)

    rows = conn.sql("SELECT Code, Name FROM raw.Country ORDER BY Code").fetchall()
    conn.close()

    codes = [r[0] for r in rows]
    names = [r[1] for r in rows]

    assert "NL" in codes
    assert "DE" in codes
    assert "BE" in codes
    assert names[codes.index("NL")] == "Netherlands"
    assert len(rows) == 16
