import type { CountryDataRecord, CountryDetailRecord } from '@/types/apiTypes'
import { fetchCountryDataForCountry } from './fetchCountryData'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

const COUNTRY_DETAIL_FIELDS = 'Name,Code,Geometry,Image'

export interface CountryWithData {
	country: CountryDetailRecord
	data: CountryDataRecord[]
}

export async function fetchCountryByCode(code: string, locale = 'en'): Promise<CountryWithData | null> {
	const trimmed = code.trim()

	if (!trimmed) {
		return null
	}

	try {
		const countryTableId = await getTableIdByName('Country')

		if (!countryTableId) {
			return null
		}

		const where = `(Code,eq,${trimmed})`

		const response = await instance.get<FetchResponseRecords<CountryDetailRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${countryTableId}/records?where=${encodeURIComponent(where)}`,
			{ params: { fields: COUNTRY_DETAIL_FIELDS }, timeout: 20000 }
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch country: ${response.statusText}`)
		}

		const country = response.data.records[0] ?? null

		if (!country) {
			return null
		}

		// Note: fetchCountryDataForCountry self-handles its errors (returns []),
		// so the surrounding try/catch here only guards the Country lookup.
		const data = await fetchCountryDataForCountry(country.id, locale)

		return { country, data }
	} catch (error) {
		console.error('Error fetching country by code:', error)
		return null
	}
}
