import type { ComponentType } from 'react'

import Image from 'next/image'

import { FlaskConical, MapPin, Percent, TrainTrack, TriangleAlert } from 'lucide-react'

import { InfoCard } from '@/components/InfoCard'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Card, CardContent } from '@/components/ui/card'
import type { CountryDetailRecord } from '@/types/apiTypes'

const numberFmt = new Intl.NumberFormat('en-US')

function formatStatText(value: string | null): string {
	if (value == null || value.trim() === '') {
		return '—'
	}

	return value
}

function countryNumericOrLinkCount(value: unknown): number | null {
	if (value == null) {
		return null
	}

	if (typeof value === 'number' && Number.isFinite(value)) {
		return value
	}

	if (typeof value === 'string') {
		const parsed = Number.parseFloat(value)

		if (Number.isFinite(parsed)) {
			return parsed
		}
	}

	if (Array.isArray(value)) {
		return value.length
	}

	return null
}

function formatCountStat(value: unknown, nounPhrase: string): string {
	const n = countryNumericOrLinkCount(value)

	if (n == null || n <= 0) {
		return '—'
	}

	return `${numberFmt.format(n)} ${nounPhrase}`
}

interface StatCardProps {
	icon: ComponentType<{ className?: string }>
	title: string
	value: string
}

function StatCard({ icon: Icon, title, value }: StatCardProps) {
	return (
		<Card className='rounded-sm border-gray-300 bg-transparent py-4 shadow-none'>
			<CardContent className='flex flex-col items-center gap-3 text-center'>
				<div className='flex items-center justify-center gap-2'>
					<Icon className='size-5 shrink-0 text-gray-600' aria-hidden />
					<span className='text-[16px] leading-snug font-medium text-gray-600'>{title}</span>
				</div>
				<p className='text-navy-500 text-[28px] leading-tight font-semibold'>{value}</p>
			</CardContent>
		</Card>
	)
}

interface CountryProfileDetailProps {
	country: CountryDetailRecord | null
	loading: boolean
	error: string | null
}

export function CountryProfileDetail({ country, loading, error }: CountryProfileDetailProps) {
	if (loading) {
		return (
			<div className='text-navy-800 mt-10 font-[lexend] text-sm' role='status'>
				Loading...
			</div>
		)
	}

	if (error) {
		return (
			<div
				className='mt-10 rounded-lg border border-red-200 bg-red-50 px-4 py-3 font-[lexend] text-sm text-red-800'
				role='alert'
			>
				{error}
			</div>
		)
	}

	if (!country) {
		return null
	}

	const f = country.fields
	const imageSrc = f.Url ?? 'https://placehold.co/310x240.png'

	const pvcDisplay = formatStatText(f['PVC Level'] ?? null)
	const vcmDisplay = formatStatText(f['VCM Level'] ?? null)
	const distributionZonesCount = countryNumericOrLinkCount(f['Distribution Zones'])

	const analysesDisplay =
		distributionZonesCount != null && distributionZonesCount > 0 ? numberFmt.format(distributionZonesCount) : '—'

	const municipalitiesDisplay = formatCountStat(f.Municipalities, 'municipalities')

	return (
		<section className='mt-10 mb-8 flex flex-col gap-8' aria-live='polite'>
			<InfoCard bgClassName='bg-navy-50'>
				<div className='text-navy-800 flex flex-col gap-4'>
					<div className='flex items-center gap-1'>
						<MapPin />
						<h2 className='font-[lexend] text-[24px] font-medium'>{f.Name} — Data overview</h2>
					</div>
					<dl className='flex flex-col items-start gap-10 md:flex-row md:items-start'>
						<div className='w-full shrink-0 md:max-w-[48%] md:basis-[48%]'>
							<Image
								src={imageSrc}
								alt={f.Name ? `Illustration — ${f.Name}` : 'Country illustration'}
								width={640}
								height={300}
								className='h-[300px] w-full rounded-md object-cover'
							/>
						</div>
						<div className='flex w-full min-w-0 flex-1 flex-col items-start justify-center md:w-auto'>
							<div className='grid w-full grid-cols-1 gap-4 md:grid-cols-2'>
								<StatCard icon={TrainTrack} title='VCM impacted network' value={pvcDisplay} />
								<StatCard icon={Percent} title='VCM exposure rate' value={vcmDisplay} />
								<StatCard icon={FlaskConical} title='Number of VCM analyses' value={analysesDisplay} />
								<StatCard icon={MapPin} title='Identified risk zones' value={municipalitiesDisplay} />
							</div>
						</div>
					</dl>

					<Accordion type='single' collapsible className='w-full'>
						<AccordionItem value='more-details' className='border-navy-200 border-b-0'>
							<AccordionTrigger className='text-navy-800 py-3 font-[lexend] text-[19px] font-medium hover:no-underline'>
								More details
							</AccordionTrigger>
							<AccordionContent className='pb-2'>
								<ul className='font-regular list-disc pl-5 text-[17px] text-gray-600'>
									<li>...</li>
								</ul>
							</AccordionContent>
						</AccordionItem>
					</Accordion>
				</div>
			</InfoCard>

			<InfoCard bgClassName='bg-navy-50'>
				<div className='text-navy-800 flex flex-col gap-4'>
					<div className='flex items-center gap-1'>
						<TriangleAlert />
						<h2 className='font-[lexend] text-[24px] font-medium'>Missing data</h2>
					</div>

					<div className='flex w-full flex-col items-start gap-4'>
						{/* TODO: refactor when data clarified */}
						{['Full PVC network inventory', 'Regular VCM testing', 'Replacement plans'].map(title => (
							<div key={title} className='flex w-full flex-col border-l-[6px] border-gray-300 bg-white px-4 py-2'>
								<dt className='font-regular text-[20px]'>{title}</dt>
								<dd className='text-[16px] text-gray-600'>...</dd>
							</div>
						))}
					</div>
				</div>
			</InfoCard>
		</section>
	)
}
