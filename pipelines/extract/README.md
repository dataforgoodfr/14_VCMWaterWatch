Workflows that download and parse raw data into the `data/raw` folder.

# extract_countries

Writes hardcoded European country metadata (Code, Name) into `raw.Country`. No download required — the country list is maintained in `pipelines/transform/config.py`. Country geometries are dissolved from municipality boundaries in the transform step (`dissolve_countries`).

# download_municipalities

Downloads the EU commune GPKG from GISCO, reprojects to EPSG:4326, and writes `data/raw/municipalities.geojson`.

# de_wasserportal

Queries the DE WasserPortal API to find the water company serving each German municipality (by centroid lat/lon). Groups results by company and writes `data/raw/WaterCompany_de_wasserportal.ndjson`.

Output fields per record: Name, Phone, Email, Website, Description, Source (`WasserPortal`), CountryCode, Municipalities (list of codes).
