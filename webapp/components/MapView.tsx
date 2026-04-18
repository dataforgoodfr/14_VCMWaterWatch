'use client'

import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'

import Link from 'next/link'

import maplibregl from 'maplibre-gl'
import type { MapLayerMouseEvent, MapLibreEvent } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import Map from 'react-map-gl/maplibre'
import type { MapRef, ViewStateChangeEvent } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { GeocodePlace } from '@/lib/geocode/photon'
import { formatAnalysisDate, type RecentAnalysis } from '@/lib/fetchAnalysesForDistributionZone'
import useLocale from '@/hooks/useLocale'
import { ROUTES } from '@/routes/routes'
import { distributionZoneTierFilter, type MapRiskTier } from '@/lib/map/distributionZoneRisk'
import { createBaseMapStyle, COUNTRIES_FILL_LAYER_ID, MAP_DISTRIBUTION_ZONES_MIN_ZOOM } from '@/lib/map/mapStyle'
import {
	pvcTooltipBadgeFromTileProperty,
	rawTooltipPvcFromFeatureProperties,
	rawTooltipVcmFromFeatureProperties,
	vcmTooltipBadgeFromTileProperty
} from '@/lib/map/mapTooltipPvcBadge'
import { Card, CardContent, CardTitle } from '@/components/ui/card'

import { MapRiskFilters } from './MapRiskFilters'
import { SearchBar } from './SearchBar'

let protocolRegistered = false
let pmtilesProtocol: Protocol | null = null

const MAP_INTRO_VIEW_STATE = {
	longitude: -18,
	latitude: 28,
	zoom: 1.45
} as const

const MAP_NORWAY_SPAIN_BOUNDS: [[number, number], [number, number]] = [
	[-9.9, 35.4],
	[31.2, 65.4]
]

const DISTRIBUTION_ZONES_LAYER_IDS = ['distribution-zones-fill', 'distribution-zones-outline'] as const

const RISK_FILTER_LAYER_IDS = [...DISTRIBUTION_ZONES_LAYER_IDS] as const

const DISTRIBUTION_ZONE_PICK_LAYER_ID = DISTRIBUTION_ZONES_LAYER_IDS[0]

function emptyMapMoveSubscriptionCleanup() {
	/* not subscribed */
}

interface ZoneCardState {
	lng: number
	lat: number
	name: string
	tooltipPvcRaw: string | null
	tooltipVcmRaw: string | null
	zoneId: number | null
}

function parseDistributionZoneIdFromProperties(props: Record<string, unknown>): number | null {
	const v = props.noco_id ?? props.id ?? props.Id

	if (typeof v === 'number' && Number.isFinite(v)) {
		return v
	}

	if (typeof v === 'string') {
		const n = Number(v)

		return Number.isFinite(n) ? n : null
	}

	return null
}

function parseDistributionZoneIdFromFeature(feature: {
	id?: string | number | undefined
	properties?: unknown
}): number | null {
	const fid = feature.id

	if (typeof fid === 'number' && Number.isFinite(fid)) {
		return fid
	}

	if (typeof fid === 'string') {
		const n = Number(fid)

		return Number.isFinite(n) ? n : null
	}

	const props = feature.properties

	if (props !== null && typeof props === 'object' && !Array.isArray(props)) {
		return parseDistributionZoneIdFromProperties(props as Record<string, unknown>)
	}

	return null
}

function displayZoneName(value: unknown): string {
	if (typeof value === 'string') {
		const trimmed = value.trim()

		return trimmed !== '' ? trimmed : '—'
	}

	if (typeof value === 'number' && Number.isFinite(value)) {
		return String(value)
	}

	return '—'
}

