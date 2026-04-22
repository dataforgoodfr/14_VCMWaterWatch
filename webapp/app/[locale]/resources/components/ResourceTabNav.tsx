'use client'

import { useEffect, useState } from 'react'

import Link from 'next/link'

import { cn } from '@/lib/utils'

const TABS = [
	{ id: 'resources', label: 'Resources' },
	{ id: 'methodology', label: 'Methodology' }
] as const

type TabId = (typeof TABS)[number]['id']

export default function ResourceTabNav() {
	const [activeTab, setActiveTab] = useState<TabId>('resources')

	useEffect(() => {
		const observers: IntersectionObserver[] = []

		// Track which sections are intersecting and pick the topmost one
		const intersecting = new Set<TabId>()

		TABS.forEach(({ id }) => {
			const el = document.getElementById(id)

			if (!el) {
				return
			}

			const observer = new IntersectionObserver(
				([entry]) => {
					if (entry.isIntersecting) {
						intersecting.add(id)
					} else {
						intersecting.delete(id)
					}

					// Set active to the first tab whose section is visible
					const firstVisible = TABS.find(t => intersecting.has(t.id))

					if (firstVisible) {
						setActiveTab(firstVisible.id)
					}
				},
				{ rootMargin: '-20% 0px -60% 0px', threshold: 0 }
			)

			observer.observe(el)
			observers.push(observer)
		})

		return () => {
			observers.forEach(o => o.disconnect())
		}
	}, [])

	return (
		<nav className='border-navy-200 sticky top-0 z-10 border-b bg-white backdrop-blur-sm'>
			<div className='container mx-auto flex gap-1 px-2'>
				{TABS.map(tab => (
					<Link
						key={tab.id}
						href={`#${tab.id}`}
						onClick={() => setActiveTab(tab.id)}
						aria-current={activeTab === tab.id ? 'true' : undefined}
						className={cn(
							'px-5 py-4 font-[lexend] text-sm font-medium transition-colors',
							activeTab === tab.id
								? 'border-aqua-400 text-medium border-b-[3px]'
								: 'text-navy-600 hover:bg-navy-100 hover:text-navy-800'
						)}
					>
						{tab.label}
					</Link>
				))}
			</div>
		</nav>
	)
}
