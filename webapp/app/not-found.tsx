import Link from 'next/link'
import Image from 'next/image'

import { Button } from '@/components/ui/button'

const NotFound = () => {
	return (
		<div className='grid min-h-screen grid-cols-1 lg:grid-cols-2'>
			<div className='flex flex-col items-center justify-center px-4 py-8 text-center'>
				<h2 className='mb-6 text-5xl font-semibold'>Whoops!</h2>
				<h3 className='mb-1.5 text-3xl font-semibold'>Something went wrong</h3>
				<p className='text-muted-foreground mb-6 max-w-sm'>
					The page you&apos;re looking for isn&apos;t found, we suggest you back to home.
				</p>
				<Button asChild size='lg' className='rounded-lg text-base'>
					<Link
						href='/'
						className='bg-primary-600 hover:bg-primary-800 focus:ring-primary-300 dark:focus:ring-primary-900 my-4 inline-flex rounded-lg px-5 py-2.5 text-center text-sm font-medium text-white focus:ring-4 focus:outline-none'
					>
						Back to Homepage
					</Link>
				</Button>
			</div>
			<div className='relative max-h-screen w-full p-2 max-lg:hidden'>
				<div className='h-full w-full rounded-2xl bg-black' />
				<Image
					src='https://cdn.shadcnstudio.com/ss-assets/blocks/marketing/error/image-1.png'
					alt='404 illustration'
					width={406}
					height={406}
					className='absolute top-1/2 left-1/2 h-[clamp(260px,25vw,406px)] -translate-x-1/2 -translate-y-1/2'
					style={{ width: 'auto', height: 'auto' }}
					priority
				/>
			</div>
		</div>
	)
}

export default NotFound
