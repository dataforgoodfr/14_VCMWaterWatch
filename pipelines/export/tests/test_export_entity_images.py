"""Tests for the generic export_entity_images workflow."""

import json
import os
from unittest.mock import MagicMock, Mock, patch


from pipelines.export.export_entity_images import (
    _ext_from_mimetype,
    _slugify,
    export_entity_images_flow,
    export_entity_images_task,
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


class TestSlugify:
    def test_lowercase(self):
        assert _slugify("Hello World") == "hello-world"

    def test_accents(self):
        assert _slugify("Gaspard Lemaire") == "gaspard-lemaire"
        assert _slugify("François Léger") == "francois-leger"

    def test_multiple_spaces(self):
        assert _slugify("A  B") == "a-b"

    def test_non_alphanum(self):
        assert _slugify("foo_bar-baz!") == "foo-bar-baz"

    def test_leading_trailing_hyphens(self):
        assert _slugify("--hello--") == "hello"


# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _make_attachment(signed_url: str, mimetype: str = "image/jpeg") -> dict:
    return {"signedUrl": signed_url, "mimetype": mimetype}


def _make_records(
    pairs: list[tuple[str, list[dict] | None]],
    key_field: str = "Code",
) -> list[dict]:
    return [
        {"Id": i + 1, key_field: key, "Image": images}
        for i, (key, images) in enumerate(pairs)
    ]


def _run_task(
    records: list[dict],
    tmp_path,
    *,
    key_field: str = "Code",
    entity_name: str = "country",
    slugify: bool = False,
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
        patch("pipelines.export.export_entity_images.services") as mock_services,
        patch("httpx.get", return_value=mock_response),
    ):
        mock_services.db_helper.return_value = mock_db
        result = export_entity_images_task.fn(
            table_name="TestTable",
            key_field=key_field,
            entity_name=entity_name,
            fields=[key_field, "Image"],
            output_dir=tmp_path,
            slugify=slugify,
        )

    return result


# ---------------------------------------------------------------------------
# export_entity_images_task
# ---------------------------------------------------------------------------


class TestExportEntityImagesTask:
    def test_downloads_and_writes_file(self, tmp_path):
        records = _make_records([("FR", [_make_attachment("https://example.com/fr.jpg")])])
        manifest = _run_task(records, tmp_path)

        assert "FR" in manifest
        filename = manifest["FR"]
        assert filename.startswith("FR.")
        assert filename.endswith(".jpg")
        assert (tmp_path / filename).read_bytes() == b"fake-image-data"

    def test_uses_content_hash_in_filename(self, tmp_path):
        import hashlib

        image_bytes = b"some-image-content"
        expected_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        records = _make_records([("DE", [_make_attachment("https://example.com/de.jpg")])])
        manifest = _run_task(records, tmp_path, image_bytes=image_bytes)

        assert expected_hash in manifest["DE"]

    def test_skips_record_without_image(self, tmp_path):
        records = _make_records(
            [("FR", None), ("DE", [_make_attachment("https://x/de.jpg")])]
        )
        manifest = _run_task(records, tmp_path)
        assert "FR" not in manifest
        assert "DE" in manifest

    def test_skips_record_without_key(self, tmp_path):
        records = [{"Id": 1, "Code": None, "Image": [_make_attachment("https://x/img.jpg")]}]
        manifest = _run_task(records, tmp_path)
        assert manifest == {}

    def test_skips_attachment_without_signed_url(self, tmp_path):
        records = _make_records([("FR", [{"mimetype": "image/jpeg"}])])
        manifest = _run_task(records, tmp_path)
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
        manifest = _run_task(records, tmp_path)
        assert "FR" in manifest
        written = [f for f in tmp_path.iterdir() if not f.name.startswith(".")]
        assert len(written) == 1

    def test_handles_http_error_gracefully(self, tmp_path):
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
            return bad_response if "bad" in url else good_response

        with (
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", side_effect=fake_get),
        ):
            mock_services.db_helper.return_value = mock_db
            manifest = export_entity_images_task.fn(
                table_name="Country",
                key_field="Code",
                entity_name="country",
                fields=["Code", "Image"],
                output_dir=tmp_path,
                slugify=False,
            )

        assert "FR" not in manifest
        assert "DE" in manifest

    def test_png_extension(self, tmp_path):
        records = _make_records([("IT", [_make_attachment("https://x/it.png", "image/png")])])
        manifest = _run_task(records, tmp_path, content_type="image/png")
        assert manifest["IT"].endswith(".png")

    def test_slugify_key(self, tmp_path):
        records = _make_records(
            [("Gaspard Lemaire", [_make_attachment("https://x/img.jpg")])],
            key_field="Name",
        )
        manifest = _run_task(records, tmp_path, key_field="Name", slugify=True)
        assert "gaspard-lemaire" in manifest
        assert manifest["gaspard-lemaire"].startswith("gaspard-lemaire.")

    def test_slug_collision_suffixed(self, tmp_path):
        """Two records whose names slugify to the same value get distinct keys."""
        records = [
            {"Id": 1, "Name": "Test User", "Image": [_make_attachment("https://x/1.jpg")]},
            {"Id": 2, "Name": "Test-User", "Image": [_make_attachment("https://x/2.jpg")]},
        ]
        manifest = _run_task(records, tmp_path, key_field="Name", slugify=True)
        assert "test-user" in manifest
        assert "test-user-2" in manifest


# ---------------------------------------------------------------------------
# export_entity_images_flow (integration-style, no real HTTP)
# ---------------------------------------------------------------------------


def _run_flow(
    records: list[dict],
    base_dir,
    *,
    entity_name: str = "country",
    key_field: str = "Code",
    image_bytes: bytes = b"img",
    content_type: str = "image/jpeg",
    extra_env: dict | None = None,
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
            entity_name=entity_name,
            table_name="TestTable",
            key_field=key_field,
            fields=[key_field, "Image"],
            slugify=(key_field == "Name"),
        )


class TestExportEntityImagesFlow:
    def _dest(self, base_dir, entity_name: str = "country"):
        return base_dir / entity_name

    def test_writes_manifest_json(self, tmp_path):
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        _run_flow(records, tmp_path)

        dest = self._dest(tmp_path)
        manifest_path = dest / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert "FR" in manifest

    def test_manifest_maps_key_to_filename(self, tmp_path):
        records = _make_records(
            [
                ("FR", [_make_attachment("https://x/fr.jpg")]),
                ("DE", [_make_attachment("https://x/de.jpg")]),
            ]
        )
        _run_flow(records, tmp_path)
        dest = self._dest(tmp_path)
        manifest = json.loads((dest / "manifest.json").read_text())
        for code in ("FR", "DE"):
            assert code in manifest
            assert (dest / manifest[code]).exists()

    def test_removes_stale_files(self, tmp_path):
        dest = self._dest(tmp_path)
        dest.mkdir(parents=True)
        stale = dest / "OLD.aabbccdd.jpg"
        stale.write_bytes(b"old")

        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        _run_flow(records, tmp_path)

        assert not stale.exists(), "Stale file should be removed"
        assert (dest / "manifest.json").exists()

    def test_creates_destination_if_missing(self, tmp_path):
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        _run_flow(records, tmp_path / "deep" / "path")
        assert (tmp_path / "deep" / "path" / "country").is_dir()

    def test_no_images_skips_update(self, tmp_path):
        dest = self._dest(tmp_path)
        dest.mkdir(parents=True)
        existing_manifest = dest / "manifest.json"
        existing_manifest.write_text('{"FR": "FR.old.jpg"}')

        _run_flow([], tmp_path)  # empty records → no images

        # Manifest should be unchanged
        assert existing_manifest.read_text() == '{"FR": "FR.old.jpg"}'

    def test_team_entity_uses_slugified_keys(self, tmp_path):
        records = [
            {"Id": 1, "Name": "Alice Martin", "Image": [_make_attachment("https://x/1.jpg")]},
        ]
        _run_flow(records, tmp_path, entity_name="team", key_field="Name")
        dest = self._dest(tmp_path, "team")
        manifest = json.loads((dest / "manifest.json").read_text())
        assert "alice-martin" in manifest
