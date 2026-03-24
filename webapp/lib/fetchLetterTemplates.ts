import { Template } from '@/app/[locale]/act/data/templates'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

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

// Server-side cache keyed by locale
const cache = new Map<string, { data: Template[]; timestamp: number }>()
const CACHE_DURATION_MS = 5 * 60 * 1000 // 5 minutes

export async function fetchLetterTemplates(locale: string): Promise<Template[]> {
	const cached = cache.get(locale)

	if (cached && Date.now() - cached.timestamp < CACHE_DURATION_MS) {
		return cached.data
	}

	try {
		const tableId = await getTableIdByName('LetterTemplate')

		if (!tableId) {
			console.warn('LetterTemplate table not found in NocoDB')
			return []
		}

		const baseId = process.env.NOCODB_BASE_ID

		const response = await instance.get<FetchResponseRecords<LetterTemplateRecord>>(
			`/data/${baseId}/${tableId}/records?where=(Active,eq,true)~and(Locale,eq,${locale})&sort=SortOrder`
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch letter templates: ${response.statusText}`)
		}

		const templates: Template[] = response.data.records.map(r => ({
			icon: r.fields.Icon,
			title: r.fields.Title,
			content: r.fields.Content
		}))

		cache.set(locale, { data: templates, timestamp: Date.now() })

		return templates
	} catch (error) {
		console.error('Error fetching letter templates:', error)

		// Return stale cache if available
		if (cached) {
			console.warn('Returning stale letter template cache due to fetch error')
			return cached.data
		}

		return []
	}
}
