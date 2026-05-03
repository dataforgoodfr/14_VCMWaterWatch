"""Tests for pipelines/extract/fr_outline.py"""

import datetime
from pathlib import Path

import duckdb
import pytest

from pipelines.extract.fr_outline import (
    normalize_commune_name,
    parse_xlsx,
)


# ---------------------------------------------------------------------------
# Unit tests: normalize_commune_name
# ---------------------------------------------------------------------------

def test_normalize_basic():
    assert normalize_commune_name("Saint-Malo") == "SAINT MALO"


def test_normalize_accents():
    assert normalize_commune_name("Évreux") == "EVREUX"


def test_normalize_trailing_la():
    assert normalize_commune_name("Chapelle (LA)") == "CHAPELLE"


def test_normalize_trailing_les():
    assert normalize_commune_name("Sables (LES)") == "SABLES"


def test_normalize_trailing_le():
    assert normalize_commune_name("Havre (LE)") == "HAVRE"


def test_normalize_apostrophe():
    assert normalize_commune_name("L'Isle-Adam") == "L ISLE ADAM"


def test_normalize_collapse_spaces():
    assert normalize_commune_name("  Saint  Pierre  ") == "SAINT PIERRE"


def test_normalize_none():
    assert normalize_commune_name(None) == ""


def test_normalize_empty():
    assert normalize_commune_name("") == ""


# ---------------------------------------------------------------------------
# Synthetic xlsx helpers (using DuckDB's excel extension; no openpyxl)
# ---------------------------------------------------------------------------

def _write_xlsx(conn: duckdb.DuckDBPyConnection, path: Path, headers: list[str],
                rows: list[tuple]) -> Path:
    """Write a synthetic xlsx at *path* with *headers* and *rows*.

    Values are inserted as VARCHAR and dates as DATE literals; DuckDB's
    COPY ... TO 'foo.xlsx' produces a real Excel file.
    """
    conn.execute("INSTALL excel; LOAD excel;")
    # Build VALUES clause with typed literals
    col_defs = ", ".join(f'"{h}"' for h in headers)
    values_rows = []
    for row in rows:
        parts = []
        for v in row:
            if v is None:
                parts.append("NULL")
            elif isinstance(v, datetime.date):
                parts.append(f"DATE '{v.isoformat()}'")
            elif isinstance(v, (int, float)):
                parts.append(str(v))
            else:
                esc = str(v).replace("'", "''")
                parts.append(f"'{esc}'")
        values_rows.append("(" + ", ".join(parts) + ")")
    values_sql = ", ".join(values_rows)
    conn.execute(f"CREATE OR REPLACE TEMP TABLE _t ({col_defs}) AS "
                 f"SELECT * FROM (VALUES {values_sql}) AS v({col_defs})")
    path_esc = str(path).replace("'", "''")
    conn.execute(f"COPY _t TO '{path_esc}' WITH (FORMAT 'xlsx', HEADER true)")
    conn.execute("DROP TABLE _t")
    return path


def _make_bretagne_xlsx(conn, tmp_path):
    return _write_xlsx(
        conn,
        tmp_path / "Annexe C (Bretagne).xlsx",
        ["Département", "Commune", "Date", "CVM (µg/L)"],
        [
            ("029", "Brest", datetime.date(2023, 6, 1), "0.25"),
            ("029", "Quimper", datetime.date(2023, 6, 2), "0,10"),
            ("029", "Landerneau", datetime.date(2023, 6, 3), "#EMPTY"),
            ("029", "Morlaix", datetime.date(2023, 6, 4), "<0.5"),
            ("029", "Chapelle (LA)", datetime.date(2023, 6, 5), "0.60"),
            ("2A", "Ajaccio", datetime.date(2023, 6, 6), "0.05"),
        ],
    )


def _make_normandie_xlsx(conn, tmp_path):
    return _write_xlsx(
        conn,
        tmp_path / "Annexe F (Normandie).xlsx",
        ["Dépt - Code", "PSV - Commune - Nom", "PLV - Date",
         "Chlorure de vinyl monomère (µg/L)"],
        [
            ("14", "Caen", datetime.date(2022, 1, 15), "0,55"),
            ("76", "Rouen", datetime.date(2022, 3, 20), "0"),
        ],
    )


def _make_aquitaine_xlsx(conn, tmp_path):
    return _write_xlsx(
        conn,
        tmp_path / "Annexe G (Nouvelle-Aquitaine).xlsx",
        ["Dept", "Commune", "PLV - Date", "Résultat"],
        [
            ("33", "Bordeaux", datetime.date(2021, 5, 10), "1,20"),
            ("33", "Pessac", datetime.date(2021, 5, 11), "#EMPTY"),
        ],
    )


@pytest.fixture()
def conn():
    c = duckdb.connect()
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Integration tests: parse_xlsx
# ---------------------------------------------------------------------------

