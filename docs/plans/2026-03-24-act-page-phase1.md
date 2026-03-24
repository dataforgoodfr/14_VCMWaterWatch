# Phase 1 Implementation Plan — Act Page Search + Static Action Guide

## Goal

Deliver a functional `/act` page with:
1. A search that finds distribution zones by municipality/zone/actor name
2. A results panel showing zone details + color badge
3. A static action guide with all 3 scenarios (accordion) + sidebar with templates

No forms, no data submission — that's phase 2.

---

## Prerequisites

- [ ] Manually add a `SearchIndex` text field to the `DistributionZone` table in NocoDB (via UI)
- [ ] Confirm color code thresholds with data team (what values do `VCM Level` / `PVC Level` hold?)
- [ ] Get final email template text (letter to mayor, email to water company, letter to MP)

---

## Task 1: Python script to build SearchIndex (~1h)

**File:** `pipelines/tasks/build_search_index.py`

Follows existing pipeline patterns (Prefect task + `DatabaseHelper`).

### Logic

```python
@task
def build_search_index_task(db_helper):
    # 1. Load all DistributionZone records with fields:
    #    Id, Name, ActorName (linked), Municipality names (linked/rollup)
    zones = db_helper.load_all_records(
        "DistributionZone",
        fields=["Id", "Name", "ActorName"]
    )
    # Note: Municipality names may need a separate load if not available
    # as a rollup field. Check what "Municipalities" returns — it's a
    # link count, not names. May need:
    #   - Load all Municipality records with fields=["Name", "DistributionZone"]
    #   - Group by DZ ID
    #   - Join names

    # 2. For each zone, build index string:
    #    "{zone_name} | {municipality1}, {municipality2} | {actor1}, {actor2}"
    for zone in zones:
        parts = [zone["Name"]]
        if zone.get("_municipality_names"):
            parts.append(", ".join(zone["_municipality_names"]))
        if zone.get("ActorName"):
            actor_names = zone["ActorName"]
            if isinstance(actor_names, list):
                parts.append(", ".join(actor_names))
            else:
                parts.append(str(actor_names))
        zone["SearchIndex"] = " | ".join(parts)

    # 3. Batch update
    updates = [{"Id": z["Id"], "SearchIndex": z["SearchIndex"]} for z in zones]
    db_helper.update_records(updates, "DistributionZone")

@flow
def build_search_index():
    db = services.db_helper()
    build_search_index_task(db)
```

### Sub-tasks
1. Check how municipality names are accessible from DZ records (linked field rollup? separate query?)
2. Implement the script
3. Run it once to populate the field
4. Verify in NocoDB that `SearchIndex` is populated correctly

---

## Task 2: Modify search API route (~0.5h)

**File:** `webapp/app/api/searchbydistributionzone/route.ts`

### Changes
- Change NocoDB query filter from `(Name,like,{query})` to `(SearchIndex,like,{query})`
- Expand `fields=` to return: `Name`, `Country`, `ActorName` (for dropdown display)
- Keep limit at 10

**File:** `webapp/lib/fetchDistributionZones.ts`
- Update the query parameter and fields list
- Update return type if needed (add `ActorName` to `DistributionZoneGeoLimitedFields`)

**File:** `webapp/types/apiTypes.ts`
- Add `ActorName?: string[]` to `DistributionZoneGeoLimitedFields`

---

## Task 3: New detail endpoint (~1h)

**File:** `webapp/app/api/distributionzone/[id]/route.ts` (new)

### Endpoint
`GET /api/distributionzone/{id}`

### Returns
Full zone record with fields:
- `Name`, `Code`
- `Country` (linked)
- `PVC Level`, `VCM Level`
- `ActorName`, `ActorEmail`
- `Municipality Geometries` (or a separate municipality names query)

### Implementation
```typescript
export async function GET(request: Request, { params }: { params: { id: string } }) {
    const zoneId = params.id
    const tableId = await getTableIdByName('DistributionZone')
    const response = await instance.get(
        `/data/${process.env.NOCODB_BASE_ID}/${tableId}/records/${zoneId}`
    )
    return NextResponse.json(response.data)
}
```

