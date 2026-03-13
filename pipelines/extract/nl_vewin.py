import json
from pathlib import Path
import httpx
from prefect import flow, task
import polars as pl
from shapely.geometry import MultiPolygon
import shapely

layer_definition_api = "https://www.arcgis.com/sharing/rest/content/items/277d87966ce842308506b74535376509/data?f=json"

@task(name="get_companies_task")
def get_companies_task() -> list:
    """
    Uses vewin.nl to get water companies.

    Returns a list with all companies' names.
    """
    url = layer_definition_api
    #get_run_logger().info(url)
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    companies_list = []
    companies_info = data.get("operationalLayers")
    for layer in companies_info:
        if layer["title"] == "Waterbedrijven":
            info_list = layer["layerDefinition"]["drawingInfo"]["renderer"]["uniqueValueInfos"]
            for info in info_list:
                companies_list.append(info["value"])
    return companies_list

geojson_url = "https://services5.arcgis.com/ZcRj7hEl3ya9tYHV/arcgis/rest/services/Waterbedrijven_Nederland/FeatureServer/0/query"

@task(name="get_geometry_task")
def get_geometry_task(name: str) -> dict:
    params = {
    "where": f"Naam='{name}'",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "pgeojson"
    }
    
    #get_run_logger().info(geojson_url)
    response = httpx.get(geojson_url, params=params, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    features = data["features"]
    company_info = {"Name": features[0]["properties"]["Naam"],
                    "Phone": features[0]["properties"]["Telefoonnummer"]}
    if len(features) == 1:
        company_info["Geometry"] = json.dumps(features[0]["geometry"])
    else:
        geometries = []
        for feature in features:
            geometries.append(shapely.from_geojson(json.dumps(feature["geometry"])))
        print(type(geometries), type(geometries[0]))
        company_info["Geometry"] = shapely.to_geojson(MultiPolygon(geometries))
    print("Type Geometry", type(company_info["Geometry"]))
    return company_info

@flow(name="save_distribution_zones_and_water_companies_task")
def save_distribution_zones_and_water_companies(path: Path):
    companies = get_companies_task()
    distribution_zones = []
    water_companies = []
    for company in companies:
        row = get_geometry_task(company)
        row_dz = {"Code": row["Name"],
                  "CountryCode": "NL",
                  "Municipalities": [],
                  "Geometry": row["Geometry"]}
        distribution_zones.append(row_dz)
        row_wc = {"Name": row["Name"],
                  "CountryCode": "NL",
                  "Source": "Vewin",
                  "Website": "",
                  "Phone": row["Phone"],
                  "Email": "",
                  "Description": ""}
        water_companies.append(row_wc)
    distribution_zones_df = pl.DataFrame(distribution_zones)
    distribution_zones_df.write_ndjson(path / "staging" / "DistributionZone_nl.ndjson")
    water_companies_df = pl.DataFrame(water_companies)
    water_companies_df.write_ndjson(path / "staging" / "WaterCompany_nl.ndjson")

if __name__=="__main__":
    save_distribution_zones_and_water_companies(Path("data"))
