/**
 * Fetches team members from NocoDB `Team` table.
 *
 * Returns members sorted by `nc_order` (ascending) and resolves each
 * member's image URL via the generic entity image pipeline.
 */

import { getEntityImageSrc } from './entityImage'
import { instance } from './instance'
import type { FetchResponseRecords } from './instance'

/** Table ID for the NocoDB Team table. */
const TEAM_TABLE_ID = 'mdwyoi1vy3ol4am'

const TEAM_FIELDS = 'Id,Name,Expertise,City,Image,SubTeam,nc_order'

interface NocoDBTeamRow {
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

export async function fetchTeam(): Promise<TeamMember[]> {
	try {
		const response = await instance.get<FetchResponseRecords<NocoDBTeamRow>>(
			`/data/${process.env.NOCODB_BASE_ID}/${TEAM_TABLE_ID}/records`,
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

		const rows = response.data.records ?? []

		return rows
			.filter((row): row is NocoDBTeamRow & { Name: string } => Boolean(row.Name))
			.map(row => {
				const slug = slugifyName(row.Name)

				return {
					id: String(row.Id),
					name: row.Name,
					role: row.Expertise ?? '',
					city: row.City ?? null,
					subTeam: row.SubTeam ?? null,
					imageSrc: getEntityImageSrc('team', slug)
				}
			})
	} catch (error) {
		console.error('Error fetching team:', error)
		return []
	}
}
