import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

import type { Record as NocoRecord } from '@/types/apiTypes'

export interface RecentAnalysis {
	date: string | null
	vcmMeasure: number | null
}

interface AnalysisFields {
	Date: string | null
	CVMMeasure: number | null
}

/**
 * Format an ISO date string to DD/MM/YYYY for display.
 */
export function formatAnalysisDate(value: string | null | undefined): string {
	if (value == null) {
		return '—'
	}

	const d = new Date(value)

	if (isNaN(d.getTime())) {
		return value
	}

	const dd = String(d.getUTCDate()).padStart(2, '0')
	const mm = String(d.getUTCMonth() + 1).padStart(2, '0')
	const yyyy = d.getUTCFullYear()

	return `${dd}/${mm}/${yyyy}`
}

/**
 * Fetch the most recent analyses (up to 3) for a distribution zone.
 */
export async function fetchRecentAnalyses(distributionZoneId: number): Promise<RecentAnalysis[]> {
	try {
		const tableId = await getTableIdByName('Analysis')

		if (!tableId) {
			return []
		}

		const response = await instance.get<FetchResponseRecords<NocoRecord<AnalysisFields>>>(
			`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`,
			{
				timeout: 15000,
				params: {
					where: `(DistributionZone,eq,${distributionZoneId})`,
					sort: '-Date',
					pageSize: 3,
					fields: 'Date,CVMMeasure'
				}
			}
		)

		if (response.status !== 200 || !response.data.records?.length) {
			return []
		}

		return response.data.records.map(r => ({
			date: r.fields.Date ?? null,
			vcmMeasure: r.fields.CVMMeasure ?? null
		}))
	} catch (error) {
		console.error('Error fetching analyses for distribution zone:', error)

		return []
	}
}
