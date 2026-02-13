Workflows that download and parse raw data into the `data/raw` folder.

# download_municipalities

Downloads the EU commune GPKG from GISCO, reprojects to EPSG:4326, and writes `data/raw/municipalities.geojson`.

# de_wasserportal

Queries the DE WasserPortal API to find the water company serving each German municipality (by centroid lat/lon). Groups results by company and writes `data/raw/WaterCompany_de_wasserportal.ndjson`.

Output fields per record: Name, Phone, Email, Website, Description, Source (`WasserPortal`), CountryCode, Municipalities (list of codes).
