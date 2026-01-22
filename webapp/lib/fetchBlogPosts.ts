import { BlogPostRecord } from '@/types/apiTypes'
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'

interface FetchBlogPostsParams {
	locale: string
	isAll?: boolean
}

export async function fetchBlogPosts({ locale, isAll }: FetchBlogPostsParams) {
	try {
		const blogPostsTableId = await getTableIdByName('BlogPost')
		const queryAll = isAll ? '' : `~and(Language,eq,${locale})`

		const blogPostsResponse = await instance.get<FetchResponseRecords<BlogPostRecord>>(
			`/data/${process.env.NOCODB_BASE_ID}/${blogPostsTableId}/records?${queryAll}`
		)

		if (blogPostsResponse.status !== 200) {
			throw new Error(`Failed to fetch blog posts: ${blogPostsResponse.statusText}`)
		}

		const blogPostsData = blogPostsResponse.data

		return blogPostsData.records || []
	} catch (error) {
		console.error('Error fetching blog posts:', error)
		return []
	}
}
