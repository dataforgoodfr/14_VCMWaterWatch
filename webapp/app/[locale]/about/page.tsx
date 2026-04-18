import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { InfoCard } from '@/components/InfoCard'
import { SectionSeparator } from '@/components/SectionSeparator'
import { TeamCard } from '@/components/TeamCard'
import { getT } from '@/i18n/server'
import type { Locale } from '@/i18n/i18next.config'

interface TeamMember {
	id: string
	initials: string
	name: string
	role: string
	color: 'teal' | 'green' | 'purple' | 'navy'
}

const teams: { labelKey: string; members: TeamMember[] }[] = [
	{
		labelKey: 'about-team-product',
		members: [
			{
				id: 'ml-prod',
				initials: 'ML',
				name: 'Marie Laurent',
				role: 'Scientific Director\nHydrogeology, CNRS',
				color: 'teal'
			},
			{
				id: 'kd-prod',
				initials: 'KD',
				name: 'Karim Diouf',
				role: 'Lead Developer\nData & Cartography',
				color: 'green'
			},
			{
				id: 'sv-prod',
				initials: 'SV',
				name: 'Sofia Vasquez',
				role: 'Network Coordinator\nAssociation Relations',
				color: 'purple'
			},
			{ id: 'tm-prod', initials: 'TM', name: 'Thomas Müller', role: 'Policy Analyst\nEU Regulation', color: 'navy' }
		]
	},
	{
		labelKey: 'about-team-legal',
		members: [
			{
				id: 'ml-legal',
				initials: 'ML',
				name: 'Marie Laurent',
				role: 'Scientific Director\nHydrogeology, CNRS',
				color: 'teal'
			},
			{
				id: 'kd-legal',
				initials: 'KD',
				name: 'Karim Diouf',
				role: 'Lead Developer\nData & Cartography',
				color: 'green'
			},
			{
				id: 'sv-legal',
				initials: 'SV',
				name: 'Sofia Vasquez',
				role: 'Network Coordinator\nAssociation Relations',
				color: 'purple'
			},
			{ id: 'tm-legal', initials: 'TM', name: 'Thomas Müller', role: 'Policy Analyst\nEU Regulation', color: 'navy' }
		]
	}
]

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params
	const { t } = await getT('default', { locale: locale as Locale })

	return (
		<main className='flex min-h-screen flex-col'>
			{/* Header */}
			<div className='container mx-auto px-4 pt-16 md:px-8'>
				<h1 className='text-navy-800 font-[lexend] text-3xl font-semibold'>{t('about-title')}</h1>
				<p className='text-navy-600 mt-2 text-lg'>{t('about-subtitle')}</p>
				<div className='mt-6'>
					<SectionSeparator />
				</div>
			</div>

			{/* Description Card */}
			<section className='container mx-auto px-4 py-12 md:px-8'>
				<InfoCard>
					<div className='flex flex-col gap-4'>
						<p className='text-navy-800 text-base leading-relaxed'>{t('about-description-p1')}</p>
						<p className='text-navy-800 text-base leading-relaxed'>{t('about-description-p2')}</p>
						<p className='text-navy-800 text-base leading-relaxed'>{t('about-description-p3')}</p>
					</div>
				</InfoCard>
			</section>

			{/* Team Section */}
			<section className='container mx-auto px-4 pb-12 md:px-8'>
				<h2 className='text-navy-800 font-[lexend] text-2xl font-semibold'>{t('about-team-title')}</h2>

				{teams.map((team, idx) => (
					<div key={team.labelKey} className={idx === 0 ? 'mt-8' : 'mt-10'}>
						<h3 className='text-navy-800 mb-4 font-[lexend] text-base font-semibold'>{t(team.labelKey)}</h3>
						<div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4'>
							{team.members.map(member => (
								<TeamCard key={member.id} {...member} />
							))}
						</div>
					</div>
				))}
			</section>

			{/* Join CTA */}
			<section className='container mx-auto px-4 pb-16 md:px-8'>
				<div className='bg-navy-50 flex flex-col items-start justify-between gap-6 rounded-2xl border border-gray-200 px-8 py-6 sm:flex-row sm:items-center'>
					<div>
						<h3 className='text-navy-800 font-[lexend] text-lg font-semibold'>{t('about-join-title')}</h3>
						<p className='text-navy-600 mt-1 text-base'>{t('about-join-description')}</p>
					</div>
					<Button
						asChild
						className='bg-aqua-600 hover:bg-aqua-700 shrink-0 rounded-xl px-6 py-3 font-semibold text-white'
					>
						<Link href='mailto:contact@vcm-watch.eu'>
							{t('about-join-cta')} <ArrowUpRight className='ml-1 size-4' />
						</Link>
					</Button>
				</div>
			</section>
		</main>
	)
}
