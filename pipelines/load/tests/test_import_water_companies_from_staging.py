"""Unit and integration tests for import_water_companies_from_staging."""

import polars as pl
from unittest.mock import Mock, patch

from pipelines.load.import_water_companies_from_staging import (
    _parse_municipalities,
    _validate_country,
    _validate_municipalities,
    _check_duplicates,
    validate_and_split_rows_task,
    write_ndjson_and_load_task,
)


class TestParseMunicipalities:
    """Tests for _parse_municipalities."""

    def test_empty_string_returns_empty_list(self):
        assert _parse_municipalities("") == []
        assert _parse_municipalities("   ") == []
        assert _parse_municipalities(None) == []

    def test_single_municipality(self):
        assert _parse_municipalities("Berlin") == ["Berlin"]
        assert _parse_municipalities("  Kiel  ") == ["Kiel"]

    def test_comma_separated_trimmed(self):
        assert _parse_municipalities("Berlin, Kiel, Hamburg") == [
            "Berlin",
            "Kiel",
            "Hamburg",
        ]
        assert _parse_municipalities(" Berlin ,  Kiel , Hamburg ") == [
            "Berlin",
            "Kiel",
            "Hamburg",
        ]

    def test_empty_parts_skipped(self):
        assert _parse_municipalities("Berlin,,Kiel,") == ["Berlin", "Kiel"]


def _make_ref(
    country: pl.DataFrame | None = None,
    municipality: pl.DataFrame | None = None,
    distribution_zone: pl.DataFrame | None = None,
    actor: pl.DataFrame | None = None,
) -> dict[str, pl.DataFrame]:
    """Build minimal ref dict for validation tests."""
    return {
        "Country": country if country is not None else pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
        "Municipality": municipality if municipality is not None else pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
        "DistributionZone": distribution_zone if distribution_zone is not None else pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
        "Actor": actor if actor is not None else pl.DataFrame(schema={"Name": pl.Utf8}),
    }


class TestValidateCountry:
    """Tests for _validate_country."""

    def test_empty_country_returns_error(self):
        ref = _make_ref()
        code, err = _validate_country(ref, None)
        assert code is None
        assert err == "Country is required"

        code, err = _validate_country(ref, "")
        assert code is None
        assert err == "Country is required"

        code, err = _validate_country(ref, "   ")
        assert code is None
        assert err == "Country is required"

    def test_country_not_found(self):
        ref = _make_ref(country=pl.DataFrame({"Code": ["DE", "FR"], "Name": ["Germany", "France"]}))
        code, err = _validate_country(ref, "Spain")
        assert code is None
        assert err == "Country 'Spain' not found"

    def test_country_found_by_name_case_insensitive(self):
        ref = _make_ref(country=pl.DataFrame({"Code": ["DE", "FR"], "Name": ["Germany", "France"]}))
        code, err = _validate_country(ref, "Germany")
        assert code == "DE"
        assert err is None

        code, err = _validate_country(ref, "germany")
        assert code == "DE"
        assert err is None


