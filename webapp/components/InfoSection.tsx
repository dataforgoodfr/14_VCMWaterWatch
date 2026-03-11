import { InfoCard } from '@/components/InfoCard'

export const InfoSection = () => {
	const blocks = [
		{
			label: 'Le problème',
			content:
				"Classé cancérigène certain (groupe 1) par le CIRC, il est associé à des risques d'angiosarcome hépatique et de carcinome hépatocellulaire. Le chlorure de vinyle monomère (CVM ou VCM) est un composé chimique hautement cancérigène qui peut contaminer l'eau potable via les canalisations en PVC vieillissantes."
		},
		{
			label: 'Les enjeux',
			content:
				"Des millions de kilomètres de canalisations en PVC sont installés en Europe, dont une partie significative approche de sa fin de vie. La transparence des données reste inégale entre pays, rendant difficile l'évaluation précise des risques pour les populations."
		}
	]

	const stats = [
		{ value: '275 000 km', label: 'de canalisation' },
		{ value: '12 pays', label: 'européens' },
		{ value: 'XXX', label: 'de personnes impactées' }
	]

	return (
		<section className='w-full bg-gray-50 py-16 md:py-24'>
			<div className='container mx-auto px-4 md:px-8'>
				<InfoCard>
					<div className='flex flex-col gap-4'>
						<h3 className='text-navy-800 font-[lexend] text-[32px] font-semibold'>Qu&apos;est-ce que le CVM ?</h3>
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
