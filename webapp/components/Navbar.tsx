'use client'

import { useEffect, useState } from 'react'

import Image from 'next/image'

import { Menu } from 'lucide-react'

import { cn } from '@/lib/utils'

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Button } from '@/components/ui/button'
import {
	NavigationMenu,
	NavigationMenuContent,
	NavigationMenuItem,
	NavigationMenuLink,
	NavigationMenuList,
	NavigationMenuTrigger
} from '@/components/ui/navigation-menu'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { ROUTES, SUB_PAGES } from '@/routes/routes'
import LanguageDropDown from './LanguageDropDown'

interface MenuItem {
	title: string
	url: string
	description?: string
	icon?: React.ReactNode
	items?: MenuItem[]
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

// Component created from https://www.shadcnblocks.com/block/navbar1
const Navbar = ({
	logo = {
		url: ROUTES.HOME,
		src: 'https://deifkwefumgah.cloudfront.net/shadcnblocks/block/logos/shadcnblockscom-icon.svg',
		alt: 'logo',
		title: 'VCM Water Watch'
	},
	menu = [
		{ title: 'Home', url: ROUTES.HOME },
		{
			title: 'VCM Pollution History',
			url: `${ROUTES.PAGE}/${SUB_PAGES.VCM_POLLUTION_HISTORY}`
		},
		{
			title: 'Blog',
			url: ROUTES.BLOG
		}
	],
	className
}: NavbarProps) => {
	// Suppress hydration mismatch for Radix UI components
	// They generate random IDs that differ between server and client
	const [isClient, setIsClient] = useState(false)

	useEffect(() => {
		setIsClient(true)
	}, [])

	// Don't render interactive elements until client-side
	// This prevents hydration mismatches from Radix UI ID generation
	if (isClient) {
		return (
			<section className={cn('py-4', className)}>
				<div className='container'>
					{/* Desktop Menu */}
					<nav className='hidden items-center justify-between lg:flex'>
						<div className='flex items-center gap-6'>
							{/* Logo */}
							<a href={logo.url} className='flex items-center gap-2'>
								<Image src={logo.src} height={32} width={32} className='max-h-8 dark:invert' alt={logo.alt} priority />
								<span className='text-lg font-semibold tracking-tighter'>{logo.title}</span>
							</a>
							<div className='flex items-center'>
								<NavigationMenu>
									<NavigationMenuList>{menu.map(item => renderMenuItem(item))}</NavigationMenuList>
								</NavigationMenu>
							</div>
						</div>
						<div className='flex gap-2'>
							<LanguageDropDown />
						</div>
					</nav>

					{/* Mobile Menu */}
					<div className='block lg:hidden'>
						<div className='flex items-center justify-between'>
							{/* Logo */}
							<a href={logo.url} className='flex items-center gap-2'>
								<Image src={logo.src} height={32} width={32} className='max-h-8 dark:invert' alt={logo.alt} priority />
							</a>
							<Sheet>
								<SheetTrigger asChild>
									<Button variant='outline' size='icon'>
										<Menu className='size-4' />
									</Button>
								</SheetTrigger>
								<SheetContent className='overflow-y-auto'>
									<SheetHeader>
										<SheetTitle>
											<a href={logo.url} className='flex items-center gap-2'>
												<Image
													src={logo.src}
													height={32}
													width={32}
													className='max-h-8 dark:invert'
													alt={logo.alt}
													priority
												/>
											</a>
										</SheetTitle>
									</SheetHeader>
									<div className='flex flex-col gap-6 p-4'>
										<Accordion type='single' collapsible className='flex w-full flex-col gap-4'>
											{menu.map(item => renderMobileMenuItem(item))}
										</Accordion>

										<div className='flex flex-col gap-3'>
											<LanguageDropDown />
										</div>
									</div>
								</SheetContent>
							</Sheet>
						</div>
					</div>
				</div>
			</section>
		)
	} else {
		return null
	}
}

const renderMenuItem = (item: MenuItem) => {
	if (item.items) {
		return (
			<NavigationMenuItem key={item.title}>
				<NavigationMenuTrigger>{item.title}</NavigationMenuTrigger>
				<NavigationMenuContent className='bg-popover text-popover-foreground'>
					{item.items.map(subItem => (
						<NavigationMenuLink asChild key={subItem.title} className='w-80'>
							<SubMenuLink item={subItem} />
						</NavigationMenuLink>
					))}
				</NavigationMenuContent>
			</NavigationMenuItem>
		)
	}

	return (
		<NavigationMenuItem key={item.title}>
			<NavigationMenuLink
				href={item.url}
				className='group bg-background hover:bg-muted hover:text-accent-foreground inline-flex h-10 w-max items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors'
			>
				{item.title}
			</NavigationMenuLink>
		</NavigationMenuItem>
	)
}

const renderMobileMenuItem = (item: MenuItem) => {
	if (item.items) {
		return (
			<AccordionItem key={item.title} value={item.title} className='border-b-0'>
				<AccordionTrigger className='text-md py-0 font-semibold hover:no-underline'>{item.title}</AccordionTrigger>
				<AccordionContent className='mt-2'>
					{item.items.map(subItem => (
						<SubMenuLink key={subItem.title} item={subItem} />
					))}
				</AccordionContent>
			</AccordionItem>
		)
	}

	return (
		<a key={item.title} href={item.url} className='text-md font-semibold'>
			{item.title}
		</a>
	)
}

const SubMenuLink = ({ item }: { item: MenuItem }) => {
	return (
		<a
			className='hover:bg-muted hover:text-accent-foreground flex min-w-80 flex-row gap-4 rounded-md p-3 leading-none no-underline transition-colors outline-none select-none'
			href={item.url}
		>
			<div className='text-foreground'>{item.icon}</div>
			<div>
				<div className='text-sm font-semibold'>{item.title}</div>
				{item.description && <p className='text-muted-foreground text-sm leading-snug'>{item.description}</p>}
			</div>
		</a>
	)
}

export { Navbar }
