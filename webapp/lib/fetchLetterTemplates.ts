import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

export interface Template {
	icon: string
	title: string
	content: string
}

interface LetterTemplateRecord {
	fields: {
		Title: string
		Icon: string
		Content: string
		SortOrder: number
		Locale: string
		Active: boolean
	}
}

export async function fetchLetterTemplates(locale: string): Promise<Template[]> {
	try {
		const tableId = await getTableIdByName('LetterTemplate')

		if (!tableId) {
			console.warn('LetterTemplate table not found in NocoDB')
			return []
		}

		const baseId = process.env.NOCODB_BASE_ID

		const response = await instance.get<FetchResponseRecords<LetterTemplateRecord>>(
			`/data/${baseId}/${tableId}/records?where=(Active,eq,1)~and(Locale,eq,${locale})&sort=${JSON.stringify([{ direction: 'asc', field: 'SortOrder' }])}`
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch letter templates: ${response.statusText}`)
		}

		return response.data.records.map(r => ({
			icon: r.fields.Icon,
			title: r.fields.Title,
			content: r.fields.Content
		}))
	} catch (error) {
		console.error('Error fetching letter templates:', error)
		return []
	}
}
