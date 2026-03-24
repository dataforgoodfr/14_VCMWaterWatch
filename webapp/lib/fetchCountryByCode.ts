import type { CountryDetailRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

const COUNTRY_DETAIL_FIELDS = 'Name,Code,Geometry,PVC Level,VCM Level,Distribution Zones,Municipalities,Actors'

export async function fetchCountryByCode(code: string): Promise<CountryDetailRecord | null> {
	const trimmed = code.trim()

	if (!trimmed) {
		return null
	}

	try {
		const countryTableId = await getTableIdByName('Country')

		if (!countryTableId) {
			return null
		}

		const response = await instance.get<FetchResponseRecords<CountryDetailRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${countryTableId}/records?where=(Code,eq,${trimmed})`,
			{ params: { fields: COUNTRY_DETAIL_FIELDS }, timeout: 20000 }
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch country: ${response.statusText}`)
		}

		return response.data.records[0] ?? null
	} catch (error) {
		console.error('Error fetching country by code:', error)
		return null
	}
}
