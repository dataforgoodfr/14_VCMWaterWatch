export function normalizePath(value: string): string {
	const pathWithoutLocale = value.replace(/^\/(en|fr)(?=\/|$)/, '') || '/'
	const normalized = pathWithoutLocale.startsWith('/') ? pathWithoutLocale : `/${pathWithoutLocale}`

	if (normalized !== '/' && normalized.endsWith('/')) {
		return normalized.slice(0, -1)
	}

	return normalized
}

export function isActivePath(currentPath: string, itemPath: string): boolean {
	if (itemPath === '/') {
		return currentPath === '/'
	}

	return currentPath === itemPath || currentPath.startsWith(`${itemPath}/`)
}
