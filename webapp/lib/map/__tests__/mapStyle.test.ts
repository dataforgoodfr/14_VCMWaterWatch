import { describe, it, expect, vi, afterEach } from 'vitest'

import { createBaseMapStyle, COUNTRIES_FILL_LAYER_ID } from '../mapStyle'

describe('createBaseMapStyle', () => {
	afterEach(() => {
		vi.restoreAllMocks()
	})

	it('returns a synchronous StyleSpecification (no network)', () => {
		const style = createBaseMapStyle()

		// Would throw if a Promise were returned
		expect(style.version).toBe(8)
		expect(style.sources).toBeDefined()
		expect(style.layers).toBeDefined()
	})

	it('merges bundled basemap sources with thematic sources', () => {
		const style = createBaseMapStyle()
		const sourceKeys = Object.keys(style.sources)

		expect(sourceKeys).toContain('openmaptiles')
		expect(sourceKeys).toContain('world-countries')
		expect(sourceKeys).toContain('countries-vector')
		expect(sourceKeys).toContain('distribution-zones-vector')
	})

	it('preserves glyphs and sprite from the bundled style', () => {
		const style = createBaseMapStyle()

		expect(style.glyphs).toContain('openfreemap.org')
		expect(style.sprite).toBeTruthy()
	})

	it('adds OSM attribution to basemap sources', () => {
		const style = createBaseMapStyle()
		const src = style.sources.openmaptiles as Record<string, unknown>

		expect(String(src.attribution)).toContain('OpenStreetMap')
	})

	it('filters layers per source-layer allow-list (excludes landuse, building, boundary, minor roads)', () => {
		const style = createBaseMapStyle()
		const ids = style.layers.map(l => l.id)

		// Basemap layers from disallowed source-layers must not appear
		const basemapSourceKeys = new Set(
			Object.keys(style.sources).filter(
				k => !['world-countries', 'countries-vector', 'distribution-zones-vector'].includes(k)
			)
		)

		for (const layer of style.layers) {
			if (
				'source' in layer &&
				typeof layer.source === 'string' &&
				basemapSourceKeys.has(layer.source) &&
				'source-layer' in layer &&
				typeof layer['source-layer'] === 'string'
			) {
				const sl = layer['source-layer']

				expect(
					['water', 'waterway', 'water_name', 'place', 'transportation_name', 'transportation'].includes(sl),
					`Unexpected source-layer "${sl}" in layer "${layer.id}"`
				).toBe(true)
			}
		}

		// Transportation: only motorway / major ids may appear
		for (const layer of style.layers) {
			if ('source-layer' in layer && layer['source-layer'] === 'transportation') {
				expect(
					layer.id.startsWith('highway_motorway') || layer.id.startsWith('highway_major'),
					`Minor-road layer "${layer.id}" should have been excluded`
				).toBe(true)
			}
		}

		// Our thematic layers must all be present
		expect(ids).toContain(COUNTRIES_FILL_LAYER_ID)
		expect(ids).toContain('distribution-zones-fill')
		expect(ids).toContain('countries-outline')
	})

	it('orders layers: water/roads → thematic fills → labels', () => {
		const style = createBaseMapStyle()
		const idx = (id: string) => style.layers.findIndex(l => l.id === id)

		const countriesFill = idx(COUNTRIES_FILL_LAYER_ID)
		const distZoneFill = idx('distribution-zones-fill')

		// At least one non-symbol basemap layer must precede our fills
		const firstBasemapNonSymbol = style.layers.findIndex(
			l =>
				l.type !== 'symbol' &&
				!['world-countries', 'countries-vector', 'distribution-zones-vector'].includes(
					'source' in l && typeof l.source === 'string' ? l.source : ''
				) &&
				l.id !== 'background'
		)

		expect(firstBasemapNonSymbol).toBeGreaterThanOrEqual(0)
		expect(firstBasemapNonSymbol).toBeLessThan(countriesFill)

		// All symbol layers (labels) must follow our thematic fills
		const firstSymbol = style.layers.findIndex(l => l.type === 'symbol')

		if (firstSymbol !== -1) {
			expect(distZoneFill).toBeLessThan(firstSymbol)
		}
	})

	it('does not warn about transportation id-prefix when using the bundled style', () => {
		// eslint-disable-next-line @typescript-eslint/no-empty-function
		const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

		createBaseMapStyle()

		expect(warnSpy).not.toHaveBeenCalled()
	})

	it('returns the same object reference on repeated calls (module-scope result)', () => {
		const a = createBaseMapStyle()
		const b = createBaseMapStyle()

		expect(a).toBe(b)
	})
})
