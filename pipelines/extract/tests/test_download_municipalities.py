"""Tests for PT municipality dissolve in download_municipalities."""
import json
import tempfile
from pathlib import Path

from pipelines.extract.download_municipalities import dissolve_pt_concelhos


def _make_parish_geojson(path: Path):
    """Create a tiny GeoJSON with 3 parishes in 2 municipalities."""
    features = [
        {
            "type": "Feature",
            "properties": {
                "COMM_ID": "PT10105A",
                "CNTR_CODE": "PT",
                "COMM_NAME": "Parish A",
                "NSI_CODE": "010501",
                "NUTS_CODE": "PT191",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
        },
        {
            "type": "Feature",
            "properties": {
                "COMM_ID": "PT10105B",
                "CNTR_CODE": "PT",
                "COMM_NAME": "Parish B",
                "NSI_CODE": "010502",
                "NUTS_CODE": "PT191",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]],
            },
        },
        {
            "type": "Feature",
            "properties": {
                "COMM_ID": "PT10106A",
                "CNTR_CODE": "PT",
                "COMM_NAME": "Parish C",
                "NSI_CODE": "010601",
                "NUTS_CODE": "PT16D",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]],
            },
        },
    ]
    geojson = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(geojson))


def _make_concelhos_csv(path: Path):
    """Create a concelhos CSV with 2 municipalities."""
    path.write_text(
        "cod_distrito,cod_concelho,nome_concelho\n"
        "01,05,Aveiro\n"
        "01,06,Castelo de Paiva\n"
    )


def test_dissolve_pt_concelhos():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        geojson_path = tmp / "municipalities.geojson"
        concelhos_path = tmp / "concelhos.csv"
        output_path = tmp / "pt_concelhos_municipalities.geojson"

        _make_parish_geojson(geojson_path)
        _make_concelhos_csv(concelhos_path)

        dissolve_pt_concelhos(geojson_path, concelhos_path, output_path)

        with open(output_path) as f:
            result = json.load(f)

        features = result["features"]
        assert len(features) == 2

        by_name = {f["properties"]["COMM_NAME"]: f for f in features}
        assert "Aveiro" in by_name
        assert "Castelo de Paiva" in by_name

        aveiro = by_name["Aveiro"]
        assert aveiro["properties"]["CNTR_CODE"] == "PT"
        assert aveiro["properties"]["COMM_ID"] == "PT_CONC_0105"
        assert aveiro["geometry"]["type"] in ("Polygon", "MultiPolygon")
