import type { StyleSpecification } from 'maplibre-gl'

import { buildMapFeatureFillColor, buildMapFeatureLineColor } from './distributionZoneRisk'
import { resolveRiskCssVar } from './riskCssVars'

export const COUNTRIES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_countries.pmtiles'
export const DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_distribution_zones.pmtiles'
export const COUNTRIES_PM_TILES_URL = `pmtiles://${COUNTRIES_PM_TILES_PUBLIC_PATH}`
export const DISTRIBUTION_ZONES_PM_TILES_URL = `pmtiles://${DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH}`
export const COUNTRIES_SOURCE_LAYER = 'data_countries'
export const DISTRIBUTION_ZONES_SOURCE_LAYER = 'data_distribution_zones'

export const MAP_DISTRIBUTION_ZONES_MIN_ZOOM = 4.5

export const WORLD_COUNTRIES_GEOJSON_URL =
	'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

export function createBaseMapStyle(
	resolveRiskColor: (cssVarName: string) => string = resolveRiskCssVar
): StyleSpecification {
	return {
		version: 8,
		sources: {
			'world-countries': {
				type: 'geojson',
				data: WORLD_COUNTRIES_GEOJSON_URL
			},
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
				id: 'world-countries-outline',
				type: 'line',
				source: 'world-countries',
				paint: {
					'line-color': '#b0bfc9',
					'line-width': 1
				}
			},
			{
				id: 'countries-lowzoom-fill',
				type: 'fill',
				source: 'countries-vector',
				'source-layer': COUNTRIES_SOURCE_LAYER,
				maxzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
				paint: {
					'fill-color': buildMapFeatureFillColor(resolveRiskColor),
					'fill-opacity': 0.88
				}
			},
			{
				id: 'countries-lowzoom-outline',
				type: 'line',
				source: 'countries-vector',
				'source-layer': COUNTRIES_SOURCE_LAYER,
				maxzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
				paint: {
					'line-color': buildMapFeatureLineColor(resolveRiskColor),
					'line-width': 0.8
				}
			},
			{
				id: 'distribution-zones-fill',
				type: 'fill',
				source: 'distribution-zones-vector',
				'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
				minzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
				paint: {
					'fill-color': buildMapFeatureFillColor(resolveRiskColor),
					'fill-opacity': 0.88
				}
			},
			{
				id: 'distribution-zones-outline',
				type: 'line',
				source: 'distribution-zones-vector',
				'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
				minzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
				paint: {
					'line-color': buildMapFeatureLineColor(resolveRiskColor),
					'line-width': 0.8
				}
			}
		]
	}
}
