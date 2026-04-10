const FALLBACK: Readonly<Record<string, string>> = {
	'--risk-confirme-border': '#dc2626',
	'--risk-confirme-bg': '#fee2e2',
	'--risk-probable-border': '#d97706',
	'--risk-probable-bg': '#fef3c7',
	'--risk-absent-border': '#16a34a',
	'--risk-absent-bg': '#dcfce7',
	'--risk-inconnu-border': '#64748b',
	'--risk-inconnu-bg': '#f1f5f9'
}

export function resolveRiskCssVar(cssVarName: string): string {
	if (typeof document === 'undefined') {
		return FALLBACK[cssVarName] ?? ''
	}

	const v = getComputedStyle(document.documentElement).getPropertyValue(cssVarName).trim()

	return v || FALLBACK[cssVarName] || ''
}
