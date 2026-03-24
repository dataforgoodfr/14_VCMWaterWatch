import type { StyleSpecification } from 'maplibre-gl'
import type { LayerProps } from 'react-map-gl/maplibre'

export const WORLD_COUNTRIES_GEOJSON_URL =
	'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

export const BASE_STYLE: StyleSpecification = {
	version: 8,
	sources: {
		'world-countries': {
			type: 'geojson',
			data: WORLD_COUNTRIES_GEOJSON_URL
		}
	},
	layers: [
		{
			id: 'background',
			type: 'background' as const,
			paint: {
				'background-color': '#f9fafb'
			}
		},
		{
			id: 'world-countries-outline',
			type: 'line',
			source: 'world-countries',
			paint: {
				'line-color': '#b0bfc9',
				'line-width': 0.8
			}
		}
	]
}

export const ZONES_FILL_LAYER: LayerProps = {
	id: 'zones-fill',
	type: 'fill',
	filter: ['==', ['get', 'layer'], 'zone'],
	paint: {
		'fill-color': '#1f9ba9',
		'fill-opacity': 0.5
	}
}

export const COUNTRIES_LINE_LAYER: LayerProps = {
	id: 'countries-outline',
	type: 'line',
	filter: ['==', ['get', 'layer'], 'country'],
	paint: {
		'line-color': '#b0bfc9',
		'line-width': 1.2
	}
}