**File:** `webapp/types/apiTypes.ts`
- Add a `DistributionZoneDetailFields` interface with all fields above

**File:** `webapp/lib/fetchDistributionZoneDetail.ts` (new)
- `fetchDistributionZoneDetail(id: number): Promise<DistributionZoneDetailRecord>`

---

## Task 4: Debounced autocomplete SearchBar (~1.5h)

**File:** `webapp/app/[locale]/act/components/ActSearchBar.tsx` (new)

Don't modify the existing `SearchBar` — create a new one specific to the act page.

### Behavior
- Text input with placeholder "Enter your city, postal code, or address..."
- On input change: debounce 300ms, min 3 chars, call `/api/searchbydistributionzone?q=...`
- Show dropdown below input with results:
  ```
  Zone du Nord — France
    Veolia Eau
  Zone de l'Ouest — France
    Suez Eau
  ```
  Each item shows: zone name + country on first line, actor name on second line (muted)
- On item click: call detail endpoint, populate results panel, close dropdown
- On click outside / Escape: close dropdown
- Loading state: spinner in dropdown
- Empty state: "No results"

### Implementation notes
- Custom hook `useDebounce(value, delay)` or inline `setTimeout`
- No external autocomplete library needed — simple `div` dropdown with `absolute` positioning
- Keyboard nav (up/down/enter) is nice-to-have, not phase 1

---

## Task 5: Results panel (~1.5h)

**File:** `webapp/app/[locale]/act/components/ZoneResultPanel.tsx` (new)

### UI
Appears below the search bar when a zone is selected. Card with:

```
┌─────────────────────────────────────────────────┐
│  Zone du Nord                          🟢       │
│  France                                         │
│─────────────────────────────────────────────────│
│  Company     Veolia Eau Nord                   │
│  Contact      eau-nord@veolia.fr                │
│  PVC Level    —                                 │
│  VCM Level    Compliant                         │
│  Municipalities  Lille, Roubaix, Tourcoing, ... │
└─────────────────────────────────────────────────┘
```

### Color badge
Derive from VCM/PVC levels. For now, use a simple mapping function that can be updated once thresholds are confirmed:

```typescript
// lib/colorCode.ts
type ColorCode = 'green' | 'yellow' | 'orange' | 'red'

export function deriveColorCode(vcmLevel: string | null, pvcLevel: string | null): ColorCode {
    // Placeholder logic — update when thresholds confirmed
    if (!vcmLevel || vcmLevel === 'Conforme') return 'green'
    if (vcmLevel === 'Vigilance') return 'yellow'
    // ...
    return 'red'
}
```

### Props
```typescript
interface ZoneResultPanelProps {
    zone: DistributionZoneDetailRecord | null
    loading: boolean
}
```

---

## Task 6: Static action guide (~2.5h)

**File:** `webapp/app/[locale]/act/components/ActionGuide.tsx` (new)

Two-column layout: `grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-8`

### Left column — Scenarios accordion

Uses `@radix-ui/react-accordion` (already in deps). Three items, all collapsed by default.

**File:** `webapp/app/[locale]/act/components/ScenarioAccordion.tsx` (new)

Each accordion item:
- Trigger: colored badge (circle or pill) + scenario title
- Content: static English text, hardcoded

Content per scenario — see requirements doc. Key points:
- 🟢 Green: 3 lines + CTA link to step 3 (anchor `#contribute`)
- 🟡🟠 Yellow/Orange: caution banner + 3 numbered steps
- 🔴 Red: alert banner (red bg) + 4 numbered steps

Numbered steps rendered as an `<ol>` with styled list items. Sub-steps within "Contact your water provider" as nested `<ul>`.

### Right column — Sticky sidebar

**File:** `webapp/app/[locale]/act/components/ActionGuideSidebar.tsx` (new)

