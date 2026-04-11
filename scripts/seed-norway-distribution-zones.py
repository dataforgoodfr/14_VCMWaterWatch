#!/usr/bin/env python3
"""Create a DistributionZone and Actor for each Norwegian municipality.

For each municipality in Norway:
 - Creates a DistributionZone with the same name, code, and geometry, linked to
   the municipality and country
 - Creates an Actor (Type "Water Company") with the same name, linked to the DZ

Skips municipalities that already have a matching DistributionZone (by Code).

Usage: python3 scripts/seed-norway-distribution-zones.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipelines.common.db_helper import DatabaseHelper

NOCODB_URL = os.environ.get(
    "NOCODB_URL", "https://noco.services.dataforgood.fr"
)
NOCODB_TOKEN = os.environ.get("NOCODB_TOKEN", "")
NOCODB_BASE_ID = os.environ.get("NOCODB_BASE_ID", "pqc6cnm5mpnr9ka")


def main():
    if not NOCODB_TOKEN:
        print("Set NOCODB_TOKEN environment variable")
        sys.exit(1)

    db = DatabaseHelper(
        api_token=NOCODB_TOKEN, base_url=NOCODB_URL, base_id=NOCODB_BASE_ID
    )

    # 1. Find Norway country ID
    countries = db.load_all_records("Country", fields=["Code", "Id"])
    norway = next((c for c in countries if c["Code"] == "NO"), None)
    if not norway:
        print("Country 'NO' not found")
        sys.exit(1)
    norway_id = norway["Id"]
    print(f"Norway country ID: {norway_id}")

    # 2. Load Norwegian municipalities
    # Filter to Norway - municipalities are linked to country, but we may need
    # to load the country link. Let's load with Country field too.
    munis_with_country = db.load_all_records(
        "Municipality", fields=["Id", "Code", "Name", "Geometry", "Country"]
    )
    no_munis = [
        m for m in munis_with_country
        if _is_norway(m, norway_id)
    ]
    print(f"Found {len(no_munis)} Norwegian municipalities")

    # 3. Load existing DZs to skip duplicates
    existing_dzs = db.load_all_records(
        "DistributionZone", fields=["Code", "Id"]
    )
    existing_dz_codes = {dz["Code"] for dz in existing_dzs}

    to_create = [m for m in no_munis if m["Name"] not in existing_dz_codes]
    print(f"{len(to_create)} new DistributionZones to create (skipping {len(no_munis) - len(to_create)} existing)")

    if not to_create:
        print("Nothing to do")
        return

    # 4. Create DistributionZones
    dz_records = [
        {
            "Code": m["Name"],
            "Name": m["Name"],
            "Geometry": m.get("Geometry"),
            "Country": {"Id": norway_id},
        }
        for m in to_create
    ]
    inserted_dzs = db.insert_records(dz_records, "DistributionZone")
    print(f"Inserted {len(inserted_dzs)} DistributionZones")

    # 5. Link DZs to their municipalities
    for dz, muni in zip(inserted_dzs, to_create):
        dz["Municipality_id"] = muni["Id"]
    db.link_records(
        inserted_dzs,
        table_name="DistributionZone",
        link_field_name="Municipalities",
        foreign_key_column="Municipality_id",
    )
    print("Linked DistributionZones to Municipalities")

    # 6. Create Actors
    actor_records = [
        {
            "Name": m["Name"],
            "Type": "Water Company",
            "Country_id": norway_id,
        }
        for m in to_create
    ]
    inserted_actors = db.insert_records(actor_records, "Actor")
    print(f"Inserted {len(inserted_actors)} Actors")

    # 7. Link Actors to DZs
    for actor, dz in zip(inserted_actors, inserted_dzs):
        actor["DistributionZone_id"] = dz["Id"]
    db.link_records(
        inserted_actors,
        table_name="Actor",
        link_field_name="Distribution Zones",
        foreign_key_column="DistributionZone_id",
    )
    print("Linked Actors to DistributionZones")

    print("\nDone!")


def _is_norway(muni: dict, norway_id) -> bool:
    """Check if a municipality belongs to Norway."""
    country = muni.get("Country")
    if not country:
        return False
    # Country field could be a dict with Id, or a list of linked records
    if isinstance(country, dict):
        return country.get("Id") == norway_id or country.get("id") == norway_id
    if isinstance(country, list):
        return any(c.get("Id") == norway_id or c.get("id") == norway_id for c in country)
    return False


if __name__ == "__main__":
    main()
