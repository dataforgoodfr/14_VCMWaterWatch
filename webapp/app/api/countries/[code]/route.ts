import { NextResponse } from 'next/server'

import { fetchCountryByCode } from '@/lib/fetchCountryByCode'

export async function GET(request: Request, { params }: { params: Promise<{ code: string }> }) {
	const { code } = await params
	const decoded = decodeURIComponent(code)

	const { searchParams } = new URL(request.url)
	const ALLOWED_LOCALES = new Set(['en', 'fr', 'de'])
	const locale = ALLOWED_LOCALES.has(searchParams.get('locale') ?? '') ? searchParams.get('locale')! : 'en'

	const result = await fetchCountryByCode(decoded, locale)

	if (!result) {
		return NextResponse.json({ country: null, data: [] }, { status: 404 })
	}

	return NextResponse.json({ country: result.country, data: result.data })
}
