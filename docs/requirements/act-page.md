# Act Page ("Agir") — Functional Requirements

## 1. Overview

The Act page (`/act`) provides a guided, 4-step experience helping users identify their water situation, understand what actions to take, contribute data, and join the project as volunteers.

The page is a single scrollable view with four clearly separated, numbered sections. Layout uses a centered max-width container consistent with the rest of the site.

---

## 2. Step 1 — Find Your Water Company

### 2.1 Purpose

Allow users to search for their water distribution zone and view key water quality information including a color-coded risk assessment.

### 2.2 Search

- **Input:** A text field with placeholder "Enter your city, postal code, or address…"
- **Behavior:** Debounced type-ahead (300 ms delay, minimum 3 characters). As the user types, a dropdown displays matching distribution zones with zone name, country, and water company name as context.
- **Data source:** Search is performed against a denormalized `SearchIndex` field on the Distribution Zone table that concatenates zone name, municipality names, and actor names.

### 2.3 Results Panel

When the user selects a distribution zone from the dropdown, a panel appears below the search bar displaying:

| Information | Description |
|---|---|
| Distribution zone name | Name of the selected zone |
| Country | Country the zone belongs to |
| Water company | Name of the water company (actor) responsible |
| Water company email | Contact email for the water company |
| PVC Level | PVC contamination level (may be null) |
| VCM Level | VCM contamination level (may be null) |
| Municipalities | List of municipalities served by the zone |

### 2.4 Color-Coded Risk Badge

A color badge is derived from VCM/PVC levels and displayed prominently in the results panel:

| Color | Label | Condition |
|---|---|---|
| 🟢 Green | Safe | VCM Level is null or "Conforme" |
| 🟡 Yellow | Caution | VCM Level is "Vigilance" or PVC Level is non-null but low |
| 🟠 Orange | Warning | VCM Level is elevated but below regulatory limit |
| 🔴 Red | Danger | VCM Level exceeds regulatory limit |

> **Note:** Exact thresholds depend on values in the database. To be confirmed with the data team.

---

## 3. Step 2 — Action Guide ("Que dois-je faire ?")

### 3.1 Purpose

Provide actionable guidance for all three risk scenarios so users can identify their situation and follow the appropriate steps. This section is fully static and works independently of Step 1.

### 3.2 Layout

- **Desktop:** Two columns — content (left, ~60%) and sticky sidebar (right, ~40%).
- **Mobile:** Single stacked column.

### 3.3 Scenarios (Left Column)

Three collapsible accordion sections, all collapsed by default. Each has a colored header badge.

#### 3.3.1 🟢 Your water is compliant
- Reassurance: nothing to do for now.
- Advisory: CVM pollution can develop over time due to aging pre-1980 PVC pipes.
- Call to action: share private analysis data (links to Step 3).

#### 3.3.2 🟡🟠 Caution recommended
- Banner: "You may continue drinking the water, but exercise caution — especially for infants and vulnerable individuals."
- Action steps:
  1. **Contact your water provider** — request testing, demand specific control points, cite the 30-day CADA deadline, demand pipe replacement if non-compliant, assert right to bottled water, mention private testing option (~€40–100).
  2. **Contact your elected official.**
  3. **If no action is taken** — consider legal action.

#### 3.3.3 🔴 Urgent action required
- Alert banner: "Stop consuming tap water immediately."
- Action steps:
  1. **Stop consuming water** — do not drink or cook with it; note CVM inhalation risk.
  2. **Contact your water provider** — same sub-steps as caution scenario.
  3. **Contact your elected official.**
  4. **If no action is taken** — consider legal action.

### 3.4 Sidebar (Right Column)

- **Important reminder box:** As a subscriber you are paying for a service. Supplying safe water is a legal obligation. You have the right to demand transparency and solutions.
- **Letter templates:** Three cards, each opening a slide-over modal with full template text and a "Copy to clipboard" button:
  - Letter to the mayor
  - Email to water company
  - Letter to your MP
- **Notice:** "Keep written records of all communications with your water provider, mayor, and elected officials."

---

## 4. Step 3 — Contribute Data

### 4.1 Purpose

Enable users to contact decision-makers using pre-written templates and submit water quality data or corrections to the project.

### 4.2 Layout

Two columns on desktop (stacked on mobile).

### 4.3 Contact Decision-Makers (Left Column)

- Heading and explanation text.
- Three clickable template cards (same templates as sidebar in Step 2):
  - Letter to the mayor
  - Email to water company
  - Letter to your MP
