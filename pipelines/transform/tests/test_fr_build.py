"""Tests for pipelines/transform/fr_build.py

Uses an in-memory DuckDB that mimics the dansmoneau schema so no real file download
is needed.
"""

import datetime
from pathlib import Path

import duckdb
import pytest

from pipelines.transform.fr_build import (
    build_distribution_zones,
    build_water_companies,
    build_analysis_dansmoneau,
    build_analysis_outline,
    build_analysis_dedup,
    _attach_dansmoneau,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def dmeau_db(tmp_path) -> Path:
    """Create a minimal dansmoneau-compatible DuckDB file."""
    db_path = tmp_path / "fr_dansmoneau.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("INSTALL spatial; LOAD spatial;")

    conn.execute("""
        CREATE TABLE int__udi (
            cdreseau VARCHAR,
            nomreseaux VARCHAR,
            inseecommunes VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO int__udi VALUES
            ('UDI001', 'Réseau A', '29001,29002'),
            ('UDI002', 'Réseau B', '29003'),
            ('UDI003', NULL,       '29004')
    """)

    conn.execute("""
        CREATE TABLE int__udi_geom (
            code_udi VARCHAR,
            geom JSON
        )
    """)
    conn.execute("""
        INSERT INTO int__udi_geom VALUES
            ('UDI001', '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}'),
            ('UDI002', '{"type":"Polygon","coordinates":[[[1,0],[2,0],[2,1],[1,1],[1,0]]]}')
    """)

    conn.execute("""
        CREATE TABLE edc_prelevements (
            cdreseau VARCHAR,
            distrlib VARCHAR,
            moalib VARCHAR,
            ugelib VARCHAR,
            dateprel DATE,
            de_partition INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO edc_prelevements VALUES
            ('UDI001', 'Compagnie A', NULL, NULL, '2024-06-01', 2024),
            ('UDI001', 'Compagnie A', NULL, NULL, '2023-01-01', 2023),
            ('UDI002', 'Compagnie B', NULL, NULL, '2024-03-15', 2024),
            ('UDI003', 'Compagnie A', NULL, NULL, '2024-09-01', 2024)
    """)

    conn.execute("""
        CREATE TABLE int__resultats_udi_communes (
            cdreseau VARCHAR,
            inseecommune VARCHAR,
            datetimeprel TIMESTAMP,
            valtraduite DOUBLE,
            limite_qualite DOUBLE,
            categorie VARCHAR,
            de_partition INTEGER,
            referenceprel VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO int__resultats_udi_communes VALUES
            ('UDI001', '29001', '2023-05-10', 0.25, 0.5, 'cvm', 2023, 'REF001'),
            ('UDI001', '29001', '2024-01-15', 0.80, 0.5, 'cvm', 2024, 'REF002'),
            ('UDI001', '29002', '2024-02-20', 0.10, 0.5, 'cvm', 2024, 'REF003'),
            ('UDI002', '29003', '2024-03-01', 0.60, 0.5, 'cvm', 2024, 'REF004'),
            -- Non-CVM row (should be excluded)
            ('UDI001', '29001', '2024-04-01', 1.00, 0.5, 'nitrate', 2024, 'REF005'),
            -- Old row (de_partition < 2023, should be excluded)
            ('UDI001', '29001', '2022-12-01', 0.90, 0.5, 'cvm', 2022, 'REF006')
    """)

    conn.execute("""
        CREATE TABLE cog_communes (
            COM VARCHAR,
            DEP VARCHAR,
            NCC VARCHAR,
            TYPECOM VARCHAR,
            de_partition INTEGER
        )
    """)
    conn.execute("""
        INSERT INTO cog_communes VALUES
            ('29001', '29', 'BREST',    'COM', 2024),
            ('29003', '29', 'QUIMPER',  'COM', 2024),
            ('29004', '14', 'CAEN',     'COM', 2024)
    """)

    conn.close()
    return db_path


@pytest.fixture()
def conn_with_dmeau(tmp_path, dmeau_db):
    """An in-memory DuckDB with raw + staging attached AND dansmoneau attached."""
    raw_path = tmp_path / "raw" / "raw.duckdb"
    staging_path = tmp_path / "staging" / "staging.duckdb"
    raw_path.parent.mkdir(parents=True)
    staging_path.parent.mkdir(parents=True)

    conn = duckdb.connect()
    conn.execute(f"ATTACH '{raw_path}' AS raw")
    conn.execute(f"ATTACH '{staging_path}' AS staging")
    _attach_dansmoneau(conn, dmeau_db)
    # Seed INSEE→COMM_ID map used by build_distribution_zones.  Covers the
    # commune codes referenced by the test UDI fixtures.
    conn.execute("""
        CREATE OR REPLACE TEMP TABLE _fr_insee_to_comm AS
        SELECT * FROM (VALUES
            ('29001', 'FR11929001'),
            ('29002', 'FR11929002'),
            ('29003', 'FR11929003'),
            ('29004', 'FR11929004')
        ) AS t(insee, comm_id)
    """)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Tests: build_distribution_zones
# ---------------------------------------------------------------------------

def test_build_distribution_zones_count(conn_with_dmeau):
    count = build_distribution_zones(conn_with_dmeau)
    assert count == 3


def test_build_distribution_zones_schema(conn_with_dmeau):
    build_distribution_zones(conn_with_dmeau)
    rows = conn_with_dmeau.execute(
        'SELECT "Code", "Name", "CountryCode", "Type" FROM staging."DistributionZone_fr" ORDER BY "Code"'
    ).fetchdf()
    assert list(rows["Code"]) == ["UDI001", "UDI002", "UDI003"]
    assert list(rows["CountryCode"]) == ["FR", "FR", "FR"]
    assert list(rows["Type"]) == ["Distribution", "Distribution", "Distribution"]


def test_build_distribution_zones_null_name_falls_back_to_code(conn_with_dmeau):
    build_distribution_zones(conn_with_dmeau)
    rows = conn_with_dmeau.execute(
        'SELECT "Code", "Name" FROM staging."DistributionZone_fr" WHERE "Code" = \'UDI003\''
    ).fetchall()
    assert rows[0][1] == "UDI003"


def test_build_distribution_zones_geometry(conn_with_dmeau):
    build_distribution_zones(conn_with_dmeau)
    rows = conn_with_dmeau.execute(
        'SELECT "Code", "Geometry" FROM staging."DistributionZone_fr" ORDER BY "Code"'
    ).fetchall()
    # UDI001 and UDI002 have geometry; UDI003 does not
    assert rows[0][1] is not None  # UDI001
    assert rows[1][1] is not None  # UDI002
    assert rows[2][1] is None      # UDI003


# ---------------------------------------------------------------------------
# Tests: build_water_companies
# ---------------------------------------------------------------------------

def test_build_water_companies_most_recent(conn_with_dmeau):
    """distrlib assigned to a UDI should be the most-recent one."""
    count = build_water_companies(conn_with_dmeau)
    # UDI001+UDI003 → Compagnie A;  UDI002 → Compagnie B
    assert count == 2


def test_build_water_companies_zones_list(conn_with_dmeau):
    build_water_companies(conn_with_dmeau)
    rows = conn_with_dmeau.execute(
        'SELECT "Name", "DistributionZones" FROM staging."WaterCompany_fr" ORDER BY "Name"'
    ).fetchdf()
    names = list(rows["Name"])
    assert "Compagnie A" in names
    assert "Compagnie B" in names
    comp_a_zones = rows.loc[rows["Name"] == "Compagnie A", "DistributionZones"].iloc[0]
    assert set(comp_a_zones) == {"UDI001", "UDI003"}


# ---------------------------------------------------------------------------
# Tests: build_analysis_dansmoneau
# ---------------------------------------------------------------------------

def test_build_analysis_dansmoneau_filters_cvm(conn_with_dmeau):
    """Only rows with categorie='cvm' and de_partition >= 2023 are included."""
    count = build_analysis_dansmoneau(conn_with_dmeau)
    # REF001,REF002,REF003,REF004 → 4 rows (REF005 is nitrate, REF006 is 2022)
    assert count == 4


def test_build_analysis_dansmoneau_schema(conn_with_dmeau):
    build_analysis_dansmoneau(conn_with_dmeau)
    cols = {
        r[0]
        for r in conn_with_dmeau.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_catalog = 'staging' AND table_name = 'Analysis_fr_dansmoneau'"
        ).fetchall()
    }
    assert {"DistributionZoneCode", "MunicipalityCode", "Date", "CVMMeasure", "Source", "SourceRef"} <= cols


