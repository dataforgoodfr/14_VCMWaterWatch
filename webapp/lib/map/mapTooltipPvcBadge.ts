import type React from 'react'

import { riskTierConfig } from '@/lib/colorCode'

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
	return tilePropertyString(props.tooltip_pvc_level)
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

const PVC_TOOLTIP_BADGES: Record<string, Pick<PvcTooltipBadge, 'label' | 'style'>> = {
	'No PVC': {
		label: 'No PVC recorded',
		style: tierStyle('absent'),
	},
	'PVC, Unknown date': {
		label: 'PVC present, details unknown',
		style: tierStyle('probable'),
	},
	'PVC, pre-1980': {
		label: 'PVC present, pre-1980',
		style: tierStyle('confirme'),
	},
	'No response or data unavailable': {
		label: 'No response or data unavailable',
		// slate-600 ≈ #475569
		style: { borderColor: '#475569', backgroundColor: '#475569', color: '#ffffff' },
	},
	Unknown: {
		label: 'Unknown PVC presence',
		style: tierStyle('inconnu'),
	},
}

export function pvcTooltipBadgeFromTileProperty(raw: unknown): PvcTooltipBadge | null {
	const key = tilePropertyString(raw)

	if (key === null) {
		return null
	}

	const cfg = PVC_TOOLTIP_BADGES[key]

	if (!cfg) {
		return null
	}

	return { label: cfg.label, style: cfg.style }
}
