import { PageFieldRecord, TranslationRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponse, instance } from './instance'

interface FetchPageDictionaryParams {
	slug: string
	locale: string
}

export async function fetchPageDictionary({ slug, locale }: FetchPageDictionaryParams) {
	try {
		// Step 1: Fetch page fields corresponding to the slug
		const FieldPageTableId = await getTableIdByName('PageField')

		const fieldsResponse = await instance.get(`/tables/${FieldPageTableId}/records?where=(WebsitePage,eq,${slug})`)

		if (fieldsResponse.status !== 200) {
			throw new Error(`Failed to fetch page fields: ${fieldsResponse.statusText}`)
		}

		const fieldsData: FetchResponse<PageFieldRecord> = fieldsResponse.data
		const pageFields = fieldsData.list

		const pageFieldsList = pageFields.map(pf => pf.Key).join(',')

		// If none of the fetched fields match, fall back to the default list
		const pageFieldsListCsv = pageFieldsList ?? ''

		// Step 2: Fetch translations for these page fields
		const TranslationTableId = await getTableIdByName('Translation')

		const translationsResponse = await instance.get(
			`/tables/${TranslationTableId}/records/?where=(PageField,in,${pageFieldsListCsv})~and(Language,eq,${locale})`
		)

		if (translationsResponse.status !== 200) {
			throw new Error(`Failed to fetch translations: ${translationsResponse.statusText}`)
		}

		const translationsData: FetchResponse<TranslationRecord> = translationsResponse.data

		// Step 3: Merge translations into a dictionary organized by field key
		const dictionary: Record<string, string> = {}

		translationsData.list.forEach(translation => {
			const fieldKey = translation.PageField.Key

			dictionary[fieldKey] = translation.Value
		})

		return dictionary
	} catch (error) {
		console.error(`Error fetching dictionary for slug "${slug}" and language "${locale}":`, error)
		throw error
	}
}
