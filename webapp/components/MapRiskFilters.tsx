'use client'

import { riskTierConfig, type MapRiskTier } from '@/lib/colorCode'
import { cn } from '@/lib/utils'

const TIER_ORDER: MapRiskTier[] = ['confirme', 'probable', 'absent', 'inconnu']

const FILTERS = TIER_ORDER.map(id => {
	const t = riskTierConfig[id]

	return {
		id,
		label: t.label,
		style: {
			borderColor: t.border,
			backgroundColor: t.bg,
			color: t.border
		},
		ringColor: t.border
	}
})

interface MapRiskFiltersProps {
	active: MapRiskTier | null
	onChange: (tier: MapRiskTier | null) => void
}

export function MapRiskFilters({ active, onChange }: MapRiskFiltersProps) {
	return (
		<div className='flex flex-wrap gap-2'>
			{FILTERS.map(f => {
				const isOn = active === f.id

				return (
					<button
						key={f.id}
						type='button'
						aria-pressed={isOn}
						onClick={() => onChange(isOn ? null : f.id)}
						className={cn(
							'focus-visible:ring-navy-400 rounded-3xl border px-3 py-1.5 text-left text-sm font-medium outline-none select-none hover:brightness-[0.98] focus-visible:ring-2 focus-visible:ring-offset-2 active:scale-[0.98]',
							isOn && 'font-semibold'
						)}
						style={{
							borderColor: f.style.borderColor,
							backgroundColor: f.style.backgroundColor,
							color: f.style.color,
							...(isOn ? { boxShadow: `0 0 0 2px #fff, 0 0 0 4px ${f.ringColor}` } : {})
						}}
					>
						{f.label}
					</button>
				)
			})}
		</div>
	)
}
