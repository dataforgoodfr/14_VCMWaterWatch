"""Unit and integration tests for import_water_companies_from_staging."""

from unittest.mock import Mock, patch

from pipelines.load.import_water_companies_from_staging import (
    _parse_municipalities,
    _validate_country,
    _validate_municipalities,
    _check_duplicates,
    validate_and_split_rows_task,
    write_staging_and_load_task,
)


class TestParseMunicipalities:

    def test_empty_string_returns_empty_list(self):
        assert _parse_municipalities("") == []
        assert _parse_municipalities("   ") == []
        assert _parse_municipalities(None) == []

    def test_single_municipality(self):
        assert _parse_municipalities("Berlin") == ["Berlin"]
        assert _parse_municipalities("  Kiel  ") == ["Kiel"]

    def test_comma_separated_trimmed(self):
        assert _parse_municipalities("Berlin, Kiel, Hamburg") == [
            "Berlin", "Kiel", "Hamburg",
        ]
        assert _parse_municipalities(" Berlin ,  Kiel , Hamburg ") == [
            "Berlin", "Kiel", "Hamburg",
        ]

    def test_empty_parts_skipped(self):
        assert _parse_municipalities("Berlin,,Kiel,") == ["Berlin", "Kiel"]


def _make_ref(
    country=None, municipality=None, distribution_zone=None, actor=None,
) -> dict[str, list[dict]]:
    """Build minimal ref dict for validation tests."""
    return {
        "Country": country if country is not None else [],
        "Municipality": municipality if municipality is not None else [],
        "DistributionZone": distribution_zone if distribution_zone is not None else [],
        "Actor": actor if actor is not None else [],
    }


class TestValidateCountry:

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
        ref = _make_ref(country=[{"Code": "DE", "Name": "Germany"}, {"Code": "FR", "Name": "France"}])
        code, err = _validate_country(ref, "Spain")
        assert code is None
        assert err == "Country 'Spain' not found"

    def test_country_found_by_name_case_insensitive(self):
        ref = _make_ref(country=[{"Code": "DE", "Name": "Germany"}, {"Code": "FR", "Name": "France"}])
        code, err = _validate_country(ref, "Germany")
        assert code == "DE"
        assert err is None

        code, err = _validate_country(ref, "germany")
        assert code == "DE"
        assert err is None


