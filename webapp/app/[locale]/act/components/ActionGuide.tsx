import ScenarioAccordion from './ScenarioAccordion'
import ActionGuideSidebar from './ActionGuideSidebar'

export default function ActionGuide() {
	return (
		<div>
			<h2 className='mb-6 text-xl font-semibold text-gray-800'>What can you do?</h2>
			<div className='grid grid-cols-1 gap-8 lg:grid-cols-[3fr_2fr]'>
				<div>
					<p className='mb-4 text-sm text-gray-600'>
						Select the scenario that matches your situation to see recommended actions.
					</p>
					<ScenarioAccordion />
				</div>
				<ActionGuideSidebar />
			</div>
		</div>
	)
}
