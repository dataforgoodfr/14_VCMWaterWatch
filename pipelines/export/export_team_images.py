"""
Thin wrapper around :mod:`pipelines.export.export_entity_images` for About
page team member photos.

Kept as a named module so Prefect deployments and webhook triggers can
reference it explicitly, and so ``just export-team-images`` has a clear entry
point.
"""

from pipelines.export.export_entity_images import export_entity_images_flow

TEAM_FIELDS = ["Id", "Name", "Image"]

if __name__ == "__main__":
    export_entity_images_flow(
        entity_name="team",
        table_name="Team",
        key_field="Name",
        fields=TEAM_FIELDS,
        slugify=True,
    )
