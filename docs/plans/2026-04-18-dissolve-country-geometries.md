# Dissolve Country Geometries from Municipalities

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Replace the independent GISCO country boundary download with country polygons dissolved from municipality geometries, so country and zone borders align exactly.

**Architecture:** A new extract step writes hardcoded country metadata (Code, Name) to `raw.Country`. A new transform step dissolves `staging.Municipality` geometries by `CountryCode` and writes to `staging.Country`. The existing `download_countries.py` and the Country branch of `geojson.py` are removed.

**Tech Stack:** Python, DuckDB (spatial extension), Prefect, tippecanoe (existing)

---

### Task 1: Create `extract_countries.py`

**Files:**
- Create: `pipelines/extract/extract_countries.py`
- Test: `pipelines/extract/tests/test_extract_countries.py`

**Step 1: Write the failing test**

```python
# pipelines/extract/tests/test_extract_countries.py
"""Tests for extract_countries."""
import duckdb
import pytest
from pipelines.extract.extract_countries import extract_countries


def test_extract_countries_writes_raw_table(tmp_path):
    """extract_countries writes Code and Name columns into raw.Country."""
    raw_db = tmp_path / "raw" / "raw.duckdb"
    raw_db.parent.mkdir(parents=True)
    # Create the raw database so ATTACH works
    duckdb.connect(str(raw_db)).close()

    conn = duckdb.connect()
    conn.execute(f"ATTACH '{raw_db}' AS raw")

    extract_countries(conn)

    rows = conn.sql("SELECT Code, Name FROM raw.Country ORDER BY Code").fetchall()
    conn.close()

    codes = [r[0] for r in rows]
    names = [r[1] for r in rows]

    assert "NL" in codes
    assert "DE" in codes
    assert "BE" in codes
    assert names[codes.index("NL")] == "Netherlands"
    assert len(rows) == 16
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/extract/tests/test_extract_countries.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

```python
# pipelines/extract/extract_countries.py
"""
Write hardcoded European country metadata into raw.Country.

No download required — the country list is maintained in
pipelines.transform.config.EUROPEAN_COUNTRIES.
"""

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipelines.transform.config import EUROPEAN_COUNTRIES


@task(name="extract_countries", cache_policy=NO_CACHE)
def extract_countries(conn: duckdb.DuckDBPyConnection) -> None:
    """Write EUROPEAN_COUNTRIES into raw.Country (Code, Name)."""
    records = [
        {"Code": code, "Name": name} for code, name in EUROPEAN_COUNTRIES.items()
    ]
    import pandas as pd

    df = pd.DataFrame(records)
    conn.execute('CREATE OR REPLACE TABLE raw."Country" AS SELECT * FROM df')


