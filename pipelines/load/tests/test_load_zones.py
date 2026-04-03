"""Tests for load_zones deduplication logic."""
import duckdb
from pipelines.load.load_zones import load_source_data


def _setup_staging(conn, table_name: str, records: list[dict]):
    """Helper to create a staging table from records."""
    import pandas as pd
    df = pd.DataFrame(records)  # noqa: F841 - used by DuckDB SQL
    conn.execute(f'CREATE OR REPLACE TABLE staging."{table_name}" AS SELECT * FROM df')


class TestLoadSourceDataDedup:

    def setup_method(self):
        self.conn = duckdb.connect()
        self.conn.execute("ATTACH ':memory:' AS staging")

    def teardown_method(self):
        self.conn.close()

    def test_deduplicates_by_code_within_single_table(self):
        _setup_staging(self.conn, "DistributionZone_import", [
            {"Code": "CompanyA", "Name": "CompanyA", "CountryCode": "SE", "Municipalities": ["SE001"]},
            {"Code": "CompanyA", "Name": "CompanyA", "CountryCode": "SE", "Municipalities": ["SE001"]},
            {"Code": "CompanyB", "Name": "CompanyB", "CountryCode": "SE", "Municipalities": ["SE002"]},
        ])
        result = load_source_data(self.conn, "DistributionZone")
        codes = [r["Code"] for r in result]
        assert sorted(codes) == ["CompanyA", "CompanyB"]

    def test_deduplicates_across_tables(self):
        _setup_staging(self.conn, "DistributionZone_import", [
            {"Code": "CompanyA", "Name": "CompanyA", "CountryCode": "SE"},
        ])
        _setup_staging(self.conn, "DistributionZone_other", [
            {"Code": "CompanyA", "Name": "CompanyA", "CountryCode": "SE", "Geometry": '{"type":"Point"}'},
        ])
        result = load_source_data(self.conn, "DistributionZone")
        assert len(result) == 1
        # Should prefer the row with more data (Geometry)
        assert result[0].get("Geometry") == '{"type":"Point"}'

    def test_no_duplicates_passes_through(self):
        _setup_staging(self.conn, "DistributionZone_a", [
            {"Code": "A", "Name": "A", "CountryCode": "SE"},
        ])
        _setup_staging(self.conn, "DistributionZone_b", [
            {"Code": "B", "Name": "B", "CountryCode": "NL"},
        ])
        result = load_source_data(self.conn, "DistributionZone")
        assert len(result) == 2

    def test_empty_tables_returns_empty(self):
        result = load_source_data(self.conn, "DistributionZone")
        assert result == []
