"""Tests for pipelines/tasks/deduce_vcm_level.py"""

from unittest.mock import MagicMock

import duckdb
import pandas as pd

from pipelines.tasks.deduce_vcm_level import (
    compute_vcm_levels,
    apply_vcm_levels,
    update_vcm_levels,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(rows: list[dict]) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect()
    conn.execute("ATTACH ':memory:' AS staging")
    if rows:
        _df = pd.DataFrame(rows)
        conn.execute('CREATE OR REPLACE TABLE staging."Analysis_fr" AS SELECT * FROM _df')
    return conn


_ANALYSIS_ROWS = [
    # UDI001: has a high reading
    {"DistributionZoneCode": "UDI001", "CVMMeasure": 0.25},
    {"DistributionZoneCode": "UDI001", "CVMMeasure": 0.80},
    # UDI002: all low readings
    {"DistributionZoneCode": "UDI002", "CVMMeasure": 0.10},
    {"DistributionZoneCode": "UDI002", "CVMMeasure": 0.30},
    # UDI003: exactly at threshold — NOT above, so Low
    {"DistributionZoneCode": "UDI003", "CVMMeasure": 0.50},
]


# ---------------------------------------------------------------------------
# compute_vcm_levels
# ---------------------------------------------------------------------------

class TestComputeVcmLevels:
    def test_high_when_any_exceeds_threshold(self):
        conn = _make_conn(_ANALYSIS_ROWS)
        result = compute_vcm_levels(conn)
        assert result["UDI001"] == "High"

    def test_low_when_all_below_threshold(self):
        conn = _make_conn(_ANALYSIS_ROWS)
        result = compute_vcm_levels(conn)
        assert result["UDI002"] == "Low"

    def test_low_when_exactly_at_threshold(self):
        """0.5 is NOT > 0.5, so level is Low."""
        conn = _make_conn(_ANALYSIS_ROWS)
        result = compute_vcm_levels(conn)
        assert result["UDI003"] == "Low"

    def test_unknown_zone_not_in_staging(self):
        """Zones absent from staging are not in the map (handled by apply step)."""
        conn = _make_conn(_ANALYSIS_ROWS)
        result = compute_vcm_levels(conn)
        assert "UDI_ABSENT" not in result

    def test_empty_table_returns_empty(self):
        conn = _make_conn([])
        result = compute_vcm_levels(conn)
        assert result == {}

    def test_no_table_returns_empty(self):
        conn = duckdb.connect()
        conn.execute("ATTACH ':memory:' AS staging")
        result = compute_vcm_levels(conn)
        assert result == {}

    def test_three_zone_fixture_counts(self):
        conn = _make_conn(_ANALYSIS_ROWS)
        result = compute_vcm_levels(conn)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# apply_vcm_levels
# ---------------------------------------------------------------------------

class TestApplyVcmLevels:
    def _zones(self):
        return [
            {"Id": "id-1", "Code": "UDI001", "VCM Level": "Unknown"},
            {"Id": "id-2", "Code": "UDI002", "VCM Level": "< 0.5 μg/L"},
            {"Id": "id-3", "Code": "UDI003", "VCM Level": None},
            # Zone not in level_map → should become 'Unknown'
            {"Id": "id-4", "Code": "UDI_ABSENT", "VCM Level": "> 0.5 μg/L"},
        ]

    def _level_map(self):
        return {"UDI001": "High", "UDI002": "Low", "UDI003": "Low"}

    def test_high_zone_updated(self):
        updates = apply_vcm_levels(self._zones(), self._level_map())
        udi001 = next(u for u in updates if u["Id"] == "id-1")
        assert udi001["VCM Level"] == "> 0.5 μg/L"

    def test_unchanged_zone_not_in_updates(self):
        """UDI002 already has Low → should not appear in updates."""
        updates = apply_vcm_levels(self._zones(), self._level_map())
        ids_updated = {u["Id"] for u in updates}
        assert "id-2" not in ids_updated

    def test_absent_zone_gets_unknown(self):
        updates = apply_vcm_levels(self._zones(), self._level_map())
        udi_absent = next(u for u in updates if u["Id"] == "id-4")
        assert udi_absent["VCM Level"] == "Unknown"

    def test_none_current_level_triggers_update(self):
        updates = apply_vcm_levels(self._zones(), self._level_map())
        ids_updated = {u["Id"] for u in updates}
        assert "id-3" in ids_updated

    def test_empty_zones_returns_empty(self):
        assert apply_vcm_levels([], {"UDI001": "High"}) == []

    def test_empty_level_map_all_unknown(self):
        zones = [{"Id": "id-1", "Code": "UDI001", "VCM Level": "High"}]
        updates = apply_vcm_levels(zones, {})
        assert updates[0]["VCM Level"] == "Unknown"


# ---------------------------------------------------------------------------
# update_vcm_levels (mocked db_helper)
# ---------------------------------------------------------------------------

class TestUpdateVcmLevels:
    def test_calls_update_records(self):
        db = MagicMock()
        updates = [{"Id": "id-1", "VCM Level": "High"}]
        update_vcm_levels(updates, db)
        db.update_records.assert_called_once()
        args = db.update_records.call_args
        assert args[1]["table_name"] == "DistributionZone"

    def test_empty_does_not_call(self):
        db = MagicMock()
        update_vcm_levels([], db)
        db.update_records.assert_not_called()
