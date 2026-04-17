import { NextResponse } from 'next/server'

import { fetchMunicipalityNamesForDistributionZone } from '@/lib/fetchMunicipalitiesForDistributionZone'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { instance } from '@/lib/instance'
import { mapTooltipPvcFromNocoLink, tilePropertyString } from '@/lib/map/mapTooltipPvcBadge'
import type { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { HTTP_STATUS } from '@/types/httpTypes'

function coerceLinkRowId(value: unknown): number | null {
	if (typeof value === 'number' && Number.isFinite(value)) {
		return value
	}

	if (typeof value === 'string' && /^\d+$/.test(value.trim())) {
		return Number(value.trim())
	}

	return null
}

async function fetchMapTooltipPvcByLinkRowId(linkRowId: number): Promise<string | null> {
	const tooltipTableId = await getTableIdByName('Map - Tooltip')

	if (!tooltipTableId) {
		return null
	}

	try {
		const res = await instance.get(`/data/${process.env.NOCODB_BASE_ID}/${tooltipTableId}/records/${linkRowId}`, {
			timeout: 15000
		})

		const data = res.data as { fields?: Record<string, unknown> }

		if (data?.fields && typeof data.fields === 'object') {
			return tilePropertyString(data.fields['PVC Level'])
		}

		return null
	} catch {
		return null
	}
}

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
			const baseFields = raw.fields as unknown as Record<string, unknown>
			let mapTooltipPvcLevel = mapTooltipPvcFromNocoLink(baseFields['Map - Tooltip'])

			if (mapTooltipPvcLevel === null) {
				const linkId = coerceLinkRowId(baseFields['Map - Tooltip'])

				if (linkId !== null) {
					mapTooltipPvcLevel = await fetchMapTooltipPvcByLinkRowId(linkId)
				}
			}

			return NextResponse.json({
				...raw,
				fields: {
					...raw.fields,
					MunicipalityNames: municipalityNames,
					MapTooltipPvcLevel: mapTooltipPvcLevel
				}
			} satisfies DistributionZoneDetailRecord)
		}

		return NextResponse.json(zoneResponse.data)
	} catch (error) {
		console.error('Error in GET /api/distributionzone/[id]:', error)
		return NextResponse.json(HTTP_STATUS.InternalServerError)
	}
}
