'use client'

import { useMemo } from 'react'

import Map, { Layer, Source } from 'react-map-gl/maplibre'
import 'maplibre-gl/dist/maplibre-gl.css'

import type { MapData } from '@/lib/map/mapData'
import { recordsToGeoJSON } from '@/lib/map/mapData'
import { BASE_STYLE, COUNTRIES_LINE_LAYER, ZONES_FILL_LAYER } from '@/lib/map/mapStyle'
import { SearchBar } from './SearchBar'

interface MapViewProps {
	initialData: MapData
}

export function MapView({ initialData }: MapViewProps) {
	const geojson = useMemo(
		() => recordsToGeoJSON(initialData.zones, initialData.countries),
		[initialData.zones, initialData.countries]
	)

	const recordsCount = initialData.zones.length + initialData.countries.length

	return (
		<div className='relative h-[calc(100vh-168px)] min-h-[400px] w-full'>
			<div className='absolute top-4 left-4 z-10'>
				<SearchBar />
			</div>
			{geojson.features.length === 0 && recordsCount > 0 && (
				<div className='absolute bottom-4 left-1/2 z-10 -translate-x-1/2 rounded bg-amber-100 px-4 py-2 text-sm text-amber-900'>
					{recordsCount} enregistrement(s) chargé(s) mais aucune géométrie trouvée. Vérifiez que les colonnes Geometry
					ou Municipality Geometries sont renseignées.
				</div>
			)}
			<Map
				initialViewState={{
					longitude: 10,
					latitude: 50,
					zoom: 3.5
				}}
				style={{ width: '100%', height: '100%' }}
				mapStyle={BASE_STYLE}
			>
				{geojson.features.length > 0 && (
					<Source id='distribution-zones' type='geojson' data={geojson}>
						<Layer {...COUNTRIES_LINE_LAYER} />
						<Layer {...ZONES_FILL_LAYER} />
					</Source>
				)}
			</Map>
		</div>
	)
}
