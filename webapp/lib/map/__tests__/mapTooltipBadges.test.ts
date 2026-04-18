import { describe, it, expect } from 'vitest'

import {
	pvcCountryTooltipBadgeFromTileProperty,
	pvcTooltipBadgeFromTileProperty,
	rawTooltipPvcFromFeatureProperties,
	rawTooltipVcmFromFeatureProperties,
	vcmCountryTooltipBadgeFromTileProperty,
	vcmTooltipBadgeFromTileProperty
} from '../mapTooltipPvcBadge'

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

describe('pvcTooltipBadgeFromTileProperty', () => {
	it('matches case-insensitively', () => {
		const badge = pvcTooltipBadgeFromTileProperty('PVC, Pre-1980')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('PVC present, pre-1980')
	})

	it('matches lowercase variant', () => {
		const badge = pvcTooltipBadgeFromTileProperty('pvc, pre-1980')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('PVC present, pre-1980')
	})

	it('returns null for unrecognized', () => {
		expect(pvcTooltipBadgeFromTileProperty('bogus')).toBeNull()
	})
})

describe('rawTooltipPvcFromFeatureProperties', () => {
	it('reads pvc_level from tile properties', () => {
		expect(rawTooltipPvcFromFeatureProperties({ pvc_level: 'No PVC' })).toBe('No PVC')
	})

	it('returns null when missing', () => {
		expect(rawTooltipPvcFromFeatureProperties({})).toBeNull()
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

describe('pvcCountryTooltipBadgeFromTileProperty', () => {
	it('returns red badge for "known_length"', () => {
		const badge = pvcCountryTooltipBadgeFromTileProperty('known_length')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('PVC network length known')
		expect(badge!.style.borderColor).toBe('#dc2626')
	})

	it('returns gray badge for "unknown_length"', () => {
		const badge = pvcCountryTooltipBadgeFromTileProperty('unknown_length')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('PVC network length unknown')
		expect(badge!.style.borderColor).toBe('#64748b')
	})

	it('returns gray badge for "unknown"', () => {
		const badge = pvcCountryTooltipBadgeFromTileProperty('unknown')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('PVC presence unknown')
		expect(badge!.style.borderColor).toBe('#64748b')
	})

	it('returns null for null/empty/zone-style values', () => {
		expect(pvcCountryTooltipBadgeFromTileProperty(null)).toBeNull()
		expect(pvcCountryTooltipBadgeFromTileProperty('')).toBeNull()
		expect(pvcCountryTooltipBadgeFromTileProperty('No PVC')).toBeNull()
	})
})

describe('vcmCountryTooltipBadgeFromTileProperty', () => {
	it('returns gray badge for "unknown"', () => {
		const badge = vcmCountryTooltipBadgeFromTileProperty('unknown')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('No VCM data')
		expect(badge!.style.borderColor).toBe('#64748b')
	})

	it('returns yellow badge for "positive_analysis"', () => {
		const badge = vcmCountryTooltipBadgeFromTileProperty('positive_analysis')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('Positive VCM analysis')
		expect(badge!.style.borderColor).toBe('#a16207')
	})

	it('returns orange badge for "confirmed_localized_contamination"', () => {
		const badge = vcmCountryTooltipBadgeFromTileProperty('confirmed_localized_contamination')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('Localized VCM contamination')
		expect(badge!.style.borderColor).toBe('#ea580c')
	})

	it('returns red badge for "confirmed_widespread_contamination"', () => {
		const badge = vcmCountryTooltipBadgeFromTileProperty('confirmed_widespread_contamination')

		expect(badge).not.toBeNull()
		expect(badge!.label).toBe('Widespread VCM contamination')
		expect(badge!.style.borderColor).toBe('#dc2626')
	})

	it('returns null for null/empty/zone-style values', () => {
		expect(vcmCountryTooltipBadgeFromTileProperty(null)).toBeNull()
		expect(vcmCountryTooltipBadgeFromTileProperty('')).toBeNull()
		expect(vcmCountryTooltipBadgeFromTileProperty('> 0.5 mcg/L')).toBeNull()
	})
})
