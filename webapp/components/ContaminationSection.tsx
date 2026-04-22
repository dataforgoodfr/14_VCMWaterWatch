import { CardImage } from './CardImage'

export const ContaminationSection = () => {
	return (
		<div className='py-6'>
			<h3 className='text-navy-800 pt-16 pb-8 font-[lexend] text-[32px] font-semibold'>
				Documented contamination cases
			</h3>
			<div className='flex flex-col items-center gap-12 md:flex-row md:items-start md:justify-between'>
				<CardImage
					img={{ url: '/images/contaminations-usa.jpg', alt: 'Miami, Florida (USA).' }}
					title='Miami, Florida (USA), 1975'
					description='The leaching phenomenon of VCM from contaminated PVC pipes is first identified. The US Environmental Protection Agency identify high levels of VCM in drinking water (5,6 μg/L). Additional contamination cases are subsequently confirmed in the US.'
				/>
				<CardImage
					img={{ url: '/images/contaminations-italie.jpg', alt: 'France.' }}
					title='France, 2010s-2020s'
					description='Systematic VCM analyses reveal contamination in thousands of municipalities across the country, with the highest number of cases observed in Nouvelle-Aquitaine and Normandy. In affected areas, drinking water consumption is restricted and pipes are progressively replaced. However, no nationwide communication campaign is implemented to inform citizens.'
				/>
				<CardImage
					img={{ url: '/images/contaminations-scandales.jpg', alt: 'United Kingdom, Italy, Germany, Sweden, Denmark' }}
					title='United Kingdom, Italy, Germany, Sweden, Denmark, 2010s–2020s'
					description='Sporadic VCM analyses reveal contamination in a limited number of municipalities across Europe. However, no nationwide monitoring campaigns are implemented in these countries.'
				/>
			</div>
		</div>
	)
}
