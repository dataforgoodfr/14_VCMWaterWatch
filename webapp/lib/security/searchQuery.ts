const MAX_SEARCH_QUERY_LENGTH = 200

/** Chars that break NocoDB `where=(Name,like,...)` filter syntax when embedded raw */
const NOCODB_LIKE_SPECIAL = /[,()~&]/g

function stripControlCharacters(s: string): string {
	let out = ''

	for (let i = 0; i < s.length; i++) {
		const c = s.charCodeAt(i)

		if (c >= 32 && c !== 127) {
			out += s[i]
		}
	}

	return out
}

export function sanitizeSearchQuery(input: string | null | undefined): string | null {
	if (input == null) {
		return null
	}

	const trimmed = input.trim()

	if (trimmed.length === 0) {
		return null
	}

	if (trimmed.length > MAX_SEARCH_QUERY_LENGTH) {
		return null
	}

	const noControl = stripControlCharacters(trimmed)

	if (noControl.length === 0) {
		return null
	}

	return noControl.length > MAX_SEARCH_QUERY_LENGTH ? null : noControl
}

export function sanitizeNocoDbLikeValue(input: string): string {
	return input.replace(NOCODB_LIKE_SPECIAL, ' ').replace(/\s+/g, ' ').trim()
}

export function sanitizePhotonLang(input: string | undefined): string {
	const s = input?.trim() ?? ''

	return /^[a-z]{2}$/.test(s) ? s : 'en'
}
