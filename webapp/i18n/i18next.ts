import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import resourcesToBackend from "i18next-resources-to-backend";
import LanguageDetector from "i18next-browser-languagedetector";
import { getI18nOptions, Locale } from "@/i18n/i18next.config";

const runsOnServerSide = typeof window === "undefined";

// Only run on client side
if (!runsOnServerSide) {
  i18next
    .use(initReactI18next)
    .use(LanguageDetector)
    .use(
      resourcesToBackend(
        (language: Locale, namespace: string | string[]) =>
          import(`./${language}/${namespace}.json`)
      )
    )
    .init({
      ...getI18nOptions(),
      lng: undefined, // let detect the language on client side
      detection: {
        order: ["path", "htmlTag", "cookie", "navigator"],
      },
      preload: [],
    });
}

export default i18next;
