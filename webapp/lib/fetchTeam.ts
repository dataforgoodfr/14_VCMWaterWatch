/**
 * Fetch team members from the NocoDB `Team` table.
 *
 * Members are sorted by `nc_order` (ascending) so the About page respects the
 * order set in NocoDB.  Each member's `imageSrc` is resolved via the generic
 * entity-image helper, using a slug derived from the member's name (matching
 * the filename prefix written by `export_entity_images_flow`).
 */

import { getEntityImageSrc } from '@/lib/entityImage'
import { getTableIdByName } from '@/lib/fetchMetaTables'
import { FetchResponseRecords, instance } from '@/lib/instance'

const TEAM_FIELDS = 'Id,Name,Expertise,City,Image,SubTeam,nc_order'

/** Slugify a name the same way the Python export pipeline does:
 *  lowercase, ASCII-fold, non-alphanum → `-`, collapse, trim. */
function slugify(name: string): string {
	return name
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '') // strip combining accents
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '')
}

/** A single row returned by the NocoDB `Team` table. */
interface TeamRecord {
	Id: number
	Name?: string | null
	Expertise?: string | null
	City?: string | null
	SubTeam?: string | null
	nc_order?: number | null
}

/** Normalised team member returned by `fetchTeam`. */
export interface TeamMember {
	id: number
	name: string
	/** Role / expertise as stored in NocoDB. */
	role: string
	city: string | null
	subTeam: string | null
	/** Order within the sub-team (from `nc_order`). */
	order: number
	/** Public URL for the member's photo, or `null` if not available. */
	imageSrc: string | null
}

export async function fetchTeam(): Promise<TeamMember[]> {
	try {
		const tableId = await getTableIdByName('Team')

		if (!tableId) {
			console.warn('fetchTeam: Team table not found in NocoDB meta')
			return []
		}

		const response = await instance.get<FetchResponseRecords<TeamRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`,
			{
				params: {
					fields: TEAM_FIELDS,
					sort: 'nc_order',
					pageSize: 200
				},
				timeout: 10000
			}
		)

		if (response.status !== 200) {
			throw new Error(`Failed to fetch team: ${response.statusText}`)
		}

		const records = response.data.records ?? []

		return records
			.filter((r): r is TeamRecord & { Name: string } => Boolean(r.Name))
			.map(r => ({
				id: r.Id,
				name: r.Name,
				role: r.Expertise ?? '',
				city: r.City ?? null,
				subTeam: r.SubTeam ?? null,
				order: r.nc_order ?? 0,
				imageSrc: getEntityImageSrc('team', slugify(r.Name))
			}))
	} catch (error) {
		console.error('Error fetching team:', error)
		return []
	}
}
