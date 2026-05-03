import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitest/config'

export default defineConfig({
	test: {
		environment: 'node',
		passWithNoTests: true
	},
	resolve: {
		alias: {
			'@': fileURLToPath(new URL('.', import.meta.url))
		}
	}
})
