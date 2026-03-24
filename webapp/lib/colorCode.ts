export type ColorCode = 'green' | 'yellow' | 'orange' | 'red'

/**
 * Derive a color code from VCM/PVC level values.
 * Placeholder logic — update when thresholds are confirmed with data team.
 */
export function deriveColorCode(vcmLevel: string | null, pvcLevel: string | null): ColorCode {
	// Use the worse of the two levels
	const levels = [vcmLevel, pvcLevel].filter(Boolean)

	if (levels.some(l => l === 'Non conforme' || l === 'Non-conforme')) {
		return 'red'
	}

	if (levels.some(l => l === 'Vigilance renforcée')) {
		return 'orange'
	}

	if (levels.some(l => l === 'Vigilance')) {
		return 'yellow'
	}

	return 'green'
}

export const colorCodeConfig: Record<ColorCode, { bg: string; text: string; label: string }> = {
	green: { bg: 'bg-green-500', text: 'text-green-700', label: 'Compliant' },
	yellow: { bg: 'bg-yellow-400', text: 'text-yellow-700', label: 'Vigilance' },
	orange: { bg: 'bg-orange-500', text: 'text-orange-700', label: 'Reinforced vigilance' },
	red: { bg: 'bg-red-500', text: 'text-red-700', label: 'Non-compliant' }
}
