import type { StyleSpecification } from 'maplibre-gl'

export const COUNTRIES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_countries.pmtiles'
export const DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_distribution_zones.pmtiles'
export const COUNTRIES_PM_TILES_URL = `pmtiles://${COUNTRIES_PM_TILES_PUBLIC_PATH}`
export const DISTRIBUTION_ZONES_PM_TILES_URL = `pmtiles://${DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH}`
export const COUNTRIES_SOURCE_LAYER = 'data_countries'
export const DISTRIBUTION_ZONES_SOURCE_LAYER = 'data_distribution_zones'

export const BASE_STYLE: StyleSpecification = {
	version: 8,
	sources: {
		'countries-vector': {
			type: 'vector',
			url: COUNTRIES_PM_TILES_URL
		},
		'distribution-zones-vector': {
			type: 'vector',
			url: DISTRIBUTION_ZONES_PM_TILES_URL
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
			id: 'countries-outline',
			type: 'line',
			source: 'countries-vector',
			'source-layer': COUNTRIES_SOURCE_LAYER,
			paint: {
				'line-color': '#b0bfc9',
				'line-width': 1.2
			}
		},
		{
			id: 'distribution-zones-fill',
			type: 'fill',
			source: 'distribution-zones-vector',
			'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
			paint: {
				'fill-color': '#1f9ba9',
				'fill-opacity': 0.5
			}
		},
		{
			id: 'distribution-zones-outline',
			type: 'line',
			source: 'distribution-zones-vector',
			'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
			paint: {
				'line-color': '#118996',
				'line-width': 0.8
			}
		}
	]
}
