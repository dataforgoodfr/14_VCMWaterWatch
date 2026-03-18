# Replace Polars with DuckDB

## Goal

Remove polars dependency entirely. Use DuckDB as both the staging storage layer (replacing NDJSON files) and the in-memory data processing engine. `db_helper.py` (NocoDB API) switches to plain `list[dict]` for its interface.

## Architecture

```
                  ┌─────────────┐     ┌───────────────┐
  extract/ ──────>│   raw.db    │────>│  staging.db   │──────> load/ ──────> NocoDB
                  └─────────────┘     └───────────────┘           ▲
                        ▲               ▲                         │
                        │    transform/ ─┘                   db_helper.py
                        │                                   (list[dict] API)
                  external APIs
```

- **`data/raw/raw.duckdb`** replaces `data/raw/*.ndjson` — raw extracted data
- **`data/staging/staging.duckdb`** replaces `data/staging/*.ndjson` — transformed data ready for load
- Both attached in a single connection — cross-DB queries via `raw.` / `staging.` prefixes
- **`db_helper.py`** accepts/returns `list[dict]` — no DuckDB dependency, pure HTTP + JSON
- **`staging_db.py`** is thin — provides `get_connection()` (attaches both DBs) and `write_table()` convenience
- **Pipeline files** get a DuckDB connection and run SQL directly for joins, filters, group_by, etc.
- Pipeline SQL queries return **DuckDB relations** (lazy, chainable) — materialized to `list[dict]` only when passing data to `db_helper`

## Connection lifecycle & parameter passing

### Current state

Two conventions exist today:

| Flow | Receives | Meaning |
|------|----------|---------|
| `geojson`, `create_distribution_zones`, `de_wasserportal`, `export_pmtiles`, `import_water_companies_from_staging` | `data_dir = data` | Project root; builds `data/raw`, `data/staging` internally |
| `load_zones_flow` | `data_directory = data/staging` | Reads NDJSON directly from staging dir |
| `load_water_companies` | `data_path = data/staging` | Same — reads NDJSON from staging dir |

`import_water_companies_from_staging` bridges the two by computing `staging_dir = data_dir / "staging"` and passing that to `load_zones_flow` and `load_water_companies`.

### New convention

With DuckDB, every flow just needs a **connection** (which knows where both DBs are). The path is only needed by `staging_db.get_connection()`.

**`@flow` entry points** own the connection:

```python
@flow
def load_zones_flow(level: str, data_dir: Path):
    conn = staging_db.get_connection(data_dir)
    try:
        df = load_source_data(conn, level)
        ...
    finally:
        conn.close()
```

**`@task` functions and helpers** receive `conn`:

```python
@task
def lookup_parent_task(conn, df, level_config):
    ...
```

**Sub-flow calls** pass `data_dir` (not `conn`), so each flow opens its own connection:

```python
# import_water_companies_from_staging.py
load_zones_flow(level="DistributionZone", data_dir=data_directory)  # not staging_dir
load_water_companies(data_dir=data_directory)                        # not staging_dir
```

This eliminates the `staging_dir` vs `data_dir` confusion — all flows receive the project-level `data/` path.

### Thread safety

DuckDB connections are **not thread-safe**. Current code calls all tasks synchronously (no `.submit()`), so sharing one `conn` within a flow is safe.

Constraint: **do not use `.submit()` on tasks that share a conn**. This is documented in `staging_db.py` docstring.

If concurrent tasks are needed later, each task can call `get_connection()` itself (cheap — in-memory connect + ATTACH is fast). Cross-task temp tables aren't used.

## Data flow between layers

