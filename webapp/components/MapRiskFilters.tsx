'use client'

import type { MapRiskTier } from '@/lib/map/distributionZoneRisk'
import { cn } from '@/lib/utils'

const FILTERS: {
	id: MapRiskTier
	label: string
	className: string
	ringClass: string
}[] = [
	{
		id: 'confirme',
		label: 'Confirmé',
		className: 'border-risk-confirme-border bg-risk-confirme-bg text-risk-confirme-border',
		ringClass: 'ring-risk-confirme-border'
	},
	{
		id: 'probable',
		label: 'Probable',
		className: 'border-risk-probable-border bg-risk-probable-bg text-risk-probable-border',
		ringClass: 'ring-risk-probable-border'
	},
	{
		id: 'absent',
		label: 'Absent',
		className: 'border-risk-absent-border bg-risk-absent-bg text-risk-absent-border',
		ringClass: 'ring-risk-absent-border'
	},
	{
		id: 'inconnu',
		label: 'Inconnu',
		className: 'border-risk-inconnu-border bg-risk-inconnu-bg text-risk-inconnu-border',
		ringClass: 'ring-risk-inconnu-border'
	}
]

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
							'focus-visible:ring-navy-400 rounded-3xl border-1 px-3 py-1.5 text-left text-sm font-medium shadow-sm transition-[box-shadow,transform] outline-none select-none hover:brightness-[0.98] focus-visible:ring-2 focus-visible:ring-offset-2 active:scale-[0.98]',
							f.className,
							isOn && cn('font-semibold ring-2 ring-offset-2', f.ringClass)
						)}
					>
						{f.label}
					</button>
				)
			})}
		</div>
	)
}
