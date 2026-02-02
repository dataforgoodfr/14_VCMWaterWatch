import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
	output: 'standalone',
	reactStrictMode: false,
	images: {
		remotePatterns: [{ hostname: 'cdn.shadcnstudio.com' }, { hostname: 'noco-uploads.s3.fr-par.scw.cloud' }]
	},
	rewrites() {
		const backend = process.env.NOCODB_URL

		if (!backend) {
			// If the backend URL is not set, do not add the rewrite to avoid invalid destination
			console.warn('NOCODB_URL not defined; skipping API rewrite')
			return []
		}

		return [
			{
				source: '/api/:path*', // Match requests starting with "/api"
				destination: `${backend}/:path*` // Proxy to Backend
			}
		]
	}
}

export default nextConfig
