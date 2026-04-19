import fs from 'fs'
import os from 'os'
import path from 'path'

import type { NextRequest } from 'next/server'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GET } from '../../../app/country-images/[...path]/route'

let tmpDir: string
const originalEnv = process.env.COUNTRY_IMAGES_DIR

function makeRequest(urlPath: string): NextRequest {
	return {
		nextUrl: { pathname: urlPath }
	} as unknown as NextRequest
}

beforeEach(() => {
	tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'country-images-route-test-'))
})

afterEach(() => {
	fs.rmSync(tmpDir, { recursive: true, force: true })

	if (originalEnv === undefined) {
		delete process.env.COUNTRY_IMAGES_DIR
	} else {
		process.env.COUNTRY_IMAGES_DIR = originalEnv
	}
})

describe('GET /country-images/[...path]', () => {
	it('returns 404 when COUNTRY_IMAGES_DIR is unset', async () => {
		delete process.env.COUNTRY_IMAGES_DIR
		const res = await GET(makeRequest('/country-images/FR.abc.jpg'))

		expect(res.status).toBe(404)
	})

	it('returns 404 for a missing file', async () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		const res = await GET(makeRequest('/country-images/nonexistent.jpg'))

		expect(res.status).toBe(404)
	})

	it('returns 404 for path traversal attempt', async () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		const res = await GET(makeRequest('/country-images/../../etc/passwd'))

		expect(res.status).toBe(404)
	})

	it('returns 200 with correct Content-Type for a jpg', async () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		const imgPath = path.join(tmpDir, 'FR.abc.jpg')

		fs.writeFileSync(imgPath, Buffer.from([0xff, 0xd8, 0xff]))

		const res = await GET(makeRequest('/country-images/FR.abc.jpg'))

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/jpeg')
		expect(res.headers.get('Cache-Control')).toBe('public, max-age=31536000, immutable')
	})

	it('returns 200 with correct Content-Type for a png', async () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		const imgPath = path.join(tmpDir, 'DE.123.png')

		fs.writeFileSync(imgPath, Buffer.from([0x89, 0x50, 0x4e, 0x47]))

		const res = await GET(makeRequest('/country-images/DE.123.png'))

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/png')
	})
})