# ---------------------------------------------------------------------------
# Tests: build_analysis_outline
# ---------------------------------------------------------------------------

def _seed_outline_samples(conn):
    """Write outline_cvm_samples into raw schema for tests."""
    import pandas as pd
    _df = pd.DataFrame([
        {
            "dept": "29",
            "commune_name_raw": "Brest",
            "commune_name_norm": "BREST",
            "plv_date": datetime.date(2019, 4, 10),
            "value_ugl": 0.15,
            "source_file": "Annexe C (Bretagne).xlsx",
        },
        {
            "dept": "29",
            "commune_name_raw": "Quimper",
            "commune_name_norm": "QUIMPER",
            "plv_date": datetime.date(2020, 8, 22),
            "value_ugl": 0.55,
            "source_file": "Annexe C (Bretagne).xlsx",
        },
        # Unresolvable commune
        {
            "dept": "99",
            "commune_name_raw": "Fantasyland",
            "commune_name_norm": "FANTASYLAND",
            "plv_date": datetime.date(2020, 1, 1),
            "value_ugl": 0.30,
            "source_file": "Annexe C (Bretagne).xlsx",
        },
    ])
    conn.execute("CREATE OR REPLACE TABLE raw.outline_cvm_samples AS SELECT * FROM _df")


def test_build_analysis_outline_count(conn_with_dmeau):
    _seed_outline_samples(conn_with_dmeau)
    count = build_analysis_outline(conn_with_dmeau)
    # Brest → UDI001; Quimper → UDI002; Fantasyland → unmatched
    assert count == 2


