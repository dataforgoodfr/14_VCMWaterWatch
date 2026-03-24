import ActSearchSection from './components/ActSearchSection'
import ActionGuide from './components/ActionGuide'

export default function ActPage() {
	return (
		<main className='mx-auto w-full max-w-5xl space-y-16 px-6 py-16'>
			<h1 className='text-3xl font-semibold text-gray-900'>Take action</h1>

			{/* Step 1: Search */}
			<section id='search'>
				<ActSearchSection />
			</section>

			{/* Step 2: Action Guide */}
			<section id='guide'>
				<ActionGuide />
			</section>

			{/* Steps 3 & 4: placeholder for phase 2 (forms, data submission) */}
		</main>
	)
}
