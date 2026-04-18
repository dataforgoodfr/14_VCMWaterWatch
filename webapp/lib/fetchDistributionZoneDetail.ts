import { DistributionZoneDetailRecord } from '@/types/apiTypes'

export async function fetchDistributionZoneDetail(id: number): Promise<DistributionZoneDetailRecord | null> {
	try {
		const response = await fetch(`/api/distributionzone/${id}`)

		if (!response.ok) {
			throw new Error(`Failed to fetch distribution zone detail: ${response.statusText}`)
		}

		const data = (await response.json()) as DistributionZoneDetailRecord

		if (!data?.fields || typeof data.fields !== 'object') {
			console.error('Invalid distribution zone detail response: missing fields')
			return null
		}

		return data
	} catch (error) {
		console.error('Error fetching distribution zone detail:', error)
		return null
	}
}
