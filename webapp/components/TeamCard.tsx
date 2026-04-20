import Image from 'next/image'

interface TeamCardProps {
	initials: string
	name: string
	role: string
	color?: 'teal' | 'green' | 'purple' | 'navy'
	/** Optional photo URL.  When provided, the photo replaces the initials bubble. */
	imageSrc?: string | null
}

const colorMap = {
	teal: 'bg-aqua-600',
	green: 'bg-emerald-600',
	purple: 'bg-purple-600',
	navy: 'bg-navy-600'
}

const colorKeys = Object.keys(colorMap) as (keyof typeof colorMap)[]

/**
 * Derive a deterministic color from a string (e.g. a member id) so that the
 * color is stable across renders without requiring a hardcoded prop.
 */
function deterministicColor(seed: string): keyof typeof colorMap {
	let hash = 0

	for (let i = 0; i < seed.length; i++) {
		hash = (hash * 31 + seed.charCodeAt(i)) >>> 0
	}

	return colorKeys[hash % colorKeys.length]
}

export const TeamCard = ({ initials, name, role, color, imageSrc }: TeamCardProps) => {
	const resolvedColor = color ?? deterministicColor(name)

	return (
		<div className='flex flex-col items-center gap-3 rounded-2xl border border-gray-200 bg-white px-6 py-8'>
			{imageSrc ? (
				<div className='h-16 w-16 overflow-hidden rounded-full'>
					<Image src={imageSrc} alt={name} width={64} height={64} className='h-full w-full object-cover' />
				</div>
			) : (
				<div
					className={`flex h-16 w-16 items-center justify-center rounded-full text-lg font-bold text-white ${colorMap[resolvedColor]}`}
				>
					{initials}
				</div>
			)}
			<p className='text-navy-800 font-[lexend] text-base font-semibold'>{name}</p>
			<p className='text-navy-600 text-center text-sm leading-snug whitespace-pre-line'>{role}</p>
		</div>
	)
}
