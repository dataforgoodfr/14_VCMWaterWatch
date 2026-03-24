import { CardImage } from './CardImage'

export const ContaminationSection = () => {
	return (
		<div className='py-6'>
			<h3 className='text-navy-800 pt-16 pb-8 font-[lexend] text-[32px] font-semibold'>
				Documented contamination examples
			</h3>
			<div className='flex flex-col gap-12 md:flex-row'>
				<CardImage
					img={{ url: '/images/contaminations-usa.jpg', alt: 'Louisville, Kentucky, USA.' }}
					title='Louisville, Kentucky (USA), 2004'
					description='High VCM levels detected in several neighborhoods served by PVC pipes installed in the 1970s. Emergency replacement of 12 km of network.'
				/>
				<CardImage
					img={{ url: '/images/contaminations-italie.jpg', alt: 'Campania region, Italy.' }}
					title='Campania region, Italy, 2008'
					description='Large-scale contamination linked to degraded PVC pipes. Epidemiological study showing increased liver disease incidence in affected areas.'
				/>
				<CardImage
					img={{ url: '/images/contaminations-scandales.jpg', alt: 'Black-and-white photo of an industrial plant.' }}
					title='Industrial scandals, 1970s–1990s'
					description='Multiple cases of hepatic angiosarcoma among PVC industry workers in Europe and the United States highlighted VCM toxicity.'
				/>
			</div>
		</div>
	)
}