@flow(name="extract_countries")
def extract_countries_flow(data_directory):
    """Standalone flow entry point."""
    from pathlib import Path
    from pipelines.common import staging_db

    conn = staging_db.get_connection(Path(data_directory))
    try:
        extract_countries(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    extract_countries_flow(data_directory)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/extract/tests/test_extract_countries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pipelines/extract/extract_countries.py pipelines/extract/tests/test_extract_countries.py
git commit -m "feat: add extract_countries step with hardcoded country metadata"
```

---

### Task 2: Create `dissolve_countries.py`

**Files:**
- Create: `pipelines/transform/dissolve_countries.py`
- Create: `pipelines/transform/tests/__init__.py`
- Create: `pipelines/transform/tests/test_dissolve_countries.py`

**Step 1: Write the failing test**

```python
# pipelines/transform/tests/__init__.py
# (empty)
```

```python
# pipelines/transform/tests/test_dissolve_countries.py
"""Tests for dissolve_countries."""
import json

import duckdb
import pytest

from pipelines.transform.dissolve_countries import dissolve_countries


def _make_polygon(lon, lat, size=0.1):
    """Return a simple GeoJSON polygon string around (lon, lat)."""
    return json.dumps({
        "type": "Polygon",
        "coordinates": [[
            [lon, lat],
            [lon + size, lat],
            [lon + size, lat + size],
            [lon, lat + size],
            [lon, lat],
        ]],
    })


@pytest.fixture
def conn(tmp_path):
    raw_db = tmp_path / "raw" / "raw.duckdb"
    staging_db = tmp_path / "staging" / "staging.duckdb"
    raw_db.parent.mkdir(parents=True)
    staging_db.parent.mkdir(parents=True)
    duckdb.connect(str(raw_db)).close()
    duckdb.connect(str(staging_db)).close()

    c = duckdb.connect()
    c.execute(f"ATTACH '{raw_db}' AS raw")
    c.execute(f"ATTACH '{staging_db}' AS staging")

    # Seed raw.Country
    c.execute("""
        CREATE TABLE raw."Country" AS
        SELECT * FROM (VALUES ('NL', 'Netherlands'), ('BE', 'Belgium')) t(Code, Name)
    """)

    # Seed staging.Municipality with 2 NL and 1 BE municipality
    import pandas as pd
    municipalities = pd.DataFrame([
        {"Code": "NL001", "Name": "Amsterdam", "CountryCode": "NL",
         "Geometry": _make_polygon(4.9, 52.4)},
        {"Code": "NL002", "Name": "Rotterdam", "CountryCode": "NL",
         "Geometry": _make_polygon(4.5, 51.9)},
        {"Code": "BE001", "Name": "Antwerp", "CountryCode": "BE",
         "Geometry": _make_polygon(4.4, 51.2)},
    ])
    c.execute('CREATE TABLE staging."Municipality" AS SELECT * FROM municipalities')

    yield c
    c.close()


def test_dissolve_creates_staging_country(conn):
    """dissolve_countries writes Code, Name, Geometry into staging.Country."""
    dissolve_countries(conn)

    rows = conn.sql(
        'SELECT Code, Name, Geometry FROM staging."Country" ORDER BY Code'
    ).fetchall()
    assert len(rows) == 2

    codes = [r[0] for r in rows]
    assert codes == ["BE", "NL"]

    # Names come from raw.Country
    names = [r[1] for r in rows]
    assert names == ["Belgium", "Netherlands"]

    # Geometry is valid GeoJSON
    for row in rows:
        geom = json.loads(row[2])
        assert geom["type"] in ("Polygon", "MultiPolygon")


def test_dissolve_unions_geometries(conn):
    """NL has 2 municipalities — dissolved geometry should cover both."""
    dissolve_countries(conn)

    geom_json = conn.sql("""
        SELECT Geometry FROM staging."Country" WHERE Code = 'NL'
    """).fetchone()[0]
    geom = json.loads(geom_json)
    assert geom["type"] in ("Polygon", "MultiPolygon")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest pipelines/transform/tests/test_dissolve_countries.py -v`
Expected: FAIL — module not found

**Step 3: Write minimal implementation**

```python
# pipelines/transform/dissolve_countries.py
"""
Dissolve municipality geometries into country polygons.

Reads staging.Municipality and raw.Country, writes staging.Country
with Code, Name, and dissolved Geometry (GeoJSON string).

This ensures country borders exactly match zone borders built from
the same municipality geometries.
"""

from pathlib import Path

import duckdb
from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db


@task(name="dissolve_countries", cache_policy=NO_CACHE)
def dissolve_countries(conn: duckdb.DuckDBPyConnection) -> None:
    """Dissolve municipality geometries by CountryCode into staging.Country."""
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.execute("""
        CREATE OR REPLACE TABLE staging."Country" AS
        SELECT
            c.Code,
            c.Name,
            ST_AsGeoJSON(
                ST_Union_Agg(ST_GeomFromGeoJSON(m."Geometry"))
            ) AS "Geometry"
        FROM staging."Municipality" m
        JOIN raw."Country" c ON c.Code = m."CountryCode"
        GROUP BY c.Code, c.Name
    """)


@flow(name="dissolve_countries")
def dissolve_countries_flow(data_directory: Path) -> None:
    """Standalone flow entry point."""
    conn = staging_db.get_connection(data_directory)
    try:
        dissolve_countries(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    dissolve_countries_flow(data_directory)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest pipelines/transform/tests/test_dissolve_countries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pipelines/transform/dissolve_countries.py pipelines/transform/tests/__init__.py pipelines/transform/tests/test_dissolve_countries.py
git commit -m "feat: add dissolve_countries transform step"
```

---

### Task 3: Remove Country from `geojson.py` and `config.py`

**Files:**
- Modify: `pipelines/transform/geojson.py` (lines ~108-112: remove Country import from `import_all_geojson_flow`)
- Modify: `pipelines/transform/config.py` (remove `"Country"` entry from `LEVEL_CONFIGS`)

**Step 1: Edit `pipelines/transform/config.py`**

Remove the `"Country"` entry from `LEVEL_CONFIGS`:

```python
# Before:
LEVEL_CONFIGS: Dict[str, LevelConfig] = {
    "Country": LevelConfig(
        file_suffix="countries",
        parent_level=None,
        title_property="name",
        code_property="ISO3166-1-Alpha-2",
    ),
    "Region": LevelConfig(
# After:
LEVEL_CONFIGS: Dict[str, LevelConfig] = {
    "Region": LevelConfig(
```

**Step 2: Edit `pipelines/transform/geojson.py`**

In `import_all_geojson_flow`, remove the Country import block. Change:

```python
        logger.info("Starting Country import...")
        import_geojson_flow(level="Country", source_dir=source_dir, conn=conn)

        logger.info("Starting Municipality import...")
```

To:

```python
        logger.info("Starting Municipality import...")
```

Also update the module docstring from:
```
Prefect workflow for transforming GeoJSON data into the zone objects (Country + Municipality)
```
To:
```
Prefect workflow for transforming GeoJSON data into Municipality zone objects
```

**Step 3: Run existing tests to verify nothing breaks**

Run: `uv run pytest pipelines/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add pipelines/transform/config.py pipelines/transform/geojson.py
git commit -m "refactor: remove Country import from geojson transform"
```

---

### Task 4: Delete `download_countries.py` and update justfile

**Files:**
- Delete: `pipelines/extract/download_countries.py`
- Modify: `pipelines/justfile`

**Step 1: Delete `download_countries.py`**

```bash
git rm pipelines/extract/download_countries.py
```

**Step 2: Update `pipelines/justfile`**

Replace the `extract-countries` recipe:

```
# Before:
# Download country boundary data from GISCO and convert to GeoJSON.
extract-countries:
  uv run python -m pipelines.extract.download_countries

# After:
# Write country metadata into raw database.
extract-countries:
  uv run python -m pipelines.extract.extract_countries ${DATA_DIR}
```

Add a `transform-dissolve-countries` recipe after `transform-geojson`:

```
# Dissolve municipality geometries into country polygons.
# Must run after transform-geojson.
transform-dissolve-countries:
  uv run python -m pipelines.transform.dissolve_countries ${DATA_DIR}
```

Add a `transform-all` recipe that runs both in the correct order:

```
# Run all transform steps in the correct order.
# Municipality GeoJSON must be imported before country dissolve.
transform-all:
  @just pipelines transform-geojson
  @just pipelines transform-dissolve-countries
  @just pipelines transform-create-distribution-zones
```

**Step 3: Verify recipes parse**

Run: `just pipelines` (should list all recipes without error)

**Step 4: Commit**

```bash
git add pipelines/extract/download_countries.py pipelines/justfile
git commit -m "refactor: replace country download with dissolve pipeline, add transform-all"
```

---

### Task 5: Update documentation

**Files:**
- Modify: `pipelines/README.md`
- Modify: `pipelines/extract/README.md` (if it mentions country download)

**Step 1: Check extract README**

Read `pipelines/extract/README.md` for any references to country download/GISCO.

**Step 2: Update `pipelines/README.md`**

In the "Running an import task" section, the existing text is generic enough. Add a note to the Common Tasks or after the categories list:

After the line `- tasks: additional processing on data within the database`, add:

```
Use `just pipelines transform-all` to run all transform steps in the correct dependency order.
```

**Step 3: Update `pipelines/extract/README.md`**

Replace any mention of downloading country boundaries from GISCO with:
"Country metadata (code + name) is written directly from hardcoded configuration. Country geometries are dissolved from municipality boundaries in the transform step."

**Step 4: Commit**

```bash
git add pipelines/README.md pipelines/extract/README.md
git commit -m "docs: update pipeline documentation for country dissolve workflow"
```

---

### Task 6: End-to-end verification

**Step 1: Run the full pipeline to verify**

```bash
just pipelines extract-countries
just pipelines extract-municipalities
just pipelines transform-all
```

**Step 2: Verify staging.Country has geometry**

```bash
uv run python -c "
import duckdb
conn = duckdb.connect()
conn.execute(\"ATTACH 'data/staging/staging.duckdb' AS staging\")
rows = conn.sql('SELECT Code, Name, length(Geometry) as geom_len FROM staging.Country ORDER BY Code').fetchall()
for r in rows:
    print(f'{r[0]:3s}  {r[1]:20s}  geom_len={r[2]}')
print(f'Total: {len(rows)} countries')
conn.close()
"
```

Expected: 16 countries, all with non-zero geometry length.

**Step 3: Run all tests**

Run: `uv run pytest pipelines/ -v`
Expected: All pass
