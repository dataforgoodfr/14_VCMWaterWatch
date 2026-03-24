"""Database helper module for loading and inserting data using NocoDB API."""

from typing import Dict, List, Optional, Any
import httpx


class DatabaseHelper:
    """Helper class for NocoDB operations using list[dict].

    This class provides a simple interface to interact with NocoDB's REST API,
    accepting and returning plain ``list[dict]`` records.

    Configuration is loaded dynamically from the NocoDB meta API at startup.
    """

    def __init__(self, api_token: str, base_url: str, base_id: str):
        """
        Initialize the database helper with NocoDB connection.

        Args:
            api_token: NocoDB API token for authentication (xc-token header)
            base_url: NocoDB server URL (e.g. "https://noco.services.dataforgood.fr")
            base_id: NocoDB base (project) ID (e.g. "pqc6cnm5mpnr9ka")
        """
        base_url = base_url.rstrip("/")
        # If URL already has /api/v3, use as-is; otherwise append it
        if base_url.lower().endswith("/api/v3"):
            self.api_base = base_url
        else:
            self.api_base = f"{base_url}/api/v3"
        self.base_url = self.api_base  # for backward compat
        self.base_id = base_id

        # Setup HTTP client
        headers = {"Content-Type": "application/json", "xc-token": api_token}
        self.client = httpx.Client(
            base_url=self.api_base, headers=headers, timeout=30.0
        )

        # Fetch schema from meta API
        self.table_ids: Dict[str, str] = {}
        self.link_field_ids: Dict[str, Dict[str, str]] = {}
        self._fetch_schema()

    def _fetch_schema(self) -> None:
        """Fetch table IDs and link field IDs from the NocoDB meta API.

        Calls:
          1. GET .../meta/bases/{base_id}/tables  -> list of tables
          2. GET .../meta/bases/{base_id}/tables/{table_id}  -> per-table schema

        Populates:
          - self.table_ids: {table_title: table_id}
          - self.link_field_ids: {table_title: {link_field_title: link_field_id}}
        """
        # Step 1: list all tables
        resp = self.client.get(f"/meta/bases/{self.base_id}/tables")
        resp.raise_for_status()
        tables = resp.json().get("list", [])

        if not tables:
            raise ValueError(
                f"No tables found for base '{self.base_id}'. "
                "Check that NOCODB_BASE_ID is correct and the API token has access."
            )

        for table in tables:
            self.table_ids[table["title"]] = table["id"]

        for table_name, table_id in self.table_ids.items():
            resp = self.client.get(
                f"/meta/bases/{self.base_id}/tables/{table_id}"
            )
            resp.raise_for_status()
            schema = resp.json()

            link_fields: Dict[str, str] = {}
            for field in schema.get("fields", []):
                if field.get("type") == "Links":
                    link_fields[field["title"]] = field["id"]

            if link_fields:
                self.link_field_ids[table_name] = link_fields

    def _get_table_id(self, table_name: str) -> str:
        table_id = self.table_ids.get(table_name)
        if not table_id:
            raise ValueError(
                f"Unknown table: {table_name}. "
                f"Available tables: {list(self.table_ids.keys())}"
            )
        return table_id

    def load_fields(
        self,
        table_name: str,
        fields: List[str] | None = None,
        condition: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict]:
        """
        Load one or more fields from a NocoDB table.

        Returns:
            list[dict] with the selected fields
        """
        table_id = self._get_table_id(table_name)

        params: Dict[str, Any] = {
            "pageSize": min(limit, 1000),
        }
        if fields:
            params["fields"] = ",".join(fields)

        if offset > 0:
            page = (offset // min(limit, 1000)) + 1
            params["page"] = page

        if condition:
            where_parts = [f"({k},eq,{v})" for k, v in condition.items()]
            params["where"] = "~and".join(where_parts)

        endpoint = f"/data/{self.base_id}/{table_id}/records"
        response = self.client.get(endpoint, params=params)
        if response.status_code == 422:
            err_payload = response.json()
            if err_payload["error"] != "ERR_INVALID_OFFSET_VALUE":
                raise ValueError(f"Failed to load fields: {response.json()}")
        else:
            response.raise_for_status()

        data = response.json()
        records = data.get("records", [])

        if not records:
            return []

        # Transform v3 format: {id: 123, fields: {...}} -> {Id: 123, ...}
        flattened_records = []
        for record in records:
            flat_record: dict[str, Any] = {}
            if "id" in record:
                flat_record["Id"] = record["id"]
            if "fields" in record:
                flat_record.update(record["fields"])
            # Select only requested fields
            if fields:
                flat_record = {k: flat_record.get(k) for k in fields}
            flattened_records.append(flat_record)

        return flattened_records

    def insert_records(
        self, records: list[dict], table_name: str, batch_size: int = 10
    ) -> list[dict]:
        """
        Insert records into a NocoDB table (bulk insert).

        Returns:
            list[dict] with the inserted records and their IDs
        """
        if len(records) == 0:
            return records

        table_id = self._get_table_id(table_name)

        # Make a copy so we don't mutate the caller's data
        records = [dict(r) for r in records]

        endpoint = f"/data/{self.base_id}/{table_id}/records"

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            v3_batch = [{"fields": record} for record in batch]

            response = self.client.post(endpoint, json=v3_batch)
            if response.status_code == 422:
                raise ValueError(f"Failed to insert records: {response.json()}")
            response.raise_for_status()

            response_data = response.json()
            inserted_records = response_data["records"]

            for j, record in enumerate(inserted_records):
                batch[j]["Id"] = record["id"]

        return records

    def update_records(
        self, records: list[dict], table_name: str, batch_size: int = 10
    ) -> list[dict]:
        """
        Update existing records in a NocoDB table (bulk update).
        """
        if len(records) == 0:
            return records

        if not any("Id" in r for r in records):
            raise ValueError(
                "Records must have 'Id' key containing record IDs to update."
            )

        table_id = self._get_table_id(table_name)

        # Filter out rows where Id is null
        records_to_update = [r for r in records if r.get("Id") is not None]
        if not records_to_update:
            return records

        # Make copies for PATCH payload
        records_to_update = [dict(r) for r in records_to_update]

        endpoint = f"/data/{self.base_id}/{table_id}/records"

        for i in range(0, len(records_to_update), batch_size):
            batch = records_to_update[i : i + batch_size]

            v3_batch = []
            for record in batch:
                r = dict(record)
                record_id = r.pop("Id")
                v3_batch.append({"id": str(record_id), "fields": r})

            response = self.client.patch(endpoint, json=v3_batch)
            if response.status_code == 422:
                raise ValueError(f"Failed to update records: {response.json()}")
            response.raise_for_status()

        return records_to_update

    def delete_records(
        self, records: list[dict], table_name: str, batch_size: int = 10
    ) -> None:
        """
        Delete records from a NocoDB table (bulk delete).
        """
        if len(records) == 0:
            return

        if not any("Id" in r for r in records):
            raise ValueError(
                "Records must have 'Id' key containing record IDs to delete."
            )

        table_id = self._get_table_id(table_name)

        ids = [r["Id"] for r in records if r.get("Id") is not None]
        if not ids:
            return

        endpoint = f"/data/{self.base_id}/{table_id}/records"

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            delete_payload = [{"id": str(id_val)} for id_val in batch_ids]

            response = self.client.request("DELETE", endpoint, json=delete_payload)
            if response.status_code == 422:
                raise ValueError(f"Failed to delete records: {response.json()}")
            response.raise_for_status()

    def load_all_records(
        self,
        table_name: str,
        fields: Optional[List[str]] = None,
        condition: Optional[Dict[str, Any]] = None,
    ) -> list[dict]:
        """
        Load all records from a table with automatic pagination.
        """
        all_records: list[dict] = []
        offset = 0
        limit = 1000

        while True:
            batch = self.load_fields(
                table_name=table_name,
                fields=fields,
                condition=condition,
                limit=limit,
                offset=offset,
            )

            all_records.extend(batch)

            if len(batch) < limit:
                break

            offset += limit

        return all_records

    def link_records(
        self,
        records: list[dict],
        table_name: str,
        link_field_name: str,
        foreign_key_column: str,
    ) -> None:
        """
        Link records in a parent table to records in a related table.
        """
        if table_name not in self.link_field_ids:
            raise ValueError(
                f"Table '{table_name}' has no link fields defined. "
                f"Available tables with links: {list(self.link_field_ids.keys())}"
            )

        if link_field_name not in self.link_field_ids[table_name]:
            raise ValueError(
                f"Link field '{link_field_name}' not found for table '{table_name}'. "
                f"Available link fields: {list(self.link_field_ids[table_name].keys())}"
            )

        columns = set()
        for r in records:
            columns.update(r.keys())

        if "Id" not in columns:
            raise ValueError(
                "Records must have 'Id' key. "
                "Did you call insert_records() first?"
            )

        if foreign_key_column not in columns:
            raise ValueError(
                f"Column '{foreign_key_column}' not found in records. "
                f"Available columns: {sorted(columns)}"
            )

        table_id = self._get_table_id(table_name)
        link_field_id = self.link_field_ids[table_name][link_field_name]

        records_to_link = [r for r in records if r.get(foreign_key_column) is not None]
        if not records_to_link:
            return

        endpoint_template = f"/data/{self.base_id}/{table_id}/links/{link_field_id}/{{record_id}}"

        for row in records_to_link:
            record_id = row["Id"]
            foreign_value = row[foreign_key_column]

            if isinstance(foreign_value, list):
                link_payload = [{"id": str(v)} for v in foreign_value]
            else:
                link_payload = [{"id": str(foreign_value)}]

            endpoint = endpoint_template.format(record_id=record_id)
            response = self.client.post(endpoint, json=link_payload)
            response.raise_for_status()

    def __del__(self):
        """Close the HTTP client when the object is destroyed."""
        if hasattr(self, "client"):
            self.client.close()
