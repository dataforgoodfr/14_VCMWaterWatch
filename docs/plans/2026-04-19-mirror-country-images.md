# Mirror NocoDB country images to a shared volume

## Goal

Country profile images currently come from NocoDB as short-lived S3 signed URLs
(`X-Amz-Date`/`X-Amz-Signature` change every request). Each page load is a
fresh URL → no browser / Next.js image-optimizer / CDN cache hits → the image
is flagged as the LCP on `/country-profile` and adds avoidable latency.

Mirror the images to a shared Docker volume (same pattern as PMTiles), serve
them at a **stable, cache-friendly URL** from the webapp, and refresh on
NocoDB webhook.

## Pattern reference

PMTiles already work this way:

- `pipelines/export/export_pmtiles.py` — Prefect flow writing to
  `PM_TILES_DIR` (default `/public/pmtiles`).
- `pipelines/worker/app.py` — FastAPI service; NocoDB webhook triggers a
  debounced export for tables `Country` / `DistributionZone`.
- `docker-compose.deploy.yml` — shared `pmtiles-data` volume mounted in both
  `webapp` (`/public/pmtiles`) and `worker` (`/public/pmtiles`).
- Next.js serves them as static assets under `/pmtiles/...`.

We'll replicate this for images.

## Proposed changes

### 1. New Prefect flow: `pipelines/export/export_country_images.py`

- Read `Country` records from NocoDB via `services.db_helper()`, requesting
  fields `Id,Code,Image`.
- For each record with an `Image` attachment:
  - Pick the first attachment (same logic as `CountryProfileDetail.tsx`).
  - Download the bytes from `signedUrl` (server-side, one-shot — signed URL
    is only used inside the worker).
  - Compute a short content hash (e.g. first 8 hex chars of SHA-256).
  - Write to `{COUNTRY_IMAGES_DIR}/{code}.{hash}.{ext}` (extension from
    mimetype). Hashed filename gives a free cache-buster: when the image
    changes, the URL changes.
- Write a manifest `{COUNTRY_IMAGES_DIR}/manifest.json`:
  ```json
  { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
  ```
- Atomic swap: write to a temp dir, then `os.replace` manifest last (readers
  see either the old or new full set, never a torn state).
- Delete stale files for codes no longer present / whose hash changed
  (after manifest swap).
- Env var: `COUNTRY_IMAGES_DIR` (default `data/export/country-images`
  locally, `/public/country-images` in prod).
- Tests under `pipelines/export/tests/` mocking `db_helper` and HTTP.

### 2. Wire up the worker: `pipelines/worker/app.py`

- Add `COUNTRY_IMAGES_TRIGGER_TABLES = {"Country"}`.
- Add `_schedule_country_images()` + `_run_country_images_flow()` mirroring
  the existing debounce pattern (reuse `_flow_run_lock` so Prefect runs
  serialize).
- In `nocodb_webhook`, if `table_name in COUNTRY_IMAGES_TRIGGER_TABLES`,
  schedule it and add `"export_country_images"` to the response.
- Extend `test_app.py` accordingly.

Note: `Country` is already a PMTiles trigger, so a NocoDB edit on Country
will (correctly) schedule both flows; they'll run serialized via
`_flow_run_lock`.

### 3. Compose / deploy

`docker-compose.deploy.yml`:

- New named volume `country-images-data`.
- Mount on `webapp`: `/public/country-images`.
- Mount on `worker`: `/public/country-images`.
- New env var on both services:
  `COUNTRY_IMAGES_DIR=/public/country-images`.

Local `docker-compose.yml` doesn't currently run the webapp/worker; no
change needed there.

**Local dev strategy**: commit a seed set of country images under
`webapp/public/country-images/` (plus a committed `manifest.json`). This
makes `pnpm dev` work with zero setup. To keep the Docker image lean:

- Add `webapp/public/country-images/` to `webapp/.dockerignore` so the
  seeded files never ship in the image.
- In production, the `country-images-data` volume mount at
  `/public/country-images` provides the real (current) set, written by the
  worker.
- Devs who want fresh images locally can run
  `just export-country-images` (writes to the same folder, `COUNTRY_IMAGES_DIR`
  defaults to `webapp/public/country-images`).

The seed is intentionally lightweight — one representative image per
country we currently have, refreshed manually when it drifts too far.

### 4. Webapp consumption

- Add a tiny helper `webapp/lib/countryImage.ts`:
  - Server-side reads `public/country-images/manifest.json` once (cached in
    module scope), maps `code` → `/country-images/<file>`.
  - Falls back to `null` if manifest missing or code absent.
- `app/[locale]/country-profile/components/CountryProfileDetail.tsx`:
  - Replace the `signedUrl` lookup with
    `getCountryImageSrc(f.Code) ?? placeholder`.
  - Add `priority` to the `<Image>` (fixes the LCP warning directly; the
    asset is now cacheable so `priority` is cheap on repeat visits).
- `next.config.ts`: no change needed — the URL is same-origin static.
- Leave NocoDB S3 domains in `remotePatterns` for now (still used by blog
  posts / carousel); remove later if we mirror those too.

### 5. Housekeeping

- `webapp/.dockerignore`: exclude `public/country-images/` so committed
  seed images don't bloat the production image (volume mount supplies
  them at runtime).
- `justfile`: `just export-country-images` target for local runs.
- Seed images are **committed** (see local dev strategy above); no
  `.gitignore` entry.

### 6. Documentation

- Short README section in `pipelines/export/README.md` describing the flow,
  the volume layout, and the webhook wiring.

## Scope (explicitly out)

- Blog post images (`BlogPost`, `Blog` components) and any other
  NocoDB-attachment-driven images. The same pattern will apply if/when we
  want to mirror them; keeping this PR focused on the country profile LCP
  issue.
- Automated stale-file GC beyond "remove files not in new manifest" — no
  cron sweeper needed.

## Open questions

0. **Verify volume-mount shadowing works with `output: 'standalone'`**:
   confirm the pmtiles setup already relies on this (volume mounted at
   `/public/pmtiles` overlays whatever the image contains). If the
   standalone build copies `public/` into a read-only location, we may
   need a small tweak. Quick check during implementation.

1. **Filename strategy**: `{code}.{hash}.{ext}` vs. `{code}/{hash}.{ext}`
   vs. plain `{code}.{ext}` with `Cache-Control: must-revalidate`. Hash in
   filename is simplest and lets us set `immutable` caching. OK?
   - OK
2. **Multiple images per country**: the `Image` field in NocoDB is an
   array; today the UI uses only `[0]`. Mirror just `[0]`, or all of them
   (indexed)? Proposal: just `[0]` for now.
   - OK
3. **Image optimization**: rely on Next.js `<Image>` to produce
   AVIF/WebP at request time (default behaviour), or pre-generate multiple
   sizes in the flow? Proposal: let Next handle it — it can now because
   the source URL is stable.
   - OK
4. **First-run bootstrap**: should the worker run the flow once on
   startup (in addition to on-webhook), so a fresh deploy has images
   without waiting for an edit? Proposal: yes, add a startup hook
   (same question probably applies to pmtiles — check current behaviour).
   - NOT NEEDED
5. **Webhook setup**: NocoDB already has a webhook on `Country` for
   PMTiles — confirm it fires on `records.after.update` *and*
   `records.after.insert` and attachment edits. No code change here, just
   a deployment checklist item.
   - MAKE MANUAL CHECK
