import { InfoCard } from '@/components/InfoCard'

export const InfoSection = () => {
	const blocks = [
		{
			label: 'The issue',
			content:
				'Classified as a known human carcinogen (Group 1) by the International Agency for Research on Cancer, vinyl chloride is associated with an increased risk of hepatic angiosarcoma and hepatocellular carcinoma, two forms of liver cancer. Vinyl chloride monomer (VCM) can leach into drinking water from PVC pipes installed before 1980. Although the European Union established a regulatory limit of 0.5 μg/L in 1998, monitoring of this substance is not systematically required, creating a significant blind spot in water quality surveillance.'
		},
		{
			label: 'Why it matters',
			content:
				'Hundreds of thousands of kilometers of pre-1980 PVC pipes remain in use across Europe. In France, where systematic monitoring was introduced in 2012, more than 5,000 municipalities have reported VCM concentrations exceeding the EU threshold, in some cases reaching several hundred μg/L. In other European countries, where legacy PVC infrastructure is also known to exist, no comparable monitoring programs are in place, -leaving potential contamination largely undetected.'
		}
	]

	const stats = [
		{ value: '< 300,000 km', label: 'of piping' },
		{ value: '16 countries', label: 'at risk' },
		{ value: '6 countries', label: 'with identified contamination' }
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
