'use client'

import { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { deriveColorCode, colorCodeConfig } from '@/lib/colorCode'

interface ZoneResultPanelProps {
	zone: DistributionZoneDetailRecord | null
	loading: boolean
}

export default function ZoneResultPanel({ zone, loading }: ZoneResultPanelProps) {
	if (loading) {
		return (
			<div className='mt-6 animate-pulse rounded-lg border border-gray-200 bg-white p-6 shadow-sm'>
				<div className='h-6 w-1/3 rounded bg-gray-200' />
				<div className='mt-3 h-4 w-1/4 rounded bg-gray-200' />
				<div className='mt-6 space-y-3'>
					{Array.from({ length: 4 }).map((_, i) => (
						<div key={i} className='h-4 w-2/3 rounded bg-gray-100' />
					))}
				</div>
			</div>
		)
	}

	if (!zone) {
		return null
	}

	const { fields } = zone
	const colorCode = deriveColorCode(fields['VCM Level'], fields['PVC Level'])
	const config = colorCodeConfig[colorCode]

	return (
		<div className='mt-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm'>
			<div className='flex items-start justify-between'>
				<div>
					<h3 className='text-lg font-semibold text-gray-900'>{fields.Name}</h3>
					{fields.Country && <p className='text-sm text-gray-500'>{fields.Country.fields.Name}</p>}
				</div>
				<span
					className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${config.bg} text-white`}
				>
					{config.label}
				</span>
			</div>

			<div className='mt-4 border-t border-gray-100 pt-4'>
				<dl className='space-y-2 text-sm'>
					<Row label='Company' value={fields.ActorName?.join(', ')} />
					<Row label='Contact' value={fields.ActorEmail?.join(', ')} />
					<Row label='PVC Level' value={fields['PVC Level']} />
					<Row label='VCM Level' value={fields['VCM Level']} />
					<Row label='Municipalities' value={fields.MunicipalityNames?.join(', ')} />
				</dl>
			</div>
		</div>
	)
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
	return (
		<div className='flex gap-4'>
			<dt className='w-28 shrink-0 font-medium text-gray-500'>{label}</dt>
			<dd className='text-gray-900'>{value ?? '—'}</dd>
		</div>
	)
}
