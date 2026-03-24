import { Map, Megaphone, Flag } from 'lucide-react'

import { ActionCard } from './ActionCard'

export const CardsSection = () => {
	const cards = [
		{
			icon: Map,
			title: 'Interactive map',
			description: 'Explore data by region, city, or water utility. Review analyses and action plans.',
			buttonText: 'Open the map',
			href: '/map'
		},
		{
			icon: Flag,
			title: 'Country profiles',
			description: 'Browse national data, applicable legislation, and contribution history.',
			buttonText: 'View countries',
			href: '/country-profile'
		},
		{
			icon: Megaphone,
			title: 'Take action',
			description: 'Reach out to decision-makers, contribute data, or join our volunteer community.',
			buttonText: 'Get involved',
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
