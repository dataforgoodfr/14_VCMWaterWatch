'use client'

import { useMemo, useState } from 'react'

import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { ChevronRightIcon, Menu } from 'lucide-react'

import { isActivePath, normalizePath } from '@/lib/path'
import { cn } from '@/lib/utils'

import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { ROUTES } from '@/routes/routes'
import LanguageDropDown from './LanguageDropDown'

interface MenuItem {
	title: string
	url: string
}

interface NavbarProps {
	className?: string
	logo?: {
		url: string
		src: string
		alt: string
		title: string
		className?: string
	}
	menu?: MenuItem[]
}

const Navbar = ({
	logo = {
		url: ROUTES.HOME,
		src: '/images/vcm-logo-white.svg',
		alt: 'VCM Water Watch Logo',
		title: 'VCM Water Watch'
	},
	menu = [
		{ title: 'Accueil', url: ROUTES.HOME },
		{
			title: 'Carte interactive',
			url: '/map'
		},
		{
			title: 'La pollution au CVM',
			url: ROUTES.VCM_POLLUTION_HISTORY
		},
		{
			title: 'Fiches pays',
			url: ROUTES.COUNTRY
		},
		{ title: 'Agir', url: ROUTES.ACT },
		{ title: 'Ressources', url: ROUTES.RESOURCES },
		{ title: 'À propos', url: ROUTES.ABOUT }
	],
	className
}: NavbarProps) => {
	const pathname = usePathname()
	const normalizedPathname = useMemo(() => normalizePath(pathname ?? ROUTES.HOME), [pathname])
	const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

	return (
		<section className={cn('border-navy-600 bg-navy-700 flex justify-center border-b px-3', className)}>
			<div className='container max-w-[1680px]'>
				<nav className='hidden h-[84px] items-center justify-between lg:flex'>
					<div className='flex items-center gap-8'>
						<Link href={logo.url} className='flex items-center'>
							<Image
								src={logo.src}
								height={52}
								width={138}
								className='h-[44px] w-auto'
								alt={logo.alt}
								priority
								unoptimized
							/>
						</Link>
						<div className='flex items-center gap-1'>
							{menu.map(item => (
								<Link
									key={item.title}
									href={item.url}
									className={cn(
										'hover:text-aqua-200 inline-flex h-[46px] items-center border-b-[2px] border-transparent px-3 text-[18px] font-medium text-nowrap text-white/95 transition-colors',
										isActivePath(normalizedPathname, normalizePath(item.url)) && 'border-aqua-400 text-white'
									)}
								>
									{item.title}
								</Link>
							))}
						</div>
					</div>
					<LanguageDropDown className='hover:text-aqua-200 text-[20px] text-white/95' />
				</nav>

				<div className='block lg:hidden'>
					<div className='flex h-[64px] items-center justify-between'>
						<Link href={logo.url} className='flex items-center'>
							<Image
								src={logo.src}
								height={52}
								width={138}
								className='h-[38px] w-auto'
								alt={logo.alt}
								priority
								unoptimized
							/>
						</Link>
						<Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
							<SheetTrigger asChild>
								<Button variant='ghost' size='icon' className='text-white hover:bg-white/10 hover:text-white'>
									<Menu className='size-4' />
								</Button>
							</SheetTrigger>
							<SheetContent side='top' className='bg-navy-500 p-5 text-white'>
								<SheetHeader>
									<SheetTitle>
										<Link href={logo.url} className='flex items-center' onClick={() => setIsMobileMenuOpen(false)}>
											<Image
												src={logo.src}
												height={52}
												width={138}
												className='h-[38px] w-auto'
												alt={logo.alt}
												priority
												unoptimized
											/>
										</Link>
									</SheetTitle>
								</SheetHeader>
								<div className='mt-6 flex flex-col gap-2'>
									{menu.map(item => (
										<Link
											key={item.title}
											href={item.url}
											onClick={() => setIsMobileMenuOpen(false)}
											className={cn(
												'flex justify-between p-3 text-base font-medium text-white/90 transition-colors hover:bg-white/10 hover:text-white',
												isActivePath(normalizedPathname, normalizePath(item.url)) && 'bg-white/10 text-white'
											)}
										>
											<span>{item.title}</span>
											<ChevronRightIcon />
										</Link>
									))}
									<div className='mt-4'>
										<LanguageDropDown
											className='hover:text-aqua-200 justify-start px-3 text-base text-white/95'
											onLocaleSelected={() => setIsMobileMenuOpen(false)}
										/>
									</div>
								</div>
							</SheetContent>
						</Sheet>
					</div>
				</div>
			</div>
		</section>
	)
}

export { Navbar }
