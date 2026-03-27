'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Field, FieldLabel, FieldError } from '@/components/ui/field'

import { Template } from '@/lib/fetchLetterTemplates'
import TemplateCard from './TemplateCard'
import TemplateModal from './TemplateModal'
import DataSubmissionForm from './DataSubmissionForm'

const ROLES = [
	{ icon: '🏛️', title: 'Legal experts', description: 'Help communities understand their rights' },
	{ icon: '💻', title: 'Developers', description: 'Contribute to the open-source codebase' },
	{ icon: '🔬', title: 'Water specialists', description: 'Share expertise on water quality & PVC' }
]

interface GetInvolvedSectionProps {
	templates: Template[]
}

export default function GetInvolvedSection({ templates }: GetInvolvedSectionProps) {
	const [openTemplate, setOpenTemplate] = useState<number | null>(null)

	// Join form state
	const [name, setName] = useState('')
	const [email, setEmail] = useState('')
	const [expertise, setExpertise] = useState('')
	const [message, setMessage] = useState('')
	const [submitting, setSubmitting] = useState(false)
	const [success, setSuccess] = useState(false)
	const [error, setError] = useState<string | null>(null)

	async function handleJoin(e: React.FormEvent) {
		e.preventDefault()

		if (!name || !email || !expertise) {
			return
		}

		setSubmitting(true)
		setError(null)
		setSuccess(false)

		try {
			const res = await fetch('/api/join', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name, email, expertise, message: message || undefined })
			})

			if (!res.ok) {
				const body = (await res.json().catch(() => ({}))) as { error?: string }

				throw new Error(body.error ?? 'Submission failed')
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
			<h2 className='text-navy-800 mb-6 font-[lexend] text-2xl font-semibold'>Get involved</h2>

			<div className='grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-start'>
				{/* Column 1: Letter Templates */}
				<div className='border-navy-200 bg-navy-50 rounded-xl border p-5'>
					<h3 className='text-navy-800 mb-1 text-lg font-semibold'>📝 Letter templates</h3>
					<p className='text-navy-600 mb-4 text-sm'>
						Contact your local officials and water providers to demand transparency.
					</p>
					<div className='space-y-3'>
						{templates.map((tpl, i) => (
							<TemplateCard key={i} icon={tpl.icon} title={tpl.title} onClick={() => setOpenTemplate(i)} />
						))}
					</div>
					<div className='border-aqua-400 bg-aqua-100 mt-4 rounded-lg border p-3'>
						<p className='text-aqua-800 text-xs'>
							⚠️ <strong>Keep written records</strong> of all communications with your water provider, mayor, and
							elected officials.
						</p>
					</div>
				</div>

				{/* Column 2: Contribute Data */}
				<div className='border-navy-200 bg-navy-50 rounded-xl border p-5'>
					<h3 className='text-navy-800 mb-1 text-lg font-semibold'>📊 Contribute data</h3>
					<p className='text-navy-600 mb-4 text-sm'>
						Share water quality reports, PVC pipe info, or submit corrections.
					</p>
					<DataSubmissionForm />
				</div>

				{/* Column 3: Join Us */}
				<div className='border-navy-200 bg-navy-50 rounded-xl border p-5'>
					<h3 className='text-navy-800 mb-1 text-lg font-semibold'>🤝 Join us</h3>
					<p className='text-navy-600 mb-4 text-sm'>We&apos;re looking for volunteers to help improve the platform.</p>

					{/* Role chips */}
					<div className='mb-4 flex flex-wrap gap-2'>
						{ROLES.map(role => (
							<span
								key={role.title}
								className='border-navy-200 inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-1 text-xs'
								title={role.description}
							>
								{role.icon} {role.title}
							</span>
						))}
					</div>

					<form
						onSubmit={e => {
							void handleJoin(e)
						}}
						className='space-y-3'
					>
						<Field>
							<FieldLabel htmlFor='join-name'>Name *</FieldLabel>
							<Input id='join-name' required value={name} onChange={e => setName(e.target.value)} />
						</Field>
						<Field>
							<FieldLabel htmlFor='join-email'>Email *</FieldLabel>
							<Input id='join-email' type='email' required value={email} onChange={e => setEmail(e.target.value)} />
						</Field>
						<Field>
							<FieldLabel htmlFor='join-expertise'>Expertise *</FieldLabel>
							<Input
								id='join-expertise'
								required
								value={expertise}
								onChange={e => setExpertise(e.target.value)}
								placeholder='e.g. Water engineer…'
							/>
						</Field>
						<Field>
							<FieldLabel htmlFor='join-message'>Message</FieldLabel>
							<textarea
								id='join-message'
								rows={3}
								value={message}
								onChange={e => setMessage(e.target.value)}
								placeholder="How you'd like to help…"
								className='border-input focus-visible:border-ring focus-visible:ring-ring/50 w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]'
							/>
						</Field>

						{error && <FieldError>{error}</FieldError>}
						{success && <p className='text-sm font-medium text-green-700'>✓ Thank you! We&apos;ll be in touch.</p>}

						<Button type='submit' disabled={submitting || !name || !email || !expertise} className='w-full'>
							{submitting ? 'Sending…' : 'Send my application'}
						</Button>
					</form>
				</div>
			</div>

			{/* Template modals */}
			{templates.map((tpl, i) => (
				<TemplateModal
					key={i}
					title={tpl.title}
					content={tpl.content}
					open={openTemplate === i}
					onOpenChange={open => setOpenTemplate(open ? i : null)}
				/>
			))}
		</div>
	)
}
