'use client'

import { useState, useEffect, useRef } from 'react'

import { DistributionZoneGeoLimitedRecord } from '@/types/apiTypes'

interface ActSearchBarProps {
	onSelect: (zoneId: number) => void
}

export default function ActSearchBar({ onSelect }: ActSearchBarProps) {
	const [query, setQuery] = useState('')
	const [results, setResults] = useState<DistributionZoneGeoLimitedRecord[]>([])
	const [loading, setLoading] = useState(false)
	const [open, setOpen] = useState(false)
	const containerRef = useRef<HTMLDivElement>(null)
	const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

	useEffect(() => {
		if (debounceRef.current) {
			clearTimeout(debounceRef.current)
		}

		if (query.length < 3) {
			setResults([])
			setOpen(false)
			return
		}

		debounceRef.current = setTimeout(() => {
			void (async () => {
				setLoading(true)

				try {
					const res = await fetch(`/api/searchbydistributionzone?q=${encodeURIComponent(query)}`)
					const data = (await res.json()) as DistributionZoneGeoLimitedRecord[] | null

					setResults(data ?? [])
					setOpen(true)
				} catch {
					setResults([])
				} finally {
					setLoading(false)
				}
			})()
		}, 300)

		return () => {
			if (debounceRef.current) {
				clearTimeout(debounceRef.current)
			}
		}
	}, [query])

	// Close on click outside
	useEffect(() => {
		function handleClick(e: MouseEvent) {
			if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
				setOpen(false)
			}
		}

		document.addEventListener('mousedown', handleClick)
		return () => document.removeEventListener('mousedown', handleClick)
	}, [])

	return (
		<div ref={containerRef} className='relative w-full max-w-xl'>
			<input
				type='text'
				value={query}
				onChange={e => setQuery(e.target.value)}
				onKeyDown={e => e.key === 'Escape' && setOpen(false)}
				placeholder='Enter your city, postal code, or water company...'
				className='w-full rounded-lg border border-gray-300 px-4 py-3 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none'
			/>

			{open && (
				<div className='absolute z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg'>
					{loading && <div className='px-4 py-3 text-sm text-gray-500'>Searching...</div>}
					{!loading && results.length === 0 && <div className='px-4 py-3 text-sm text-gray-500'>No results</div>}
					{!loading &&
						results.map(zone => (
							<button
								key={zone.id}
								className='block w-full px-4 py-3 text-left first:rounded-t-lg last:rounded-b-lg hover:bg-gray-50'
								onClick={() => {
									onSelect(zone.id)
									setQuery(zone.fields.Name)
									setOpen(false)
								}}
							>
								<div className='text-sm font-medium text-gray-900'>
									{zone.fields.Name}
									{zone.fields.Country && (
										<span className='ml-2 text-gray-500'>— {zone.fields.Country.fields.Name}</span>
									)}
								</div>
								{zone.fields.ActorName && zone.fields.ActorName.length > 0 && (
									<div className='text-xs text-gray-400'>{zone.fields.ActorName.join(', ')}</div>
								)}
							</button>
						))}
				</div>
			)}
		</div>
	)
}
