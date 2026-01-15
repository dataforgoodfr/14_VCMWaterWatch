#!/usr/bin/env node

/**
 * Setup git hooks for monorepo configuration
 * This script runs after npm install and sets up the pre-commit hook
 * in .git/hooks (at the root) to run lint-staged from the webapp folder
 */

const fs = require('fs')
const path = require('path')

// Find the .git directory (should be at repo root)
let gitDir = path.resolve(__dirname, '../../.git')

if (!fs.existsSync(gitDir)) {
	console.warn('⚠️  .git directory not found. Skipping git hooks setup.')
	process.exit(0)
}

const hooksDir = path.join(gitDir, 'hooks')
const preCommitPath = path.join(hooksDir, 'pre-commit')

// Create hooks directory if it doesn't exist
if (!fs.existsSync(hooksDir)) {
	fs.mkdirSync(hooksDir, { recursive: true })
}

// Git hook content
const hookContent = `#!/bin/sh
cd webapp && npx lint-staged
`

// Write the pre-commit hook
fs.writeFileSync(preCommitPath, hookContent, { mode: 0o755 })

console.log('✅ Git hooks setup successfully!')
console.log(`   Pre-commit hook created at: ${preCommitPath}`)
