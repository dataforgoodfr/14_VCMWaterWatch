import type { LayerSpecification, StyleSpecification } from 'maplibre-gl'

import { buildMapFeatureFillColor, buildMapFeatureLineColor } from './distributionZoneRisk'
import positronStyle from './positronStyle.json'

export const COUNTRIES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_countries.pmtiles'
export const DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH = '/pmtiles/data_distribution_zones.pmtiles'
export const COUNTRIES_PM_TILES_URL = `pmtiles://${COUNTRIES_PM_TILES_PUBLIC_PATH}`
export const DISTRIBUTION_ZONES_PM_TILES_URL = `pmtiles://${DISTRIBUTION_ZONES_PM_TILES_PUBLIC_PATH}`
export const COUNTRIES_SOURCE_LAYER = 'data_countries'
export const DISTRIBUTION_ZONES_SOURCE_LAYER = 'data_distribution_zones'

export const COUNTRIES_FILL_LAYER_ID = 'countries-fill'
export const COUNTRIES_OUTLINE_LAYER_ID = 'countries-outline'
export const MAP_DISTRIBUTION_ZONES_MIN_ZOOM = 4.5

export const WORLD_COUNTRIES_GEOJSON_URL =
	'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

/** URL the bundled positronStyle.json was originally fetched from. Kept for reference only. */
export const OPENFREEMAP_STYLE_URL = 'https://tiles.openfreemap.org/styles/positron'

export const OSM_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
export const OPENFREEMAP_ATTRIBUTION = '© <a href="https://openfreemap.org">OpenFreeMap</a>'

/**
 * Allow-list of source-layer values from OpenFreeMap positron to include.
 *
 * We keep only layers that provide geographic anchoring without competing
 * with our thematic choropleth fills:
 * - Water body fills (lakes, sea) – light blue, low contrast.
 * - Major water lines (rivers).
 * - Major road lines (motorway / major only – see narrowing below).
 * - Place labels (city / town / village / country / state).
 * - Road labels (motorway shields, major road names).
 *
 * Excluded: landuse fills, buildings, minor roads, rail, admin boundaries.
 *
 * The `transportation` source-layer is further narrowed: only layers whose
 * id starts with `highway_motorway` or `highway_major` are included.
 */
const BASEMAP_SOURCE_LAYER_ALLOW_LIST: ReadonlySet<string> = new Set([
	'water',
	'waterway',
	'water_name',
	'place',
	'transportation_name',
	'transportation' // narrowed to motorway/major only below
])

/**
 * Returns true if a basemap layer should be included in the merged style.
 *
 * Filtering rules:
 * 1. `background` type → always include.
 * 2. No `source-layer` → exclude (only background handled above).
 * 3. `source-layer` not in allow-list → exclude.
 * 4. `source-layer === 'transportation'` → include only motorway / major.
 * 5. All other allow-listed source-layers → include.
 */
function isAllowedBasemapLayer(layer: LayerSpecification): boolean {
	// Always include background-type layers from basemap
	if (layer.type === 'background') {
		return true
	}

	// Layers with no source-layer (e.g. raster, hillshade, custom) are excluded
	if (!('source-layer' in layer) || typeof layer['source-layer'] !== 'string') {
		return false
	}

	const sourceLayer = layer['source-layer']

	if (!BASEMAP_SOURCE_LAYER_ALLOW_LIST.has(sourceLayer)) {
		return false
	}

	// Narrow transportation to motorway and major roads only
	if (sourceLayer === 'transportation') {
		return layer.id.startsWith('highway_motorway') || layer.id.startsWith('highway_major')
	}

	return true
}

/**
 * Splits basemap layers into two groups so we can interleave them with our
 * thematic layers:
 * - `waterAndRoads`: background, water fills, river lines, road lines
 *   → rendered below thematic fills
 * - `labels`: symbol layers (place names, road shields, water names)
 *   → rendered above thematic fills for legibility
 */
function splitBasemapLayers(layers: LayerSpecification[]): {
	waterAndRoads: LayerSpecification[]
	labels: LayerSpecification[]
} {
	const waterAndRoads: LayerSpecification[] = []
	const labels: LayerSpecification[] = []

	for (const layer of layers) {
		if (layer.type === 'symbol') {
			labels.push(layer)
		} else {
			waterAndRoads.push(layer)
		}
	}

	return { waterAndRoads, labels }
}

