import Image from 'next/image'

import { MapPin, TriangleAlert } from 'lucide-react'

import { InfoCard } from '@/components/InfoCard'
import type { CountryDetailRecord } from '@/types/apiTypes'
import { Separator } from '@/components/ui/separator'

function formatLinkField(value: unknown): string {
	if (value === null || value === undefined) {
		return '—'
	}

	if (typeof value === 'number') {
		return String(value)
	}

	if (Array.isArray(value)) {
		return `${value.length} item(s)`
	}

	if (typeof value === 'object') {
		return JSON.stringify(value)
	}

	if (typeof value === 'string' || typeof value === 'boolean') {
		return String(value)
	}

	return '—'
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

	return (
		<section className='mt-10 mb-8 flex flex-col gap-8' aria-live='polite'>
			<InfoCard bgClassName='bg-navy-50'>
				<div className='text-navy-800 flex flex-col gap-4'>
					<div className='flex items-center gap-1'>
						<MapPin />
						<h2 className='font-[lexend] text-[24px] font-medium'>{f.Name} — Data overview</h2>
					</div>
					<dl className='flex flex-col items-start gap-10 md:flex-row'>
						<Image
							src={imageSrc}
							alt={f.Name ? `Illustration — ${f.Name}` : 'Country illustration'}
							width={310}
							height={240}
							className='h-auto max-w-[min(100%,600px)] shrink-0 rounded-md object-cover'
						/>
						<div className='flex w-full flex-col items-start justify-center'>
							<div className='flex w-full flex-col items-start justify-around md:flex-row md:items-center'>
								<div className='flex flex-col items-start md:items-center'>
									<dt className='text-[16px] font-medium'>Total PVC network</dt>
									<dd className='text-navy-500 text-[23px] font-semibold'>...</dd>
								</div>
								<div className='flex flex-col items-start md:items-center'>
									<dt className='text-[16px] font-medium'>Share of network</dt>
									<dd className='text-navy-500 text-[23px] font-semibold'>...</dd>
								</div>
								<div className='flex flex-col items-start md:items-center'>
									<dt className='text-[16px] font-medium'>Identified risk areas</dt>
									<dd className='text-navy-500 text-[23px] font-semibold'>
										{formatLinkField(f.Municipalities) ? `${formatLinkField(f.Municipalities)} municipalities` : '—'}
									</dd>
								</div>
							</div>

							<Separator className='my-6 w-full self-stretch bg-gray-300' />

							<p className='text-[17px] font-semibold'>Applicable legislation</p>
							<ul className='font-regular list-disc pl-4 text-[17px] text-gray-600'>
								<li>...</li>
								<li>...</li>
								<li>...</li>
							</ul>
						</div>
					</dl>
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
