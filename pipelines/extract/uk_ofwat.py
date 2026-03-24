"""
Prefect workflow for extracting UK Ofwat water company data from a GeoJSON file.
Reads data/raw/uk_ofwat_streamwaterdata.geojson (432 polygon features for UK water
company service areas) and writes staging tables for water companies and distribution zones.
"""

import json
from pathlib import Path

import duckdb
from prefect import flow, get_run_logger, task

from pipelines.common import staging_db

# Normalize company name variants
_NAME_MAP = {
    "Icosa Water Services Limited": "Icosa Water Services Ltd",
    "Leep Networks (Water) Ltd (formerly SSE Water Ltd)": "Leep Networks (Water) Ltd",
    "Leep Networks (Water) Ltd (formerly Peel Water Networks Ltd)": "Leep Networks (Water) Ltd",
    "Leep Networks (Water) Limited (formerly SSE Water Ltd)": "Leep Networks (Water) Ltd",
    "Northumbrian Water Limited": "Northumbrian Water",
}


def _normalize(name: str) -> str:
    return _NAME_MAP.get(name, name)


@task(name="extract_uk_ofwat_companies")
def extract_companies_and_zones(data_directory: Path) -> tuple[list[dict], list[dict]]:
    """Read GeoJSON, produce water company and distribution zone records."""
    logger = get_run_logger()
    geojson_path = data_directory / "raw" / "uk_ofwat_streamwaterdata.geojson"

    conn = duckdb.connect()
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    rows = conn.sql(f"""
        SELECT
            COMPANY,
            CoType,
            ST_AsGeoJSON(geom) AS geojson
        FROM ST_Read('{geojson_path}')
    """).fetchall()
    conn.close()

    # Group polygons by normalized company name
    from collections import defaultdict
    company_polygons: dict[str, list] = defaultdict(list)
    company_cotype: dict[str, str] = {}

    for company, cotype, geojson_str in rows:
        name = _normalize(company)
        geom = json.loads(geojson_str)
        # Collect all coordinate sets
        if geom["type"] == "Polygon":
            company_polygons[name].append(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            company_polygons[name].extend(geom["coordinates"])
        if name not in company_cotype:
            company_cotype[name] = cotype

    logger.info(f"Found {len(company_polygons)} unique companies")

    companies = []
    zones = []
    for name in sorted(company_polygons):
        companies.append({
            "Name": name,
            "CountryCode": "GB",
            "Phone": "",
            "Email": "",
            "Website": "",
            "Description": company_cotype[name],
            "Source": "Ofwat",
        })
        multi = {
            "type": "MultiPolygon",
            "coordinates": company_polygons[name],
        }
        zones.append({
            "Code": name,
            "Name": name,
            "CountryCode": "GB",
            "Municipalities": json.dumps([]),
            "Geometry": json.dumps(multi),
        })

    return companies, zones


@flow(name="extract_uk_ofwat", persist_result=True)
def extract_uk_ofwat(data_directory: Path = Path("data")):
    companies, zones = extract_companies_and_zones(data_directory)

    conn = staging_db.get_connection(data_directory)
    try:
        staging_db.write_table(conn, "WaterCompany_uk_ofwat", companies)
        staging_db.write_table(conn, "DistributionZone_uk_ofwat", zones)
        get_run_logger().info(
            f"Wrote {len(companies)} companies and {len(zones)} zones to staging"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    extract_uk_ofwat(Path("data"))
