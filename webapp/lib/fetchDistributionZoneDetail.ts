import { DistributionZoneDetailRecord } from '@/types/apiTypes'

export async function fetchDistributionZoneDetail(id: number): Promise<DistributionZoneDetailRecord | null> {
	try {
		const response = await fetch(`/api/distributionzone/${id}`)

		if (!response.ok) {
			throw new Error(`Failed to fetch distribution zone detail: ${response.statusText}`)
		}

		return (await response.json()) as DistributionZoneDetailRecord
	} catch (error) {
		console.error('Error fetching distribution zone detail:', error)
		return null
	}
}
