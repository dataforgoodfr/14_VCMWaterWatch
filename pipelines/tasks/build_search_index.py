"""
Build a SearchIndex field on DistributionZone records.
The SearchIndex concatenates zone name, municipality names (from the zone's
Municipalities link), and actor names to enable search across all three.
"""

from pipelines.common import services


def _linked_record_ids(links) -> list[int]:
    """Extract numeric Ids from a NocoDB Links field (list/dict/scalar)."""
    if links is None:
        return []
    ids: list[int] = []
    if isinstance(links, list):
        for item in links:
            if isinstance(item, dict):
                raw = item.get("Id", item.get("id"))
            else:
                raw = item
            if raw is not None:
                ids.append(int(raw))
    elif isinstance(links, dict):
        raw = links.get("Id", links.get("id"))
        if raw is not None:
            ids.append(int(raw))
    else:
        ids.append(int(links))
    return ids


def build_search_index_task(db_helper):
    """
    Build a SearchIndex text field for each DistributionZone by combining
    zone name, municipality names, and actor names.
    """
    # Municipality → zone link title varies in NocoDB; use DistributionZone.Municipalities instead.
    municipalities = db_helper.load_all_records(
        "Municipality",
        fields=["Id", "Name"],
    )
    id_to_name: dict[int, str] = {}
    for muni in municipalities:
        mid = muni.get("Id")
        if mid is not None and muni.get("Name") is not None:
            id_to_name[int(mid)] = muni["Name"]

    zones = db_helper.load_all_records(
        "DistributionZone",
        fields=["Id", "Name", "ActorName", "Municipalities"],
    )

    # Build search index for each zone
    updates = []
    for zone in zones:
        parts = [zone["Name"]]

        muni_ids = _linked_record_ids(zone.get("Municipalities"))
        muni_names = [id_to_name[i] for i in muni_ids if i in id_to_name]
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


def build_search_index():
    db = services.db_helper()
    count = build_search_index_task(db)
    print(f"Updated SearchIndex for {count} distribution zones")


if __name__ == "__main__":
    build_search_index()
