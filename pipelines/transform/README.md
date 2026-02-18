Workflows that process data from `data/raw` into `data/staging`.

# geojson (import_all_geojson)

Transforms raw GeoJSON files into NDJSON zone records ready for loading. Imports Country data first, then Municipality data (filtered to configured European countries). Property mapping per level is defined in `config.py`.

Output: `data/staging/Country.ndjson`, `data/staging/Municipality.ndjson`.

# create_distribution_zones

Reads water company NDJSON files from `data/raw` and creates one distribution zone per company (1:1 mapping), with linked municipality codes.

Output: `data/staging/DistributionZone_from_water_companies.ndjson`.