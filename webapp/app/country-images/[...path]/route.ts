/**
 * Route handler for serving country profile images from a configurable
 * directory on the host filesystem.
 *
 * Set `COUNTRY_IMAGES_DIR` to the directory containing the images and
 * `manifest.json` written by `pipelines/export/export_country_images.py`.
 *
 * This mirrors the pmtiles route handler pattern so there is a single code
 * path in both dev and prod, driven by the env var rather than Next.js'
 * static file handler (which cannot serve files outside `public/`).
 *
 * - Returns 404 if the file is missing or the path is unsafe (contains `..`).
 * - Returns 404 if `COUNTRY_IMAGES_DIR` is unset (country images optional).
 * - Sets `Cache-Control: public, max-age=31536000, immutable` because
 *   filenames are content-hashed in the manifest.
 */

import { readFile } from 'node:fs/promises'
import path from 'node:path'

import type { NextRequest } from 'next/server'

const CONTENT_TYPES: Record<string, string> = {
	jpg: 'image/jpeg',
	jpeg: 'image/jpeg',
	png: 'image/png',
	webp: 'image/webp'
}

function getCountryImagesDir(): string | null {
	return process.env.COUNTRY_IMAGES_DIR ?? null
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

function resolveImagePath(parts: string[]): string | null {
	const dir = getCountryImagesDir()

	if (!dir) {
		return null
	}

	const safePath = sanitizePath(parts)

	if (!safePath) {
		return null
	}

	return path.join(dir, safePath)
}

export async function GET(request: NextRequest): Promise<Response> {
	const parts = request.nextUrl.pathname.split('/').filter(Boolean).slice(1)
	const filePath = resolveImagePath(parts)

	if (!filePath) {
		return new Response('Not found', { status: 404 })
	}

	// Content-Type is derived from the resolved on-disk path (not URL input)
	// so the header reflects what is actually served.
	let buffer: Buffer

	try {
		buffer = await readFile(filePath)
	} catch {
		return new Response('Not found', { status: 404 })
	}

	return new Response(buffer, {
		status: 200,
		headers: {
			'Content-Type': getContentType(filePath),
			'Content-Length': String(buffer.byteLength),
			'Cache-Control': 'public, max-age=31536000, immutable'
		}
	})
}
