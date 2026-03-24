"""
Prefect workflow for extracting Dutch water company data from Vewin's ArcGIS services.
Fetches company names and service area geometries, then writes staging tables for
water companies and distribution zones into DuckDB.
"""

import json
from pathlib import Path

import httpx
from prefect import flow, get_run_logger, task
import shapely
from shapely.geometry import MultiPolygon

from pipelines.common import staging_db

LAYER_DEFINITION_API = (
    "https://www.arcgis.com/sharing/rest/content/items/"
    "277d87966ce842308506b74535376509/data?f=json"
)

GEOJSON_URL = (
    "https://services5.arcgis.com/ZcRj7hEl3ya9tYHV/arcgis/rest/services/"
    "Waterbedrijven_Nederland/FeatureServer/0/query"
)


@task(name="extract_nl_vewin_companies")
def get_companies() -> list[str]:
    """Fetch water company names from the Vewin layer definition."""
    logger = get_run_logger()
    response = httpx.get(LAYER_DEFINITION_API, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    companies = []
    for layer in data.get("operationalLayers", []):
        if layer["title"] == "Waterbedrijven":
            infos = layer["layerDefinition"]["drawingInfo"]["renderer"]["uniqueValueInfos"]
            companies = [info["value"] for info in infos]
            break

    logger.info(f"Found {len(companies)} companies from Vewin")
    return companies


@task(name="extract_nl_vewin_geometry")
def get_geometry(name: str) -> dict:
    """Fetch geometry and contact info for a single company."""
    params = {
        "where": f"Naam='{name}'",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "pgeojson",
    }
    response = httpx.get(GEOJSON_URL, params=params, timeout=30.0)
    response.raise_for_status()
    features = response.json()["features"]

    info = {
        "Name": features[0]["properties"]["Naam"],
        "Phone": features[0]["properties"]["Telefoonnummer"],
    }

    if len(features) == 1:
        info["Geometry"] = json.dumps(features[0]["geometry"])
    else:
        geometries = [
            shapely.from_geojson(json.dumps(f["geometry"])) for f in features
        ]
        info["Geometry"] = shapely.to_geojson(MultiPolygon(geometries))

    return info


@flow(name="extract_nl_vewin", persist_result=True)
def extract_nl_vewin(data_directory: Path = Path("data")):
    """Extract Dutch water companies and distribution zones into staging DuckDB."""
    logger = get_run_logger()
    companies_list = get_companies()

    water_companies = []
    distribution_zones = []

    for company_name in companies_list:
        row = get_geometry(company_name)
        water_companies.append({
            "Name": row["Name"],
            "CountryCode": "NL",
            "Source": "Vewin",
            "Website": "",
            "Phone": row["Phone"],
            "Email": "",
            "Description": "",
        })
        distribution_zones.append({
            "Code": row["Name"],
            "Name": row["Name"],
            "CountryCode": "NL",
            "Municipalities": json.dumps([]),
            "Geometry": row["Geometry"],
        })

    conn = staging_db.get_connection(data_directory)
    try:
        staging_db.write_table(conn, "WaterCompany_nl_vewin", water_companies)
        staging_db.write_table(conn, "DistributionZone_nl_vewin", distribution_zones)
        logger.info(
            f"Wrote {len(water_companies)} companies and "
            f"{len(distribution_zones)} zones to staging"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    extract_nl_vewin(Path("data"))
