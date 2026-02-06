import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
	output: 'standalone',
	reactStrictMode: false,
	images: {
		remotePatterns: [{ hostname: 'cdn.shadcnstudio.com' }, { hostname: 'noco-uploads.s3.fr-par.scw.cloud' }]
	}
}

export default nextConfig
