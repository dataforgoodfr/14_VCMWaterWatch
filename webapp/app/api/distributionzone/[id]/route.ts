import { NextResponse } from 'next/server'

import { fetchMunicipalityNamesForDistributionZone } from '@/lib/fetchMunicipalitiesForDistributionZone'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { instance } from '@/lib/instance'
import type { DistributionZoneDetailRecord } from '@/types/apiTypes'
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

		const [zoneResponse, municipalityNames] = await Promise.all([
			instance.get(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records/${id}`, { timeout: 20000 }),
			fetchMunicipalityNamesForDistributionZone(zoneId)
		])

		const raw = zoneResponse.data as DistributionZoneDetailRecord

		if (raw?.fields && typeof raw.fields === 'object') {
			return NextResponse.json({
				...raw,
				fields: {
					...raw.fields,
					MunicipalityNames: municipalityNames
				}
			} satisfies DistributionZoneDetailRecord)
		}

		return NextResponse.json(zoneResponse.data)
	} catch (error) {
		console.error('Error in GET /api/distributionzone/[id]:', error)
		return NextResponse.json(HTTP_STATUS.InternalServerError)
	}
}
