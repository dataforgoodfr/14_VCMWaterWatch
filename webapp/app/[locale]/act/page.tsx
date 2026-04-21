import { SectionSeparator } from '@/components/SectionSeparator'
import { fetchLetterTemplates } from '@/lib/fetchLetterTemplates'

import ActSearchSection from './components/ActSearchSection'
import ActionGuide from './components/ActionGuide'
import GetInvolvedSection from './components/GetInvolvedSection'

export const revalidate = 300 // SEMI_STATIC_REVALIDATE_SECONDS

export default async function ActPage({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params

	const templates = await fetchLetterTemplates(locale)

	return (
		<main className='container mx-auto px-4 py-16 md:px-8'>
			<div>
				<h1 className='text-navy-800 font-[lexend] text-3xl font-semibold'>Take action</h1>
				<div className='mt-6'>
					<SectionSeparator />
				</div>
			</div>

			<div className='mt-12 space-y-16'>
				{/* Step 1: Search */}
				<section id='search'>
					<ActSearchSection />
				</section>

				<hr className='border-navy-200' />

				{/* Step 2: Action Guide */}
				<section id='guide'>
					<ActionGuide />
				</section>

				<hr className='border-navy-200' />

				{/* Step 3: Get Involved (Templates + Contribute + Join) */}
				<section id='involved'>
					<GetInvolvedSection templates={templates} />
				</section>
			</div>
		</main>
	)
}
