import fs from 'fs'
import os from 'os'
import path from 'path'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { _resetManifestCache, getEntityImageSrc } from '../entityImage'

let tmpDir: string
const originalEnv = process.env.EXPORT_IMAGES_DIR

function writeManifest(entity: string, manifest: Record<string, string>): void {
	const entityDir = path.join(tmpDir, entity)

	fs.mkdirSync(entityDir, { recursive: true })
	fs.writeFileSync(path.join(entityDir, 'manifest.json'), JSON.stringify(manifest))
}

beforeEach(() => {
	tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'entity-images-test-'))
	_resetManifestCache()
})

afterEach(() => {
	fs.rmSync(tmpDir, { recursive: true, force: true })

	if (originalEnv === undefined) {
		delete process.env.EXPORT_IMAGES_DIR
	} else {
		process.env.EXPORT_IMAGES_DIR = originalEnv
	}

	_resetManifestCache()
})

describe('getEntityImageSrc — country', () => {
	it('returns null when EXPORT_IMAGES_DIR is unset', () => {
		delete process.env.EXPORT_IMAGES_DIR
		expect(getEntityImageSrc('country', 'FR')).toBeNull()
	})

	it('returns null for null/undefined/empty key', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.abc.jpg' })
		expect(getEntityImageSrc('country', null)).toBeNull()
		expect(getEntityImageSrc('country', undefined)).toBeNull()
		expect(getEntityImageSrc('country', '')).toBeNull()
	})

	it('returns null when key is not in manifest', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.abc.jpg' })
		expect(getEntityImageSrc('country', 'DE')).toBeNull()
	})

	it('returns the correct URL for a known code', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.abc.jpg', DE: 'DE.123.png' })
		expect(getEntityImageSrc('country', 'FR')).toBe('/images/country/FR.abc.jpg')
		expect(getEntityImageSrc('country', 'DE')).toBe('/images/country/DE.123.png')
	})

	it('returns null when manifest file is absent', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		// No manifest.json written
		expect(getEntityImageSrc('country', 'FR')).toBeNull()
	})

	it('picks up an updated manifest without cache reset', async () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.v1.jpg' })
		expect(getEntityImageSrc('country', 'FR')).toBe('/images/country/FR.v1.jpg')

		// Simulate the worker writing a new manifest (ensure mtime changes).
		await new Promise(r => setTimeout(r, 10))
		writeManifest('country', { FR: 'FR.v2.jpg' })

		expect(getEntityImageSrc('country', 'FR')).toBe('/images/country/FR.v2.jpg')
	})
})

describe('getEntityImageSrc — team', () => {
	it('returns the correct URL for a team member slug', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('team', {
			'gaspard-lemaire': 'gaspard-lemaire.9f8e7d6c.jpg'
		})
		expect(getEntityImageSrc('team', 'gaspard-lemaire')).toBe('/images/team/gaspard-lemaire.9f8e7d6c.jpg')
	})

	it('returns null when team manifest is absent', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		// No team manifest written
		expect(getEntityImageSrc('team', 'gaspard-lemaire')).toBeNull()
	})

	it('caches country and team manifests independently', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.abc.jpg' })
		writeManifest('team', { 'alice-martin': 'alice-martin.11223344.jpg' })

		expect(getEntityImageSrc('country', 'FR')).toBe('/images/country/FR.abc.jpg')
		expect(getEntityImageSrc('team', 'alice-martin')).toBe('/images/team/alice-martin.11223344.jpg')
		// Cross-entity misses
		expect(getEntityImageSrc('country', 'alice-martin')).toBeNull()
		expect(getEntityImageSrc('team', 'FR')).toBeNull()
	})

	it('resets only the specified entity cache', () => {
		process.env.EXPORT_IMAGES_DIR = tmpDir
		writeManifest('country', { FR: 'FR.abc.jpg' })
		writeManifest('team', { 'alice-martin': 'alice-martin.11223344.jpg' })

		// Warm both caches
		getEntityImageSrc('country', 'FR')
		getEntityImageSrc('team', 'alice-martin')

		// Reset only team
		_resetManifestCache('team')

		// Country cache still valid, team re-reads from disk
		expect(getEntityImageSrc('country', 'FR')).toBe('/images/country/FR.abc.jpg')
	})
})
