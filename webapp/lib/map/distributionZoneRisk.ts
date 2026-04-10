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

export function distributionZoneTierFilter(tier: MapRiskTier): FilterSpecification {
	return ['==', DISTRIBUTION_ZONE_TIER_EXPR, tier]
}
