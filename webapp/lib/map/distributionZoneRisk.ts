import type { ExpressionSpecification, FilterSpecification } from 'maplibre-gl'

import { colorCodeConfig } from '@/lib/colorCode'

// Re-export for backwards compat — canonical definition now in colorCode.ts
export type { MapRiskTier } from '@/lib/colorCode'

const MAP_COLOR_KEY: ExpressionSpecification = [
	'downcase', ['to-string', ['coalesce', ['get', 'map_color'], '']]
]

export function buildMapFeatureFillColor(): ExpressionSpecification {
	return [
		'match',
		MAP_COLOR_KEY,
		'red',    colorCodeConfig.red.bg,
		'orange', colorCodeConfig.orange.bg,
		'yellow', colorCodeConfig.yellow.bg,
		'green',  colorCodeConfig.green.bg,
		'gray',   colorCodeConfig.gray.bg,
		'grey',   colorCodeConfig.gray.bg,
		colorCodeConfig.gray.bg, // default
	]
}

export function buildMapFeatureLineColor(): ExpressionSpecification {
	return [
		'match',
		MAP_COLOR_KEY,
		'red',    colorCodeConfig.red.border,
		'orange', colorCodeConfig.orange.border,
		'yellow', colorCodeConfig.yellow.border,
		'green',  colorCodeConfig.green.border,
		'gray',   colorCodeConfig.gray.border,
		'grey',   colorCodeConfig.gray.border,
		colorCodeConfig.gray.border, // default
	]
}

export function distributionZoneTierFilter(tier: import('@/lib/colorCode').MapRiskTier): FilterSpecification {
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
