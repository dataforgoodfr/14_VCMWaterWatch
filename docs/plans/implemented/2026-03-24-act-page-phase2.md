# Act Page Phase 2 — Steps 3 & 4 Implementation Plan

## Goal

Implement Step 3 (Contribute Data) and Step 4 (Join the Project) sections of the `/act` page. These are the remaining placeholders in `webapp/app/[locale]/act/page.tsx`.

---

## Phase 2a: Step 3 — Contribute Data

### Component: `ContributeDataSection`

**File:** `webapp/app/[locale]/act/components/ContributeDataSection.tsx`

Two-column layout on desktop (stacked on mobile), matching existing page patterns (`grid grid-cols-1 md:grid-cols-2 gap-8`).

#### Left column — 3a: Contact Decision-Makers

- Heading + short explanation paragraph
- 3 template cards reusing the same `templates` data already defined in `ActionGuideSidebar.tsx`
- Each card opens `TemplateModal` (already exists)
- If zone data was selected in Step 1, templates keep placeholders (pre-fill deferred)
- "Submit a correction" link/button at bottom (anchor to 3c)

**Refactoring needed:**
- Extract `templates` array from `ActionGuideSidebar.tsx` into a shared `webapp/app/[locale]/act/data/templates.ts` so both sidebar and this section can import it

**New files:**
- `webapp/app/[locale]/act/data/templates.ts` — shared template data
- `webapp/app/[locale]/act/components/ContributeDataSection.tsx` — section shell
- `webapp/app/[locale]/act/components/TemplateCard.tsx` — clickable card (icon + title), reusable

**Modified files:**
- `webapp/app/[locale]/act/components/ActionGuideSidebar.tsx` — import templates from shared file instead of inline
- `webapp/app/[locale]/act/page.tsx` — add Steps 3 & 4 sections

#### Right column — 3b: Share Your Data

**Component:** `DataSubmissionForm`  
**File:** `webapp/app/[locale]/act/components/DataSubmissionForm.tsx`

Form fields using existing `webapp/components/ui/input.tsx`, `field.tsx`, `label.tsx`:

| Field | Type | Required |
|---|---|---|
| Data type | `<select>` (Analysis report, PVC presence info, Correction, Other) | Yes |
| Document source | `<input type="text">` placeholder "e.g. Rapport annuel 2024" | No |
| Submit button | "Submit data" | — |

**Submission:** POST to `/api/contribute` which inserts a row into a NocoDB `Contributions` table. Fields: data type, document source, zone ID (if available), file attachment (NocoDB supports file fields via base64 or URL). The API route uses the existing NocoDB client pattern.

**New file:** `webapp/app/api/contribute/route.ts` — POST handler, validates fields, inserts into NocoDB `Contributions` table.

#### 3c: Correction/Feedback

Below the two columns, a small callout box:
- "Found an error or received a response? Submit a correction."
- Button → submits a correction record to the same `/api/contribute` endpoint with data type "Correction"

Inline in `ContributeDataSection.tsx`, no separate component needed.

---

## Phase 2b: Step 4 — Join the Project

### Component: `JoinProjectSection`

**File:** `webapp/app/[locale]/act/components/JoinProjectSection.tsx`

Two-column layout:

#### Left column — Role cards
3 cards (not clickable, informational):
- 🏛️ Legal experts — "Help affected communities understand their rights"
- 💻 Volunteer developers — "Contribute to the platform's open-source codebase"
- 🔬 Water specialists — "Share expertise on water quality analysis and PVC infrastructure"

Use `webapp/components/ui/card.tsx` for consistent styling.

#### Right column — Contact form

| Field | Type | Required |
|---|---|---|
| Name | `<input type="text">` | Yes |
| Email | `<input type="email">` | Yes |
| Expertise / Motivation | `<input type="text">` | Yes |
| Message | `<textarea>` | No |
| Submit button | "Send my application" | — |

**Submission:** POST to `/api/join` which inserts a row into a NocoDB `Volunteers` table. Fields: name, email, expertise, message.

**New file:** `webapp/app/api/join/route.ts` — POST handler, validates fields, inserts into NocoDB `Volunteers` table.

**Modified files:**
- `webapp/app/[locale]/act/page.tsx` — add Step 4 section

---

---

## File Summary

| File | Action |
|---|---|
| `webapp/app/api/contribute/route.ts` | New — POST contributions to NocoDB |
| `webapp/app/api/join/route.ts` | New — POST volunteer applications to NocoDB |
| `webapp/app/[locale]/act/data/templates.ts` | New — shared template data + fillTemplate |
| `webapp/app/[locale]/act/components/TemplateCard.tsx` | New — reusable clickable template card |
| `webapp/app/[locale]/act/components/ContributeDataSection.tsx` | New — Step 3 |
| `webapp/app/[locale]/act/components/DataSubmissionForm.tsx` | New — file/data submission form |
| `webapp/app/[locale]/act/components/JoinProjectSection.tsx` | New — Step 4 |
| `webapp/app/[locale]/act/components/ActionGuideSidebar.tsx` | Modify — import templates from shared file |
| `webapp/app/[locale]/act/page.tsx` | Modify — add Steps 3 & 4 sections |

---

## Implementation Order

1. Extract templates to shared file + refactor `ActionGuideSidebar` (no visual change)
2. Create `TemplateCard` component
3. Build `ContributeDataSection` (left column: template cards, right column: form, bottom: correction CTA)
4. Build `DataSubmissionForm`
5. Build `JoinProjectSection` (role cards + contact form)
6. Add API routes (`/api/contribute`, `/api/join`)
7. Wire Steps 3 & 4 into `page.tsx`

---

## Estimate: ~4.5h

| Task | Hours |
|---|---|
| Template extraction + refactor | 0.5 |
| TemplateCard component | 0.25 |
| ContributeDataSection + DataSubmissionForm | 1.5 |
| JoinProjectSection | 1 |
| API routes (`/api/contribute`, `/api/join`) + NocoDB tables | 1 |
| Testing & polish | 0.25 |

---

## Open Questions

1. **NocoDB tables:** Need to create `Contributions` and `Volunteers` tables in NocoDB with appropriate fields
