import type { Record as NocoRecord } from '@/types/apiTypes'

import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

interface MunicipalityNameFields {
	Name: string
}

/**
 * Loads municipality display names for a distribution zone via the Municipality → DistributionZone link.
 * Does not use geometry fields.
 */
export async function fetchMunicipalityNamesForDistributionZone(distributionZoneId: number): Promise<string[]> {
	try {
		const tableId = await getTableIdByName('Municipality')

		if (!tableId) {
			return []
		}

		const response = await instance.get<FetchResponseRecords<NocoRecord<MunicipalityNameFields>>>(
			`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records?where=(DistributionZone,eq,${distributionZoneId})&fields=Name&l=2000`,
			{ timeout: 20000 }
		)

		if (response.status !== 200 || !response.data.records?.length) {
			return []
		}

		const names = response.data.records.map(r => r.fields.Name).filter(Boolean)
		return [...new Set(names)].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }))
	} catch (error) {
		console.error('Error fetching municipalities for distribution zone:', error)
		return []
	}
}