class TestValidateMunicipalities:
    """Tests for _validate_municipalities."""

    def test_empty_municipalities_returns_error(self):
        ref = _make_ref()
        codes, err = _validate_municipalities(ref, None, "DE")
        assert codes == []
        assert err == "Municipalities is required"

        codes, err = _validate_municipalities(ref, "", "DE")
        assert codes == []
        assert err == "Municipalities is required"

    def test_municipality_not_found(self):
        ref = _make_ref(municipality=pl.DataFrame({"Code": ["DE001", "DE002"], "Name": ["Berlin", "Kiel"]}))
        codes, err = _validate_municipalities(ref, "Hamburg", "DE")
        assert codes == []
        assert err == "Municipality 'Hamburg' not found"

    def test_match_by_name(self):
        ref = _make_ref(municipality=pl.DataFrame({"Code": ["DE001", "DE002"], "Name": ["Berlin", "Kiel"]}))
        codes, err = _validate_municipalities(ref, "Berlin, Kiel", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_match_by_code(self):
        ref = _make_ref(municipality=pl.DataFrame({"Code": ["DE001", "DE002"], "Name": ["Berlin", "Kiel"]}))
        codes, err = _validate_municipalities(ref, "DE001, DE002", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_mixed_name_and_code(self):
        ref = _make_ref(municipality=pl.DataFrame({"Code": ["DE001", "DE002"], "Name": ["Berlin", "Kiel"]}))
        codes, err = _validate_municipalities(ref, "Berlin, DE002", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_empty_database_returns_error(self):
        ref = _make_ref(municipality=pl.DataFrame())
        codes, err = _validate_municipalities(ref, "Berlin", "DE")
        assert codes == []
        assert err == "No municipalities in database"


class TestCheckDuplicates:
    """Tests for _check_duplicates."""

    def test_empty_company_name(self):
        ref = _make_ref()
        is_dup, err = _check_duplicates(ref, None, "DE")
        assert is_dup is True
        assert err == "Company Name is required"

        is_dup, err = _check_duplicates(ref, "", "DE")
        assert is_dup is True
        assert err == "Company Name is required"

    def test_duplicate_distribution_zone_by_code(self):
        ref = _make_ref(
            distribution_zone=pl.DataFrame({"Code": ["Stadtwerke Kiel"], "Name": ["Stadtwerke Kiel AG"]}),
        )
        is_dup, err = _check_duplicates(ref, "Stadtwerke Kiel", "DE")
        assert is_dup is True
        assert "Distribution zone" in err
        assert "already exists" in err

    def test_duplicate_distribution_zone_by_name(self):
        ref = _make_ref(
            distribution_zone=pl.DataFrame({"Code": ["SWK"], "Name": ["Stadtwerke Kiel AG"]}),
        )
        is_dup, err = _check_duplicates(ref, "Stadtwerke Kiel AG", "DE")
        assert is_dup is True
        assert "Distribution zone" in err

    def test_duplicate_actor(self):
        ref = _make_ref(actor=pl.DataFrame({"Name": ["Stadtwerke Kiel AG"]}))
        is_dup, err = _check_duplicates(ref, "Stadtwerke Kiel AG", "DE")
        assert is_dup is True
        assert "Water company" in err
        assert "already exists" in err

    def test_no_duplicate(self):
        ref = _make_ref()
        is_dup, err = _check_duplicates(ref, "New Water Co", "DE")
        assert is_dup is False
        assert err is None


class TestValidateAndSplitRows:
    """Tests for validate_and_split_rows_task."""

    def test_empty_input_returns_empty_dfs(self):
        db = Mock()
        valid, failed = validate_and_split_rows_task(pl.DataFrame(), db)
        assert valid.is_empty()
        assert failed.is_empty() or failed.columns == ["Id", "ImportError", "ImportStatus"]

    def test_country_validation_failure(self):
        db = Mock()
        db.load_all_records.side_effect = [
            pl.DataFrame({"Code": ["DE"], "Name": ["Germany"]}),
            pl.DataFrame({"Code": ["DE001"], "Name": ["Berlin"]}),
            pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
            pl.DataFrame(schema={"Name": pl.Utf8}),
        ]
        df = pl.DataFrame({
            "Id": [1],
            "Company Name": ["Test Co"],
            "Country": ["Spain"],
            "Municipalities": ["Berlin"],
        })
        valid, failed = validate_and_split_rows_task(df, db)
        assert valid.is_empty()
        assert len(failed) == 1
        assert failed["ImportError"][0] == "Country 'Spain' not found"
        assert failed["ImportStatus"][0] == "Failed"

    def test_municipality_validation_failure(self):
        db = Mock()
        db.load_all_records.side_effect = [
            pl.DataFrame({"Code": ["DE"], "Name": ["Germany"]}),
            pl.DataFrame({"Code": ["DE001"], "Name": ["Berlin"]}),
            pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
            pl.DataFrame(schema={"Name": pl.Utf8}),
        ]
        df = pl.DataFrame({
            "Id": [1],
            "Company Name": ["Test Co"],
            "Country": ["Germany"],
            "Municipalities": ["UnknownCity"],
        })
        valid, failed = validate_and_split_rows_task(df, db)
        assert valid.is_empty()
        assert len(failed) == 1
        assert "Municipality 'UnknownCity' not found" in failed["ImportError"][0]

    def test_valid_row_passes(self):
        db = Mock()
        db.load_all_records.side_effect = [
            pl.DataFrame({"Code": ["DE"], "Name": ["Germany"]}),
            pl.DataFrame({"Code": ["DE001"], "Name": ["Berlin"]}),
            pl.DataFrame(schema={"Code": pl.Utf8, "Name": pl.Utf8}),
            pl.DataFrame(schema={"Name": pl.Utf8}),
        ]
        df = pl.DataFrame({
            "Id": [1],
            "Company Name": ["Test Co"],
            "Country": ["Germany"],
            "Municipalities": ["Berlin"],
        })
        valid, failed = validate_and_split_rows_task(df, db)
        assert len(valid) == 1
        assert valid["Id"][0] == 1
        assert valid["Company Name"][0] == "Test Co"
        assert valid["CountryCode"][0] == "DE"
        assert valid["Municipalities"].to_list()[0] == ["DE001"]
        assert failed.is_empty()


class TestNdjsonOutputFormat:
    """Tests for NDJSON output structure."""

    def test_distribution_zone_and_water_company_format(self, tmp_path):
        """Verify the structure of written NDJSON matches load_zones and load_water_companies expectations."""
        valid_df = pl.DataFrame({
            "Id": [42],
            "Company Name": ["Stadtwerke Kiel AG"],
            "CountryCode": ["DE"],
            "Municipalities": [["DE001", "DE002"]],
            "Email": ["info@example.com"],
            "Phone": ["+49 123"],
            "Website": ["https://example.com"],
        })
        with patch(
            "pipelines.load.import_water_companies_from_staging.load_zones_flow"
        ) as mock_load_zones, patch(
            "pipelines.load.import_water_companies_from_staging.load_water_companies"
        ) as mock_load_companies:
            write_ndjson_and_load_task(valid_df, tmp_path)

        dist_path = tmp_path / "staging" / "DistributionZone_import.ndjson"
        wc_path = tmp_path / "staging" / "WaterCompany_import.ndjson"
        assert dist_path.exists()
        assert wc_path.exists()

        dist_df = pl.read_ndjson(dist_path)
        assert dist_df.columns == ["Code", "Name", "CountryCode", "Municipalities"]
        assert dist_df["Code"][0] == "Stadtwerke Kiel AG"
        assert dist_df["Name"][0] == "Stadtwerke Kiel AG"
        assert dist_df["CountryCode"][0] == "DE"
        assert dist_df["Municipalities"].to_list()[0] == ["DE001", "DE002"]

        wc_df = pl.read_ndjson(wc_path)
        assert "CountryCode" in wc_df.columns
        assert "Name" in wc_df.columns
        assert "Email" in wc_df.columns
        assert "Phone" in wc_df.columns
        assert "Website" in wc_df.columns
        assert "Description" in wc_df.columns
        assert "Source" in wc_df.columns
        assert wc_df["Source"][0] == "NocoDB Import (42)"

        mock_load_zones.assert_called_once_with(
            level="DistributionZone",
            data_directory=tmp_path / "staging",
        )
        mock_load_companies.assert_called_once_with(data_path=tmp_path / "staging")

    def test_empty_valid_df_skips_write_and_load(self, tmp_path):
        with patch(
            "pipelines.load.import_water_companies_from_staging.load_zones_flow"
        ) as mock_load_zones, patch(
            "pipelines.load.import_water_companies_from_staging.load_water_companies"
        ) as mock_load_companies:
            write_ndjson_and_load_task(pl.DataFrame(), tmp_path)

        mock_load_zones.assert_not_called()
        mock_load_companies.assert_not_called()