```python
# Flow entry point creates connection
conn = staging_db.get_connection(Path("data"))

# Pipeline reads from staging DB — stays as DuckDB relation
munis = conn.sql("SELECT * FROM staging.Municipality WHERE CountryCode = 'DE'")

# Bridge: register db_helper results for SQL joins
existing = db_helper.load_all_records("Municipality")  # list[dict]
conn.execute("CREATE OR REPLACE TEMP TABLE existing AS SELECT * FROM (VALUES ...)")
# (staging_db provides a helper to register list[dict] as temp table)
new = conn.sql("SELECT m.* FROM munis m ANTI JOIN existing e ON m.Code = e.Code")

# Materialize to list[dict] only when calling db_helper
db_helper.insert_records(new.fetchdf().to_dict('records'), "Municipality")

conn.close()
```

## Proposed Changes

### 1. `pipelines/common/db_helper.py` — convert to list[dict]

All methods change signature:
- `load_fields(...)` → returns `list[dict]`
- `load_all_records(...)` → returns `list[dict]`
- `insert_records(records: list[dict], ...)` → returns `list[dict]` (with Id populated)
- `update_records(records: list[dict], ...)`
- `delete_records(records: list[dict], ...)`
- `link_records(records: list[dict], ...)`

Remove all `pl.*` calls. Replace with plain list/dict operations:
- `df.is_empty()` → `len(records) == 0`
- `df.filter(pl.col("Id").is_not_null())` → `[r for r in records if r.get("Id") is not None]`
- `df.to_dicts()` → already dicts
- `df["Id"].to_list()` → `[r["Id"] for r in records]`
- `pl.concat(...)` → `list1 + list2`
- `iter_rows(named=True)` → iterate list directly

No DuckDB dependency here. Pure HTTP client.

### 2. `pipelines/common/staging_db.py` — new module (~80 LOC)

Thin module — connection management, write convenience, and temp table registration. Pipelines own their SQL.

```python
def get_connection(data_dir: str | Path = "data") -> duckdb.DuckDBPyConnection:
    """Attach both raw and staging DBs in a single connection.

    NOT thread-safe — do not share across concurrent tasks (.submit()).
    """
    conn = duckdb.connect()
    conn.execute(f"ATTACH '{data_dir}/raw/raw.duckdb' AS raw")
    conn.execute(f"ATTACH '{data_dir}/staging/staging.duckdb' AS staging")
    return conn

def write_table(conn, table_name: str, records: list[dict], schema: str = "staging"):
    """CREATE OR REPLACE + INSERT into raw.table or staging.table"""

def register_temp(conn, name: str, records: list[dict]):
    """Register a list[dict] as a temp table for use in SQL joins."""
```

No query helpers — pipelines run SQL directly on the connection and get DuckDB relations back.

Tables mirror old NDJSON files, now prefixed by schema:
- `staging.Municipality` (was `data/staging/Municipality.ndjson`)
- `staging.Country` (was `data/staging/Country.ndjson`)
- `staging.DistributionZone_from_water_companies` (was `data/staging/DistributionZone_from_water_companies.ndjson`)
- `staging.DistributionZone_import` (was `data/staging/DistributionZone_import.ndjson`)
- `raw.WaterCompany_de_wasserportal` (was `data/raw/WaterCompany_de_wasserportal.ndjson`)
- `staging.WaterCompany_import` (was `data/staging/WaterCompany_import.ndjson`)

Glob patterns like `WaterCompany*.ndjson` become:
```sql
SELECT * FROM raw.WaterCompany_de_wasserportal
UNION ALL
SELECT * FROM staging.WaterCompany_import
```

### 3. `pipelines/transform/geojson.py`

- Remove `import polars`
- Build rows as `list[dict]` (already does this), write to staging DB via `staging_db.write_table()`
- `pl.concat([...])` → just extend list
- `pl.col("Code").is_in(...)` → SQL `WHERE Code IN (...)`

### 4. `pipelines/transform/create_distribution_zones.py`

- Read from staging DB: `SELECT Name AS Code, Name, CountryCode, Municipalities, 'Distribution' AS Type FROM WaterCompany_%`
- Write result to staging DB `DistributionZone_from_water_companies` table

### 5. `pipelines/extract/de_wasserportal.py`

