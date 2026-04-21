"""Tests for export_pmtiles workflow."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from pipelines.export.export_pmtiles import create_pmtiles_task, export_zones_geojson_task


class TestExportZonesGeojson:

    def test_produces_valid_feature_collection(self, tmp_path):
        """Records with geometry become Features; records without are skipped."""
        fake_records = [
            {
                "Id": 1, "Code": "DE", "Name": "Germany",
                "Geometry": '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}',
                "PVC Level": "High", "VCM Level": "Medium",
            },
            {
                "Id": 2, "Code": "FR", "Name": "France",
                "Geometry": '{"type":"Polygon","coordinates":[[[2,2],[3,2],[3,3],[2,2]]]}',
                "PVC Level": "Low", "VCM Level": None,
            },
            {
                "Id": 3, "Code": "XX", "Name": "NoGeom",
                "Geometry": None,
                "PVC Level": None, "VCM Level": None,
            },
        ]

        mock_db = Mock()
        mock_db.load_all_records.return_value = fake_records

        with patch("pipelines.export.export_pmtiles.services") as mock_services:
            mock_services.db_helper.return_value = mock_db

            path = export_zones_geojson_task(
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
        assert de["properties"]["noco_id"] == 1
        assert de["geometry"]["type"] == "Polygon"

        fr = collection["features"][1]
        assert fr["properties"]["code"] == "FR"
        assert fr["properties"]["vcm_level"] is None
        assert fr["properties"]["noco_id"] == 2

    def test_distribution_zone_produces_valid_feature_collection(self, tmp_path):
        """DistributionZone table exports with company name from ActorName."""
        fake_df = [{
            "Id": 42,
            "Code": "DZ001",
            "Name": "Water Zone Alpha",
            "Geometry": '{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}',
            "PVC Level": "Medium",
            "VCM Level": "Low",
            "ActorName": ["Water Company Alpha"],
        }]

        mock_db = Mock()
        mock_db.load_all_records.return_value = fake_df

        with patch("pipelines.export.export_pmtiles.services") as mock_services:
            mock_services.db_helper.return_value = mock_db

            path = export_zones_geojson_task(
                table_name="DistributionZone", output_dir=tmp_path
            )

        assert path == tmp_path / "DistributionZone_tile_data.geojson"

        collection = json.loads(path.read_text())
        assert collection["type"] == "FeatureCollection"
        assert len(collection["features"]) == 1

        zone = collection["features"][0]
        assert zone["properties"]["code"] == "DZ001"
        assert zone["properties"]["name"] == "Water Zone Alpha"
        assert zone["properties"]["company_name"] == "Water Company Alpha"
        assert zone["properties"]["noco_id"] == 42
        assert zone["geometry"]["type"] == "Polygon"

    def test_empty_table_produces_empty_collection(self, tmp_path):
        mock_db = Mock()
        mock_db.load_all_records.return_value = []

        with patch("pipelines.export.export_pmtiles.services") as mock_services:
            mock_services.db_helper.return_value = mock_db

            path = export_zones_geojson_task(
                table_name="Country", output_dir=tmp_path
            )

        collection = json.loads(path.read_text())
        assert collection["features"] == []  # empty list — Id field irrelevant here


def _sample_geojson() -> dict:
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
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "output"

        result = create_pmtiles_task(
            geojson_file=geojson_file, layer="data_countries", output_dir=output_dir,
        )

        assert result == output_dir / "data_countries.pmtiles"
        assert result.exists()
        assert result.stat().st_size > 0

    def test_creates_output_dir_if_missing(self, tmp_path):
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "nested" / "deep" / "output"

        result = create_pmtiles_task(
            geojson_file=geojson_file, layer="test_layer", output_dir=output_dir,
        )

        assert output_dir.is_dir()
        assert result.exists()

    def test_overwrites_existing_file(self, tmp_path):
        geojson_file = tmp_path / "input.geojson"
        geojson_file.write_text(json.dumps(_sample_geojson()))
        output_dir = tmp_path / "output"

        create_pmtiles_task(
            geojson_file=geojson_file, layer="data_countries", output_dir=output_dir
        )
        result = create_pmtiles_task(
            geojson_file=geojson_file, layer="data_countries", output_dir=output_dir
        )

        assert result.exists()

    def test_raises_on_invalid_input(self, tmp_path):
        bad_file = tmp_path / "bad.geojson"
        bad_file.write_text("not valid json at all")
        output_dir = tmp_path / "output"

        with pytest.raises(subprocess.CalledProcessError):
            create_pmtiles_task(
                geojson_file=bad_file, layer="bad_layer", output_dir=output_dir
            )
