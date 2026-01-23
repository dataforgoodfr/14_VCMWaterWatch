import { notFound } from 'next/navigation'

import { fetchPageDictionary } from '@/lib/fetchPageDictionary'
import { VcmPollutionHistory } from './components/VcmPollutionHistory'
import { SUB_PAGES } from '@/routes/routes'

interface PageProps {
	params: { slug: string; locale: string }
	searchParams?: Record<string, string | string[] | undefined>
}

export default async function Page({ params }: PageProps) {
	// eslint-disable-next-line @typescript-eslint/await-thenable
	const { slug, locale } = await params
	const dictionary = await fetchPageDictionary({ slug, locale })

	if (!slug || !dictionary) {
		notFound()
	}

	switch (slug) {
		// eslint-disable-next-line @typescript-eslint/no-unsafe-enum-comparison
		case SUB_PAGES.VCM_POLLUTION_HISTORY:
			return <VcmPollutionHistory dictionary={dictionary} />
		default:
			notFound()
	}
}
