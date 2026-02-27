import { Geist_Mono, Lato, Lexend } from 'next/font/google'

import type { Metadata } from 'next'
import './globals.css'

import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'

const lato = Lato({
	variable: '--font-lato',
	weight: ['400', '700'],
	subsets: ['latin']
})

const lexend = Lexend({
	variable: '--font-lexend',
	weight: ['400', '500', '600', '700'],
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
			<body className={`${lato.variable} ${lexend.variable} ${geistMono.variable} h-full antialiased`}>
				<Navbar />
				{children}
				<Footer />
			</body>
		</html>
	)
}
