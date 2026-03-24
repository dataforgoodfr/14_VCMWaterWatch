import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ROUTES } from '@/routes/routes'

export const HeroSection = () => {
	return (
		<section className='relative flex h-[500px] w-full items-center overflow-hidden text-white'>
			{/* Background Image Placeholder */}
			<div
				className='absolute inset-0 -z-10 bg-cover bg-center'
				style={{
					backgroundImage: `linear-gradient(rgba(38, 71, 102, 0.54), rgba(38, 71, 102, 0.54)), url('/images/hero-bg.jpg')`
				}}
			/>

			<div className='relative z-10 container mx-auto px-4 md:px-8'>
				<div className='max-w-6xl'>
					<h1 className='bg-navy-400 mb-8 p-4 font-[lexend] leading-16 font-semibold uppercase md:text-5xl lg:text-[52px]'>
						Mapping CVM/VCM pollution risks across Europe
					</h1>
					<p className='mb-8 max-w-4xl text-lg text-blue-50 md:text-[24px]'>
						A collaborative platform to document and track vinyl chloride monomer (VCM) in European drinking water
						networks.
					</p>
					<Button
						asChild
						size='lg'
						className='bg-aqua-600 text-md hover:bg-aqua-700 rounded-xl px-8 py-6 font-semibold text-white'
					>
						<Link href={ROUTES.MAP}>
							VIEW THE MAP <ArrowUpRight className='size-6' />
						</Link>
					</Button>
				</div>
			</div>
		</section>
	)
}
