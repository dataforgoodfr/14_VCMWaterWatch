import Link from 'next/link'

import { ArrowUpRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { InfoCard } from '@/components/InfoCard'
import { SectionSeparator } from '@/components/SectionSeparator'
import { TeamCard } from '@/components/TeamCard'
import { getT } from '@/i18n/server'
import type { Locale } from '@/i18n/i18next.config'
import { fetchTeam } from '@/lib/fetchTeam'
import { SEMI_STATIC_REVALIDATE_SECONDS } from '@/lib/revalidate'

export const revalidate = SEMI_STATIC_REVALIDATE_SECONDS

/** Derive initials from a full name (first + last initial). */
function getInitials(name: string): string {
	const parts = name.trim().split(/\s+/)

	if (parts.length === 1) {
		return parts[0].charAt(0).toUpperCase()
	}

	return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
}

/** Title-case a string, replacing underscores and hyphens with spaces. */
function humanise(value: string): string {
	return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params
	const { t } = await getT('default', { locale: locale as Locale })

	const members = await fetchTeam()

	// Group members by SubTeam, preserving the nc_order-sorted list order so
	// section order = first-seen order across the sorted member list.
	const sectionOrder: string[] = []
	const grouped = new Map<string, typeof members>()

	for (const member of members) {
		const key = member.subTeam ?? '__other__'

		if (!grouped.has(key)) {
			grouped.set(key, [])
			sectionOrder.push(key)
		}

		grouped.get(key)!.push(member)
	}

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

				{sectionOrder.map((subTeamKey, idx) => {
					const i18nKey = subTeamKey === '__other__' ? 'about-team-other' : `about-team-${subTeamKey}`
					// Fall back to a humanised label when the i18n key is missing.
					const rawLabel = subTeamKey === '__other__' ? 'Other' : humanise(subTeamKey)
					const label = t(i18nKey) === i18nKey ? rawLabel : t(i18nKey)
					const subTeamMembers = grouped.get(subTeamKey)!

					return (
						<div key={subTeamKey} className={idx === 0 ? 'mt-8' : 'mt-10'}>
							<h3 className='text-navy-800 mb-4 font-[lexend] text-base font-semibold'>{label}</h3>
							<div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4'>
								{subTeamMembers.map(member => (
									<TeamCard
										key={member.id}
										initials={getInitials(member.name)}
										name={member.name}
										role={member.role}
										imageSrc={member.imageSrc}
									/>
								))}
							</div>
						</div>
					)
				})}
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
