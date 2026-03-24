'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Field, FieldLabel, FieldError } from '@/components/ui/field'
import { Card, CardContent } from '@/components/ui/card'

const ROLES = [
	{
		icon: '🏛️',
		title: 'Legal experts',
		description: 'Help affected communities understand their rights'
	},
	{
		icon: '💻',
		title: 'Volunteer developers',
		description: "Contribute to the platform's open-source codebase"
	},
	{
		icon: '🔬',
		title: 'Water specialists',
		description: 'Share expertise on water quality analysis and PVC infrastructure'
	}
]

export default function JoinProjectSection() {
	const [name, setName] = useState('')
	const [email, setEmail] = useState('')
	const [expertise, setExpertise] = useState('')
	const [message, setMessage] = useState('')
	const [submitting, setSubmitting] = useState(false)
	const [success, setSuccess] = useState(false)
	const [error, setError] = useState<string | null>(null)

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault()
		if (!name || !email || !expertise) return

		setSubmitting(true)
		setError(null)
		setSuccess(false)

		try {
			const res = await fetch('/api/join', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name,
					email,
					expertise,
					message: message || undefined
				})
			})

			if (!res.ok) {
				const body = await res.json().catch(() => ({}))
				throw new Error((body as { error?: string }).error ?? 'Submission failed')
			}

			setSuccess(true)
			setName('')
			setEmail('')
			setExpertise('')
			setMessage('')
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Submission failed')
		} finally {
			setSubmitting(false)
		}
	}

	return (
		<div>
			<h2 className='text-navy-800 mb-6 font-[lexend] text-2xl font-semibold'>Join the project</h2>

			<div className='grid grid-cols-1 gap-8 md:grid-cols-2'>
				{/* Role cards */}
				<div className='space-y-4'>
					<h3 className='text-navy-800 text-lg font-semibold'>We're looking for</h3>
					<div className='space-y-3'>
						{ROLES.map(role => (
							<Card key={role.title} className='py-4'>
								<CardContent className='flex items-start gap-3'>
									<span className='text-2xl'>{role.icon}</span>
									<div>
										<p className='text-navy-800 text-sm font-semibold'>{role.title}</p>
										<p className='text-navy-600 mt-1 text-sm'>{role.description}</p>
									</div>
								</CardContent>
							</Card>
						))}
					</div>
				</div>

				{/* Contact form */}
				<div className='space-y-4'>
					<h3 className='text-navy-800 text-lg font-semibold'>Get in touch</h3>
					<form onSubmit={handleSubmit} className='space-y-4'>
						<Field>
							<FieldLabel htmlFor='join-name'>Name *</FieldLabel>
							<Input id='join-name' required value={name} onChange={e => setName(e.target.value)} />
						</Field>

						<Field>
							<FieldLabel htmlFor='join-email'>Email *</FieldLabel>
							<Input
								id='join-email'
								type='email'
								required
								value={email}
								onChange={e => setEmail(e.target.value)}
							/>
						</Field>

						<Field>
							<FieldLabel htmlFor='join-expertise'>Expertise / Motivation *</FieldLabel>
							<Input
								id='join-expertise'
								required
								value={expertise}
								onChange={e => setExpertise(e.target.value)}
								placeholder='e.g. Water engineer, Full-stack developer…'
							/>
						</Field>

						<Field>
							<FieldLabel htmlFor='join-message'>Message</FieldLabel>
							<textarea
								id='join-message'
								rows={4}
								value={message}
								onChange={e => setMessage(e.target.value)}
								placeholder="Tell us how you'd like to contribute…"
								className='border-input w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]'
							/>
						</Field>

						{error && <FieldError>{error}</FieldError>}

						{success && (
							<p className='text-sm font-medium text-green-700'>
								✓ Thank you! We'll be in touch soon.
							</p>
						)}

						<Button type='submit' disabled={submitting || !name || !email || !expertise} className='w-full'>
							{submitting ? 'Sending…' : 'Send my application'}
						</Button>
					</form>
				</div>
			</div>
		</div>
	)
}
