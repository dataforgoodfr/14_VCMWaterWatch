import { NextRequest, NextResponse } from 'next/server'

import acceptLanguage from 'accept-language'

import { Locale, cookieName, fallbackLanguage, languages } from './i18n/i18next.config'

acceptLanguage.languages(languages)

export const config = {
	matcher: ['/((?!api|_next/static|_next/image|assets|public|images|favicon.ico|.*\\..*).*)']
}

export function proxy(req: NextRequest) {
	let lng: string | undefined

	if (req.cookies.has(cookieName)) {
		lng = acceptLanguage.get(req.cookies.get(cookieName)?.value) ?? undefined
	}

	lng ??= acceptLanguage.get(req.headers.get('Accept-Language')) ?? undefined
	lng ??= fallbackLanguage

	if (
		!languages.some((loc: Locale) => req.nextUrl.pathname.startsWith(`/${loc}`)) &&
		!req.nextUrl.pathname.startsWith('/_next') &&
		!req.nextUrl.pathname.startsWith('/images') &&
		!req.nextUrl.pathname.includes('.')
	) {
		return NextResponse.redirect(new URL(`/${lng}${req.nextUrl.pathname}`, req.url))
	}

	if (req.headers.has('referer')) {
		const refererUrl = new URL(req.headers.get('referer') ?? '')

		const lngInReferer = languages.find(l => refererUrl.pathname.startsWith(`/${l}`))

		const response = NextResponse.next()

		if (lngInReferer) {
			response.cookies.set(cookieName, lngInReferer)
		}

		return response
	}

	return NextResponse.next()
}
