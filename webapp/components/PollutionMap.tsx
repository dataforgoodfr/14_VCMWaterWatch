'use client'

import { useState, JSX } from 'react'

import { MapProvider } from 'react-map-gl/maplibre'

import PollutionMapBaseLayer from '@/components/PollutionMapBaseLayer'
// import PollutionMapFilters from '@/components/PollutionMapFilters'
import { MAPLIBRE_MAP } from '@/mapConfig/config'
// import MapZoneSelector from './MapZoneSelector'
// import PollutionMapLegend from './PollutionMapLegend'

// import type { PollutionStats, ParameterValues } from '../lib/data'

export default function PollutionMap({
	// pollutionStats,
	// parameterValues,
	initialCategory = 'cvm'
}: {
	// pollutionStats: PollutionStats
	// parameterValues: ParameterValues
	initialCategory?: string
}) {
	const [period, _setPeriod] = useState('dernier_prel')
	const [category] = useState(initialCategory)
	const [displayMode, _setDisplayMode] = useState<'communes' | 'udis'>('udis')

	const [mapState, setMapState] = useState<{
		longitude: number
		latitude: number
		zoom: number
	}>(MAPLIBRE_MAP.initialViewState)

	const [selectedZoneCode, setSelectedZoneCode] = useState<string | null>(null)

	const [marker, setMarker] = useState<{
		longitude: number
		latitude: number
		content?: JSX.Element
	} | null>(null)

	const [isMobile] = useState(() => {
		if (typeof window !== 'undefined') {
			return window.innerWidth < 768
		}

		return false // Default to false for SSR
	})

	// const [sidePanelOpen, setSidePanelOpen] = useState(() => !isMobile)
	const [colorblindMode, _setColorblindMode] = useState(false)

	// const handleAddressSelect = async (result: FilterResult | null) => {
	// 	if (result) {
	// 		const { center, zoom, address, postcode } = result

	// 		setMapState({ longitude: center[0], latitude: center[1], zoom })
	// 		setMarker({
	// 			longitude: center[0],
	// 			latitude: center[1],
	// 			content: <>{address}</>
	// 		})

	// 		// Detect if we're in a DROM or Metropole based on postcode, and set display mode
	// 		// DROM postcodes: 971 (Guadeloupe), 972 (Martinique), 973 (Guyane), 974 (Réunion), 976 (Mayotte)
	// 		const isInDROM = postcode ? /^97[1234678]/.test(postcode) : false

	// 		setDisplayMode(isInDROM ? 'communes' : 'udis')
	// 	} else {
	// 		setMarker(null)
	// 		setSelectedZoneCode(null)
	// 	}
	// }

	return (
		<div className='flex h-screen w-full flex-col overflow-hidden'>
			<div className='flex min-h-0 flex-1'>
				<MapProvider>
					<div className='h-full w-full'>
						<PollutionMapBaseLayer
							period={period}
							category={category}
							displayMode={displayMode}
							selectedZoneCode={selectedZoneCode}
							setSelectedZoneCode={setSelectedZoneCode}
							mapState={mapState}
							onMapStateChange={setMapState}
							marker={marker}
							setMarker={setMarker}
							colorblindMode={colorblindMode}
							isMobile={isMobile}
							// parameterValues={parameterValues}
						/>

						{/* <div className='absolute top-4 left-4 z-10 flex flex-col gap-1 md:flex-row md:gap-6'>
							<PollutionMapFilters
								period={period}
								setPeriod={setPeriod}
								category={category}
								// setCategory={setCategory}
							/> */}
						{/* <div className='md:hidden'>
								<PollutionMapSearchBox communeInseeCode={selectedZoneCode} onAddressFilter={handleAddressSelect} />
							</div> */}
						{/* </div> */}

						{/* <div className='absolute top-4 right-20 z-9 hidden md:block'>
							<PollutionMapSearchBox communeInseeCode={selectedZoneCode} onAddressFilter={handleAddressSelect} />
						</div> */}

						{/* <div className='absolute top-4 right-4 z-8'>
							<MapZoneSelector setDisplayMode={setDisplayMode} />
						</div> */}

						{/* <div className='absolute bottom-4 left-0 w-full pr-12 pl-4 md:left-4 md:w-auto md:px-0'>
							<PollutionMapLegend
								period={period}
								category={category}
								pollutionStats={pollutionStats}
								colorblindMode={colorblindMode}
								setColorblindMode={setColorblindMode}
								displayMode={displayMode}
								isMobile={isMobile}
							/>
						</div> */}
					</div>
				</MapProvider>
			</div>
		</div>
	)
}
