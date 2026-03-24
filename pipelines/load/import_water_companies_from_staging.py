"""
Import water company data from NocoDB staging table.

Reads rows from Water Company Import (ImportStatus = Pending or unset), validates each row,
writes DistributionZone and WaterCompany to staging DB, runs load_zones and load_water_companies,
and updates ImportStatus/ImportError on staging rows.
"""

import os
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import services, staging_db
from pipelines.common.db_helper import DatabaseHelper
from pipelines.load.load_zones import load_zones_flow
from pipelines.load.load_water_companies import load_water_companies

STAGING_TABLE = os.getenv("WATER_COMPANY_IMPORT_TABLE", "Water Company Import")


def _parse_municipalities(raw: str | None) -> list[str]:
    """Parse comma-separated municipalities, trim each."""
    if not raw or not str(raw).strip():
        return []
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def _load_reference_data(db: DatabaseHelper) -> dict[str, list[dict]]:
    """Load Country, Municipality, DistributionZone, Actor once for validation."""
    _debug("_load_reference_data: loading Country, Municipality, DistributionZone, Actor...")
    ref = {
        "Country": db.load_all_records(table_name="Country", fields=["Code", "Name"]),
        "Municipality": db.load_all_records(table_name="Municipality", fields=["Code", "Name"]),
        "DistributionZone": db.load_all_records(table_name="DistributionZone", fields=["Code", "Name"]),
        "Actor": db.load_all_records(
            table_name="Actor", fields=["Name"], condition={"Type": "Water Company"}
        ),
    }
    _debug(f"_load_reference_data: done (Country={len(ref['Country'])}, Municipality={len(ref['Municipality'])}, ...)")
    return ref


def _validate_country(
    ref: dict[str, list[dict]], country_name: str | None
) -> tuple[str | None, str | None]:
    if not country_name or not str(country_name).strip():
        return None, "Country is required"
    name = str(country_name).strip()
    for r in ref["Country"]:
        if r.get("Name", "").lower() == name.lower():
            return r["Code"], None
    return None, f"Country '{name}' not found"


def _validate_municipalities(
    ref: dict[str, list[dict]],
    municipalities_raw: str | None,
    country_code: str | None,
) -> tuple[list[str], str | None]:
    names = _parse_municipalities(municipalities_raw)
    if not names:
        return [], "Municipalities is required"
    munis = ref["Municipality"]
    if not munis:
        return [], "No municipalities in database"
    codes = []
    for n in names:
        n_clean = n.strip()
        match = None
        for r in munis:
            if (r.get("Name", "").lower() == n_clean.lower()
                    or r.get("Code", "").lower() == n_clean.lower()):
                match = r
                break
        if not match:
            return [], f"Municipality '{n}' not found"
        codes.append(match["Code"])
    return codes, None


def _check_duplicates(
    ref: dict[str, list[dict]],
    company_name: str,
    country_code: str | None,
) -> tuple[bool, str | None]:
    if not company_name or not str(company_name).strip():
        return True, "Company Name is required"
    name = str(company_name).strip()
    for r in ref["DistributionZone"]:
        if (r.get("Code", "").lower() == name.lower()
                or r.get("Name", "").lower() == name.lower()):
            return True, f"Distribution zone '{name}' already exists"
    for r in ref["Actor"]:
        if r.get("Name", "").lower() == name.lower():
            return True, f"Water company '{name}' already exists"
    return False, None


def _debug(msg: str) -> None:
    print(f"[DEBUG] {msg}", flush=True)


@task(name="read_staging_rows", cache_policy=NO_CACHE)
def read_staging_rows_task(db: DatabaseHelper) -> list[dict]:
    """Load all rows from Water Company Import, filter to Pending or unset."""
    _debug("read_staging_rows: starting")
    if STAGING_TABLE not in db.table_ids:
        raise ValueError(
            f"Staging table '{STAGING_TABLE}' not found in NocoDB. "
            "Create it via Noco UI."
        )
    _debug(f"read_staging_rows: fetching from {STAGING_TABLE} (may paginate)...")
    all_rows = db.load_all_records(
        table_name=STAGING_TABLE,
        fields=[
            "Id", "Company Name", "Country", "Municipalities",
            "Email", "Phone", "Website", "ImportError", "ImportStatus",
        ],
    )
    _debug(f"read_staging_rows: got {len(all_rows)} total rows")
    if not all_rows:
        return []
    pending = [
        r for r in all_rows
        if not r.get("ImportStatus") or str(r["ImportStatus"]).strip() == ""
        or str(r["ImportStatus"]).strip() == "Pending"
    ]
    _debug(f"read_staging_rows: {len(pending)} pending rows")
    return pending


