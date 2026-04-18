import Link from 'next/link'

import { ArrowUpRight, BookOpen, Database, FlaskConical, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'

const INFO_CARDS = [
	{
		icon: FlaskConical,
		title: 'Data collection methodology',
		body: 'Water quality data is gathered from official national databases, citizen-submitted reports, and partner research institutions. All entries are timestamped and linked to a source reference.'
	},
	{
		icon: Database,
		title: 'Risk level classification',
		body: 'Contamination risk is scored using the CVM Reference Table below, combining measured VCM concentration, pipe age, and infrastructure type to produce a four-tier risk level.'
	},
	{
		icon: BookOpen,
		title: 'Scientific references',
		body: 'Our thresholds and health guidance align with the WHO Guidelines for Drinking-water Quality and EU Directive 2020/2184 on water intended for human consumption.'
	},
	{
		icon: Users,
		title: 'Community contributions',
		body: 'Citizen-submitted data is reviewed by volunteer water specialists before it is published. Unverified contributions are flagged with a "pending review" status on the map.'
	}
]

// CVM Reference Table rows: [level, concentration, pipe age, infrastructure type]
const CVM_TABLE_ROWS = [
	{
		level: 'Low',
		levelColor: 'bg-green-100 text-green-800',
		concentration: '< 0.5 µg/L',
		pipeAge: '< 20 years',
		infrastructure: 'Modern PVC or non-PVC'
	},
	{
		level: 'Moderate',
		levelColor: 'bg-yellow-100 text-yellow-800',
		concentration: '0.5 – 2 µg/L',
		pipeAge: '20 – 35 years',
		infrastructure: 'Older PVC, maintained'
	},
	{
		level: 'High',
		levelColor: 'bg-orange-100 text-orange-800',
		concentration: '2 – 5 µg/L',
		pipeAge: '35 – 50 years',
		infrastructure: 'Ageing PVC 70s/80s network'
	},
	{
		level: 'Critical',
		levelColor: 'bg-red-100 text-red-800',
		concentration: '> 5 µg/L',
		pipeAge: '> 50 years',
		infrastructure: 'Pre-1975 PVC, degraded'
	}
]

// TODO: i18n — INFO_CARDS and CVM_TABLE_ROWS are hardcoded in English; extract for translation when i18n is added
export default function MethodologySection() {
	return (
		<div>
			{/* Section header */}
			<div className='mb-8'>
				<h2 className='text-navy-800 font-[lexend] text-2xl font-semibold'>Methodology</h2>
				<p className='text-navy-600 mt-2 max-w-2xl text-base'>
					How we collect, validate, and classify VCM contamination data — and how you can contribute.
				</p>
			</div>

			{/* 2×2 info cards */}
			<div className='mb-10 grid grid-cols-1 gap-5 sm:grid-cols-2'>
				{INFO_CARDS.map(card => {
					const Icon = card.icon

					return (
						<div key={card.title} className='border-navy-200 bg-navy-50 rounded-xl border p-5'>
							<div className='mb-3 flex items-center gap-3'>
								<div className='bg-navy-800 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white'>
									<Icon className='h-5 w-5' />
								</div>
								<h3 className='text-navy-800 font-[lexend] text-base font-semibold'>{card.title}</h3>
							</div>
							<p className='text-navy-600 text-sm leading-relaxed'>{card.body}</p>
						</div>
					)
				})}
			</div>

			{/* CVM Reference Table */}
			<div className='mb-10'>
				<h3 className='text-navy-800 mb-4 font-[lexend] text-lg font-semibold'>CVM Risk Level Reference Table</h3>
				<div className='border-navy-200 overflow-x-auto rounded-xl border'>
					<table className='w-full text-sm'>
						<thead>
							<tr className='bg-navy-800 text-left text-white'>
								<th scope='col' className='px-4 py-3 font-semibold'>Risk level</th>
								<th scope='col' className='px-4 py-3 font-semibold'>VCM concentration</th>
								<th scope='col' className='px-4 py-3 font-semibold'>Pipe age</th>
								<th scope='col' className='px-4 py-3 font-semibold'>Infrastructure type</th>
							</tr>
						</thead>
						<tbody>
							{CVM_TABLE_ROWS.map((row, i) => (
								<tr key={row.level} className={i % 2 === 0 ? 'bg-white' : 'bg-navy-50'}>
									<td className='px-4 py-3'>
										<span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${row.levelColor}`}>
											{row.level}
										</span>
									</td>
									<td className='text-navy-700 px-4 py-3 font-mono text-xs'>{row.concentration}</td>
									<td className='text-navy-700 px-4 py-3'>{row.pipeAge}</td>
									<td className='text-navy-700 px-4 py-3'>{row.infrastructure}</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
				<p className='text-navy-500 mt-2 text-xs'>
					* Thresholds are indicative and based on WHO/EU guidance. Site-specific factors may alter the final classification.
				</p>
			</div>

			{/* Who to contact CTA */}
			<div>
				<h3 className='text-navy-800 mb-4 font-[lexend] text-lg font-semibold'>Who to contact?</h3>
				<div className='bg-navy-900 flex flex-col items-start justify-between gap-4 rounded-xl px-6 py-6 sm:flex-row sm:items-center'>
					<div>
						<p className='font-[lexend] text-base font-semibold text-white'>Questions about the methodology?</p>
						<p className='mt-1 text-sm text-white/70'>
							Reach out to our scientific team or join the open-source project to propose improvements.
						</p>
					</div>
					<Button
						asChild
						variant='outlinePrimary'
						size='xl'
						className='shrink-0 border-white text-white hover:bg-white hover:text-navy-900'
					>
						<Link href='/act#involved' className='text-[15px]'>
							Get in touch
							<ArrowUpRight className='transition-transform group-hover:translate-x-1 group-hover:-translate-y-1' />
						</Link>
					</Button>
				</div>
			</div>
		</div>
	)
}
