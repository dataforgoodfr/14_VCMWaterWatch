"""
Import water company data from NocoDB staging table.

Reads rows from Water Company Import (ImportStatus = Pending or unset), validates each row,
creates DistributionZone and WaterCompany NDJSON files, runs load_zones and load_water_companies,
and updates ImportStatus/ImportError on staging rows.

See docs/plans/import-water-company-from-nocodb-staging.md for full specification.
"""

import os
from pathlib import Path

import polars as pl
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services
from pipelines.common.db_helper import DatabaseHelper
from pipelines.load.load_zones import load_zones_flow
from pipelines.load.load_water_companies import load_water_companies

STAGING_TABLE = os.getenv("WATER_COMPANY_IMPORT_TABLE", "Water Company Import")


def _parse_municipalities(raw: str | None) -> list[str]:
    """Parse comma-separated municipalities, trim each."""
    if not raw or not str(raw).strip():
        return []
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def _load_reference_data(db: DatabaseHelper) -> dict[str, pl.DataFrame]:
    """Load Country, Municipality, DistributionZone, Actor once for validation."""
    _debug("_load_reference_data: loading Country, Municipality, DistributionZone, Actor...")
    ref = {
        "Country": db.load_all_records(
            table_name="Country", fields=["Code", "Name"]
        ),
        "Municipality": db.load_all_records(
            table_name="Municipality", fields=["Code", "Name"]
        ),
        "DistributionZone": db.load_all_records(
            table_name="DistributionZone", fields=["Code", "Name"]
        ),
        "Actor": db.load_all_records(
            table_name="Actor",
            fields=["Name"],
            condition={"Type": "Water Company"},
        ),
    }
    _debug(f"_load_reference_data: done (Country={len(ref['Country'])}, Municipality={len(ref['Municipality'])}, ...)")
    return ref


def _validate_country(
    ref: dict[str, pl.DataFrame], country_name: str | None
) -> tuple[str | None, str | None]:
    """
    Lookup Country by Name; return (CountryCode, error_msg).
    If not found, return (None, error_msg).
    """
    if not country_name or not str(country_name).strip():
        return None, "Country is required"
    name = str(country_name).strip()
    countries = ref["Country"]
    match = countries.filter(pl.col("Name").str.to_lowercase() == name.lower())
    if match.is_empty():
        return None, f"Country '{name}' not found"
    return match["Code"][0], None


def _validate_municipalities(
    ref: dict[str, pl.DataFrame],
    municipalities_raw: str | None,
    country_code: str | None,
) -> tuple[list[str], str | None]:
    """
    Parse municipalities, lookup each by Name OR Code in Municipality table.
    Return (list of Municipality.Code, error_msg).
    If any fail to match, return ([], error_msg).
    """
    names = _parse_municipalities(municipalities_raw)
    if not names:
        return [], "Municipalities is required"
    munis = ref["Municipality"]
    if munis.is_empty():
        return [], "No municipalities in database"
    codes = []
    for n in names:
        n_clean = n.strip()
        match = munis.filter(
            (pl.col("Name").str.to_lowercase() == n_clean.lower())
            | (pl.col("Code").str.to_lowercase() == n_clean.lower())
        )
        if match.is_empty():
            return [], f"Municipality '{n}' not found"
        codes.append(match["Code"][0])
    return codes, None


def _check_duplicates(
    ref: dict[str, pl.DataFrame],
    company_name: str,
    country_code: str | None,
) -> tuple[bool, str | None]:
    """
    Check DistributionZone (Code, Name) and Actor (Name, Type=Water Company).
    Return (is_duplicate, error_msg). If duplicate, error_msg describes which.
    """
    if not company_name or not str(company_name).strip():
        return True, "Company Name is required"
    name = str(company_name).strip()
    zones = ref["DistributionZone"]
    zone_match = zones.filter(
        (pl.col("Code").str.to_lowercase() == name.lower())
        | (pl.col("Name").str.to_lowercase() == name.lower())
    )
    if not zone_match.is_empty():
        return True, f"Distribution zone '{name}' already exists"
    actors = ref["Actor"]
    actor_match = actors.filter(pl.col("Name").str.to_lowercase() == name.lower())
    if not actor_match.is_empty():
        return True, f"Water company '{name}' already exists"
    return False, None


