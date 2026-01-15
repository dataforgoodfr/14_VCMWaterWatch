import { notFound } from 'next/navigation'

import { fetchBlogPost } from '@/lib/fetchBlogPost'
import { Blogpost } from './components/BlogPost'

interface PageProps {
	params: { slug: string }
	searchParams?: Record<string, string | string[] | undefined>
}

export default async function Page({ params }: PageProps) {
	// eslint-disable-next-line @typescript-eslint/await-thenable
	const { slug } = await params
	const blogPost = await fetchBlogPost({ slug })

	if (!slug || !blogPost) {
		notFound()
	} else {
		return <Blogpost post={blogPost} />
	}
}
