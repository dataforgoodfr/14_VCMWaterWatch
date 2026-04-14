'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import maplibregl from 'maplibre-gl'
import type { MapLibreEvent } from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import Map from 'react-map-gl/maplibre'
import type { MapRef } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { GeocodePlace } from '@/lib/geocode/photon'
import { distributionZoneTierFilter, type MapRiskTier } from '@/lib/map/distributionZoneRisk'
import { createBaseMapStyle } from '@/lib/map/mapStyle'
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

export function MapView() {
	const mapRef = useRef<MapRef>(null)
	const [mapLoaded, setMapLoaded] = useState(false)
	const [riskFilter, setRiskFilter] = useState<MapRiskTier | null>(null)
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

	const onMapLoad = useCallback((e: MapLibreEvent) => {
		const map = e.target

		setMapLoaded(true)

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

		for (const id of DISTRIBUTION_ZONES_LAYER_IDS) {
			if (map.getLayer(id)) {
				map.setFilter(id, filter)
			}
		}
	}, [mapLoaded, riskFilter])

	return (
		<div className='relative h-[calc(100vh-168px)] min-h-[400px] w-full'>
			<div className='absolute top-4 left-4 z-10 flex max-w-[min(100%,36rem)] flex-col gap-3'>
				<Card className='border-navy-100 gap-0 bg-white py-0 shadow-none'>
					<CardContent className='px-4 py-4'>
						<div className='flex flex-wrap items-center gap-x-3 gap-y-2'>
							<CardTitle className='text-navy-800 shrink-0 font-sans text-[14px] font-normal'>Risks</CardTitle>
							<MapRiskFilters active={riskFilter} onChange={setRiskFilter} />
						</div>
					</CardContent>
				</Card>
				<SearchBar onSelectPlace={onSelectPlace} />
			</div>
			<Map
				ref={mapRef}
				initialViewState={{
					longitude: MAP_INTRO_VIEW_STATE.longitude,
					latitude: MAP_INTRO_VIEW_STATE.latitude,
					zoom: MAP_INTRO_VIEW_STATE.zoom
				}}
				mapStyle={mapStyle}
				style={{ width: '100%', height: '100%' }}
				onLoad={onMapLoad}
			/>
		</div>
	)
}
