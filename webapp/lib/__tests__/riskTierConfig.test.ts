import { describe, it, expect } from 'vitest'
import { riskTierConfig, type MapRiskTier } from '../colorCode'

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

	it('confirme derives from red', () => {
		expect(riskTierConfig.confirme.border).toBe('#dc2626')
	})

	it('probable derives from orange', () => {
		expect(riskTierConfig.probable.border).toBe('#ea580c')
	})

	it('absent derives from green', () => {
		expect(riskTierConfig.absent.border).toBe('#16a34a')
	})

	it('inconnu derives from gray', () => {
		expect(riskTierConfig.inconnu.border).toBe('#64748b')
	})
})
