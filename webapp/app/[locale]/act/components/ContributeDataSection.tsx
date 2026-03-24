'use client'

import { useState } from 'react'

import { templates } from '../data/templates'
import TemplateCard from './TemplateCard'
import TemplateModal from './TemplateModal'
import DataSubmissionForm from './DataSubmissionForm'

export default function ContributeDataSection() {
	const [openTemplate, setOpenTemplate] = useState<number | null>(null)

	return (
		<div>
			<h2 className='text-navy-800 mb-6 font-[lexend] text-2xl font-semibold'>Contribute data</h2>

			<div className='grid grid-cols-1 gap-8 md:grid-cols-2'>
				{/* 3a: Contact Decision-Makers */}
				<div className='space-y-4'>
					<h3 className='text-navy-800 text-lg font-semibold'>Contact decision-makers</h3>
					<p className='text-navy-800 text-sm'>
						Use these letter templates to contact your local officials and water providers. Customize them with your
						zone information and send them to demand transparency and action.
					</p>

					<div className='grid grid-cols-1 gap-3'>
						{templates.map((tpl, i) => (
							<TemplateCard key={i} icon={tpl.icon} title={tpl.title} onClick={() => setOpenTemplate(i)} />
						))}
					</div>

					<p className='text-navy-600 text-sm'>
						Found an error or received a response?{' '}
						<a href='#correction' className='text-aqua-700 underline underline-offset-4 hover:text-aqua-900'>
							Submit a correction
						</a>
					</p>
				</div>

				{/* 3b: Share Your Data */}
				<div className='space-y-4'>
					<h3 className='text-navy-800 text-lg font-semibold'>Share your data</h3>
					<p className='text-navy-800 text-sm'>
						Have water quality reports, PVC pipe information, or other relevant data? Share it with us to help improve
						the platform.
					</p>
					<DataSubmissionForm />
				</div>
			</div>

			{/* 3c: Correction/Feedback */}
			<div id='correction' className='border-aqua-400 bg-aqua-100 mt-8 rounded-lg border p-4'>
				<h4 className='text-aqua-900 text-sm font-semibold'>🔄 Found an error or received a response?</h4>
				<p className='text-aqua-800 mt-1 text-sm'>
					Submit a correction to help us keep data accurate and up-to-date.
				</p>
				<div className='mt-3'>
					<DataSubmissionForm defaultDataType='Correction' />
				</div>
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
