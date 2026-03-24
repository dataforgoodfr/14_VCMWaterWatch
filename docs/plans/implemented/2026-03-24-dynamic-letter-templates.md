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

**Seed data:** Populate the table with the 3 existing templates from `templates.ts` (locale `en`, all active) so there is no regression.

### New server-side fetch function

- **`webapp/lib/fetchLetterTemplates.ts`** — Fetches active templates from NocoDB filtered by locale (derived from the `[locale]` route param), ordered by `SortOrder`. Uses server-side in-memory cache with 5-min TTL, matching the existing `fetchMetaTables.ts` pattern. Maps NocoDB PascalCase fields (`Title`, `Icon`, `Content`) to the existing camelCase `Template` interface (`title`, `icon`, `content`).

### Frontend changes

- **`webapp/app/[locale]/act/data/templates.ts`** — Keep as fallback
- **`webapp/app/[locale]/act/page.tsx`** — Make `async`, destructure `locale` from `params` (same pattern as root `page.tsx`: `{ params }: { params: Promise<{ locale: string }> }`), call `fetchLetterTemplates(locale)`, pass templates as props to `GetInvolvedSection`
- **`webapp/app/[locale]/act/components/GetInvolvedSection.tsx`** — Accept `templates` as a prop instead of importing static array
- **`webapp/app/[locale]/act/components/ActionGuideSidebar.tsx`** — Delete (dead code: not imported anywhere, callouts already inlined in `ActionGuide.tsx`)

### Fallback strategy

If the fetch fails or returns empty, fall back to the current hardcoded templates from `data/templates.ts` so the page never renders empty. Since templates are passed as props from the server, no loading states are needed in child components.

## Open Questions

1. **Who manages templates?** Direct NocoDB UI is fine for now — no need for an admin page.
2. **i18n now or later?** Add the `Locale` field now but only populate `en` initially. Locale value is derived from the `[locale]` route param.
3. **Caching** — Use server-side in-memory cache with 5-min TTL, consistent with `fetchMetaTables.ts`.
