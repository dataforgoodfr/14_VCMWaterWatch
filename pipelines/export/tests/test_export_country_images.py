"""
Tests for export_country_images — now a thin wrapper around export_entity_images.

The full generic tests live in test_export_entity_images.py.  These tests
verify the country-specific wrapper invokes the generic flow with the correct
parameters.
"""

import os
from unittest.mock import MagicMock, Mock, patch

from pipelines.export.export_entity_images import (
    _ext_from_mimetype,
    export_entity_images_flow,
)


# ---------------------------------------------------------------------------
# Smoke-test: the wrapper symbols are importable
# ---------------------------------------------------------------------------


class TestExtFromMimetype:
    def test_jpeg(self):
        assert _ext_from_mimetype("image/jpeg") == ".jpg"

    def test_png(self):
        assert _ext_from_mimetype("image/png") == ".png"

    def test_webp(self):
        assert _ext_from_mimetype("image/webp") == ".webp"

    def test_none_falls_back_to_bin(self):
        assert _ext_from_mimetype(None) == ".bin"

    def test_unknown_falls_back_to_bin(self):
        assert _ext_from_mimetype("application/octet-stream") == ".bin"


# ---------------------------------------------------------------------------
# Functional: country flow writes expected manifest
# ---------------------------------------------------------------------------


def _make_attachment(signed_url: str, mimetype: str = "image/jpeg") -> dict:
    return {"signedUrl": signed_url, "mimetype": mimetype}


def _make_records(pairs: list[tuple[str, list[dict] | None]]) -> list[dict]:
    return [
        {"Id": i + 1, "Code": code, "Image": images}
        for i, (code, images) in enumerate(pairs)
    ]


class TestCountryImagesViaGenericFlow:
    def _run_country_flow(
        self,
        records: list[dict],
        base_dir,
        *,
        image_bytes: bytes = b"img",
        content_type: str = "image/jpeg",
    ):
        mock_db = Mock()
        mock_db.load_all_records.return_value = records

        mock_response = MagicMock()
        mock_response.content = image_bytes
        mock_response.headers = {"content-type": content_type}
        mock_response.raise_for_status = Mock()

        with (
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", return_value=mock_response),
            patch.dict(os.environ, {"EXPORT_IMAGES_DIR": str(base_dir)}),
        ):
            mock_services.db_helper.return_value = mock_db
            export_entity_images_flow(
                entity_name="country",
                table_name="Country",
                key_field="Code",
                fields=["Id", "Code", "Image"],
                slugify=False,
            )

    def test_writes_manifest_for_countries(self, tmp_path):
        import json

        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_country_flow(records, tmp_path)

        dest = tmp_path / "country"
        manifest = json.loads((dest / "manifest.json").read_text())
        assert "FR" in manifest
        assert (dest / manifest["FR"]).exists()

    def test_country_code_used_as_key(self, tmp_path):
        import json

        records = _make_records(
            [
                ("FR", [_make_attachment("https://x/fr.jpg")]),
                ("DE", [_make_attachment("https://x/de.jpg")]),
            ]
        )
        self._run_country_flow(records, tmp_path)

        manifest = json.loads((tmp_path / "country" / "manifest.json").read_text())
        for code in ("FR", "DE"):
            assert code in manifest
            assert manifest[code].startswith(f"{code}.")
