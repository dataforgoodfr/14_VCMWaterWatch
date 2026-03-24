'use client'

import { useState } from 'react'

import { templates } from '../data/templates'
import TemplateCard from './TemplateCard'
import TemplateModal from './TemplateModal'

export default function ActionGuideSidebar() {
	const [openTemplate, setOpenTemplate] = useState<number | null>(null)

	return (
		<div className='space-y-6'>
			{/* Important reminder */}
			<div className='border-navy-300 bg-navy-100 rounded-lg border p-4'>
				<h4 className='text-navy-900 text-sm font-semibold'>💡 Important reminder</h4>
				<p className='text-navy-800 mt-2 text-sm'>
					You are paying for a water distribution service. Access to safe, clean drinking water is a legal obligation
					for your water provider and municipality. You have every right to demand transparency and action.
				</p>
			</div>

			{/* Letter templates */}
			<div>
				<h4 className='text-navy-800 mb-3 text-sm font-semibold'>Letter templates</h4>
				<div className='grid grid-cols-1 gap-4 md:grid-cols-3'>
					{templates.map((tpl, i) => (
						<TemplateCard key={i} icon={tpl.icon} title={tpl.title} onClick={() => setOpenTemplate(i)} />
					))}
				</div>
			</div>

			{/* Notice */}
			<div className='border-aqua-400 bg-aqua-100 rounded-lg border p-4'>
				<p className='text-aqua-800 text-sm'>
					⚠️ <strong>Keep written records</strong> of all communications with your water provider, mayor, and elected
					officials.
				</p>
			</div>

			{/* Template modals */}
			{templates.map((tpl, i) => (
				<TemplateModal
					key={i}
					title={tpl.title}
					content={tpl.content}
					open={openTemplate === i}
					onOpenChange={open => setOpenTemplate(open ? i : null)}
				/>
			))}
		</div>
	)
}
