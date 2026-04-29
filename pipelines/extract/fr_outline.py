"""
Prefect workflow for extracting Outline regional CVM Excel exports.

Parses regional Excel files in ``data/raw/vcm_france/`` using DuckDB's
``excel`` extension and writes normalised rows into
``raw.outline_cvm_samples``.

Output columns:
  dept              – department code (str, e.g. "29", "2A")
  commune_name_raw  – original commune name from the file
  commune_name_norm – normalised for COG join (uppercase, no accents, spaces)
  plv_date          – sampling date (Python date)
  value_ugl         – CVM measurement in µg/L (float or None)
  source_file       – basename of the source Excel file

Column detection is fuzzy (accent-insensitive substring match) so the same
generic parser handles Bretagne / Normandie / Nouvelle-Aquitaine despite their
schema differences.
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional

import duckdb
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db


# ---------------------------------------------------------------------------
# Normalisation helpers (used both directly and as DuckDB UDFs)
# ---------------------------------------------------------------------------

def _remove_accents(text: str) -> str:
    """Remove diacritics (accents) from a string."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


_TRAILING_ARTICLES = re.compile(r"\s+\(L[AE]S?\)$", re.IGNORECASE)


def normalize_commune_name(name: Optional[str]) -> str:
    """Normalize a commune name for COG join.

    Steps:
    1. Strip surrounding whitespace
    2. Upper-case
    3. Remove accents
    4. Replace hyphens and apostrophes with spaces
    5. Remove trailing articles like " (LA)", " (LE)", " (LES)"
    6. Collapse multiple spaces
    """
    if not name:
        return ""
    name = str(name).strip().upper()
    name = _remove_accents(name)
    name = name.replace("-", " ").replace("'", " ").replace("\u2019", " ")
    name = _TRAILING_ARTICLES.sub("", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _norm_header(h: str) -> str:
    """Lowercase + accent-stripped header value, for fuzzy matching."""
    return _remove_accents(str(h)).lower().strip()


def _find_col(cols: list[str], candidates: list[str]) -> Optional[str]:
    """Return the first column whose normalised name contains any candidate."""
    for cand in candidates:
        cand_n = cand.lower()
        for c in cols:
            if cand_n in _norm_header(c):
                return c
    return None


def _qid(name: str) -> str:
    """Quote a DuckDB column identifier."""
    return '"' + name.replace('"', '""') + '"'


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _ensure_udf(conn: duckdb.DuckDBPyConnection) -> None:
    """Register the ``normalize_commune_name`` Python UDF on the connection.

    Safe to call more than once – re-registration is a no-op after the first.
    """
    try:
        conn.create_function(
            "normalize_commune_name", normalize_commune_name, ["VARCHAR"], "VARCHAR"
        )
    except (duckdb.CatalogException, duckdb.NotImplementedException, duckdb.InvalidInputException):
        # Already registered on this connection
        pass


def _list_sheets(path: Path) -> list[str]:
    """Return worksheet titles in workbook order.

    Uses openpyxl because DuckDB 1.5's ``excel`` extension doesn't expose a
    sheet-enumeration function; the cost is trivial (read-only metadata read).
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return [s.title for s in wb.worksheets]
    finally:
        wb.close()


def _detect_header_row(
    conn: duckdb.DuckDBPyConnection,
    path_str: str,
    sheet: str,
    scan_rows: int = 30,
) -> Optional[tuple[int, list[str]]]:
    """Scan the first *scan_rows* rows of *sheet* for a valid header row.

    A header row must contain all four required columns (dept, commune, date,
    value) detected by fuzzy substring match.  Returns
    ``(row_number_1_indexed, header_cells)`` or ``None``.
    """
    sheet_esc = sheet.replace("'", "''")
    sample = conn.execute(
        f"SELECT * FROM read_xlsx('{path_str}', sheet='{sheet_esc}', "
        f"header=false, all_varchar=true) LIMIT {scan_rows}"
    ).fetchall()

    for idx, row in enumerate(sample, start=1):
        cells = [str(c) if c is not None else "" for c in row]
        if (
            _find_col(cells, ["departement", "dept"])
            and _find_col(cells, ["commune"])
            and _find_col(cells, ["date"])
            and _find_col(cells, ["chlorure", "cvm", "valeur", "resultat"])
        ):
            return idx, cells
    return None


def parse_xlsx(conn: duckdb.DuckDBPyConnection, path: Path) -> list[dict]:
    """Parse an Outline xlsx file via DuckDB's excel extension.

    Iterates through every worksheet and auto-detects the header row (handles
    preamble rows).  Sheets must have all four required columns (dept,
    commune, date, value) detected by fuzzy substring match; sheets that
    don't match are silently skipped.  Files where no sheet matches return an
    empty list – callers should surface this as a warning.

    The dept column must contain numeric codes (e.g. ``'07'``, ``14``) or
    Corsica codes (``'2A'``, ``'2B'``); files with non-numeric dept columns
    (department names) are not supported and should be skipped upstream.
    """
    import math
    import pandas as pd

    _ensure_udf(conn)
    conn.execute("INSTALL excel; LOAD excel;")

    path_str = str(path).replace("'", "''")
    sheet_names = _list_sheets(path)

    all_records: list[dict] = []
    for sheet in sheet_names:
        hdr = _detect_header_row(conn, path_str, sheet)
        if hdr is None:
            continue
        hdr_row, cols = hdr

        dept_col = _find_col(cols, ["departement", "dept"])
        commune_col = _find_col(cols, ["commune"])
        date_col = _find_col(cols, ["date"])
        value_col = _find_col(cols, ["chlorure", "cvm", "valeur", "resultat"])
        # _detect_header_row guarantees commune/date/value are present.

        sheet_esc = sheet.replace("'", "''")
        # DuckDB range starts at header row; header=true consumes hdr_row as
        # the column labels and returns subsequent rows as data.
        read_expr = (
            f"read_xlsx('{path_str}', sheet='{sheet_esc}', "
            f"header=true, all_varchar=true, range='A{hdr_row}:ZZ1048576')"
        )

        # Dept normalisation: numeric → stripped of leading zeros / '.0';
        # otherwise keep upper-cased varchar (preserves Corsica 2A/2B).
        if dept_col:
            dept_expr = (
                f"COALESCE("
                f"  TRY_CAST(TRY_CAST({_qid(dept_col)} AS DOUBLE) AS BIGINT)::VARCHAR, "
                f"  trim(upper({_qid(dept_col)}))"
                f")"
            )
        else:
            dept_expr = "NULL"

        # Value normalisation: handle decimal-comma, '#EMPTY', '<0.5', '>X', N/A.
        value_expr = (
            f"TRY_CAST("
            f"  CASE "
            f"    WHEN {_qid(value_col)} IS NULL THEN NULL "
            f"    WHEN regexp_matches(trim({_qid(value_col)}), '^[<>]') THEN NULL "
            f"    WHEN upper(trim({_qid(value_col)})) IN ('#EMPTY','N/A','ND','') THEN NULL "
            f"    ELSE replace(trim({_qid(value_col)}), ',', '.') "
            f"  END "
            f"AS DOUBLE)"
        )

        sql = f"""
            SELECT
                {dept_expr}                              AS dept,
                trim({_qid(commune_col)})                AS commune_name_raw,
                normalize_commune_name(
                    trim({_qid(commune_col)})
                )                                        AS commune_name_norm,
                TRY_CAST({_qid(date_col)} AS DATE)       AS plv_date,
                {value_expr}                             AS value_ugl,
                '{path.name.replace("'", "''")}'         AS source_file
            FROM {read_expr}
            WHERE {_qid(commune_col)} IS NOT NULL
        """
        df = conn.execute(sql).fetchdf()
        if dept_col:
            df = df[df["dept"].notna() & (df["dept"].astype(str).str.len() > 0)]

            # Sanity-check dept values: INSEE codes are numeric (optionally with
            # 2A/2B for Corsica).  If the column holds department names (e.g.
            # 'AIN', 'ALLIER') instead, bail on this sheet – we cannot link
            # back to communes without a numeric dept.
            if len(df) > 0:
                sample = df["dept"].astype(str).head(50)
                numeric_like = sample.str.match(r"^(\d+|2[AB])$", case=False)
                if numeric_like.mean() < 0.5:
                    # Return a signal to caller via exception-free side channel:
                    # we simply drop the sheet's rows.  The empty result for
                    # the file triggers the caller's skip-with-warning.
                    continue

        # pandas NaN → None, Timestamp → datetime.date for clean downstream use.
        for r in df.to_dict(orient="records"):
            clean = {}
            for k, v in r.items():
                if v is None:
                    clean[k] = None
                elif isinstance(v, float) and math.isnan(v):
                    clean[k] = None
                elif isinstance(v, pd.Timestamp):
                    clean[k] = v.date() if not pd.isna(v) else None
                else:
                    clean[k] = v
            all_records.append(clean)

    return all_records


# ---------------------------------------------------------------------------
# Prefect tasks / flow
# ---------------------------------------------------------------------------

@task(name="extract_fr_outline_parse", cache_policy=NO_CACHE)
def parse_outline_files(data_directory: Path) -> list[dict]:
    """Parse all Outline Excel files in ``data/raw/vcm_france/``."""
    logger = get_run_logger()
    vcm_dir = data_directory / "raw" / "vcm_france"
    if not vcm_dir.exists():
        logger.warning(f"Directory {vcm_dir} does not exist; no Outline files parsed")
        return []

    xlsx_files = sorted(vcm_dir.glob("*.xlsx"))
    if not xlsx_files:
        logger.warning(f"No .xlsx files found in {vcm_dir}")
        return []

    # Throw-away in-memory connection for the xlsx reads
    conn = duckdb.connect()
    try:
        all_rows: list[dict] = []
        skipped: list[str] = []
        for xlsx in xlsx_files:
            logger.info(f"Parsing {xlsx.name} …")
            try:
                rows = parse_xlsx(conn, xlsx)
            except Exception as exc:
                # Unexpected failure (corrupt xlsx, I/O error) – re-raise so
                # the pipeline fails loudly.  Structural mismatches are
                # signalled via an empty result, not an exception.
                logger.error(f"  ✗ Failed to parse {xlsx.name}: {exc}")
                raise
            if not rows:
                logger.warning(
                    f"  ⚠ Skipped {xlsx.name}: no sheet with a recognisable header "
                    f"(expected dept + commune + date + value columns with numeric "
                    f"dept codes)."
                )
                skipped.append(xlsx.name)
                continue
            logger.info(f"  → {len(rows)} rows from {xlsx.name}")
            all_rows.extend(rows)
    finally:
        conn.close()

    if skipped:
        logger.warning(
            f"Outline extract: skipped {len(skipped)} file(s) with unsupported "
            f"structure: {skipped}"
        )
    logger.info(f"Total Outline rows: {len(all_rows)}")
    return all_rows


@task(name="extract_fr_outline_write", cache_policy=NO_CACHE)
def write_outline_samples(conn, rows: list[dict]) -> None:
    """Write parsed rows into ``raw.outline_cvm_samples``."""
    staging_db.write_table(conn, "outline_cvm_samples", rows, schema="raw")


@flow(name="extract_fr_outline", persist_result=False)
def extract_fr_outline(data_directory: Path = Path("data")) -> None:
    """Extract Outline CVM samples into ``raw.outline_cvm_samples``."""
    rows = parse_outline_files(data_directory)
    conn = staging_db.get_connection(data_directory)
    try:
        write_outline_samples(conn, rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    data_directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    extract_fr_outline(data_directory)
