"""
Prefect workflow for downloading data from DE WasserPortal API.
Uses the data in staging.Municipality to get the latitude and longitude of the municipalities.
Then uses the DE WasserPortal API to get the water company for each municipality.
The data is saved to raw.WaterCompany_de_wasserportal.
"""

import json
from pathlib import Path
import httpx
from prefect.cache_policies import INPUTS, NO_CACHE
from shapely.geometry import shape
from prefect import flow, get_run_logger, task
from prefect.concurrency.sync import rate_limit

from pipelines.common import staging_db


@task(name="get_water_company", cache_policy=INPUTS)
def get_water_company(lat: float, lon: float) -> dict | None:
    """
    Uses DE WasserPortal API to get the water company for a given latitude and longitude.
    """
    rate_limit("water-api")
    url = f"https://api.wasserportal.info/api/public/findgebiet?latitude={lat}&longitude={lon}"
    get_run_logger().info(url)
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    if response.status_code == 204:
        get_run_logger().info(
            f"No company found for latitude {lat} and longitude {lon}"
        )
        return None
    data = response.json()
    company = data.get("versorger")
    if not company:
        get_run_logger().info(
            f"Invalid response format for latitude {lat} and longitude {lon}: {data}"
        )
        return None
    return {
        "Name": company["bezeichnung"],
        "Phone": company["telefonBuero"],
        "Email": company["email"],
        "Website": company["www"],
        "Description": company["beschreibung"],
    }


@task(name="get_existing_de_municipalities")
def get_existing_de_municipalities_task(
    country_code: str, conn
) -> list[dict]:
    """
    Get existing DE municipalities from staging DB.
    """
    rel = conn.sql(
        f"SELECT * FROM staging.Municipality WHERE CountryCode = '{country_code}'"
    )
    return rel.fetchdf().to_dict("records")


@task(name="merge_water_companies", cache_policy=NO_CACHE)
def merge_water_companies_task(conn, companies: list[dict]) -> list[dict]:
    """
    Group water companies by Name and aggregate all fields appropriately.
    """
    staging_db.register_temp(conn, "raw_companies", companies)
    result = conn.sql("""
        SELECT
            Name,
            first(Phone) AS Phone,
            first(Email) AS Email,
            first(Website) AS Website,
            first(Description) AS Description,
            'WasserPortal' AS Source,
            'DE' AS CountryCode,
            list(Municipality) AS Municipalities
        FROM raw_companies
        GROUP BY Name
    """)
    return result.fetchdf().to_dict("records")


@flow(name="download_de_wasserportal", persist_result=True)
def download_de_wasserportal(data_directory: Path):
    conn = staging_db.get_connection(data_directory)
    try:
        municipalities = get_existing_de_municipalities_task("DE", conn)
        companies = []
        count = len(municipalities)
        for i, row in enumerate(municipalities):
            get_run_logger().info(
                f"Processing municipality {i+1} of {count}: {row['Name']}"
            )
            geometry = json.loads(row["Geometry"])
            poly = shape(geometry)
            center = poly.centroid
            lat, lon = center.y, center.x
            muni = get_water_company(lat, lon)
            if muni:
                companies.append({**muni, "Municipality": row["Code"]})

        merged = merge_water_companies_task(conn, companies)
        staging_db.write_table(
            conn, "WaterCompany_de_wasserportal", merged, schema="raw"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    download_de_wasserportal(Path("data"))
