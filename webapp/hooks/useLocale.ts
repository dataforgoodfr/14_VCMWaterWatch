'use client'

import { useParams } from 'next/navigation'

import { fallbackLanguage, languages, Locale } from '@/i18n/i18next.config'

// This hook is used to determine the appropriate language setting for the application based on the URL parameters or pathname, defaulting to a fallback language if necessary.

export default function useLocale(): Locale {
	const params = useParams()

	const locale = params?.locale as Locale | undefined

	if (locale && languages.includes(locale)) {
		return locale
	}

	return fallbackLanguage
}
