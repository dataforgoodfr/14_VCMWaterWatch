import { TriangleAlert } from 'lucide-react'

import { InfoCard } from './InfoCard'

export const PubliHealthRiskSection = () => {
	return (
		<div className='pt-10 pb-24'>
			<InfoCard>
				<div className='flex flex-col gap-8'>
					<div className='flex items-center gap-2'>
						<TriangleAlert className='text-navy-800' size={30} />
						<p className='text-navy-800 font-[lexend] text-[32px] font-semibold'>Health risks</p>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Classification</p>
						<p className='font-regular text-[20px] text-gray-600'>
							Vinyl chloride monomer is classified in Group 1 by the International Agency for Research on Cancer (IARC):
							definite human carcinogen.
						</p>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Associated conditions</p>
						<ul className='list-disc px-6'>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Hepatic angiosarcoma:</span> rare liver cancer strongly linked to VCM
								exposure
							</li>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Hepatocellular carcinoma:</span> more common form of liver cancer
							</li>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Other risks:</span> neurological effects and peripheral vascular issues
								(e.g. Raynaud&apos;s phenomenon)
							</li>
						</ul>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Safety levels</p>
						<p className='font-regular text-[20px] text-gray-600'>
							The EU directive sets a limit of 0.5 µg/L in drinking water. However, because VCM is carcinogenic, there
							is no exposure threshold considered risk-free.
						</p>
					</div>
				</div>
			</InfoCard>
		</div>
	)
}
