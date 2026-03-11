import { TriangleAlert } from 'lucide-react'

import { InfoCard } from './InfoCard'

export const PubliHealthRiskSection = () => {
	return (
		<div className='pt-10 pb-24'>
			<InfoCard>
				<div className='flex flex-col gap-8'>
					<div className='flex items-center gap-2'>
						<TriangleAlert className='text-navy-800' size={30} />
						<p className='text-navy-800 font-[lexend] text-[32px] font-semibold'>Risques sanitaires</p>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Classification</p>
						<p className='font-regular text-[20px] text-gray-600'>
							Le chlorure de vinyle monomère est classé dans le Groupe 1 par le Centre International de Recherche sur le
							Cancer (CIRC) : cancérigène certain pour l&apos;homme.
						</p>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Pathologies associées</p>
						<ul className='list-disc px-6'>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Angiosarcome hépatique :</span> cancer rare du foie, fortement corrélé à
								l&apos;exposition au CVM
							</li>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Carcinome hépatocellulaire :</span> forme plus commune de cancer du foie
							</li>
							<li className='font-regular text-[20px] text-gray-600'>
								<span className='font-bold'>Autres risques :</span> troubles neurologiques, atteintes vasculaires
								périphériques (syndrome de Raynaud)
							</li>
						</ul>
					</div>

					<div>
						<p className='text-navy-500 font-[lexend] text-[24px] font-medium'>Niveaux de sécurité</p>
						<p className='font-regular text-[20px] text-gray-600'>
							La directive européenne fixe une limite de 0,5 µg/L dans l&apos;eau potable. Cependant, le caractère
							cancérigène du CVM implique qu&apos;il n&apos;existe pas de seuil d&apos;exposition sans risque.
						</p>
					</div>
				</div>
			</InfoCard>
		</div>
	)
}
