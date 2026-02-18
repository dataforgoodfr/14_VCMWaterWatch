"""Tests for export_pmtiles workflow."""

import json
import subprocess
from unittest.mock import Mock, patch

import polars as pl
import pytest

from pipelines.export.export_pmtiles import create_pmtiles_task, export_zones_geojson_task


class TestExportZonesGeojson:

    def test_produces_valid_feature_collection(self, tmp_path):
        """Records with geometry become Features; records without are skipped."""
        fake_df = pl.DataFrame({
            "Code": ["DE", "FR", "XX"],
            "Name": ["Germany", "France", "NoGeom"],
            "Geometry": [
                '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}',
                '{"type":"Polygon","coordinates":[[[2,2],[3,2],[3,3],[2,2]]]}',
                None,
            ],
            "PVC Level": ["High", "Low", None],
            "VCM Level": ["Medium", None, None],
        })

        mock_db = Mock()
        mock_db.load_all_records.return_value = fake_df

        with patch("pipelines.export.export_pmtiles.services") as mock_services:
            mock_services.db_helper.return_value = mock_db

            path = export_zones_geojson_task.fn(
                table_name="Country", output_dir=tmp_path
            )

        assert path == tmp_path / "Country_tile_data.geojson"

        collection = json.loads(path.read_text())
        assert collection["type"] == "FeatureCollection"
        assert len(collection["features"]) == 2

        de = collection["features"][0]
        assert de["properties"]["code"] == "DE"
        assert de["properties"]["pvc_level"] == "High"
        assert de["properties"]["vcm_level"] == "Medium"
        assert de["geometry"]["type"] == "Polygon"

        fr = collection["features"][1]
        assert fr["properties"]["code"] == "FR"
        assert fr["properties"]["vcm_level"] is None

    def test_empty_table_produces_empty_collection(self, tmp_path):
        """An empty table should produce a valid but empty FeatureCollection."""
        fake_df = pl.DataFrame(
            schema={
                "Code": pl.Utf8,
                "Name": pl.Utf8,
                "Geometry": pl.Utf8,
                "PVC Level": pl.Utf8,
                "VCM Level": pl.Utf8,
            }
        )

        mock_db = Mock()
        mock_db.load_all_records.return_value = fake_df

        with patch("pipelines.export.export_pmtiles.services") as mock_services:
            mock_services.db_helper.return_value = mock_db

            path = export_zones_geojson_task.fn(
                table_name="Country", output_dir=tmp_path
            )

        collection = json.loads(path.read_text())
        assert collection["features"] == []


def _sample_geojson() -> dict:
    """A minimal valid GeoJSON FeatureCollection with two polygons."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
                "properties": {"code": "DE", "name": "Germany"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]],
                },
                "properties": {"code": "FR", "name": "France"},
            },
        ],
    }


class TestCreatePmtiles:

    def test_produces_pmtiles_file(self, tmp_path):
        """tippecanoe creates a .pmtiles file named after the layer."""
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "output"

        result = create_pmtiles_task.fn(
            geojson_file=geojson_file,
            layer="data_countries",
            output_dir=output_dir,
        )

        assert result == output_dir / "data_countries.pmtiles"
        assert result.exists()
        assert result.stat().st_size > 0

    def test_creates_output_dir_if_missing(self, tmp_path):
        """output_dir is created automatically when it does not exist."""
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "nested" / "deep" / "output"

        result = create_pmtiles_task.fn(
            geojson_file=geojson_file,
            layer="test_layer",
            output_dir=output_dir,
        )

        assert output_dir.is_dir()
        assert result.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """--force flag allows idempotent re-runs."""
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "output"

        # Run twice — second run must not fail
        create_pmtiles_task.fn(
            geojson_file=geojson_file, layer="data_countries", output_dir=output_dir
        )
        result = create_pmtiles_task.fn(
            geojson_file=geojson_file, layer="data_countries", output_dir=output_dir
        )

        assert result.exists()

    def test_raises_on_invalid_input(self, tmp_path):
        """tippecanoe should fail on a malformed GeoJSON file."""
        bad_file = tmp_path / "bad.geojson"
        bad_file.write_text("not valid json at all")
        output_dir = tmp_path / "output"

        with pytest.raises(subprocess.CalledProcessError):
            create_pmtiles_task.fn(
                geojson_file=bad_file, layer="bad_layer", output_dir=output_dir
            )
