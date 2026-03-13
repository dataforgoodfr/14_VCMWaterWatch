'use client'
import * as React from 'react'

import { Card, CardContent } from '@/components/ui/card'
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel'
import type { CountryListRecord } from '@/types/apiTypes'

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

	return (
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
									onClick={() => setSelectedCode(code)}
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
	)
}
