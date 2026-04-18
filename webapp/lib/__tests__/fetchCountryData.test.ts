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
		// sort must be a JSON array (v3 API requirement), ascending on Order
		expect(callUrl).toMatch(/sort=.*Order/i)
		expect(decodeURIComponent(callUrl ?? '')).toContain('[{"direction":"asc","field":"Order"}]')
	})

	it('falls back to en when requested locale has no rows', async () => {
		const frRows: CountryDataRecord[] = []
		const enRows = [makeRow({ Order: 1 })]

		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet
			.mockResolvedValueOnce({ status: 200, data: { records: frRows } })
			.mockResolvedValueOnce({ status: 200, data: { records: enRows } })

		const result = await fetchCountryDataForCountry(7, 'fr')

		expect(result).toEqual(enRows)
		expect(mockGet).toHaveBeenCalledTimes(2)
		expect(mockGet.mock.calls[0]?.[0]).toContain('Language%2Ceq%2Cfr')
		expect(mockGet.mock.calls[1]?.[0]).toContain('Language%2Ceq%2Cen')
	})

	it('does not retry when locale is already en and returns empty', async () => {
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

	it('filters out rows with empty or whitespace-only Content', async () => {
		const rows = [
			makeRow({ Content: 'real content', Order: 1 }),
			makeRow({ Content: '', Order: 2 }),
			makeRow({ Content: '   ', Order: 3 }),
			makeRow({ Content: null, Order: 4 })
		]

		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet.mockResolvedValue({ status: 200, data: { records: rows } })

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toHaveLength(1)
		expect(result[0]?.fields.Content).toBe('real content')
	})

	it('returns empty array when server responds with non-200 status', async () => {
		mockGetTableIdByName.mockResolvedValue('table-abc')
		mockGet.mockResolvedValue({ status: 500, statusText: 'Internal Server Error' })

		const result = await fetchCountryDataForCountry(7, 'en')

		expect(result).toEqual([])
	})
})
