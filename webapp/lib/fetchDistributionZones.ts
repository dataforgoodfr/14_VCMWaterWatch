import { CountryMapRecord, DistributionZoneGeoLimitedRecord, DistributionZoneMapRecord } from '@/types/apiTypes'
import { FetchResponseRecords, instance } from './instance'
import { getTableIdByName } from './fetchMetaTables'

const ZONE_MAP_FIELDS = 'Name,Code,Geometry,Municipality Geometries,PVC Level,VCM Level,Country'

const COUNTRY_MAP_FIELDS = 'Name,Code,Geometry,PVC Level,VCM Level'

export interface FetchDistributionZonesParams {
	query: string
}

export async function fetchDistributionZonesForMap() {
	try {
		const DistributionZoneId = await getTableIdByName('DistributionZone')

		if (!DistributionZoneId) {
			return null
		}

		const response = await instance.get<FetchResponseRecords<DistributionZoneMapRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${DistributionZoneId}/records`,
			{ params: { fields: ZONE_MAP_FIELDS, pageSize: 500 }, timeout: 15000 }
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch distribution zones: ${response.statusText}`)
		}

		return response.data.records || null
	} catch (error) {
		console.error('Error fetching distribution zones for map:', error)
		return null
	}
}

export async function fetchCountriesForMap() {
	try {
		const CountryId = await getTableIdByName('Country')

		if (!CountryId) {
			return null
		}

		const response = await instance.get<FetchResponseRecords<CountryMapRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${CountryId}/records`,
			{ params: { fields: COUNTRY_MAP_FIELDS, pageSize: 100 }, timeout: 15000 }
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch countries: ${response.statusText}`)
		}

		return response.data.records || null
	} catch (error) {
		console.error('Error fetching countries for map:', error)
		return null
	}
}

export async function fetchDistributionZonesLimitedFieldsGeo({ query }: FetchDistributionZonesParams) {
	try {
		const DistributionZoneId = await getTableIdByName('DistributionZone')

		const distributionZonesResponse = await instance.get<FetchResponseRecords<DistributionZoneGeoLimitedRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${DistributionZoneId}/records?where=(SearchIndex,like,${query})&fields=Name,Country,ActorName&l=10`
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
