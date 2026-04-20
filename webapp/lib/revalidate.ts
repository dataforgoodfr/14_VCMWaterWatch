/**
 * Shared ISR (Incremental Static Regeneration) revalidation constant.
 *
 * Use `export const revalidate = SEMI_STATIC_REVALIDATE_SECONDS` in any
 * Next.js page or layout that changes infrequently (country profiles, about
 * page, act page, etc.).  Centralised here so the TTL is adjustable in one
 * place.
 */
export const SEMI_STATIC_REVALIDATE_SECONDS = 300
