/**
 * Fetches team members from NocoDB `Team` table.
 *
 * Returns members sorted by `nc_order` (ascending) and resolves each
 * member's image URL via the generic entity image pipeline.
 */

import { getEntityImageSrc } from './entityImage'
import { getTableIdByName } from './fetchMetaTables'
import { instance } from './instance'
import type { FetchResponseRecords } from './instance'

const TEAM_FIELDS = 'Id,Name,Expertise,City,Image,SubTeam,nc_order'

interface NocoDBTeamRowFields {
	Id: number
	Name: string | null
	Expertise: string | null
	City: string | null
	Image: unknown
	SubTeam: string | null
	nc_order: number | null
}

export interface TeamMember {
	id: string
	name: string
	/** Role / expertise description, used in TeamCard */
	role: string
	city: string | null
	subTeam: string | null
	/** Resolved public URL for the member's photo, or null. */
	imageSrc: string | null
}

/**
 * Slugify a team member name for use as the image manifest key.
 * Must match the Python _slugify() implementation in export_entity_images.py.
 */
function slugifyName(name: string): string {
	return name
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '') // strip combining diacritics
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '')
}

interface NocoDBTeamRecord {
	id: string | number
	fields: NocoDBTeamRowFields
}

export async function fetchTeam(): Promise<TeamMember[]> {
	try {
		const tableId = await getTableIdByName('Members')

		if (!tableId) {
			console.warn('fetchTeam: Members table not found in NocoDB meta')
			return []
		}

		const response = await instance.get<FetchResponseRecords<NocoDBTeamRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`,
			{
				params: {
					fields: TEAM_FIELDS,
					sort: JSON.stringify([{ field: 'nc_order', direction: 'asc' }]),
					// TODO: paginate if the team exceeds 200 members — mirror the
					// load_all_records() pattern from pipelines/common/services.py
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
			.filter((record): record is NocoDBTeamRecord & { fields: { Name: string } } => Boolean(record.fields?.Name))
			.map(record => {
				const { fields } = record
				const slug = slugifyName(fields.Name)

				return {
					id: String(record.id),
					name: fields.Name,
					role: fields.Expertise ?? '',
					city: fields.City ?? null,
					subTeam: fields.SubTeam ?? null,
					imageSrc: getEntityImageSrc('team', slug)
				}
			})
	} catch (error) {
		console.error('Error fetching team:', error)
		return []
	}
}
