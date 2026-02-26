import { Map, Megaphone, Flag } from 'lucide-react'

import { ActionCard } from './ActionCard'

export const CardsSection = () => {
	const cards = [
		{
			icon: Map,
			title: 'Carte interactive',
			description:
				"Explorez les données par région, ville ou compagnie d'eau. Consultez les analyses et plans d'action.",
			buttonText: 'Accéder à la carte',
			href: '/map'
		},
		{
			icon: Flag,
			title: 'Fiches pays',
			description: "Consultez les données nationales, la législation en vigueur et l'historique des contributions.",
			buttonText: 'Voir les pays',
			href: '/country-profile'
		},
		{
			icon: Megaphone,
			title: 'Agir',
			description: 'Contactez vos décideurs, contribuez aux données ou rejoignez notre communauté de bénévoles.',
			buttonText: "Passer à l'action",
			href: '/act'
		}
	]

	return (
		<section className='bg-white py-6'>
			<div className='container mx-auto px-4 md:px-8'>
				<div className='grid grid-cols-1 gap-8 md:grid-cols-3'>
					{cards.map((card, index) => (
						<ActionCard key={index} {...card} />
					))}
				</div>
			</div>
		</section>
	)
}
