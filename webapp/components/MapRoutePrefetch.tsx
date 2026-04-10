'use client'

import { useEffect } from 'react'

import { useRouter } from 'next/navigation'

import { DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH, WORLD_COUNTRIES_GEOJSON_URL } from '@/lib/map/mapStyle'
import { ROUTES } from '@/routes/routes'

const WORLD_COUNTRIES_GEOJSON_PREFETCH_ID = 'prefetch-map-world-countries-geojson'
const DISTRIBUTION_ZONES_PM_TILES_PREFETCH_ID = 'prefetch-map-distribution-zones-pmtiles'

interface MapRoutePrefetchProps {
	locale: string
}

export function MapRoutePrefetch({ locale }: MapRoutePrefetchProps) {
	const router = useRouter()

	useEffect(() => {
		router.prefetch(`/${locale}${ROUTES.MAP}`)

		const prefetchAsset = (id: string, href: string, as: string) => {
			if (document.head.querySelector(`link#${id}`)) {
				return
			}

			const link = document.createElement('link')

			link.id = id
			link.rel = 'prefetch'
			link.as = as
			link.href = href
			link.crossOrigin = 'anonymous'
			document.head.appendChild(link)
		}

		prefetchAsset(WORLD_COUNTRIES_GEOJSON_PREFETCH_ID, WORLD_COUNTRIES_GEOJSON_URL, 'fetch')
		prefetchAsset(DISTRIBUTION_ZONES_PM_TILES_PREFETCH_ID, DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH, 'fetch')
	}, [locale, router])

	return null
}
