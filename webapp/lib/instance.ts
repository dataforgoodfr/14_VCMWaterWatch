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

export const instance = axios.create({
	baseURL: process.env.NOCODB_URL,
	timeout: 1000,
	headers: { 'xc-token': process.env.NOCODB_TOKEN ?? '' }
})
