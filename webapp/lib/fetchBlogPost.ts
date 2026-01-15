import { BlogPost } from '@/types/apiTypes'
import { FetchResponse, instance } from './instance'
import { getTableIdByName } from './fetchMetaTables'

export interface FetchBlogPostsParams {
	slug: string
}

export async function fetchBlogPost({ slug }: FetchBlogPostsParams) {
	try {
		const blogPostTableId = await getTableIdByName('BlogPost')

		const blogPostResponse = await instance.get(`/tables/${blogPostTableId}/records?where=(Slug,eq,${slug})`)

		if (blogPostResponse.status !== 200) {
			throw new Error(`Failed to fetch blog post: ${blogPostResponse.statusText}`)
		}

		const blogPostData: FetchResponse<BlogPost> = blogPostResponse.data

		return blogPostData.list[0] || null
	} catch (error) {
		console.error('Error fetching blog post:', error)
		return null
	}
}
