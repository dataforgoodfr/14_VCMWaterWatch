import type { GeoJSONMultiPolygon, GeoJSONPolygon, CountryMapRecord, DistributionZoneMapRecord } from '@/types/apiTypes'
import { fetchCountriesForMap, fetchDistributionZonesForMap } from '@/lib/fetchDistributionZones'

export interface MapData {
	zones: DistributionZoneMapRecord[]
	countries: CountryMapRecord[]
}

export async function fetchMapData(): Promise<MapData> {
	return {
		zones: (await fetchDistributionZonesForMap()) ?? [],
		countries: (await fetchCountriesForMap()) ?? []
	}
}

export function getGeometryFromRecord(
	r: DistributionZoneMapRecord | CountryMapRecord
): (GeoJSONPolygon | GeoJSONMultiPolygon)[] {
	const fields = r.fields as unknown as Record<string, unknown>
	const geometryStr = (fields.Geometry as string) ?? (fields.geometry as string) ?? ''
	const municipalityGeoms = (fields['Municipality Geometries'] as string[] | undefined) ?? []

	const results: (GeoJSONPolygon | GeoJSONMultiPolygon)[] = []

	if (geometryStr) {
		try {
			const geom = JSON.parse(geometryStr) as GeoJSONPolygon | GeoJSONMultiPolygon

			if (geom?.type === 'Polygon' || geom?.type === 'MultiPolygon') {
				results.push(geom)
			}
		} catch {
			/* ignore */
		}
	}

	for (const str of municipalityGeoms) {
		if (typeof str !== 'string') {
			continue
		}

		try {
			const geom = JSON.parse(str) as GeoJSONPolygon | GeoJSONMultiPolygon

			if (geom?.type === 'Polygon' || geom?.type === 'MultiPolygon') {
				results.push(geom)
			}
		} catch {
			/* ignore */
		}
	}

	return results
}

export function recordsToGeoJSON(zoneRecords: DistributionZoneMapRecord[], countryRecords: CountryMapRecord[]) {
	const features: {
		type: 'Feature'
		geometry: GeoJSONPolygon | GeoJSONMultiPolygon
		properties: Record<string, unknown>
	}[] = []

	for (const r of zoneRecords) {
		const geometries = getGeometryFromRecord(r)
		const fields = r.fields as unknown as Record<string, unknown>
		const country = (r.fields as { Country?: { fields?: { Name?: string } } }).Country

		const props = {
			id: r.id,
			layer: 'zone',
			name: fields.Name ?? '',
			country: country?.fields?.Name ?? '',
			vcmLevel: fields['VCM Level'],
			pvcLevel: fields['PVC Level']
		}

		for (const geometry of geometries) {
			features.push({ type: 'Feature', geometry, properties: props })
		}
	}

	for (const r of countryRecords) {
		const geometries = getGeometryFromRecord(r)
		const fields = r.fields as unknown as Record<string, unknown>

		const props = {
			id: r.id,
			layer: 'country',
			name: fields.Name ?? '',
			country: fields.Name ?? '',
			vcmLevel: fields['VCM Level'],
			pvcLevel: fields['PVC Level']
		}

		for (const geometry of geometries) {
			features.push({ type: 'Feature', geometry, properties: props })
		}
	}

	return {
		type: 'FeatureCollection' as const,
		features
	}
}
