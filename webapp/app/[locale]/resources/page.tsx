import { SectionSeparator } from '@/components/SectionSeparator'

import MethodologySection from './components/MethodologySection'
import ResourcesSection from './components/ResourcesSection'
import ResourceTabNav from './components/ResourceTabNav'

export default function ResourcesPage() {
	return (
		<main className='container mx-auto px-4 py-16 md:px-8'>
			{/* Page header */}
			<div>
				<h1 className='text-navy-800 font-[lexend] text-3xl font-semibold'>Resources</h1>
				<div className='mt-6'>
					<SectionSeparator />
				</div>
			</div>

			{/* Sticky tab navigation */}
			<div className='mt-6'>
				<ResourceTabNav />
			</div>

			{/* Sections */}
			<div className='mt-12 space-y-16'>
				{/* Resources section */}
				<section id='resources' className='scroll-mt-[148px]'>
					<ResourcesSection />
				</section>

				<hr className='border-navy-200' />

				{/* Methodology section */}
				<section id='methodology' className='scroll-mt-[148px]'>
					<MethodologySection />
				</section>
			</div>
		</main>
	)
}
