"""Tests for the export_country_images wrapper.

The heavy logic has moved to ``export_entity_images``.  These tests verify
that the wrapper correctly delegates to the generic flow with country-specific
arguments.  Full coverage of the generic pipeline is in
``test_export_entity_images.py``.
"""

from unittest.mock import patch

from pipelines.export.export_country_images import export_country_images


class TestExportCountryImagesWrapper:
    def test_delegates_to_generic_flow(self):
        with patch(
            "pipelines.export.export_country_images.export_entity_images_flow"
        ) as mock_flow:
            export_country_images()

        mock_flow.assert_called_once_with(
            entity_name="country",
            table_name="Country",
            key_field="Code",
            fields=["Id", "Code", "Image"],
            slugify=False,
        )
