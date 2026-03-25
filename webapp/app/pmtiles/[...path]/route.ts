import { access, open, stat } from 'node:fs/promises'
import path from 'node:path'

import type { NextRequest } from 'next/server'

const PUBLIC_PM_TILES_DIR = path.join(process.cwd(), 'public', 'pmtiles')
const REPO_EXPORT_PM_TILES_DIR = path.join(process.cwd(), '..', 'data', 'export')

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

async function resolvePmTilesPath(parts: string[]): Promise<string | null> {
	const safePath = sanitizePath(parts)

	if (!safePath) {
		return null
	}

	const candidates = [path.join(PUBLIC_PM_TILES_DIR, safePath), path.join(REPO_EXPORT_PM_TILES_DIR, safePath)]

	for (const candidate of candidates) {
		try {
			await access(candidate)
			return candidate
		} catch {
			// try next candidate
		}
	}

	return null
}

function parseRange(rangeHeader: string, fileSize: number): { start: number; end: number } | null {
	const match = /^bytes=(\d*)-(\d*)$/.exec(rangeHeader)

	if (!match) {
		return null
	}

	const [, startStr, endStr] = match

	if (!startStr && !endStr) {
		return null
	}

	if (startStr && endStr) {
		const start = Number(startStr)
		const end = Number(endStr)

		if (Number.isNaN(start) || Number.isNaN(end) || start > end || end >= fileSize) {
			return null
		}

		return { start, end }
	}

	if (startStr) {
		const start = Number(startStr)

		if (Number.isNaN(start) || start >= fileSize) {
			return null
		}

		return { start, end: fileSize - 1 }
	}

	const suffixLength = Number(endStr)

	if (Number.isNaN(suffixLength) || suffixLength <= 0) {
		return null
	}

	const start = Math.max(fileSize - suffixLength, 0)

	return { start, end: fileSize - 1 }
}

function buildHeaders(fileSize: number, extra: Record<string, string> = {}) {
	return {
		'Accept-Ranges': 'bytes',
		'Cache-Control': 'public, max-age=31536000, immutable',
		'Content-Type': 'application/vnd.pmtiles',
		...extra,
		'Content-Length': String(extra['Content-Length'] ?? fileSize)
	}
}

async function handleRequest(request: NextRequest, isHead: boolean): Promise<Response> {
	const parts = request.nextUrl.pathname.split('/').filter(Boolean).slice(1)
	const filePath = await resolvePmTilesPath(parts)

	if (!filePath) {
		return new Response('Not found', { status: 404 })
	}

	const fileStats = await stat(filePath)
	const fileSize = fileStats.size
	const rangeHeader = request.headers.get('range')

	if (!rangeHeader) {
		if (isHead) {
			return new Response(null, { status: 200, headers: buildHeaders(fileSize) })
		}

		const buffer = await open(filePath, 'r').then(async file => {
			try {
				return await file.readFile()
			} finally {
				await file.close()
			}
		})

		return new Response(buffer, {
			status: 200,
			headers: buildHeaders(fileSize)
		})
	}

	const range = parseRange(rangeHeader, fileSize)

	if (!range) {
		return new Response('Requested Range Not Satisfiable', {
			status: 416,
			headers: {
				'Accept-Ranges': 'bytes',
				'Content-Range': `bytes */${fileSize}`
			}
		})
	}

	const { start, end } = range
	const chunkSize = end - start + 1

	if (isHead) {
		return new Response(null, {
			status: 206,
			headers: buildHeaders(fileSize, {
				'Content-Length': String(chunkSize),
				'Content-Range': `bytes ${start}-${end}/${fileSize}`
			})
		})
	}

	const file = await open(filePath, 'r')

	try {
		const chunk = new Uint8Array(chunkSize)

		await file.read(chunk, 0, chunkSize, start)

		return new Response(chunk, {
			status: 206,
			headers: buildHeaders(fileSize, {
				'Content-Length': String(chunkSize),
				'Content-Range': `bytes ${start}-${end}/${fileSize}`
			})
		})
	} finally {
		await file.close()
	}
}

export async function GET(request: NextRequest): Promise<Response> {
	return handleRequest(request, false)
}

export async function HEAD(request: NextRequest): Promise<Response> {
	return handleRequest(request, true)
}
