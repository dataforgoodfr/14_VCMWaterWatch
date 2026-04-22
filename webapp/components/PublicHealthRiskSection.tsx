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
							Vinyl chloride monomer is classified as a Group 1 substance (known carcinogen) by the International Agency
							for Research on Cancer (IARC).
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
								<span className='font-bold'>Hepatic steatosis:</span> “fatty liver” disease
							</li>
						</ul>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Safety levels</p>
						<p className='font-regular text-[20px] text-gray-600'>
							The 1998 EU Directive sets a limit value of 0.5 µg/L for vinyl chloride monomer in drinking water, while
							the World Health Organization recommends a more stringent guideline value of 0.3 µg/L. However, as a
							non-threshold carcinogen, vinyl chloride is considered to have no completely risk-free level of exposure.
						</p>
					</div>
				</div>
			</InfoCard>
		</div>
	)
}
