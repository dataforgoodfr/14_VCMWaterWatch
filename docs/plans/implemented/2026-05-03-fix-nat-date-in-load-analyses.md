# Fix NaT Date Error in load_analyses

## Goal

Eliminate the `ERR_INVALID_VALUE_FOR_FIELD: Invalid value 'NaT' for type 'Date'`
error on `load_analyses` by fixing the two real bugs that cause it, rather
than masking with a null-guard.

## Background (from investigation)

Null counts actually observed:

| Layer                               | Null Date     | Non-null | Notes |
|-------------------------------------|---------------|----------|-------|
| `raw.outline_cvm_samples`           | 74,317 (100%) | 0        | `plv_date` never populated |
| `staging.Analysis_fr_outline`       | 87,497 (100%) | 0        | commune explosion amplifies |
| `staging.Analysis_fr_dansmoneau`    | 0             | 501,680  | healthy |
| `staging.Analysis_fr` (merged)      | 33,251        | 475,024  | outline rows survive dedup |

Outline XLSX date cells are Excel **serial numbers as strings** (e.g. `'44727'`,
`'45044'`) because the extractor reads with `all_varchar=true`. Current code
does `TRY_CAST({date_col} AS DATE)` — that silently fails on serial numbers
and all Outline dates become NULL.

The NULL dates then ride through staging → `load_analyses` where
`str(row.get("Date", ""))` turns pandas `NaT` into the literal `"NaT"`,
which NocoDB rejects.

## Plan

Two fixes, in order. After both land, no null-guard is needed because the
upstream NULL source is eliminated and NULLs from DuckDB stay as Python
`None` (which `prepare_records` handles naturally — `str(None)` doesn't
appear because we won't reach that path; and if we ever did, `str(None)`
returning `"None"` would still be a bug — so we'll also remove the
`str(...)` coercion as part of step 2).

### Step 1 — Fix the Outline date extractor

File: `pipelines/extract/fr_outline.py` (~line 200)

Replace:
```python
TRY_CAST({_qid(date_col)} AS DATE) AS plv_date,
```

With a parser that tries Excel serial first, then ISO, then French format:
```python
# Excel stores dates as days since 1899-12-30 (accounting for Excel's 1900
# leap-year bug). all_varchar=true turns them into integer-looking strings.
f"""
COALESCE(
    DATE '1899-12-30' + TRY_CAST({_qid(date_col)} AS INTEGER),
    TRY_CAST({_qid(date_col)} AS DATE),
    TRY_STRPTIME({_qid(date_col)}, '%d/%m/%Y')::DATE,
    TRY_STRPTIME({_qid(date_col)}, '%Y-%m-%d')::DATE
) AS plv_date,
"""
```

Verification steps:
1. Re-run `fr_outline` extractor against the existing XLSX fixtures.
2. Assert `raw.outline_cvm_samples`: `COUNT(*) WHERE plv_date IS NULL` drops
   from 74,317 → near zero (a handful of empty cells acceptable).
3. Spot-check parsed dates against the source XLSX (e.g. serial `44727` →
   `2022-06-08`).
4. Re-run `fr_build` → `staging.Analysis_fr_outline` and `Analysis_fr` null
   counts should collapse to ~0.

Add a fixture-based unit test in `pipelines/extract/tests/` (or extend the
existing one) that asserts a serial-number cell parses to the correct date.

**Sub-step: warn-log on unparsed date cells.** After running the SQL into
`df`, detect rows where the source cell was non-empty but all parse
branches produced NULL, and log per-file:
```python
unparsed = df[df["plv_date"].isna() & df[date_col].astype(str).str.strip().ne("")]
if len(unparsed) > 0:
    sample = unparsed[date_col].astype(str).head(5).tolist()
    logger.warning(
        f"{path.name}: {len(unparsed)} date cell(s) failed all parse "
        f"branches (serial/ISO/DD-MM-YYYY). Samples: {sample}"
    )
```
Add a unit test with a garbage date cell asserting the warning fires.

### Step 2 — Drop pandas round-trip in `load_staging_analyses`

File: `pipelines/load/load_analyses.py` (~line 72)

Replace:
```python
rows = conn.execute(union_sql).fetchdf().to_dict(orient="records")
```

With native DuckDB fetch so NULLs stay Python `None` and dates stay as
`datetime.date` (not pandas `Timestamp`/`NaT`):
```python
result = conn.execute(union_sql)
col_names = [d[0] for d in result.description]
rows = [dict(zip(col_names, r)) for r in result.fetchall()]
```

Then in `prepare_records` (~line 172), stop string-coercing via `str()` and
isoformat dates at the loader boundary (stdlib `json` can't serialize
`datetime.date`, and `db_helper` uses httpx `json=` which falls through to
stdlib):
```python
"Date": row["Date"].isoformat() if row.get("Date") else None,
```
Update the dedup-key line to use the native value (no `str()`):
```python
row.get("Date"),   # datetime.date or None
```

`_make_description` can stay as-is — `f"... @ {date}"` on a `datetime.date`
produces the ISO string we want (`"2022-06-08"`).

**Why isoformat at the loader, not a custom encoder in `db_helper`:**
no other loader ships date fields today; `db_helper` should stay generic
NocoDB plumbing; explicit conversion at the call site is a one-line change
with zero blast radius. Revisit if a third caller needs date/datetime
/Decimal serialization — then promote to a `json.dumps(..., default=...)`
in `db_helper`.

### Step 3 — Tests & verification

- Unit test in `pipelines/load/tests/test_load_analyses.py` covering
  `prepare_records` with a `datetime.date` input → asserts no `"NaT"`,
  `"None"`, or `"NaT"` strings leak into the output dicts.
- Full integration: run the pipeline end-to-end, assert `load_analyses`
  inserts succeed with zero 422 errors and the rejected row count is 0.

## Out of Scope (follow-up)

The same `.fetchdf().to_dict(...)` pattern exists in:
- `pipelines/load/load_water_companies.py:64`
- `pipelines/load/load_zones.py:94`
- `pipelines/extract/de_wasserportal.py:60,82`

Latent bugs waiting for any nullable date/timestamp column. Worth a sweep
in a follow-up branch but not blocking this fix.

## Open Questions

None — ready to implement.
