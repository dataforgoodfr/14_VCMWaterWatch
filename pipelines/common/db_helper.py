"""Database helper module for loading and inserting data using NocoDB API."""

from typing import Dict, List, Optional, Any
import polars as pl
import httpx
import json
import re
from pathlib import Path


# Link field IDs extracted from swagger file
LINK_FIELD_IDS: Dict[str, Dict[str, str]] = {
    "Actor": {
        "Contacts": "c33y0i580vry0b2",
        "Country": "cyauwdp4zhgjzgw",
        "Distribution Zones": "c07ta1ff4n2d7fv",
        "Interactions": "c9hswu4xal8fqdv",
        "Zones": "cl426jurhv4prp1",
    },
    "Analysis": {
        "Zone": "cz3mphin1xmgz54",
    },
    "Attachment": {
        "Interaction": "cg8ewp4l4cd6g81",
    },
    "ContactPerson": {
        "Actor": "czhttvyt50wtc9b",
    },
    "Country": {
        "Actors": "c2kwo40lxxpl9ds",
        "Distribution Zones": "c3z8syohglc642n",
        "Municipalities": "c7ihcbx9ux2u0m8",
    },
    "DistributionZone": {
        "Actors": "cxvebklqtcljgbr",
        "Country": "cvqrmhcm1oy4w9r",
        "Interactions": "cdbcif735pv7jwa",
        "Municipalities": "cixn6cop13sahwm",
    },
    "Interaction": {
        "Actor": "c3myqu8izdqy4hm",
        "Attachments": "cciu7rawwhhiw0w",
        "Distribution Zone": "cen4auiduszs81f",
        "Zone": "c9v7d0th7wlbuot",
    },
    "Municipality": {
        "Country": "cdutxg2krgjqb2f",
        "Distribution Zone": "c9ztov908mvso1v",
    },
    "Page": {
        "PageFields": "cvd7pwauikoiwy0",
    },
    "PageField": {
        "Translations": "c94yyru03b2kvz8",
        "WebsitePage": "crnt4gjmygneti8",
    },
    "Translation": {
        "PageField": "cu2ip53y4p6bj1v",
    },
    "Zone_OLD": {
        "Actors": "crchwow9pqhe78o",
        "Analysis": "cvy23o27xc6bz9n",
        "Contains Areas": "ce19bme4uy6d5h9",
        "Interactions": "co92u1gp84qx6qn",
    },
}

# View name to view ID mappings extracted from swagger file
VIEW_NAMES: Dict[str, Dict[str, str]] = {
    "Actor": {
        "Default view": "vw3iewh0mpimkk1f",
    },
    "Analysis": {
        "Default view": "vwh0xc5evlle6nco",
    },
    "Attachment": {
        "Default view": "vwiqlcw653c0xifz",
    },
    "ContactPerson": {
        "Default view": "vwrvneriqexypzjm",
    },
    "Country": {
        "Default view": "vwnc4xpxy25qn1g9",
    },
    "DistributionZone": {
        "Default view": "vwhpk8kw4npo3d3d",
        "Missing Geometries": "vw2o0h78effk3g7v",
    },
    "Interaction": {
        "Default view": "vwaaoke3oeby9knc",
    },
    "Municipality": {
        "Default view": "vwv5d0f7odzf04ql",
    },
    "Page": {
        "Default view": "vwrsp9oe1hhlrspu",
    },
    "PageField": {
        "Default view": "vw6ptvtcdeyrmv79",
    },
    "Translation": {
        "Default view": "vwlpqskp8mxounin",
    },
    "Zone_OLD": {
        "Countries": "vwqj5ccgz7x02y3i",
        "Default view": "vw43dwdr3xswhbsv",
        "Distribution Zones": "vw27vufl67az4v5h",
        "Municipalities / Communes": "vw74ss2146qnca71",
    },
}


