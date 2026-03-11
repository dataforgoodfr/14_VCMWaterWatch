import { NextResponse } from 'next/server'

import { fetchCountriesForMap, fetchDistributionZonesForMap } from '@/lib/fetchDistributionZones'

export async function GET() {
	try {
		const [zones, countries] = await Promise.all([fetchDistributionZonesForMap(), fetchCountriesForMap()])

		return NextResponse.json({ zones: zones ?? [], countries: countries ?? [] })
	} catch (error) {
		console.error('Error in GET /api/distributionzones:', error)
		return NextResponse.json({ zones: [], countries: [] }, { status: 500 })
	}
}
