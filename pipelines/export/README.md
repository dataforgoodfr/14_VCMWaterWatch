Workflows that will process data from NocoDB and save it into the export folder.

# export_pmtiles

Export zone tables (Country, DistributionZone) from NocoDB as PMTiles files.

1. Reads zone records and writes a GeoJSON FeatureCollection per table to `data/staging`.
2. Converts each GeoJSON file to a PMTiles archive in `data/export` using [tippecanoe](https://github.com/felt/tippecanoe).

Each zone table maps to a layer name (configured in `ZONE_TABLES`), which determines both the vector-tile layer name and the output filename (`<layer>.pmtiles`).

| Zone Table       | Layer Name              | Output File                    |
|------------------|-------------------------|--------------------------------|
| Country          | data_countries          | data_countries.pmtiles          |
| DistributionZone | data_distribution_zones | data_distribution_zones.pmtiles |

DistributionZone features include a `company_name` property (from linked Actor records) when available.

# export_country_images

Mirror country profile images from NocoDB to a local directory so they can be
served from a stable, cache-friendly URL instead of short-lived S3 signed URLs.

## How it works

1. Reads all `Country` records from NocoDB (fields: `Id`, `Code`, `Image`).
2. For each country with at least one image attachment, downloads the first
   image using the `signedUrl` (server-side only — the signed URL is never
   exposed to end users).
3. Computes the first 8 hex characters of the SHA-256 hash of the image bytes
   to produce a cache-busting filename: `{code}.{hash}.{ext}`.
4. Writes each image to a staging directory, then atomically moves the files
   into the destination and writes `manifest.json` last.

## Output layout

```
<COUNTRY_IMAGES_DIR>/
    FR.a1b2c3d4.jpg
    IT.9f8e7d6c.png
    manifest.json          ← { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
```

The manifest is written **last**, so readers always see either a fully
consistent old set or a fully consistent new set — never a torn state.
Stale files (images whose hash changed or whose country was removed) are
deleted after the manifest swap.

## Webhook wiring

The `export_country_images` flow is triggered automatically by the worker
(`pipelines/worker/app.py`) whenever NocoDB fires a webhook for the `Country`
table.  It shares the same `_flow_run_lock` as the PMTiles export, so the two
flows are serialized — a `Country` change triggers both exports sequentially.

## Volume layout (production)

In production, `docker-compose.deploy.yml` defines a `country-images-data`
named volume that is mounted in two places:

| Service | Mount path               | Purpose                              |
|---------|--------------------------|--------------------------------------|
| worker  | `/public/country-images` | Flow writes images + manifest here   |
| webapp  | `/public/country-images` | Route handler reads files from here  |

The webapp service also has `COUNTRY_IMAGES_DIR=/public/country-images` set.
The route handler at `webapp/app/country-images/[...path]/route.ts` reads
files directly from `COUNTRY_IMAGES_DIR`, and `webapp/lib/countryImage.ts`
reads `manifest.json` (cached in module scope) to resolve
`code → /country-images/<file>`.

## Local development

A seed `manifest.json` is committed at `data/export/country-images/manifest.json`
so `pnpm dev` works without running the pipeline.  Set
`COUNTRY_IMAGES_DIR=../data/export/country-images` in `webapp/.env.local`
(already present in the committed file).  To refresh images locally:

```bash
just pipelines export-country-images
# or, with a custom destination:
COUNTRY_IMAGES_DIR=/tmp/ci uv run python -m pipelines.export.export_country_images
```

## Environment variables

| Variable             | Default                       | Description                              |
|----------------------|-------------------------------|------------------------------------------|
| `COUNTRY_IMAGES_DIR` | `data/export/country-images`  | Destination directory for images         |
| `NOCODB_TOKEN`       | *(required)*                  | NocoDB API token                         |
| `NOCODB_URL`         | *(required)*                  | NocoDB base URL                          |
| `NOCODB_BASE_ID`     | *(required)*                  | NocoDB base ID                           |
