"""
Prefect workflow for extracting Outline regional CVM Excel exports.

Parses three regional Excel files (Bretagne, Normandie, Nouvelle-Aquitaine) and
writes normalised rows into ``raw.outline_cvm_samples``.

Output columns:
  dept              – department code (str, e.g. "29", "2A")
  commune_name_raw  – original commune name from the file
  commune_name_norm – normalised for COG join (uppercase, no accents, spaces)
  plv_date          – sampling date (Python date)
  value_ugl         – CVM measurement in µg/L (float or None)
  source_file       – basename of the source Excel file
"""

import datetime
import re
import unicodedata
from pathlib import Path
from typing import Optional

import openpyxl
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from pipelines.common import staging_db


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _remove_accents(text: str) -> str:
    """Remove diacritics (accents) from a string."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


_TRAILING_ARTICLES = re.compile(
    r"\s+\(L[AE]S?\)$", re.IGNORECASE
)


def normalize_commune_name(name: str) -> str:
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
    name = name.strip().upper()
    name = _remove_accents(name)
    name = name.replace("-", " ").replace("'", " ").replace("\u2019", " ")
    name = _TRAILING_ARTICLES.sub("", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _parse_value(raw) -> Optional[float]:
    """Parse a CVM measurement value.

    - ``#EMPTY``, blank, None → None
    - ``<0.5``-style strings → None (below detection limit, treated as no
      quantifiable measurement; callers may choose to map to 0.0 instead)
    - Decimal-comma strings like ``"0,12"`` → 0.12
    - Numeric types returned as-is.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    if not s or s.upper() in ("#EMPTY", "N/A", "ND"):
        return None
    if s.startswith("<") or s.startswith(">"):
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Per-region parsers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase + remove accents for fuzzy header matching."""
    return _remove_accents(text.strip().lower())


def _find_header_row(ws, candidates: list[str]) -> int:
    """Return the 1-based row index where all candidates appear as substrings
    of at least one cell value (accent-insensitive)."""
    for row in ws.iter_rows():
        cell_values = [
            _normalize(str(c.value)) for c in row if c.value is not None
        ]
        if all(
            any(cand.lower() in cv for cv in cell_values)
            for cand in candidates
        ):
            return row[0].row
    raise ValueError(
        f"Could not find header row containing {candidates} in sheet '{ws.title}'"
    )


def _col_index(ws, header_row: int, name: str) -> int:
    """Return the 1-based column index for *name* (substring, accent-insensitive)
    in *header_row*."""
    name_norm = _normalize(name)
    for cell in ws[header_row]:
        if cell.value and name_norm in _normalize(str(cell.value)):
            return cell.column
    raise ValueError(f"Column '{name}' not found in header row {header_row}")


def _parse_bretagne(path: Path) -> list[dict]:
    """Parse Annexe C (Bretagne).xlsx."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows: list[dict] = []
    for sheet in wb.worksheets:
        try:
            hr = _find_header_row(sheet, ["departement", "commune", "date"])
        except ValueError:
            continue
        dept_col = _col_index(sheet, hr, "departement")
        commune_col = _col_index(sheet, hr, "commune")
        date_col = _col_index(sheet, hr, "date")
        # CVM column – try a few variants
        cvm_col = None
        for candidate in ["cvm (µg/l)", "cvm (ug/l)", "cvm", "valeur (µg/l)", "valeur", "chlorure", "resultat"]:
            try:
                cvm_col = _col_index(sheet, hr, candidate)
                break
            except ValueError:
                pass
        if cvm_col is None:
            continue

        for row in sheet.iter_rows(min_row=hr + 1, values_only=True):
            dept_raw = row[dept_col - 1]
            commune_raw = row[commune_col - 1]
            date_raw = row[date_col - 1]
            value_raw = row[cvm_col - 1]

            if dept_raw is None and commune_raw is None:
                continue
            dept = str(dept_raw).strip().lstrip("0") if dept_raw else None
            # Dept codes like "029" → "29"; keep "2A", "2B" as-is
            if dept and dept.isdigit():
                dept = str(int(dept))
            commune = str(commune_raw).strip() if commune_raw else None
            if not dept or not commune:
                continue

            if isinstance(date_raw, datetime.datetime):
                plv_date = date_raw.date()
            elif isinstance(date_raw, datetime.date):
                plv_date = date_raw
            else:
                # Try parsing string
                try:
                    plv_date = datetime.date.fromisoformat(str(date_raw).strip())
                except (ValueError, TypeError):
                    plv_date = None

            rows.append({
                "dept": dept,
                "commune_name_raw": commune,
                "commune_name_norm": normalize_commune_name(commune),
                "plv_date": plv_date,
                "value_ugl": _parse_value(value_raw),
                "source_file": path.name,
            })
    wb.close()
    return rows


def _parse_normandie(path: Path) -> list[dict]:
    """Parse Annexe F (Normandie).xlsx.

    Normandie sheets can have département in the sheet name or a column.
    """
    return _parse_generic(path, dept_col_hint="departement")


