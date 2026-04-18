/**
 * NocoDB single-select options for the `Map Color` column.
 * These are the only valid values; NocoDB enforces the constraint.
 */
export type ColorCode = 'green' | 'yellow' | 'orange' | 'red' | 'gray'

/**
 * Return the NocoDB `Map Color` value as a `ColorCode`, defaulting to `'gray'`.
 *
 * `Map Color` is a NocoDB single-select with exactly these options:
 * - `'red'`: Non-compliant
 * - `'orange'`: Reinforced vigilance
 * - `'yellow'`: Vigilance
 * - `'green'`: Compliant
 * - `'gray'`: Unknown
 *
 * Since NocoDB enforces the single-select constraint, any non-null return
 * is guaranteed to be a valid `ColorCode` key in `colorCodeConfig`.
 * An unknown value at runtime would be a NocoDB data issue, not an app bug.
 */
export function colorCodeFromMapColor(mapColor: string | null | undefined): ColorCode {
	switch ((mapColor ?? '').toLowerCase()) {
		case 'red':    return 'red'
		case 'orange': return 'orange'
		case 'yellow': return 'yellow'
		case 'green':  return 'green'
		default:       return 'gray'
	}
}

export const colorCodeConfig: Record<
	ColorCode,
	{
		label: string
		/** Saturated hex — badge backgrounds, legend dots */
		solid: string
		/** Light hex — map polygon fills, filter-button backgrounds */
		bg: string
		/** Dark hex — map strokes, filter-button borders */
		border: string
	}
> = {
	red:    { label: 'Non-compliant',        solid: '#ef4444', bg: '#fee2e2', border: '#dc2626' },
	orange: { label: 'Reinforced vigilance', solid: '#f97316', bg: '#fed7aa', border: '#ea580c' },
	yellow: { label: 'Vigilance',            solid: '#facc15', bg: '#fef08a', border: '#a16207' },
	green:  { label: 'Compliant',            solid: '#22c55e', bg: '#dcfce7', border: '#16a34a' },
	gray:   { label: 'Unknown',              solid: '#9ca3af', bg: '#f1f5f9', border: '#64748b' },
}

/** Canonical type for the four risk tiers shown on the map */
export type MapRiskTier = 'confirme' | 'probable' | 'absent' | 'inconnu'

export const riskTierConfig: Record<
	MapRiskTier,
	{
		label: string
		/** Light hex — map polygon fills, filter-button backgrounds */
		bg: string
		/** Dark hex — map strokes, filter-button borders */
		border: string
	}
> = {
	confirme: { label: 'Confirmed', bg: colorCodeConfig.red.bg,    border: colorCodeConfig.red.border },
	probable: { label: 'Probable',  bg: colorCodeConfig.orange.bg,  border: colorCodeConfig.orange.border },
	absent:   { label: 'Absent',    bg: colorCodeConfig.green.bg,   border: colorCodeConfig.green.border },
	inconnu:  { label: 'Unknown',   bg: colorCodeConfig.gray.bg,    border: colorCodeConfig.gray.border },
}