def test_build_analysis_outline_no_raw_table(conn_with_dmeau):
    """When raw.outline_cvm_samples missing, returns 0 without error."""
    count = build_analysis_outline(conn_with_dmeau)
    assert count == 0


# ---------------------------------------------------------------------------
# Tests: build_analysis_dedup (priority: dansmoneau wins)
# ---------------------------------------------------------------------------

def _build_dedup_fixture(conn):
    """Seed both source tables with an overlapping row."""
    import pandas as pd

    _dansmoneau_df = pd.DataFrame([
        {
            "DistributionZoneCode": "UDI001",
            "MunicipalityCode": "29001",
            "Date": datetime.date(2023, 5, 10),
            "CVMMeasure": 0.25,
            "Source": "dansmoneau",
            "SourceRef": "REF001",
        },
    ])
    _outline_df = pd.DataFrame([
        # Same key as above — should be deduped away
        {
            "DistributionZoneCode": "UDI001",
            "MunicipalityCode": "29001",
            "Date": datetime.date(2023, 5, 10),
            "CVMMeasure": 0.25,
            "Source": "outline",
            "SourceRef": "Annexe C (Bretagne).xlsx",
        },
        # Different key — kept
        {
            "DistributionZoneCode": "UDI002",
            "MunicipalityCode": "29003",
            "Date": datetime.date(2020, 8, 22),
            "CVMMeasure": 0.55,
            "Source": "outline",
            "SourceRef": "Annexe C (Bretagne).xlsx",
        },
    ])
    conn.execute(
        'CREATE OR REPLACE TABLE staging."Analysis_fr_dansmoneau" AS SELECT * FROM _dansmoneau_df'
    )
    conn.execute(
        'CREATE OR REPLACE TABLE staging."Analysis_fr_outline" AS SELECT * FROM _outline_df'
    )


def test_build_analysis_dedup_count(conn_with_dmeau):
    _build_dedup_fixture(conn_with_dmeau)
    count = build_analysis_dedup(conn_with_dmeau)
    assert count == 2


def test_build_analysis_dedup_prefers_dansmoneau(conn_with_dmeau):
    _build_dedup_fixture(conn_with_dmeau)
    build_analysis_dedup(conn_with_dmeau)
    rows = conn_with_dmeau.execute(
        'SELECT "Source" FROM staging."Analysis_fr" WHERE "DistributionZoneCode" = \'UDI001\''
    ).fetchall()
    assert rows[0][0] == "dansmoneau"
