import axios from 'axios'

export interface FetchResponseMeta<T> {
	list: T[]
}

export interface FetchResponseRecords<T> {
	records: T[]
	next?: string | null
	prev?: string | null
	nestedNext: string | null
	nestedPrev?: string | null
}

/** Match pipelines/common/db_helper.py: NOCODB_URL may be host-only; v3 APIs live under /api/v3. */
function nocoDbApiBaseUrl(): string {
	const raw = process.env.NOCODB_URL?.trim() ?? ''

	if (!raw) {
		return ''
	}

	const base = raw.replace(/\/+$/, '')

	return base.toLowerCase().endsWith('/api/v3') ? base : `${base}/api/v3`
}

export const instance = axios.create({
	baseURL: nocoDbApiBaseUrl(),
	timeout: 1000,
	headers: { 'xc-token': process.env.NOCODB_TOKEN ?? '' },
	proxy: false
})
