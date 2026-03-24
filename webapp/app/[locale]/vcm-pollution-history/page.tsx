import { TimelineSection } from '@/components/TimelineSection'
import { ContaminationSection } from '@/components/ContaminationSection'
import { PubliHealthRiskSection } from '@/components/PublicHealthRiskSection'

export default function VcmPollutionHistoryPage() {
	return (
		<main className='container mx-auto px-4 md:px-8'>
			<h1 className='text-navy-800 pt-16 pb-8 font-[lexend] text-[32px] font-semibold'>
				VCM in drinking water networks
			</h1>

			<TimelineSection />
			<ContaminationSection />
			<PubliHealthRiskSection />
		</main>
	)
}
