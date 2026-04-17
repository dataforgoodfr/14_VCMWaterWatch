export type ColorCode = 'green' | 'yellow' | 'orange' | 'red' | 'gray'

/**
 * Return the NocoDB `Map Color` value cast to `ColorCode`, or `null` if the
 * value is absent.  `Map Color` is the single source of truth for zone / country
 * colouring (see `pipelines/export/export_pmtiles.py` and
 * `webapp/lib/map/distributionZoneRisk.ts`).  No derivation from VCM / PVC
 * levels is performed here.
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
