Workflows that process data from `data/raw` into `data/staging`.

Use `just pipelines transform-all` to run all transform steps in the correct dependency order.

# geojson (import_all_geojson)

Transforms raw GeoJSON files into staging zone records ready for loading. Imports Municipality data filtered to configured European countries. Property mapping per level is defined in `config.py`.

Output: `staging.Municipality` table.

# dissolve_countries

Dissolves municipality geometries by country code to produce country polygons. This ensures country borders exactly match zone borders built from the same municipality geometries. Requires `staging.Municipality` (from geojson) and `raw.Country` (from extract_countries).

Output: `staging.Country` table.

# create_distribution_zones

Reads water company NDJSON files from `data/raw` and creates one distribution zone per company (1:1 mapping), with linked municipality codes.

Output: `data/staging/DistributionZone_from_water_companies.ndjson`.