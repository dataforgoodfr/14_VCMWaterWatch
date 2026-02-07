'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Field } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { DistributionZoneGeoLimitedRecord } from '@/types/apiTypes'

export function SearchBar() {
	const [query, setQuery] = useState('')
	const [results, setResults] = useState<DistributionZoneGeoLimitedRecord[]>([])
	const [, setLoading] = useState(false)

	const handleSearch = async () => {
		if (!query) {
			return
		}

		setLoading(true)

		try {
			const res = await fetch(`/api/searchbydistributionzone?q=${encodeURIComponent(query)}`)
			const data = (await res.json()) as DistributionZoneGeoLimitedRecord[]

			setResults(data || [])
		} catch (error) {
			console.error('Search failed', error)
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className='p-4'>
			<form
				onSubmit={e => {
					e.preventDefault()
					void handleSearch()
				}}
				className='flex gap-2'
			>
				<Field orientation='horizontal'>
					<Input
						type='search'
						placeholder='Search...'
						value={query}
						onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
					/>
					<Button type='submit'>Search</Button>
				</Field>
			</form>
			<ul className='mt-4'>
				{results.map(item => (
					<li key={item.id} className='border-b py-2'>
						{item.fields.Name}, {item.fields.Country.fields.Name}
					</li>
				))}
			</ul>
		</div>
	)
}
