import ScenarioColumns from './ScenarioColumns'
import ActionGuideSidebar from './ActionGuideSidebar'

export default function ActionGuide() {
	return (
		<div>
			<h2 className='mb-6 text-xl font-semibold text-gray-800'>What can you do?</h2>
			<p className='mb-4 text-sm text-gray-600'>
				Select the scenario that matches your situation to see recommended actions.
			</p>
			<ScenarioColumns />
			<div className='mt-10'>
				<ActionGuideSidebar />
			</div>
		</div>
	)
}
