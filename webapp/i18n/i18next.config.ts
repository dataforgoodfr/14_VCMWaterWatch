export const i18n = {
  defaultLocale: "en",
  locales: ["en", "fr"],
} as const;
export type Locale = (typeof i18n)["locales"][number];

export const cookieName = "i18next";
export const fallbackLanguage = "en";
export const defaultNamespace = "default";
export const headerName = "x-i18next-current-language";
export const languages: Locale[] = [fallbackLanguage, "fr"];
export const languagesOptionsTranslations = {
  en: "English",
  fr: "Français",
};

export function getI18nOptions(
  lng = fallbackLanguage,
  ns: string | string[] = defaultNamespace // file from which we read the dictionary content
) {
  return {
    supportedLngs: languages,
    fallbackLng: fallbackLanguage,
    lng,
    fallbackNS: defaultNamespace,
    defaultNS: defaultNamespace,
    ns,
  };
}
