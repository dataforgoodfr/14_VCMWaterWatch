import ResourceCard, { type ResourceCardProps } from './ResourceCard'
import CtaBanner from './CtaBanner'

interface MockResource extends ResourceCardProps {
	id: string
}

const MOCK_RESOURCES: MockResource[] = [
	{
		id: 'citizen-guide-water-quality',
		type: 'guide',
		title: 'Citizen Guide to Water Quality Testing',
		description:
			'A step-by-step guide for residents who want to collect water samples and understand laboratory results related to VCM contamination.',
		actionLabel: 'Read guide',
		actionUrl: '#'
	},
	{
		id: 'european-pvc-pipe-report-2023',
		type: 'report',
		title: 'European PVC Pipe Infrastructure Report 2023',
		description:
			'An overview of PVC water distribution pipes installed across Europe in the 1970s–80s, with maps of known contamination hotspots.',
		actionLabel: 'View report',
		actionUrl: '#'
	},
	{
		id: 'request-water-quality-data',
		type: 'guide',
		title: 'How to Request Water Quality Data from Authorities',
		description:
			'Know your rights. This guide explains the legal frameworks in EU countries that entitle citizens to access official water quality records.',
		actionLabel: 'Read guide',
		actionUrl: '#'
	},
	{
		id: 'letter-template-water-provider',
		type: 'template',
		title: 'Letter Template: Request to Water Provider',
		description:
			'A ready-to-use letter template to formally request VCM contamination data from your local water utility or municipal authority.',
		actionLabel: 'Download template',
		actionUrl: '#'
	},
	{
		id: 'vcm-health-risks-factsheet',
		type: 'factsheet',
		title: 'VCM Health Risks – Key Facts',
		description:
			'A concise fact sheet summarising the established health risks associated with vinyl chloride monomer (VCM) exposure through drinking water.',
		actionLabel: 'View fact sheet',
		actionUrl: '#'
	},
	{
		id: 'pvc-pipe-degradation-webinar',
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
					Guides, reports and templates to train and source your processes.
				</p>
			</div>

			{/* 3-column grid */}
			<div className='grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3'>
				{MOCK_RESOURCES.map(resource => (
					<ResourceCard key={resource.id} {...resource} />
				))}
			</div>

			{/* CTA banner */}
			<div className='mt-8'>
				<CtaBanner
					title='Do you have a resource to share?'
					subtitle='Feel free to write us.'
					buttonLabel='Contact us'
					href={`mailto:${process.env.CONTACT_EMAIL}`}
				/>
			</div>
		</div>
	)
}
