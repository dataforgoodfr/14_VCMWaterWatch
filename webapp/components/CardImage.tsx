import Image from 'next/image'

import { FileArchive } from 'lucide-react'

import { Card, CardDescription, CardTitle } from '@/components/ui/card'

interface CardImagePropsType {
	img: { url: string; alt: string }
	title: string
	description: string
}

export function CardImage({ img, title, description }: CardImagePropsType) {
	return (
		<Card className='relative mx-auto w-full border-none pt-0 shadow-none'>
			<div className='absolute inset-0 z-30 aspect-video' />
			<Image
				src={img.url}
				alt={img.alt}
				width={380}
				height={180}
				className='relative z-20 aspect-video w-full rounded-md object-cover'
			/>
			<div>
				<div className='flex gap-1'>
					<FileArchive className='text-navy-800 mt-1' />
					<CardTitle className='text-navy-800 font-[lexend] text-[20px] font-medium'>{title}</CardTitle>
				</div>
				<CardDescription className='text-[20px] text-gray-600'>{description}</CardDescription>
			</div>
		</Card>
	)
}
