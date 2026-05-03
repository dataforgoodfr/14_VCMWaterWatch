"""Tests for pipelines/load/load_analyses.py"""

import datetime
from unittest.mock import MagicMock

import duckdb

from pipelines.load.load_analyses import (
    load_staging_analyses,
    prepare_records,
    insert_analyses,
    update_analyses,
    _make_description,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(*tables: tuple[str, list[dict]]) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with a staging schema seeded with the given tables.

    Uses DuckDB parameterized INSERT so Python native types (e.g. datetime.date)
    are stored with matching DuckDB types (DATE, not TIMESTAMP).
    """
    conn = duckdb.connect()
    conn.execute("ATTACH ':memory:' AS staging")
    for table_name, records in tables:
        if not records:
            continue
        cols = list(records[0].keys())
        col_defs = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join("?" * len(cols))
        # Create table using the first row so DuckDB infers types from Python values
        first_vals = [records[0][c] for c in cols]
        conn.execute(
            f'CREATE TABLE staging."{table_name}" AS '
            f'SELECT {col_defs} FROM (VALUES ({placeholders})) AS t({col_defs})',
            first_vals,
        )
        for r in records[1:]:
            conn.execute(
                f'INSERT INTO staging."{table_name}" ({col_defs}) VALUES ({placeholders})',
                [r[c] for c in cols],
            )
    return conn


SAMPLE_ROWS = [
    {
        "DistributionZoneCode": "UDI001",
        "MunicipalityCode": "29001",
        "Date": datetime.date(2023, 5, 10),
        "CVMMeasure": 0.25,
        "Source": "dansmoneau",
        "SourceRef": "REF001",
    },
    {
        "DistributionZoneCode": "UDI002",
        "MunicipalityCode": "29003",
        "Date": datetime.date(2024, 3, 1),
        "CVMMeasure": 0.60,
        "Source": "dansmoneau",
        "SourceRef": "REF004",
    },
    # Zone not in NocoDB → should be skipped
    {
        "DistributionZoneCode": "UDI_UNKNOWN",
        "MunicipalityCode": "99999",
        "Date": datetime.date(2024, 1, 1),
        "CVMMeasure": 0.10,
        "Source": "dansmoneau",
        "SourceRef": "REF999",
    },
]


# ---------------------------------------------------------------------------
# load_staging_analyses
# ---------------------------------------------------------------------------

class TestLoadStagingAnalyses:
    def test_returns_all_rows(self):
        conn = _make_conn(("Analysis_fr", SAMPLE_ROWS[:2]))
        result = load_staging_analyses(conn)
        assert len(result) == 2

    def test_empty_when_no_tables(self):
        conn = duckdb.connect()
        conn.execute("ATTACH ':memory:' AS staging")
        result = load_staging_analyses(conn)
        assert result == []

    def test_unions_multiple_tables(self):
        conn = _make_conn(
            ("Analysis_fr", SAMPLE_ROWS[:1]),
            ("Analysis_other", SAMPLE_ROWS[1:2]),
        )
        result = load_staging_analyses(conn)
        assert len(result) == 2

    def test_handles_missing_columns_in_some_tables(self):
        """Tables with different schemas are unioned with NULLs for missing cols."""
        rows_a = [{"DistributionZoneCode": "Z1", "Date": datetime.date(2023, 1, 1)}]
        rows_b = [{"DistributionZoneCode": "Z2", "CVMMeasure": 0.5}]
        conn = _make_conn(("Analysis_a", rows_a), ("Analysis_b", rows_b))
        result = load_staging_analyses(conn)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# prepare_records
# ---------------------------------------------------------------------------

class TestPrepareRecords:
    def setup_method(self):
        self.zone_map = {"UDI001": "z1", "UDI002": "z2"}
        self.muni_map = {"29001": "m1", "29003": "m2"}
        self.existing_map = {}

    def test_all_inserted_when_no_existing(self):
        to_insert, to_update, skipped = prepare_records(
            SAMPLE_ROWS, self.zone_map, self.muni_map, self.existing_map
        )
        assert len(to_insert) == 2
        assert len(to_update) == 0
        assert skipped == 1

    def test_skipped_when_zone_not_in_map(self):
        _, _, skipped = prepare_records(
            SAMPLE_ROWS, {}, self.muni_map, self.existing_map
        )
        assert skipped == 3  # all skipped

    def test_update_when_description_exists(self):
        desc = _make_description(SAMPLE_ROWS[0])
        existing = {desc: "existing-id-123"}
        to_insert, to_update, _ = prepare_records(
            SAMPLE_ROWS[:2], self.zone_map, self.muni_map, existing
        )
        assert len(to_insert) == 1
        assert len(to_update) == 1
        assert to_update[0]["Id"] == "existing-id-123"

    def test_dedup_within_batch(self):
        """Duplicate rows within the same batch are deduplicated."""
        duped = SAMPLE_ROWS[:1] * 3  # same row 3×
        to_insert, _, _ = prepare_records(duped, self.zone_map, self.muni_map, {})
        assert len(to_insert) == 1

    def test_zone_id_attached(self):
        to_insert, _, _ = prepare_records(
            SAMPLE_ROWS[:1], self.zone_map, self.muni_map, {}
        )
        assert to_insert[0]["_zone_id"] == "z1"

    def test_muni_id_none_when_not_in_map(self):
        to_insert, _, _ = prepare_records(
            SAMPLE_ROWS[:1], self.zone_map, {}, {}
        )
        assert to_insert[0]["_muni_id"] is None


# ---------------------------------------------------------------------------
# insert_analyses (mocked db_helper)
# ---------------------------------------------------------------------------

class TestInsertAnalyses:
    def _make_db_helper(self, return_ids: list[str]) -> MagicMock:
        db = MagicMock()
        db.insert_records.side_effect = lambda records, **kwargs: [
            {**r, "Id": return_ids[i]} for i, r in enumerate(records)
        ]
        return db

    def test_ids_attached_to_records(self):
        records = [
            {"Description": "d1", "CVMMeasure": 0.1, "_zone_id": "z1", "_muni_id": None},
            {"Description": "d2", "CVMMeasure": 0.2, "_zone_id": "z2", "_muni_id": "m1"},
        ]
        db = self._make_db_helper(["id-1", "id-2"])
        result = insert_analyses(records, db)
        assert result[0]["Id"] == "id-1"
        assert result[1]["Id"] == "id-2"

    def test_internal_keys_stripped_before_insert(self):
        records = [{"Description": "d1", "_zone_id": "z1", "_muni_id": None}]
        db = self._make_db_helper(["id-1"])
        insert_analyses(records, db)
        call_args = db.insert_records.call_args[0][0]
        for r in call_args:
            assert "_zone_id" not in r
            assert "_muni_id" not in r

    def test_empty_returns_empty(self):
        db = MagicMock()
        result = insert_analyses([], db)
        assert result == []
        db.insert_records.assert_not_called()


# ---------------------------------------------------------------------------
# update_analyses (mocked db_helper)
# ---------------------------------------------------------------------------

class TestUpdateAnalyses:
    def test_calls_update_records(self):
        db = MagicMock()
        records = [{"Id": "id-1", "Description": "d1", "_zone_id": "z1"}]
        update_analyses(records, db)
        db.update_records.assert_called_once()

    def test_empty_does_not_call(self):
        db = MagicMock()
        update_analyses([], db)
        db.update_records.assert_not_called()

    def test_internal_keys_stripped(self):
        db = MagicMock()
        records = [{"Id": "id-1", "Description": "d1", "_zone_id": "z1"}]
        update_analyses(records, db)
        call_args = db.update_records.call_args[0][0]
        for r in call_args:
            assert "_zone_id" not in r


# ---------------------------------------------------------------------------
# Regression tests: no NaT / None strings leak through
# ---------------------------------------------------------------------------

class TestPrepareRecordsDateHandling:
    """Ensure NaT / None strings never appear in output records."""

    def setup_method(self):
        self.zone_map = {"UDI001": "z1"}
        self.muni_map = {}
        self.existing_map = {}

    def test_datetime_date_serialised_to_isoformat(self):
        rows = [{
            "DistributionZoneCode": "UDI001",
            "MunicipalityCode": None,
            "Date": datetime.date(2022, 6, 8),
            "CVMMeasure": 0.25,
            "Source": "outline",
            "SourceRef": "REF1",
        }]
        to_insert, _, _ = prepare_records(rows, self.zone_map, self.muni_map, self.existing_map)
        assert len(to_insert) == 1
        assert to_insert[0]["Date"] == "2022-06-08"

    def test_none_date_stays_none(self):
        rows = [{
            "DistributionZoneCode": "UDI001",
            "MunicipalityCode": None,
            "Date": None,
            "CVMMeasure": 0.25,
            "Source": "outline",
            "SourceRef": "REF2",
        }]
        to_insert, _, _ = prepare_records(rows, self.zone_map, self.muni_map, self.existing_map)
        assert len(to_insert) == 1
        assert to_insert[0]["Date"] is None

    def test_no_nat_string_in_output(self):
        """'NaT' must never appear as a string value in any record field."""
        rows = [{
            "DistributionZoneCode": "UDI001",
            "MunicipalityCode": None,
            "Date": None,
            "CVMMeasure": 0.5,
            "Source": "outline",
            "SourceRef": "REF3",
        }]
        to_insert, _, _ = prepare_records(rows, self.zone_map, self.muni_map, self.existing_map)
        for record in to_insert:
            for key, val in record.items():
                assert val != "NaT", f"Field {key!r} contains literal 'NaT'"
                assert val != "None", f"Field {key!r} contains literal 'None'"


class TestLoadStagingAnalysesNativeTypes:
    """load_staging_analyses must return native Python types, not pandas Timestamps."""

    def test_date_is_python_date_not_timestamp(self):
        """DuckDB native fetch → datetime.date, not pandas.Timestamp or NaT."""
        import datetime as dt
        rows_data = [{
            "DistributionZoneCode": "UDI001",
            "Date": dt.date(2023, 5, 10),
            "CVMMeasure": 0.25,
        }]
        conn = _make_conn(("Analysis_fr", rows_data))
        result = load_staging_analyses(conn)
        assert len(result) == 1
        date_val = result[0]["Date"]
        # Must be exactly datetime.date, not a datetime.datetime subclass or pandas Timestamp
        assert type(date_val) is dt.date, f"Expected datetime.date, got {type(date_val)}: {date_val!r}"
        assert str(date_val) != "NaT", "Date must not be NaT"
