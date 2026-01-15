import { createInstance } from 'i18next'
import resourcesToBackend from 'i18next-resources-to-backend'
import { initReactI18next } from 'react-i18next/initReactI18next'

import { getI18nOptions } from '@/i18n/i18next.config'
import type { Locale } from '@/i18n/i18next.config'

interface InitOptions {
	keyPrefix?: string
	[key: string]: unknown
}

// Initializes i18next for server-side use (without React context)

async function initI18nextServer(lng: Locale, ns: string | string[]) {
	const i18nInstance = createInstance()

	await i18nInstance
		.use(resourcesToBackend((language: Locale, namespace: string) => import(`./${language}/${namespace}.json`)))
		.init(getI18nOptions(lng, ns))
	return i18nInstance
}

// Initializes i18next for client-side use (with React context)

async function initI18nextClient(lng: Locale, ns: string | string[]) {
	const i18nInstance = createInstance()

	await i18nInstance
		.use(initReactI18next)
		.use(resourcesToBackend((language: Locale, namespace: string) => import(`./${language}/${namespace}.json`)))
		.init(getI18nOptions(lng, ns))
	return i18nInstance
}

// Server-side translation hook for use in Server Components

export async function getServerTranslation(lng: Locale, ns: string | string[], options?: InitOptions) {
	const i18nextInstance = await initI18nextServer(lng, ns)

	return {
		t: i18nextInstance.getFixedT(lng, Array.isArray(ns) ? ns[0] : ns, options?.keyPrefix),
		i18n: i18nextInstance
	}
}

/**
 * Client-side translation hook for use in Client Components (via SSG)
 * Use this when you need to pre-initialize i18next on the server for client components
 */
export async function getClientTranslation(lng: Locale, ns: string | string[]) {
	const i18nextInstance = await initI18nextClient(lng, ns)

	return {
		t: i18nextInstance.getFixedT(lng, Array.isArray(ns) ? ns[0] : ns),
		i18n: i18nextInstance
	}
}
