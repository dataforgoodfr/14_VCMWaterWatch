import { SectionSeparator } from '@/components/SectionSeparator'

import ActSearchSection from './components/ActSearchSection'
import ActionGuide from './components/ActionGuide'
import ContributeDataSection from './components/ContributeDataSection'
import JoinProjectSection from './components/JoinProjectSection'

export default function ActPage() {
	return (
		<main className='container mx-auto space-y-16 px-4 py-16 md:px-8'>
			<div>
				<h1 className='text-navy-800 font-[lexend] text-3xl font-semibold'>Take action</h1>
				<div className='mt-6'>
					<SectionSeparator />
				</div>
			</div>

			{/* Step 1: Search */}
			<section id='search'>
				<ActSearchSection />
			</section>

			{/* Step 2: Action Guide */}
			<section id='guide'>
				<ActionGuide />
			</section>

			{/* Step 3: Contribute Data */}
			<section id='contribute'>
				<ContributeDataSection />
			</section>

			{/* Step 4: Join the Project */}
			<section id='join'>
				<JoinProjectSection />
			</section>
		</main>
	)
}