/** Our own thematic layers (countries + distribution zones). */
function buildThematicLayers(): LayerSpecification[] {
	return [
		{
			id: 'world-countries-outline',
			type: 'line',
			source: 'world-countries',
			maxzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
			paint: {
				'line-color': '#b0bfc9',
				'line-width': 1
			}
		} as LayerSpecification,
		{
			id: COUNTRIES_FILL_LAYER_ID,
			type: 'fill',
			source: 'countries-vector',
			'source-layer': COUNTRIES_SOURCE_LAYER,
			paint: {
				'fill-color': buildMapFeatureFillColor(),
				// Full opacity when zoomed out; faded once distribution zones appear
				'fill-opacity': ['step', ['zoom'], 0.88, MAP_DISTRIBUTION_ZONES_MIN_ZOOM, 0.25]
			}
		} as LayerSpecification,
		{
			id: COUNTRIES_OUTLINE_LAYER_ID,
			type: 'line',
			source: 'countries-vector',
			'source-layer': COUNTRIES_SOURCE_LAYER,
			paint: {
				'line-color': buildMapFeatureLineColor(),
				'line-width': 0.8,
				'line-opacity': ['step', ['zoom'], 1, MAP_DISTRIBUTION_ZONES_MIN_ZOOM, 0.3]
			}
		} as LayerSpecification,
		{
			id: 'distribution-zones-fill',
			type: 'fill',
			source: 'distribution-zones-vector',
			'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
			minzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
			paint: {
				'fill-color': buildMapFeatureFillColor(),
				'fill-opacity': 0.88
			}
		} as LayerSpecification,
		{
			id: 'distribution-zones-outline',
			type: 'line',
			source: 'distribution-zones-vector',
			'source-layer': DISTRIBUTION_ZONES_SOURCE_LAYER,
			minzoom: MAP_DISTRIBUTION_ZONES_MIN_ZOOM,
			paint: {
				'line-color': buildMapFeatureLineColor(),
				'line-width': 0.8
			}
		} as LayerSpecification
	]
}

/** Our own thematic sources. */
function buildThematicSources(): StyleSpecification['sources'] {
	return {
		'world-countries': {
			type: 'geojson',
			data: WORLD_COUNTRIES_GEOJSON_URL,
			attribution: OSM_ATTRIBUTION
		},
		'countries-vector': {
			type: 'vector',
			url: COUNTRIES_PM_TILES_URL
		},
		'distribution-zones-vector': {
			type: 'vector',
			url: DISTRIBUTION_ZONES_PM_TILES_URL
		}
	}
}

/**
 * Builds the full map style by merging a filtered subset of the bundled
 * OpenFreeMap positron style with our thematic layers.
 *
 * Layer order: basemap background → water + roads → thematic fills → labels
 *
 * positronStyle.json is a bundle-time snapshot (no fetch, no flicker).
 * To update: curl -fsSL https://tiles.openfreemap.org/styles/positron | python3 -m json.tool --compact > webapp/lib/map/positronStyle.json
 */
let _cachedStyle: StyleSpecification | null = null

export function createBaseMapStyle(): StyleSpecification {
	if (_cachedStyle) {
		return _cachedStyle
	}

	const basemapStyle = positronStyle as unknown as StyleSpecification

	const sourceBasemapLayers = basemapStyle.layers ?? []

	const hasTransportationLayers = sourceBasemapLayers.some(
		l => 'source-layer' in l && l['source-layer'] === 'transportation'
	)

	const allowedBasemapLayers = sourceBasemapLayers.filter(isAllowedBasemapLayer)

	// Guard against upstream renames of `highway_motorway*` / `highway_major*`
	// layer ids. If the source has transportation layers but our narrowing
	// matched none, roads would silently disappear.
	const matchedTransportation = allowedBasemapLayers.some(
		l => 'source-layer' in l && l['source-layer'] === 'transportation'
	)

	if (hasTransportationLayers && !matchedTransportation) {
		console.warn(
			'[mapStyle] OpenFreeMap transportation layers present but none matched the highway_motorway/highway_major id prefix allow-list. Road network will be missing from the basemap; layer ids may have been renamed upstream.'
		)
	}

	const { waterAndRoads, labels } = splitBasemapLayers(allowedBasemapLayers)

	const mergedSources: StyleSpecification['sources'] = {
		...(basemapStyle.sources ?? {}),
		...buildThematicSources()
	}

	// Add attribution to basemap sources
	for (const key of Object.keys(basemapStyle.sources ?? {})) {
		const src = mergedSources[key]

		if (src && !('attribution' in src && src.attribution)) {
			;(src as Record<string, unknown>).attribution = `${OSM_ATTRIBUTION} | ${OPENFREEMAP_ATTRIBUTION}`
		}
	}

	const layers: LayerSpecification[] = [...waterAndRoads, ...buildThematicLayers(), ...labels]

	if (!basemapStyle.glyphs) {
		throw new Error('[mapStyle] positronStyle.json is missing "glyphs" — re-snapshot the file from OpenFreeMap')
	}

	_cachedStyle = {
		version: 8,
		glyphs: basemapStyle.glyphs,
		sprite: basemapStyle.sprite,
		sources: mergedSources,
		layers
	}

	return _cachedStyle
}

// ---------------------------------------------------------------------------
// Compatibility shim – callers that imported these no longer need them.
// ---------------------------------------------------------------------------

/** @deprecated The style is now bundled; there is no async fallback. */
export function createFallbackMapStyle(): StyleSpecification {
	return createBaseMapStyle()
}
