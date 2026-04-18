import { describe, it, expect } from 'vitest'
import { colorCodeConfig, riskTierConfig, type MapRiskTier } from '../colorCode'

describe('riskTierConfig', () => {
	const EXPECTED_TIERS: MapRiskTier[] = ['confirme', 'probable', 'absent', 'inconnu']

	it('has all four tiers', () => {
		expect(Object.keys(riskTierConfig).sort()).toEqual([...EXPECTED_TIERS].sort())
	})

	it.each(EXPECTED_TIERS)('%s has label, bg, border as hex strings', (tier) => {
		const c = riskTierConfig[tier]
		expect(c.label).toBeTruthy()
		expect(c.bg).toMatch(/^#[0-9a-fA-F]{6}$/)
		expect(c.border).toMatch(/^#[0-9a-fA-F]{6}$/)
	})

	it('confirme derives from colorCodeConfig.red', () => {
		expect(riskTierConfig.confirme.bg).toBe(colorCodeConfig.red.bg)
		expect(riskTierConfig.confirme.border).toBe(colorCodeConfig.red.border)
	})

	it('probable derives from colorCodeConfig.orange', () => {
		expect(riskTierConfig.probable.bg).toBe(colorCodeConfig.orange.bg)
		expect(riskTierConfig.probable.border).toBe(colorCodeConfig.orange.border)
	})

	it('absent derives from colorCodeConfig.green', () => {
		expect(riskTierConfig.absent.bg).toBe(colorCodeConfig.green.bg)
		expect(riskTierConfig.absent.border).toBe(colorCodeConfig.green.border)
	})

	it('inconnu derives from colorCodeConfig.gray', () => {
		expect(riskTierConfig.inconnu.bg).toBe(colorCodeConfig.gray.bg)
		expect(riskTierConfig.inconnu.border).toBe(colorCodeConfig.gray.border)
	})
})
