'use client'

import { useEffect } from 'react'

import { useRouter } from 'next/navigation'

import { COUNTRIES_PM_TILES_PUBLIC_PATH, DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH } from '@/lib/map/mapStyle'
import { ROUTES } from '@/routes/routes'

const COUNTRIES_PM_TILES_PREFETCH_ID = 'prefetch-map-countries-pmtiles'
const DISTRIBUTION_ZONES_PM_TILES_PREFETCH_ID = 'prefetch-map-distribution-zones-pmtiles'

interface MapRoutePrefetchProps {
	locale: string
}

export function MapRoutePrefetch({ locale }: MapRoutePrefetchProps) {
	const router = useRouter()

	useEffect(() => {
		router.prefetch(`/${locale}${ROUTES.MAP}`)

		const prefetchPmTilesArchive = (id: string, href: string) => {
			if (document.head.querySelector(`link#${id}`)) {
				return
			}

			const link = document.createElement('link')

			link.id = id
			link.rel = 'prefetch'
			link.as = 'fetch'
			link.href = href
			link.crossOrigin = 'anonymous'
			document.head.appendChild(link)
		}

		prefetchPmTilesArchive(COUNTRIES_PM_TILES_PREFETCH_ID, COUNTRIES_PM_TILES_PUBLIC_PATH)
		prefetchPmTilesArchive(DISTRIBUTION_ZONES_PM_TILES_PREFETCH_ID, DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH)
	}, [locale, router])

	return null
}
