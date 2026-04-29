"""
Prefect workflow for building France staging tables from the dansmoneau DuckDB
and the Outline raw samples.

Produces:
  staging.DistributionZone_fr   – UDI zones with geometry
  staging.WaterCompany_fr       – operators (most-recent distrlib per UDI)
  staging.Analysis_fr_dansmoneau – individual CVM samples from dansmoneau (2023+)
  staging.Analysis_fr_outline    – individual CVM samples from Outline, commune-exploded
  staging.Analysis_fr            – deduped union (dansmoneau preferred)

Logs unmatched Outline communes (inseecommune IS NULL) for review.
"""

from pathlib import Path

import duckdb
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db

DANSMONEAU_FILE = "fr_dansmoneau.duckdb"
MUNICIPALITIES_GEOJSON = "municipalities.geojson"


def _get_dmeau_path(data_directory: Path) -> Path:
    return data_directory / "raw" / DANSMONEAU_FILE


@task(name="fr_build_insee_comm_map", cache_policy=NO_CACHE)
def build_insee_comm_map(conn: duckdb.DuckDBPyConnection, data_directory: Path) -> int:
    """Build a temp table mapping GISCO ``NSI_CODE`` (INSEE) to ``COMM_ID``.

    Dansmoneau stores communes by INSEE code (e.g. ``07148``) but the NocoDB
    Municipality table uses GISCO's ``COMM_ID`` (e.g. ``FR11907148``).  We load
    the GeoJSON once and register the FR-only mapping as a temp table so the
    subsequent build queries can translate via a simple join.
    """
    import json

    logger = get_run_logger()
    geojson_path = data_directory / "raw" / MUNICIPALITIES_GEOJSON
    if not geojson_path.exists():
        logger.warning(
            f"{geojson_path} not found; skipping INSEE→COMM_ID map (FR zones will"
            " not be linked to municipalities).  Run 'just extract-municipalities'"
            " + 'just transform-geojson' first."
        )
        conn.execute(
            "CREATE OR REPLACE TEMP TABLE _fr_insee_to_comm (insee VARCHAR, comm_id VARCHAR)"
        )
        return 0

    with open(geojson_path, "r") as fh:
        geo = json.load(fh)

    rows = [
        (p.get("NSI_CODE"), p.get("COMM_ID"))
        for feat in geo.get("features", [])
        for p in [feat.get("properties", {})]
        if p.get("CNTR_CODE") == "FR" and p.get("NSI_CODE") and p.get("COMM_ID")
    ]
    import pandas as pd
    df = pd.DataFrame(rows, columns=["insee", "comm_id"])
    conn.execute("CREATE OR REPLACE TEMP TABLE _fr_insee_to_comm AS SELECT * FROM df")
    logger.info(f"INSEE→COMM_ID map: {len(df)} FR communes")
    return len(df)


def _attach_dansmoneau(conn: duckdb.DuckDBPyConnection, dmeau_path: Path) -> None:
    """Attach the dansmoneau DuckDB as a read-only database named 'data'.

    The upstream file (data.duckdb) was built with 'data' as its internal
    catalog name.  DuckDB 1.x does not remap internal catalog references when
    attaching with a different alias, so we must preserve the original name.
    """
    # Install spatial extension for geometry support
    conn.execute("INSTALL spatial; LOAD spatial;")
    conn.execute(f"ATTACH '{dmeau_path}' AS data (READ_ONLY)")


