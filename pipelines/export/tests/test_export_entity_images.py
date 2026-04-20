"""Tests for the generic export_entity_images workflow."""

import json
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
    def test_simple(self):
        assert _slugify("Gaspard Lemaire") == "gaspard-lemaire"

    def test_accents_removed(self):
        assert _slugify("Ève Müller") == "eve-muller"

    def test_apostrophe(self):
        assert _slugify("John O'Brien") == "john-o-brien"

    def test_multiple_spaces_become_single_dash(self):
        assert _slugify("John  Smith") == "john-smith"

    def test_underscores(self):
        assert _slugify("some_name") == "some-name"

    def test_trim_dashes(self):
        assert _slugify("  hello  ") == "hello"

    def test_numbers_preserved(self):
        assert _slugify("Member 42") == "member-42"

    def test_all_special_chars(self):
        assert _slugify("Ångström & Co.") == "angstrom-co"


# ---------------------------------------------------------------------------
# Helper constructors
# ---------------------------------------------------------------------------


def _make_attachment(signed_url: str, mimetype: str = "image/jpeg") -> dict:
    return {"signedUrl": signed_url, "mimetype": mimetype}


def _make_records(
    pairs: list[tuple[str, list[dict] | None]],
    key_field: str = "Code",
) -> list[dict]:
    return [
        {"Id": i + 1, key_field: code, "Image": images}
        for i, (code, images) in enumerate(pairs)
    ]


# ---------------------------------------------------------------------------
# export_entity_images_task — country (no slugify)
# ---------------------------------------------------------------------------


class TestExportEntityImagesTaskCountry:
    def _run(
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
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", return_value=mock_response),
        ):
            mock_services.db_helper.return_value = mock_db
            result = export_entity_images_task.fn(
                table_name="Country",
                key_field="Code",
                entity_name="country",
                fields=["Id", "Code", "Image"],
                output_dir=tmp_path,
                slugify=False,
            )

        return result

    def test_downloads_and_writes_file(self, tmp_path):
        records = _make_records([("FR", [_make_attachment("https://example.com/fr.jpg")])])
        manifest = self._run(records, tmp_path)

        assert "FR" in manifest
        filename = manifest["FR"]
        assert filename.startswith("FR.")
        assert filename.endswith(".jpg")
        assert (tmp_path / filename).exists()
        assert (tmp_path / filename).read_bytes() == b"fake-image-data"

    def test_uses_content_hash_in_filename(self, tmp_path):
        import hashlib

        image_bytes = b"some-image-content"
        expected_hash = hashlib.sha256(image_bytes).hexdigest()[:8]

        records = _make_records([("DE", [_make_attachment("https://example.com/de.jpg")])])
        manifest = self._run(records, tmp_path, image_bytes=image_bytes)

        assert expected_hash in manifest["DE"]

    def test_skips_record_without_image(self, tmp_path):
        records = _make_records([("FR", None), ("DE", [_make_attachment("https://x/de.jpg")])])
        manifest = self._run(records, tmp_path)

        assert "FR" not in manifest
        assert "DE" in manifest

    def test_skips_record_without_key(self, tmp_path):
        records = [{"Id": 1, "Code": None, "Image": [_make_attachment("https://x/img.jpg")]}]
        manifest = self._run(records, tmp_path)
        assert manifest == {}

    def test_skips_attachment_without_signed_url(self, tmp_path):
        records = _make_records([("FR", [{"mimetype": "image/jpeg"}])])
        manifest = self._run(records, tmp_path)
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
        manifest = self._run(records, tmp_path)

        assert "FR" in manifest
        assert len(list(tmp_path.iterdir())) == 1

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
            if "bad" in url:
                return bad_response
            return good_response

        with (
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", side_effect=fake_get),
        ):
            mock_services.db_helper.return_value = mock_db
            manifest = export_entity_images_task.fn(
                table_name="Country",
                key_field="Code",
                entity_name="country",
                fields=["Id", "Code", "Image"],
                output_dir=tmp_path,
                slugify=False,
            )

        assert "FR" not in manifest
        assert "DE" in manifest

    def test_png_extension(self, tmp_path):
        records = _make_records([("IT", [_make_attachment("https://x/it.png", "image/png")])])
        manifest = self._run(records, tmp_path, content_type="image/png")
        assert manifest["IT"].endswith(".png")


# ---------------------------------------------------------------------------
# export_entity_images_task — team (slugify=True)
# ---------------------------------------------------------------------------


