/**
 * Server-side helper for resolving entity image URLs.
 *
 * Images are mirrored from NocoDB to a shared Docker volume by the
 * `export_entity_images` Prefect flow and served via the Next.js route
 * handler at `/images/[entity]/[...path]`.  A `manifest.json` file in
 * `<EXPORT_IMAGES_DIR>/<entity>/` maps entity keys to stable, hashed
 * filenames:
 *
 *   country: { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
 *   team:    { "gaspard-lemaire": "gaspard-lemaire.a1b2c3d4.jpg" }
 *
 * This module reads the manifest on demand (cached per entity with mtime-based
 * invalidation) and exposes a single helper `getEntityImageSrc` that converts
 * an entity type + key to a public URL path, or returns `null` if no image is
 * available.
 *
 * **Configuration:** set `EXPORT_IMAGES_DIR` to the directory written by
 * the export pipeline (e.g. `../data/export/images` locally, or
 * `/public/images` in production via the `images-data` Docker volume).
 * If the env var is unset, `getEntityImageSrc` returns `null` for every key
 * (entity images are optional).
 *
 * **Local dev:** run `just export-country-images` or `just export-team-images`,
 * then set `EXPORT_IMAGES_DIR=../data/export/images` in `webapp/.env.local`.
 */

import fs from 'fs'
import path from 'path'

/**
 * Allowlist of entity names that may be served via the `/images/[entity]/...`
 * route and resolved by `getEntityImageSrc`.
 *
 * This is the single source of truth: the route handler imports it from here
 * rather than duplicating the list.  Add new entity names here when the
 * pipeline exports them.
 */
export const ALLOWED_ENTITIES = ['country', 'team'] as const
export type EntityName = (typeof ALLOWED_ENTITIES)[number]

type Manifest = Record<string, string>

interface CacheEntry {
	manifest: Manifest
	mtime: number
	dir: string
}

/** Per-entity manifest cache. */
const _cache = new Map<EntityName, CacheEntry>()

function getManifestPath(entity: EntityName): string | null {
	const dir = process.env.EXPORT_IMAGES_DIR

	if (!dir) {
		return null
	}

	return path.join(dir, entity, 'manifest.json')
}

/**
 * Load (and cache) the entity image manifest from disk.
 * Re-reads the file whenever its mtime changes so that a new manifest
 * written by the worker container is picked up without restarting the
 * Next.js server.
 * Returns an empty object if `EXPORT_IMAGES_DIR` is unset, the manifest
 * is missing, or the manifest is malformed.
 */
function loadManifest(entity: EntityName): Manifest {
	const manifestPath = getManifestPath(entity)

	if (!manifestPath) {
		return {}
	}

	const dir = path.dirname(manifestPath)
	const cached = _cache.get(entity)

	// Invalidate if the configured directory changed (e.g. in tests).
	if (cached && cached.dir !== dir) {
		_cache.delete(entity)
	}

	try {
		const stat = fs.statSync(manifestPath, { throwIfNoEntry: false })
		const mtime = stat?.mtimeMs ?? 0
		const current = _cache.get(entity)

		if (mtime === current?.mtime) {
			return current.manifest
		}

		if (!stat) {
			// File absent — cache the empty result to avoid repeated stat calls.
			_cache.set(entity, { manifest: {}, mtime: 0, dir })
			return {}
		}

		const raw = fs.readFileSync(manifestPath, 'utf-8')
		const manifest = JSON.parse(raw) as Manifest

		_cache.set(entity, { manifest, mtime, dir })
		return manifest
	} catch {
		// Missing or malformed manifest is expected in CI / fresh checkouts.
		_cache.set(entity, { manifest: {}, mtime: 0, dir })
		return {}
	}
}

/**
 * Return the public URL for an entity image, or `null` if none is available.
 *
 * @param entity  Entity type, e.g. `'country'` or `'team'`.
 * @param key     Entity key as stored in the manifest (country code for
 *                country, slugified name for team members).
 */
export function getEntityImageSrc(entity: EntityName, key: string | null | undefined): string | null {
	if (!key) {
		return null
	}

	const manifest = loadManifest(entity)
	const filename = manifest[key]

	if (!filename) {
		return null
	}

	return `/images/${entity}/${filename}`
}

/** @internal Exposed only for tests — clears the module-scope cache. */
export function _resetManifestCache(): void {
	_cache.clear()
}
