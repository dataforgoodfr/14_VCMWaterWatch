declare module 'react-map-gl/maplibre' {
	import type {
		Map as MaplibreMap,
		MapLayerMouseEvent,
		MapLibreEvent,
	} from 'maplibre-gl'
	import type { FC } from 'react'

	export interface MapRef {
		getMap(): MaplibreMap
		getCenter(): { lng: number; lat: number }
		getZoom(): number
		getBounds(): unknown
		flyTo(options: Record<string, unknown>): void
		easeTo(options: Record<string, unknown>): void
		fitBounds(bounds: unknown, options?: Record<string, unknown>): void
	}

	export interface ViewState {
		longitude: number
		latitude: number
		zoom: number
		bearing?: number
		pitch?: number
		padding?: { top: number; bottom: number; left: number; right: number }
	}

	export interface ViewStateChangeEvent {
		viewState: ViewState
		target: MaplibreMap
		originalEvent?: Event
	}

	export interface MapProps {
		id?: string
		initialViewState?: Partial<ViewState>
		style?: React.CSSProperties
		mapStyle?: string | object
		mapLib?: unknown
		cursor?: string
		onLoad?: (e: MapLibreEvent) => void
		onMove?: (e: ViewStateChangeEvent) => void
		onMoveEnd?: (e: ViewStateChangeEvent) => void
		onClick?: (e: MapLayerMouseEvent) => void
		onMouseEnter?: (e: MapLayerMouseEvent) => void
		onMouseLeave?: (e: MapLayerMouseEvent) => void
		onMouseMove?: (e: MapLayerMouseEvent) => void
		interactiveLayerIds?: string[]
		ref?: React.Ref<MapRef>
		children?: React.ReactNode
		[key: string]: unknown
	}

	const Map: FC<MapProps>
	export default Map

	export const Source: FC<Record<string, unknown>>
	export const Layer: FC<Record<string, unknown>>
	export const Marker: FC<Record<string, unknown>>
	export const Popup: FC<Record<string, unknown>>
	export const NavigationControl: FC<Record<string, unknown>>
	export const ScaleControl: FC<Record<string, unknown>>
	export const GeolocateControl: FC<Record<string, unknown>>
	export const FullscreenControl: FC<Record<string, unknown>>
	export const AttributionControl: FC<Record<string, unknown>>
	export function useControl<T>(create: () => T, options?: Record<string, unknown>): T
}