class TestValidateMunicipalities:

    def test_empty_municipalities_returns_error(self):
        ref = _make_ref()
        codes, err = _validate_municipalities(ref, None, "DE")
        assert codes == []
        assert err == "Municipalities is required"

        codes, err = _validate_municipalities(ref, "", "DE")
        assert codes == []
        assert err == "Municipalities is required"

    def test_municipality_not_found(self):
        ref = _make_ref(municipality=[{"Code": "DE001", "Name": "Berlin"}, {"Code": "DE002", "Name": "Kiel"}])
        codes, err = _validate_municipalities(ref, "Hamburg", "DE")
        assert codes == []
        assert err == "Municipality 'Hamburg' not found"

    def test_match_by_name(self):
        ref = _make_ref(municipality=[{"Code": "DE001", "Name": "Berlin"}, {"Code": "DE002", "Name": "Kiel"}])
        codes, err = _validate_municipalities(ref, "Berlin, Kiel", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_match_by_code(self):
        ref = _make_ref(municipality=[{"Code": "DE001", "Name": "Berlin"}, {"Code": "DE002", "Name": "Kiel"}])
        codes, err = _validate_municipalities(ref, "DE001, DE002", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_mixed_name_and_code(self):
        ref = _make_ref(municipality=[{"Code": "DE001", "Name": "Berlin"}, {"Code": "DE002", "Name": "Kiel"}])
        codes, err = _validate_municipalities(ref, "Berlin, DE002", "DE")
        assert codes == ["DE001", "DE002"]
        assert err is None

    def test_empty_database_returns_error(self):
        ref = _make_ref(municipality=[])
        codes, err = _validate_municipalities(ref, "Berlin", "DE")
        assert codes == []
        assert err == "No municipalities in database"


class TestCheckDuplicates:

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
            distribution_zone=[{"Code": "Stadtwerke Kiel", "Name": "Stadtwerke Kiel AG"}],
        )
        is_dup, err = _check_duplicates(ref, "Stadtwerke Kiel", "DE")
        assert is_dup is True
        assert "Distribution zone" in err
        assert "already exists" in err

    def test_duplicate_distribution_zone_by_name(self):
        ref = _make_ref(
            distribution_zone=[{"Code": "SWK", "Name": "Stadtwerke Kiel AG"}],
        )
        is_dup, err = _check_duplicates(ref, "Stadtwerke Kiel AG", "DE")
        assert is_dup is True
        assert "Distribution zone" in err

    def test_duplicate_actor(self):
        ref = _make_ref(actor=[{"Name": "Stadtwerke Kiel AG"}])
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

    def test_empty_input_returns_empty(self):
        db = Mock()
        valid, failed = validate_and_split_rows_task([], db)
        assert valid == []
        assert failed == []

    def test_country_validation_failure(self):
        db = Mock()
        db.load_all_records.side_effect = [
            [{"Code": "DE", "Name": "Germany"}],
            [{"Code": "DE001", "Name": "Berlin"}],
            [],
            [],
        ]
        records = [{
            "Id": 1,
            "Company Name": "Test Co",
            "Country": "Spain",
            "Municipalities": "Berlin",
        }]
        valid, failed = validate_and_split_rows_task(records, db)
        assert valid == []
        assert len(failed) == 1
        assert failed[0]["ImportError"] == "Country 'Spain' not found"
        assert failed[0]["ImportStatus"] == "Failed"

    def test_municipality_validation_failure(self):
        db = Mock()
        db.load_all_records.side_effect = [
            [{"Code": "DE", "Name": "Germany"}],
            [{"Code": "DE001", "Name": "Berlin"}],
            [],
            [],
        ]
        records = [{
            "Id": 1,
            "Company Name": "Test Co",
            "Country": "Germany",
            "Municipalities": "UnknownCity",
        }]
        valid, failed = validate_and_split_rows_task(records, db)
        assert valid == []
        assert len(failed) == 1
        assert "Municipality 'UnknownCity' not found" in failed[0]["ImportError"]

    def test_valid_row_passes(self):
        db = Mock()
        db.load_all_records.side_effect = [
            [{"Code": "DE", "Name": "Germany"}],
            [{"Code": "DE001", "Name": "Berlin"}],
            [],
            [],
        ]
        records = [{
            "Id": 1,
            "Company Name": "Test Co",
            "Country": "Germany",
            "Municipalities": "Berlin",
        }]
        valid, failed = validate_and_split_rows_task(records, db)
        assert len(valid) == 1
        assert valid[0]["Id"] == 1
        assert valid[0]["Company Name"] == "Test Co"
        assert valid[0]["CountryCode"] == "DE"
        assert valid[0]["Municipalities"] == ["DE001"]
        assert failed == []


class TestStagingOutputFormat:

    def test_distribution_zone_and_water_company_format(self, tmp_path):
        """Verify the structure of written staging DB matches load_zones and load_water_companies expectations."""
        import duckdb

        valid_records = [{
            "Id": 42,
            "Company Name": "Stadtwerke Kiel AG",
            "CountryCode": "DE",
            "Municipalities": ["DE001", "DE002"],
            "Email": "info@example.com",
            "Phone": "+49 123",
            "Website": "https://example.com",
        }]
        with patch(
            "pipelines.load.import_water_companies_from_staging.load_zones_flow"
        ) as mock_load_zones, patch(
            "pipelines.load.import_water_companies_from_staging.load_water_companies"
        ) as mock_load_companies:
            write_staging_and_load_task(valid_records, tmp_path)

        # Verify data was written to staging DB
        conn = duckdb.connect()
        staging_path = tmp_path / "staging" / "staging.duckdb"
        assert staging_path.exists()
        conn.execute(f"ATTACH '{staging_path}' AS staging")

        dist_records = conn.sql("SELECT * FROM staging.DistributionZone_import").fetchdf().to_dict("records")
        assert len(dist_records) == 1
        assert dist_records[0]["Code"] == "Stadtwerke Kiel AG"
        assert dist_records[0]["Name"] == "Stadtwerke Kiel AG"
        assert dist_records[0]["CountryCode"] == "DE"
        assert list(dist_records[0]["Municipalities"]) == ["DE001", "DE002"]

        wc_records = conn.sql("SELECT * FROM staging.WaterCompany_import").fetchdf().to_dict("records")
        assert len(wc_records) == 1
        assert wc_records[0]["CountryCode"] == "DE"
        assert wc_records[0]["Name"] == "Stadtwerke Kiel AG"
        assert wc_records[0]["Email"] == "info@example.com"
        assert wc_records[0]["Source"] == "NocoDB Import (42)"

        conn.close()

        mock_load_zones.assert_called_once_with(
            level="DistributionZone",
            data_directory=tmp_path,
        )
        mock_load_companies.assert_called_once_with(data_dir=tmp_path)

    def test_empty_valid_records_skips_write_and_load(self, tmp_path):
        with patch(
            "pipelines.load.import_water_companies_from_staging.load_zones_flow"
        ) as mock_load_zones, patch(
            "pipelines.load.import_water_companies_from_staging.load_water_companies"
        ) as mock_load_companies:
            write_staging_and_load_task([], tmp_path)

        mock_load_zones.assert_not_called()
        mock_load_companies.assert_not_called()
