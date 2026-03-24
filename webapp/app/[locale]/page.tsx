import { CardsSection } from '@/components/CardsSection'
import { HeroSection } from '@/components/HeroSection'
import { InfoSection } from '@/components/InfoSection'
import { MapRoutePrefetch } from '@/components/MapRoutePrefetch'
import { SectionSeparator } from '@/components/SectionSeparator'

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params

	return (
		<main className='flex min-h-screen flex-col items-center justify-between'>
			<MapRoutePrefetch locale={locale} />
			<HeroSection />
			<SectionSeparator />
			<InfoSection />
			<CardsSection />
		</main>
	)
}
