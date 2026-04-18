import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
	output: 'standalone',
	reactStrictMode: false,
	headers: () => [
		{
			source: '/:path*',
			headers: [
				{ key: 'X-Frame-Options', value: 'SAMEORIGIN' },
				{ key: 'X-Content-Type-Options', value: 'nosniff' },
				{ key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
				{ key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
				{ key: 'X-DNS-Prefetch-Control', value: 'on' }
			]
		}
	],
	images: {
		remotePatterns: [
			{ hostname: 'cdn.shadcnstudio.com' },
			{ hostname: 'noco-uploads.s3.fr-par.scw.cloud' },
			{ hostname: 'vcm-watch.s3.fr-par.scw.cloud' },
			{ hostname: 'placehold.co', protocol: 'https' }
		]
	}
}

export default nextConfig
