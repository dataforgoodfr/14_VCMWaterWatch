import { MetaTable, TableName } from '@/types/apiTypes'
import { FetchResponse, instance } from './instance'

export interface TableMapping {
	id: string
	table_name: string
}

// Server-side cache - persists for the lifetime of the server process
let tableCache: TableMapping[] | null = null
let cacheTimestamp: number | null = null

const CACHE_DURATION_MS = 5 * 60 * 1000 // 5 minutes

/**
 * Fetch meta tables from NocoDB and cache the results
 * @param forceRefresh - Force a fresh fetch even if cache is still valid
 */
export async function fetchMetaTables(forceRefresh = false): Promise<TableMapping[]> {
	try {
		if (!forceRefresh && tableCache && cacheTimestamp && Date.now() - cacheTimestamp < CACHE_DURATION_MS) {
			return tableCache
		}

		const metaTablesResponse = await instance.get<FetchResponse<MetaTable>>(
			`/meta/bases/${process.env.NOCODB_BASE_ID}/tables`
		)

		if (metaTablesResponse.status !== 200) {
			throw new Error(`Failed to fetch meta tables: ${metaTablesResponse.statusText}`)
		}

		const metaTablesData = metaTablesResponse.data

		// Transform and cache the table mappings
		tableCache = metaTablesData.list
			.filter((table): table is MetaTable & { table_name: string } => Boolean(table.table_name))
			.map(table => ({
				id: table.id,
				table_name: table.table_name
			}))

		cacheTimestamp = Date.now()
		return tableCache
	} catch (error) {
		console.error('Error fetching meta tables:', error)

		// Return cached data if available, even if it's stale
		if (tableCache) {
			console.warn('Returning stale table cache due to fetch error')

			return tableCache
		}

		throw error
	}
}

export async function getTableIdByName(tableName: TableName, forceRefresh = false): Promise<string | null> {
	const tables = await fetchMetaTables(forceRefresh)
	const table = tables.find(t => t.table_name === tableName)

	return table?.id ?? null
}

// Clear the cache (when tables have been updated)
export function clearTableCache(): void {
	tableCache = null
	cacheTimestamp = null
}
