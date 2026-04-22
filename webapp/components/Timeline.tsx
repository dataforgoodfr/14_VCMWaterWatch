const data = [
	{
		date: '1974',
		title: 'United States',
		description:
			'OSHA establishes workplace air regulations for vinyl chloride in 1974, following a major occupational health scandal in which exposed workers in PVC production plants developed fatal hepatic angiosarcomas.'
	},
	{
		date: '1978',
		title: 'Europe',
		description:
			'European Directive 78/610/EEC prohibits the installation of PVC water pipes contaminated with VCM, which is known to migrate into drinking water. The directive is transposed into national legislation by Member States in the following years.'
	},
	{
		date: '1998',
		title: 'Europe',
		description:
			'EU Directive 98/83/EC sets a parametric value of 0.5 µg/L for vinyl chloride monomer in drinking water. However, it does not require monitoring of this parameter, which limits its effective enforcement.'
	},
	{
		date: '2012',
		title: 'France',
		description:
			'Instruction n° DGS/EA4/2012/366 mandates systematic monitoring of vinyl chloride monomer (VCM) in drinking water. In the following years, tens of thousands of analyses are carried out, revealing contamination in thousands of municipalities.'
	},
	{
		date: '2023',
		title: 'Spain',
		description:
			'Royal Decree 3/2023 establishes a framework for systematic VCM testing in distribution networks and at consumer taps where PVC pipes are suspected. Monitoring results under this new framework are not yet publicly available.'
	}
]

function TimelineItem({ date, title, description }: { date: string; title: string; description: string }) {
	return (
		<div className='relative flex gap-4'>
			<div className='border-aqua-500 bg-aqua-500 z-10 mt-1.5 -ml-[11px] h-3 w-3 shrink-0 rounded-full border-2' />
			<div className='pb-8'>
				<p className='text-navy-800 mb-0 font-[lexend] text-[20px] font-medium'>{date}</p>
				<p className='text-navy-800 text-xl font-semibold tracking-[-0.01em]'>{title}</p>
				<p className='text-sm text-pretty text-gray-600'>{description}</p>
			</div>
		</div>
	)
}

export default function Timeline() {
	return (
		<div className='px-1 py-4 md:px-0'>
			<div className='relative pl-[5px] md:hidden'>
				<div className='border-border absolute top-0 bottom-0 left-0 w-0 border-l-2 border-dashed' />
				{data.map((item, index) => (
					<TimelineItem key={index} date={item.date} title={item.title} description={item.description} />
				))}
			</div>

			<div className='relative hidden items-start gap-10 md:flex'>
				<div className='border-border absolute top-[75px] right-0 left-0 border-t-2 border-dashed' />
				{data.map(({ description, date, title }, index) => (
					<div className='relative flex min-w-0 flex-1 flex-col items-center' key={index}>
						<div className='w-full space-y-3'>
							<p className='text-navy-800 mb-0 font-[lexend] text-[20px] font-medium'>{date}</p>
							<p className='text-navy-800 text-xl font-semibold tracking-[-0.01em]'>{title}</p>
							<div className='border-aqua-500 bg-aqua-500 z-10 h-3 w-3 shrink-0 rounded-full border-2' />
							<p className='text-sm text-pretty text-gray-600 sm:text-base'>{description}</p>
						</div>
					</div>
				))}
			</div>
		</div>
	)
}
