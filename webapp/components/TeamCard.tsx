import Image from 'next/image'

interface TeamCardProps {
	initials: string
	name: string
	role: string
	color: 'teal' | 'green' | 'purple' | 'navy'
	/** Optional photo URL.  When provided the initials bubble is replaced. */
	imageSrc?: string | null
}

const colorMap = {
	teal: 'bg-aqua-600',
	green: 'bg-emerald-600',
	purple: 'bg-purple-600',
	navy: 'bg-navy-600'
}

export const TeamCard = ({ initials, name, role, color, imageSrc }: TeamCardProps) => {
	return (
		<div className='flex flex-col items-center gap-3 rounded-2xl border border-gray-200 bg-white px-6 py-8'>
			{imageSrc ? (
				<div className='relative h-16 w-16 overflow-hidden rounded-full'>
					<Image src={imageSrc} alt={name} fill className='object-cover' sizes='64px' />
				</div>
			) : (
				<div
					className={`flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold text-white ${colorMap[color]}`}
				>
					{initials}
				</div>
			)}
			<p className='text-navy-800 font-[lexend] text-base font-semibold'>{name}</p>
			<p className='text-navy-600 text-center text-sm leading-snug whitespace-pre-line'>{role}</p>
		</div>
	)
}
