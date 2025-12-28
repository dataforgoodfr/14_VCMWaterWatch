# GeoJSON Import Workflow

A Prefect workflow for importing GeoJSON data at various geographic levels (Country, Region, PostalCode).

## Features

- Import GeoJSON FeatureCollection data at multiple geographic levels
- Configurable property mappings for Title and Code
- Automatic parent relationship resolution
- Duplicate detection (skips existing records)
- Uses Polars for efficient data processing

## Installation

```bash
uv sync
```

## Configuration

Edit `config.py` to configure level mappings:

```python
LEVEL_CONFIGS = {
    "Country": LevelConfig(
        file_suffix="Countries",
        title_property="name",
        code_property="iso_code",
        parent_level=None,
        table_name="countries"
    ),
    # ... other levels
}
```

## Usage

### Basic Usage

```python
from workflow import load_zones_level_flow
from pathlib import Path

load_zones_level_flow(
    level="Country",
    geojson_file_path=Path("data/countries.geojson"),
    db_connection_string="postgresql://user:pass@host:port/dbname"
)
```

### Command Line

```bash
python workflow.py Country data/countries.geojson "postgresql://user:pass@host:port/dbname"
```

## Workflow Steps

1. **Load Reference Data**: Loads parent area codes and IDs from the database
2. **Load Existing Data**: Loads existing codes for the current level to avoid duplicates
3. **Transform GeoJSON**: Converts GeoJSON features to Polars DataFrame with Title, Code, Geometry, and ParentCode
4. **Lookup Parent**: Resolves parent IDs using the reference data
5. **Load to Database**: Inserts new records into the database

## Database Schema

Each level table should have the following columns:
- `Title` (string): The title/name of the geographic area
- `Code` (string): Unique code identifier
- `Geometry` (JSON/Geometry): GeoJSON geometry
- `Parent` (integer, nullable): Foreign key to parent area ID
