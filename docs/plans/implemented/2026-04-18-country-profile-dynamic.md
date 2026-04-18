# Country Profile — make detail page dynamic from CountryData

## Goal

The country-profile detail panel currently mixes NocoDB data (`Country.PVC Level`, `VCM Level`, link counts) with hardcoded content (the "More details" accordion list, the "Missing data" cards). Drive all of it from the `CountryData` NocoDB table, locale-aware.

## NocoDB `CountryData` schema (confirmed)

Columns used:
- `Country_id` (FK → Country.Id)
- `Type` — SingleSelect: `stat`, `legislation`, `missing_data`
- `Language` — SingleSelect: `en`, `fr`, `de`
- `Order` — Number (ordering within a type; for `stat`, Order 1..4 = network / % exposure / # tests / risk zones)
- `Title` — SingleLineText (meaningful only for `stat`; blank/null for the others)
- `Content` — LongText

Stat Order mapping (from data inspection):
- 1 → "Network affected by VCM" (currently shown from `PVC Level`)
- 2 → "% Network exposed to VCM" (currently from `VCM Level`)
- 3 → "Number of VCM tests" (currently from distribution-zone count)
- 4 → "Identified risk zones" (currently from municipality count)

## Proposed changes

### 1. New lib/fetchCountryDataForCountry.ts

Fetch all `CountryData` rows for a given `Country_id` + `Language`, sorted by `Order`. One NocoDB call, `where=(Country_id,eq,N)~and(Language,eq,xx)`, fields `Id,Type,Order,Title,Content`.

### 2. Extend `fetchCountryByCode` / API route

Two options — prefer (a) for simplicity:

(a) Have `fetchCountryByCode(code, locale)` additionally fetch CountryData and return `{ country, data: CountryDataRecord[] }`. API route `/api/countries/[code]` accepts `?locale=xx` and returns both.

(b) Separate endpoint `/api/countries/[code]/data?locale=xx`. Two client requests.

Going with (a).

Drop `PVC Level`, `VCM Level`, `Distribution Zones`, `Municipalities` from `COUNTRY_DETAIL_FIELDS` (no longer used for stats). Keep `Name, Code, Geometry, Actors, Url`.

### 3. Types (`types/apiTypes.ts`)

```ts
export interface CountryDataFields {
  Id: number
  Type: 'stat' | 'legislation' | 'missing_data'
  Order: number
  Title: string | null
  Content: string | null
}
export type CountryDataRecord = Record<CountryDataFields>
```

Remove `'PVC Level'`, `'VCM Level'`, `'Distribution Zones'`, `'Municipalities'` from `CountryDetailFields`.

### 4. `CountryCarousel.tsx`

- Accept/propagate `locale` (read from `useLocale` via next-intl or pass down from page).
- Include `?locale=` on the fetch.
- Pass `data` prop to `CountryProfileDetail`.

### 5. `CountryProfileDetail.tsx`

- Take `data: CountryDataRecord[]` prop.
- Stats row: filter `Type==='stat'`, sort by `Order`, render `StatCard`s using NocoDB `Title` directly as the label and `Content` (fallback `—`) as the value. Drops the current formatCountStat / distribution-zone / municipality logic. Keep the existing icon mapping by Order (1→TrainTrack, 2→Percent, 3→FlaskConical, 4→MapPin).
- "More details" accordion: filter `Type==='legislation'`, sort by `Order`, render `Content` as `<li>` entries. Hide the accordion if no non-empty entries.
- "Missing data" cards: filter `Type==='missing_data'`, sort by `Order`. Each row has only `Content` (no per-row title in NocoDB). Render as `<div>` with `Content` only — drop the hardcoded `['Full PVC network inventory', ...]` titles. Hide section if empty.

### 6. Page (`app/[locale]/country-profile/page.tsx`)

Pick up `locale` from params and pass to carousel.

### 7. i18n strings

None needed — stat labels come straight from NocoDB `Title`.

## Files touched

- `webapp/types/apiTypes.ts`
- `webapp/lib/fetchCountryByCode.ts`
- new `webapp/lib/fetchCountryData.ts`
- `webapp/app/api/countries/[code]/route.ts`
- `webapp/app/[locale]/country-profile/page.tsx`
- `webapp/app/[locale]/country-profile/components/CountryCarousel.tsx`
- `webapp/app/[locale]/country-profile/components/CountryProfileDetail.tsx`

## Open questions

(none — see Decisions above)

<!-- resolved -->

## Decisions

1. Stat card titles: use NocoDB `Title` directly, no fallback.
2. `legislation` rendered as bullet list inside the accordion (preserves current look).
3. `fetchCountries` (list) untouched.
4. Unsupported locale → fall back to `en` if fetched CountryData list is empty.
5. Accordion stays collapsed by default.

## Post-implementation amendments

- **COUNTRY_DETAIL_FIELDS change**: plan said keep `Name, Code, Geometry, Actors, Url`. Actual shipped set is `Name, Code, Geometry, Image` — `Url` was replaced by `Image` (NocoDB attachment, resolved via `signedUrl`) to support the illustration in the detail card, and `Actors` was dropped because it is no longer referenced by `CountryProfileDetail` (stats now come from `CountryData`). `CountryDetailFields` type updated accordingly.
- **Locale fallback (Decision #4)**: initially shipped with no fallback; corrected in follow-up so `fetchCountryDataForCountry` retries once with `fallbackLanguage` when the requested locale returns zero rows.
- **API route locale allowlist** now sourced from `i18n.locales` / `fallbackLanguage` instead of a hardcoded set.
