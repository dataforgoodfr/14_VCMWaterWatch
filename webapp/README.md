This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Components and UI libraries

We use [Shadcn](https://ui.shadcn.com/) for components, in combination with [TailwindCSS](https://tailwindcss.com/) to style a component inline.
To add a shadcn component:
```bash
npx shadcn@latest add navigation-menu
```
For icons, we use the default library in Shadcn, [Lucide](https://www.shadcn.io/icons/lucide).

## Internationalisation i18n

For the internationalisation of the app we are using [next-i18next](https://github.com/i18next/next-i18next). Our setup is based on this article from [Locize](https://www.locize.com/blog/i18n-next-app-router/).

## BlogPosts / news markdown

We use the library [react-markdown](https://remarkjs.github.io/react-markdown/) to display blog posts / news. Visit [CommonMark](https://commonmark.org) for Markdown guidelines and tutorial. You can style the components by passing the components props to ReactMarkdown. 

```bash
<ReactMarkdown components={components}>{Content}</ReactMarkdown>
```
