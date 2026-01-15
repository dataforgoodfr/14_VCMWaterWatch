import { Geist, Geist_Mono } from 'next/font/google'

// import type { Metadata } from 'next'
import './globals.css'

// import { Navbar } from '@/components/Navbar'

const geistSans = Geist({
	variable: '--font-geist-sans',
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
			<body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
				<Navbar />
				{children}
			</body>
		</html>
	)
}
