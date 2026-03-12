import path from 'path'

import dotenv from 'dotenv'
import type { NextConfig } from 'next'

// Load .env from repo root (shared with Python pipelines). CWD is webapp/ when running dev/build.
dotenv.config({ path: path.resolve(process.cwd(), '../.env') })

const nextConfig: NextConfig = {
	output: 'standalone',
	reactStrictMode: false,
	images: {
		remotePatterns: [{ hostname: 'cdn.shadcnstudio.com' }, { hostname: 'noco-uploads.s3.fr-par.scw.cloud' }]
	}
}

export default nextConfig
