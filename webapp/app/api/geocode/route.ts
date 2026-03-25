import { NextResponse } from 'next/server'

import { searchPhoton } from '@/lib/geocode/photon'
import { sanitizePhotonLang, sanitizeSearchQuery } from '@/lib/security/searchQuery'
import { HTTP_STATUS } from '@/types/httpTypes'

const DEFAULT_PHOTON_BASE = 'https://photon.komoot.io'

function resolvePhotonBaseUrl(envValue: string | undefined): string {
	const raw = envValue?.trim() ?? ''

	if (raw === '') {
		return DEFAULT_PHOTON_BASE
	}

	try {
		const u = new URL(raw)

		if (u.protocol !== 'https:' && u.protocol !== 'http:') {
			return DEFAULT_PHOTON_BASE
		}

		if (u.username !== '' || u.password !== '') {
			return DEFAULT_PHOTON_BASE
		}

		return raw.replace(/\/$/, '')
	} catch {
		return DEFAULT_PHOTON_BASE
	}
}

export async function GET(request: Request) {
	const { searchParams } = new URL(request.url)
	const rawQ = searchParams.get('q')
	const safeQ = sanitizeSearchQuery(rawQ)

	if (!safeQ) {
		return NextResponse.json({ error: 'Invalid or empty query' }, { status: HTTP_STATUS.BadRequest.code })
	}

	const baseUrl = resolvePhotonBaseUrl(process.env.PHOTON_BASE_URL)
	const lang = sanitizePhotonLang(process.env.PHOTON_LANG)

	try {
		const places = await searchPhoton(safeQ, baseUrl, lang)

		return NextResponse.json({ places })
	} catch {
		console.error('Error in GET /api/geocode')

		return NextResponse.json({ places: [] }, { status: HTTP_STATUS.OK.code })
	}
}
