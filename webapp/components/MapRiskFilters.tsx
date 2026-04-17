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
		label: 'Confirmed',
		className:
			'border-1 border-[var(--risk-confirme-border)] bg-[var(--risk-confirme-bg)] text-[var(--risk-confirme-border)]',
		ringClass: 'ring-[var(--risk-confirme-border)]'
	},
	{
		id: 'probable',
		label: 'Probable',
		className:
			'border-1 border-[var(--risk-probable-border)] bg-[var(--risk-probable-bg)] text-[var(--risk-probable-border)]',
		ringClass: 'ring-[var(--risk-probable-border)]'
	},
	{
		id: 'absent',
		label: 'Absent',
		className:
			'border-1 border-[var(--risk-absent-border)] bg-[var(--risk-absent-bg)] text-[var(--risk-absent-border)]',
		ringClass: 'ring-[var(--risk-absent-border)]'
	},
	{
		id: 'inconnu',
		label: 'Unknown',
		className:
			'border-1 border-[var(--risk-inconnu-border)] bg-[var(--risk-inconnu-bg)] text-[var(--risk-inconnu-border)]',
		ringClass: 'ring-[var(--risk-inconnu-border)]'
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
							'focus-visible:ring-navy-400 rounded-3xl px-3 py-1.5 text-left text-sm font-medium outline-none select-none hover:brightness-[0.98] focus-visible:ring-2 focus-visible:ring-offset-2 active:scale-[0.98]',
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