- Signature stays `download_de_wasserportal(data_directory: Path)` — creates conn internally
- Read municipalities from staging DB: `conn.sql("SELECT * FROM staging.Municipality WHERE CountryCode = 'DE'")`
- Build companies list as `list[dict]` (already mostly does this)
- Group-by via SQL: `SELECT Name, first(Phone), ..., list(Municipality) AS Municipalities FROM ... GROUP BY Name`
- Write to raw DB: `staging_db.write_table(conn, "WaterCompany_de_wasserportal", records, schema="raw")`

### 6. `pipelines/load/load_zones.py`

- **Signature change**: `load_zones_flow(level, data_directory)` — `data_directory` now always means project root (`data/`), not `data/staging`
- Flow creates `conn = staging_db.get_connection(data_directory)`, passes `conn` to tasks, closes on exit
- `load_source_data(conn, level)` → `conn.sql(f"SELECT * FROM staging.{level}")`
- `filter_existing_data` → SQL `ANTI JOIN` with db_helper results registered as temp table
- `lookup_parent_task(conn, ...)` → SQL join
- `lookup_children_task(conn, ...)` → SQL `unnest` + join + `list()` aggregate
- `insert_records_task` → `.fetchall()` → `list[dict]` → `db_helper.insert_records()`
- `link_children_task` → `.fetchall()` → `list[dict]` → `db_helper.link_records()`

### 7. `pipelines/load/load_water_companies.py`

- **Signature change**: `load_water_companies(data_dir: Path)` — receives project root, not `data/staging`
- Flow creates `conn = staging_db.get_connection(data_dir)`, passes `conn` to tasks, closes on exit
- Read from staging DB `WaterCompany_*` tables via `conn`
- Lookups via SQL joins against `db_helper.load_all_records()` results (register as DuckDB temp tables)
- Insert/link via `db_helper`

### 8. `pipelines/load/import_water_companies_from_staging.py`

- **Rename**: `write_ndjson_and_load_task` → `write_staging_and_load_task`
- No longer computes `staging_dir = data_dir / "staging"` — passes `data_directory` directly to `load_zones_flow` and `load_water_companies`
- Creates own conn for writing to staging DB tables (instead of NDJSON)
- Validation logic already uses plain dicts internally — minimal change
- Remove `pl.DataFrame` construction, use `list[dict]` throughout

### 9. `pipelines/tasks/clean_blank_actors.py`

- `db_helper.load_all_records()` returns `list[dict]`
- Filter: `[r for r in records if r.get("Name") is None]`
- Pass to `db_helper.delete_records()`

### 10. `pipelines/tasks/calculate_distribution_zone.py`

- `load_all_records()` returns `list[dict]`
- Filter/iterate already mostly dict-based (shapely ops on geometry strings)
- `with_columns` → just set key on each dict

### 11. `pipelines/export/export_pmtiles.py`

- continue reading from nocodb
- Iterate rows as dicts to build GeoJSON FeatureCollection — logic stays the same
- Remove polars import

### 12. Test files

| File | Changes |
|------|---------|
| `common/tests/test_db_helper.py` | Assertions on list[dict] instead of pl.DataFrame |
| `load/tests/test_import_water_companies_from_staging.py` | Remove pl.DataFrame construction, use list[dict]. Remove ndjson assertions → query staging DB |
| `export/tests/test_export_pmtiles.py` | Rework to remove dataframe |

### 13. `pyproject.toml`

- Remove `polars>=1.22.0`
- Add `duckdb>=1.2.0`

## Open Questions

(none remaining)

## Resolved

- **Two DBs**: `data/raw/raw.duckdb` + `data/staging/staging.duckdb`, attached in single connection
- **`.gitignore`**: add `data/raw/raw.duckdb` and `data/staging/staging.duckdb`
- **Export pipeline**: reads from staging DB (not NocoDB), just replace polars with DuckDB queries

## Estimate

3-5 days total.
