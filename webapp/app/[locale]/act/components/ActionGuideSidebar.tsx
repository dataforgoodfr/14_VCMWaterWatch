'use client'

import { useState } from 'react'

import TemplateModal from './TemplateModal'

const templates = [
	{
		icon: '🏛️',
		title: 'Letter to the mayor',
		content: `Dear Mayor,

I am writing to you as a resident of [YOUR MUNICIPALITY] to express my concern about the quality of drinking water distributed in our area.

Recent analyses have shown that the levels of vinyl chloride monomer (VCM) and/or polyvinyl chloride (PVC) particles in our water supply exceed [or approach] the regulatory limits set by [RELEVANT REGULATION].

As the authority responsible for the public water distribution service, I respectfully request:

1. Full transparency on the latest water quality analyses for our distribution zone
2. Information about the materials (notably PVC pipes) used in our water distribution network
3. A concrete action plan and timeline for replacing any non-compliant infrastructure

I remind you that access to safe drinking water is a fundamental right, and that the municipality has a legal obligation to ensure the quality of distributed water.

I look forward to your written response within 15 days.

Yours sincerely,
[YOUR NAME]
[YOUR ADDRESS]`
	},
	{
		icon: '🏢',
		title: 'Email to water company',
		content: `Dear Sir/Madam,

As a customer and resident served by your water distribution network in [DISTRIBUTION ZONE], I am writing to request information about the quality of the water supplied to my home.

I have become aware of concerns regarding vinyl chloride monomer (VCM) contamination in water distributed through PVC pipes. I would like to request:

1. The most recent water quality analysis results for my distribution zone
2. Information about the pipe materials used in my area
3. Details about any planned pipe replacement or remediation programs
4. Your company's monitoring protocol for VCM levels

As a paying customer, I expect full transparency regarding the quality of the service I pay for. Safe drinking water is not optional — it is a legal obligation.

Please provide a written response within 15 business days.

Best regards,
[YOUR NAME]
[YOUR CUSTOMER REFERENCE]
[YOUR ADDRESS]`
	},
	{
		icon: '🏛️',
		title: 'Letter to your MP',
		content: `Dear [MP NAME],

I am writing to you as your constituent to raise a serious public health concern regarding drinking water quality in [YOUR AREA].

Water analyses have revealed that the distribution zone serving our community shows [elevated/non-compliant] levels of vinyl chloride monomer (VCM), a substance classified as carcinogenic.

This contamination is linked to aging PVC pipes in the water distribution network. Despite the known health risks, replacement of these pipes has been slow and insufficient.

I urge you to:

1. Raise this issue in Parliament and demand a national audit of PVC pipe infrastructure
2. Push for increased funding for pipe replacement programs
3. Advocate for stricter monitoring and public reporting of VCM levels
4. Ensure that affected communities receive timely information and support

The health of our community depends on decisive action. I look forward to hearing about the steps you will take.

Yours sincerely,
[YOUR NAME]
[YOUR ADDRESS]
[YOUR CONSTITUENCY]`
	}
]

export default function ActionGuideSidebar() {
	const [openTemplate, setOpenTemplate] = useState<number | null>(null)

	return (
		<div className='space-y-6 lg:sticky lg:top-24'>
			{/* Important reminder */}
			<div className='rounded-lg border border-blue-200 bg-blue-50 p-4'>
				<h4 className='text-sm font-semibold text-blue-900'>💡 Important reminder</h4>
				<p className='mt-2 text-sm text-blue-800'>
					You are paying for a water distribution service. Access to safe, clean drinking water is a legal obligation
					for your water provider and municipality. You have every right to demand transparency and action.
				</p>
			</div>

			{/* Letter templates */}
			<div className='space-y-3'>
				<h4 className='text-sm font-semibold text-gray-700'>Letter templates</h4>
				{templates.map((tpl, i) => (
					<button
						key={i}
						onClick={() => setOpenTemplate(i)}
						className='flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-gray-300 hover:shadow'
					>
						<span className='text-xl'>{tpl.icon}</span>
						<span className='text-sm font-medium text-gray-800'>{tpl.title}</span>
					</button>
				))}
			</div>

			{/* Notice */}
			<div className='rounded-lg border border-amber-200 bg-amber-50 p-4'>
				<p className='text-sm text-amber-800'>
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
