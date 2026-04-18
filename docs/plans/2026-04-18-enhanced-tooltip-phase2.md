# Enhanced Distribution Zone Tooltip — Phase 2 Implementation Plan

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Add "Top 3 VCM Results" and a "Take action!" button to the map distribution zone tooltip, and support pre-filling the Act page when linked from the tooltip.

**Architecture:** Extend the existing `/api/distributionzone/[id]/tooltip` endpoint to also fetch the last 3 Analysis records (parallel query alongside PVC comment). The MapView tooltip renders analysis rows and a link button. The Act page reads an optional `zone` query param to auto-load the zone detail on arrival.

**Tech Stack:** Next.js (App Router), NocoDB REST API v3, MapLibre GL, Tailwind CSS, Vitest

**GitHub Issue:** https://github.com/dataforgoodfr/14_VCMWaterWatch/issues/78

---

## Data Reference

### Analysis table (NocoDB)
| Field       | Type   | Notes                                |
|-------------|--------|--------------------------------------|
| Date        | date   | Analysis date                        |
| Description | string | Not used in tooltip                  |
| CVMMeasure  | float  | VCM measurement in µg/L             |

Linked to DistributionZone via a Links field. Query pattern: `where=(DistributionZone,eq,{zoneId})&sort=-Date&pageSize=3&fields=Date,CVMMeasure`

### Tooltip API response shape (extended)
```json
{
  "pvcLevelComment": "Some comment...",
  "recentAnalyses": [
    { "date": "2026-04-22", "vcmMeasure": 10.901 },
    { "date": "2026-04-10", "vcmMeasure": 0.8 },
    { "date": "2026-04-14", "vcmMeasure": 0.4 }
  ]
}
```

---

## Task 1: Add analysis fetching utility + tests

**Files:**
- Create: `webapp/lib/fetchAnalysesForDistributionZone.ts`
- Create: `webapp/lib/__tests__/fetchAnalysesForDistributionZone.test.ts`

**Step 1: Write the failing test**

Create `webapp/lib/__tests__/fetchAnalysesForDistributionZone.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { formatAnalysisDate, type RecentAnalysis } from '../fetchAnalysesForDistributionZone'

describe('formatAnalysisDate', () => {
  it('formats ISO date to DD/MM/YYYY', () => {
    expect(formatAnalysisDate('2026-04-22')).toBe('22/04/2026')
  })

  it('formats ISO datetime to DD/MM/YYYY', () => {
    expect(formatAnalysisDate('2026-04-22T10:30:00Z')).toBe('22/04/2026')
  })

  it('returns raw string for unparseable dates', () => {
    expect(formatAnalysisDate('not-a-date')).toBe('not-a-date')
  })

  it('returns "—" for null/undefined', () => {
    expect(formatAnalysisDate(null)).toBe('—')
    expect(formatAnalysisDate(undefined)).toBe('—')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd webapp && npx vitest run lib/__tests__/fetchAnalysesForDistributionZone.test.ts`
Expected: FAIL — module not found

**Step 3: Implement the utility**

Create `webapp/lib/fetchAnalysesForDistributionZone.ts`:

