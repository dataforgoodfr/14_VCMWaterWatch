import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Mock the instance and dependencies before importing fetchTeam
vi.mock('@/lib/instance', () => ({
	instance: {
		get: vi.fn()
	}
}))

vi.mock('@/lib/fetchMetaTables', () => ({
	getTableIdByName: vi.fn()
}))

vi.mock('@/lib/entityImage', () => ({
	getEntityImageSrc: vi.fn().mockReturnValue(null)
}))

import { instance } from '@/lib/instance'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { fetchTeam } from '../fetchTeam'

// eslint-disable-next-line @typescript-eslint/unbound-method
const mockGet = vi.mocked(instance.get)
const mockGetTableId = vi.mocked(getTableIdByName)

beforeEach(() => {
	mockGetTableId.mockResolvedValue('table-id-123')
})

afterEach(() => {
	vi.clearAllMocks()
})

describe('fetchTeam', () => {
	it('returns empty array when Team table not found', async () => {
		mockGetTableId.mockResolvedValue(null)
		const result = await fetchTeam()

		expect(result).toEqual([])
	})

	it('returns empty array on network error', async () => {
		mockGet.mockRejectedValue(new Error('Network error'))
		const result = await fetchTeam()

		expect(result).toEqual([])
	})

	it('maps NocoDB records to TeamMember', async () => {
		mockGet.mockResolvedValue({
			status: 200,
			data: {
				records: [
					{
						Id: 1,
						Name: 'Alice Martin',
						Expertise: 'Developer',
						City: 'Paris',
						SubTeam: 'project',
						nc_order: 1
					}
				]
			}
		})

		const result = await fetchTeam()

		expect(result).toHaveLength(1)
		expect(result[0]).toMatchObject({
			id: 1,
			name: 'Alice Martin',
			role: 'Developer',
			city: 'Paris',
			subTeam: 'project',
			order: 1
		})
	})

	it('skips records without a name', async () => {
		mockGet.mockResolvedValue({
			status: 200,
			data: {
				records: [
					{ Id: 1, Name: null, Expertise: 'Developer' },
					{ Id: 2, Name: 'Bob', Expertise: 'Designer' }
				]
			}
		})

		const result = await fetchTeam()

		expect(result).toHaveLength(1)
		expect(result[0].name).toBe('Bob')
	})

	it('handles missing optional fields gracefully', async () => {
		mockGet.mockResolvedValue({
			status: 200,
			data: {
				records: [{ Id: 1, Name: 'Charlie' }]
			}
		})

		const result = await fetchTeam()

		expect(result[0]).toMatchObject({
			id: 1,
			name: 'Charlie',
			role: '',
			city: null,
			subTeam: null,
			order: 0
		})
	})
})
