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


def _get_dmeau_path(data_directory: Path) -> Path:
    return data_directory / "raw" / DANSMONEAU_FILE


def _attach_dansmoneau(conn: duckdb.DuckDBPyConnection, dmeau_path: Path) -> None:
    """Attach the dansmoneau DuckDB as a read-only database named 'dmeau'."""
    # Install spatial extension for geometry support
    conn.execute("INSTALL spatial; LOAD spatial;")
    conn.execute(f"ATTACH '{dmeau_path}' AS dmeau (READ_ONLY)")


@task(name="fr_build_distribution_zones", cache_policy=NO_CACHE)
def build_distribution_zones(conn: duckdb.DuckDBPyConnection) -> int:
    """Materialize staging.DistributionZone_fr from dansmoneau UDI tables."""
    logger = get_run_logger()
    conn.execute("""
        CREATE OR REPLACE TABLE staging."DistributionZone_fr" AS
        SELECT
            u.cdreseau   AS "Code",
            COALESCE(u.nomreseaux, u.cdreseau) AS "Name",
            'FR'         AS "CountryCode",
            'Distribution' AS "Type",
            str_split(u.inseecommunes, ',') AS "Municipalities",
            ST_AsGeoJSON(g.geom) AS "Geometry"
        FROM dmeau.main.int__udi u
        LEFT JOIN dmeau.main.int__udi_geom g USING (cdreseau)
        WHERE u.cdreseau IS NOT NULL
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
                ROW_NUMBER() OVER (PARTITION BY cdreseau ORDER BY datetimeprel DESC) AS rn
            FROM dmeau.main.edc_prelevements
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
        FROM dmeau.main.int__resultats_udi_communes
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
        conn.execute('CREATE OR REPLACE TABLE staging."Analysis_fr_outline" (dummy INTEGER)')
        return 0

    # Resolve commune names via COG, then explode to UDIs
    max_partition = conn.execute(
        "SELECT max(de_partition) FROM dmeau.main.cog_communes"
    ).fetchone()[0]

    conn.execute(f"""
        CREATE OR REPLACE TABLE staging._outline_resolved AS
        SELECT s.*, c.COM AS inseecommune
        FROM raw.outline_cvm_samples s
        LEFT JOIN dmeau.main.cog_communes c
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
                FROM dmeau.main.int__udi
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
