'use client'

import { useState, useEffect } from 'react'

import { useSearchParams } from 'next/navigation'

import { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { fetchDistributionZoneDetail } from '@/lib/fetchDistributionZoneDetail'
import ActSearchBar from './ActSearchBar'
import ZoneResultPanel from './ZoneResultPanel'

export default function ActSearchSection() {
	const searchParams = useSearchParams()

	// Read initial zone from URL synchronously so we don't need a synchronous
	// setState call inside an effect (satisfies react-hooks/set-state-in-effect).
	const urlZoneParam = searchParams.get('zone')

	const urlZoneId = urlZoneParam !== null && Number.isFinite(Number(urlZoneParam)) ? Number(urlZoneParam) : null

	const [selectedZoneId, setSelectedZoneId] = useState<number | null>(urlZoneId)
	const [zone, setZone] = useState<DistributionZoneDetailRecord | null>(null)
	const [loading, setLoading] = useState(urlZoneId !== null)

	function handleSelect(zoneId: number) {
		setLoading(true)
		setSelectedZoneId(zoneId)
	}

	// Auto-load zone from ?zone= query param (e.g. linked from map tooltip).
	// Also re-fetches whenever the user picks a new zone via the search bar.
	// Only setState is called inside async callbacks — never synchronously in
	// the effect body — to satisfy the react-hooks/set-state-in-effect rule.
	useEffect(() => {
		if (selectedZoneId === null) {
			return
		}

		let cancelled = false

		void fetchDistributionZoneDetail(selectedZoneId)
			.then(detail => {
				if (!cancelled) {
					setZone(detail)
				}
			})
			.catch(() => {
				if (!cancelled) {
					setZone(null)
				}
			})
			.finally(() => {
				if (!cancelled) {
					setLoading(false)
				}
			})

		return () => {
			cancelled = true
		}
	}, [selectedZoneId])

	return (
		<div className='flex w-full flex-col items-center'>
			<ActSearchBar onSelect={handleSelect} />
			<ZoneResultPanel zone={zone} loading={loading} />
		</div>
	)
}
