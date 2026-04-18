import { describe, it, expect } from 'vitest'
import { buildMapFeatureFillColor, buildMapFeatureLineColor } from '../distributionZoneRisk'
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
