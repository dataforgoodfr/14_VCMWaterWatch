'use client'

import { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { colorCodeFromMapColor, colorCodeConfig } from '@/lib/colorCode'

interface ZoneResultPanelProps {
	zone: DistributionZoneDetailRecord | null
	loading: boolean
}

export default function ZoneResultPanel({ zone, loading }: ZoneResultPanelProps) {
	if (loading) {
		return (
			<div className='border-navy-800 bg-navy-50 mt-6 animate-pulse rounded-r-2xl border-l-4 p-6 shadow-sm'>
				<div className='bg-navy-200 h-6 w-1/3 rounded' />
				<div className='bg-navy-200 mt-3 h-4 w-1/4 rounded' />
				<div className='mt-6 space-y-3'>
					{Array.from({ length: 4 }).map((_, i) => (
						<div key={i} className='bg-navy-100 h-4 w-2/3 rounded' />
					))}
				</div>
			</div>
		)
	}

	if (!zone) {
		return null
	}

	const { fields } = zone
	const colorCode = colorCodeFromMapColor(fields['Map Color'])
	const config = colorCode ? colorCodeConfig[colorCode] : null

	return (
		<div className='border-navy-800 bg-navy-50 mt-6 rounded-r-2xl border-l-4 p-6 shadow-sm'>
			<div className='flex items-start justify-between'>
				<div>
					<h3 className='text-navy-800 text-lg font-semibold'>{fields.Name}</h3>
					{fields.Country && <p className='text-navy-600 text-sm'>{fields.Country.fields.Name}</p>}
				</div>
				{config && (
					<span
						className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${config.bg} text-white`}
					>
						{config.label}
					</span>
				)}
			</div>

			<div className='border-navy-200 mt-4 border-t pt-4'>
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
			<dt className='text-navy-600 w-28 shrink-0 font-medium'>{label}</dt>
			<dd className='text-navy-800'>{value ?? '—'}</dd>
		</div>
	)
}
