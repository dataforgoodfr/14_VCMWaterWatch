import fs from 'fs'
import os from 'os'
import path from 'path'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { ALLOWED_ENTITIES } from '@/lib/entityImage'

import { GET } from './route'

let tmpDir: string
const originalEnv = process.env.EXPORT_IMAGES_DIR

function makeParams(entity: string, pathParts: string[]) {
	return Promise.resolve({ entity, path: pathParts })
}

// Minimal NextRequest stub — the route only reads params
const stubRequest = {} as import('next/server').NextRequest

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

describe('ALLOWED_ENTITIES', () => {
	it('includes country and team', () => {
		expect(ALLOWED_ENTITIES).toContain('country')
		expect(ALLOWED_ENTITIES).toContain('team')
	})
})

describe('GET /images/[entity]/[...path]', () => {
	it('returns 404 when EXPORT_IMAGES_DIR is unset', async () => {
		delete process.env.EXPORT_IMAGES_DIR
		const res = await GET(stubRequest, { params: makeParams('country', ['FR.abc.jpg']) })

		expect(res.status).toBe(404)
	})

	it('returns 404 for an unknown entity', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const res = await GET(stubRequest, { params: makeParams('blog', ['author.jpg']) })

		expect(res.status).toBe(404)
	})

	it('returns 404 for a missing file', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const res = await GET(stubRequest, { params: makeParams('country', ['nonexistent.jpg']) })

		expect(res.status).toBe(404)
	})

	it('returns 404 for path traversal attempt', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir

		const res = await GET(stubRequest, {
			params: makeParams('country', ['..', '..', 'etc', 'passwd'])
		})

		expect(res.status).toBe(404)
	})

	it('returns 404 when normalised path is "." (e.g. [foo, ..])', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const entityDir = path.join(tmpDir, 'country')

		fs.mkdirSync(entityDir, { recursive: true })

		const res = await GET(stubRequest, { params: makeParams('country', ['foo', '..']) })

		expect(res.status).toBe(404)
	})

	it('returns 200 with correct Content-Type for a jpg (country)', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const entityDir = path.join(tmpDir, 'country')

		fs.mkdirSync(entityDir, { recursive: true })
		fs.writeFileSync(path.join(entityDir, 'FR.abc.jpg'), Buffer.from([0xff, 0xd8, 0xff]))

		const res = await GET(stubRequest, { params: makeParams('country', ['FR.abc.jpg']) })

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/jpeg')
		expect(res.headers.get('Cache-Control')).toBe('public, max-age=31536000, immutable')
	})

	it('returns 200 with correct Content-Type for a png (country)', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const entityDir = path.join(tmpDir, 'country')

		fs.mkdirSync(entityDir, { recursive: true })
		fs.writeFileSync(path.join(entityDir, 'DE.123.png'), Buffer.from([0x89, 0x50, 0x4e, 0x47]))

		const res = await GET(stubRequest, { params: makeParams('country', ['DE.123.png']) })

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/png')
	})

	it('returns 200 with correct Content-Type for a jpg (team)', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		const entityDir = path.join(tmpDir, 'team')

		fs.mkdirSync(entityDir, { recursive: true })
		fs.writeFileSync(path.join(entityDir, 'alice-smith.a1b2.jpg'), Buffer.from([0xff, 0xd8, 0xff]))

		const res = await GET(stubRequest, {
			params: makeParams('team', ['alice-smith.a1b2.jpg'])
		})

		expect(res.status).toBe(200)
		expect(res.headers.get('Content-Type')).toBe('image/jpeg')
	})
})
