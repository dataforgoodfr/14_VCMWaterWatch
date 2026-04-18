import { describe, it, expect } from 'vitest'
import { buildMapFeatureFillColor, buildMapFeatureLineColor, distributionZoneTierFilter } from '../distributionZoneRisk'
import { colorCodeConfig } from '@/lib/colorCode'

describe('buildMapFeatureFillColor', () => {
	it('returns a MapLibre match expression without a resolve callback', () => {
		const expr = buildMapFeatureFillColor()
		expect(expr[0]).toBe('match')
		// Should contain hex values from colorCodeConfig
		expect(expr).toContain(colorCodeConfig.red.bg)
		expect(expr).toContain(colorCodeConfig.orange.bg)
		expect(expr).toContain(colorCodeConfig.yellow.bg)
		expect(expr).toContain(colorCodeConfig.green.bg)
		expect(expr).toContain(colorCodeConfig.gray.bg)
	})
})

describe('buildMapFeatureLineColor', () => {
	it('returns a MapLibre match expression without a resolve callback', () => {
		const expr = buildMapFeatureLineColor()
		expect(expr[0]).toBe('match')
		expect(expr).toContain(colorCodeConfig.red.border)
		expect(expr).toContain(colorCodeConfig.orange.border)
		expect(expr).toContain(colorCodeConfig.yellow.border)
		expect(expr).toContain(colorCodeConfig.green.border)
		expect(expr).toContain(colorCodeConfig.gray.border)
	})
})

describe('distributionZoneTierFilter', () => {
	it('confirme matches only red', () => {
		const f = distributionZoneTierFilter('confirme')
		expect(f).toEqual(['==', expect.anything(), 'red'])
	})

	it('probable matches orange and yellow (multi-value any)', () => {
		const f = distributionZoneTierFilter('probable')
		expect(f[0]).toBe('any')
		const inner = f as unknown[]
		const matchedValues = inner.slice(1).map((clause: unknown) => (clause as unknown[])[2])
		expect(matchedValues).toContain('orange')
		expect(matchedValues).toContain('yellow')
	})

	it('absent matches only green', () => {
		const f = distributionZoneTierFilter('absent')
		expect(f).toEqual(['==', expect.anything(), 'green'])
	})

	it('inconnu matches gray, grey, and empty string', () => {
		const f = distributionZoneTierFilter('inconnu')
		expect(f[0]).toBe('any')
		const inner = f as unknown[]
		const matchedValues = inner.slice(1).map((clause: unknown) => (clause as unknown[])[2])
		expect(matchedValues).toContain('gray')
		expect(matchedValues).toContain('grey')
		expect(matchedValues).toContain('')
	})
})
