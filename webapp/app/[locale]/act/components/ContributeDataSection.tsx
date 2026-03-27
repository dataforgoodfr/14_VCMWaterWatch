'use client'

import DataSubmissionForm from './DataSubmissionForm'

export default function ContributeDataSection() {
	return (
		<div>
			<h2 className='text-navy-800 mb-2 font-[lexend] text-2xl font-semibold'>Contribute data</h2>
			<p className='text-navy-800 mb-6 text-sm'>
				Have water quality reports, PVC pipe information, or other relevant data? Share it with us to help improve the
				platform. You can also submit corrections if you spot an error.
			</p>

			<div className='border-navy-200 bg-navy-50 mx-auto max-w-xl rounded-xl border p-6'>
				<DataSubmissionForm />
			</div>
		</div>
	)
}
