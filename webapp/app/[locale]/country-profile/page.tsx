import { fetchCountries } from '@/lib/fetchCountries'
import type { CountryListRecord } from '@/types/apiTypes'

import { CountryCarousel } from './components/CountryCarousel'

interface CountryProfilePageProps {
	params: Promise<{ locale: string }>
}

export default async function CountryProfilePage({ params }: CountryProfilePageProps) {
	const { locale } = await params
	const countries: CountryListRecord[] = await fetchCountries()

	return (
		<main className='container mx-auto px-4 md:px-8'>
			<h1 className='text-navy-800 pt-16 font-[lexend] text-[32px] font-semibold'>Country profiles</h1>
			<p className='pt-8 pb-2 font-[lexend] text-[19px] font-medium text-gray-600'>Select a country</p>
			{countries.length === 0 ? (
				<p className='mt-4 text-lg text-gray-600'>No countries available.</p>
			) : (
				<CountryCarousel countries={countries} locale={locale} />
			)}
		</main>
	)
}
