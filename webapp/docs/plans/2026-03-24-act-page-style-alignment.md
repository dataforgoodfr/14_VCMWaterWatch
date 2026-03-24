# Act Page Style Alignment

## Goal

Align the Act page (`/act`) with the site's navy/aqua design system used on the homepage and other pages.

## Current Issues

- Act page uses generic Tailwind grays (`text-gray-900`, `text-gray-800`, `bg-gray-200`) instead of the navy palette
- Headings use default fonts instead of `font-[lexend]`
- No use of `InfoCard` component or navy left-border styling
- Alert boxes use generic `blue-50`/`amber-50`/`red-50` instead of navy/aqua tones
- Page layout uses `max-w-5xl` instead of `container mx-auto px-4 md:px-8` like other pages

## Proposed Changes

### `app/[locale]/act/page.tsx`

- Change layout wrapper from `max-w-5xl` to `container mx-auto px-4 md:px-8`
- Use `text-navy-800 font-[lexend]` for h1
- Add `SectionSeparator` between hero area and content if appropriate

### `app/[locale]/act/components/ActSearchSection.tsx`

- h2: `text-navy-800 font-[lexend] text-2xl` (was `text-xl text-gray-800`)

### `app/[locale]/act/components/ActionGuide.tsx`

- h2: `text-navy-800 font-[lexend] text-2xl` (was `text-xl text-gray-800`)
- Description text: `text-navy-800` instead of `text-gray-600`

### `app/[locale]/act/components/ScenarioColumns.tsx`

- Card container: use `InfoCard`-style `border-l-4 border-navy-800 rounded-r-2xl` instead of generic `border-gray-200 rounded-lg`
- Card background: `bg-navy-50` instead of `bg-white`
- Title text: `text-navy-800` instead of `text-gray-900`
- Body text: `text-navy-800` instead of `text-gray-700`
- Colored alert boxes (yellow/red) can stay as-is for semantic meaning (warnings/danger)
- Links: `text-navy-600` instead of `text-blue-600`

### `app/[locale]/act/components/ZoneResultPanel.tsx`

- Card: `border-l-4 border-navy-800 rounded-r-2xl bg-navy-50`
- Text colors: `text-navy-800` / `text-navy-600` replacing grays
- Label dt: `text-navy-600` instead of `text-gray-500`

### `app/[locale]/act/components/ActionGuideSidebar.tsx`

- "Important reminder" box: `bg-navy-100 border-navy-300` with `text-navy-800`/`text-navy-900`
- Letter template buttons: `border-navy-200 bg-navy-50` with `text-navy-800`
- Warning box: keep amber for semantic meaning, or switch to `bg-aqua-100 border-aqua-400 text-aqua-800`

## Open Questions

- Should the Act page have a hero section similar to other pages, or is the current simpler layout preferred?
- Should we wrap the scenario columns in an `InfoCard` for consistency?
