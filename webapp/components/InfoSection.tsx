import { InfoCard } from '@/components/InfoCard'

export const InfoSection = () => {
	const blocks = [
		{
			label: 'The issue',
			content:
				'Classified as a definite human carcinogen (Group 1) by the IARC, it is linked to risks of hepatic angiosarcoma and hepatocellular carcinoma. Vinyl chloride monomer (VCM) is a highly carcinogenic compound that can contaminate drinking water through aging PVC pipes.'
		},
		{
			label: 'Why it matters',
			content:
				'Millions of kilometers of PVC piping are installed across Europe, and a significant share is nearing end of life. Data transparency varies widely between countries, making it hard to assess population-level risk with precision.'
		}
	]

	const stats = [
		{ value: '275,000 km', label: 'of piping' },
		{ value: '12 countries', label: 'in Europe' },
		{ value: 'XXX', label: 'people potentially affected' }
	]

	return (
		<section className='w-full bg-gray-50 py-16 md:py-24'>
			<div className='container mx-auto px-4 md:px-8'>
				<InfoCard>
					<div className='flex flex-col gap-4'>
						<h3 className='text-navy-800 font-[lexend] text-[32px] font-semibold'>What is VCM?</h3>
						<div className='flex flex-col justify-between gap-18 lg:flex-row'>
							{blocks.map(block => (
								<div key={block.label} className='flex flex-1 flex-col gap-2.5'>
									<p className='text-navy-800 font-[lexend] text-2xl font-medium'>{block.label}</p>
									<p className='text-navy-800 text-xl'>{block.content}</p>
								</div>
							))}
						</div>

						<div className='flex flex-col justify-around gap-8 py-6 lg:flex-row lg:gap-0'>
							{stats.map(stat => (
								<div key={stat.label} className='flex flex-col items-center gap-0'>
									<p className='text-navy-600 font-[lexend] text-[44px] font-medium'>{stat.value}</p>
									<p className='text-navy-800 text-xl'>{stat.label}</p>
								</div>
							))}
						</div>
					</div>
				</InfoCard>
			</div>
		</section>
	)
}
