import { fetchPageDictionary } from "@/lib/fetchPageDictionary";
import { VcmPollutionHistory } from "./components/VcmPollutionHistory";
import { notFound } from "next/navigation";
import { SUB_PAGES } from "@/routes/routes";

interface PageProps {
  params: { slug: string; locale: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

export default async function Page({ params }: PageProps) {
  const { slug, locale } = await params;
  const dictionary = await fetchPageDictionary({ slug, locale });

  if (!slug || !dictionary) {
    notFound();
  }

  switch (slug) {
    case SUB_PAGES.VCM_POLLUTION_HISTORY:
      return <VcmPollutionHistory dictionary={dictionary} />;
    default:
      notFound();
  }
}
