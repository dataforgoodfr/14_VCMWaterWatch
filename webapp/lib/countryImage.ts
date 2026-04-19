/**
 * Server-side helper for resolving country profile image URLs.
 *
 * Images are mirrored from NocoDB to a shared Docker volume by the
 * `export_country_images` Prefect flow and served via a dedicated Next.js
 * route handler at `/country-images/[...path]`.  A `manifest.json` file in
 * the same directory maps country codes to stable, hashed filenames:
 *
 *   { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
 *
 * This module reads the manifest on demand (cached with mtime-based
 * invalidation) and exposes a single helper `getCountryImageSrc` that
 * converts a country code to a public URL path, or returns `null` if no
 * image is available.
 *
 * **Configuration:** set `COUNTRY_IMAGES_DIR` to the directory written by
 * the export pipeline (e.g. `../data/export/country-images` locally, or
 * `/public/country-images` in production via the `country-images-data`
 * Docker volume). If the env var is unset, `getCountryImageSrc` returns
 * `null` for every code (country images are optional).
 *
 * **Local dev:** run `just pipelines export-country-images` once, or rely on
 * the committed seed at `data/export/country-images/`.  Set
 * `COUNTRY_IMAGES_DIR=../data/export/country-images` in `webapp/.env.local`.
 *
 * **Production:** `docker-compose.deploy.yml` sets
 * `COUNTRY_IMAGES_DIR=/public/country-images` and mounts the
 * `country-images-data` volume there on both worker and webapp.
 */

import fs from 'fs'
import path from 'path'

const COUNTRY_IMAGES_PREFIX = '/country-images'

type Manifest = Record<string, string>

/** Module-scoped cache so the manifest is only read from disk when changed. */
let _manifest: Manifest | null = null
/** mtime of the manifest file when it was last successfully read. */
let _manifestMtime = 0
/** The resolved dir when the cache was last populated. */
let _manifestDir = ''

function getManifestPath(): string | null {
	const dir = process.env.COUNTRY_IMAGES_DIR

	if (!dir) {
		return null
	}

	return path.join(dir, 'manifest.json')
}

/**
 * Load (and cache) the country image manifest from disk.
 * Re-reads the file whenever its mtime changes so that a new manifest
 * written by the worker container is picked up without restarting the
 * Next.js server.
 * Returns an empty object if `COUNTRY_IMAGES_DIR` is unset, the manifest
 * is missing, or the manifest is malformed.
 */
function loadManifest(): Manifest {
	const manifestPath = getManifestPath()

	if (!manifestPath) {
		return {}
	}

	// Invalidate cache if the configured directory has changed (e.g. in tests).
	const dir = path.dirname(manifestPath)

	if (dir !== _manifestDir) {
		_manifest = null
		_manifestMtime = 0
		_manifestDir = dir
	}

	try {
		const stat = fs.statSync(manifestPath, { throwIfNoEntry: false })
		const mtime = stat?.mtimeMs ?? 0

		if (_manifest !== null && mtime === _manifestMtime) {
			return _manifest
		}

		if (!stat) {
			// File absent — cache the empty result to avoid repeated stat calls.
			_manifest = {}
			_manifestMtime = 0
			return _manifest
		}

		const raw = fs.readFileSync(manifestPath, 'utf-8')

		_manifest = JSON.parse(raw) as Manifest
		_manifestMtime = mtime
	} catch {
		// Missing manifest is expected in CI / fresh checkouts without seed images.
		_manifest = {}
		_manifestMtime = 0
	}

	return _manifest
}

/**
 * Return the public URL for a country's profile image, or `null` if none.
 *
 * @param code  ISO country code as stored in NocoDB (e.g. `"FR"`, `"DE"`).
 */
export function getCountryImageSrc(code: string | null | undefined): string | null {
	if (!code) {
		return null
	}

	const manifest = loadManifest()
	const filename = manifest[code]

	if (!filename) {
		return null
	}

	return `${COUNTRY_IMAGES_PREFIX}/${filename}`
}

/** @internal Exposed only for tests — clears the module-scope cache. */
export function _resetManifestCache(): void {
	_manifest = null
	_manifestMtime = 0
	_manifestDir = ''
}
