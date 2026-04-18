import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

import ResourceCard, { type ResourceCardProps } from './ResourceCard'

const MOCK_RESOURCES: ResourceCardProps[] = [
	{
		type: 'guide',
		title: 'Citizen Guide to Water Quality Testing',
		description:
			'A step-by-step guide for residents who want to collect water samples and understand laboratory results related to VCM contamination.',
		actionLabel: 'Read guide',
		actionUrl: '#'
	},
	{
		type: 'report',
		title: 'European PVC Pipe Infrastructure Report 2023',
		description:
			'An overview of PVC water distribution pipes installed across Europe in the 1970s–80s, with maps of known contamination hotspots.',
		actionLabel: 'View report',
		actionUrl: '#'
	},
	{
		type: 'guide',
		title: 'How to Request Water Quality Data from Authorities',
		description:
			'Know your rights. This guide explains the legal frameworks in EU countries that entitle citizens to access official water quality records.',
		actionLabel: 'Read guide',
		actionUrl: '#'
	},
	{
		type: 'template',
		title: 'Letter Template: Request to Water Provider',
		description:
			'A ready-to-use letter template to formally request VCM contamination data from your local water utility or municipal authority.',
		actionLabel: 'Download template',
		actionUrl: '#'
	},
	{
		type: 'factsheet',
		title: 'VCM Health Risks – Key Facts',
		description:
			'A concise fact sheet summarising the established health risks associated with vinyl chloride monomer (VCM) exposure through drinking water.',
		actionLabel: 'View fact sheet',
		actionUrl: '#'
	},
	{
		type: 'video',
		title: 'Understanding PVC Pipe Degradation (Webinar)',
		description:
			'A recorded webinar by water chemistry experts explaining how PVC pipes degrade over time and how VCM can leach into drinking water.',
		actionLabel: 'Watch video',
		actionUrl: '#'
	}
]

// TODO: i18n — MOCK_RESOURCES is hardcoded in English; extract for translation when i18n is added
export default function ResourcesSection() {
	return (
		<div>
			{/* Section header */}
			<div className='mb-8'>
				<h2 className='text-navy-800 font-[lexend] text-2xl font-semibold'>Resources</h2>
				<p className='text-navy-600 mt-2 max-w-2xl text-base'>
					Guides, reports, templates, and other materials to help citizens, researchers, and advocates understand and act on
					VCM water contamination.
				</p>
			</div>

			{/* 3-column grid */}
			<div className='grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3'>
				{MOCK_RESOURCES.map(resource => (
					<ResourceCard key={resource.title} {...resource} />
				))}
			</div>

			{/* CTA banner */}
			<div className='bg-navy-900 mt-10 flex flex-col items-start justify-between gap-4 rounded-xl px-6 py-6 sm:flex-row sm:items-center'>
				<div>
					<p className='font-[lexend] text-lg font-semibold text-white'>Have a resource to share?</p>
					<p className='mt-1 text-sm text-white/70'>
						Help the community grow by submitting a guide, report, or any relevant material.
					</p>
				</div>
				<Button asChild variant='outlinePrimary' size='xl' className='shrink-0 border-white text-white hover:bg-white hover:text-navy-900'>
					<Link href='/act#involved' className='text-[15px]'>
						Contact us
						<ArrowUpRight className='transition-transform group-hover:translate-x-1 group-hover:-translate-y-1' />
					</Link>
				</Button>
			</div>
		</div>
	)
}
