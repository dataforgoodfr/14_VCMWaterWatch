import CtaBanner from './CtaBanner'

// Each card uses a simple styled span (circle + text character) instead of a lucide icon.
// This matches the design mockup which shows minimal circle icons.
const INFO_CARDS = [
	{
		iconChar: 'ℹ',
		iconBg: 'bg-blue-100',
		iconColor: 'text-blue-700',
		title: 'Data Sources',
		body: 'Data comes from three sources: (1) official reports from national health authorities, (2) citizen contributions verified by our team, (3) peer-reviewed scientific publications.'
	},
	{
		iconChar: '✓',
		iconBg: 'bg-green-100',
		iconColor: 'text-green-700',
		title: 'Verification Process',
		body: 'Each citizen contribution goes through validation: verification of the source document, cross-referencing with official data, and validation by at least one member of the scientific team.'
	},
	{
		iconChar: '?',
		iconBg: 'bg-amber-100',
		iconColor: 'text-amber-700',
		title: 'Interpreting Thresholds',
		body: 'CVM concentrations are expressed in µg/L. The European directive sets a threshold of 0.5 µg/L. Some countries apply stricter standards. See the table below.'
	},
	{
		iconChar: '!',
		iconBg: 'bg-red-100',
		iconColor: 'text-red-700',
		title: 'Limitations & Precautions',
		body: 'Map data does not replace official analysis. When in doubt, contact your local health authority. VCM Watch is a citizen awareness tool.'
	}
]

// CVM Concentration Reference Table — columns match design:
// Concentration (µg/L) | Level | Interpretation | Recommended Action
const CVM_TABLE_ROWS = [
	{
		concentration: '< 0.1',
		level: 'Compliant (strict)',
		dotColor: 'bg-green-500',
		interpretation: 'Below detection threshold',
		action: 'No action required'
	},
	{
		concentration: '0.1 – 0.5',
		level: 'Compliant',
		dotColor: 'bg-green-400',
		interpretation: 'EU Directive 2020/2184 met',
		action: 'Routine monitoring'
	},
	{
		concentration: '0.5 – 1.0',
		level: 'Vigilance',
		dotColor: 'bg-orange-400',
		interpretation: 'Above EU threshold',
		action: 'Report to health authority'
	},
	{
		concentration: '> 1.0',
		level: 'Alert',
		dotColor: 'bg-red-500',
		interpretation: 'Significant exceedance',
		action: 'Contact ARS urgently'
	},
	{
		concentration: 'Not measured',
		level: 'Unknown',
		dotColor: 'bg-gray-400',
		interpretation: 'Data unavailable',
		action: 'Request local analysis'
	}
]

// TODO: i18n — INFO_CARDS and CVM_TABLE_ROWS are hardcoded in English; extract for translation when i18n is added
export default function MethodologySection() {
	return (
		<div>
			{/* Section header */}
			<div className='mb-8'>
				<h2 className='text-navy-800 font-[lexend] text-2xl font-semibold'>Methodology</h2>
				<p className='text-navy-600 mt-2 max-w-2xl text-base'>
					How to interpret the data and who to contact to act correctly.
				</p>
			</div>

			{/* 2×2 info cards */}
			<div className='mb-10 grid grid-cols-1 gap-5 sm:grid-cols-2'>
				{INFO_CARDS.map(card => (
					<div key={card.title} className='border-navy-200 bg-navy-50 rounded-xl border p-5'>
						<div className='mb-3 flex items-center gap-3'>
							<span
								className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-base font-bold ${card.iconBg} ${card.iconColor}`}
							>
								{card.iconChar}
							</span>
							<h3 className='text-navy-800 font-[lexend] text-base font-semibold'>{card.title}</h3>
						</div>
						<p className='text-navy-600 text-sm leading-relaxed'>{card.body}</p>
					</div>
				))}
			</div>

			{/* CVM Concentration Reference Table */}
			<div className='mb-10'>
				<h3 className='text-navy-800 mb-4 font-[lexend] text-lg font-semibold'>CVM Concentration Reference Table</h3>
				<div className='border-navy-200 overflow-x-auto rounded-xl border'>
					<table className='w-full text-sm'>
						<thead>
							<tr className='bg-navy-800 text-left text-white'>
								<th scope='col' className='px-4 py-3 font-semibold'>Concentration (µg/L)</th>
								<th scope='col' className='px-4 py-3 font-semibold'>Level</th>
								<th scope='col' className='px-4 py-3 font-semibold'>Interpretation</th>
								<th scope='col' className='px-4 py-3 font-semibold'>Recommended Action</th>
							</tr>
						</thead>
						<tbody>
							{CVM_TABLE_ROWS.map((row, i) => (
								<tr key={row.level} className={i % 2 === 0 ? 'bg-white' : 'bg-navy-50'}>
									<td className='text-navy-700 px-4 py-3 font-mono text-xs'>{row.concentration}</td>
									<td className='px-4 py-3'>
										<span className='flex items-center gap-1.5'>
											<span className={`inline-block h-2.5 w-2.5 rounded-full ${row.dotColor}`} />
											<span className='text-navy-700'>{row.level}</span>
										</span>
									</td>
									<td className='text-navy-700 px-4 py-3'>{row.interpretation}</td>
									<td className='text-navy-700 px-4 py-3'>{row.action}</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
				<p className='text-navy-500 mt-2 text-xs'>
					* Thresholds based on WHO guidelines and EU Directive 2020/2184. Site-specific factors may affect the final classification.
				</p>
			</div>

			{/* Who to contact CTA */}
			<div>
				<h3 className='text-navy-800 mb-4 font-[lexend] text-lg font-semibold'>Who to contact?</h3>
				<CtaBanner
					title='Questions about the methodology?'
					subtitle='Reach out to our scientific team or join the open-source project to propose improvements.'
					buttonLabel='Get in touch'
					href='/act#involved'
				/>
			</div>
		</div>
	)
}
