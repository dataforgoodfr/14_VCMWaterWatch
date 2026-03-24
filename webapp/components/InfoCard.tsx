import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

interface InfoCardProps {
	children: ReactNode
	bgClassName?: string
}

export const InfoCard = ({ children, bgClassName = 'bg-navy-100' }: InfoCardProps) => {
	return <div className={cn('border-navy-800 rounded-r-2xl border-l-[6px] px-8 py-8.5', bgClassName)}>{children}</div>
}
