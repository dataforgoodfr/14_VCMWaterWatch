"use client";

import { useEffect, useState } from "react";
import { useTranslation as useTranslationOrg } from "react-i18next";
import { useCookies } from "react-cookie";
import { cookieName } from "@/i18n/i18next.config";
import type { Locale } from "@/i18n/i18next.config";

const runsOnServerSide = typeof window === "undefined";

/**
 * Client-side translation hook using React i18next
 * Handles language detection, cookies, and state management
 */
export function useClientTranslation(
  lng?: Locale,
  ns?: string | string[],
  options?: object
) {
  const [cookies, setCookie] = useCookies([cookieName]);
  const ret = useTranslationOrg(ns, options);
  const { i18n } = ret;

  if (runsOnServerSide && lng && i18n.resolvedLanguage !== lng) {
    i18n.changeLanguage(lng);
  } else {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [activeLng, setActiveLng] = useState(i18n.resolvedLanguage);
    
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useEffect(() => {
      if (activeLng === i18n.resolvedLanguage) return;
      setActiveLng(i18n.resolvedLanguage);
    }, [activeLng, i18n.resolvedLanguage]);
    
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useEffect(() => {
      if (!lng || i18n.resolvedLanguage === lng) return;
      i18n.changeLanguage(lng);
    }, [lng, i18n]);
    
    // eslint-disable-next-line react-hooks/rules-of-hooks
    useEffect(() => {
      if (cookies.i18next === lng) return;
      setCookie(cookieName, lng, { path: "/" });
    }, [lng, cookies.i18next, setCookie]);
  }
  
  return ret;
}
