"""Tests for DatabaseHelper class."""

import pytest
from unittest.mock import Mock
import polars as pl
from pipelines.common.db_helper import DatabaseHelper


class TestDatabaseHelperInitialization:
    """Test suite for DatabaseHelper initialization."""

    def test_initialization_with_default_swagger_path(self):
        """Test that DatabaseHelper initializes correctly with default swagger path."""
        # Use a dummy token for testing
        db = DatabaseHelper(api_token="test_token_dummy")

        # Verify base URL was extracted from swagger
        assert db.base_url is not None
        assert db.base_url == "https://noco.services.dataforgood.fr"

        # Verify table IDs were extracted
        assert len(db.table_ids) > 0
        assert isinstance(db.table_ids, dict)

    def test_expected_tables_are_present(self):
        """Test that all expected tables are extracted from swagger."""
        db = DatabaseHelper(api_token="test_token_dummy")

        expected_tables = [
            "Zone_OLD",
            "Actor",
            "Interaction",
            "Analysis",
            "Attachment",
            "ContactPerson",
        ]

        for table_name in expected_tables:
            assert (
                table_name in db.table_ids
            ), f"Table '{table_name}' not found in table_ids"
            assert isinstance(
                db.table_ids[table_name], str
            ), f"Table ID for '{table_name}' is not a string"
            assert (
                len(db.table_ids[table_name]) > 0
            ), f"Table ID for '{table_name}' is empty"

    def test_get_table_id_valid(self):
        """Test _get_table_id method with valid table name."""
        db = DatabaseHelper(api_token="test_token_dummy")

        table_id = db._get_table_id("Actor")
        assert table_id is not None
        assert isinstance(table_id, str)
        assert len(table_id) > 0

    def test_get_table_id_invalid(self):
        """Test _get_table_id method with invalid table name."""
        db = DatabaseHelper(api_token="test_token_dummy")

        with pytest.raises(ValueError, match="Unknown table"):
            db._get_table_id("NonExistentTable")

    def test_client_initialization(self):
        """Test that httpx client is properly initialized."""
        db = DatabaseHelper(api_token="test_token_123")

        # Verify client exists
        assert hasattr(db, "client")
        assert db.client is not None

        # Verify headers are set correctly
        assert "xc-token" in db.client.headers
        assert db.client.headers["xc-token"] == "test_token_123"
        assert db.client.headers["Content-Type"] == "application/json"

    def test_custom_swagger_path(self, tmp_path):
        """Test initialization with a custom swagger path."""
        # Create a minimal test swagger file with v3 format
        test_swagger = {
            "openapi": "3.1.0",
            "servers": [{"url": "https://test.example.com"}],
            "paths": {
                "/api/v3/data/testbase123/testtable456/records": {
                    "get": {"tags": ["TestTable"]}
                }
            },
        }

        swagger_path = tmp_path / "test_swagger.json"
        import json

        with open(swagger_path, "w") as f:
            json.dump(test_swagger, f)

        # Initialize with custom path
        db = DatabaseHelper(api_token="test", swagger_path=swagger_path)

        assert db.base_url == "https://test.example.com"
        assert db.base_id == "testbase123"
        assert "TestTable" in db.table_ids
        assert db.table_ids["TestTable"] == "testtable456"

    def test_missing_swagger_file(self, tmp_path):
        """Test that initialization fails gracefully with missing swagger file."""
        non_existent_path = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError):
            DatabaseHelper(api_token="test", swagger_path=non_existent_path)


class TestDatabaseHelperTableMapping:
    """Test suite for table ID mapping functionality."""

    @pytest.fixture
    def db_helper(self):
        """Fixture to create a DatabaseHelper instance."""
        return DatabaseHelper(api_token="test_token")

    def test_all_tables_have_unique_ids(self, db_helper):
        """Test that all table IDs are unique."""
        table_ids = list(db_helper.table_ids.values())
        assert len(table_ids) == len(set(table_ids)), "Table IDs are not unique"

    def test_table_names_are_strings(self, db_helper):
        """Test that all table names are strings."""
        for table_name in db_helper.table_ids.keys():
            assert isinstance(table_name, str)
            assert len(table_name) > 0

    def test_print_table_mapping(self, db_helper, capsys):
        """Test printing table mapping (useful for documentation)."""
        print("\nTable ID Mapping:")
        for table_name, table_id in sorted(db_helper.table_ids.items()):
            print(f"  {table_name}: {table_id}")

        captured = capsys.readouterr()
        assert "Zone_OLD:" in captured.out
        assert "Actor:" in captured.out


