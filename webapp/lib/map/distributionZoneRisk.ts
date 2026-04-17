import type { ExpressionSpecification, FilterSpecification } from 'maplibre-gl'

export type MapRiskTier = 'confirme' | 'probable' | 'absent' | 'inconnu'

const vcmStr: ExpressionSpecification = ['to-string', ['coalesce', ['get', 'vcm_level'], '']]
const pvcStr: ExpressionSpecification = ['to-string', ['coalesce', ['get', 'pvc_level'], '']]

export const DISTRIBUTION_ZONE_TIER_EXPR: ExpressionSpecification = [
	'case',
	['all', ['==', vcmStr, ''], ['==', pvcStr, '']],
	'inconnu',
	[
		'any',
		['==', ['get', 'vcm_level'], 'Non conforme'],
		['==', ['get', 'vcm_level'], 'Non-conforme'],
		['==', ['get', 'pvc_level'], 'Non conforme'],
		['==', ['get', 'pvc_level'], 'Non-conforme']
	],
	'confirme',
	[
		'any',
		['==', ['get', 'vcm_level'], 'Vigilance renforcée'],
		['==', ['get', 'pvc_level'], 'Vigilance renforcée'],
		['==', ['get', 'vcm_level'], 'Vigilance'],
		['==', ['get', 'pvc_level'], 'Vigilance']
	],
	'probable',
	'absent'
]

export function buildDistributionZoneFillColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const inconnu = resolve('--risk-inconnu-bg')

	return [
		'match',
		DISTRIBUTION_ZONE_TIER_EXPR,
		'confirme',
		resolve('--risk-confirme-bg'),
		'probable',
		resolve('--risk-probable-bg'),
		'absent',
		resolve('--risk-absent-bg'),
		'inconnu',
		inconnu,
		inconnu
	]
}

export function buildDistributionZoneLineColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const inconnu = resolve('--risk-inconnu-border')

	return [
		'match',
		DISTRIBUTION_ZONE_TIER_EXPR,
		'confirme',
		resolve('--risk-confirme-border'),
		'probable',
		resolve('--risk-probable-border'),
		'absent',
		resolve('--risk-absent-border'),
		'inconnu',
		inconnu,
		inconnu
	]
}

const MAP_COLOR_KEY: ExpressionSpecification = ['downcase', ['to-string', ['coalesce', ['get', 'map_color'], '']]]

const MAP_COLOR_ORANGE_BG = '#fed7aa'
const MAP_COLOR_ORANGE_BORDER = '#ea580c'

const MAP_COLOR_YELLOW_BG = '#fef08a'
const MAP_COLOR_YELLOW_BORDER = '#a16207'

export function buildMapFeatureFillColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const tierFallback = buildDistributionZoneFillColor(resolve)

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
		resolve('--risk-inconnu-bg'),
		'grey',
		resolve('--risk-inconnu-bg'),
		tierFallback
	]
}

export function buildMapFeatureLineColor(resolve: (cssVarName: string) => string): ExpressionSpecification {
	const tierFallback = buildDistributionZoneLineColor(resolve)

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
		resolve('--risk-inconnu-border'),
		'grey',
		resolve('--risk-inconnu-border'),
		tierFallback
	]
}

export function distributionZoneTierFilter(tier: MapRiskTier): FilterSpecification {
	return ['==', DISTRIBUTION_ZONE_TIER_EXPR, tier]
}
