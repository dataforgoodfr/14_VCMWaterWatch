/**
 * Route handler for serving entity images (country flags, team member photos,
 * …) from a configurable directory on the host filesystem.
 *
 * URL structure: `/images/[entity]/[...path]`
 *   - `entity` must be in the allowlist (`ALLOWED_ENTITIES`) — currently
 *     `'country'` and `'team'`.  Future entities are one-line additions to
 *     that constant in `webapp/lib/entityImage.ts`.
 *   - `path` is the relative path within the entity subdirectory (normally
 *     just the filename, e.g. `FR.a1b2c3d4.jpg`).
 *
 * Set `EXPORT_IMAGES_DIR` to the directory containing the entity
 * subdirectories written by `pipelines/export/export_entity_images.py`.
 *
 * - Returns 404 if `EXPORT_IMAGES_DIR` is unset (images are optional).
 * - Returns 404 if `entity` is not in the allowlist.
 * - Returns 404 if the path contains `..` (path-traversal guard).
 * - Returns 404 if the file is missing.
 * - Sets `Cache-Control: public, max-age=31536000, immutable` because
 *   filenames are content-hashed.
 */

import { readFile } from 'node:fs/promises'
import path from 'node:path'

import type { NextRequest } from 'next/server'

import { ALLOWED_ENTITIES } from '@/lib/entityImage'

const CONTENT_TYPES: Record<string, string> = {
	jpg: 'image/jpeg',
	jpeg: 'image/jpeg',
	png: 'image/png',
	webp: 'image/webp'
}

function getImagesBaseDir(): string | null {
	return process.env.EXPORT_IMAGES_DIR ?? null
}

function isAllowedEntity(entity: string): boolean {
	return (ALLOWED_ENTITIES as readonly string[]).includes(entity)
}

function sanitizePath(parts: string[]): string | null {
	if (parts.length === 0) {
		return null
	}

	const clean = path.normalize(parts.join('/'))

	if (clean.includes('..')) {
		return null
	}

	return clean
}

function getContentType(filename: string): string {
	const ext = filename.split('.').pop()?.toLowerCase() ?? ''

	return CONTENT_TYPES[ext] ?? 'application/octet-stream'
}

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<{ entity: string; path: string[] }> }
): Promise<Response> {
	const baseDir = getImagesBaseDir()

	if (!baseDir) {
		return new Response('Not found', { status: 404 })
	}

	const { entity, path: pathParts } = await params

	if (!isAllowedEntity(entity)) {
		return new Response('Not found', { status: 404 })
	}

	const safePath = sanitizePath(pathParts)

	if (!safePath) {
		return new Response('Not found', { status: 404 })
	}

	const filePath = path.join(baseDir, entity, safePath)

	let buffer: Buffer

	try {
		buffer = await readFile(filePath)
	} catch {
		return new Response('Not found', { status: 404 })
	}

	return new Response(new Uint8Array(buffer), {
		status: 200,
		headers: {
			'Content-Type': getContentType(filePath),
			'Content-Length': String(buffer.byteLength),
			'Cache-Control': 'public, max-age=31536000, immutable'
		}
	})
}
