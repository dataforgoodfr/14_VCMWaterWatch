'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

import { Search } from 'lucide-react'

import { Input } from '@/components/ui/input'
import type { GeocodePlace } from '@/lib/geocode/photon'
import { cn } from '@/lib/utils'

const MIN_QUERY_CHARS = 2
const DEBOUNCE_MS = 400

export interface SearchBarProps {
	onSelectPlace: (place: GeocodePlace) => void
}

export function SearchBar({ onSelectPlace }: SearchBarProps) {
	const [query, setQuery] = useState('')
	const [places, setPlaces] = useState<GeocodePlace[]>([])
	const [loading, setLoading] = useState(false)
	const [suggestionsDismissed, setSuggestionsDismissed] = useState(false)
	const requestIdRef = useRef(0)

	const runSearch = useCallback(async (q: string) => {
		const trimmed = q.trim()

		if (trimmed.length < MIN_QUERY_CHARS) {
			setPlaces([])

			return
		}

		const id = ++requestIdRef.current

		setLoading(true)

		try {
			const res = await fetch(`/api/geocode?q=${encodeURIComponent(trimmed)}`)

			let nextPlaces: GeocodePlace[] = []

			if (res.ok) {
				const data = (await res.json()) as { places?: GeocodePlace[] }

				if (Array.isArray(data.places)) {
					nextPlaces = data.places
				}
			}

			if (id !== requestIdRef.current) {
				return
			}

			setPlaces(nextPlaces)
		} catch {
			console.error('Search failed')

			if (id === requestIdRef.current) {
				setPlaces([])
			}
		} finally {
			if (id === requestIdRef.current) {
				setLoading(false)
			}
		}
	}, [])

	useEffect(() => {
		const trimmed = query.trim()

		if (trimmed.length < MIN_QUERY_CHARS) {
			requestIdRef.current += 1
			setPlaces([])
			setLoading(false)

			return
		}

		const t = window.setTimeout(() => {
			void runSearch(query)
		}, DEBOUNCE_MS)

		return () => {
			window.clearTimeout(t)
		}
	}, [query, runSearch])

	useEffect(() => {
		setSuggestionsDismissed(false)
	}, [query])

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault()
		void runSearch(query)
	}

	const hasResults = places.length > 0
	const showEmpty = !loading && query.trim().length >= MIN_QUERY_CHARS && !hasResults
	const showHint = query.trim().length > 0 && query.trim().length < MIN_QUERY_CHARS
	const showSuggestionsPanel = (hasResults || showEmpty) && !suggestionsDismissed

	const handleSelectPlace = (place: GeocodePlace) => {
		setSuggestionsDismissed(true)
		setPlaces([])
		onSelectPlace(place)
	}

	return (
		<div className='relative w-full'>
			<form onSubmit={handleSubmit} className='w-full'>
				<div className='relative'>
					<Search
						className='text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2'
						aria-hidden
					/>
					<Input
						type='search'
						placeholder='Search for a municipality…'
						value={query}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
						autoComplete='off'
						className='border-navy-100 h-11 bg-white py-2 pr-3 pl-9 shadow-none'
					/>
				</div>
			</form>

			{showHint && (
				<p className='text-muted-foreground mt-1.5 px-0.5 text-xs'>Enter at least {MIN_QUERY_CHARS} characters.</p>
			)}

			{showSuggestionsPanel && (
				<ul
					className='border-navy-100 absolute top-full right-0 left-0 z-20 mt-1 max-h-72 overflow-y-auto rounded-md border bg-white text-sm shadow-none'
					role='listbox'
				>
					{places.map(place => (
						<li key={place.id}>
							<button
								type='button'
								className={cn(
									'hover:bg-muted/80 w-full px-3 py-2 text-left transition-colors',
									'focus-visible:ring-ring focus-visible:ring-2 focus-visible:outline-none'
								)}
								onClick={() => handleSelectPlace(place)}
							>
								{place.displayName}
							</button>
						</li>
					))}

					{showEmpty && <li className='text-muted-foreground px-3 py-4 text-center'>No results for this search.</li>}
				</ul>
			)}
		</div>
	)
}
