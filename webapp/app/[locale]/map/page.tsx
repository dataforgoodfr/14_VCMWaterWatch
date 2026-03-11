import { MapView } from '@/components/MapView'
import { fetchMapData } from '@/lib/map/mapData'

export default async function MapPage() {
	const data = await fetchMapData()

	return <MapView initialData={data} />
}
