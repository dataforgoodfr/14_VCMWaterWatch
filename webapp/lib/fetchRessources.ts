import { RessourcesRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

export async function fetchRessources({ locale }: { locale: string }): Promise<RessourcesRecord[]> {
	try {
		const tableId = await getTableIdByName('Ressources')

		if (!tableId) {
			console.warn('fetchRessources: Ressources table not found in NocoDB meta')
			return []
		}

		const where = `(Language,eq,${locale})`
		const sort = JSON.stringify([{ field: 'nc_order', direction: 'asc' }])

		const res = await instance.get<FetchResponseRecords<RessourcesRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`,
			{ params: { where, sort } }
		)

		if (res.status !== 200) {
			throw new Error(res.statusText)
		}

		return res.data.records ?? []
	} catch (e) {
		console.error('Error fetching ressources:', e)
		return []
	}
}
