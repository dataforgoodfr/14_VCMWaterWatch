"""Example usage of DatabaseHelper for NocoDB operations."""
from db_helper import DatabaseHelper
import polars as pl

# Example 1: Initialize with API token
# The base URL and table IDs are automatically loaded from nocodb_swagger.json
db = DatabaseHelper(api_token="your_token_here")

# Example 2: Load specific fields from a table
zones_df = db.load_fields(
    table_name="Zone",
    fields=["Id", "Title", "Code"]
)
print(zones_df)

# Example 3: Load fields with a condition
filtered_zones = db.load_fields(
    table_name="Zone",
    fields=["Id", "Title", "Code"],
    condition={"Code": "FR"}  # WHERE Code = 'FR'
)
print(filtered_zones)

# Example 4: Load all records with automatic pagination
all_zones = db.load_all_records(
    table_name="Zone",
    fields=["Id", "Title", "Code", "Geometry"]
)
print(f"Total zones: {len(all_zones)}")

# Example 5: Insert new records
new_zones = pl.DataFrame({
    "Title": ["New Zone 1", "New Zone 2"],
    "Code": ["NZ1", "NZ2"],
    "Geometry": ['{"type": "Point", "coordinates": [0, 0]}'] * 2
})
db.insert_records(new_zones, "Zone")

# Available tables (loaded dynamically from swagger):
# Run this to see what tables are available:
print(f"Available tables: {list(db.table_ids.keys())}")


