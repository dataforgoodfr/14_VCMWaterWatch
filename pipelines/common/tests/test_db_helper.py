"""Tests for DatabaseHelper class."""

import pytest
from unittest.mock import Mock, patch
import polars as pl
from pipelines.common.db_helper import DatabaseHelper


# --- Test fixtures / helpers ---

# Minimal meta API responses for a two-table database
TABLES_LIST_RESPONSE = {
    "list": [
        {"id": "tbl_actor", "title": "Actor"},
        {"id": "tbl_zone", "title": "Zone"},
    ]
}

ACTOR_SCHEMA_RESPONSE = {
    "id": "tbl_actor",
    "title": "Actor",
    "fields": [
        {"id": "fld_id", "title": "Id", "type": "ID"},
        {"id": "fld_name", "title": "Name", "type": "SingleLineText"},
        {"id": "fld_email", "title": "Email", "type": "Email"},
        {
            "id": "lnk_zones",
            "title": "Zones",
            "type": "Links",
            "options": {"relation_type": "mm", "related_table_id": "tbl_zone"},
        },
        {
            "id": "lnk_country",
            "title": "Country",
            "type": "Links",
            "options": {"relation_type": "bt", "related_table_id": "tbl_country"},
        },
    ],
}

ZONE_SCHEMA_RESPONSE = {
    "id": "tbl_zone",
    "title": "Zone",
    "fields": [
        {"id": "fld_zid", "title": "Id", "type": "ID"},
        {"id": "fld_code", "title": "Code", "type": "SingleLineText"},
        {"id": "fld_geom", "title": "Geometry", "type": "LongText"},
    ],
}


def _mock_meta_get(url, **kwargs):
    """Side-effect for client.get that returns canned meta API responses."""
    mock_resp = Mock()
    mock_resp.raise_for_status = Mock()
    mock_resp.status_code = 200

    if url.endswith("/tables") and "/tables/" not in url.rstrip("/tables").split("/tables")[0] + "X":
        # List tables
        mock_resp.json.return_value = TABLES_LIST_RESPONSE
    elif url.endswith("/tbl_actor"):
        mock_resp.json.return_value = ACTOR_SCHEMA_RESPONSE
    elif url.endswith("/tbl_zone"):
        mock_resp.json.return_value = ZONE_SCHEMA_RESPONSE
    else:
        mock_resp.json.return_value = {}
    return mock_resp


def _make_db_helper() -> DatabaseHelper:
    """Create a DatabaseHelper with mocked meta API calls."""
    with patch("httpx.Client") as MockClient:
        mock_client = Mock()
        MockClient.return_value = mock_client
        mock_client.get = Mock(side_effect=_mock_meta_get)

        db = DatabaseHelper(
            api_token="test_token",
            base_url="https://test.example.com",
            base_id="test_base_id",
        )
        # After init, replace the side_effect so tests can set their own mocks
        mock_client.get = Mock()
        return db


# --- Initialization tests ---


class TestDatabaseHelperInitialization:
    """Test suite for DatabaseHelper initialization."""

    def test_initialization_sets_base_url_and_id(self):
        db = _make_db_helper()
        assert db.base_url == "https://test.example.com"
        assert db.base_id == "test_base_id"

    def test_table_ids_populated(self):
        db = _make_db_helper()
        assert db.table_ids == {"Actor": "tbl_actor", "Zone": "tbl_zone"}

    def test_link_field_ids_populated(self):
        db = _make_db_helper()
        assert "Actor" in db.link_field_ids
        assert db.link_field_ids["Actor"] == {
            "Zones": "lnk_zones",
            "Country": "lnk_country",
        }

    def test_tables_without_links_not_in_link_field_ids(self):
        db = _make_db_helper()
        assert "Zone" not in db.link_field_ids

    def test_get_table_id_valid(self):
        db = _make_db_helper()
        assert db._get_table_id("Actor") == "tbl_actor"
        assert db._get_table_id("Zone") == "tbl_zone"

    def test_get_table_id_invalid(self):
        db = _make_db_helper()
        with pytest.raises(ValueError, match="Unknown table"):
            db._get_table_id("NonExistent")

    def test_client_headers(self):
        with patch("httpx.Client") as MockClient:
            mock_client = Mock()
            MockClient.return_value = mock_client
            mock_client.get = Mock(side_effect=_mock_meta_get)

            DatabaseHelper(
                api_token="my_secret_token",
                base_url="https://noco.example.com",
                base_id="base123",
            )

            MockClient.assert_called_once_with(
                base_url="https://noco.example.com",
                headers={
                    "Content-Type": "application/json",
                    "xc-token": "my_secret_token",
                },
                timeout=30.0,
            )

    def test_empty_tables_raises(self):
        with patch("httpx.Client") as MockClient:
            mock_client = Mock()
            MockClient.return_value = mock_client

            empty_resp = Mock()
            empty_resp.raise_for_status = Mock()
            empty_resp.json.return_value = {"list": []}
            mock_client.get = Mock(return_value=empty_resp)

            with pytest.raises(ValueError, match="No tables found"):
                DatabaseHelper(
                    api_token="tok",
                    base_url="https://x.com",
                    base_id="bad_base",
                )

    def test_trailing_slash_stripped(self):
        db = _make_db_helper()
        # base_url should not end with /
        assert not db.base_url.endswith("/")


