interface InfoCardProps {
	children: React.ReactNode
}

export const InfoCard = ({ children }: InfoCardProps) => {
	return <div className='bg-navy-100 border-navy-800 rounded-r-2xl border-l-[6px] px-8 py-8.5'>{children}</div>
}
