import type React from 'react'

import { riskTierConfig, colorCodeConfig } from '@/lib/colorCode'

export interface PvcTooltipBadge {
	label: string
	style: React.CSSProperties
}

export function tilePropertyString(value: unknown): string | null {
	if (typeof value === 'string') {
		const t = value.trim()

		return t === '' ? null : t
	}

	if (typeof value === 'number' && Number.isFinite(value)) {
		return String(value)
	}

	return null
}

export function rawTooltipPvcFromFeatureProperties(props: Record<string, unknown>): string | null {
	return tilePropertyString(props.pvc_level)
}

export function mapTooltipPvcFromNocoLink(link: unknown): string | null {
	if (link == null) {
		return null
	}

	let node: unknown = link

	if (Array.isArray(node)) {
		if (node.length === 0) {
			return null
		}

		node = node[0]
	}

	if (typeof node !== 'object' || node === null) {
		return null
	}

	const rec = node as Record<string, unknown>

	const inner =
		rec.fields !== undefined && typeof rec.fields === 'object' && rec.fields !== null
			? (rec.fields as Record<string, unknown>)
			: rec

	return tilePropertyString(inner['PVC Level'])
}

function tierStyle(tier: keyof typeof riskTierConfig): React.CSSProperties {
	const t = riskTierConfig[tier]

	return { borderColor: t.border, backgroundColor: t.bg, color: t.border }
}

/** Style for the "No response or data unavailable" badge (no riskTier equivalent) */
const UNAVAILABLE_BG = '#475569' // slate-600
const UNAVAILABLE_FG = '#ffffff'

function buildCaseInsensitiveMap(
	entries: Record<string, Pick<PvcTooltipBadge, 'label' | 'style'>>
): Map<string, Pick<PvcTooltipBadge, 'label' | 'style'>> {
	const map = new Map<string, Pick<PvcTooltipBadge, 'label' | 'style'>>()

	for (const [k, v] of Object.entries(entries)) {
		map.set(k.toLowerCase(), v)
	}

	return map
}

const PVC_TOOLTIP_BADGES = buildCaseInsensitiveMap({
	'No PVC': {
		label: 'No PVC recorded',
		style: tierStyle('absent')
	},
	'PVC, Unknown date': {
		label: 'PVC present, details unknown',
		style: tierStyle('probable')
	},
	'PVC, Pre-1980': {
		label: 'PVC present, pre-1980',
		style: tierStyle('confirme')
	},
	'No response or data unavailable': {
		label: 'No response or data unavailable',
		style: { borderColor: UNAVAILABLE_BG, backgroundColor: UNAVAILABLE_BG, color: UNAVAILABLE_FG }
	},
	Unknown: {
		label: 'Unknown PVC presence',
		style: tierStyle('inconnu')
	}
})

// --- VCM badge config ---

const VCM_TOOLTIP_BADGES = buildCaseInsensitiveMap({
	'> 0.5 mcg/L': {
		label: 'VCM level > 0.5 mcg/L',
		style: tierStyle('confirme')
	},
	'< 0.5 mcg/L': {
		label: 'VCM level < 0.5 mcg/L',
		style: tierStyle('absent')
	},
	'No analysis': {
		label: 'No VCM analysis',
		style: {
			borderColor: colorCodeConfig.yellow.border,
			backgroundColor: colorCodeConfig.yellow.bg,
			color: colorCodeConfig.yellow.border
		}
	},
	Unknown: {
		label: 'VCM level unknown',
		style: tierStyle('inconnu')
	}
})

export function vcmTooltipBadgeFromTileProperty(raw: unknown): PvcTooltipBadge | null {
	const key = tilePropertyString(raw)

	if (key === null) {
		return null
	}

	const cfg = VCM_TOOLTIP_BADGES.get(key.toLowerCase())

	if (!cfg) {
		return null
	}

	return { label: cfg.label, style: cfg.style }
}

export function rawTooltipVcmFromFeatureProperties(props: Record<string, unknown>): string | null {
	return tilePropertyString(props.vcm_level)
}

export function pvcTooltipBadgeFromTileProperty(raw: unknown): PvcTooltipBadge | null {
	const key = tilePropertyString(raw)

	if (key === null) {
		return null
	}

	const cfg = PVC_TOOLTIP_BADGES.get(key.toLowerCase())

	if (!cfg) {
		return null
	}

	return { label: cfg.label, style: cfg.style }
}
