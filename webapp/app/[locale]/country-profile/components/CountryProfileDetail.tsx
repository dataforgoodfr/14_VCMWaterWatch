import type { ComponentType } from 'react'

import Image from 'next/image'

import { FlaskConical, HelpCircle, MapPin, Percent, TrainTrack, TriangleAlert } from 'lucide-react'

import { InfoCard } from '@/components/InfoCard'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Card, CardContent } from '@/components/ui/card'
import type { CountryDataRecord, CountryDetailRecord } from '@/types/apiTypes'

/** Icon lookup by Order (1-indexed) */
const STAT_ICONS: Record<number, ComponentType<{ className?: string }>> = {
	1: TrainTrack,
	2: Percent,
	3: FlaskConical,
	4: MapPin
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
	data: CountryDataRecord[]
	mirroredImageUrl?: string | null
	loading: boolean
	error: string | null
}

export function CountryProfileDetail({ country, data, mirroredImageUrl, loading, error }: CountryProfileDetailProps) {
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

	const attachment = f.Image?.[0]

	// Prefer the mirrored stable URL resolved server-side (passed as prop from
	// the API route which has fs access); fall back to the NocoDB signed URL.
	const imageSrc =
		mirroredImageUrl ??
		attachment?.signedUrl ??
		attachment?.thumbnails?.card_cover?.signedUrl ??
		'https://placehold.co/310x240.png'

	// Partition CountryData by type (already ordered by Order from server)
	const stats = data.filter(r => r.fields.Type === 'stat')

	const legislationItems = data.filter(r => r.fields.Type === 'legislation')

	const missingDataItems = data.filter(r => r.fields.Type === 'missing_data')

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
								priority
								className='h-[300px] w-full rounded-md object-cover'
							/>
						</div>
						<div className='flex w-full min-w-0 flex-1 flex-col items-start justify-center md:w-auto'>
							<div className='grid w-full grid-cols-1 gap-4 md:grid-cols-2'>
								{stats.map(row => {
									const Icon = STAT_ICONS[row.fields.Order]

									if (!Icon && process.env.NODE_ENV !== 'production') {
										console.warn(`CountryData stat row has unexpected Order=${row.fields.Order} (id=${row.id})`)
									}

									const title = row.fields.Title
									const value = row.fields.Content

									if (!title || !value) {
										return null
									}

									return <StatCard key={row.id} icon={Icon ?? HelpCircle} title={title} value={value} />
								})}
							</div>
						</div>
					</dl>

					{legislationItems.length > 0 && (
						<Accordion type='single' collapsible className='w-full'>
							<AccordionItem value='more-details' className='border-navy-200 border-b-0'>
								<AccordionTrigger className='text-navy-800 py-3 font-[lexend] text-[19px] font-medium hover:no-underline'>
									More details
								</AccordionTrigger>
								<AccordionContent className='pb-2'>
									<ul className='font-regular list-disc pl-5 text-[17px] text-gray-600'>
										{legislationItems.map(row => (
											<li key={row.id}>{row.fields.Content}</li>
										))}
									</ul>
								</AccordionContent>
							</AccordionItem>
						</Accordion>
					)}
				</div>
			</InfoCard>

			{missingDataItems.length > 0 && (
				<InfoCard bgClassName='bg-navy-50'>
					<div className='text-navy-800 flex flex-col gap-4'>
						<div className='flex items-center gap-1'>
							<TriangleAlert />
							<h2 className='font-[lexend] text-[24px] font-medium'>Missing data</h2>
						</div>

						<div className='flex w-full flex-col items-start gap-4'>
							{missingDataItems.map(row => (
								<div key={row.id} className='flex w-full flex-col border-l-[6px] border-gray-300 bg-white px-4 py-2'>
									<p className='font-regular text-[17px] text-gray-600'>{row.fields.Content}</p>
								</div>
							))}
						</div>
					</div>
				</InfoCard>
			)}
		</section>
	)
}