@task(name="fr_build_distribution_zones", cache_policy=NO_CACHE)
def build_distribution_zones(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.DistributionZone_fr from dansmoneau UDI tables."""
    logger = get_run_logger()
    conn.execute("""
        CREATE OR REPLACE TABLE staging."DistributionZone_fr" AS
        WITH exploded AS (
            SELECT
                u.cdreseau,
                u.nomreseaux,
                unnest(str_split(u.inseecommunes, ',')) AS insee
            FROM data.main.int__udi u
            WHERE u.cdreseau IS NOT NULL
        ),
        mapped AS (
            SELECT e.cdreseau,
                   any_value(e.nomreseaux) AS nomreseaux,
                   list(m.comm_id) FILTER (WHERE m.comm_id IS NOT NULL) AS comm_ids
            FROM exploded e
            LEFT JOIN _fr_insee_to_comm m ON m.insee = e.insee
            GROUP BY e.cdreseau
        )
        SELECT
            m.cdreseau   AS "Code",
            COALESCE(m.nomreseaux, m.cdreseau) AS "Name",
            'FR'         AS "CountryCode",
            'Distribution' AS "Type",
            m.comm_ids   AS "Municipalities",
            g.geom::VARCHAR AS "Geometry"
        FROM mapped m
        LEFT JOIN data.main.int__udi_geom g ON m.cdreseau = g.code_udi
    """)
    count = conn.execute('SELECT count(*) FROM staging."DistributionZone_fr"').fetchone()[0]
    logger.info(f"DistributionZone_fr: {count} zones")
    return count


@task(name="fr_build_water_companies", cache_policy=NO_CACHE)
def build_water_companies(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.WaterCompany_fr from dansmoneau edc_prelevements."""
    logger = get_run_logger()
    conn.execute("""
        CREATE OR REPLACE TABLE staging."WaterCompany_fr" AS
        WITH latest AS (
            SELECT
                cdreseau,
                distrlib,
                ROW_NUMBER() OVER (PARTITION BY cdreseau ORDER BY dateprel DESC) AS rn
            FROM data.main.edc_prelevements
            WHERE de_partition >= 2023
              AND distrlib IS NOT NULL
              AND cdreseau IS NOT NULL
        )
        SELECT
            distrlib       AS "Name",
            'FR'           AS "CountryCode",
            list(cdreseau) AS "DistributionZones"
        FROM latest
        WHERE rn = 1
        GROUP BY distrlib
    """)
    count = conn.execute('SELECT count(*) FROM staging."WaterCompany_fr"').fetchone()[0]
    logger.info(f"WaterCompany_fr: {count} operators")
    return count


@task(name="fr_build_analysis_dansmoneau", cache_policy=NO_CACHE)
def build_analysis_dansmoneau(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.Analysis_fr_dansmoneau from dansmoneau CVM samples."""
    logger = get_run_logger()
    conn.execute("""
        CREATE OR REPLACE TABLE staging."Analysis_fr_dansmoneau" AS
        SELECT
            cdreseau                       AS "DistributionZoneCode",
            inseecommune                   AS "MunicipalityCode",
            CAST(datetimeprel AS DATE)     AS "Date",
            CAST(valtraduite AS DOUBLE)    AS "CVMMeasure",
            'dansmoneau'                   AS "Source",
            referenceprel                  AS "SourceRef"
        FROM data.main.int__resultats_udi_communes
        WHERE categorie = 'cvm'
          AND de_partition >= 2023
          AND valtraduite IS NOT NULL
          AND cdreseau IS NOT NULL
    """)
    count = conn.execute('SELECT count(*) FROM staging."Analysis_fr_dansmoneau"').fetchone()[0]
    logger.info(f"Analysis_fr_dansmoneau: {count} rows")
    return count


@task(name="fr_build_analysis_outline", cache_policy=NO_CACHE)
def build_analysis_outline(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.Analysis_fr_outline from Outline samples, exploded to communes."""
    logger = get_run_logger()

    # Check that raw.outline_cvm_samples exists
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_catalog = 'raw' AND table_name = 'outline_cvm_samples'"
    ).fetchall()
    if not tables:
        logger.warning("raw.outline_cvm_samples not found; skipping Outline analysis build")
        conn.execute('''CREATE OR REPLACE TABLE staging."Analysis_fr_outline" (
            "DistributionZoneCode" VARCHAR,
            "MunicipalityCode"     VARCHAR,
            "Date"                 DATE,
            "CVMMeasure"           DOUBLE,
            "Source"               VARCHAR,
            "SourceRef"            VARCHAR
        )''')
        return 0

    # Resolve commune names via COG, then explode to UDIs
    max_partition = conn.execute(
        "SELECT max(de_partition) FROM data.main.cog_communes"
    ).fetchone()[0]

    conn.execute(f"""
        CREATE OR REPLACE TABLE staging._outline_resolved AS
        SELECT s.*, c.COM AS inseecommune
        FROM raw.outline_cvm_samples s
        LEFT JOIN data.main.cog_communes c
          ON c.DEP  = s.dept
         AND c.NCC  = s.commune_name_norm
         AND c.TYPECOM = 'COM'
         AND c.de_partition = {max_partition}
    """)

    unmatched = conn.execute(
        "SELECT count(*) FROM staging._outline_resolved WHERE inseecommune IS NULL"
    ).fetchone()[0]
    if unmatched:
        logger.warning(f"{unmatched} Outline rows could not be matched to a COG commune")
        sample = conn.execute(
            "SELECT dept, commune_name_raw, commune_name_norm FROM staging._outline_resolved "
            "WHERE inseecommune IS NULL LIMIT 20"
        ).fetchdf()
        logger.warning(f"Sample unmatched:\n{sample.to_string()}")

    conn.execute("""
        CREATE OR REPLACE TABLE staging."Analysis_fr_outline" AS
        WITH exploded AS (
            SELECT
                u.cdreseau,
                u.inseecommune,
                r.plv_date,
                r.value_ugl,
                r.source_file
            FROM staging._outline_resolved r
            JOIN (
                SELECT cdreseau, unnest(str_split(inseecommunes, ',')) AS inseecommune
                FROM data.main.int__udi
            ) u USING (inseecommune)
            WHERE r.inseecommune IS NOT NULL
              AND r.value_ugl IS NOT NULL
        )
        SELECT
            cdreseau   AS "DistributionZoneCode",
            inseecommune AS "MunicipalityCode",
            plv_date   AS "Date",
            value_ugl  AS "CVMMeasure",
            'outline'  AS "Source",
            source_file AS "SourceRef"
        FROM exploded
    """)
    count = conn.execute('SELECT count(*) FROM staging."Analysis_fr_outline"').fetchone()[0]
    logger.info(f"Analysis_fr_outline: {count} rows")
    return count


@task(name="fr_build_analysis_dedup", cache_policy=NO_CACHE)
def build_analysis_dedup(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.Analysis_fr as a deduped union (dansmoneau preferred)."""
    logger = get_run_logger()
    conn.execute("""
        CREATE OR REPLACE TABLE staging."Analysis_fr" AS
        SELECT DISTINCT ON (
            "DistributionZoneCode",
            "MunicipalityCode",
            "Date",
            round("CVMMeasure", 2)
        )
            "DistributionZoneCode",
            "MunicipalityCode",
            "Date",
            "CVMMeasure",
            "Source",
            "SourceRef"
        FROM (
            SELECT *, 1 AS priority FROM staging."Analysis_fr_dansmoneau"
            UNION ALL
            SELECT *, 2 AS priority FROM staging."Analysis_fr_outline"
            WHERE "DistributionZoneCode" IS NOT NULL
        )
        ORDER BY
            "DistributionZoneCode",
            "MunicipalityCode",
            "Date",
            round("CVMMeasure", 2),
            priority
    """)
    count = conn.execute('SELECT count(*) FROM staging."Analysis_fr"').fetchone()[0]
    logger.info(f"Analysis_fr (deduped): {count} rows")
    return count


@flow(name="fr_build", persist_result=False)
def fr_build(data_directory: Path = Path("data")) -> None:
    """Build all France staging tables from dansmoneau + Outline sources."""
    logger = get_run_logger()
    dmeau_path = _get_dmeau_path(data_directory)
    if not dmeau_path.exists():
        raise FileNotFoundError(
            f"dansmoneau DuckDB not found at {dmeau_path}. "
            "Run 'just extract-fr-dansmoneau' first."
        )

    conn = staging_db.get_connection(data_directory)
    try:
        _attach_dansmoneau(conn, dmeau_path)
        build_insee_comm_map(conn, data_directory)
        build_distribution_zones(conn)
        build_water_companies(conn)
        build_analysis_dansmoneau(conn)
        build_analysis_outline(conn)
        build_analysis_dedup(conn)
    finally:
        conn.close()

    logger.info("France staging tables built successfully")


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    fr_build(data_directory)
