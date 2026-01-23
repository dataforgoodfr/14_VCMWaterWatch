import Image from 'next/image'

import { ArrowRightIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardTitle, CardDescription, CardHeader, CardFooter } from '@/components/ui/card'

import { getT } from '@/i18n/server'
import type { Locale } from '@/i18n/i18next.config'
import { BlogPostRecord } from '@/types/apiTypes'

export default async function Blog({ blogCards, locale }: { blogCards: BlogPostRecord[]; locale: Locale }) {
	const { t } = await getT('default', { locale })

	return (
		<section className='py-8 sm:py-16 lg:py-24'>
			<div className='mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'>
				<div className='mb-12 space-y-4 text-center sm:mb-16 lg:mb-24'>
					<p className='text-primary text-sm font-medium uppercase'>{t('blog-list')}</p>
					<h2 className='text-2xl font-semibold md:text-3xl lg:text-4xl'>{t('blog-resources')}</h2>
					<p className='text-muted-foreground text-xl'>{t('blog-get-info')}</p>
				</div>

				<div className='grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3'>
					{blogCards.map(item => (
						<Card className='pt-0 shadow-none max-lg:last:col-span-full' key={item.fields.Slug}>
							<CardContent className='px-0'>
								<div className='relative aspect-video h-60 w-full overflow-hidden rounded-t-xl'>
									{item.fields.Image[0].signedUrl && (
										<Image src={item.fields.Image[0].signedUrl} alt={item.fields.Alt} fill className='object-cover' />
									)}
								</div>
							</CardContent>
							<CardHeader className='mb-2 gap-3'>
								<CardTitle className='text-xl'>
									<a href={`blog/${item.fields.Slug}`}>{item.fields.Title}</a>
								</CardTitle>
								<CardDescription className='text-base'>{item.fields.Subtitle}</CardDescription>
							</CardHeader>
							<CardFooter>
								<Button className='group rounded-lg text-base has-[>svg]:px-6' size='lg' asChild>
									<a href={`blog/${item.fields.Slug}`}>
										{t('blog-read-more')}
										<ArrowRightIcon className='transition-transform duration-200 group-hover:translate-x-0.5' />
									</a>
								</Button>
							</CardFooter>
						</Card>
					))}
				</div>
			</div>
		</section>
	)
}
