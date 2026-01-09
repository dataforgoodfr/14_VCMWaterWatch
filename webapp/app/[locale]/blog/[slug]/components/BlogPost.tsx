import { format } from "date-fns";

import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface BlogPostData {
  Title: string;
  // AuthorName: string;
  Image: string;
  CreatedDate: Date;
  Subtitle: string;
  Content: string;
}

interface BlogpostProps {
  className?: string;
  post?: BlogPostData;
}

const components = {
  h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h1
      className="scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl my-4"
      {...props}
    />
  ),
  h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2
      className="scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0 my-3"
      {...props}
    />
  ),
  p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="leading-7 not-first:mt-6" {...props} />
  ),
  // ...add more for blockquote, code, etc as desired
};

const Blogpost = ({ post, className }: BlogpostProps) => {
  const { Title, Image, CreatedDate, Subtitle, Content } = post;
  return (
    <section
      className={cn("py-32 flex items-center justify-center", className)}
    >
      <div className="container">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-4 text-center">
          <h1 className="max-w-3xl text-5xl font-semibold text-pretty md:text-6xl">
            {Title}
          </h1>
          <h3 className="max-w-3xl text-lg text-muted-foreground md:text-xl">
            {Subtitle}
          </h3>
          <div className="flex items-center gap-3 text-sm md:text-base">
            <span>
              {/* <a href="#" className="font-semibold">
                {authorName}
              </a> */}
              <span className="ml-1">
                on {format(CreatedDate, "MMMM d, yyyy")}
              </span>
            </span>
          </div>
          <img
            src={Image}
            alt="placeholder"
            className="mt-4 mb-8 aspect-video w-full rounded-lg border object-cover"
          />
        </div>

        <div className="mx-auto max-w-5xl dark:prose-invert">
          <ReactMarkdown components={components}>{Content}</ReactMarkdown>
        </div>
      </div>
    </section>
  );
};

export { Blogpost };
