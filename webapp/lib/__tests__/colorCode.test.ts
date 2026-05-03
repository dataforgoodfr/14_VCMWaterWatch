import { describe, it, expect } from 'vitest'

import { colorCodeConfig, type ColorCode } from '../colorCode'

describe('colorCodeConfig', () => {
	const EXPECTED_KEYS: ColorCode[] = ['red', 'orange', 'yellow', 'green', 'gray']

	it('has all five color codes', () => {
		expect(Object.keys(colorCodeConfig).sort()).toEqual([...EXPECTED_KEYS].sort())
	})

	it.each(EXPECTED_KEYS)('%s has label, solid, bg, border as hex strings', key => {
		const c = colorCodeConfig[key]

		expect(c.label).toBeTruthy()

		for (const prop of ['solid', 'bg', 'border'] as const) {
			expect(c[prop]).toMatch(/^#[0-9a-fA-F]{6}$/)
		}
	})
})
