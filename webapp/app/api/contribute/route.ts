import { NextResponse } from 'next/server'

import { instance } from '@/lib/instance'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { HTTP_STATUS } from '@/types/httpTypes'

const VALID_DATA_TYPES = ['Analysis report', 'PVC presence info', 'Correction', 'Other'] as const

interface ContributeBody {
	dataType: string
	documentSource?: string
}

export async function POST(request: Request) {
	try {
		const body = (await request.json()) as ContributeBody

		if (!body.dataType || !VALID_DATA_TYPES.includes(body.dataType as (typeof VALID_DATA_TYPES)[number])) {
			return NextResponse.json({ error: 'Invalid or missing dataType' }, { status: HTTP_STATUS.BadRequest.code })
		}

		const tableId = await getTableIdByName('Contribution')

		if (!tableId) {
			console.error('Contribution table not found in NocoDB')
			return NextResponse.json(
				{ error: 'Service temporarily unavailable' },
				{ status: HTTP_STATUS.InternalServerError.code }
			)
		}

		await instance.post(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`, {
			'Data Type': body.dataType,
			'Document Source': body.documentSource ?? ''
		})

		return NextResponse.json({ success: true }, { status: HTTP_STATUS.Created.code })
	} catch (error) {
		console.error('Error in POST /api/contribute:', error)
		return NextResponse.json({ error: 'Internal server error' }, { status: HTTP_STATUS.InternalServerError.code })
	}
}