```typescript
import { getTableIdByName } from './fetchMetaTables'
import { FetchResponseRecords, instance } from './instance'
import type { Record as NocoRecord } from '@/types/apiTypes'

export interface RecentAnalysis {
  date: string | null
  vcmMeasure: number | null
}

interface AnalysisFields {
  Date: string | null
  CVMMeasure: number | null
}

/**
 * Format an ISO date string to DD/MM/YYYY for display.
 */
export function formatAnalysisDate(value: string | null | undefined): string {
  if (value == null) return '—'
  const d = new Date(value)
  if (isNaN(d.getTime())) return value
  const dd = String(d.getUTCDate()).padStart(2, '0')
  const mm = String(d.getUTCMonth() + 1).padStart(2, '0')
  const yyyy = d.getUTCFullYear()
  return `${dd}/${mm}/${yyyy}`
}

/**
 * Fetch the most recent analyses (up to 3) for a distribution zone.
 * Queries the Analysis table sorted by Date descending, limited to 3 records.
 */
export async function fetchRecentAnalyses(distributionZoneId: number): Promise<RecentAnalysis[]> {
  try {
    const tableId = await getTableIdByName('Analysis')
    if (!tableId) return []

    const response = await instance.get<FetchResponseRecords<NocoRecord<AnalysisFields>>>(
      `/data/${process.env.NOCODB_BASE_ID}/${tableId}/records`,
      {
        timeout: 15000,
        params: {
          where: `(DistributionZone,eq,${distributionZoneId})`,
          sort: '-Date',
          pageSize: 3,
          fields: 'Date,CVMMeasure',
        },
      }
    )

    if (response.status !== 200 || !response.data.records?.length) {
      return []
    }

    return response.data.records.map((r) => ({
      date: r.fields.Date ?? null,
      vcmMeasure: r.fields.CVMMeasure ?? null,
    }))
  } catch (error) {
    console.error('Error fetching analyses for distribution zone:', error)
    return []
  }
}
```

**Step 4: Run test to verify it passes**

Run: `cd webapp && npx vitest run lib/__tests__/fetchAnalysesForDistributionZone.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add webapp/lib/fetchAnalysesForDistributionZone.ts webapp/lib/__tests__/fetchAnalysesForDistributionZone.test.ts
git commit -m "feat(api): add utility to fetch recent analyses for a distribution zone"
```

---

## Task 2: Extend the tooltip API endpoint

**Files:**
- Modify: `webapp/app/api/distributionzone/[id]/tooltip/route.ts`

**Step 1: Update the endpoint to return analyses**

Replace the contents of `webapp/app/api/distributionzone/[id]/tooltip/route.ts`:

```typescript
import { NextResponse } from 'next/server'

import { getTableIdByName } from '@/lib/fetchMetaTables'
import { fetchRecentAnalyses, type RecentAnalysis } from '@/lib/fetchAnalysesForDistributionZone'
import { instance } from '@/lib/instance'
import { HTTP_STATUS } from '@/types/httpTypes'

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  if (!id) {
    return NextResponse.json({ error: 'Zone ID is required' }, { status: HTTP_STATUS.BadRequest.code })
  }

  const zoneId = Number(id)

  if (!Number.isFinite(zoneId)) {
    return NextResponse.json({ error: 'Invalid zone ID' }, { status: HTTP_STATUS.BadRequest.code })
  }

  try {
    const tableId = await getTableIdByName('DistributionZone')

    if (!tableId) {
      return NextResponse.json({ error: 'Table not found' }, { status: HTTP_STATUS.InternalServerError.code })
    }

    const [zoneRes, recentAnalyses] = await Promise.all([
      instance.get(`/data/${process.env.NOCODB_BASE_ID}/${tableId}/records/${id}`, {
        timeout: 10000,
        params: { fields: 'PVC Level Comment' },
      }),
      fetchRecentAnalyses(zoneId),
    ])

    const data = zoneRes.data as { fields?: Record<string, unknown> }
    const f = data?.fields

    return NextResponse.json({
      pvcLevelComment: f?.['PVC Level Comment'] ?? null,
      recentAnalyses,
    })
  } catch (error) {
    console.error('Error in GET /api/distributionzone/[id]/tooltip:', error)
    return NextResponse.json(HTTP_STATUS.InternalServerError)
  }
}
```

**Step 2: Commit**

```bash
git add webapp/app/api/distributionzone/\[id\]/tooltip/route.ts
git commit -m "feat(api): extend tooltip endpoint with recent analyses"
```

---

## Task 3: Render analyses and "Take action" button in MapView tooltip

**Files:**
- Modify: `webapp/components/MapView.tsx`

**Step 1: Update state and API response type**

At the top of `MapView.tsx`, add the import:

```typescript
import { formatAnalysisDate, type RecentAnalysis } from '@/lib/fetchAnalysesForDistributionZone'
```

Also import `useLocale`:

```typescript
import useLocale from '@/hooks/useLocale'
```

Also import `Link` from Next.js:

