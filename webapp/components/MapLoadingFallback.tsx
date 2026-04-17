'use client'

import { useEffect, useState } from 'react'

import { Loader2 } from 'lucide-react'

const SPINNER_DELAY_MS = 350

export function MapLoadingFallback() {
	const [showSpinner, setShowSpinner] = useState(false)

	useEffect(() => {
		const id = window.setTimeout(() => setShowSpinner(true), SPINNER_DELAY_MS)

		return () => window.clearTimeout(id)
	}, [])

	return (
		<div
			className='relative flex h-screen w-full items-center justify-center bg-white'
			role='status'
			aria-busy='true'
			aria-live='polite'
		>
			{showSpinner && (
				<>
					<span className='sr-only'>Loading map</span>
					<Loader2 className='text-aqua-400 size-10 animate-spin' aria-hidden />
				</>
			)}
		</div>
	)
}
