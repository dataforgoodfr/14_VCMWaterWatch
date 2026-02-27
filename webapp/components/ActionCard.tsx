import Link from 'next/link'

import { ArrowUpRight, LucideIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface ActionCardProps {
	icon: LucideIcon
	title: string
	description: string
	buttonText: string
	href: string
}

export const ActionCard = ({ icon: Icon, title, description, buttonText, href }: ActionCardProps) => {
	return (
		<div className='border-navy-800 bg-aqua-100 flex h-full flex-col rounded-r-2xl border-l-4 px-6 py-7'>
			<div className='mb-1 flex items-center gap-2'>
				<div className='relative flex items-center justify-center text-white'>
					<Icon className='absolute left-3 z-2 h-6 w-6' fill='#FFF' />
					<div className='bg-navy-800 absolute left-0 z-1 h-12 w-12 rounded-md text-white' />
					<div className='bg-navy-400 absolute top-[-20px] left-1.5 z-0 flex h-12 w-12 items-center justify-center rounded-md text-white' />
				</div>
				<p className='text-navy-800 pl-14 text-xl font-bold'>{title}</p>
			</div>
			<p className='text-md text-medium text-navy-800 pt-4 leading-relaxed'>{description}</p>
			<div className='pt-4'>
				<Button asChild variant='outlinePrimary' size='xl'>
					<Link href={href} className='text-[15px]'>
						{buttonText}
						<ArrowUpRight className='transition-transform group-hover:translate-x-1 group-hover:-translate-y-1' />
					</Link>
				</Button>
			</div>
		</div>
	)
}