def test_parse_bretagne_basic(conn, tmp_path):
    path = _make_bretagne_xlsx(conn, tmp_path)
    rows = parse_xlsx(conn, path)
    assert len(rows) == 6

    brest = next(r for r in rows if r["commune_name_raw"] == "Brest")
    assert brest["dept"] == "29"
    assert brest["value_ugl"] == pytest.approx(0.25)
    assert brest["commune_name_norm"] == "BREST"

    # Decimal-comma value parsed
    quimper = next(r for r in rows if r["commune_name_raw"] == "Quimper")
    assert quimper["value_ugl"] == pytest.approx(0.10)

    # Sentinels → None
    assert next(r for r in rows if r["commune_name_raw"] == "Landerneau")["value_ugl"] is None
    assert next(r for r in rows if r["commune_name_raw"] == "Morlaix")["value_ugl"] is None

    # (LA) stripped from norm
    chapelle = next(r for r in rows if r["commune_name_raw"] == "Chapelle (LA)")
    assert chapelle["commune_name_norm"] == "CHAPELLE"
    assert chapelle["value_ugl"] == pytest.approx(0.60)

    # Corsican dept preserved
    ajaccio = next(r for r in rows if r["commune_name_raw"] == "Ajaccio")
    assert ajaccio["dept"] == "2A"


def test_parse_normandie_numeric_dept(conn, tmp_path):
    path = _make_normandie_xlsx(conn, tmp_path)
    rows = parse_xlsx(conn, path)
    assert len(rows) == 2
    caen = next(r for r in rows if r["commune_name_raw"] == "Caen")
    assert caen["dept"] == "14"
    assert caen["value_ugl"] == pytest.approx(0.55)
    rouen = next(r for r in rows if r["commune_name_raw"] == "Rouen")
    assert rouen["dept"] == "76"
    assert rouen["value_ugl"] == pytest.approx(0.0)


def test_parse_aquitaine_empty_sentinel(conn, tmp_path):
    path = _make_aquitaine_xlsx(conn, tmp_path)
    rows = parse_xlsx(conn, path)
    assert len(rows) == 2
    bx = next(r for r in rows if r["commune_name_raw"] == "Bordeaux")
    assert bx["dept"] == "33"
    assert bx["commune_name_norm"] == "BORDEAUX"
    assert bx["value_ugl"] == pytest.approx(1.20)
    pessac = next(r for r in rows if r["commune_name_raw"] == "Pessac")
    assert pessac["value_ugl"] is None


def test_source_file_set(conn, tmp_path):
    path = _make_bretagne_xlsx(conn, tmp_path)
    rows = parse_xlsx(conn, path)
    assert all(r["source_file"] == path.name for r in rows)


def test_plv_date_is_python_date(conn, tmp_path):
    path = _make_bretagne_xlsx(conn, tmp_path)
    rows = parse_xlsx(conn, path)
    brest = next(r for r in rows if r["commune_name_raw"] == "Brest")
    assert isinstance(brest["plv_date"], datetime.date)


def test_missing_required_columns_returns_empty(conn, tmp_path):
    """File without dept/commune/date/value columns → no rows (skipped)."""
    p = _write_xlsx(
        conn, tmp_path / "weird.xlsx",
        ["foo", "bar"], [("a", "b"), ("c", "d")],
    )
    assert parse_xlsx(conn, p) == []


def test_non_numeric_dept_skipped(conn, tmp_path):
    """File whose dept column holds department names → rows dropped."""
    p = _write_xlsx(
        conn, tmp_path / "names_as_dept.xlsx",
        ["Departement", "Commune", "Date", "CVM"],
        [
            ("AIN", "Anglefort", datetime.date(2020, 1, 1), "0.1"),
            ("ALLIER", "Moulins", datetime.date(2020, 2, 1), "0.2"),
        ],
    )
    assert parse_xlsx(conn, p) == []


# ---------------------------------------------------------------------------
# Serial-number date parsing (Excel stores dates as integer serials)
# ---------------------------------------------------------------------------

def test_excel_serial_date_parsed(conn, tmp_path):
    """Excel serial-number date strings are parsed to the correct date.

    Serial 44727 = 2022-06-15 (DATE '1899-12-30' + 44727 days).
    all_varchar=true returns the cell value as a string, so the extractor
    must handle integer-looking strings in the date column.
    """
    # Pass the serial as a plain string so it lands in the xlsx as a text cell
    p = _write_xlsx(
        conn,
        tmp_path / "Annexe serial.xlsx",
        ["Département", "Commune", "Date", "CVM (µg/L)"],
        [
            ("029", "Brest", "44727", "0.25"),
            ("029", "Quimper", "45044", "0.10"),
        ],
    )
    rows = parse_xlsx(conn, p)
    assert len(rows) == 2
    brest = next(r for r in rows if r["commune_name_raw"] == "Brest")
    assert brest["plv_date"] == datetime.date(2022, 6, 15), (
        f"Expected 2022-06-15, got {brest['plv_date']}"
    )
    quimper = next(r for r in rows if r["commune_name_raw"] == "Quimper")
    assert quimper["plv_date"] == datetime.date(2023, 4, 28), (
        f"Expected 2023-04-28, got {quimper['plv_date']}"
    )


def test_garbage_date_logs_warning(conn, tmp_path, caplog):
    """Cells with unparseable date values fire a WARNING log."""
    import logging
    p = _write_xlsx(
        conn,
        tmp_path / "Annexe garbage.xlsx",
        ["Département", "Commune", "Date", "CVM (µg/L)"],
        [
            ("029", "Brest", "not-a-date", "0.25"),
            ("029", "Quimper", "2023-06-01", "0.10"),
        ],
    )
    with caplog.at_level(logging.WARNING, logger="pipelines.extract.fr_outline"):
        parse_xlsx(conn, p)

    assert any("failed all parse" in r.message for r in caplog.records), (
        f"Expected warning about unparsed date, got: {[r.message for r in caplog.records]}"
    )
