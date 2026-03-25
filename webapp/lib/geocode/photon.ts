export interface GeocodePlace {
	id: string
	displayName: string
	west: number
	south: number
	east: number
	north: number
}

interface PhotonProperties {
	osm_id?: number
	osm_type?: string
	name?: string
	street?: string
	housenumber?: string
	city?: string
	district?: string
	state?: string
	country?: string
	postcode?: string
	extent?: number[]
}

interface PhotonFeature {
	type: 'Feature'
	geometry: {
		type: 'Point'
		coordinates: [number, number]
	}
	properties?: PhotonProperties
}

interface PhotonResponse {
	type: 'FeatureCollection'
	features?: PhotonFeature[]
}

function boundsFromLatLon(lat: number, lon: number, marginDeg = 0.08) {
	const west = lon - marginDeg
	const east = lon + marginDeg
	const south = lat - marginDeg
	const north = lat + marginDeg

	return { west, south, east, north }
}

function buildDisplayName(p: PhotonProperties): string {
	const line1 = [p.housenumber, p.street].filter(Boolean).join(' ').trim()

	const parts = [
		p.name,
		line1 || undefined,
		p.city && p.city !== p.name ? p.city : undefined,
		p.district,
		p.state,
		p.country
	].filter((x): x is string => Boolean(x?.trim()))

	const deduped = [...new Set(parts)]
	const joined = deduped.join(', ')

	return joined !== '' ? joined : (p.name ?? 'Place')
}

function parsePhotonFeature(feature: PhotonFeature, index: number): GeocodePlace | null {
	const coords = feature.geometry?.coordinates

	if (!coords || coords.length < 2) {
		return null
	}

	const lon = coords[0]
	const lat = coords[1]

	if (Number.isNaN(lat) || Number.isNaN(lon)) {
		return null
	}

	const p = feature.properties ?? {}

	const id =
		p.osm_id != null && p.osm_type != null ? `photon-${p.osm_type}-${p.osm_id}` : `photon-${index}-${lat}-${lon}`

	let west: number
	let south: number
	let east: number
	let north: number
	const ext = p.extent

	if (Array.isArray(ext) && ext.length >= 4) {
		;[west, south, east, north] = ext.map(Number)

		if ([west, south, east, north].some(n => Number.isNaN(n))) {
			const b = boundsFromLatLon(lat, lon)

			;({ west, south, east, north } = b)
		}
	} else {
		const b = boundsFromLatLon(lat, lon)

		;({ west, south, east, north } = b)
	}

	return {
		id,
		displayName: buildDisplayName(p),
		west,
		south,
		east,
		north
	}
}

export async function searchPhoton(query: string, baseUrl: string, lang: string): Promise<GeocodePlace[]> {
	const trimmed = query.trim()

	if (!trimmed) {
		return []
	}

	const origin = baseUrl.replace(/\/$/, '')
	const url = new URL(`${origin}/api/`)

	url.searchParams.set('q', trimmed)
	url.searchParams.set('limit', '8')
	url.searchParams.set('lang', lang)

	const res = await fetch(url.toString(), {
		cache: 'no-store',
		headers: {
			Accept: 'application/json',
			'User-Agent': 'VCMWaterWatch/1.0 (photon geocode)'
		}
	})

	if (!res.ok) {
		throw new Error(`Photon HTTP ${res.status}`)
	}

	const raw = (await res.json()) as PhotonResponse
	const features = raw.features

	if (!Array.isArray(features)) {
		return []
	}

	const out: GeocodePlace[] = []

	features.forEach((feature, index) => {
		if (feature.type !== 'Feature' || feature.geometry?.type !== 'Point') {
			return
		}

		const place = parsePhotonFeature(feature, index)

		if (place) {
			out.push(place)
		}
	})

	return out
}
