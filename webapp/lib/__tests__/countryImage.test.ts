import fs from 'fs'
import os from 'os'
import path from 'path'

import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { _resetManifestCache, getCountryImageSrc } from '../countryImage'

let tmpDir: string
const originalEnv = process.env.COUNTRY_IMAGES_DIR

function writeManifest(manifest: Record<string, string>): void {
	fs.writeFileSync(path.join(tmpDir, 'manifest.json'), JSON.stringify(manifest))
}

beforeEach(() => {
	tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'country-images-test-'))
	_resetManifestCache()
})

afterEach(() => {
	fs.rmSync(tmpDir, { recursive: true, force: true })

	if (originalEnv === undefined) {
		delete process.env.COUNTRY_IMAGES_DIR
	} else {
		process.env.COUNTRY_IMAGES_DIR = originalEnv
	}

	_resetManifestCache()
})

describe('getCountryImageSrc', () => {
	it('returns null when COUNTRY_IMAGES_DIR is unset', () => {
		delete process.env.COUNTRY_IMAGES_DIR
		expect(getCountryImageSrc('FR')).toBeNull()
	})

	it('returns null for null/undefined/empty code', () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		writeManifest({ FR: 'FR.abc.jpg' })
		expect(getCountryImageSrc(null)).toBeNull()
		expect(getCountryImageSrc(undefined)).toBeNull()
		expect(getCountryImageSrc('')).toBeNull()
	})

	it('returns null when code is not in manifest', () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		writeManifest({ FR: 'FR.abc.jpg' })
		expect(getCountryImageSrc('DE')).toBeNull()
	})

	it('returns the correct URL for a known code', () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		writeManifest({ FR: 'FR.abc.jpg', DE: 'DE.123.png' })
		expect(getCountryImageSrc('FR')).toBe('/country-images/FR.abc.jpg')
		expect(getCountryImageSrc('DE')).toBe('/country-images/DE.123.png')
	})

	it('returns null when manifest file is absent', () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		// No manifest.json written
		expect(getCountryImageSrc('FR')).toBeNull()
	})

	it('picks up an updated manifest without cache reset', async () => {
		process.env.COUNTRY_IMAGES_DIR = tmpDir
		writeManifest({ FR: 'FR.v1.jpg' })
		expect(getCountryImageSrc('FR')).toBe('/country-images/FR.v1.jpg')

		// Simulate the worker writing a new manifest (ensure mtime changes).
		await new Promise(r => setTimeout(r, 10))
		writeManifest({ FR: 'FR.v2.jpg' })

		expect(getCountryImageSrc('FR')).toBe('/country-images/FR.v2.jpg')
	})
})
