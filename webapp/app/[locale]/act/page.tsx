import { fetchLetterTemplates } from '@/lib/fetchLetterTemplates'
import ActionGuide from './components/ActionGuide'
import ActSearchSection from './components/ActSearchSection'
import GetInvolvedSection from './components/GetInvolvedSection'

export const revalidate = 300 // SEMI_STATIC_REVALIDATE_SECONDS

export default async function ActPage({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params

	const templates = await fetchLetterTemplates(locale)

	return (
		<main className='bg-gray-50'>
			<div className='container mx-auto px-4 py-16 md:px-8'>
				<div className='flex flex-col items-center gap-12'>
					<h1 className='text-navy-800 font-[lexend] text-[42px] font-semibold'>Take action for your water</h1>
					<h2 className='text-center font-[lexend] text-[24px] font-semibold text-gray-500'>
						Check your city&apos;s situation, understand the level of risk linked to CVM/VCM contamination, and get
						essential information to help you take action!
					</h2>

					<ActSearchSection />

					{/* <ScenarioColumns /> */}
					<ActionGuide />

					{/* <TakeActionInfos /> */}
					<GetInvolvedSection templates={templates} />
				</div>
			</div>
		</main>
	)
}
