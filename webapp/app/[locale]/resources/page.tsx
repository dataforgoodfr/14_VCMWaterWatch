import MethodologySection from './components/MethodologySection'
import ResourcesSection from './components/ResourcesSection'
import ResourceTabNav from './components/ResourceTabNav'

export default function ResourcesPage() {
	return (
		<main className='bg-gray-50'>
			<ResourceTabNav />
			<div className='container mx-auto px-4 md:px-8'>
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
			</div>
		</main>
	)
}