```typescript
import Link from 'next/link'
```

Also import `ROUTES`:

```typescript
import { ROUTES } from '@/routes/routes'
```

Add state for analyses after the existing `zoneDetailPvcComment` state:

```typescript
const [zoneDetailAnalyses, setZoneDetailAnalyses] = useState<RecentAnalysis[]>([])
const [zoneDetailLoading, setZoneDetailLoading] = useState(false)
```

Get the locale at the top of the component:

```typescript
const locale = useLocale()
```

**Step 2: Update closeZoneCard to reset new state**

In the `closeZoneCard` callback, also reset analyses and loading:

```typescript
const closeZoneCard = useCallback(() => {
  setZoneDetailPvcComment(undefined)
  setZoneDetailAnalyses([])
  setZoneDetailLoading(false)
  setZoneCard(null)
}, [])
```

**Step 3: Update the API fetch effect**

Replace the existing `useEffect` that fetches `/api/distributionzone/${id}/tooltip`:

```typescript
useEffect(() => {
  if (!zoneCard?.zoneId) {
    return
  }

  const id = zoneCard.zoneId
  const ac = new AbortController()

  setZoneDetailLoading(true)

  void (async () => {
    try {
      const res = await fetch(`/api/distributionzone/${id}/tooltip`, { signal: ac.signal })

      if (!res.ok) {
        if (!ac.signal.aborted) {
          setZoneDetailPvcComment(null)
          setZoneDetailAnalyses([])
          setZoneDetailLoading(false)
        }
        return
      }

      const body = (await res.json()) as {
        pvcLevelComment: string | null
        recentAnalyses: RecentAnalysis[]
      }

      if (!ac.signal.aborted) {
        setZoneDetailPvcComment(body.pvcLevelComment)
        setZoneDetailAnalyses(body.recentAnalyses ?? [])
        setZoneDetailLoading(false)
      }
    } catch {
      if (!ac.signal.aborted) {
        setZoneDetailPvcComment(null)
        setZoneDetailAnalyses([])
        setZoneDetailLoading(false)
      }
    }
  })()

  return () => ac.abort()
}, [zoneCard?.zoneId])
```

**Step 4: Update tooltip JSX**

Replace the `<CardContent>` inside the zone card overlay:

```tsx
<CardContent className='flex flex-col gap-2 px-4 py-3'>
  <p className='text-navy-800 text-sm font-medium'>{zoneCard.name}</p>
  <div className='flex flex-wrap gap-2'>
    {zoneCardPvcBadge ? (
      <span
        className='inline-flex rounded-3xl border px-3 py-1.5 text-left text-xs font-medium'
        style={zoneCardPvcBadge.style}
      >
        {zoneCardPvcBadge.label}
      </span>
    ) : null}
    {zoneCardVcmBadge ? (
      <span
        className='inline-flex rounded-3xl border px-3 py-1.5 text-left text-xs font-medium'
        style={zoneCardVcmBadge.style}
      >
        {zoneCardVcmBadge.label}
      </span>
    ) : null}
  </div>
  {zoneDetailPvcComment ? (
    <p className='text-navy-600 text-xs'>{zoneDetailPvcComment}</p>
  ) : null}
  {zoneDetailLoading ? (
    <div className='flex flex-col gap-1.5 pt-1'>
      <div className='bg-navy-100 h-3 w-1/3 animate-pulse rounded' />
      <div className='bg-navy-100 h-2.5 w-3/4 animate-pulse rounded' />
      <div className='bg-navy-100 h-2.5 w-2/3 animate-pulse rounded' />
    </div>
  ) : zoneDetailAnalyses.length > 0 ? (
    <div className='pt-1'>
      <p className='text-navy-800 text-xs font-semibold'>Top 3 VCM Results</p>
      <ul className='text-navy-600 mt-1 list-inside list-disc text-xs'>
        {zoneDetailAnalyses.map((a, i) => (
          <li key={i}>
            {formatAnalysisDate(a.date)}
            {a.vcmMeasure != null ? ` - ${a.vcmMeasure} µg/L` : ''}
          </li>
        ))}
      </ul>
    </div>
  ) : null}
  {zoneCard.zoneId != null ? (
    <Link
      href={`/${locale}${ROUTES.ACT}?zone=${zoneCard.zoneId}`}
      className='bg-navy-800 hover:bg-navy-700 mt-1 inline-flex items-center justify-center rounded-lg px-4 py-2 text-xs font-medium text-white transition-colors'
    >
      Take action !
    </Link>
  ) : null}
</CardContent>
```

