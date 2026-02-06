import { SearchBar } from '@/components/SearchBar'
// import { fetchPollutionStats, fetchParameterValues } from '../lib/data'
import PollutionMap from '@/components/PollutionMap'

// Mise en cache de la page pour 24 heures
export const revalidate = 86400

export default function Map() {
	// export default async function Map() {
	// const stats = await fetchPollutionStats()
	// const parameterValues = await fetchParameterValues()

	return (
		<div className='h-full w-full'>
			<div> Map Page</div>
			<SearchBar />
			<PollutionMap />
			{/* <PollutionMap pollutionStats={stats} parameterValues={parameterValues} showBanner={false} /> */}
		</div>
	)
}
