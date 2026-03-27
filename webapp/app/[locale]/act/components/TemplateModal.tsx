'use client'

import { useState } from 'react'

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'

interface TemplateModalProps {
	title: string
	content: string
	open: boolean
	onOpenChange: (open: boolean) => void
}

export default function TemplateModal({ title, content, open, onOpenChange }: TemplateModalProps) {
	const [copied, setCopied] = useState(false)

	function handleCopy() {
		void navigator.clipboard.writeText(content).then(() => {
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		})
	}

	return (
		<Sheet open={open} onOpenChange={onOpenChange}>
			<SheetContent side='right' className='w-full sm:max-w-lg'>
				<SheetHeader className='p-6 pb-0'>
					<SheetTitle>{title}</SheetTitle>
					<SheetDescription>Copy and adapt this template for your situation.</SheetDescription>
				</SheetHeader>
				<div className='flex-1 overflow-y-auto px-6 py-4'>
					<pre className='font-sans text-sm leading-relaxed whitespace-pre-wrap text-gray-700'>{content}</pre>
				</div>
				<div className='border-t p-4'>
					<button
						onClick={handleCopy}
						className='w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700'
					>
						{copied ? '✓ Copied!' : 'Copy to clipboard'}
					</button>
				</div>
			</SheetContent>
		</Sheet>
	)
}
