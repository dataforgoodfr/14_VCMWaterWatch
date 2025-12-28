import json
import httpx
from prefect.cache_policies import INPUTS
from shapely.geometry import shape
from prefect import flow, get_run_logger, task
import polars as pl

from pipelines.common import services


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
    url = f"https://api.wasserportal.info/api/public/findgebiet?latitude={lat}&longitude={lon}"
    response = httpx.get(url)
    response.raise_for_status()
    if response.status_code == 204:
        get_run_logger().info(
            f"No company found for latitude {lat} and longitude {lon}"
        )
        return None
    data = response.json()
    company = data.get("versorger")
    if not company:
        get_run_logger().info(f"Invalid response format for latitude {lat} and longitude {lon}: {data}")
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
    for row in municipalities_df.iter_rows(named=True):
        geometry = json.loads(row["Geometry"])
        poly = shape(geometry)
        center = poly.centroid
        lat, lon = center.y, center.x
        water_company = get_water_company(lat, lon)
        if water_company:
            companies.append({**water_company, "Municipality": row["Name"]})
    return pl.DataFrame(companies)


@task(name="get_existing_de_municipalities")
def get_existing_de_municipalities_task(country_code: str) -> pl.DataFrame:
    """
    Get existing DE municipalities from the database.
    Return a dataframe with the following fields:
    - Code: str
    - Geometry: GeoJSON
    """
    db_helper = services.db_helper()
    country_df = db_helper.load_all_records(
        table_name="Country",
        fields=["Code", "Id"],
        condition={"Code": country_code},
    )
    if country_df.is_empty():
        raise ValueError(f"Country {country_code} not found")
    country_id = country_df.item(0, "Id")
    df = db_helper.load_all_records(
        table_name="Municipality",
        fields=["Name", "Geometry"],
        condition={"Country_id": country_id},
    )
    return df


@task(name="merge_water_companies")
def merge_water_companies_task(water_companies_df: pl.DataFrame) -> pl.DataFrame:
    """
    Group water companies by Name and aggregate all fields appropriately.
    Municipalities field should be a list of municipality names.
    """
    print(water_companies_df)
    return water_companies_df.group_by("Name").agg(
        [
            pl.col("Phone").first(),
            pl.col("Email").first(),
            pl.col("Website").first(),
            pl.col("Description").first(),
            pl.col("Municipality").alias("Municipalities"),
        ]
    ).with_columns(
        pl.col("Municipalities").list.join(";").alias("Municipalities")
    )


@task(name="write_to_csv")
def write_to_csv_task(df: pl.DataFrame, file_path: str) -> None:
    """Write dataframe to CSV file"""
    df.write_csv(file_path)


# @task(name="insert_water_companies")
# def insert_water_companies_task(companies_df: pl.DataFrame, db_helper: DatabaseHelper) -> None:
#     """
#     Insert water companies into the database.
#     """
#     db_helper.insert_records(companies_df, table_name="Actor")
@flow(name="download_de_wasserportal", persist_result=True)
def download_de_wasserportal():
    municipalities_df = get_existing_de_municipalities_task("DE")
    water_companies_df = get_water_companies_task(municipalities_df)
    water_companies_df = merge_water_companies_task(water_companies_df)
    write_to_csv_task(water_companies_df, "data/de_water_companies.csv")


if __name__ == "__main__":
    download_de_wasserportal()
