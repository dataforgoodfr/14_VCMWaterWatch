import type { CountryDataRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

const COUNTRY_DATA_FIELDS = 'Id,Type,Order,Title,Content'

/**
 * Fetch all CountryData rows for a given Country_id and locale (Language).
 * Falls back to 'en' if no rows are found for the requested locale.
 */
export async function fetchCountryDataForCountry(countryId: number, locale: string): Promise<CountryDataRecord[]> {
	try {
		const tableId = await getTableIdByName('CountryData')

		if (!tableId) {
			return []
		}

		const rows = await fetchRows(tableId, countryId, locale)

		// Fall back to 'en' if the requested locale returned nothing
		if (rows.length === 0 && locale !== 'en') {
			return fetchRows(tableId, countryId, 'en')
		}

		return rows
	} catch (error) {
		console.error('Error fetching CountryData:', error)
		return []
	}
}

async function fetchRows(tableId: string, countryId: number, language: string): Promise<CountryDataRecord[]> {
	const where = `(Country_id,eq,${countryId})~and(Language,eq,${language})`
	const sort = JSON.stringify([{ direction: 'asc', field: 'Order' }])

	const response = await instance.get<FetchResponseRecords<CountryDataRecord>>(
		`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records?where=${encodeURIComponent(where)}&sort=${encodeURIComponent(sort)}`,
		{
			params: { fields: COUNTRY_DATA_FIELDS, pageSize: 100 },
			timeout: 20000
		}
	)

	if (response.status !== 200) {
		throw new Error(`Failed to fetch CountryData: ${response.statusText}`)
	}

	// Drop rows with no Content — NocoDB stores placeholder rows per Type/Order even when empty
	return (response.data.records ?? []).filter(r => (r.fields.Content ?? '').trim() !== '')
}
