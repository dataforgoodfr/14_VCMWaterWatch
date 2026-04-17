"""Tests for download_municipalities pipeline tasks."""
import json
import tempfile
from pathlib import Path

import duckdb

from pipelines.extract.download_municipalities import (
    add_population_to_communes,
    dissolve_pt_concelhos,
    export_geojson,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_communes_table(conn: duckdb.DuckDBPyConnection, include_population: bool = False) -> None:
    """Populate a ``communes`` table in *conn* with test data.

    Includes:
    - 2 PT parishes belonging to 2 different concelhos (for dissolve test)
    - 1 AT commune (non-PT, to confirm it is not included in PT output)

    Pass ``include_population=True`` to pre-populate the POPULATION column
    (used by tests that skip the add_population_to_communes step).
    """
    if include_population:
        conn.sql("""
            CREATE TABLE communes AS
            SELECT 'AT70701' AS COMM_ID, 'Test AT'  AS COMM_NAME, 'AT' AS CNTR_CODE,
                   NULL      AS NSI_CODE, NULL AS NUTS_CODE,
                   ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))') AS geom,
                   NULL::BIGINT AS POPULATION
            UNION ALL
            SELECT 'PT10105A', 'Parish A', 'PT', '010501', NULL,
                   ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))'), NULL::BIGINT
            UNION ALL
            SELECT 'PT10105B', 'Parish B', 'PT', '010502', NULL,
                   ST_GeomFromText('POLYGON((1 0, 2 0, 2 1, 1 1, 1 0))'), NULL::BIGINT
            UNION ALL
            SELECT 'PT10106A', 'Parish C', 'PT', '010601', NULL,
                   ST_GeomFromText('POLYGON((3 0, 4 0, 4 1, 3 1, 3 0))'), NULL::BIGINT
        """)
    else:
        conn.sql("""
            CREATE TABLE communes AS
            SELECT 'AT70701' AS COMM_ID, 'Test AT'  AS COMM_NAME, 'AT' AS CNTR_CODE,
                   NULL      AS NSI_CODE, NULL AS NUTS_CODE,
                   ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))') AS geom
            UNION ALL
            SELECT 'PT10105A', 'Parish A', 'PT', '010501', NULL,
                   ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))')
            UNION ALL
            SELECT 'PT10105B', 'Parish B', 'PT', '010502', NULL,
                   ST_GeomFromText('POLYGON((1 0, 2 0, 2 1, 1 1, 1 0))')
            UNION ALL
            SELECT 'PT10106A', 'Parish C', 'PT', '010601', NULL,
                   ST_GeomFromText('POLYGON((3 0, 4 0, 4 1, 3 1, 3 0))')
        """)


def _make_lau_csv(path: Path, year: int) -> None:
    """Write a minimal LAU CSV with POP_<year> column."""
    path.write_text(
        f"GISCO_ID,LAU_ID,LAU_NAME,POP_{year}\n"
        f"AT70701,70701,Test AT,12345\n"
        f"PT10105A,10105A,Parish A,500\n"
        f"PT10105B,10105B,Parish B,300\n"
        f"PT10106A,10106A,Parish C,200\n"
    )


def _make_concelhos_csv(path: Path) -> None:
    """Write a minimal concelhos CSV."""
    path.write_text(
        "cod_distrito,cod_concelho,nome_concelho\n"
        "01,05,Aveiro\n"
        "01,06,Castelo de Paiva\n"
    )


def _make_test_conn() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with spatial extension loaded."""
    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    return conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_add_population_to_communes():
    """Population values from the LAU CSV are joined onto the communes table."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        lau_csv = tmp / "lau_population_2023.csv"
        year = 2023
        _make_lau_csv(lau_csv, year)

        conn = _make_test_conn()
        _make_communes_table(conn)  # no POPULATION column yet
        add_population_to_communes(conn, lau_csv, year)

        rows = conn.sql("SELECT COMM_ID, POPULATION FROM communes ORDER BY COMM_ID").fetchall()
        by_id = dict(rows)

        assert by_id["AT70701"] == 12345
        assert by_id["PT10105A"] == 500
        assert by_id["PT10105B"] == 300
        assert by_id["PT10106A"] == 200

        conn.close()


def test_dissolve_pt_concelhos():
    """PT parishes are dissolved into concelhos; POPULATION is summed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        concelhos_csv = tmp / "concelhos.csv"
        output_path = tmp / "pt_concelhos_municipalities.geojson"

        _make_concelhos_csv(concelhos_csv)

        conn = _make_test_conn()
        _make_communes_table(conn, include_population=True)

        # Manually set population values (as add_population_to_communes would)
        conn.sql("""
            UPDATE communes SET POPULATION = 500 WHERE COMM_ID = 'PT10105A';
            UPDATE communes SET POPULATION = 300 WHERE COMM_ID = 'PT10105B';
            UPDATE communes SET POPULATION = 200 WHERE COMM_ID = 'PT10106A';
        """)

        dissolve_pt_concelhos(conn, concelhos_csv)
        export_geojson(conn, "pt_concelhos", output_path)

        with open(output_path) as f:
            result = json.load(f)

        features = result["features"]
        assert len(features) == 2

        by_name = {f["properties"]["COMM_NAME"]: f for f in features}
        assert "Aveiro" in by_name
        assert "Castelo de Paiva" in by_name

        aveiro = by_name["Aveiro"]
        assert aveiro["properties"]["CNTR_CODE"] == "PT"
        assert aveiro["properties"]["COMM_ID"] == "PT_CONC_0105"
        assert aveiro["geometry"]["type"] in ("Polygon", "MultiPolygon")

        # Aveiro has parishes A (500) + B (300) = 800
        assert aveiro["properties"]["POPULATION"] == 800

        castelo = by_name["Castelo de Paiva"]
        # Castelo de Paiva has parish C (200)
        assert castelo["properties"]["POPULATION"] == 200

        conn.close()


def test_export_geojson():
    """export_geojson writes a valid GeoJSON FeatureCollection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        output_path = tmp / "out.geojson"

        conn = _make_test_conn()
        conn.sql("""
            CREATE TABLE test_export AS
            SELECT
                'X001'  AS COMM_ID,
                'Test'  AS COMM_NAME,
                'AT'    AS CNTR_CODE,
                ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))') AS geom
        """)
        export_geojson(conn, "test_export", output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        assert data["features"][0]["properties"]["COMM_ID"] == "X001"
        conn.close()