class DatabaseHelper:
    """Helper class for NocoDB operations using Polars dataframes.

    This class provides a simple interface to interact with NocoDB's REST API,
    allowing for reading and writing data using Polars DataFrames.

    Configuration is loaded from the OpenAPI swagger file.
    """

    def __init__(self, api_token: str, swagger_path: Optional[Path] = None):
        """
        Initialize the database helper with NocoDB connection.

        Args:
            api_token: NocoDB API token for authentication (xc-token header)
            swagger_path: Optional path to swagger JSON file.
                         Defaults to nocodb_swagger.json in the same directory

        Example:
            db = DatabaseHelper(api_token="your_token_here")
        """
        # Load swagger file
        swagger_file: Path
        if swagger_path is None:
            swagger_file = Path(__file__).parent / "nocodb_swagger.json"
        else:
            swagger_file = swagger_path

        with open(swagger_file, "r") as f:
            swagger = json.load(f)

        # Extract base URL from servers section
        servers = swagger.get("servers", [])
        if not servers:
            raise ValueError("No servers defined in swagger file")

        # Get the first concrete URL (not a template)
        self.base_url = None
        for server in servers:
            url = server.get("url", "")
            if "{" not in url:  # Skip template URLs
                self.base_url = url.rstrip("/")
                break

        if not self.base_url:
            raise ValueError("No concrete server URL found in swagger file")

        # Extract base_id and table IDs from paths
        # Pattern for v3: /api/v3/data/{base_id}/{table_id}/records
        self.base_id: str = ""
        self.table_ids: Dict[str, str] = {}
        paths = swagger.get("paths", {})

        pattern = re.compile(r"/api/v3/data/([a-z0-9]+)/([a-z0-9]+)/records$")

        for path, methods in paths.items():
            match = pattern.match(path)
            if match:
                base_id = match.group(1)
                table_id = match.group(2)

                # Set base_id if not already set
                if not self.base_id:
                    self.base_id = base_id

                # Get the table name from the first method's tags
                for method in methods.values():
                    if isinstance(method, dict) and "tags" in method:
                        tags = method.get("tags", [])
                        if tags:
                            table_name = tags[0]
                            self.table_ids[table_name] = table_id
                            break

        if not self.table_ids:
            raise ValueError("No table IDs found in swagger file")

        if not self.base_id:
            raise ValueError("No base ID found in swagger file")

        # Setup HTTP client
        headers = {"Content-Type": "application/json", "xc-token": api_token}

        self.client = httpx.Client(
            base_url=self.base_url, headers=headers, timeout=30.0
        )

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

    def _resolve_view_name(self, table_name: str, view_name: str) -> str:
        """
        Resolve a view name to its view ID for a given table.

        Args:
            table_name: Name of the table
            view_name: Name of the view to resolve

        Returns:
            View ID corresponding to the view name

        Raises:
            ValueError: If table has no views defined or view name not found
        """
        if not view_name:
            return ""

        # Check if table has any views defined
        if table_name not in VIEW_NAMES:
            raise ValueError(
                f"Table '{table_name}' has no views defined in swagger file. "
                f"Tables with views: {list(VIEW_NAMES.keys())}"
            )

        # Check if view name exists for this table
        table_views = VIEW_NAMES[table_name]
        if view_name not in table_views:
            raise ValueError(
                f"View '{view_name}' not found for table '{table_name}'. "
                f"Available views: {list(table_views.keys())}"
            )

        return table_views[view_name]

    def load_fields(
        self,
        table_name: str,
        fields: List[str] | None = None,
        condition: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0,
        viewName: str = "",
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
            viewName: Optional view name to filter records (default: "")
                     View name will be resolved to view ID using VIEW_NAMES mapping

        Returns:
            Polars DataFrame with the selected fields

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If viewName is provided but not found in VIEW_NAMES
        """
        table_id = self._get_table_id(table_name)

        # Resolve view name to view ID if provided
        view_id = self._resolve_view_name(table_name, viewName)

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

        # Add viewId parameter if view_id is provided
        if view_id:
            params["viewId"] = view_id

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
        viewName: str = "",
    ) -> pl.DataFrame:
        """
        Load all records from a table with automatic pagination.

        Args:
            table_name: Name of the table to query
            fields: Optional list of field names to select (if None, returns all fields)
            condition: Optional dictionary of key-value pairs for WHERE clause
            viewName: Optional view name to filter records (default: "")
                     View name will be resolved to view ID using VIEW_NAMES mapping

        Returns:
            Polars DataFrame with all matching records

        Raises:
            ValueError: If viewName is provided but not found in VIEW_NAMES
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
                viewName=viewName,
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
            link_field_name: Exact link field name from swagger (e.g., "Zones")
            foreign_key_column: Column in df containing foreign key IDs (e.g., "Zone_id").
                              Can be either a single integer or a list of integers.
                              If a list, all IDs in the list will be linked to the record.

        Raises:
            ValueError: If table_name not in LINK_FIELD_IDS
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
        # Validate table exists
        if table_name not in LINK_FIELD_IDS:
            raise ValueError(
                f"Table '{table_name}' has no link fields defined. "
                f"Available tables: {list(LINK_FIELD_IDS.keys())}"
            )

        # Validate link field exists for table
        if link_field_name not in LINK_FIELD_IDS[table_name]:
            raise ValueError(
                f"Link field '{link_field_name}' not found for table '{table_name}'. "
                f"Available link fields: {list(LINK_FIELD_IDS[table_name].keys())}"
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
        link_field_id = LINK_FIELD_IDS[table_name][link_field_name]

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
