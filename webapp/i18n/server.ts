import { headerName } from "./i18next.config";
import { headers } from "next/headers";
import { getServerTranslation } from "./index";
import type { Locale } from "./i18next.config";

interface GetTOptions {
  keyPrefix?: string;
  [key: string]: unknown;
}

export async function getT(
  ns: string | string[],
  options?: GetTOptions & { locale?: Locale }
) {
  // Allow explicit locale override, otherwise try to read from headers
  let lng: Locale;

  if (options?.locale) {
    lng = options.locale;
  } else {
    const headerList = await headers();
    lng = (headerList.get(headerName) || "en") as Locale;
  }
  const otherOptions = { ...(options || {}) } as GetTOptions;

  return getServerTranslation(lng, ns, otherOptions);
}
