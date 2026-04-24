import { ArrowUpRight } from 'lucide-react'

export interface ResourceCardProps {
	typeKey: string | null
	title: string
	description: string
	actionUrl: string
	actionLabel?: string
}

const TYPE_CONFIG: Record<string, { label: string; className: string; actionLabel: string }> = {
	'institutional-report': {
		label: 'Institutional report',
		className: 'bg-blue-100 text-blue-800 border-blue-200',
		actionLabel: 'View report'
	},
	'research-paper': {
		label: 'Research paper',
		className: 'bg-teal-100 text-teal-800 border-teal-200',
		actionLabel: 'Read paper'
	},
	'news-item': {
		label: 'News',
		className: 'bg-orange-100 text-orange-800 border-orange-200',
		actionLabel: 'Read article'
	},
	guide: {
		label: 'Guide',
		className: 'bg-green-100 text-green-800 border-green-200',
		actionLabel: 'Read guide'
	},
	template: {
		label: 'Template',
		className: 'bg-orange-100 text-orange-800 border-orange-200',
		actionLabel: 'Download template'
	},
	factsheet: {
		label: 'Fact sheet',
		className: 'bg-teal-100 text-teal-800 border-teal-200',
		actionLabel: 'View fact sheet'
	},
	video: {
		label: 'Video',
		className: 'bg-red-100 text-red-800 border-red-200',
		actionLabel: 'Watch video'
	}
}

const DEFAULT_CONFIG = {
	className: 'bg-gray-100 text-gray-800 border-gray-200',
	actionLabel: 'Open resource'
}

function titleCase(slug: string): string {
	return slug.replace(/[-_]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function resolveType(key: string | null): {
	label: string
	className: string
	actionLabel: string
} {
	if (!key) {
		return { label: 'Resource', ...DEFAULT_CONFIG }
	}

	const hit = TYPE_CONFIG[key]

	if (hit) {
		return hit
	}

	return { label: titleCase(key), ...DEFAULT_CONFIG }
}

export default function ResourceCard({ typeKey, title, description, actionUrl, actionLabel }: ResourceCardProps) {
	const config = resolveType(typeKey)
	const linkText = actionLabel ?? config.actionLabel

	return (
		<div className='flex h-full flex-col rounded-sm bg-white p-10 shadow-xs'>
			{/* Tag badge */}
			<div className='mb-3'>
				<span className={`inline-block rounded border px-2.5 py-0.5 text-xs font-semibold ${config.className}`}>
					{config.label}
				</span>
			</div>

			{/* Title */}
			<h3 className='text-navy-800 mb-2 font-[lexend] text-base leading-snug font-semibold'>{title}</h3>

			{/* Description */}
			<p className='text-navy-600 mb-4 flex-1 text-sm leading-relaxed'>{description}</p>

			{/* Action link (external) */}
			<div className='mt-auto flex justify-end'>
				<a
					href={actionUrl}
					target='_blank'
					rel='noopener noreferrer'
					className='text-navy-700 hover:text-navy-900 inline-flex items-center gap-1 text-sm font-medium underline-offset-2 hover:underline'
				>
					{linkText}
					<ArrowUpRight className='h-4 w-4' />
				</a>
			</div>
		</div>
	)
}
