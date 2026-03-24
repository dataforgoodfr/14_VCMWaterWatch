# Dynamic Letter Templates from NocoDB

## Goal

Replace hardcoded letter templates with records stored in NocoDB, allowing non-developers to edit template text, add new templates, and support future i18n — without code changes.

## Proposed Changes

### NocoDB: New `LetterTemplate` table

| Field | Type | Notes |
|---|---|---|
| Title | Text | e.g. "Letter to the mayor" |
| Icon | Text | Emoji string |
| Content | Long Text | Template body with `[PLACEHOLDER]` tokens |
| SortOrder | Number | Display ordering |
| Locale | Text | `en`, `fr`, etc. (future i18n) |
| Active | Checkbox | Toggle visibility without deleting |

### New API route

- **`webapp/app/api/letter-templates/route.ts`** — GET, fetches active templates from NocoDB filtered by locale, ordered by `SortOrder`

### Frontend changes

- **`webapp/app/[locale]/act/data/templates.ts`** — delete (or keep as fallback)
- **`webapp/app/[locale]/act/components/GetInvolvedSection.tsx`** — fetch templates from API on mount instead of importing static array
- **`webapp/app/[locale]/act/components/ActionGuideSidebar.tsx`** — same
- **`webapp/app/[locale]/act/components/ContributeDataSection.tsx`** — same (if it uses templates directly)

Consider a shared hook: `webapp/hooks/useLetterTemplates.ts` — SWR/fetch with static fallback on error.

### Fallback strategy

If the API call fails, fall back to the current hardcoded templates so the page never renders empty.

## Open Questions

1. **Who manages templates?** Direct NocoDB UI, or do we need an admin page?
2. **i18n now or later?** Add the `Locale` field now but only populate `en` initially?
3. **Caching** — templates rarely change. Cache at API level (e.g. 1h revalidate) or client-side?
