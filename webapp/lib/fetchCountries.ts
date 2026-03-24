import { CountryListRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

const COUNTRY_LIST_FIELDS = 'Name,Code,PVC Level,VCM Level'

export async function fetchCountries(): Promise<CountryListRecord[]> {
	try {
		const countryTableId = await getTableIdByName('Country')

		if (!countryTableId) {
			return []
		}

		const response = await instance.get<FetchResponseRecords<CountryListRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${countryTableId}/records`,
			{ params: { fields: COUNTRY_LIST_FIELDS, pageSize: 200 }, timeout: 10000 }
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch countries: ${response.statusText}`)
		}

		return response.data.records ?? []
	} catch (error) {
		console.error('Error fetching countries:', error)
		return []
	}
}
