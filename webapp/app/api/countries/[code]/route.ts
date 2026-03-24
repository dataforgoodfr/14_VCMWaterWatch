import { NextResponse } from 'next/server'

import { fetchCountryByCode } from '@/lib/fetchCountryByCode'

export async function GET(_request: Request, { params }: { params: Promise<{ code: string }> }) {
	const { code } = await params
	const decoded = decodeURIComponent(code)
	const country = await fetchCountryByCode(decoded)

	if (!country) {
		return NextResponse.json({ country: null }, { status: 404 })
	}

	return NextResponse.json({ country })
}
