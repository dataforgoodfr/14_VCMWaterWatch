import { NextRequest, NextResponse } from 'next/server'

import acceptLanguage from 'accept-language'

import { Locale, fallbackLanguage, languages, cookieName } from './i18n/i18next.config'

acceptLanguage.languages(languages)

export const config = {
	// Avoid matching for static files, API routes, etc.
	matcher: ['/((?!api|_next/static|_next/image|assets|public|images|favicon.ico|.*\\..*).*)']
}

export function proxy(req: NextRequest) {
	let lng

	if (req.cookies.has(cookieName)) {
		lng = acceptLanguage.get(req.cookies.get(cookieName)?.value)
	}

	lng ??= acceptLanguage.get(req.headers.get('Accept-Language'))
	lng ??= fallbackLanguage

	// Redirect if lng in path is not supported
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
