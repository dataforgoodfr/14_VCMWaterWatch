'use client'

import { useEffect } from 'react'

import { useRouter } from 'next/navigation'

import { WORLD_COUNTRIES_GEOJSON_URL } from '@/lib/map/mapStyle'
import { ROUTES } from '@/routes/routes'

const GEOJSON_PREFETCH_ID = 'prefetch-map-world-countries-geojson'

interface MapRoutePrefetchProps {
	locale: string
}

export function MapRoutePrefetch({ locale }: MapRoutePrefetchProps) {
	const router = useRouter()

	useEffect(() => {
		router.prefetch(`/${locale}${ROUTES.MAP}`)

		if (document.head.querySelector(`link#${GEOJSON_PREFETCH_ID}`)) {
			return
		}

		const link = document.createElement('link')

		link.id = GEOJSON_PREFETCH_ID
		link.rel = 'prefetch'
		link.href = WORLD_COUNTRIES_GEOJSON_URL
		link.crossOrigin = 'anonymous'
		document.head.appendChild(link)
	}, [locale, router])

	return null
}