def _parse_nouvelle_aquitaine(path: Path) -> list[dict]:
    """Parse Annexe G (Nouvelle-Aquitaine).xlsx."""
    return _parse_generic(path, dept_col_hint="departement")


def _parse_generic(path: Path, dept_col_hint: str = "departement") -> list[dict]:
    """Generic parser for regions where the schema is similar to Bretagne."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows: list[dict] = []
    for sheet in wb.worksheets:
        try:
            hr = _find_header_row(sheet, ["commune", "date"])
        except ValueError:
            continue

        # dept may come from a column or the sheet title
        dept_col = None
        for dept_hint in [dept_col_hint, "dept"]:
            try:
                dept_col = _col_index(sheet, hr, dept_hint)
                sheet_dept = None
                break
            except ValueError:
                pass
        if dept_col is None:
            # Try to extract dept from sheet name e.g. "Dept 14" or "14"
            m = re.search(r"\b(\d{1,2}[aAbB]?)\b", sheet.title)
            sheet_dept = m.group(1) if m else None

        try:
            commune_col = _col_index(sheet, hr, "commune")
        except ValueError:
            continue
        try:
            date_col = _col_index(sheet, hr, "date")
        except ValueError:
            continue
        cvm_col = None
        for candidate in ["cvm (µg/l)", "cvm (ug/l)", "cvm", "valeur (µg/l)", "valeur", "chlorure", "resultat"]:
            try:
                cvm_col = _col_index(sheet, hr, candidate)
                break
            except ValueError:
                pass
        if cvm_col is None:
            continue

        for row in sheet.iter_rows(min_row=hr + 1, values_only=True):
            commune_raw = row[commune_col - 1]
            date_raw = row[date_col - 1]
            value_raw = row[cvm_col - 1]

            if dept_col is not None:
                dept_raw = row[dept_col - 1]
                dept = str(dept_raw).strip().lstrip("0") if dept_raw else None
                if dept and dept.isdigit():
                    dept = str(int(dept))
            else:
                dept = sheet_dept

            commune = str(commune_raw).strip() if commune_raw else None
            if not dept or not commune:
                continue

            if isinstance(date_raw, datetime.datetime):
                plv_date = date_raw.date()
            elif isinstance(date_raw, datetime.date):
                plv_date = date_raw
            else:
                try:
                    plv_date = datetime.date.fromisoformat(str(date_raw).strip())
                except (ValueError, TypeError):
                    plv_date = None

            rows.append({
                "dept": dept,
                "commune_name_raw": commune,
                "commune_name_norm": normalize_commune_name(commune),
                "plv_date": plv_date,
                "value_ugl": _parse_value(value_raw),
                "source_file": path.name,
            })
    wb.close()
    return rows


# Dispatch table keyed by lower-case filename stem patterns
_PARSERS = {
    "bretagne": _parse_bretagne,
    "normandie": _parse_normandie,
    "nouvelle-aquitaine": _parse_nouvelle_aquitaine,
    "aquitaine": _parse_nouvelle_aquitaine,  # shortened variant
}


def _choose_parser(path: Path):
    stem = path.stem.lower()
    for key, fn in _PARSERS.items():
        if key in stem:
            return fn
    # Default fallback
    return _parse_generic


# ---------------------------------------------------------------------------
# Prefect tasks / flow
# ---------------------------------------------------------------------------

@task(name="extract_fr_outline_parse", cache_policy=NO_CACHE)
def parse_outline_files(data_directory: Path) -> list[dict]:
    """Parse all Outline Excel files in data/raw/vcm_france/."""
    logger = get_run_logger()
    vcm_dir = data_directory / "raw" / "vcm_france"
    if not vcm_dir.exists():
        logger.warning(f"Directory {vcm_dir} does not exist; no Outline files parsed")
        return []

    all_rows: list[dict] = []
    xlsx_files = sorted(vcm_dir.glob("*.xlsx"))
    if not xlsx_files:
        logger.warning(f"No .xlsx files found in {vcm_dir}")
        return []

    for xlsx in xlsx_files:
        logger.info(f"Parsing {xlsx.name} …")
        parser = _choose_parser(xlsx)
        try:
            rows = parser(xlsx)
            logger.info(f"  → {len(rows)} rows from {xlsx.name}")
            all_rows.extend(rows)
        except Exception as exc:
            logger.error(f"  ✗ Failed to parse {xlsx.name}: {exc}")
            raise

    logger.info(f"Total Outline rows: {len(all_rows)}")
    return all_rows


@task(name="extract_fr_outline_write", cache_policy=NO_CACHE)
def write_outline_samples(conn, rows: list[dict]) -> None:
    """Write parsed rows into raw.outline_cvm_samples."""
    staging_db.write_table(conn, "outline_cvm_samples", rows, schema="raw")


@flow(name="extract_fr_outline", persist_result=False)
def extract_fr_outline(data_directory: Path = Path("data")) -> None:
    """Extract Outline CVM samples into raw.outline_cvm_samples."""
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
