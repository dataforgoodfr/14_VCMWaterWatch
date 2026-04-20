"""
Thin wrapper around :mod:`pipelines.export.export_entity_images` for country
profile images.

Kept as a named module so existing Prefect deployments, webhook triggers, and
``just export-country-images`` continue to work without reconfiguration.
"""


from pipelines.export.export_entity_images import (
    _ext_from_mimetype,
    export_entity_images_flow,
    export_entity_images_task,
)

__all__ = [
    "_ext_from_mimetype",
    "export_entity_images_task",
    "export_entity_images_flow",
]

COUNTRY_FIELDS = ["Id", "Code", "Image"]


if __name__ == "__main__":
    export_entity_images_flow(
        entity_name="country",
        table_name="Country",
        key_field="Code",
        fields=COUNTRY_FIELDS,
        slugify=False,
    )
