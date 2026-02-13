import { Geist_Mono, Lato } from 'next/font/google'

import type { Metadata } from 'next'
import './globals.css'

import { Navbar } from '@/components/Navbar'

const lato = Lato({
	variable: '--font-lato',
	weight: ['400', '700'],
	subsets: ['latin']
})

const geistMono = Geist_Mono({
	variable: '--font-geist-mono',
	subsets: ['latin']
})

export const metadata: Metadata = {
	title: 'VCM Water Watch',
	description: 'Monitor and report VCM water pollution in Europe'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
	return (
		<html>
			<body className={`${lato.variable} ${geistMono.variable} antialiased`}>
				<Navbar />
				{children}
			</body>
		</html>
	)
}
