"""
Prefect workflow for downloading data from DE WasserPortal API.
Uses the data in data/staging/Municipality.ndjson to get the latitude and longitude of the municipalities.
Then uses the DE WasserPortal API to get the water company for each municipality.
The data is saved as JSON (line delimited) in data/staging/WaterCompany_de_wasserportal.ndjson.
"""

import json
from pathlib import Path
import httpx
from prefect.cache_policies import INPUTS, NO_CACHE
from shapely.geometry import shape
from prefect import flow, get_run_logger, task
from prefect.concurrency.sync import rate_limit
import polars as pl


@task(name="get_water_company", cache_policy=INPUTS)
def get_water_company(lat: float, lon: float) -> dict | None:
    """
    Uses DE WasserPortal API to get the water company for a given latitude and longitude.
    Return a dict with the following fields:
     - Name: str (from "bezeichnung" field)
     - Phone: str (from "telefonBuero" field)
     - Email: str (from "email" field)
     - Website: str (from "www" field)
     - Description: str (from "beschreibung" field)

    If there is no company (status code 204), return None.
    """
    # Configure rate limit via prefect gcl on the CLI
    rate_limit("water-api")
    url = f"https://api.wasserportal.info/api/public/findgebiet?latitude={lat}&longitude={lon}"
    get_run_logger().info(url)
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    # time.sleep(2)
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


@task(name="get_water_companies")
def get_water_companies_task(municipalities_df: pl.DataFrame) -> pl.DataFrame:
    """
    Retrieve water companies for the municipalities in the dataframe.
    Return a dataframe with the following fields:
    - Name: str
    - Phone: str
    - Email: str
    - Website: str
    - Description: str
    - Municipality: str
    """
    companies = []
    count = len(municipalities_df)
    for i, row in enumerate(municipalities_df[0:305].iter_rows(named=True)):
        get_run_logger().info(
            f"Processing municipality {i+1} of {count}: {row['Name']}"
        )
        geometry = json.loads(row["Geometry"])
        poly = shape(geometry)
        center = poly.centroid
        lat, lon = center.y, center.x
        water_company = get_water_company(lat, lon)
        if water_company:
            companies.append({**water_company, "Municipality": row["Name"]})
    return pl.DataFrame(companies)


@task(name="get_existing_de_municipalities")
def get_existing_de_municipalities_task(
    country_code: str, data_directory: Path
) -> pl.DataFrame:
    """
    Get existing DE municipalities from the database.
    Return a dataframe with the following fields:
    - Code: str
    - Name: str
    - Geometry: GeoJSON
    """
    return pl.read_ndjson(data_directory / "staging" / "Municipality.ndjson").filter(
        pl.col("CountryCode") == country_code
    )


@task(name="merge_water_companies", cache_policy=NO_CACHE)
def merge_water_companies_task(water_companies_df: pl.DataFrame) -> pl.DataFrame:
    """
    Group water companies by Name and aggregate all fields appropriately.
    Municipalities field should be a list of municipality names.
    """
    return water_companies_df.group_by("Name").agg(
        [
            pl.col("Phone").first(),
            pl.col("Email").first(),
            pl.col("Website").first(),
            pl.col("Description").first(),
            pl.lit("WasserPortal").alias("Source"),
            pl.lit("DE").alias("CountryCode"),
            pl.col("Municipality").alias("Municipalities"),
        ]
    )


@flow(name="download_de_wasserportal", persist_result=True)
def download_de_wasserportal(data_directory: Path):
    municipalities_df = get_existing_de_municipalities_task("DE", data_directory)
    # Submit all water company lookups as independent tasks
    companies = []
    count = len(municipalities_df)
    for i, row in enumerate(municipalities_df.iter_rows(named=True)):
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

    water_companies_df = pl.DataFrame(companies)
    water_companies_df = merge_water_companies_task(water_companies_df)
    water_companies_df.write_ndjson(
        data_directory / "raw" / "WaterCompany_de_wasserportal.ndjson"
    )


if __name__ == "__main__":
    download_de_wasserportal(Path("data"))