**Step 5: Commit**

```bash
git add webapp/components/MapView.tsx
git commit -m "feat(tooltip): render VCM analyses and Take action button"
```

---

## Task 4: Act page — auto-load zone from query param

**Files:**
- Modify: `webapp/app/[locale]/act/components/ActSearchSection.tsx`

**Step 1: Write the failing test**

Create `webapp/app/[locale]/act/components/__tests__/ActSearchSection.test.tsx`:

Note: this component uses `useSearchParams` from `next/navigation` and `fetch`. Since the vitest environment is `node` (not jsdom), and mocking Next.js navigation is complex, we skip a unit test here and rely on manual verification in Task 5. However, the logic is straightforward — a `useEffect` that calls an existing function.

**Step 2: Update ActSearchSection to read query param**

In `webapp/app/[locale]/act/components/ActSearchSection.tsx`, add `useSearchParams` and a `useEffect`:

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'

import { DistributionZoneDetailRecord } from '@/types/apiTypes'
import { fetchDistributionZoneDetail } from '@/lib/fetchDistributionZoneDetail'
import ActSearchBar from './ActSearchBar'
import ZoneResultPanel from './ZoneResultPanel'

export default function ActSearchSection() {
  const searchParams = useSearchParams()
  const [zone, setZone] = useState<DistributionZoneDetailRecord | null>(null)
  const [loading, setLoading] = useState(false)

  function handleSelect(zoneId: number) {
    setLoading(true)

    void fetchDistributionZoneDetail(zoneId)
      .then(detail => {
        setZone(detail)
      })
      .catch(() => {
        setZone(null)
      })
      .finally(() => {
        setLoading(false)
      })
  }

  // Auto-load zone from ?zone= query param (e.g. linked from map tooltip)
  useEffect(() => {
    const zoneParam = searchParams.get('zone')
    if (!zoneParam) return
    const zoneId = Number(zoneParam)
    if (Number.isFinite(zoneId)) {
      handleSelect(zoneId)
    }
  }, [searchParams])

  return (
    <div>
      <h2 className='text-navy-800 mb-4 font-[lexend] text-2xl font-semibold'>Find your distribution zone</h2>
      <ActSearchBar onSelect={handleSelect} />
      <ZoneResultPanel zone={zone} loading={loading} />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add webapp/app/\[locale\]/act/components/ActSearchSection.tsx
git commit -m "feat(act): auto-load zone from query param for Take action link"
```

---

## Task 5: Manual verification

**Step 1: Start the dev server**

```bash
cd webapp && npm run dev
```

**Step 2: Verify tooltip with analyses**

1. Open `http://localhost:3000/en/map`
2. Zoom in past zoom 4.5, click a distribution zone
3. Verify:
   - Zone name + PVC/VCM badges appear instantly
   - Loading skeleton shows briefly
   - "Top 3 VCM Results" section appears with dated entries (if zone has analyses)
   - If no analyses, section is hidden — no empty state shown
   - "Take action!" button appears at bottom

**Step 3: Verify Take action link**

1. Click the "Take action!" button in the tooltip
2. Verify it navigates to `/en/act?zone={id}`
3. Verify the Act page auto-loads the zone detail in the result panel
4. Verify the search bar still works normally for manual searches

**Step 4: Verify edge cases**

- Click a zone with no analyses → no analysis section, button still shows
- Click a zone, then click another → previous data clears, new data loads
- Press Escape → tooltip closes cleanly

**Step 5: Final commit if any tweaks needed**

```bash
git add -A
git commit -m "fix(tooltip): adjustments from manual testing"
```
