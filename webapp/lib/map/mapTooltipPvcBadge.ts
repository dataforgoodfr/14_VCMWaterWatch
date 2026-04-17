export interface PvcTooltipBadge {
	label: string
	className: string
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

const PVC_TOOLTIP_BADGES: Record<string, Pick<PvcTooltipBadge, 'label' | 'className'>> = {
	'No PVC': {
		label: 'No PVC recorded',
		className: 'border-1 border-[var(--risk-absent-border)] bg-[var(--risk-absent-bg)] text-[var(--risk-absent-border)]'
	},
	'PVC, Unknown date': {
		label: 'PVC present, details unknown',
		className:
			'border-1 border-[var(--risk-probable-border)] bg-[var(--risk-probable-bg)] text-[var(--risk-probable-border)]'
	},
	'PVC, pre-1980': {
		label: 'PVC present, pre-1980',
		className:
			'border-1 border-[var(--risk-confirme-border)] bg-[var(--risk-confirme-bg)] text-[var(--risk-confirme-border)]'
	},
	'No response or data unavailable': {
		label: 'No response or data unavailable',
		className: 'border border-slate-600/90 bg-slate-600/90 text-white'
	},
	Unknown: {
		label: 'Unknown PVC presence',
		className:
			'border-1 border-[var(--risk-inconnu-border)] bg-[var(--risk-inconnu-bg)] text-[var(--risk-inconnu-border)]'
	}
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

	return { label: cfg.label, className: cfg.className }
}
