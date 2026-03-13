import { fetchCountries } from '@/lib/fetchCountries'
import type { CountryListRecord } from '@/types/apiTypes'

import { CountryCarousel } from './components/CountryCarousel'

export default async function CountryProfilePage() {
	const countries: CountryListRecord[] = await fetchCountries()

	return (
		<main className='container mx-auto px-4 md:px-8'>
			<h1 className='text-navy-800 pt-16 font-[lexend] text-[32px] font-semibold'>Fiches pays</h1>
			<p className='pt-8 pb-2 font-[lexend] text-[19px] font-medium text-gray-600'>Sélectionnez un pays</p>
			{countries.length === 0 ? (
				<p className='mt-4 text-lg text-gray-600'>Aucun pays disponible.</p>
			) : (
				<CountryCarousel countries={countries} />
			)}
		</main>
	)
}