# --- Table mapping tests ---


class TestDatabaseHelperTableMapping:
    @pytest.fixture
    def db_helper(self):
        return _make_db_helper()

    def test_all_tables_have_unique_ids(self, db_helper):
        ids = list(db_helper.table_ids.values())
        assert len(ids) == len(set(ids))

    def test_table_names_are_strings(self, db_helper):
        for name in db_helper.table_ids:
            assert isinstance(name, str) and len(name) > 0


# --- Data operation tests ---


class TestDatabaseHelperLoadFields:
    @pytest.fixture
    def db_helper(self):
        return _make_db_helper()

    def test_load_fields_basic(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {
                    "id": 123,
                    "fields": {
                        "Name": "Water Company A",
                        "Email": "contact@example.com",
                        "Type": "Public",
                    },
                },
                {
                    "id": 456,
                    "fields": {
                        "Name": "Water Company B",
                        "Email": "info@example.com",
                        "Type": "Private",
                    },
                },
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        result = db_helper.load_fields(
            table_name="Actor", fields=["Id", "Name", "Email"]
        )

        assert isinstance(result, pl.DataFrame)
        assert result.shape == (2, 3)
        assert result.columns == ["Id", "Name", "Email"]
        assert result["Id"].to_list() == [123, 456]
        assert result["Name"].to_list() == ["Water Company A", "Water Company B"]

    def test_load_fields_with_condition(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {
            "records": [
                {"id": 789, "fields": {"Name": "Public Water Co", "Type": "Public"}}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        result = db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name", "Type"],
            condition={"Type": "Public"},
        )

        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        assert "(Type,eq,Public)" in params["where"]
        assert result.shape == (1, 3)

    def test_load_fields_with_pagination(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        db_helper.load_fields(
            table_name="Actor", fields=["Id", "Name"], limit=500, offset=1000
        )

        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        assert params["pageSize"] == 500
        assert params["page"] == 3

    def test_load_fields_empty_result(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        result = db_helper.load_fields(
            table_name="Actor", fields=["Id", "Name", "Email"]
        )

        assert isinstance(result, pl.DataFrame)
        assert result.is_empty()
        assert result.columns == ["Id", "Name", "Email"]
        assert result.schema["Id"] == pl.Int64
        assert result.schema["Name"] == pl.Utf8

    def test_load_fields_v3_endpoint_construction(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        db_helper.load_fields(table_name="Actor", fields=["Id", "Name"])

        call_args = db_helper.client.get.call_args
        endpoint = call_args[0][0]
        assert endpoint == "/api/v3/data/test_base_id/tbl_actor/records"

    def test_load_fields_multiple_conditions(self, db_helper):
        mock_response = Mock()
        mock_response.json.return_value = {"records": []}
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.get = Mock(return_value=mock_response)

        db_helper.load_fields(
            table_name="Actor",
            fields=["Id", "Name"],
            condition={"Type": "Public", "Country": "Germany"},
        )

        call_args = db_helper.client.get.call_args
        params = call_args[1]["params"]
        where_clause = params["where"]
        assert "(Type,eq,Public)" in where_clause
        assert "(Country,eq,Germany)" in where_clause
        assert "~and" in where_clause


class TestDatabaseHelperLinkRecords:
    @pytest.fixture
    def db_helper(self):
        return _make_db_helper()

    def test_link_records_single_fk(self, db_helper):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.post = Mock(return_value=mock_response)

        df = pl.DataFrame({"Id": [1, 2], "Zone_id": [10, 20]})
        db_helper.link_records(df, "Actor", "Zones", "Zone_id")

        assert db_helper.client.post.call_count == 2

    def test_link_records_list_fk(self, db_helper):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        db_helper.client.post = Mock(return_value=mock_response)

        df = pl.DataFrame({"Id": [1], "Zone_ids": [[10, 20, 30]]})
        db_helper.link_records(df, "Actor", "Zones", "Zone_ids")

        payload = db_helper.client.post.call_args[1]["json"]
        assert len(payload) == 3

    def test_link_records_unknown_table(self, db_helper):
        df = pl.DataFrame({"Id": [1], "fk": [10]})
        with pytest.raises(ValueError, match="no link fields"):
            db_helper.link_records(df, "Zone", "Something", "fk")

    def test_link_records_unknown_link_field(self, db_helper):
        df = pl.DataFrame({"Id": [1], "fk": [10]})
        with pytest.raises(ValueError, match="not found for table"):
            db_helper.link_records(df, "Actor", "BadField", "fk")

    def test_link_records_missing_id_column(self, db_helper):
        df = pl.DataFrame({"Zone_id": [10]})
        with pytest.raises(ValueError, match="Id"):
            db_helper.link_records(df, "Actor", "Zones", "Zone_id")

    def test_link_records_missing_fk_column(self, db_helper):
        df = pl.DataFrame({"Id": [1]})
        with pytest.raises(ValueError, match="not found in DataFrame"):
            db_helper.link_records(df, "Actor", "Zones", "Zone_id")
