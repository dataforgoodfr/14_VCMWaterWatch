export const VcmPollutionHistory = ({ dictionary }: { dictionary: Record<string, string> }) => {
	return (
		<div>
			{/* TODO: Use https://www.abui.io/components/timeline-steps */}
			<h1>{dictionary.main_title}</h1>
			<h2>{dictionary.history_heading}</h2>
			<div>{dictionary.history_line_1975_title}</div>
			<p>{dictionary.history_line_1975_text}</p>
			<div>{dictionary.history_line_1978_title}</div>
			<p>{dictionary.history_line_1978_text}</p>
		</div>
	)
}
