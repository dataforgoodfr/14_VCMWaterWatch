'use client'

import { useCallback, useEffect, useRef } from 'react'

import maplibregl from 'maplibre-gl'
import type { MapLibreEvent } from 'maplibre-gl'
import { PMTiles, Protocol, type Header } from 'pmtiles'
import Map from 'react-map-gl/maplibre'
import type { MapRef } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { GeocodePlace } from '@/lib/geocode/photon'
import { BASE_STYLE, DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH } from '@/lib/map/mapStyle'
import { SearchBar } from './SearchBar'

let protocolRegistered = false
let pmtilesProtocol: Protocol | null = null

function headerToBoundsLngLat(header: Header) {
	return [
		[header.minLon, header.minLat],
		[header.maxLon, header.maxLat]
	] as [[number, number], [number, number]]
}

export function MapView() {
	const mapRef = useRef<MapRef>(null)

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

		const run = async () => {
			try {
				const url = new URL(DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH, window.location.origin).href
				const header = await new PMTiles(url).getHeader()

				map.fitBounds(headerToBoundsLngLat(header), {
					padding: { top: 24, bottom: 24, left: 24, right: 24 },
					duration: 900,
					linear: false,
					maxZoom: header.maxZoom
				})
			} catch {
				// ignore
			}
		}

		void run()
	}, [])

	return (
		<div className='relative h-[calc(100vh-168px)] min-h-[400px] w-full'>
			<div className='absolute top-4 left-4 z-10'>
				<SearchBar onSelectPlace={onSelectPlace} />
			</div>
			<Map
				ref={mapRef}
				initialViewState={{
					longitude: 10,
					latitude: 50,
					zoom: 3.5
				}}
				mapStyle={BASE_STYLE}
				style={{ width: '100%', height: '100%' }}
				onLoad={onMapLoad}
			/>
		</div>
	)
}