@task(name="validate_and_split_rows", cache_policy=NO_CACHE)
def validate_and_split_rows_task(
    records: list[dict], db: DatabaseHelper
) -> tuple[list[dict], list[dict]]:
    """
    Validate each row. Return (valid_rows, failed_rows).
    """
    if not records:
        return [], []
    ref = _load_reference_data(db)
    valid_rows = []
    failed_rows = []
    total = len(records)
    _debug(f"validate_and_split_rows: validating {total} rows")
    for i, row in enumerate(records):
        _debug(f"validate_and_split_rows: row {i+1}/{total} (Id={row.get('Id')})")
        row_id = row.get("Id")
        company_name = row.get("Company Name")
        country_name = row.get("Country")
        municipalities_raw = row.get("Municipalities")
        country_code, country_err = _validate_country(ref, country_name)
        if country_err:
            failed_rows.append({"Id": row_id, "ImportError": country_err, "ImportStatus": "Failed"})
            continue
        muni_codes, muni_err = _validate_municipalities(ref, municipalities_raw, country_code)
        if muni_err:
            failed_rows.append({"Id": row_id, "ImportError": muni_err, "ImportStatus": "Failed"})
            continue
        is_dup, dup_err = _check_duplicates(ref, company_name, country_code)
        if is_dup:
            failed_rows.append({"Id": row_id, "ImportError": dup_err, "ImportStatus": "Failed"})
            continue
        valid_rows.append({
            "Id": row_id,
            "Company Name": company_name,
            "CountryCode": country_code,
            "Municipalities": muni_codes,
            "Email": row.get("Email") or "",
            "Phone": row.get("Phone") or "",
            "Website": row.get("Website") or "",
        })
    _debug(f"validate_and_split_rows: done {len(valid_rows)} valid, {len(failed_rows)} failed")
    return valid_rows, failed_rows


@task(name="write_staging_and_load", cache_policy=NO_CACHE)
def write_staging_and_load_task(
    valid_records: list[dict], data_dir: Path
) -> None:
    """
    Build DistributionZone and WaterCompany records, write to staging DB,
    run load_zones DistributionZone, run load_water_companies.
    """
    if not valid_records:
        return
    _debug("write_staging_and_load: starting")

    dist_zones = [
        {
            "Code": r["Company Name"],
            "Name": r["Company Name"],
            "CountryCode": r["CountryCode"],
            "Municipalities": r["Municipalities"],
        }
        for r in valid_records
    ]
    water_companies = [
        {
            "CountryCode": r["CountryCode"],
            "Name": r["Company Name"],
            "Email": r["Email"],
            "Phone": r["Phone"],
            "Website": r["Website"],
            "Description": "",
            "Source": f"NocoDB Import ({r['Id']})",
        }
        for r in valid_records
    ]

    conn = staging_db.get_connection(data_dir)
    try:
        staging_db.write_table(conn, "DistributionZone_import", dist_zones, schema="staging")
        staging_db.write_table(conn, "WaterCompany_import", water_companies, schema="staging")
    finally:
        conn.close()

    _debug("write_staging_and_load: starting load_zones DistributionZone...")
    load_zones_flow(level="DistributionZone", data_directory=data_dir)
    _debug("write_staging_and_load: starting load_water_companies...")
    load_water_companies(data_dir=data_dir)
    _debug("write_staging_and_load: done")


@task(name="update_staging_status", cache_policy=NO_CACHE)
def update_staging_status_task(
    db: DatabaseHelper,
    failed_records: list[dict],
    success_ids: list[int],
) -> None:
    """Update ImportError and ImportStatus on staging rows."""
    _debug(f"update_staging_status: {len(failed_records)} failed, {len(success_ids)} success")
    if failed_records:
        db.update_records(
            [{"Id": r["Id"], "ImportError": r["ImportError"], "ImportStatus": r["ImportStatus"]}
             for r in failed_records],
            table_name=STAGING_TABLE,
        )
    if success_ids:
        success_records = [
            {"Id": sid, "ImportError": "", "ImportStatus": "Success"}
            for sid in success_ids
        ]
        db.update_records(success_records, table_name=STAGING_TABLE)


@flow(name="import_water_companies_from_staging", persist_result=False)
def import_water_companies_from_staging_flow(data_dir: Path | None = None) -> None:
    """
    Main pipeline: read staging → validate → write to staging DB → load → update status.
    """
    logger = get_run_logger()
    _debug("flow: starting")
    data_directory = data_dir or Path(os.getenv("DATA_DIR", "data"))
    _debug(f"flow: data_dir={data_directory}")
    db = services.db_helper()
    _debug("flow: db_helper created")
    records = read_staging_rows_task(db)
    _debug("flow: read_staging_rows done")
    if not records:
        logger.info("No pending rows in staging table")
        return
    logger.info(f"Processing {len(records)} pending rows")
    _debug("flow: starting validate_and_split_rows")
    valid_records, failed_records = validate_and_split_rows_task(records, db)
    _debug("flow: validate_and_split_rows done")
    if failed_records:
        logger.info(f"Validation failed for {len(failed_records)} rows")
        update_staging_status_task(db, failed_records, [])
    if not valid_records:
        return
    _debug("flow: starting write_staging_and_load")
    write_staging_and_load_task(valid_records, data_directory)
    _debug("flow: write_staging_and_load done")
    success_ids = [r["Id"] for r in valid_records]
    update_staging_status_task(db, [], success_ids)
    logger.info(f"Successfully imported {len(success_ids)} rows")


if __name__ == "__main__":
    import sys

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    import_water_companies_from_staging_flow(data_dir=data_dir)
