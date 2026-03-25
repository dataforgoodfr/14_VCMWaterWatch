import { NextResponse } from 'next/server'

import { fetchDistributionZonesLimitedFieldsGeo } from '@/lib/fetchDistributionZones'
import { sanitizeSearchQuery } from '@/lib/security/searchQuery'
import { HTTP_STATUS } from '@/types/httpTypes'

export async function GET(request: Request) {
	const { searchParams } = new URL(request.url)
	const rawQuery = searchParams.get('q')
	const query = sanitizeSearchQuery(rawQuery)

	if (!query) {
		return NextResponse.json({ error: 'Invalid or empty query' }, { status: HTTP_STATUS.BadRequest.code })
	}

	try {
		const results = await fetchDistributionZonesLimitedFieldsGeo({ query })

		return NextResponse.json(results ?? [])
	} catch {
		console.error('Error in GET /api/searchbydistributionzone')

		return NextResponse.json(
			{ error: HTTP_STATUS.InternalServerError.label },
			{ status: HTTP_STATUS.InternalServerError.code }
		)
	}
}
