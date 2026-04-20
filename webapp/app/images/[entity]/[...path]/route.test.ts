import fs from 'fs'
import os from 'os'
import path from 'path'

import type { NextRequest } from 'next/server'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GET } from './route'

let tmpDir: string
const originalEnv = process.env.EXPORT_IMAGES_DIR

function makeRequest(entity: string, filePath: string[]): NextRequest {
	return {
		nextUrl: { pathname: `/images/${entity}/${filePath.join('/')}` }
	} as unknown as NextRequest
}

function makeParams(entity: string, filePath: string[]): Promise<{ entity: string; path: string[] }> {
	return Promise.resolve({ entity, path: filePath })
}

beforeEach(() => {
	tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'entity-images-route-test-'))
})

afterEach(() => {
	fs.rmSync(tmpDir, { recursive: true, force: true })

	if (originalEnv === undefined) {
		delete process.env.EXPORT_IMAGES_DIR
	} else {
		process.env.EXPORT_IMAGES_DIR = originalEnv
	}
})

describe('GET /images/[entity]/[...path]', () => {
	it('returns 404 when EXPORT_IMAGES_DIR is unset', async () => {
		delete process.env.EXPORT_IMAGES_DIR

		const res = await GET(makeRequest('country', ['FR.abc.jpg']), {
			params: makeParams('country', ['FR.abc.jpg'])
		})

		expect(res.status).toBe(404)
	})

	it('returns 404 for an unknown entity', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir

		const res = await GET(makeRequest('evil', ['foo.jpg']), {
			params: makeParams('evil', ['foo.jpg'])
		})

		expect(res.status).toBe(404)
	})

	it('returns 404 for path traversal attempt', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir

		const res = await GET(makeRequest('country', ['..', '..', 'etc', 'passwd']), {
			params: makeParams('country', ['..', '..', 'etc', 'passwd'])
		})

		expect(res.status).toBe(404)
	})

	it('returns 404 for a missing file', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir

		const res = await GET(makeRequest('country', ['nonexistent.jpg']), {
			params: makeParams('country', ['nonexistent.jpg'])
		})

		expect(res.status).toBe(404)
	})

	it('returns 200 with correct Content-Type for a jpg country image', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const countryDir = path.join(tmpDir, 'country')

		fs.mkdirSync(countryDir, { recursive: true })
		const imgPath = path.join(countryDir, 'FR.abc.jpg')

		fs.writeFileSync(imgPath, Buffer.from([0xff, 0xd8, 0xff]))

		const res = await GET(makeRequest('country', ['FR.abc.jpg']), {
			params: makeParams('country', ['FR.abc.jpg'])
		})

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/jpeg')
		expect(res.headers.get('Cache-Control')).toBe('public, max-age=31536000, immutable')
	})

	it('returns 200 with correct Content-Type for a png', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const countryDir = path.join(tmpDir, 'country')

		fs.mkdirSync(countryDir, { recursive: true })
		const imgPath = path.join(countryDir, 'DE.123.png')

		fs.writeFileSync(imgPath, Buffer.from([0x89, 0x50, 0x4e, 0x47]))

		const res = await GET(makeRequest('country', ['DE.123.png']), {
			params: makeParams('country', ['DE.123.png'])
		})

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/png')
	})

	it('returns 200 for a team entity image', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const teamDir = path.join(tmpDir, 'team')

		fs.mkdirSync(teamDir, { recursive: true })
		const imgPath = path.join(teamDir, 'alice-martin.9f8e7d6c.jpg')

		fs.writeFileSync(imgPath, Buffer.from([0xff, 0xd8, 0xff]))

		const res = await GET(makeRequest('team', ['alice-martin.9f8e7d6c.jpg']), {
			params: makeParams('team', ['alice-martin.9f8e7d6c.jpg'])
		})

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/jpeg')
	})
})
