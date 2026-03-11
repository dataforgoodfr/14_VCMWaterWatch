import { CardImage } from './CardImage'

export const ContaminationSection = () => {
	return (
		<div className='py-6'>
			<h3 className='text-navy-800 pt-16 pb-8 font-[lexend] text-[32px] font-semibold'>
				Exemples de contaminations documentées
			</h3>
			<div className='flex flex-col gap-12 md:flex-row'>
				<CardImage
					img={{ url: '/images/contaminations-usa.jpg', alt: 'Photo de LouisVille, Kentucky, USA.' }}
					title='Cas de Louisville, Kentucky (USA), 2004'
					description="Détection de niveaux élevés de CVM dans plusieurs quartiers alimentés par des canalisations PVC installées dans les années 1970. Remplacement d'urgence de 12 km de réseau."
				/>
				<CardImage
					img={{ url: '/images/contaminations-italie.jpg', alt: 'Photo de la région de Campanie, Italie.' }}
					title='Région de Campanie, Italie, 2008'
					description='Contamination massive liée à des canalisations PVC dégradées. Étude épidémiologique révélant une incidence accrue de pathologies hépatiques dans les zones concernées.'
				/>
				<CardImage
					img={{ url: '/images/contaminations-scandales.jpg', alt: "Photo en noir et blanc d'une usine." }}
					title='Scandales industriels, années 1970-1990'
					description="Plusieurs cas d'angiosarcomes hépatiques chez des travailleurs de l'industrie du PVC en Europe et aux États-Unis ont alerté sur la toxicité du CVM."
				/>
			</div>
		</div>
	)
}
