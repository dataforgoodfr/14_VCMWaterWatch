import { RessourcesRecord } from '@/types/apiTypes'
import CtaBanner from './CtaBanner'
import ResourceCard from './ResourceCard'

interface ResourcesSectionProps {
	resources: RessourcesRecord[]
}

export default function ResourcesSection({ resources }: ResourcesSectionProps) {
	return (
		<div>
			{/* Section header */}
			<div className='mb-8'>
				<h2 className='text-navy-800 font-[lexend] text-2xl font-semibold'>Resources</h2>
				<p className='text-navy-600 mt-2 max-w-2xl text-base'>
					Guides, reports and templates to train and source your processes.
				</p>
			</div>

			{resources.length > 0 && (
				<div className='grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3'>
					{resources.map(r => (
						<ResourceCard
							key={r.id}
							typeKey={r.fields.Type ?? null}
							title={r.fields.Title}
							description={r.fields['Short Description'] ?? ''}
							actionUrl={r.fields.URL ?? '#'}
						/>
					))}
				</div>
			)}

			{/* CTA banner */}
			<div className='mt-8'>
				<CtaBanner
					title='Do you have a resource to share?'
					subtitle='Feel free to write us.'
					buttonLabel='Contact us'
					href={`mailto:${process.env.CONTACT_EMAIL}`}
				/>
			</div>
		</div>
	)
}
