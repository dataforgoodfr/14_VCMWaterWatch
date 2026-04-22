import CtaBanner from './CtaBanner'

const INFO_CARDS = [
	{
		iconChar: 'ℹ',
		title: 'Data Sources',
		body: 'The collected data mainly comes from four sources: official reports from national health or environmental authorities, data provided by water companies, public archives supplied by PVC manufacturers, and academic publications focused on vinyl chloride monomer. Data directly provided by water users can also be used as a complementary input in order to build a more precise assessment of contamination risks.'
	},
	{
		iconChar: '✓',
		title: 'Verification process',
		body: 'All data have been reviewed and validated by the Earth Chair, a research unit affiliated with the University of Angers, which was the first to raise awareness of the risks associated with vinyl chloride monomer contamination in water distribution networks. This verification process helps ensure the reliability of the information presented on the VCM Watch platform.'
	},
	{
		iconChar: '?',
		title: 'Interpretation of thresholds',
		body: 'VCM concentrations are expressed in micrograms per liter (μg/L). One microgram is equal to one millionth of a gram. VCM is considered a non threshold carcinogenic substance, meaning that even a single molecule may potentially cause cancer. However, the risk remains very low below a certain level. The European Union set a threshold of 0.5 μg/L for vinyl chloride monomer in drinking water in 1998. Above this level, health risks are considered unacceptable according to international safety standards. This threshold remains relatively conservative, as the World Health Organization recommends not exceeding 0.3 μg/L.'
	},
	{
		iconChar: '!',
		title: 'Limitations & Precautions',
		body: 'The risk assessment depends on information provided by health authorities and water companies, which may contain certain gaps. The presence of PVC pipes installed before 1980 indicates only a potential risk: it does not automatically imply that the water is contaminated. VCM levels can also vary significantly from one household to another within the same municipality due to the complex physical processes governing the diffusion of this substance in water. In case of doubt, you are encouraged to request a tap water test from your water supplier or from an analytical laboratory.'
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
		action: 'Contacter la compagnie d’eau et les autorités sanitaires'
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
				<p className='text-navy-600 mt-2 text-base'>
					Vinyl chloride monomer is a carcinogenic gas that can be released into water through PVC pipes installed
					before 1980. Outside France, and more recently Spain, no country systematically monitors the presence of vinyl
					chloride monomer in water. In order to assess contamination risks, the VCM Watch platform team has compiled
					data from multiple sources that make it possible to identify the presence of problematic pipelines.
				</p>
			</div>

			{/* 2×2 info cards */}
			<div className='mb-10 grid grid-cols-1 gap-5 sm:grid-cols-2'>
				{INFO_CARDS.map(card => (
					<div key={card.title} className='rounded-sm bg-white p-8 shadow-xs'>
						<div className='mb-3 flex items-center gap-3'>
							<span className='bg-navy-800 flex h-9 w-9 shrink-0 items-center justify-center rounded-sm text-base font-bold text-white'>
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
				<div className='border-navy-200 overflow-x-auto rounded-sm border'>
					<table className='w-full text-sm'>
						<thead>
							<tr className='bg-navy-800 text-left text-white'>
								<th scope='col' className='px-4 py-3 font-semibold'>
									Concentration (µg/L)
								</th>
								<th scope='col' className='px-4 py-3 font-semibold'>
									Level
								</th>
								<th scope='col' className='px-4 py-3 font-semibold'>
									Interpretation
								</th>
								<th scope='col' className='px-4 py-3 font-semibold'>
									Recommended Action
								</th>
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
					* Thresholds based on WHO guidelines and EU Directive 2020/2184. Site-specific factors may affect the final
					classification.
				</p>
			</div>

			{/* Who to contact CTA */}
			<div className='pb-10'>
				<h3 className='text-navy-800 mb-4 font-[lexend] text-lg font-semibold'>Who to contact?</h3>
				<CtaBanner
					title='Questions about the methodology?'
					subtitle='Reach out to our scientific team or join the open-source project to propose improvements.'
					buttonLabel='Get in touch'
					href={`mailto:${process.env.CONTACT_EMAIL}`}
				/>
			</div>
		</div>
	)
}
