/**
 * Server-side helper for resolving country profile image URLs.
 *
 * Images are mirrored from NocoDB to a shared Docker volume by the
 * `export_country_images` Prefect flow and served as static assets under
 * `/country-images/`.  A `manifest.json` file in the same directory maps
 * country codes to stable, hashed filenames:
 *
 *   { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
 *
 * This module reads the manifest on demand (cached with mtime-based
 * invalidation) and exposes a single helper `getCountryImageSrc` that
 * converts a country code to a public URL path, or returns `null` if no
 * image is available.
 *
 * **Local dev**: commit a seed `webapp/public/country-images/manifest.json`
 * so `pnpm dev` works without running the pipeline.  In production, the
 * `country-images-data` Docker volume mount at `/public/country-images`
 * provides the live set written by the worker container.
 */

import fs from 'fs'
import path from 'path'

const MANIFEST_PATH = path.join(process.cwd(), 'public', 'country-images', 'manifest.json')
const COUNTRY_IMAGES_PREFIX = '/country-images'

type Manifest = Record<string, string>

/** Module-scoped cache so the manifest is only read from disk when changed. */
let _manifest: Manifest | null = null
/** mtime of the manifest file when it was last successfully read. */
let _manifestMtime = 0

/**
 * Load (and cache) the country image manifest from disk.
 * Re-reads the file whenever its mtime changes so that a new manifest
 * written by the worker container is picked up without restarting the
 * Next.js server.
 * Returns an empty object if the manifest is missing or malformed.
 */
function loadManifest(): Manifest {
	try {
		const stat = fs.statSync(MANIFEST_PATH, { throwIfNoEntry: false })
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

		const raw = fs.readFileSync(MANIFEST_PATH, 'utf-8')

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
}
