import { NextResponse } from 'next/server'

import { getTableIdByName } from '@/lib/fetchMetaTables'
import { instance } from '@/lib/instance'
import { HTTP_STATUS } from '@/types/httpTypes'

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
	const { id } = await params

	if (!id) {
		return NextResponse.json({ error: 'Zone ID is required' }, { status: HTTP_STATUS.BadRequest.code })
	}

	try {
		const tableId = await getTableIdByName('DistributionZone')

		if (!tableId) {
			return NextResponse.json({ error: 'Table not found' }, { status: HTTP_STATUS.InternalServerError.code })
		}

		const response = await instance.get(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records/${id}`)

		return NextResponse.json(response.data)
	} catch (error) {
		console.error('Error in GET /api/distributionzone/[id]:', error)
		return NextResponse.json(HTTP_STATUS.InternalServerError)
	}
}
