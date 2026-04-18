const scenarios = [
	{
		value: 'green',
		badge: '🟢',
		title: 'Your water is compliant',
		content: (
			<div className='text-navy-800 space-y-3 text-sm'>
				<p>Good news! Your water distribution zone meets the regulatory standards for PVC and VCM levels.</p>
				<p>
					Even though your water is safe, staying informed is important. VCM levels can vary significantly from one
					household to another, and additional testing may reveal contamination, particularly if your network includes
					pre-1980 PVC materials.
				</p>
				<p>
					You can contribute to our monitoring efforts by{' '}
					<a href='#contribute' className='text-navy-600 underline'>
						sharing your water data
					</a>
					.
				</p>
			</div>
		)
	},
	{
		value: 'yellow-orange',
		badge: '🟡🟠',
		title: 'Your water supply may be at risk of contamination',
		content: (
			<div className='text-navy-800 space-y-3 text-sm'>
				<div className='rounded-md border border-yellow-200 bg-yellow-50 p-3'>
					<p className='font-medium text-yellow-800'>⚠️ Action required from your water supplier</p>
				</div>
				<p>
					Your distribution zone has shown presence of pre-1980 PVC pipes and absence of monitoring. This warrants
					attention and monitoring for vinyl chloride monomer (VCM) should be put in place.
				</p>
				<ul className='list-disc space-y-2 pl-5'>
					<li>
						<strong>Contact your water provider</strong> — Request detailed analysis results for your zone and
						inquire about any planned monitoring or testing measures.
					</li>
					<li>
						<strong>Contact your mayor</strong> — In some cases, the municipality is responsible for water
						distribution. Write to request transparency and action.
					</li>
					<li>
						<strong>Stay informed</strong> — Keep up to date with developments, and consider sharing relevant
						information with other residents who may be affected.
					</li>
				</ul>
			</div>
		)
	},
	{
		value: 'red',
		badge: '🔴',
		title: 'Your water presents risks for your health',
		content: (
			<div className='text-navy-800 space-y-3 text-sm'>
				<div className='rounded-md border border-red-200 bg-red-50 p-3'>
					<p className='font-medium text-red-800'>🚨 Alert: VCM exceedances have been detected</p>
				</div>
				<p>
					Your distribution zone has reported levels of PVC-related compounds and/or VCM that may exceed regulatory
					limits. Immediate attention is required.
				</p>
				<ul className='list-disc space-y-2 pl-5'>
					<li>
						<strong>Contact your water provider without delay</strong> — Request a detailed explanation of the
						situation and a clear timeline for corrective actions.
						<ul className='text-navy-600 mt-1 list-disc space-y-1 pl-5'>
							<li>Ask for the latest available water quality data.</li>
							<li>
								Request the implementation of appropriate remediation measures, such as pipe flushing or
								replacement.
							</li>
							<li>
								If the most recent contamination findings are over a year old, ask whether corrective measures
								have been implemented and whether recent follow-up analyses confirm that the situation is now
								under control.
							</li>
						</ul>
					</li>
					<li>
						<strong>Contact your mayor</strong> — Use the official letter template to formally request
						transparency and prompt action from local authorities.
					</li>
					<li>
						<strong>Contact your Member of Parliament</strong> — Escalate the issue to ensure it receives
						national-level attention.
					</li>
					<li>
						<strong>Take precautionary measures</strong> — Until the situation is clarified, use bottled water
						for drinking.
					</li>
				</ul>
			</div>
		)
	}
]

export default function ScenarioColumns() {
	return (
		<div className='grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-stretch'>
			{scenarios.map(scenario => (
				<div
					key={scenario.value}
					className='border-navy-800 bg-navy-50 flex h-full flex-col rounded-r-2xl border-l-4 p-4 shadow-sm'
				>
					<div className='border-navy-200 mb-3 flex items-start gap-2 border-b pb-3'>
						<span className='text-lg leading-none'>{scenario.badge}</span>
						<h3 className='text-navy-800 text-sm leading-snug font-semibold'>{scenario.title}</h3>
					</div>
					<div className='min-h-0 flex-1 text-sm'>{scenario.content}</div>
				</div>
			))}
		</div>
	)
}
