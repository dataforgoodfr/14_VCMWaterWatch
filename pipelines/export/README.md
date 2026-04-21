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

# export entity images (country, team)

Mirror entity images (e.g. country flags, team member photos) from NocoDB to
a local directory so they can be served from a stable, cache-friendly URL
instead of short-lived S3 signed URLs.

The generic flow lives in `export_entity_images.py`. Thin wrappers
`export_country_images.py` and `export_team_images.py` invoke it with
entity-specific parameters.

## How it works

1. Reads all records from the configured NocoDB table (e.g. `Country`, `Team`).
2. For each record with at least one image attachment, downloads the first
   image using the `signedUrl` (server-side only — the signed URL is never
   exposed to end users).
3. Computes the first 8 hex characters of the SHA-256 hash of the image bytes
   to produce a cache-busting filename: `{key}.{hash}.{ext}` (key is the
   country `Code` or a slug of the team member's name).
4. Writes each image to a staging directory, then atomically moves the files
   into the destination and writes `manifest.json` last.

## Output layout

```
<EXPORT_IMAGES_DIR>/
    country/
        FR.a1b2c3d4.jpg
        IT.9f8e7d6c.png
        manifest.json      ← { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
    team/
        jane-doe.5e4d3c2b.png
        manifest.json
```

The manifest is written **last**, so readers always see either a fully
consistent old set or a fully consistent new set — never a torn state.
Stale files (images whose hash changed or whose record was removed) are
deleted after the manifest swap.

## Webhook wiring

The `export_country_images` flow is triggered automatically by the worker
(`pipelines/worker/app.py`) whenever NocoDB fires a webhook for the `Country`
table. It shares the same `_flow_run_lock` as the PMTiles export, so the two
flows are serialized — a `Country` change triggers both exports sequentially.

## Volume layout (production)

In production, `docker-compose.deploy.yml` defines an `images-data` named
volume that is mounted in two places:

| Service | Mount path        | Purpose                              |
|---------|-------------------|--------------------------------------|
| worker  | `/public/images`  | Flow writes images + manifest here   |
| webapp  | `/public/images`  | Route handler reads files from here  |

Both services have `EXPORT_IMAGES_DIR=/public/images` set. The generic route
handler at `webapp/app/images/[entity]/[...path]/route.ts` serves
`/images/<entity>/...` by reading files directly from
`EXPORT_IMAGES_DIR/<entity>/`, and `webapp/lib/entityImage.ts` reads each
entity's `manifest.json` (with mtime-based cache invalidation) to resolve
`key → /images/<entity>/<file>`.

## Local development

Seed `manifest.json` files are committed under `data/export/images/<entity>/`
so `pnpm dev` works without running the pipeline. Set
`EXPORT_IMAGES_DIR=../data/export/images` in `webapp/.env.local`
(already present in the committed file). To refresh images locally:

```bash
just pipelines export-country-images
just pipelines export-team-images
just pipelines export-all-images
# or, with a custom destination:
EXPORT_IMAGES_DIR=/tmp/ci uv run python -m pipelines.export.export_country_images
```

## Environment variables

| Variable            | Default                | Description                              |
|---------------------|------------------------|------------------------------------------|
| `EXPORT_IMAGES_DIR` | `data/export/images`   | Root destination directory for images    |
| `NOCODB_TOKEN`      | *(required)*           | NocoDB API token                         |
| `NOCODB_URL`        | *(required)*           | NocoDB base URL                          |
| `NOCODB_BASE_ID`    | *(required)*           | NocoDB base ID                           |
