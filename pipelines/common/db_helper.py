"""Database helper module for loading and inserting data using NocoDB API."""

from typing import Dict, List, Optional, Any
import polars as pl
import httpx


class DatabaseHelper:
    """Helper class for NocoDB operations using Polars dataframes.

    This class provides a simple interface to interact with NocoDB's REST API,
    allowing for reading and writing data using Polars DataFrames.

    Configuration is loaded dynamically from the NocoDB meta API at startup.
    """

    def __init__(self, api_token: str, base_url: str, base_id: str):
        """
        Initialize the database helper with NocoDB connection.

        Args:
            api_token: NocoDB API token for authentication (xc-token header)
            base_url: NocoDB server URL (e.g. "https://noco.services.dataforgood.fr")
            base_id: NocoDB base (project) ID (e.g. "pqc6cnm5mpnr9ka")

        Example:
            db = DatabaseHelper(
                api_token="your_token_here",
                base_url="https://noco.services.dataforgood.fr",
                base_id="pqc6cnm5mpnr9ka",
            )
        """
        self.base_url = base_url.rstrip("/")
        self.base_id = base_id

        # Setup HTTP client
        headers = {"Content-Type": "application/json", "xc-token": api_token}
        self.client = httpx.Client(
            base_url=self.base_url, headers=headers, timeout=30.0
        )

        # Fetch schema from meta API
        self.table_ids: Dict[str, str] = {}
        self.link_field_ids: Dict[str, Dict[str, str]] = {}
        self._fetch_schema()

    def _fetch_schema(self) -> None:
        """Fetch table IDs and link field IDs from the NocoDB meta API.

        Calls:
          1. GET /api/v3/meta/bases/{base_id}/tables  -> list of tables
          2. GET /api/v3/meta/bases/{base_id}/tables/{table_id}  -> per-table schema

        Populates:
          - self.table_ids: {table_title: table_id}
          - self.link_field_ids: {table_title: {link_field_title: link_field_id}}
        """
        # Step 1: list all tables
        resp = self.client.get(f"/api/v3/meta/bases/{self.base_id}/tables")
        resp.raise_for_status()
        tables = resp.json().get("list", [])

        if not tables:
            raise ValueError(
                f"No tables found for base '{self.base_id}'. "
                "Check that BASE_ID is correct and the API token has access."
            )

        # Build table_ids mapping
        for table in tables:
            self.table_ids[table["title"]] = table["id"]

        # Step 2: fetch each table's schema to extract link field IDs
        for table_name, table_id in self.table_ids.items():
            resp = self.client.get(
                f"/api/v3/meta/bases/{self.base_id}/tables/{table_id}"
            )
            resp.raise_for_status()
            schema = resp.json()

            # Extract link fields
            link_fields: Dict[str, str] = {}
            for field in schema.get("fields", []):
                if field.get("type") == "Links":
                    link_fields[field["title"]] = field["id"]

            if link_fields:
                self.link_field_ids[table_name] = link_fields

    def _get_table_id(self, table_name: str) -> str:
        """
        Get the NocoDB table ID from the friendly table name.

        Args:
            table_name: Friendly table name (e.g., "Zone", "Actor")

        Returns:
            NocoDB table ID

        Raises:
            ValueError: If table name is not recognized
        """
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
    ) -> pl.DataFrame:
        """
        Load one or more fields from a NocoDB table.

        Args:
            table_name: Name of the table to query (e.g., "Zone", "Actor")
            fields: List of field names to select
            condition: Optional dictionary of key-value pairs for WHERE clause
                      Format: {"field": "value"} creates (field,eq,value) in NocoDB
            limit: Maximum number of records to return (default: 1000, max: 1000)
            offset: Number of records to skip for pagination (default: 0)

        Returns:
            Polars DataFrame with the selected fields

        Raises:
            httpx.HTTPError: If the API request fails
        """
        table_id = self._get_table_id(table_name)

        # Build query parameters
        params: Dict[str, Any] = {
            "pageSize": min(limit, 1000),  # NocoDB max limit
        }
        if fields:
            params["fields"] = ",".join(fields)

        # Add page parameter for pagination
        if offset > 0:
            page = (offset // min(limit, 1000)) + 1
            params["page"] = page

        # Add WHERE condition if provided
        # NocoDB format: where=(field,eq,value) or where=(field1,eq,value1)~and(field2,eq,value2)
        if condition:
            where_parts = [f"({k},eq,{v})" for k, v in condition.items()]
            params["where"] = "~and".join(where_parts)

        # Make API call using v3 endpoint
        endpoint = f"/api/v3/data/{self.base_id}/{table_id}/records"
        response = self.client.get(endpoint, params=params)
        if response.status_code == 422:
            raise ValueError(f"Failed to load fields: {response.json()}")
        response.raise_for_status()

        data = response.json()
        records = data.get("records", [])

        # Convert to Polars DataFrame
        if not records:
            # Return empty DataFrame with correct schema
            # Infer types: 'id' and 'Id' -> Int64, everything else -> Utf8
            schema: Dict[str, Any] = {"Id": pl.Int64}
            if fields:
                for field in fields:
                    if field.lower() == "id":
                        schema[field] = pl.Int64
                    else:
                        schema[field] = pl.Utf8
            return pl.DataFrame(schema=schema)

        # Transform v3 format: {id: 123, fields: {...}} -> {Id: 123, ...}
        flattened_records = []
        for record in records:
            flat_record = {}
            # Map "id" to "Id"
            if "id" in record:
                flat_record["Id"] = record["id"]
            # Expand "fields" dict into top-level columns
            if "fields" in record:
                flat_record.update(record["fields"])
            flattened_records.append(flat_record)

        return pl.DataFrame(flattened_records).select(fields)

    def insert_records(
        self, df: pl.DataFrame, table_name: str, batch_size: int = 10
    ) -> pl.DataFrame:
        """
        Load a Polars DataFrame into a NocoDB table (bulk insert).

        Args:
            df: Polars DataFrame to insert
            table_name: Name of the target table (e.g., "Zone", "Actor")
            batch_size: Number of records to insert per batch (default: 10)

        Raises:
            httpx.HTTPError: If the API request fails

        Returns:
            Polars DataFrame with the inserted records and their IDs
        """
        if df.is_empty():
            return df.with_columns(pl.lit(None).alias("Id"))

        table_id = self._get_table_id(table_name)

        # Convert DataFrame to list of dicts
        records = df.to_dicts()

        # v3 endpoint
        endpoint = f"/api/v3/data/{self.base_id}/{table_id}/records"

        # Insert in batches to avoid overwhelming the API
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            # Transform to v3 format: wrap data in "fields" object
            v3_batch = [{"fields": record} for record in batch]

            response = self.client.post(endpoint, json=v3_batch)
            if response.status_code == 422:
                raise ValueError(f"Failed to insert records: {response.json()}")
            response.raise_for_status()

            # v3 returns {records: [{id: 123, fields: {...}}, ...]}
            response_data = response.json()
            inserted_records = response_data["records"]

            # Extract Id from each record and add to batch
            for j, record in enumerate(inserted_records):
                # Map v3 format "id" to "Id"
                batch[j]["Id"] = record["id"]

        return pl.DataFrame(records)

    def update_records(
        self, df: pl.DataFrame, table_name: str, batch_size: int = 10
    ) -> pl.DataFrame:
        """
        Update existing records in a NocoDB table (bulk update).

        Args:
            df: Polars DataFrame with "Id" column and fields to update
            table_name: Name of the target table (e.g., "Zone", "Actor")
            batch_size: Number of records to update per batch (default: 10)

        Raises:
            ValueError: If "Id" column is missing from dataframe
            httpx.HTTPError: If the API request fails

        Returns:
            Polars DataFrame with the updated records
        """
        if df.is_empty():
            return df

        # Validate dataframe has required column
        if "Id" not in df.columns:
            raise ValueError(
                "DataFrame must have 'Id' column containing record IDs to update."
            )

        table_id = self._get_table_id(table_name)

        # Filter out rows where Id is null
        records_to_update = df.filter(pl.col("Id").is_not_null())

        if records_to_update.is_empty():
            return df

        # Convert DataFrame to list of dicts
        records = records_to_update.to_dicts()

        # v3 endpoint
        endpoint = f"/api/v3/data/{self.base_id}/{table_id}/records"

        # Update in batches to avoid overwhelming the API
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]

            # Transform to v3 format: {"id": record_id, "fields": {...}}
            v3_batch = []
            for record in batch:
                record_id = record.pop("Id")  # Extract Id from the record
                v3_batch.append({"id": str(record_id), "fields": record})

            response = self.client.patch(endpoint, json=v3_batch)
            if response.status_code == 422:
                raise ValueError(f"Failed to update records: {response.json()}")
            response.raise_for_status()

        return records_to_update

    def delete_records(
        self, df: pl.DataFrame, table_name: str, batch_size: int = 10
    ) -> None:
        """
        Delete records from a NocoDB table (bulk delete).

        Args:
            df: Polars DataFrame with "Id" column containing record IDs to delete
            table_name: Name of the target table (e.g., "Zone", "Actor")
            batch_size: Number of records to delete per batch (default: 10)

        Raises:
            ValueError: If "Id" column is missing from dataframe
            httpx.HTTPError: If the API request fails
        """
        if df.is_empty():
            return

        # Validate dataframe has required column
        if "Id" not in df.columns:
            raise ValueError(
                "DataFrame must have 'Id' column containing record IDs to delete."
            )

        table_id = self._get_table_id(table_name)

        # Filter out rows where Id is null
        records_to_delete = df.filter(pl.col("Id").is_not_null())

        if records_to_delete.is_empty():
            return

        # Extract IDs as list
        ids = records_to_delete["Id"].to_list()

        # v3 endpoint
        endpoint = f"/api/v3/data/{self.base_id}/{table_id}/records"

        # Delete in batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]

            # Format as array of {"id": <value>}
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
    ) -> pl.DataFrame:
        """
        Load all records from a table with automatic pagination.

        Args:
            table_name: Name of the table to query
            fields: Optional list of field names to select (if None, returns all fields)
            condition: Optional dictionary of key-value pairs for WHERE clause

        Returns:
            Polars DataFrame with all matching records
        """
        all_records = []
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

            all_records.append(batch)

            if len(batch) < limit:
                # Last page
                break

            offset += limit

        return pl.concat(all_records)

    def link_records(
        self,
        df: pl.DataFrame,
        table_name: str,
        link_field_name: str,
        foreign_key_column: str,
    ) -> None:
        """
        Link records in a parent table to records in a related table.

        Args:
            df: DataFrame with 'Id' column (from insert_records()) and foreign key column
            table_name: Parent table name (e.g., "Actor")
            link_field_name: Exact link field name (e.g., "Zones")
            foreign_key_column: Column in df containing foreign key IDs (e.g., "Zone_id").
                              Can be either a single integer or a list of integers.
                              If a list, all IDs in the list will be linked to the record.

        Raises:
            ValueError: If table_name not in link_field_ids
            ValueError: If link_field_name not found for table
            ValueError: If "Id" column missing from dataframe
            ValueError: If foreign_key_column missing from dataframe
            httpx.HTTPError: If the API request fails

        Examples:
            # Link each actor to a single zone
            actors_df = db.insert_records(actors_df, "Actor")
            db.link_records(actors_df, "Actor", "Zones", "Zone_id")

            # Link each actor to multiple zones (if Zone_id is a list column)
            actors_df = db.insert_records(actors_df, "Actor")
            db.link_records(actors_df, "Actor", "Zones", "Zone_ids")
        """
        # Validate table exists in link_field_ids
        if table_name not in self.link_field_ids:
            raise ValueError(
                f"Table '{table_name}' has no link fields defined. "
                f"Available tables with links: {list(self.link_field_ids.keys())}"
            )

        # Validate link field exists for table
        if link_field_name not in self.link_field_ids[table_name]:
            raise ValueError(
                f"Link field '{link_field_name}' not found for table '{table_name}'. "
                f"Available link fields: {list(self.link_field_ids[table_name].keys())}"
            )

        # Validate dataframe has required columns
        if "Id" not in df.columns:
            raise ValueError(
                "DataFrame must have 'Id' column. "
                "Did you call insert_records() first?"
            )

        if foreign_key_column not in df.columns:
            raise ValueError(
                f"Column '{foreign_key_column}' not found in DataFrame. "
                f"Available columns: {df.columns}"
            )

        # Get table_id and link_field_id
        table_id = self._get_table_id(table_name)
        link_field_id = self.link_field_ids[table_name][link_field_name]

        # Filter out rows where foreign key is null
        records_to_link = df.filter(pl.col(foreign_key_column).is_not_null())

        if records_to_link.is_empty():
            return

        # v3 endpoint
        endpoint_template = f"/api/v3/data/{self.base_id}/{table_id}/links/{link_field_id}/{{record_id}}"

        # Link each record
        for row in records_to_link.iter_rows(named=True):
            record_id = row["Id"]
            foreign_value = row[foreign_key_column]

            # Handle both single integer and list of integers
            if isinstance(foreign_value, list):
                # List of foreign keys - create multiple link records
                link_payload = [{"id": str(v)} for v in foreign_value]
            else:
                # Single foreign key - create single link record
                link_payload = [{"id": str(foreign_value)}]

            # POST to link endpoint
            endpoint = endpoint_template.format(record_id=record_id)
            response = self.client.post(endpoint, json=link_payload)
            response.raise_for_status()

    def __del__(self):
        """Close the HTTP client when the object is destroyed."""
        if hasattr(self, "client"):
            self.client.close()
