import { notFound } from 'next/navigation'

import { fetchBlogPost } from '@/lib/fetchBlogPost'
import { Blogpost } from './components/BlogPost'

interface PageProps {
	params: { slug: string }
	searchParams?: { [key: string]: string | string[] | undefined }
}

export default async function Page({ params }: PageProps) {
	const { slug } = await params
	const blogPost = await fetchBlogPost({ slug })

	if (!slug || !blogPost) {
		notFound()
	} else {
		return <Blogpost post={blogPost} />
	}
}
