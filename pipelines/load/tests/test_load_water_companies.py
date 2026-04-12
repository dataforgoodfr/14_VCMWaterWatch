"""Tests for load_water_companies deduplication and column normalization."""
import duckdb
import pandas as pd

from pipelines.load.load_water_companies import load_water_companies_task


def _setup_staging(conn, table_name: str, records: list[dict]):
    df = pd.DataFrame(records)  # noqa: F841 - used by DuckDB SQL
    conn.execute(f'CREATE OR REPLACE TABLE staging."{table_name}" AS SELECT * FROM df')


class TestLoadWaterCompaniesTask:

    def setup_method(self):
        self.conn = duckdb.connect()
        self.conn.execute("ATTACH ':memory:' AS staging")

    def teardown_method(self):
        self.conn.close()

    def test_deduplicates_by_name(self):
        _setup_staging(self.conn, "WaterCompany_import", [
            {"Name": "CompanyA", "CountryCode": "SE", "Email": "a@b.com"},
            {"Name": "CompanyA", "CountryCode": "SE", "Email": "a@b.com"},
            {"Name": "CompanyB", "CountryCode": "SE", "Email": "b@b.com"},
        ])
        result = load_water_companies_task(self.conn)
        names = [r["Name"] for r in result]
        assert sorted(names) == ["CompanyA", "CompanyB"]

    def test_union_different_columns(self):
        _setup_staging(self.conn, "WaterCompany_import", [
            {"Name": "CompanyA", "CountryCode": "SE"},
        ])
        _setup_staging(self.conn, "WaterCompany_other", [
            {"Name": "CompanyB", "CountryCode": "NL", "Website": "http://b.com"},
        ])
        result = load_water_companies_task(self.conn)
        names = sorted(r["Name"] for r in result)
        assert names == ["CompanyA", "CompanyB"]

    def test_empty_returns_empty(self):
        result = load_water_companies_task(self.conn)
        assert result == []