class TestExportEntityImagesTaskTeam:
    def _run(
        self,
        records: list[dict],
        tmp_path,
        *,
        image_bytes: bytes = b"team-image",
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
                table_name="Team",
                key_field="Name",
                entity_name="team",
                fields=["Id", "Name", "Image"],
                output_dir=tmp_path,
                slugify=True,
            )

        return result

    def _make_team_records(self, pairs: list[tuple[str, list[dict] | None]]) -> list[dict]:
        return [
            {"Id": i + 1, "Name": name, "Image": images}
            for i, (name, images) in enumerate(pairs)
        ]

    def test_slugifies_name(self, tmp_path):
        records = self._make_team_records(
            [("Gaspard Lemaire", [_make_attachment("https://x/g.jpg")])]
        )
        manifest = self._run(records, tmp_path)

        assert "gaspard-lemaire" in manifest
        assert manifest["gaspard-lemaire"].startswith("gaspard-lemaire.")

    def test_slug_collision_suffix(self, tmp_path, caplog):
        """Two members whose names produce the same slug get -2 suffix."""
        records = self._make_team_records(
            [
                ("Marie Laurent", [_make_attachment("https://x/m1.jpg")]),
                ("Marie Laurent", [_make_attachment("https://x/m2.jpg")]),
            ]
        )

        mock_db = Mock()
        mock_db.load_all_records.return_value = records

        call_count = 0

        def fake_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            # Different bytes so hashes differ
            resp.content = f"image-{call_count}".encode()
            resp.headers = {"content-type": "image/jpeg"}
            resp.raise_for_status = Mock()
            return resp

        with (
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", side_effect=fake_get),
        ):
            mock_services.db_helper.return_value = mock_db
            manifest = export_entity_images_task.fn(
                table_name="Team",
                key_field="Name",
                entity_name="team",
                fields=["Id", "Name", "Image"],
                output_dir=tmp_path,
                slugify=True,
            )

        assert "marie-laurent" in manifest
        assert "marie-laurent-2" in manifest

    def test_accentuated_name(self, tmp_path):
        records = self._make_team_records(
            [("Ève Müller", [_make_attachment("https://x/e.jpg")])]
        )
        manifest = self._run(records, tmp_path)

        assert "eve-muller" in manifest

    def test_skips_empty_name(self, tmp_path):
        records = self._make_team_records(
            [("", [_make_attachment("https://x/empty.jpg")])]
        )
        manifest = self._run(records, tmp_path)
        assert manifest == {}


# ---------------------------------------------------------------------------
# export_entity_images_flow  (integration-style, no real HTTP)
# ---------------------------------------------------------------------------


class TestExportEntityImagesFlow:
    def _run_flow(
        self,
        records: list[dict],
        base_dir,
        *,
        entity_name: str = "country",
        table_name: str = "Country",
        key_field: str = "Code",
        fields: list[str] | None = None,
        slugify: bool = False,
        image_bytes: bytes = b"img",
        content_type: str = "image/jpeg",
    ):
        if fields is None:
            fields = ["Id", "Code", "Image"]

        mock_db = Mock()
        mock_db.load_all_records.return_value = records

        mock_response = MagicMock()
        mock_response.content = image_bytes
        mock_response.headers = {"content-type": content_type}
        mock_response.raise_for_status = Mock()

        env_patch = {"EXPORT_IMAGES_DIR": str(base_dir)}

        with (
            patch("pipelines.export.export_entity_images.services") as mock_services,
            patch("httpx.get", return_value=mock_response),
            patch.dict("os.environ", env_patch),
        ):
            mock_services.db_helper.return_value = mock_db
            export_entity_images_flow(
                entity_name=entity_name,
                table_name=table_name,
                key_field=key_field,
                fields=fields,
                slugify=slugify,
            )

    def test_writes_manifest_json(self, tmp_path):
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, tmp_path)

        manifest_path = tmp_path / "country" / "manifest.json"
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
        self._run_flow(records, tmp_path)
        dest = tmp_path / "country"
        manifest = json.loads((dest / "manifest.json").read_text())
        for code in ("FR", "DE"):
            assert code in manifest
            assert (dest / manifest[code]).exists()

    def test_removes_stale_files(self, tmp_path):
        dest = tmp_path / "country"
        dest.mkdir()
        stale = dest / "OLD.aabbccdd.jpg"
        stale.write_bytes(b"old")

        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, tmp_path)

        assert not stale.exists()
        assert (dest / "manifest.json").exists()

    def test_creates_destination_if_missing(self, tmp_path):
        dest = tmp_path / "images"
        records = _make_records([("FR", [_make_attachment("https://x/fr.jpg")])])
        self._run_flow(records, dest)
        assert (dest / "country").is_dir()

    def test_no_images_skips_update(self, tmp_path):
        dest = tmp_path / "country"
        dest.mkdir()
        existing_manifest = dest / "manifest.json"
        existing_manifest.write_text('{"FR": "FR.old.jpg"}')

        self._run_flow([], tmp_path)

        assert existing_manifest.read_text() == '{"FR": "FR.old.jpg"}'

    def test_team_entity_uses_team_subdir(self, tmp_path):
        records = [
            {"Id": 1, "Name": "Alice Smith", "Image": [_make_attachment("https://x/a.jpg")]}
        ]
        self._run_flow(
            records,
            tmp_path,
            entity_name="team",
            table_name="Team",
            key_field="Name",
            fields=["Id", "Name", "Image"],
            slugify=True,
        )
        manifest_path = tmp_path / "team" / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert "alice-smith" in manifest
