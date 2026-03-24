import Image from 'next/image'
import Link from 'next/link'

import { cn } from '@/lib/utils'
import { ROUTES } from '@/routes/routes'

interface MenuItem {
	links: {
		text: string
		url: string
	}[]
}

interface Footer2Props {
	logo?: {
		url: string
		src: string
		alt: string
		title: string
	}
	className?: string
	description?: string
	menuItems?: MenuItem[]
	copyright?: string
}

export const Footer = ({
	className,
	logo = {
		src: '/images/vcm-logo-color.svg',
		alt: 'VCM Water Watch logo',
		title: 'VCM Water Watch',
		url: ROUTES.HOME
	},
	description = 'water-watch@contact.com',
	menuItems = [
		{
			links: [
				{ text: 'Home', url: ROUTES.HOME },
				{ text: 'Interactive map', url: ROUTES.MAP },
				{ text: 'VCM pollution', url: ROUTES.VCM_POLLUTION_HISTORY },
				{ text: 'Country profiles', url: ROUTES.COUNTRY },
				{ text: 'Take action', url: ROUTES.ACT },
				{ text: 'Resources', url: ROUTES.RESOURCES },
				{ text: 'About', url: ROUTES.ABOUT }
			]
		}
	],
	copyright = '© Water Watch 2026 — All rights reserved'
}: Footer2Props) => {
	return (
		<section className={cn('bg-navy-900 flex w-full items-center justify-center py-8', className)}>
			<div className='container'>
				<footer className='text-center text-white'>
					<div className='flex flex-col items-center justify-between gap-8 lg:flex-row lg:items-center'>
						<div className='mb-8 lg:mb-0'>
							<div className='flex items-center justify-center gap-2'>
								<Link href={logo.url} className='flex items-center'>
									<Image
										src={logo.src}
										height={52}
										width={138}
										className='h-[44px] w-auto'
										alt={logo.alt}
										unoptimized
									/>
								</Link>
							</div>
							<p className='mt-4 font-bold'>{description}</p>
						</div>
						{menuItems.map((section, sectionIdx) => (
							<div key={sectionIdx}>
								<ul className='flex flex-col items-center gap-4 whitespace-nowrap lg:flex-row lg:justify-center'>
									{section.links.map((link, linkIdx) => (
										<Link key={linkIdx} href={link.url} className='hover:text-aqua-200 font-medium'>
											{link.text}
										</Link>
									))}
								</ul>
							</div>
						))}
					</div>
					<p className='mt-8 flex flex-col items-center justify-center gap-4 pt-8 text-sm font-medium md:flex-row'>
						{copyright}
					</p>
				</footer>
			</div>
		</section>
	)
}
