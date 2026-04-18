/**
 * NocoDB single-select options for the `Map Color` column.
 * These are the only valid values; NocoDB enforces the constraint.
 */
export type ColorCode = 'green' | 'yellow' | 'orange' | 'red' | 'gray'

/**
 * Return the NocoDB `Map Color` value as a `ColorCode`, or `null` if absent.
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
export function colorCodeFromMapColor(mapColor: string | null | undefined): ColorCode | null {
	return (mapColor ?? null) as ColorCode | null
}

export const colorCodeConfig: Record<ColorCode, { bg: string; text: string; label: string }> = {
	green: { bg: 'bg-green-500', text: 'text-green-700', label: 'Compliant' },
	yellow: { bg: 'bg-yellow-400', text: 'text-yellow-700', label: 'Vigilance' },
	orange: { bg: 'bg-orange-500', text: 'text-orange-700', label: 'Reinforced vigilance' },
	red: { bg: 'bg-red-500', text: 'text-red-700', label: 'Non-compliant' },
	gray: { bg: 'bg-gray-400', text: 'text-gray-700', label: 'Unknown' }
}
