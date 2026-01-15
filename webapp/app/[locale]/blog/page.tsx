import { fetchBlogPosts } from '@/lib/fetchBlogPosts'
import Blog from './components/Blog'
import notFound from '../../not-found'
import { Locale } from '@/i18n/i18next.config'

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
	const { locale } = await params
	const blogPosts = await fetchBlogPosts({ locale })

	if (!blogPosts || blogPosts.length === 0) {
		notFound()
	}

	return <Blog blogCards={blogPosts} locale={locale as Locale} />
}
