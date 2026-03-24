'use client'

import { useState } from 'react'

import { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { fetchDistributionZoneDetail } from '@/lib/fetchDistributionZoneDetail'
import ActSearchBar from './ActSearchBar'
import ZoneResultPanel from './ZoneResultPanel'

export default function ActSearchSection() {
	const [zone, setZone] = useState<DistributionZoneDetailRecord | null>(null)
	const [loading, setLoading] = useState(false)

	function handleSelect(zoneId: number) {
		setLoading(true)

		void fetchDistributionZoneDetail(zoneId)
			.then(detail => {
				setZone(detail)
			})
			.catch(() => {
				setZone(null)
			})
			.finally(() => {
				setLoading(false)
			})
	}

	return (
		<div>
			<h2 className='text-navy-800 mb-4 font-[lexend] text-2xl font-semibold'>Find your distribution zone</h2>
			<ActSearchBar onSelect={handleSelect} />
			<ZoneResultPanel zone={zone} loading={loading} />
		</div>
	)
}
