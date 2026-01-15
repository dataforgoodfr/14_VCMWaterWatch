'use client'

import { useRouter } from 'next/navigation'
import { usePathname, useSearchParams } from 'next/navigation'

import { ChevronDownIcon, GlobeIcon } from 'lucide-react'

import {
	DropdownMenu,
	DropdownMenuTrigger,
	DropdownMenuContent,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { languagesOptionsTranslations } from '@/i18n/i18next.config'
import useLocale from '@/hooks/useLocale'

export interface OptionProps {
	text: string
	value: string
}

export default function LanguageDropDown() {
	const router = useRouter()
	const pathname = usePathname()
	const locale = useLocale()
	const currentLocaleName = languagesOptionsTranslations[locale] || locale
	const searchParams = useSearchParams()

	const onLanguageChange = (option: OptionProps) => {
		const newSearchParams = new URLSearchParams(searchParams)
		const locales = Object.keys(languagesOptionsTranslations || {}) as Array<keyof typeof languagesOptionsTranslations>
		let updatedPathname = pathname
		const regex = new RegExp(`^/(${locales.join('|')})`)

		updatedPathname = pathname.replace(regex, '')

		if (!updatedPathname.startsWith('/')) {
			updatedPathname = `/${updatedPathname}`
		}

		router.push(`/${option.value}${updatedPathname}?${newSearchParams.toString()}`)
	}

	const allLocales = Object.keys(languagesOptionsTranslations || {}) as Array<keyof typeof languagesOptionsTranslations>
	const otherLocales = allLocales.filter(lang => lang !== locale)

	return (
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
				<Button variant='outline' className='flex items-center gap-2'>
					<GlobeIcon className='h-4 w-4' />
					<span>{currentLocaleName}</span>
					<ChevronDownIcon className='h-4 w-4' />
				</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align='end' className='w-45'>
				<DropdownMenuRadioGroup>
					{otherLocales.map(otherLocale => (
						<DropdownMenuRadioItem
							key={otherLocale}
							value={otherLocale}
							onClick={() => onLanguageChange({ text: otherLocale, value: otherLocale })}
						>
							{languagesOptionsTranslations[otherLocale] || otherLocale}
						</DropdownMenuRadioItem>
					))}
				</DropdownMenuRadioGroup>
			</DropdownMenuContent>
		</DropdownMenu>
	)
}
