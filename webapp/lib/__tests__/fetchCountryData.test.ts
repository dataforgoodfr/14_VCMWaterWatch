import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock dependencies before importing the module under test
vi.mock('../fetchMetaTables', () => ({
	getTableIdByName: vi.fn()
}))
vi.mock('../instance', () => ({
	instance: { get: vi.fn() }
}))

import { getTableIdByName } from '../fetchMetaTables'
import { instance } from '../instance'
import { fetchCountryDataForCountry } from '../fetchCountryData'
import type { CountryDataRecord } from '@/types/apiTypes'

const mockGetTableIdByName = vi.mocked(getTableIdByName)
// eslint-disable-next-line @typescript-eslint/unbound-method
const mockGet = vi.mocked(instance.get)

let nextId = 1

function makeRow(overrides: Partial<CountryDataRecord['fields']> = {}): CountryDataRecord {
	const id = nextId++

	return {
		id,
		fields: {
			Id: id,
			Type: 'stat',
			Order: 1,
			Title: 'Network affected',
			Content: '42%',
			...overrides
		}
	}
}

describe('fetchCountryDataForCountry', () => {
	beforeEach(() => {
		vi.clearAllMocks()
		nextId = 1
		process.env.NOCODB_BASE_ID = 'base123'
	})

	it('returns empty array when table id cannot be resolved', async () => {
		mockGetTableIdByName.mockResolvedValue(null)

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toEqual([])
		expect(mockGet).not.toHaveBeenCalled()
	})

	it('returns rows for the requested locale', async () => {
		const rows = [makeRow({ Order: 1 }), makeRow({ Order: 2 })]

		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet.mockResolvedValue({ status: 200, data: { records: rows } })

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toEqual(rows)
		// Should have called get with the correct where clause
		const callUrl = mockGet.mock.calls[0]?.[0]

		expect(callUrl).toContain('Country_id%2Ceq%2C7')
		expect(callUrl).toContain('Language%2Ceq%2Cen')
	})

	it('falls back to en when locale returns no rows', async () => {
		const enRows = [makeRow()]

		mockGetTableIdByName.mockResolvedValue('table-abc')
		// First call (fr) returns empty, second call (en) returns rows
		mockGet
			.mockResolvedValueOnce({ status: 200, data: { records: [] } })
			.mockResolvedValueOnce({ status: 200, data: { records: enRows } })

		const result = await fetchCountryDataForCountry(7, 'fr')

		expect(result).toEqual(enRows)
		expect(mockGet).toHaveBeenCalledTimes(2)
	})

	it('does not make a second call when locale is already en and returns empty', async () => {
		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet.mockResolvedValue({ status: 200, data: { records: [] } })

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toEqual([])
		expect(mockGet).toHaveBeenCalledTimes(1)
	})

	it('returns empty array on network error', async () => {
		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet.mockRejectedValue(new Error('Network failure'))

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toEqual([])
	})
})
