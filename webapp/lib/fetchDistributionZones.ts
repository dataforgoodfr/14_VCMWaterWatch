import { DistributionZoneGeoLimitedRecord } from '@/types/apiTypes'
import { FetchResponseRecords, instance } from './instance'
import { getTableIdByName } from './fetchMetaTables'

export interface FetchDistributionZonesParams {
	query: string
}

export async function fetchDistributionZonesLimitedFieldsGeo({ query }: FetchDistributionZonesParams) {
	try {
		const DistributionZoneId = await getTableIdByName('DistributionZone')

		const distributionZonesResponse = await instance.get<FetchResponseRecords<DistributionZoneGeoLimitedRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${DistributionZoneId}/records?where=(Name,like,${query})&fields=Name,Country&l=10`
		)

		if (distributionZonesResponse.status !== 200) {
			throw new Error(`Failed to fetch distribution zones: ${distributionZonesResponse.statusText}`)
		}

		const distributionZonesData: FetchResponseRecords<DistributionZoneGeoLimitedRecord> = distributionZonesResponse.data

		return distributionZonesData.records || null
	} catch (error) {
		console.error('Error fetching distribution zones:', error)
		return null
	}
}
