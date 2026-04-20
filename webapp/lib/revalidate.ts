/**
 * Shared ISR (Incremental Static Regeneration) revalidation interval for
 * semi-static pages that are updated infrequently (country profiles, About,
 * Act, …).
 *
 * Adjust this single constant to change the TTL for all pages that import it.
 */
export const SEMI_STATIC_REVALIDATE_SECONDS = 300
