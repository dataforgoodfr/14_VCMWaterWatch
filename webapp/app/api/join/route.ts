import { NextResponse } from 'next/server'

import { instance } from '@/lib/instance'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { HTTP_STATUS } from '@/types/httpTypes'

interface JoinBody {
	name: string
	email: string
	expertise: string
	message?: string
}

export async function POST(request: Request) {
	try {
		const body = (await request.json()) as JoinBody

		if (!body.name?.trim() || !body.email?.trim() || !body.expertise?.trim()) {
			return NextResponse.json(
				{ error: 'Name, email, and expertise are required' },
				{ status: HTTP_STATUS.BadRequest.code }
			)
		}

		// Basic email validation
		if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email)) {
			return NextResponse.json({ error: 'Invalid email address' }, { status: HTTP_STATUS.BadRequest.code })
		}

		const tableId = await getTableIdByName('Volunteer')

		if (!tableId) {
			console.error('Volunteer table not found in NocoDB')
			return NextResponse.json(
				{ error: 'Service temporarily unavailable' },
				{ status: HTTP_STATUS.InternalServerError.code }
			)
		}

		await instance.post(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`, {
			Name: body.name.trim(),
			Email: body.email.trim(),
			Expertise: body.expertise.trim(),
			Message: body.message?.trim() ?? ''
		})

		return NextResponse.json({ success: true }, { status: HTTP_STATUS.Created.code })
	} catch (error) {
		console.error('Error in POST /api/join:', error)
		return NextResponse.json({ error: 'Internal server error' }, { status: HTTP_STATUS.InternalServerError.code })
	}
}
