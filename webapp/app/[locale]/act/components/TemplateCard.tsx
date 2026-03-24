interface TemplateCardProps {
	icon: string
	title: string
	onClick: () => void
}

export default function TemplateCard({ icon, title, onClick }: TemplateCardProps) {
	return (
		<button
			onClick={onClick}
			className='border-navy-200 bg-navy-50 hover:border-navy-300 flex h-full min-h-[4.5rem] items-center gap-3 rounded-lg border p-3 text-left shadow-sm transition hover:shadow'
		>
			<span className='text-xl'>{icon}</span>
			<span className='text-navy-800 text-sm font-medium'>{title}</span>
		</button>
	)
}
