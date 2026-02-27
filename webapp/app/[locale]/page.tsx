import { HeroSection } from '@/components/HeroSection'
import { InfoSection } from '@/components/InfoSection'
import { CardsSection } from '@/components/CardsSection'
import { SectionSeparator } from '@/components/SectionSeparator'

export default function Page() {
	return (
		<main className='flex min-h-screen flex-col items-center justify-between'>
			<HeroSection />
			<SectionSeparator />
			<InfoSection />
			<CardsSection />
		</main>
	)
}