`sticky top-24` on desktop, normal flow on mobile.

Contains:
1. **"Important reminder"** card — blue/info styled box with the legal reminder text (you're paying for a service, safe water is a legal obligation)
2. **"Letter templates"** — 3 stacked cards, each clickable:
   - Icon + title ("Letter to the mayor", "Email to water company", "Letter to MP")
   - On click: opens a `Sheet` (radix dialog, already have `sheet.tsx`) with template text + copy button
3. **⚠️ Notice** — "Keep written records of all communications"

**File:** `webapp/app/[locale]/act/components/TemplateModal.tsx` (new)

Uses existing `sheet.tsx` component. Props:
```typescript
interface TemplateModalProps {
    title: string       // "Letter to the mayor"
    content: string     // full template text
    open: boolean
    onOpenChange: (open: boolean) => void
}
```
- Renders template text in a scrollable area
- "Copy" button → `navigator.clipboard.writeText()` + toast/feedback
- Template text hardcoded as English constants

---

## Task 7: Page shell + assembly (~0.5h)

**File:** `webapp/app/[locale]/act/page.tsx`

Replace placeholder with:

```tsx
export default function ActPage() {
    return (
        <main className="mx-auto w-full max-w-5xl px-6 py-16 space-y-16">
            <h1 className="text-3xl font-semibold text-gray-900">Agir</h1>

            {/* Step 1: Search */}
            <section id="rechercher">
                <ActSearchSection />
            </section>

            {/* Step 2: Action Guide */}
            <section id="guide">
                <ActionGuide />
            </section>

            {/* Steps 3 & 4: placeholder for phase 2 */}
        </main>
    )
}
```

`ActSearchSection` is a client component that owns the search state and renders both `ActSearchBar` and `ZoneResultPanel`.

---

## File Summary

| File | Action | Task |
|---|---|---|
| `pipelines/tasks/build_search_index.py` | New | 1 |
| `webapp/types/apiTypes.ts` | Edit | 2, 3 |
| `webapp/lib/fetchDistributionZones.ts` | Edit | 2 |
| `webapp/app/api/searchbydistributionzone/route.ts` | Edit | 2 |
| `webapp/lib/fetchDistributionZoneDetail.ts` | New | 3 |
| `webapp/app/api/distributionzone/[id]/route.ts` | New | 3 |
| `webapp/lib/colorCode.ts` | New | 5 |
| `webapp/app/[locale]/act/page.tsx` | Edit | 7 |
| `webapp/app/[locale]/act/components/ActSearchSection.tsx` | New | 4, 5 |
| `webapp/app/[locale]/act/components/ActSearchBar.tsx` | New | 4 |
| `webapp/app/[locale]/act/components/ZoneResultPanel.tsx` | New | 5 |
| `webapp/app/[locale]/act/components/ActionGuide.tsx` | New | 6 |
| `webapp/app/[locale]/act/components/ScenarioAccordion.tsx` | New | 6 |
| `webapp/app/[locale]/act/components/ActionGuideSidebar.tsx` | New | 6 |
| `webapp/app/[locale]/act/components/TemplateModal.tsx` | New | 6 |

---

## Total Estimate: ~8.5h

| Task | Hours |
|---|---|
| 1. Python search index script | 1 |
| 2. Modify search API route | 0.5 |
| 3. Detail endpoint | 1 |
| 4. Debounced autocomplete | 1.5 |
| 5. Results panel | 1.5 |
| 6. Static action guide + sidebar + templates | 2.5 |
| 7. Page shell | 0.5 |

---

## Implementation Order

1. **Task 1** — Python script (can run independently, no webapp dependency)
2. **Tasks 2 + 3** — API routes (backend, testable with curl)
3. **Tasks 4 + 5** — Search UI (depends on 2 + 3)
4. **Task 6** — Action guide (independent of search, can parallelize)
5. **Task 7** — Wire it all together

Tasks 1 and 6 can be done in parallel with everything else.
