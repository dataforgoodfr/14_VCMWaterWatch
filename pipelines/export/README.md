Workflows that will process data from NocoDB and save it into the export folder.

# export_pmtiles

Export zone tables (Country, and later DistributionZone) from NocoDB as PMTiles files.

1. Reads zone records and writes a GeoJSON FeatureCollection per table to `data/staging`.
2. Converts each GeoJSON file to a PMTiles archive in `data/export` using [tippecanoe](https://github.com/felt/tippecanoe).

Each zone table maps to a layer name (configured in `ZONE_TABLES`), which determines both the vector-tile layer name and the output filename (`<layer>.pmtiles`).

| Zone Table | Layer Name       | Output File                |
|------------|------------------|----------------------------|
| Country    | data_countries   | data_countries.pmtiles     |
