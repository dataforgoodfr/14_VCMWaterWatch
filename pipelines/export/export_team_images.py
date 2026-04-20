"""
Thin wrapper that exports team member images via the generic entity image pipeline.

Team images are mirrored from NocoDB to ``<EXPORT_IMAGES_DIR>/team/``.
Names are slugified from the member's ``Name`` field (e.g. "Gaspard Lemaire"
→ ``gaspard-lemaire.<hash>.jpg``).

Run via::

    just export-team-images
"""


from pipelines.export.export_entity_images import export_entity_images_flow

TEAM_FIELDS = ["Id", "Name", "Image"]


def export_team_images():
    """Mirror team member images from NocoDB."""
    export_entity_images_flow(
        entity_name="team",
        table_name="Team",
        key_field="Name",
        fields=TEAM_FIELDS,
        slugify=True,
    )


if __name__ == "__main__":
    export_team_images()
