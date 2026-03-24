const data = [
	{
		date: '1975',
		title: 'United States',
		description: 'The EPA classifies VCM as a carcinogen and sets the first limits for drinking water.'
	},
	{
		date: '1978',
		title: 'Europe',
		description:
			'First European directive on water quality for human consumption. VCM is identified as a substance of concern.'
	},
	{
		date: '1998',
		title: 'Directive 98/83/EC',
		description: 'EU directive setting a limit of 0.5 µg/L for vinyl chloride monomer in drinking water.'
	},
	{
		date: '2010',
		title: 'France',
		description: 'National environmental health plan published, including monitoring of aging PVC networks.'
	},
	{
		date: '2012',
		title: 'Tighter controls',
		description: 'Several member states strengthen oversight and launch programmes to replace at-risk pipes.'
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
