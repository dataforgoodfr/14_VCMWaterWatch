import { NextResponse } from 'next/server'

import { fetchDistributionZonesLimitedFieldsGeo } from '@/lib/fetchDistributionZones'
import { HTTP_STATUS } from '@/types/httpTypes'

export async function GET(request: Request) {
	const { searchParams } = new URL(request.url)
	const query = searchParams.get('q')

	if (!query) {
		return NextResponse.json({ error: "Query parameter 'q' is required" }, { status: HTTP_STATUS.BadRequest.code })
	}

	try {
		const results = await fetchDistributionZonesLimitedFieldsGeo({ query })

		return NextResponse.json(results)
	} catch (error) {
		console.error('Error in GET /api/searchbydistributionzone:', error)
		return NextResponse.json(HTTP_STATUS.InternalServerError)
	}
}
