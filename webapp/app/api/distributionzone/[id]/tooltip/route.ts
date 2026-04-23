import { NextResponse } from 'next/server'

import { getTableIdByName } from '@/lib/fetchMetaTables'
import { fetchRecentAnalyses } from '@/lib/fetchAnalysesForDistributionZone'
import { instance } from '@/lib/instance'
import { HTTP_STATUS } from '@/types/httpTypes'

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
	const { id } = await params

	if (!id) {
		return NextResponse.json({ error: 'Zone ID is required' }, { status: HTTP_STATUS.BadRequest.code })
	}

	const zoneId = Number(id)

	if (!Number.isFinite(zoneId)) {
		return NextResponse.json({ error: 'Invalid zone ID' }, { status: HTTP_STATUS.BadRequest.code })
	}

	try {
		const tableId = await getTableIdByName('DistributionZone')

		if (!tableId) {
			return NextResponse.json({ error: 'Table not found' }, { status: HTTP_STATUS.InternalServerError.code })
		}

		const [zoneRes, recentAnalyses] = await Promise.all([
			instance.get(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records/${id}`, {
				timeout: 10000,
				params: { fields: 'PVC Level comment' }
			}),
			fetchRecentAnalyses(zoneId)
		])

		const data = zoneRes.data as { fields?: Record<string, unknown> }
		const f = data?.fields

		return NextResponse.json({
			pvcLevelComment: f?.['PVC Level comment'] ?? null,
			recentAnalyses
		})
	} catch (error) {
		console.error('Error in GET /api/distributionzone/[id]/tooltip:', error)
		return NextResponse.json(HTTP_STATUS.InternalServerError)
	}
}