def _debug(msg: str) -> None:
    """Print debug message with immediate flush for visibility during hangs."""
    print(f"[DEBUG] {msg}", flush=True)


@task(name="read_staging_rows", cache_policy=NO_CACHE)
def read_staging_rows_task(db: DatabaseHelper) -> pl.DataFrame:
    """Load all rows from Water Company Import, filter to Pending or unset."""
    _debug("read_staging_rows: starting")
    if STAGING_TABLE not in db.table_ids:
        raise ValueError(
            f"Staging table '{STAGING_TABLE}' not found in NocoDB. "
            "Create it via Noco UI (see docs/plans/import-water-company-from-nocodb-staging.md)."
        )
    _debug(f"read_staging_rows: fetching from {STAGING_TABLE} (may paginate)...")
    all_rows = db.load_all_records(
        table_name=STAGING_TABLE,
        fields=[
            "Id",
            "Company Name",
            "Country",
            "Municipalities",
            "Email",
            "Phone",
            "Website",
            "ImportError",
            "ImportStatus",
        ],
    )
    _debug(f"read_staging_rows: got {len(all_rows)} total rows")
    if all_rows.is_empty():
        return all_rows
    pending = all_rows.filter(
        pl.col("ImportStatus").is_null()
        | (pl.col("ImportStatus").cast(pl.Utf8) == "")
        | (pl.col("ImportStatus").cast(pl.Utf8) == "Pending")
    )
    _debug(f"read_staging_rows: {len(pending)} pending rows")
    return pending


