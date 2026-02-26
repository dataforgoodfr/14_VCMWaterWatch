export const InfoSection = () => {
	return (
		<section className='w-full bg-gray-50 py-16 md:py-24'>
			<div className='container mx-auto px-4 md:px-8'>
				¨{/* CARD */}
				<div className='bg-navy-100 border-navy-800 rounded-r-2xl border-l-[6px] px-8 py-8.5'>
					<div className='flex flex-col gap-4'>
						<h3 className='text-navy-800 font-[lexend] text-[32px] font-semibold'>Qu&apos;est-ce que le CVM ?</h3>

						<div className='flex flex-col justify-between gap-18 lg:flex-row'>
							<div className='flex flex-1 flex-col gap-2.5'>
								<p className='text-navy-800 font-[lexend] text-2xl font-medium'>Le problème</p>
								<p className='text-navy-800 text-xl'>
									Classé cancérigène certain (groupe 1) par le CIRC, il est associé à des risques d&apos;angiosarcome
									hépatique et de carcinome hépatocellulaire. Le chlorure de vinyle monomère (CVM ou VCM) est un composé
									chimique hautement cancérigène qui peut contaminer l&apos;eau potable via les canalisations en PVC
									vieillissantes.
								</p>
							</div>

							<div className='flex flex-1 flex-col gap-2.5'>
								<p className='text-navy-800 font-[lexend] text-2xl font-medium'>Les enjeux</p>
								<p className='text-navy-800 text-xl'>
									Des millions de kilomètres de canalisations en PVC sont installés en Europe, dont une partie
									significative approche de sa fin de vie. La transparence des données reste inégale entre pays, rendant
									difficile l&apos;évaluation précise des risques pour les populations.
								</p>
							</div>
						</div>

						<div className='flex flex-col justify-around gap-8 py-6 lg:flex-row lg:gap-0'>
							<div className='flex flex-col items-center gap-0'>
								<p className='text-navy-600 font-[lexend] text-[44px] font-medium'>275 000 km</p>
								<p className='text-navy-800 text-xl'>de canalisation</p>
							</div>

							<div className='flex flex-col items-center gap-0'>
								<p className='text-navy-600 font-[lexend] text-[44px] font-medium'>12 pays</p>
								<p className='text-navy-800 text-xl'>européens</p>
							</div>

							<div className='flex flex-col items-center gap-0'>
								<p className='text-navy-600 font-[lexend] text-[44px] font-medium'>XXX</p>
								<p className='text-navy-800 text-xl'>de personnes impactées</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>
	)
}
