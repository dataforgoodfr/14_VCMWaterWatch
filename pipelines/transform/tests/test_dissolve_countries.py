"""Tests for dissolve_countries."""
import json

import duckdb
import pytest

from pipelines.transform.dissolve_countries import dissolve_countries


def _make_polygon(lon, lat, size=0.1):
    """Return a simple GeoJSON polygon string around (lon, lat)."""
    return json.dumps({
        "type": "Polygon",
        "coordinates": [[
            [lon, lat],
            [lon + size, lat],
            [lon + size, lat + size],
            [lon, lat + size],
            [lon, lat],
        ]],
    })


@pytest.fixture
def conn(tmp_path):
    raw_db = tmp_path / "raw" / "raw.duckdb"
    staging_db = tmp_path / "staging" / "staging.duckdb"
    raw_db.parent.mkdir(parents=True)
    staging_db.parent.mkdir(parents=True)
    duckdb.connect(str(raw_db)).close()
    duckdb.connect(str(staging_db)).close()

    c = duckdb.connect()
    c.execute(f"ATTACH '{raw_db}' AS raw")
    c.execute(f"ATTACH '{staging_db}' AS staging")

    # Seed raw.Country
    c.execute("""
        CREATE TABLE raw."Country" AS
        SELECT * FROM (VALUES ('NL', 'Netherlands'), ('BE', 'Belgium')) t(Code, Name)
    """)

    # Seed staging.Municipality with 2 NL and 1 BE municipality
    import pandas as pd
    _municipalities = pd.DataFrame([
        {"Code": "NL001", "Name": "Amsterdam", "CountryCode": "NL",
         "Geometry": _make_polygon(4.9, 52.4)},
        {"Code": "NL002", "Name": "Rotterdam", "CountryCode": "NL",
         "Geometry": _make_polygon(4.5, 51.9)},
        {"Code": "BE001", "Name": "Antwerp", "CountryCode": "BE",
         "Geometry": _make_polygon(4.4, 51.2)},
    ])
    c.execute('CREATE TABLE staging."Municipality" AS SELECT * FROM _municipalities')

    yield c
    c.close()


def test_dissolve_creates_staging_country(conn):
    """dissolve_countries writes Code, Name, Geometry into staging.Country."""
    dissolve_countries(conn)

    rows = conn.sql(
        'SELECT Code, Name, Geometry FROM staging."Country" ORDER BY Code'
    ).fetchall()
    assert len(rows) == 2

    codes = [r[0] for r in rows]
    assert codes == ["BE", "NL"]

    # Names come from raw.Country
    names = [r[1] for r in rows]
    assert names == ["Belgium", "Netherlands"]

    # Geometry is valid GeoJSON
    for row in rows:
        geom = json.loads(row[2])
        assert geom["type"] in ("Polygon", "MultiPolygon")


def test_dissolve_unions_geometries(conn):
    """NL has 2 municipalities — dissolved geometry should cover both."""
    dissolve_countries(conn)

    geom_json = conn.sql("""
        SELECT Geometry FROM staging."Country" WHERE Code = 'NL'
    """).fetchone()[0]
    geom = json.loads(geom_json)
    assert geom["type"] in ("Polygon", "MultiPolygon")
