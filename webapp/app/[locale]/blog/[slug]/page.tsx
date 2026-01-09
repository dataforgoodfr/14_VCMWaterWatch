import { fetchBlogPost } from "@/lib/fetchBlogPost";
import { notFound } from "next/navigation";
import { Blogpost } from "./components/BlogPost";

interface PageProps {
  params: { slug: string; locale: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

export default async function Page({ params }: PageProps) {
  const { slug, locale } = await params;
  const blogPost = await fetchBlogPost({ slug, locale });

  if (!slug || !blogPost) {
    notFound();
  } else {
    return <Blogpost post={blogPost} />;
  }
}
