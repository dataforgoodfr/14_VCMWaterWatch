"""
Thin wrapper that exports country profile images via the generic entity image pipeline.

Country images are mirrored from NocoDB to ``<EXPORT_IMAGES_DIR>/country/``.
Names use the country ``Code`` field directly (e.g. ``FR.<hash>.jpg``).

Run via::

    just export-country-images
"""


from pipelines.export.export_entity_images import export_entity_images_flow

COUNTRY_FIELDS = ["Id", "Code", "Image"]


def export_country_images():
    """Mirror country profile images from NocoDB."""
    export_entity_images_flow(
        entity_name="country",
        table_name="Country",
        key_field="Code",
        fields=COUNTRY_FIELDS,
        slugify=False,
    )


if __name__ == "__main__":
    export_country_images()
