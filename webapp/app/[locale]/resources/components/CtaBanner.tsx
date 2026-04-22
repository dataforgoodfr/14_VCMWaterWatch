import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface CtaBannerProps {
	title: string
	subtitle: string
	buttonLabel: string
	href: string
}

export default function CtaBanner({ title, subtitle, buttonLabel, href }: CtaBannerProps) {
	return (
		<div className='bg-aqua-100 flex flex-col items-start justify-between gap-1 rounded-sm px-6 py-6 sm:flex-row sm:items-center'>
			<div>
				<p className='text-navy-800 font-[lexend] text-[19px] font-bold'>{title}</p>
				<p className='text-md mt-1 text-gray-500'>{subtitle}</p>
			</div>
			<Button
				asChild
				variant='default'
				size='xl'
				className='shrink-0 rounded-sm border-white bg-green-700 text-white hover:bg-green-600'
			>
				<Link href={href} className='text-[15px]'>
					{buttonLabel}
					<ArrowUpRight className='transition-transform group-hover:translate-x-1 group-hover:-translate-y-1' />
				</Link>
			</Button>
		</div>
	)
}
