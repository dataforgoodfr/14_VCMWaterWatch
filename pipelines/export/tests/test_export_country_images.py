"""Tests for export_country_images workflow."""

import json
from unittest.mock import MagicMock, Mock, patch


from pipelines.export.export_country_images import (
    _ext_from_mimetype,
    download_country_images_task,
    export_country_images_flow,
)


# ---------------------------------------------------------------------------
# Unit helpers
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
# download_country_images_task
# ---------------------------------------------------------------------------


def _make_attachment(signed_url: str, mimetype: str = "image/jpeg") -> dict:
    return {"signedUrl": signed_url, "mimetype": mimetype}


def _make_records(
    pairs: list[tuple[str, list[dict] | None]],
) -> list[dict]:
    return [
        {"Id": i + 1, "Code": code, "Image": images}
        for i, (code, images) in enumerate(pairs)
    ]


class TestDownloadCountryImagesTask:
    def _run_with_mock_http(
        self,
        records: list[dict],
        tmp_path,
        *,
        image_bytes: bytes = b"fake-image-data",
        content_type: str = "image/jpeg",
    ) -> dict:
        mock_db = Mock()
        mock_db.load_all_records.return_value = records

        mock_response = MagicMock()
        mock_response.content = image_bytes
        mock_response.headers = {"content-type": content_type}
        mock_response.raise_for_status = Mock()

        with (
            patch("pipelines.export.export_country_images.services") as mock_services,
            patch("httpx.get", return_value=mock_response),
        ):
            mock_services.db_helper.return_value = mock_db
            result = download_country_images_task.fn(output_dir=tmp_path)

        return result

    def test_downloads_and_writes_file(self, tmp_path):
        records = _make_records(
            [("FR", [_make_attachment("https://example.com/fr.jpg")])]
        )
        manifest = self._run_with_mock_http(records, tmp_path)

        assert "FR" in manifest
        filename = manifest["FR"]
        assert filename.startswith("FR.")
        assert filename.endswith(".jpg")
        dest = tmp_path / filename
        assert dest.exists()
        assert dest.read_bytes() == b"fake-image-data"

    def test_uses_content_hash_in_filename(self, tmp_path):
        import hashlib

        image_bytes = b"some-image-content"
        expected_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        records = _make_records(
            [("DE", [_make_attachment("https://example.com/de.jpg")])]
        )
        manifest = self._run_with_mock_http(
            records, tmp_path, image_bytes=image_bytes
        )

        assert expected_hash in manifest["DE"]

    def test_skips_record_without_image(self, tmp_path):
        records = _make_records([("FR", None), ("DE", [_make_attachment("https://x/de.jpg")])])
        manifest = self._run_with_mock_http(records, tmp_path)

        assert "FR" not in manifest
        assert "DE" in manifest

    def test_skips_record_without_code(self, tmp_path):
        records = [{"Id": 1, "Code": None, "Image": [_make_attachment("https://x/img.jpg")]}]
        manifest = self._run_with_mock_http(records, tmp_path)
        assert manifest == {}

    def test_skips_attachment_without_signed_url(self, tmp_path):
        records = _make_records([("FR", [{"mimetype": "image/jpeg"}])])
        manifest = self._run_with_mock_http(records, tmp_path)
        assert "FR" not in manifest

    def test_uses_first_attachment_only(self, tmp_path):
        records = _make_records(
            [
                (
                    "FR",
                    [
                        _make_attachment("https://example.com/first.jpg"),
                        _make_attachment("https://example.com/second.jpg"),
                    ],
                )
            ]
        )
        manifest = self._run_with_mock_http(records, tmp_path)

        assert "FR" in manifest
        # Only one file written
        written = list(tmp_path.iterdir())
        assert len(written) == 1

    def test_handles_http_error_gracefully(self, tmp_path):
        """If download fails for one country, others still succeed."""
        import httpx

        records = _make_records(
            [
                ("FR", [_make_attachment("https://bad.example.com/fr.jpg")]),
                ("DE", [_make_attachment("https://example.com/de.jpg")]),
            ]
        )

        mock_db = Mock()
        mock_db.load_all_records.return_value = records

        good_response = MagicMock()
        good_response.content = b"ok-image"
        good_response.headers = {"content-type": "image/jpeg"}
        good_response.raise_for_status = Mock()

        bad_response = MagicMock()
        bad_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )

        def fake_get(url, **kwargs):
            if "bad" in url:
                return bad_response
            return good_response

        with (
            patch("pipelines.export.export_country_images.services") as mock_services,
            patch("httpx.get", side_effect=fake_get),
        ):
            mock_services.db_helper.return_value = mock_db
            manifest = download_country_images_task.fn(output_dir=tmp_path)

        assert "FR" not in manifest
        assert "DE" in manifest

    def test_png_extension(self, tmp_path):
        records = _make_records([("IT", [_make_attachment("https://x/it.png", "image/png")])])
        manifest = self._run_with_mock_http(
            records, tmp_path, content_type="image/png"
        )
        assert manifest["IT"].endswith(".png")


# ---------------------------------------------------------------------------
# export_country_images_flow  (integration-style, no real HTTP)
# ---------------------------------------------------------------------------


class TestExportCountryImagesFlow:
    def _run_flow(
        self,
        records: list[dict],
        destination,
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
            patch("pipelines.export.export_country_images.services") as mock_services,
            patch("httpx.get", return_value=mock_response),
        ):
            mock_services.db_helper.return_value = mock_db
            export_country_images_flow(destination=destination)

    def test_writes_manifest_json(self, tmp_path):
        dest = tmp_path / "images"
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, dest)

        manifest_path = dest / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert "FR" in manifest

    def test_manifest_maps_code_to_filename(self, tmp_path):
        dest = tmp_path / "images"
        records = _make_records(
            [
                ("FR", [_make_attachment("https://x/fr.jpg")]),
                ("DE", [_make_attachment("https://x/de.jpg")]),
            ]
        )
        self._run_flow(records, dest)
        manifest = json.loads((dest / "manifest.json").read_text())
        for code in ("FR", "DE"):
            assert code in manifest
            assert (dest / manifest[code]).exists()

    def test_removes_stale_files(self, tmp_path):
        dest = tmp_path / "images"
        dest.mkdir()
        stale = dest / "OLD.aabbccdd.jpg"
        stale.write_bytes(b"old")

        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, dest)

        assert not stale.exists(), "Stale file should be removed"
        assert (dest / "manifest.json").exists()

    def test_creates_destination_if_missing(self, tmp_path):
        dest = tmp_path / "deep" / "path" / "images"
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, dest)
        assert dest.is_dir()

    def test_no_images_skips_update(self, tmp_path):
        dest = tmp_path / "images"
        dest.mkdir()
        existing_manifest = dest / "manifest.json"
        existing_manifest.write_text('{"FR": "FR.old.jpg"}')

        self._run_flow([], dest)  # empty records → no images

        # Manifest should be unchanged
        assert existing_manifest.read_text() == '{"FR": "FR.old.jpg"}'
