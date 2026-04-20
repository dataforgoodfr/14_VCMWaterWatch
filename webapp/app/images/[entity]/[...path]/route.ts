/**
 * Generic route handler for serving entity images from the shared images
 * directory.
 *
 * URL pattern: /images/<entity>/<filename>
 *
 * - `entity` must be in the ALLOWED_ENTITIES allowlist (prevents arbitrary
 *   directory traversal through the entity segment).
 * - Path traversal via `..` is rejected in the path segments.
 * - Returns 404 if `EXPORT_IMAGES_DIR` is unset (images are optional).
 * - Sets `Cache-Control: public, max-age=31536000, immutable` because
 *   filenames are content-hashed.
 *
 * Replaces the old `/country-images/[...path]` route handler.
 */

import { readFile } from 'node:fs/promises'
import path from 'node:path'

import type { NextRequest } from 'next/server'

import { ALLOWED_ENTITIES } from '@/lib/entityImage'

const ALLOWED_ENTITY_SET = new Set<string>(ALLOWED_ENTITIES)

const CONTENT_TYPES: Record<string, string> = {
	jpg: 'image/jpeg',
	jpeg: 'image/jpeg',
	png: 'image/png',
	webp: 'image/webp'
}

function getImagesDir(): string | null {
	return process.env.EXPORT_IMAGES_DIR ?? null
}

function getContentType(filename: string): string {
	const ext = filename.split('.').pop()?.toLowerCase() ?? ''

	return CONTENT_TYPES[ext] ?? 'application/octet-stream'
}

/**
 * Resolve the absolute filesystem path for the requested entity image.
 *
 * Returns `null` if:
 * - `EXPORT_IMAGES_DIR` is unset
 * - `entity` is not in the allowlist
 * - any path segment contains `..`
 * - `pathParts` is empty
 */
function resolveImagePath(entity: string, pathParts: string[]): string | null {
	const dir = getImagesDir()

	if (!dir) {
		return null
	}

	if (!ALLOWED_ENTITY_SET.has(entity)) {
		return null
	}

	if (pathParts.length === 0) {
		return null
	}

	const joined = pathParts.join('/')
	const normalised = path.normalize(joined)

	// Reject `..` (path traversal) and `.` — `path.normalize(['foo','..'])`
	// returns `'.'` which would resolve to the entity directory itself and
	// trigger EISDIR on readFile.
	if (normalised.includes('..') || normalised === '.') {
		return null
	}

	return path.join(dir, entity, normalised)
}

export async function GET(
	request: NextRequest,
	{ params }: { params: Promise<{ entity: string; path: string[] }> }
): Promise<Response> {
	const { entity, path: pathParts } = await params
	const filePath = resolveImagePath(entity, pathParts)

	if (!filePath) {
		return new Response('Not found', { status: 404 })
	}

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
