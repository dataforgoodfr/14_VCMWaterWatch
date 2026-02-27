'use client'

import { Suspense } from 'react'

import { useRouter } from 'next/navigation'
import { usePathname, useSearchParams } from 'next/navigation'

import { ChevronDownIcon } from 'lucide-react'

import {
	DropdownMenu,
	DropdownMenuTrigger,
	DropdownMenuContent,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { languagesOptionsTranslations } from '@/i18n/i18next.config'
import { cn } from '@/lib/utils'
import useLocale from '@/hooks/useLocale'

export interface OptionProps {
	text: string
	value: string
}

interface LanguageDropDownProps {
	className?: string
	onLocaleSelected?: () => void
}

const localeFlags: Record<string, string> = {
	en: '🇬🇧',
	fr: '🇫🇷'
}

function LanguageDropDownInner({ className, onLocaleSelected }: LanguageDropDownProps) {
	const router = useRouter()
	const pathname = usePathname()
	const locale = useLocale()
	const currentLocaleName = languagesOptionsTranslations[locale] || locale
	const currentLocaleFlag = localeFlags[locale] || '🌐'
	const searchParams = useSearchParams()

	const onLanguageChange = (option: OptionProps) => {
		const newSearchParams = new URLSearchParams(searchParams)
		const locales = Object.keys(languagesOptionsTranslations || {}) as (keyof typeof languagesOptionsTranslations)[]
		let updatedPathname = pathname
		const regex = new RegExp(`^/(${locales.join('|')})`)

		updatedPathname = pathname.replace(regex, '')

		if (!updatedPathname.startsWith('/')) {
			updatedPathname = `/${updatedPathname}`
		}

		const query = newSearchParams.toString()
		const nextUrl = `/${option.value}${updatedPathname}${query ? `?${query}` : ''}`

		router.push(nextUrl)
		onLocaleSelected?.()
	}

	const allLocales = Object.keys(languagesOptionsTranslations || {}) as (keyof typeof languagesOptionsTranslations)[]
	const otherLocales = allLocales.filter(lang => lang !== locale)

	return (
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
				<Button
					variant='ghost'
					className={cn(
						'flex items-center gap-1 px-2 text-sm font-medium text-inherit hover:bg-transparent hover:text-inherit',
						className
					)}
				>
					<span className='text-[20px] leading-none' aria-hidden='true'>
						{currentLocaleFlag}
					</span>
					<span className='text-[18px]'>{currentLocaleName}</span>
					<ChevronDownIcon className='h-4 w-4 opacity-80' />
				</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align='end' className='bg-navy-500 border-navy-600 w-44 text-white'>
				<DropdownMenuRadioGroup>
					{otherLocales.map(otherLocale => (
						<DropdownMenuRadioItem
							key={otherLocale}
							value={otherLocale}
							className='focus:bg-navy-600 text-left focus:text-white'
							onClick={() => onLanguageChange({ text: otherLocale, value: otherLocale })}
						>
							<span className='text-[20px] leading-none' aria-hidden='true'>
								{localeFlags[otherLocale] || '🌐'}
							</span>
							<span className='text-[18px]'>{languagesOptionsTranslations[otherLocale] || otherLocale}</span>
						</DropdownMenuRadioItem>
					))}
				</DropdownMenuRadioGroup>
			</DropdownMenuContent>
		</DropdownMenu>
	)
}

export default function LanguageDropDown(props: LanguageDropDownProps) {
	return (
		<Suspense>
			<LanguageDropDownInner {...props} />
		</Suspense>
	)
}
