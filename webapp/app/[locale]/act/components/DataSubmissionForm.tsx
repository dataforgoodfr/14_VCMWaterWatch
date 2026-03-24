'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Field, FieldLabel, FieldError } from '@/components/ui/field'

const DATA_TYPES = ['Analysis report', 'PVC presence info', 'Correction', 'Other'] as const

type DataType = (typeof DATA_TYPES)[number]

interface DataSubmissionFormProps {
	defaultDataType?: DataType
}

export default function DataSubmissionForm({ defaultDataType }: DataSubmissionFormProps) {
	const [dataType, setDataType] = useState<DataType | ''>(defaultDataType ?? '')
	const [documentSource, setDocumentSource] = useState('')
	const [submitting, setSubmitting] = useState(false)
	const [success, setSuccess] = useState(false)
	const [error, setError] = useState<string | null>(null)

	async function handleSubmit(e: React.FormEvent) {
		e.preventDefault()
		if (!dataType) return

		setSubmitting(true)
		setError(null)
		setSuccess(false)

		try {
			const res = await fetch('/api/contribute', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					dataType,
					documentSource: documentSource || undefined
				})
			})

			if (!res.ok) {
				const body = await res.json().catch(() => ({}))
				throw new Error((body as { error?: string }).error ?? 'Submission failed')
			}

			setSuccess(true)
			setDataType(defaultDataType ?? '')
			setDocumentSource('')
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Submission failed')
		} finally {
			setSubmitting(false)
		}
	}

	return (
		<form onSubmit={handleSubmit} className='space-y-4'>
			<Field>
				<FieldLabel htmlFor='data-type'>Data type *</FieldLabel>
				<select
					id='data-type'
					required
					value={dataType}
					onChange={e => setDataType(e.target.value as DataType)}
					className='border-input h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]'
				>
					<option value='' disabled>
						Select a data type…
					</option>
					{DATA_TYPES.map(type => (
						<option key={type} value={type}>
							{type}
						</option>
					))}
				</select>
			</Field>

			<Field>
				<FieldLabel htmlFor='document-source'>Document source</FieldLabel>
				<Input
					id='document-source'
					placeholder='e.g. Rapport annuel 2024'
					value={documentSource}
					onChange={e => setDocumentSource(e.target.value)}
				/>
			</Field>

			{error && <FieldError>{error}</FieldError>}

			{success && <p className='text-sm font-medium text-green-700'>✓ Thank you! Your contribution has been submitted.</p>}

			<Button type='submit' disabled={submitting || !dataType} className='w-full'>
				{submitting ? 'Submitting…' : 'Submit data'}
			</Button>
		</form>
	)
}
