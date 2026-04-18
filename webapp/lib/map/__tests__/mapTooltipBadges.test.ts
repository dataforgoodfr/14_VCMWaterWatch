import { describe, it, expect } from 'vitest'

import { vcmTooltipBadgeFromTileProperty, rawTooltipVcmFromFeatureProperties } from '../mapTooltipPvcBadge'

describe('vcmTooltipBadgeFromTileProperty', () => {
	it('returns red badge for "> 0.5 mcg/L"', () => {
		const badge = vcmTooltipBadgeFromTileProperty('> 0.5 mcg/L')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('VCM level > 0.5 mcg/L')
		expect(badge!.style.borderColor).toBe('#dc2626')
	})

	it('returns green badge for "< 0.5 mcg/L"', () => {
		const badge = vcmTooltipBadgeFromTileProperty('< 0.5 mcg/L')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('VCM level < 0.5 mcg/L')
		expect(badge!.style.borderColor).toBe('#16a34a')
	})

	it('returns yellow badge for "No analysis"', () => {
		const badge = vcmTooltipBadgeFromTileProperty('No analysis')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('No VCM analysis')
		expect(badge!.style.borderColor).toBe('#a16207')
	})

	it('returns gray badge for "Unknown"', () => {
		const badge = vcmTooltipBadgeFromTileProperty('Unknown')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('VCM level unknown')
		expect(badge!.style.borderColor).toBe('#64748b')
	})

	it('returns null for null/empty/unrecognized', () => {
		expect(vcmTooltipBadgeFromTileProperty(null)).toBeNull()
		expect(vcmTooltipBadgeFromTileProperty('')).toBeNull()
		expect(vcmTooltipBadgeFromTileProperty('bogus')).toBeNull()
	})
})

describe('rawTooltipVcmFromFeatureProperties', () => {
	it('reads vcm_level from tile properties', () => {
		expect(rawTooltipVcmFromFeatureProperties({ vcm_level: '> 0.5 mcg/L' })).toBe('> 0.5 mcg/L')
	})

	it('returns null when missing', () => {
		expect(rawTooltipVcmFromFeatureProperties({})).toBeNull()
	})
})
