import axios from 'axios'

export interface FetchResponse<T> {
	list: T[]
	pageInfo: {
		totalRows: number
		page: number
		pageSize: number
		isFirstPage: boolean
		isLastPage: boolean
	}
}

export const instance = axios.create({
	baseURL: process.env.NOCODB_URL,
	timeout: 1000,
	headers: { 'xc-token': process.env.NOCODB_TOKEN ?? '' }
})
