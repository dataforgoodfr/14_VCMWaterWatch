/**
 * Server-side helper for resolving entity image URLs.
 *
 * Images are mirrored from NocoDB to a shared Docker volume by the
 * `export_entity_images` Prefect flow and served via the Next.js route
 * handler at `/images/[entity]/[...path]`.  A `manifest.json` file in each
 * entity subdirectory maps keys to stable, hashed filenames:
 *
 *   country/manifest.json: { "FR": "FR.a1b2c3d4.jpg", "IT": "IT.9f8e7d6c.png" }
 *   team/manifest.json:    { "gaspard-lemaire": "gaspard-lemaire.9f8e7d6c.jpg" }
 *
 * This module reads each manifest on demand (cached with mtime-based
 * invalidation per entity) and exposes a single helper `getEntityImageSrc`
 * that converts an entity name + key to a public URL path, or returns `null`
 * if no image is available.
 *
 * **Configuration:** set `EXPORT_IMAGES_DIR` to the directory written by the
 * export pipeline (e.g. `../data/export/images` locally, or `/public/images`
 * in production via the `images-data` Docker volume). If the env var is
 * unset, `getEntityImageSrc` returns `null` for every key (images are
 * optional).
 *
 * **Local dev:** run `just pipelines export-country-images` (or
 * `export-team-images`) once, or rely on committed seed data.  Set
 * `EXPORT_IMAGES_DIR=../data/export/images` in `webapp/.env.local`.
 *
 * **Production:** `docker-compose.deploy.yml` sets
 * `EXPORT_IMAGES_DIR=/public/images` and mounts the `images-data` volume
 * there on both worker and webapp.
 */

import fs from 'fs'
import path from 'path'

/** Entities that are allowed in the image URL (allowlist). */
export const ALLOWED_ENTITIES = ['country', 'team'] as const
export type Entity = (typeof ALLOWED_ENTITIES)[number]

const IMAGES_PREFIX = '/images'

type Manifest = Record<string, string>

/** Per-entity manifest cache. */
const _manifestCache = new Map<Entity, { manifest: Manifest; mtime: number; dir: string }>()

function getImagesBaseDir(): string | null {
	return process.env.EXPORT_IMAGES_DIR ?? null
}

function getManifestPath(entity: Entity): string | null {
	const base = getImagesBaseDir()

	if (!base) {
		return null
	}

	return path.join(base, entity, 'manifest.json')
}

/**
 * Load (and cache) the manifest for an entity from disk.
 * Re-reads the file whenever its mtime changes so that a new manifest
 * written by the worker container is picked up without restarting the
 * Next.js server.
 * Returns an empty object if `EXPORT_IMAGES_DIR` is unset, the manifest
 * is missing, or the manifest is malformed.
 */
function loadManifest(entity: Entity): Manifest {
	const manifestPath = getManifestPath(entity)

	if (!manifestPath) {
		return {}
	}

	const dir = path.dirname(manifestPath)
	const cached = _manifestCache.get(entity)

	// Invalidate cache if the directory changed (e.g. in tests).
	if (cached && cached.dir !== dir) {
		_manifestCache.delete(entity)
	}

	try {
		const stat = fs.statSync(manifestPath, { throwIfNoEntry: false })
		const mtime = stat?.mtimeMs ?? 0

		const current = _manifestCache.get(entity)

		if (mtime === current?.mtime) {
			return current.manifest
		}

		if (!stat) {
			// File absent — cache the empty result to avoid repeated stat calls.
			_manifestCache.set(entity, { manifest: {}, mtime: 0, dir })
			return {}
		}

		const raw = fs.readFileSync(manifestPath, 'utf-8')
		const manifest = JSON.parse(raw) as Manifest

		_manifestCache.set(entity, { manifest, mtime, dir })
		return manifest
	} catch {
		// Missing manifest is expected in CI / fresh checkouts without seed images.
		_manifestCache.set(entity, { manifest: {}, mtime: 0, dir })
		return {}
	}
}

/**
 * Return the public URL for an entity's image, or `null` if none.
 *
 * @param entity  Entity type (`'country'` or `'team'`).
 * @param key     Key as stored in the manifest (e.g. country code `"FR"` or
 *                team member slug `"gaspard-lemaire"`).
 */
export function getEntityImageSrc(entity: Entity, key: string | null | undefined): string | null {
	if (!key) {
		return null
	}

	const manifest = loadManifest(entity)
	const filename = manifest[key]

	if (!filename) {
		return null
	}

	return `${IMAGES_PREFIX}/${entity}/${filename}`
}

/** @internal Exposed only for tests — clears the module-scope cache. */
export function _resetManifestCache(entity?: Entity): void {
	if (entity) {
		_manifestCache.delete(entity)
	} else {
		_manifestCache.clear()
	}
}
