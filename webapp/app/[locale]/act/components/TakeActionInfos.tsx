import { ClockIcon, FileTextIcon, InfoIcon } from 'lucide-react'

const infos = [
	{
		icon: <InfoIcon />,
		title: 'Why this matters',
		content:
			'VCM is a chemical compound that can migrate from old PVC pipes into drinking water. Transparency about water quality is a fundamental right.'
	},
	{
		icon: <ClockIcon />,
		title: 'What you can do',
		content:
			'Request recent analyses, ask your water utility the right questions, and demand clear written answers about the measures being taken.'
	},
	{
		icon: <FileTextIcon />,
		title: 'Why written records matter',
		content:
			'Documented evidence is essential for future claims, repairs, or compensation requests. Keep all correspondence.'
	}
]

export default function TakeActionInfos() {
	return (
		<div className='grid grid-cols-1 gap-6 lg:grid-cols-3 lg:items-stretch'>
			{infos.map(infos => (
				<div key={infos.title} className='flex h-full flex-col gap-2 rounded-sm border border-gray-200 bg-white p-8'>
					<span className='flex h-12 w-12 items-center justify-center rounded-md bg-gray-100 p-3'>{infos.icon}</span>
					<h3 className='font-navy-800 font-weight-500 font-[lexend] text-[19px]'>{infos.title}</h3>
					<p className='text-[16px] text-gray-600'>{infos.content}</p>
				</div>
			))}
		</div>
	)
}
