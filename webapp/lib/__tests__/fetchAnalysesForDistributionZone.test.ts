import { describe, it, expect } from 'vitest'

import { formatAnalysisDate } from '../fetchAnalysesForDistributionZone'

describe('formatAnalysisDate', () => {
	it('formats ISO date to DD/MM/YYYY', () => {
		expect(formatAnalysisDate('2026-04-22')).toBe('22/04/2026')
	})

	it('formats ISO datetime to DD/MM/YYYY', () => {
		expect(formatAnalysisDate('2026-04-22T10:30:00Z')).toBe('22/04/2026')
	})

	it('returns raw string for unparseable dates', () => {
		expect(formatAnalysisDate('not-a-date')).toBe('not-a-date')
	})

	it('returns "—" for null/undefined', () => {
		expect(formatAnalysisDate(null)).toBe('—')
		expect(formatAnalysisDate(undefined)).toBe('—')
	})
})
