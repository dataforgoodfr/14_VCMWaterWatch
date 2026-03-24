'use client'
import * as React from 'react'

import { Card, CardContent } from '@/components/ui/card'
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel'
import type { CountryDetailRecord, CountryListRecord } from '@/types/apiTypes'

import { CountryProfileDetail } from './CountryProfileDetail'

function codeToFlagEmoji(code: string): string {
	if (code?.length !== 2) {
		return ''
	}

	return code
		.toUpperCase()
		.split('')
		.map(c => String.fromCodePoint(0x1f1e6 - 65 + c.charCodeAt(0)))
		.join('')
}

interface CountryCarouselProps {
	countries: CountryListRecord[]
}

export function CountryCarousel({ countries }: CountryCarouselProps) {
	const [selectedCode, setSelectedCode] = React.useState<string | null>(null)
	const [countryDetail, setCountryDetail] = React.useState<CountryDetailRecord | null>(null)
	const [detailLoading, setDetailLoading] = React.useState(false)
	const [detailError, setDetailError] = React.useState<string | null>(null)

	const loadCountry = React.useCallback(async (code: string) => {
		setSelectedCode(code)
		setDetailLoading(true)
		setDetailError(null)
		setCountryDetail(null)

		try {
			const res = await fetch(`/api/countries/${encodeURIComponent(code)}`)

			if (res.status === 404) {
				setDetailError('Pays introuvable.')
				return
			}

			if (!res.ok) {
				setDetailError('Impossible de charger les données du pays.')
				return
			}

			const data = (await res.json()) as { country: CountryDetailRecord | null }

			if (!data.country) {
				setDetailError('Pays introuvable.')
				return
			}

			setCountryDetail(data.country)
		} catch {
			setDetailError('Erreur réseau.')
		} finally {
			setDetailLoading(false)
		}
	}, [])

	const firstCountryCode = countries[0]?.fields.Code

	React.useEffect(() => {
		if (!firstCountryCode) {
			return
		}

		void loadCountry(firstCountryCode)
	}, [firstCountryCode, loadCountry])

	return (
		<>
			<Carousel className='w-full'>
				<CarouselContent className='-ml-1'>
					{countries.map(record => {
						const code = record.fields.Code
						const isSelected = selectedCode === code

						return (
							<CarouselItem key={code} className='basis-1/2 pl-1 md:basis-1/6 lg:basis-1/8'>
								<div className='p-1'>
									<Card
										className={`hover:bg-navy-50 hover:border-navy-300 cursor-pointer p-2 transition-colors select-none ${isSelected ? 'border-navy-800 bg-navy-100' : ''}`}
										onClick={() => void loadCountry(code)}
									>
										<CardContent className='flex items-center justify-center gap-2 p-2'>
											<span className='text-xl leading-none'>{codeToFlagEmoji(code)}</span>
											<span className='font-regular text-navy-800 text-[14px] whitespace-nowrap'>
												{record.fields.Name}
											</span>
										</CardContent>
									</Card>
								</div>
							</CarouselItem>
						)
					})}
				</CarouselContent>
				<CarouselPrevious />
				<CarouselNext />
			</Carousel>
			<CountryProfileDetail country={countryDetail} loading={detailLoading} error={detailError} />
		</>
	)
}
