export interface ThumbnailType {
	signedUrl: string
}

export interface ImageThumbnails {
	tiny?: ThumbnailType
	small?: ThumbnailType
	card_cover?: ThumbnailType
	[key: string]: ThumbnailType | undefined
}

export interface NocoDBImage {
	url: string
	title: string
	mimetype: string
	size: number
	width: number
	height: number
	id: string
	thumbnails: ImageThumbnails
	signedUrl: string
}

export type TableTitle =
	| 'Actor'
	| 'Interaction'
	| 'Analysis'
	| 'Attachment'
	| 'ContactPerson'
	| 'Page'
	| 'PageField'
	| 'Translation'
	| 'Country'
	| 'CountryData'
	| 'DistributionZone'
	| 'Municipality'
	| 'BlogPost'
	| 'Contribution'
	| 'Volunteer'
	| 'LetterTemplate'
	| 'Members'

export interface MetaTable {
	id: string
	source_id?: string | null
	base_id?: string | null
	table_name?: string
	title?: TableTitle
	type?: string
	meta?: {
		hasNonDefaultViews?: boolean
	} | null
	schema?: null
	enabled?: boolean
	mm?: boolean
	tags?: string[] | null
	pinned?: boolean | null
	deleted?: boolean | null
	order?: number
	created_at?: string | null
	updated_at?: string | null
	description?: string | null
	synced?: boolean
	created_by?: string | null
	owned_by?: string | null
	uuid?: string | null
	password?: string | null
	fk_custom_url_id?: string | null
}

export interface Record<T> {
	id: number
	fields: T
}

export type BlogPostRecord = Record<BlogPostFields>

export interface BlogPostFields {
	Title: string
	Subtitle: string
	Slug: string
	Content: string
	Image: NocoDBImage[]
	Alt: string
	CreatedDate: string
	UpdatedAt: string
}

export type PageFieldRecord = Record<PageFieldFields>

export interface PageFieldFields {
	Key: string
	CreatedAt: string
	UpdatedAt: string
	WebsitePage_id: number
	Translations: number
	WebsitePage: Record<{ slug: string }>
}

export type TranslationRecord = Record<TranslationFields>

export interface TranslationFields {
	Language: string
	Status: string
	Value: string
	CreatedAt: string
	UpdatedAt: string
	PageField_id: number
	PageField: Record<{ Key: string }>
}

export type DistributionZoneRecord = Record<DistributionZoneFields>

export type Country = Record<{ Name: string }>

// GeoJSON structure  for the MultiPolygon
export interface GeoJSONMultiPolygon {
	type: 'MultiPolygon'
	coordinates: number[][][][]
}

// GeoJSON structure  for the Polygon
export interface GeoJSONPolygon {
	type: 'Polygon'
	coordinates: number[][][]
}

export type GeoGeometry = GeoJSONPolygon | GeoJSONMultiPolygon

export interface DistributionZoneFields {
	Name: string
	Code: string
	// Note: The geometry arrives as a JSON string which must be parsed with JSON.parse() to obtain a GeoJSONMultiPolygon or GeoJSONPolygon
	Geometry: string
	'PVC Level': string | null
	'VCM Level': string | null
	'Map Color'?: string | null
	CreatedAt: string
	UpdatedAt: string
	Country_id: number
	Municipalities: number
	Actors: number
	Interactions: number
	Analyses: number
	Country: Country
	ActorName: string[]
	ActorEmail: string[]
	'Municipality Geometries': string[]
}
export interface DistributionZoneGeoLimitedFields {
	Name: string
	Country: Country
	ActorName?: string[]
}
export type DistributionZoneGeoLimitedRecord = Record<DistributionZoneGeoLimitedFields>

export interface DistributionZoneDetailFields {
	Name: string
	Code: string
	'PVC Level': string | null
	'VCM Level': string | null
	'PVC Level comment': string | null
	'Map Color'?: string | null
	Country: Country
	ActorName: string[]
	ActorEmail: string[]
	/** Resolved server-side from linked Municipality records; not from geometry fields */
	MunicipalityNames?: string[]
	'Municipality Geometries'?: string[]
}
export type DistributionZoneDetailRecord = Record<DistributionZoneDetailFields>

export interface DistributionZoneMapFields {
	Name: string
	Code: string
	Geometry: string
	'PVC Level': string | null
	'VCM Level': string | null
	'Map Color'?: string | null
	Country: Country
}
export type DistributionZoneMapRecord = Record<DistributionZoneMapFields>

export interface CountryMapFields {
	Name: string
	Code: string
	Geometry: string
	'PVC Level'?: string | null
	'VCM Level'?: string | null
	'Map Color'?: string | null
}
export type CountryMapRecord = Record<CountryMapFields>

export interface CountryListFields {
	Name: string
	Code: string
	'PVC Level'?: string | null
	'VCM Level'?: string | null
}
export type CountryListRecord = Record<CountryListFields>

export interface NocoAttachment {
	url?: string
	signedUrl?: string
	title?: string
	mimetype?: string
	size?: number
	width?: number
	height?: number
	thumbnails?: {
		tiny?: { signedUrl?: string }
		small?: { signedUrl?: string }
		card_cover?: { signedUrl?: string }
	}
}

export interface CountryDetailFields {
	Name: string
	Code: string
}
export type CountryDetailRecord = Record<CountryDetailFields>

export type CountryDataType = 'stat' | 'legislation' | 'missing_data' | 'more_details'

export interface CountryDataFields {
	Type: CountryDataType
	Order: number
	Title: string | null
	Content: string | null
}
export type CountryDataRecord = Record<CountryDataFields>
