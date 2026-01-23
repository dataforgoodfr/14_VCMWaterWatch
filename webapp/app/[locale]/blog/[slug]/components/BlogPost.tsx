import NextImage from 'next/image'

import { format } from 'date-fns'

import ReactMarkdown from 'react-markdown'

import { cn } from '@/lib/utils'
import { BlogPostRecord } from '@/types/apiTypes'

interface BlogpostProps {
	className?: string
	post: BlogPostRecord
}

const components = {
	h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
		<h1 className='my-4 scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl' {...props} />
	),
	h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
		<h2
			className='my-3 scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0'
			{...props}
		/>
	),
	p: (props: React.HTMLAttributes<HTMLParagraphElement>) => <p className='leading-7 not-first:mt-6' {...props} />
}

const Blogpost = ({ post, className }: BlogpostProps) => {
	const { fields } = post
	const { Title, Image, CreatedDate, Subtitle, Content } = fields

	return (
		<section className={cn('flex items-center justify-center py-32', className)}>
			<div className='container'>
				<div className='mx-auto flex max-w-5xl flex-col items-center gap-4 text-center'>
					<h1 className='max-w-3xl text-5xl font-semibold text-pretty md:text-6xl'>{Title}</h1>
					<h3 className='text-muted-foreground max-w-3xl text-lg md:text-xl'>{Subtitle}</h3>
					<div className='flex items-center gap-3 text-sm md:text-base'>
						<span>
							<span className='ml-1'>on {format(CreatedDate, 'MMMM d, yyyy')}</span>
						</span>
					</div>
					<NextImage
						src={Image[0].signedUrl}
						alt={Subtitle}
						width={1200}
						height={675}
						className='mt-4 mb-8 aspect-video w-full rounded-lg border object-cover'
					/>
				</div>

				<div className='dark:prose-invert mx-auto max-w-5xl'>
					<ReactMarkdown components={components}>{Content}</ReactMarkdown>
				</div>
			</div>
		</section>
	)
}

export { Blogpost }
