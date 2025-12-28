"""Tests for DatabaseHelper class."""

import pytest
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
            "Zone",
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

        table_id = db._get_table_id("Zone")
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
        # Create a minimal test swagger file
        test_swagger = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://test.example.com"}],
            "paths": {
                "/api/v2/tables/testtable123/records": {"get": {"tags": ["TestTable"]}}
            },
        }

        swagger_path = tmp_path / "test_swagger.json"
        import json

        with open(swagger_path, "w") as f:
            json.dump(test_swagger, f)

        # Initialize with custom path
        db = DatabaseHelper(api_token="test", swagger_path=swagger_path)

        assert db.base_url == "https://test.example.com"
        assert "TestTable" in db.table_ids
        assert db.table_ids["TestTable"] == "testtable123"

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
        assert "Zone:" in captured.out
        assert "Actor:" in captured.out
