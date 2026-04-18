import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

export type ResourceType = 'guide' | 'report' | 'template' | 'factsheet' | 'video'

export interface ResourceCardProps {
	type: ResourceType
	title: string
	description: string
	actionLabel: string
	actionUrl: string
}

const TYPE_CONFIG: Record<ResourceType, { label: string; className: string }> = {
	guide: {
		label: 'Guide',
		className: 'bg-green-100 text-green-800 border-green-200'
	},
	report: {
		label: 'Report',
		className: 'bg-blue-100 text-blue-800 border-blue-200'
	},
	template: {
		label: 'Template',
		className: 'bg-orange-100 text-orange-800 border-orange-200'
	},
	factsheet: {
		label: 'Fact sheet',
		className: 'bg-teal-100 text-teal-800 border-teal-200'
	},
	video: {
		label: 'Video',
		className: 'bg-red-100 text-red-800 border-red-200'
	}
}

export function ResourceCard({ type, title, description, actionLabel, actionUrl }: ResourceCardProps) {
	const config = TYPE_CONFIG[type]

	return (
		<div className='border-navy-200 bg-navy-50 flex h-full flex-col rounded-xl border p-5'>
			{/* Tag badge */}
			<div className='mb-3'>
				<span className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${config.className}`}>
					{config.label}
				</span>
			</div>

			{/* Title */}
			<h3 className='text-navy-800 mb-2 font-[lexend] text-base font-semibold leading-snug'>{title}</h3>

			{/* Description */}
			<p className='text-navy-600 mb-4 flex-1 text-sm leading-relaxed'>{description}</p>

			{/* Action link */}
			<div className='mt-auto flex justify-end'>
				<Link
					href={actionUrl}
					className='text-navy-700 hover:text-navy-900 inline-flex items-center gap-1 text-sm font-medium underline-offset-2 hover:underline'
				>
					{actionLabel}
					<ArrowUpRight className='h-4 w-4' />
				</Link>
			</div>
		</div>
	)
}
