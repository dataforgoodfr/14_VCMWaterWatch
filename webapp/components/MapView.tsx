'use client'

import { useCallback, useEffect, useRef } from 'react'

import maplibregl from 'maplibre-gl'
import { Protocol } from 'pmtiles'
import Map from 'react-map-gl/maplibre'
import type { MapRef } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { GeocodePlace } from '@/lib/geocode/photon'
import { BASE_STYLE } from '@/lib/map/mapStyle'
import { SearchBar } from './SearchBar'

let protocolRegistered = false
let pmtilesProtocol: Protocol | null = null

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
				style={{ width: '100%', height: '100%' }}
				mapStyle={BASE_STYLE}
			/>
		</div>
	)
}
