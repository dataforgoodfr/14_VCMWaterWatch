const scenarios = [
	{
		value: 'green',
		badge: '🟢',
		title: 'Your water is compliant',
		content: (
			<div className='space-y-3 text-sm text-gray-700'>
				<p>Good news! Your water distribution zone meets the regulatory standards for PVC and VCM levels.</p>
				<p>
					Even though your water is safe, staying informed is important. Water quality can change over time due to aging
					infrastructure.
				</p>
				<p>
					You can contribute to our monitoring efforts by{' '}
					<a href='#contribute' className='text-blue-600 underline'>
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
		title: 'Your water shows signs of concern',
		content: (
			<div className='space-y-3 text-sm text-gray-700'>
				<div className='rounded-md border border-yellow-200 bg-yellow-50 p-3'>
					<p className='font-medium text-yellow-800'>⚠️ Caution: elevated levels detected</p>
				</div>
				<p>
					Your distribution zone has shown elevated levels of PVC or VCM. While not yet exceeding legal limits, this
					warrants attention.
				</p>
				<ol className='list-decimal space-y-2 pl-5'>
					<li>
						<strong>Contact your water provider</strong> — Request detailed analysis results for your zone.
						<ul className='mt-1 list-disc space-y-1 pl-5 text-gray-600'>
							<li>Ask for the latest water quality report</li>
							<li>Request information about pipe materials in your area</li>
							<li>Ask about planned infrastructure upgrades</li>
						</ul>
					</li>
					<li>
						<strong>Contact your mayor</strong> — The municipality is responsible for water distribution. Write to
						request transparency and action.
					</li>
					<li>
						<strong>Stay informed</strong> — Follow updates and consider installing a water filter as a precaution.
					</li>
				</ol>
			</div>
		)
	},
	{
		value: 'red',
		badge: '🔴',
		title: 'Your water exceeds safety limits',
		content: (
			<div className='space-y-3 text-sm text-gray-700'>
				<div className='rounded-md border border-red-200 bg-red-50 p-3'>
					<p className='font-medium text-red-800'>🚨 Alert: non-compliant levels detected</p>
				</div>
				<p>
					Your distribution zone has exceeded regulatory limits for PVC and/or VCM. Immediate action is recommended.
				</p>
				<ol className='list-decimal space-y-2 pl-5'>
					<li>
						<strong>Contact your water provider immediately</strong> — Demand a detailed explanation and timeline for
						remediation.
						<ul className='mt-1 list-disc space-y-1 pl-5 text-gray-600'>
							<li>Request emergency water quality testing</li>
							<li>Ask for alternative water supply options</li>
							<li>Demand a written response within 15 days</li>
						</ul>
					</li>
					<li>
						<strong>Write to your mayor</strong> — Use our letter template to formally request action.
					</li>
					<li>
						<strong>Contact your Member of Parliament</strong> — Escalate the issue to ensure national attention.
					</li>
					<li>
						<strong>Protect yourself</strong> — Consider using bottled water for drinking and cooking until the
						situation is resolved.
					</li>
				</ol>
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
					className='flex h-full flex-col rounded-lg border border-gray-200 bg-white p-4 shadow-sm'
				>
					<div className='mb-3 flex items-start gap-2 border-b border-gray-100 pb-3'>
						<span className='text-lg leading-none'>{scenario.badge}</span>
						<h3 className='text-sm font-semibold leading-snug text-gray-900'>{scenario.title}</h3>
					</div>
					<div className='min-h-0 flex-1 text-sm'>{scenario.content}</div>
				</div>
			))}
		</div>
	)
}
