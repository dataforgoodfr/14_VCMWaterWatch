import { NextResponse } from 'next/server'

import { fallbackLanguage, i18n } from '@/i18n/i18next.config'
import { fetchCountryByCode } from '@/lib/fetchCountryByCode'
import { getEntityImageSrc } from '@/lib/entityImage'

const ALLOWED_LOCALES = new Set<string>(i18n.locales)

export async function GET(request: Request, { params }: { params: Promise<{ code: string }> }) {
	const { code } = await params
	const decoded = decodeURIComponent(code)

	const { searchParams } = new URL(request.url)
	const requested = searchParams.get('locale') ?? ''
	const locale = ALLOWED_LOCALES.has(requested) ? requested : fallbackLanguage

	const result = await fetchCountryByCode(decoded, locale)

	if (!result) {
		return NextResponse.json({ country: null, data: [] }, { status: 404 })
	}

	// Resolve the mirrored image URL server-side (fs is available in API routes)
	// so the client component doesn't need to access the filesystem directly.
	const mirroredImageUrl = getEntityImageSrc('country', decoded)

	return NextResponse.json({ country: result.country, data: result.data, mirroredImageUrl })
}