export function MapView() {
	const locale = useLocale()
	const mapRef = useRef<MapRef>(null)
	const [mapLoaded, setMapLoaded] = useState(false)
	const [riskFilter, setRiskFilter] = useState<MapRiskTier | null>(null)
	const [zoneCard, setZoneCard] = useState<ZoneCardState | null>(null)
	const [zoneDetailPvcComment, setZoneDetailPvcComment] = useState<string | null | undefined>(undefined)
	const [zoneDetailAnalyses, setZoneDetailAnalyses] = useState<RecentAnalysis[]>([])
	const [zoneDetailLoading, setZoneDetailLoading] = useState(false)
	const [mapCursor, setMapCursor] = useState('')
	const [mapZoom, setMapZoom] = useState<number>(MAP_INTRO_VIEW_STATE.zoom)

	const zonesLayerVisible = mapZoom >= MAP_DISTRIBUTION_ZONES_MIN_ZOOM

	const zoneCardScreenSnap = useSyncExternalStore(
		useCallback(
			onStoreChange => {
				if (!mapLoaded || !zoneCard) {
					return emptyMapMoveSubscriptionCleanup
				}

				const map = mapRef.current?.getMap()

				if (!map) {
					return emptyMapMoveSubscriptionCleanup
				}

				map.on('move', onStoreChange)

				return () => {
					map.off('move', onStoreChange)
				}
			},
			[mapLoaded, zoneCard]
		),
		() => {
			if (!zoneCard) {
				return null
			}

			const map = mapRef.current?.getMap()

			if (!map) {
				return null
			}

			const p = map.project([zoneCard.lng, zoneCard.lat])

			return `${p.x.toFixed(2)},${p.y.toFixed(2)}`
		},
		() => null
	)

	const zoneCardScreen = useMemo(() => {
		if (zoneCardScreenSnap === null) {
			return null
		}

		const comma = zoneCardScreenSnap.indexOf(',')

		if (comma === -1) {
			return null
		}

		const x = Number(zoneCardScreenSnap.slice(0, comma))
		const y = Number(zoneCardScreenSnap.slice(comma + 1))

		if (!Number.isFinite(x) || !Number.isFinite(y)) {
			return null
		}

		return { x, y }
	}, [zoneCardScreenSnap])

	const mapStyle = useMemo(() => createBaseMapStyle(), [])

	useEffect(() => {
		if (!protocolRegistered) {
			pmtilesProtocol = new Protocol()
			maplibregl.addProtocol('pmtiles', pmtilesProtocol.tile)
			protocolRegistered = true
		}
	}, [])

	const onSelectPlace = useCallback((place: GeocodePlace) => {
		mapRef.current?.fitBounds(
			[
				[place.west, place.south],
				[place.east, place.north]
			],
			{ padding: 48, duration: 800, linear: false }
		)
	}, [])

	const closeZoneCard = useCallback(() => {
		setZoneDetailPvcComment(undefined)
		setZoneDetailAnalyses([])
		setZoneDetailLoading(false)
		setZoneCard(null)
	}, [])

	const onMapClick = useCallback(
		(e: MapLayerMouseEvent) => {
			const feature = e.features?.find(f => f.layer?.id === DISTRIBUTION_ZONE_PICK_LAYER_ID)

			if (!feature?.properties) {
				closeZoneCard()
				return
			}

			const props = feature.properties as Record<string, unknown>
			const name = displayZoneName(props.name)
			const { lng, lat } = e.lngLat
			const tooltipPvcRaw = rawTooltipPvcFromFeatureProperties(props)
			const tooltipVcmRaw = rawTooltipVcmFromFeatureProperties(props)
			const zoneId = parseDistributionZoneIdFromFeature(feature)

			console.log('[MapView] click zone', {
				featureId: feature.id,
				zoneId,
				props
			})

			setZoneDetailPvcComment(undefined)
			setZoneDetailAnalyses([])
			setZoneDetailLoading(true)
			setZoneCard({ lng, lat, name, tooltipPvcRaw, tooltipVcmRaw, zoneId })
		},
		[closeZoneCard]
	)

	const onMapMouseMove = useCallback((e: MapLayerMouseEvent) => {
		const overInteractive = Boolean(
			e.features?.some(
				f => f.layer?.id === DISTRIBUTION_ZONE_PICK_LAYER_ID || f.layer?.id === COUNTRIES_FILL_LAYER_ID
			)
		)

		setMapCursor(overInteractive ? 'pointer' : '')
	}, [])

	const onMapMove = useCallback((e: ViewStateChangeEvent) => {
		const z = e.viewState.zoom

		setMapZoom(z)
		setRiskFilter(prev => (z >= MAP_DISTRIBUTION_ZONES_MIN_ZOOM ? prev : null))
	}, [])

	const onMapLoad = useCallback((e: MapLibreEvent) => {
		const map = e.target

		setMapLoaded(true)
		setMapZoom(map.getZoom())

		const zoomToRegion = () => {
			map.fitBounds(MAP_NORWAY_SPAIN_BOUNDS, {
				padding: 56,
				duration: 1600,
				linear: false,
				maxZoom: 10.5
			})
		}

		window.setTimeout(zoomToRegion, 320)
	}, [])

	useEffect(() => {
		if (!mapLoaded) {
			return
		}

		const map = mapRef.current?.getMap()

		if (!map?.isStyleLoaded()) {
			return
		}

		const filter = riskFilter === null ? null : distributionZoneTierFilter(riskFilter)

		for (const id of RISK_FILTER_LAYER_IDS) {
			if (map.getLayer(id)) {
				map.setFilter(id, filter)
			}
		}
	}, [mapLoaded, riskFilter])

	useEffect(() => {
		if (!zoneCard) {
			return
		}

		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				closeZoneCard()
			}
		}

		window.addEventListener('keydown', onKey)

		return () => window.removeEventListener('keydown', onKey)
	}, [zoneCard, closeZoneCard])

	useEffect(() => {
		if (!zoneCard?.zoneId) {
			return
		}

		const id = zoneCard.zoneId
		const ac = new AbortController()

		void (async () => {
			try {
				const res = await fetch(`/api/distributionzone/${id}/tooltip`, { signal: ac.signal })

				if (!res.ok) {
					if (!ac.signal.aborted) {
						setZoneDetailPvcComment(null)
						setZoneDetailAnalyses([])
						setZoneDetailLoading(false)
					}

					return
				}

				const body = (await res.json()) as {
					pvcLevelComment: string | null
					recentAnalyses: RecentAnalysis[]
				}

				if (!ac.signal.aborted) {
					setZoneDetailPvcComment(body.pvcLevelComment)
					setZoneDetailAnalyses(body.recentAnalyses ?? [])
					setZoneDetailLoading(false)
				}
			} catch {
				if (!ac.signal.aborted) {
					setZoneDetailPvcComment(null)
					setZoneDetailAnalyses([])
					setZoneDetailLoading(false)
				}
			}
		})()

		return () => ac.abort()
	}, [zoneCard?.zoneId])

	const zoneCardPvcBadge = zoneCard ? pvcTooltipBadgeFromTileProperty(zoneCard.tooltipPvcRaw) : null

	const zoneCardVcmBadge = zoneCard ? vcmTooltipBadgeFromTileProperty(zoneCard.tooltipVcmRaw) : null

	const zoneCardStyle = useMemo(() => {
		if (!zoneCardScreen) {
			return undefined
		}

		const pad = 16
		const vw = typeof window !== 'undefined' ? window.innerWidth : 800
		const halfCard = Math.min(26 * 16, vw - 2 * pad) / 2
		const clampedX = Math.max(pad + halfCard, Math.min(zoneCardScreen.x, vw - pad - halfCard))

		return { left: clampedX, top: zoneCardScreen.y, marginTop: -8 }
	}, [zoneCardScreen])

	return (
		<div className='relative h-screen w-full'>
			<div className='absolute top-4 left-4 z-10 flex w-[min(36rem,calc(100%-2rem))] flex-col gap-3'>
				<SearchBar onSelectPlace={onSelectPlace} />
				{zonesLayerVisible ? (
					<Card className='border-navy-100 hidden gap-0 bg-white py-0 shadow-none md:block'>
						<CardContent className='px-4 py-4'>
							<div className='flex flex-wrap items-center gap-x-3 gap-y-2'>
								<CardTitle className='text-navy-800 shrink-0 font-sans text-[14px] font-normal'>Risks</CardTitle>
								<MapRiskFilters active={riskFilter} onChange={setRiskFilter} />
							</div>
						</CardContent>
					</Card>
				) : null}
			</div>
			<div className='relative h-full w-full'>
				<Map
					ref={mapRef}
					cursor={mapCursor}
					initialViewState={{
						longitude: MAP_INTRO_VIEW_STATE.longitude,
						latitude: MAP_INTRO_VIEW_STATE.latitude,
						zoom: MAP_INTRO_VIEW_STATE.zoom
					}}
					interactiveLayerIds={[DISTRIBUTION_ZONE_PICK_LAYER_ID, COUNTRIES_FILL_LAYER_ID]}
					mapStyle={mapStyle}
					style={{ width: '100%', height: '100%' }}
					onClick={onMapClick}
					onLoad={onMapLoad}
					onMove={onMapMove}
					onMouseMove={onMapMouseMove}
				/>
				{zoneCard && zoneCardScreen ? (
					<div className='pointer-events-none absolute inset-0 z-20'>
						<div
							className='pointer-events-auto absolute max-w-[min(26rem,calc(100vw-2rem))] -translate-x-1/2 -translate-y-full'
							style={zoneCardStyle}
						>
							<Card className='border-navy-100 gap-0 bg-white py-0 shadow-md'>
								<CardContent className='flex flex-col gap-2 px-4 py-3'>
									<p className='text-navy-800 text-sm font-medium'>{zoneCard.name}</p>
									<div className='flex flex-wrap gap-2'>
										{zoneCardPvcBadge ? (
											<span
												className='inline-flex rounded-3xl border px-3 py-1.5 text-left text-xs font-medium'
												style={zoneCardPvcBadge.style}
											>
												{zoneCardPvcBadge.label}
											</span>
										) : null}
										{zoneCardVcmBadge ? (
											<span
												className='inline-flex rounded-3xl border px-3 py-1.5 text-left text-xs font-medium'
												style={zoneCardVcmBadge.style}
											>
												{zoneCardVcmBadge.label}
											</span>
										) : null}
									</div>
									{zoneDetailPvcComment ? <p className='text-navy-600 text-xs'>{zoneDetailPvcComment}</p> : null}
									{zoneDetailLoading ? (
										<div className='flex flex-col gap-1.5 pt-1'>
											<div className='bg-navy-100 h-3 w-1/3 animate-pulse rounded' />
											<div className='bg-navy-100 h-2.5 w-3/4 animate-pulse rounded' />
											<div className='bg-navy-100 h-2.5 w-2/3 animate-pulse rounded' />
										</div>
									) : zoneDetailAnalyses.length > 0 ? (
										<div className='pt-1'>
											<p className='text-navy-800 text-xs font-semibold'>Top 3 VCM Results</p>
											<ul className='text-navy-600 mt-1 list-inside list-disc text-xs'>
												{zoneDetailAnalyses.map((a, i) => (
													<li key={i}>
														{formatAnalysisDate(a.date)}
														{a.vcmMeasure != null ? ` - ${a.vcmMeasure} µg/L` : ''}
													</li>
												))}
											</ul>
										</div>
									) : null}
									{zoneCard.zoneId != null ? (
										<Link
											href={`/${locale}${ROUTES.ACT}?zone=${zoneCard.zoneId}`}
											className='bg-navy-800 hover:bg-navy-700 mt-1 inline-flex items-center justify-center rounded-lg px-4 py-2 text-xs font-medium text-white transition-colors'
										>
											Take action !
										</Link>
									) : null}
								</CardContent>
							</Card>
						</div>
					</div>
				) : null}
			</div>
		</div>
	)
}
