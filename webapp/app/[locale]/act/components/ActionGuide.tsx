import ScenarioColumns from './ScenarioColumns'

export default function ActionGuide() {
	return (
		<div>
			<h2 className='text-navy-800 mb-6 font-[lexend] text-2xl font-semibold'>What can you do?</h2>
			<p className='text-navy-800 mb-4 text-sm'>
				Select the scenario that matches your situation to see recommended actions.
			</p>
			<ScenarioColumns />

			{/* Callouts previously in ActionGuideSidebar */}
			<div className='border-navy-300 bg-navy-100 mt-8 rounded-lg border p-4'>
				<h4 className='text-navy-900 text-sm font-semibold'>💡 Important reminder</h4>
				<p className='text-navy-800 mt-2 text-sm'>
					You are paying for a water distribution service. Access to safe, clean drinking water is a legal obligation
					for your water provider and municipality. You have every right to demand transparency and action.
				</p>
			</div>
		</div>
	)
}
