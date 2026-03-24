# Extract UK Ofwat Water Companies

## Goal

Create an extract pipeline that reads `data/raw/uk_ofwat_streamwaterdata.geojson` (432 polygon features for UK water company service areas) and writes staging DuckDB tables consumable by the existing `load_zones` and `load_water_companies` pipelines.

## Source Data

- **File**: `data/raw/uk_ofwat_streamwaterdata.geojson` (~44MB, 432 features)
- **27 unique companies** (by `COMPANY` field), some with name variants (e.g. "Icosa Water Services Limited" vs "Ltd")
- Properties: `COMPANY`, `Acronym`, `CoType`, `AreaType`, `AreaServed`, `ID`, `FID`
- Geometry: Polygons defining served areas (multiple per company)

## Proposed Changes

### New file: `pipelines/extract/uk_ofwat.py`

Prefect flow that:

1. Reads the GeoJSON with DuckDB's spatial extension (`ST_Read` or load via json + shape)
2. Deduplicates company names — normalize variants:
   - "Icosa Water Services Limited" → "Icosa Water Services Ltd"
   - "Leep Networks (Water) Ltd (formerly SSE Water Ltd)" → "Leep Networks (Water) Ltd"
   - "Leep Networks (Water) Ltd (formerly Peel Water Networks Ltd)" → "Leep Networks (Water) Ltd"
   - "Leep Networks (Water) Limited (formerly SSE Water Ltd)" → "Leep Networks (Water) Ltd"
   - "Northumbrian Water Limited" → "Northumbrian Water"
3. Writes `staging.WaterCompany_uk_ofwat` with fields:
   - `Name` — normalized company name
   - `CountryCode` — `"GB"`
   - `Phone` — `""`
   - `Email` — `""`
   - `Website` — `""`
   - `Description` — `CoType` value (e.g. "regional water and sewerage company")
   - `Source` — `"Ofwat"`
4. Writes `staging.DistributionZone_uk_ofwat` with fields:
   - `Code` — normalized company name (matches WaterCompany `Name`, as per existing convention)
   - `Name` — normalized company name
   - `CountryCode` — `"GB"`
   - `Municipalities` — `[]` (empty; no municipality linkage in source data)

### No changes to existing load pipelines

`load_zones_flow(level="DistributionZone")` and `load_water_companies()` already pick up all `DistributionZone*` and `WaterCompany*` tables from staging.

## Decisions

- **Municipality linkage** — Out of scope; spatial join against municipalities is a follow-up. `Municipalities` field will be `[]`.
- **Country code** — Use `GB` (combine England and Wales).
- **Company name normalization** — Hardcoded mapping as described above.
- **Geometry storage** — The existing transform layer (`transform/geojson.py`) already produces a `Geometry` field (JSON string) and `load_zones` passes all staging fields through to NocoDB. The extract script should merge all polygons per company into a single MultiPolygon GeoJSON string and include it as a `Geometry` field on the DistributionZone staging table. This will flow through to NocoDB automatically.