@task(name="validate_and_split_rows", cache_policy=NO_CACHE)
def validate_and_split_rows_task(
    df: pl.DataFrame, db: DatabaseHelper
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Validate each row. Return (valid_rows, failed_rows).
    valid_rows have: Id, Company Name, CountryCode, Municipalities (list of codes),
    Email, Phone, Website, and other fields needed for NDJSON.
    failed_rows have: Id, ImportError, ImportStatus='Failed'
    """
    if df.is_empty():
        return df, pl.DataFrame(schema={"Id": pl.Int64, "ImportError": pl.Utf8, "ImportStatus": pl.Utf8})
    ref = _load_reference_data(db)
    valid_rows = []
    failed_rows = []
    total = len(df)
    _debug(f"validate_and_split_rows: validating {total} rows")
    for i, row in enumerate(df.iter_rows(named=True)):
        _debug(f"validate_and_split_rows: row {i+1}/{total} (Id={row.get('Id')})")
        row_id = row.get("Id")
        company_name = row.get("Company Name")
        country_name = row.get("Country")
        municipalities_raw = row.get("Municipalities")
        country_code, country_err = _validate_country(ref, country_name)
        if country_err:
            failed_rows.append(
                {"Id": row_id, "ImportError": country_err, "ImportStatus": "Failed"}
            )
            continue
        muni_codes, muni_err = _validate_municipalities(
            ref, municipalities_raw, country_code
        )
        if muni_err:
            failed_rows.append(
                {"Id": row_id, "ImportError": muni_err, "ImportStatus": "Failed"}
            )
            continue
        is_dup, dup_err = _check_duplicates(ref, company_name, country_code)
        if is_dup:
            failed_rows.append(
                {"Id": row_id, "ImportError": dup_err, "ImportStatus": "Failed"}
            )
            continue
        valid_rows.append(
            {
                "Id": row_id,
                "Company Name": company_name,
                "CountryCode": country_code,
                "Municipalities": muni_codes,
                "Email": row.get("Email") or "",
                "Phone": row.get("Phone") or "",
                "Website": row.get("Website") or "",
            }
        )
    valid_df = pl.DataFrame(valid_rows) if valid_rows else pl.DataFrame()
    failed_df = pl.DataFrame(failed_rows) if failed_rows else pl.DataFrame()
    _debug(f"validate_and_split_rows: done {len(valid_rows)} valid, {len(failed_rows)} failed")
    return valid_df, failed_df


@task(name="write_ndjson_and_load", cache_policy=NO_CACHE)
def write_ndjson_and_load_task(
    valid_df: pl.DataFrame, data_dir: Path
) -> None:
    """
    Build DistributionZone and WaterCompany NDJSON, write to data_dir/staging,
    run load_zones DistributionZone, run load_water_companies.
    """
    if valid_df.is_empty():
        return
    _debug("write_ndjson_and_load: starting")
    staging_dir = data_dir / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    dist_zones = valid_df.select(
        pl.col("Company Name").alias("Code"),
        pl.col("Company Name").alias("Name"),
        pl.col("CountryCode"),
        pl.col("Municipalities"),
    )
    water_companies = valid_df.select(
        pl.col("CountryCode"),
        pl.col("Company Name").alias("Name"),
        pl.col("Email"),
        pl.col("Phone"),
        pl.col("Website"),
        pl.lit("").alias("Description"),
        (pl.lit("NocoDB Import (") + pl.col("Id").cast(pl.Utf8) + pl.lit(")")).alias("Source"),
    )
    dist_zones.write_ndjson(staging_dir / "DistributionZone_import.ndjson")
    water_companies.write_ndjson(staging_dir / "WaterCompany_import.ndjson")
    _debug("write_ndjson_and_load: starting load_zones DistributionZone...")
    load_zones_flow(level="DistributionZone", data_directory=staging_dir)
    _debug("write_ndjson_and_load: starting load_water_companies...")
    load_water_companies(data_path=staging_dir)
    _debug("write_ndjson_and_load: done")


@task(name="update_staging_status", cache_policy=NO_CACHE)
def update_staging_status_task(
    db: DatabaseHelper,
    failed_df: pl.DataFrame,
    success_ids: list[int],
) -> None:
    """Update ImportError and ImportStatus on staging rows."""
    _debug(f"update_staging_status: {len(failed_df)} failed, {len(success_ids)} success")
    if not failed_df.is_empty():
        update_df = failed_df.select(["Id", "ImportError", "ImportStatus"])
        db.update_records(update_df, table_name=STAGING_TABLE)
    if success_ids:
        success_df = pl.DataFrame({
            "Id": success_ids,
            "ImportError": [""] * len(success_ids),
            "ImportStatus": ["Success"] * len(success_ids),
        })
        db.update_records(success_df, table_name=STAGING_TABLE)


@flow(name="import_water_companies_from_staging", persist_result=False)
def import_water_companies_from_staging_flow(data_dir: Path | None = None) -> None:
    """
    Main pipeline: read staging → validate → write NDJSON → load → update status.
    """
    logger = get_run_logger()
    _debug("flow: starting")
    data_directory = data_dir or Path(os.getenv("DATA_DIR", "data"))
    _debug(f"flow: data_dir={data_directory}")
    db = services.db_helper()
    _debug("flow: db_helper created")
    df = read_staging_rows_task(db)
    _debug("flow: read_staging_rows done")
    if df.is_empty():
        logger.info("No pending rows in staging table")
        return
    logger.info(f"Processing {len(df)} pending rows")
    _debug("flow: starting validate_and_split_rows")
    valid_df, failed_df = validate_and_split_rows_task(df, db)
    _debug("flow: validate_and_split_rows done")
    if not failed_df.is_empty():
        logger.info(f"Validation failed for {len(failed_df)} rows")
        update_staging_status_task(db, failed_df, [])
    if valid_df.is_empty():
        return
    _debug("flow: starting write_ndjson_and_load")
    write_ndjson_and_load_task(valid_df, data_directory)
    _debug("flow: write_ndjson_and_load done")
    success_ids = valid_df["Id"].to_list()
    update_staging_status_task(db, pl.DataFrame(), success_ids)
    logger.info(f"Successfully imported {len(success_ids)} rows")


if __name__ == "__main__":
    import sys

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    import_water_companies_from_staging_flow(data_dir=data_dir)
