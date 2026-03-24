"""
Prefect workflow for building a SearchIndex field on DistributionZone records.
The SearchIndex concatenates zone name, municipality names, and actor names
to enable search across all three.
"""

from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from pipelines.common import services


@task(name="build_search_index", cache_policy=NO_CACHE)
def build_search_index_task(db_helper):
    """
    Build a SearchIndex text field for each DistributionZone by combining
    zone name, municipality names, and actor names.
    """
    # Load distribution zones
    zones = db_helper.load_all_records(
        "DistributionZone",
        fields=["Id", "Name", "ActorName"],
    )

    # Load municipalities to get their names grouped by zone
    municipalities = db_helper.load_all_records(
        "Municipality",
        fields=["Id", "Name", "DistributionZone"],
    )

    # Build a map of zone ID -> list of municipality names
    zone_municipalities: dict[int, list[str]] = {}
    for muni in municipalities:
        dz_links = muni.get("DistributionZone")
        if dz_links and isinstance(dz_links, list):
            for dz in dz_links:
                dz_id = dz.get("Id") if isinstance(dz, dict) else dz
                if dz_id:
                    zone_municipalities.setdefault(dz_id, []).append(muni["Name"])
        elif dz_links and isinstance(dz_links, dict):
            dz_id = dz_links.get("Id")
            if dz_id:
                zone_municipalities.setdefault(dz_id, []).append(muni["Name"])

    # Build search index for each zone
    updates = []
    for zone in zones:
        parts = [zone["Name"]]

        muni_names = zone_municipalities.get(zone["Id"], [])
        if muni_names:
            parts.append(", ".join(muni_names))

        actor_names = zone.get("ActorName")
        if actor_names:
            if isinstance(actor_names, list):
                parts.append(", ".join(actor_names))
            else:
                parts.append(str(actor_names))

        search_index = " | ".join(parts)
        updates.append({"Id": zone["Id"], "SearchIndex": search_index})

    if updates:
        db_helper.update_records(updates, "DistributionZone")

    return len(updates)


@flow(name="build_search_index")
def build_search_index():
    db = services.db_helper()
    count = build_search_index_task(db)
    print(f"Updated SearchIndex for {count} distribution zones")


if __name__ == "__main__":
    build_search_index()
