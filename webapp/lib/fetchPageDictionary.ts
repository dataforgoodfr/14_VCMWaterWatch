import { PageFieldRecord, TranslationRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

interface FetchPageDictionaryParams {
	slug: string
	locale: string
}

export async function fetchPageDictionary({ slug, locale }: FetchPageDictionaryParams) {
	try {
		// Step 1: Fetch page fields corresponding to the slug
		const FieldPageTableId = await getTableIdByName('PageField')

		const fieldsResponse = await instance.get<FetchResponseRecords<PageFieldRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${FieldPageTableId}/records?where=(WebsitePage,eq,${slug})`
		)

		if (fieldsResponse.status !== 200) {
			throw new Error(`Failed to fetch page fields: ${fieldsResponse.statusText}`)
		}

		const fieldsData = fieldsResponse.data
		const pageFields = fieldsData.records

		const pageFieldsList = pageFields.map(pf => pf.fields.Key).join(',')

		// If none of the fetched fields match, fall back to the default list
		const pageFieldsListCsv = pageFieldsList ?? ''

		// Step 2: Fetch translations for these page fields
		const TranslationTableId = await getTableIdByName('Translation')

		const translationsResponse = await instance.get<FetchResponseRecords<TranslationRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${TranslationTableId}/records/?where=(PageField,in,${pageFieldsListCsv})~and(Language,eq,${locale})`
		)

		if (translationsResponse.status !== 200) {
			throw new Error(`Failed to fetch translations: ${translationsResponse.statusText}`)
		}

		const translationsData: FetchResponseRecords<TranslationRecord> = translationsResponse.data

		// Step 3: Merge translations into a dictionary organized by field key
		const dictionary: Record<string, string> = {}

		translationsData.records.forEach(translation => {
			const fieldKey = translation.fields.PageField.fields.Key

			dictionary[fieldKey] = translation.fields.Value
		})

		return dictionary
	} catch (error) {
		console.error(`Error fetching dictionary for slug "${slug}" and language "${locale}":`, error)
		throw error
	}
}
