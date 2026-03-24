import ScenarioColumns from './ScenarioColumns'
import ActionGuideSidebar from './ActionGuideSidebar'

export default function ActionGuide() {
	return (
		<div>
			<h2 className='text-navy-800 mb-6 font-[lexend] text-2xl font-semibold'>What can you do?</h2>
			<p className='text-navy-800 mb-4 text-sm'>
				Select the scenario that matches your situation to see recommended actions.
			</p>
			<ScenarioColumns />
			<div className='mt-10'>
				<ActionGuideSidebar />
			</div>
		</div>
	)
}
