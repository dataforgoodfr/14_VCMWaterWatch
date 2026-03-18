# Implementation Plan: Import Water Company Data from NocoDB Staging

**Related:** [GitHub Issue #32](https://github.com/dataforgoodfr/14_VCMWaterWatch/issues/32)

**Status:** Implemented

---

## Overview

Investigation users upload water company data via an Excel template into a NocoDB staging table. A CLI-triggered pipeline reads from that table, validates rows, creates DistributionZone and WaterCompany NDJSON files, runs the existing load pipelines, and updates ImportStatus on successful rows.

---

## 1. NocoDB Staging Table

Create a table in NocoDB (via Noco UI) with the following schema. Users will import their Excel file into this table.

| Field | NocoDB Type | Required | Notes |
|-------|-------------|----------|-------|
| Company Name | SingleLineText | Yes | Water company name |
| Country | SingleLineText | Yes | Full name (e.g. "Germany") |
| Municipalities | LongText | Yes | Comma-separated list of municipality names |
| Email | Email | No | |
| Phone | Phone | No | |
| Website | SingleLineText | No | |
| ImportError | LongText | No | Validation error message; null when valid |
| ImportStatus | SingleSelect | No | Options: `Pending`, `Success`, `Failed` |

**Table name:** Water Company Import

---

## 2. Field Mapping

| Staging | Target | Transformation |
|---------|--------|----------------|
| Company Name | WaterCompany.Name, DistributionZone.Code, DistributionZone.Name | Direct (1:1 company → zone) |
| Country | CountryCode | Lookup Country by Name in NocoDB; use Country.Code |
| Municipalities | DistributionZone.Municipalities | Parse; validate each; collect Municipality.Code |
| Email | WaterCompany.Email | Direct |
| Phone | WaterCompany.Phone | Direct |
| Website | WaterCompany.Website | Direct |
| — | WaterCompany.Description | Empty |
| — | WaterCompany.Source | `"NocoDB Import (record_id)"` where record_id = staging row Id |

---

## 3. Validation Rules

### 3.1 Municipality Validation

- Parse `Municipalities` as comma-separated strings; trim each.
- For each municipality value, lookup in NocoDB `Municipality` table: match **Name OR Code**.
- **If any municipality fails to match:** set `ImportError` on the row, set `ImportStatus` = `Failed`, exclude from import.
- Spelling differences cause mismatch; no fuzzy matching.

### 3.2 Duplicate Validation

Check **both** Code and Name, **separately**:

- **DistributionZone:** Row fails if any existing record has same `Code` OR same `Name`.
- **Actor (Water Company):** Row fails if any existing Actor (Type = "Water Company") has same `Name`.

If either zone or company is a duplicate, set `ImportError`, `ImportStatus` = `Failed`, exclude from import.

### 3.3 Country Validation

- Lookup in NocoDB `Country` table: match staging `Country` with `Country.Name`.
- If found, use `Country.Code` as CountryCode.
- Row fails if no matching Country record.

---

## 4. Error Handling

- **ImportError:** Per-row validation message (e.g. `"Municipality 'XYZ' not found"`, `"Distribution zone 'Stadtwerke Kiel AG' already exists"`).
- **ImportStatus:** `Pending` → `Success` (imported) or `Failed` (validation error).
- Failed rows: remain in staging with `ImportError` set; excluded from import.
- Success rows: set `ImportStatus` = `Success` after import. No cleanup of staging rows.

---

## 5. Pipeline Flow

```
1. Read all rows from NocoDB staging table (ImportStatus = Pending or unset)
2. For each row:
   a. Validate Country (lookup by Name in Country table; get Code)
   b. Validate Municipalities (each matches Name OR Code in Municipality table)
   c. Check duplicates: DistributionZone (Code, Name), Actor (Name)
   d. If any validation fails: update row with ImportError, ImportStatus=Failed; skip
3. For valid rows:
   a. Build DistributionZone NDJSON (Code, Name, CountryCode, Municipalities)
   b. Build WaterCompany NDJSON (CountryCode, Name, Email, Phone, Website, Description, Source)
4. Write NDJSON to data/staging/ (or temp dir)
5. Run load_zones DistributionZone
6. Run load_water_companies
7. Update ImportStatus = Success for all rows that were imported
```

**Prerequisites:** Country and Municipality data must already be loaded in NocoDB.

---

## 6. Configuration

- **Staging table name:** `Water Company Import` (or env var override).
- **Staging base:** Same NocoDB base as production.
- **Country lookup:** Match staging Country with `Country.Name` in NocoDB; use `Country.Code`.
- **Data directory:** Reuse `DATA_DIR` from justfile; write NDJSON to `{DATA_DIR}/staging/`.

---

## 7. CLI Interface

- **Trigger:** `just import-water-companies-from-staging` (or similar).
- **Implementation:** New module `pipelines.import_water_companies_from_staging` (or under `pipelines/load/`).
- **Webhook:** Deferred; will trigger same pipeline via API/script later.

---

## 8. Implementation Tasks

| # | Task | Notes |
|---|------|-------|
| 1 | Create NocoDB staging table | Via Noco UI; table name: Water Company Import |
| 2 | [x] Implement staging reader | Fetch rows from NocoDB Water Company Import table |
| 3 | [x] Implement country validator | Lookup Country by Name; get Code |
| 4 | [x] Implement municipality validator | Match by Name OR Code; fail row if any mismatch |
| 5 | [x] Implement duplicate checker | DistributionZone: Code, Name; Actor: Name |
| 6 | [x] Implement NDJSON writer | DistributionZone, WaterCompany formats |
| 7 | [x] Implement pipeline orchestration | Validate → write → load_zones → load_water_companies |
| 8 | [x] Implement NocoDB status updates | ImportError, ImportStatus for failed/success rows |
| 9 | [x] Add just recipe | `just pipelines import-water-companies-from-staging` |
| 10 | [x] Add unit and integration tests | See §10 Test Plan |

**Note:** The NocoDB staging table must use the exact field names from §1 (e.g. "Company Name" with space, not "CompanyName"). If you see `FIELD_NOT_FOUND`, check that field titles match the schema.

---

## 9. Dependencies

- Existing: `load_zones`, `load_water_companies`, `db_helper`, `services`
- `db_helper` must support: `load_all_records` (Municipality with Code, Name; Country; DistributionZone; Actor)
- May need `load_fields` with `condition` for duplicate checks
- May need `update_records` for ImportStatus/ImportError (or NocoDB API PATCH)

---

## 10. Test Plan

| Scope | Approach | What to test |
|-------|----------|--------------|
| **Unit** | pytest + mocks | Country validator (lookup by Name); municipality validator (Name OR Code, fail on any mismatch); duplicate checker (Code, Name); NDJSON output format |
| **Integration** | pytest + mocked `db_helper` | End-to-end flow: read staging → validate → write NDJSON → verify `load_zones` / `load_water_companies` input |
| **Manual** | `just import-water-companies-from-staging` | Run against staging NocoDB with sample Excel data; verify ImportStatus / ImportError updates |

---

## 11. Open Questions

- **Idempotency:** On re-run, rows that were already imported would fail duplicate validation (zone/company already exists) and be marked `Failed` with `ImportError`; they would not be marked `Success` again.
