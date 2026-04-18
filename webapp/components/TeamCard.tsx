interface TeamCardProps {
	initials: string
	name: string
	role: string
	color: 'teal' | 'green' | 'purple' | 'navy'
}

const colorMap = {
	teal: 'bg-aqua-600',
	green: 'bg-emerald-600',
	purple: 'bg-purple-600',
	navy: 'bg-navy-600'
}

export const TeamCard = ({ initials, name, role, color }: TeamCardProps) => {
	return (
		<div className='flex flex-col items-center gap-3 rounded-2xl border border-gray-200 bg-white px-6 py-8'>
			<div
				className={`flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold text-white ${colorMap[color]}`}
			>
				{initials}
			</div>
			<p className='text-navy-800 font-[lexend] text-base font-semibold'>{name}</p>
			<p className='text-navy-600 whitespace-pre-line text-center text-sm leading-snug'>{role}</p>
		</div>
	)
}