- Each card opens a slide-over modal with the template text and a copy button.
- Templates contain placeholders (e.g. `[YOUR MUNICIPALITY]`, `[DISTRIBUTION ZONE]`) for the user to fill in manually.

### 4.4 Share Your Data (Right Column)

A submission form with the following fields:

| Field | Type | Required |
|---|---|---|
| Data type | Dropdown: Analysis report, PVC presence info, Correction, Other | Yes |
| Document source | Text input (e.g. "Rapport annuel 2024") | No |
| Submit button | "Submit data" | — |

> **Backlog:** File upload (PDF, Excel drag-and-drop) is deferred to a future phase.

**Submission:** Data is sent via POST to a backend API endpoint which inserts a record into a NocoDB `Contributions` table.

#### Contributions Table Fields

| Field | Type | Notes |
|---|---|---|
| Data type | Single select | Analysis report, PVC presence info, Correction, Other |
| Document source | Text | Free-text description of the source |
| Zone ID | Link/Text | Optional reference to a distribution zone |

### 4.5 Correction / Feedback

Below the two columns, a callout box:
- Text: "Found an error or received a response? Submit a correction."
- Button submits a correction record to the same Contributions endpoint with data type pre-set to "Correction."

---

## 5. Step 4 — Join the Project

### 5.1 Purpose

Recruit volunteers with relevant expertise to support the project.

### 5.2 Layout

Two columns on desktop (stacked on mobile).

### 5.3 Role Information (Left Column)

Three informational cards describing needed profiles:

| Role | Description |
|---|---|
| 🏛️ Legal experts | Help affected communities understand their rights |
| 💻 Volunteer developers | Contribute to the platform's open-source codebase |
| 🔬 Water specialists | Share expertise on water quality analysis and PVC infrastructure |

### 5.4 Volunteer Form (Right Column)

| Field | Type | Required |
|---|---|---|
| Name | Text | Yes |
| Email | Email | Yes |
| Expertise / Motivation | Text | Yes |
| Message | Textarea | No |
| Submit button | "Send my application" | — |

**Submission:** Data is sent via POST to a backend API endpoint which inserts a record into a NocoDB `Volunteers` table.

#### Volunteers Table Fields

| Field | Type | Notes |
|---|---|---|
| Name | Text | Full name |
| Email | Email | Contact email |
| Expertise / Motivation | Text | Area of expertise or reason for joining |
| Message | Long text | Optional free-form message |

---

## 6. Cross-Cutting Concerns

### 6.1 Responsiveness
All sections use a two-column layout on desktop and collapse to a single column on mobile.

### 6.2 Internationalization
English only for the initial release. Localization is deferred.

### 6.3 Letter Templates — Database-Driven

Letter templates (used in the Step 2 sidebar and Step 3 contact section) are stored in a NocoDB `LetterTemplate` table so that non-developers can edit text, add new templates, and support future localization without code changes.

#### LetterTemplate Table Fields

| Field | Type | Notes |
|---|---|---|
| Title | Text | e.g. "Letter to the mayor" |
| Icon | Text | Emoji string (e.g. "🏛️") |
| Content | Long Text | Template body with `[PLACEHOLDER]` tokens |
| SortOrder | Number | Controls display ordering |
| Locale | Text | Language code (`en`, `fr`, etc.). Only `en` initially. |
| Active | Checkbox | Toggle visibility without deleting |

#### API

A GET endpoint (`/api/letter-templates`) returns active templates filtered by locale and ordered by `SortOrder`.

#### Fallback

If the API call fails, the frontend falls back to hardcoded templates so the page never renders empty.

#### Management

Templates are managed directly via the NocoDB UI. No dedicated admin page for now.

---

## 7. Open Questions

1. **Color code thresholds:** Exact VCM/PVC values mapping to 🟢🟡🟠🔴 need data team confirmation.
2. **Template text:** Final wording of letter templates to be validated by the team (will be edited directly in NocoDB once the table is set up).
3. **Elected official contacts:** Are these available in NocoDB (Actor table with type filter), or is generic guidance sufficient for now?
4. **Legal action link:** Confirm external URL (e.g. Gabrièle Gien).
5. **Analysis history:** Is analysis history per zone accessible via linked records? What fields are available?

---

## 8. Backlog (Deferred)

- File upload on the data submission form (Step 3)
- Template pre-fill with zone data from Step 1
- Internationalization / French localization
