export type ThumbnailType = {
	signedUrl: string
}

export type ImageThumbnails = {
	tiny?: ThumbnailType
	small?: ThumbnailType
	card_cover?: ThumbnailType
	[key: string]: ThumbnailType | undefined
}

export type NocoDBImage = {
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

export type TableName =
	| 'Actor'
	| 'Interaction'
	| 'Analysis'
	| 'Attachment'
	| 'ContactPerson'
	| 'Page'
	| 'PageField'
	| 'Translation'
	| 'Country'
	| 'DistributionZone'
	| 'Municipality'
	| 'BlogPost'

export interface BlogPost {
	Id: number
	Title: string
	Subtitle: string
	Slug: string
	Content: string
	Image: NocoDBImage[]
	Alt: string
	CreatedDate: string
	UpdatedAt: string
}

export interface MetaTable {
	id: string
	source_id?: string | null
	base_id?: string | null
	table_name?: TableName
	title?: string
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

export interface MetaTables {
	Actor?: MetaTable
	[tableName: string]: MetaTable | undefined
}

export interface PageFieldRecord {
	Id: number
	Key: string
	CreatedAt: string
	UpdatedAt: string
	WebsitePage_id: number
	Translations: number
	WebsitePage: {
		Id: number
		slug: string
	}
}

export interface TranslationRecord {
	Id: number
	Language: string
	Status: string
	Value: string
	CreatedAt: string
	UpdatedAt: string
	PageField_id: number
	PageField: {
		Id: number
		Key: string
	}
}
