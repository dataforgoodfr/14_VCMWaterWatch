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
		<div className='bg-navy-900 flex flex-col items-start justify-between gap-4 rounded-xl px-6 py-6 sm:flex-row sm:items-center'>
			<div>
				<p className='font-[lexend] text-base font-semibold text-white'>{title}</p>
				<p className='mt-1 text-sm text-white/70'>{subtitle}</p>
			</div>
			<Button
				asChild
				variant='outlinePrimary'
				size='xl'
				className='shrink-0 border-white text-white hover:bg-white hover:text-navy-900'
			>
				<Link href={href} className='text-[15px]'>
					{buttonLabel}
					<ArrowUpRight className='transition-transform group-hover:translate-x-1 group-hover:-translate-y-1' />
				</Link>
			</Button>
		</div>
	)
}
