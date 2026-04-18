import type { ExpressionSpecification, FilterSpecification } from 'maplibre-gl'

export type MapRiskTier = 'confirme' | 'probable' | 'absent' | 'inconnu'

// `map_color` is a NocoDB single-select column (values: red, orange, yellow, green, gray).
// Normalise to lowercase so match expressions below are case-insensitive.
// Coalesces to '' when absent so missing values fall to the inconnu default.
const MAP_COLOR_KEY: ExpressionSpecification = ['downcase', ['to-string', ['coalesce', ['get', 'map_color'], '']]]

const MAP_COLOR_ORANGE_BG = '#fed7aa'
const MAP_COLOR_ORANGE_BORDER = '#ea580c'

const MAP_COLOR_YELLOW_BG = '#fef08a'
const MAP_COLOR_YELLOW_BORDER = '#a16207'

export function buildMapFeatureFillColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const inconnu = resolve('--risk-inconnu-bg')

	return [
		'match',
		MAP_COLOR_KEY,
		'red',
		resolve('--risk-confirme-bg'),
		'orange',
		MAP_COLOR_ORANGE_BG,
		'yellow',
		MAP_COLOR_YELLOW_BG,
		'green',
		resolve('--risk-absent-bg'),
		'gray',
		inconnu,
		'grey',
		inconnu,
		inconnu // absent / null map_color → inconnu
	]
}

export function buildMapFeatureLineColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const inconnu = resolve('--risk-inconnu-border')

	return [
		'match',
		MAP_COLOR_KEY,
		'red',
		resolve('--risk-confirme-border'),
		'orange',
		MAP_COLOR_ORANGE_BORDER,
		'yellow',
		MAP_COLOR_YELLOW_BORDER,
		'green',
		resolve('--risk-absent-border'),
		'gray',
		inconnu,
		'grey',
		inconnu,
		inconnu // absent / null map_color → inconnu
	]
}

// Map tier filter buttons to map_color values:
//   confirme → red
//   probable → orange or yellow (both represent vigilance states)
//   absent   → green
//   inconnu  → gray / grey / no map_color set
export function distributionZoneTierFilter(tier: MapRiskTier): FilterSpecification {
	switch (tier) {
		case 'confirme':
			return ['==', MAP_COLOR_KEY, 'red']
		case 'probable':
			return ['any', ['==', MAP_COLOR_KEY, 'orange'], ['==', MAP_COLOR_KEY, 'yellow']]
		case 'absent':
			return ['==', MAP_COLOR_KEY, 'green']
		case 'inconnu':
			return ['any', ['==', MAP_COLOR_KEY, 'gray'], ['==', MAP_COLOR_KEY, 'grey'], ['==', MAP_COLOR_KEY, '']]
	}
}
