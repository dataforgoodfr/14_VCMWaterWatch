import { beforeEach, describe, expect, it, vi } from 'vitest'

// Mock the entityImage module before importing fetchTeam
vi.mock('../entityImage', () => ({
	getEntityImageSrc: vi.fn((entity: string, key: string) => {
		if (key === 'alice-smith') {
			return '/images/team/alice-smith.abc.jpg'
		}

		if (key === 'eve-muller') {
			return '/images/team/eve-muller.def.jpg'
		}

		return null
	})
}))

// Mock the instance module
vi.mock('../instance', () => ({
	instance: { get: vi.fn() }
}))

// Mock the meta tables module so fetchTeam resolves a Team table id
vi.mock('../fetchMetaTables', () => ({
	getTableIdByName: vi.fn(() => Promise.resolve('test-team-table-id'))
}))

import { instance } from '../instance'
import { fetchTeam } from '../fetchTeam'

// Extract the mock after the import so hoisting is not an issue
// eslint-disable-next-line @typescript-eslint/unbound-method
const mockGet = vi.mocked(instance.get)

function makeRow(
	overrides: Partial<{
		id: number
		Name: string | null
		Expertise: string | null
		City: string | null
		Squad: string | null
		nc_order: number | null
	}> = {}
) {
	const { id = 1, ...fieldOverrides } = overrides

	return {
		id,
		fields: {
			Name: 'Alice Smith',
			Expertise: 'Hydrology',
			City: 'Paris',
			Image: null,
			Squad: 'project',
			nc_order: 1,
			...fieldOverrides
		}
	}
}

beforeEach(() => {
	vi.clearAllMocks()
})

describe('fetchTeam', () => {
	it('returns an empty array on network error', async () => {
		mockGet.mockRejectedValueOnce(new Error('Network error'))
		const result = await fetchTeam()

		expect(result).toEqual([])
	})

	it('returns an empty array on non-200 response', async () => {
		mockGet.mockResolvedValueOnce({ status: 500, statusText: 'Internal Server Error', data: {} })
		const result = await fetchTeam()

		expect(result).toEqual([])
	})

	it('maps a row to TeamMember correctly', async () => {
		mockGet.mockResolvedValueOnce({ status: 200, data: { records: [makeRow()] } })

		const result = await fetchTeam()

		expect(result).toHaveLength(1)
		expect(result[0]).toEqual({
			id: '1',
			name: 'Alice Smith',
			role: 'Hydrology',
			city: 'Paris',
			subTeam: 'project',
			imageSrc: '/images/team/alice-smith.abc.jpg'
		})
	})

	it('slugifies accented names for image lookup', async () => {
		mockGet.mockResolvedValueOnce({
			status: 200,
			data: { records: [makeRow({ id: 2, Name: 'Ève Müller' })] }
		})

		const result = await fetchTeam()

		expect(result[0].imageSrc).toBe('/images/team/eve-muller.def.jpg')
	})

	it('filters out rows without a Name', async () => {
		mockGet.mockResolvedValueOnce({
			status: 200,
			data: { records: [makeRow({ Name: null }), makeRow({ id: 2, Name: 'Alice Smith' })] }
		})

		const result = await fetchTeam()

		expect(result).toHaveLength(1)
		expect(result[0].name).toBe('Alice Smith')
	})

	it('sets null imageSrc when no image is available', async () => {
		mockGet.mockResolvedValueOnce({
			status: 200,
			data: { records: [makeRow({ Name: 'Unknown Member' })] }
		})

		const result = await fetchTeam()

		expect(result[0].imageSrc).toBeNull()
	})

	it('sets null city when City field is absent', async () => {
		mockGet.mockResolvedValueOnce({ status: 200, data: { records: [makeRow({ City: null })] } })

		const result = await fetchTeam()

		expect(result[0].city).toBeNull()
	})

	it('uses nc_order sort parameter in the API call', async () => {
		mockGet.mockResolvedValueOnce({ status: 200, data: { records: [] } })
		await fetchTeam()
		expect(mockGet).toHaveBeenCalledWith(
			expect.stringContaining('/records'),
			expect.objectContaining({
				params: expect.objectContaining({ sort: JSON.stringify([{ field: 'nc_order', direction: 'asc' }]) }) as Record<
					string,
					unknown
				>
			}) as Record<string, unknown>
		)
	})
})