class TestDatabaseHelperLoadFields:
    """Test suite for load_fields method with mocked API responses."""

    @pytest.fixture
    def db_helper(self):
        """Fixture to create a DatabaseHelper instance."""
        return DatabaseHelper(api_token="test_token")

    def test_load_fields_basic(self, db_helper):
        """Test load_fields with a basic v3 API response."""
        # Mock the HTTP client's get method
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {
                    "id": 123,
                    "fields": {
                        "Name": "Water Company A",
                        "Email": "contact@example.com",
                        "Type": "Public"
                    }
                },
                {
                    "id": 456,
                    "fields": {
                        "Name": "Water Company B",
                        "Email": "info@example.com",
                        "Type": "Private"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        # Call load_fields
        result = db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name", "Email"]
        )

        # Verify the result is a Polars DataFrame
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)
        
        # Verify column names
        assert result.columns == ["Id", "Name", "Email"]
        
        # Verify data transformation (id -> Id, fields expanded)
        assert result["Id"].to_list() == [123, 456]
        assert result["Name"].to_list() == ["Water Company A", "Water Company B"]
        assert result["Email"].to_list() == ["contact@example.com", "info@example.com"]

    def test_load_fields_with_condition(self, db_helper):
        """Test load_fields with WHERE condition."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {
                    "id": 789,
                    "fields": {
                        "Name": "Public Water Co",
                        "Type": "Public"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        # Call with condition
        result = db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name", "Type"],
            condition={"Type": "Public"}
        )

        # Verify API call was made with correct parameters
        db_helper.client.get.assert_called_once()
        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        
        # Check WHERE clause was constructed
        assert "where" in params
        assert "(Type,eq,Public)" in params["where"]

        # Verify result
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (1, 3)
        assert result["Type"].to_list() == ["Public"]

    def test_load_fields_with_pagination(self, db_helper):
        """Test load_fields with pagination parameters."""
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        # Call with offset and limit
        db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name"],
            limit=500,
            offset=1000
        )

        # Verify pagination parameters
        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        
        assert params["pageSize"] == 500
        assert params["page"] == 3  # offset 1000 / limit 500 = page 3

    def test_load_fields_empty_result(self, db_helper):
        """Test load_fields with empty API response."""
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        result = db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name", "Email"]
        )

        # Should return empty DataFrame with correct schema
        assert isinstance(result, pl.DataFrame)
        assert result.is_empty()
        assert result.columns == ["Id", "Name", "Email"]
        
        # Verify Id column is Int64
        assert result.schema["Id"] == pl.Int64
        assert result.schema["Name"] == pl.Utf8
        assert result.schema["Email"] == pl.Utf8

    def test_load_fields_v3_endpoint_construction(self, db_helper):
        """Test that v3 endpoint is correctly constructed."""
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name"]
        )

        # Verify the endpoint uses v3 format
        call_args = db_helper.client.get.call_args
        endpoint = call_args[0][0]
        
        # Should be: /api/v3/data/{base_id}/{table_id}/records
        assert endpoint.startswith("/api/v3/data/")
        assert db_helper.base_id in endpoint
        assert "/records" in endpoint

    def test_load_fields_with_null_fields(self, db_helper):
        """Test load_fields handles null/None values in fields."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {
                    "id": 111,
                    "fields": {
                        "Name": "Company with partial data",
                        "Email": None,
                        "Type": "Public"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        result = db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name", "Email", "Type"]
        )

        # Verify null values are preserved
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (1, 4)
        assert result["Name"][0] == "Company with partial data"
        assert result["Email"][0] is None
        assert result["Type"][0] == "Public"

    def test_load_fields_multiple_conditions(self, db_helper):
        """Test load_fields with multiple WHERE conditions."""
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        db_helper.client.get = Mock(return_value=mock_response)

        db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name"],
            condition={"Type": "Public", "Country": "Germany"}
        )

        # Verify multiple conditions are joined with ~and
        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        where_clause = params["where"]
        
        assert "(Type,eq,Public)" in where_clause
        assert "(Country,eq,Germany)" in where_clause
        assert "~and" in where_clause

