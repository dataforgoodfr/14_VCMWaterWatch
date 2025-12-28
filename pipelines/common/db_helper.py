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
    "Interaction": {
        "Actor": "c3myqu8izdqy4hm",
        "Attachments": "cciu7rawwhhiw0w",
        "Zone": "c9v7d0th7wlbuot",
    },
    "Zone": {
        "Actors": "crchwow9pqhe78o",
        "Analysis": "cvy23o27xc6bz9n",
        "Contains Areas": "ce19bme4uy6d5h9",
        "Interactions": "co92u1gp84qx6qn",
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
        
        with open(swagger_file, 'r') as f:
            swagger = json.load(f)
        
        # Extract base URL from servers section
        servers = swagger.get('servers', [])
        if not servers:
            raise ValueError("No servers defined in swagger file")
        
        # Get the first concrete URL (not a template)
        self.base_url = None
        for server in servers:
            url = server.get('url', '')
            if '{' not in url:  # Skip template URLs
                self.base_url = url.rstrip('/')
                break
        
        if not self.base_url:
            raise ValueError("No concrete server URL found in swagger file")
        
        # Extract table IDs from paths
        # Pattern: /api/v2/tables/{table_id}/records
        self.table_ids: Dict[str, str] = {}
        paths = swagger.get('paths', {})
        
        pattern = re.compile(r'/api/v2/tables/([a-z0-9]+)/records$')
        for path, methods in paths.items():
            match = pattern.match(path)
            if match:
                table_id = match.group(1)
                # Get the table name from the first method's tags
                for method in methods.values():
                    if isinstance(method, dict) and 'tags' in method:
                        tags = method.get('tags', [])
                        if tags:
                            table_name = tags[0]
                            self.table_ids[table_name] = table_id
                            break
        
        if not self.table_ids:
            raise ValueError("No table IDs found in swagger file")
        
        # Setup HTTP client
        headers = {
            "Content-Type": "application/json",
            "xc-token": api_token
        }
        
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0
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
    
    def load_fields(
        self,
        table_name: str,
        fields: List[str],
        condition: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        offset: int = 0
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
            "fields": ",".join(fields),
            "limit": min(limit, 1000),  # NocoDB max limit
            "offset": offset
        }
        
        # Add WHERE condition if provided
        # NocoDB format: where=(field,eq,value) or where=(field1,eq,value1)~and(field2,eq,value2)
        if condition:
            where_parts = [f"({k},eq,{v})" for k, v in condition.items()]
            params["where"] = "~and".join(where_parts)
        
        # Make API call
        response = self.client.get(
            f"/api/v2/tables/{table_id}/records",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        records = data.get("list", [])
        
        # Convert to Polars DataFrame
        if not records:
            # Return empty DataFrame with correct schema
            # Infer types: 'id' and 'Id' -> Int64, everything else -> Utf8
            schema = {}
            for field in fields:
                if field.lower() == 'id':
                    schema[field] = pl.Int64
                else:
                    schema[field] = pl.Utf8
            return pl.DataFrame(schema=schema)
        
        return pl.DataFrame(records).select(fields)
    
    def insert_records(self, df: pl.DataFrame, table_name: str, batch_size: int = 100) -> pl.DataFrame:
        """
        Load a Polars DataFrame into a NocoDB table (bulk insert).
        
        Args:
            df: Polars DataFrame to insert
            table_name: Name of the target table (e.g., "Zone", "Actor")
            batch_size: Number of records to insert per batch (default: 100)
            
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
        
        # Insert in batches to avoid overwhelming the API
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            response = self.client.post(
                f"/api/v2/tables/{table_id}/records",
                json=batch
            )
            response.raise_for_status()
            for i, record in enumerate(response.json()):
                batch[i]["Id"] = record["Id"]
        return pl.DataFrame(records)
    
    def load_all_records(
        self,
        table_name: str,
        fields: Optional[List[str]] = None,
        condition: Optional[Dict[str, Any]] = None
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
        
        # If no fields specified, make initial call to get all fields
        if fields is None:
            # For now, we'll require fields to be specified
            raise ValueError("fields parameter is required for load_all_records")
        
        while True:
            batch = self.load_fields(
                table_name=table_name,
                fields=fields,
                condition=condition,
                limit=limit,
                offset=offset
            )
            
            if batch.is_empty():
                break
            
            all_records.append(batch)
            
            if len(batch) < limit:
                # Last page
                break
            
            offset += limit
        
        if not all_records:
            # Return empty DataFrame with correct schema
            schema = {}
            for field in fields:
                if field.lower() == 'id':
                    schema[field] = pl.Int64
                else:
                    schema[field] = pl.Utf8
            return pl.DataFrame(schema=schema)
        
        return pl.concat(all_records)
    
    def link_records(
        self,
        df: pl.DataFrame,
        table_name: str,
        link_field_name: str,
        foreign_key_column: str
    ) -> None:
        """
        Link records in a parent table to records in a related table.
        
        Args:
            df: DataFrame with 'Id' column (from insert_records()) and foreign key column
            table_name: Parent table name (e.g., "Actor")
            link_field_name: Exact link field name from swagger (e.g., "Zones")
            foreign_key_column: Column in df containing foreign key IDs (e.g., "Zone_id")
            
        Raises:
            ValueError: If table_name not in LINK_FIELD_IDS
            ValueError: If link_field_name not found for table
            ValueError: If "Id" column missing from dataframe
            ValueError: If foreign_key_column missing from dataframe
            httpx.HTTPError: If the API request fails
            
        Example:
            # After inserting actors, link them to their zones
            actors_df = db.insert_records(actors_df, "Actor")
            db.link_records(actors_df, "Actor", "Zones", "Zone_id")
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
        
        # Link each record
        for row in records_to_link.iter_rows(named=True):
            record_id = row["Id"]
            foreign_id = row[foreign_key_column]
            
            # POST to link endpoint
            response = self.client.post(
                f"/api/v2/tables/{table_id}/links/{link_field_id}/records/{record_id}",
                json=[{"Id": foreign_id}]
            )
            response.raise_for_status()
    
    def __del__(self):
        """Close the HTTP client when the object is destroyed."""
        if hasattr(self, 'client'):
            self.client.close()
