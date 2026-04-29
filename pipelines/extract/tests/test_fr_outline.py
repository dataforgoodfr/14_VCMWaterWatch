"""Tests for pipelines/extract/fr_outline.py"""

import datetime
from pathlib import Path

import openpyxl
import pytest

from pipelines.extract.fr_outline import (
    normalize_commune_name,
    _parse_value,
    _parse_bretagne,
    _parse_generic,
    _choose_parser,
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


# ---------------------------------------------------------------------------
# Unit tests: _parse_value
# ---------------------------------------------------------------------------

def test_parse_value_float():
    assert _parse_value(0.12) == pytest.approx(0.12)


def test_parse_value_decimal_comma():
    assert _parse_value("0,12") == pytest.approx(0.12)


def test_parse_value_empty_string():
    assert _parse_value("") is None


def test_parse_value_hash_empty():
    assert _parse_value("#EMPTY") is None


def test_parse_value_below_limit():
    assert _parse_value("<0.5") is None


def test_parse_value_none():
    assert _parse_value(None) is None


def test_parse_value_int():
    assert _parse_value(1) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Synthetic xlsx helpers
# ---------------------------------------------------------------------------

def _make_bretagne_xlsx(tmp_path: Path) -> Path:
    """Create a minimal synthetic Bretagne Excel file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bretagne"
    # Header
    ws.append(["Departement", "Commune", "Date", "CVM (µg/L)"])
    # Normal row
    ws.append(["029", "Brest", datetime.date(2023, 6, 1), 0.25])
    # Decimal comma value
    ws.append(["029", "Quimper", datetime.date(2023, 6, 2), "0,10"])
    # #EMPTY sentinel
    ws.append(["029", "Landerneau", datetime.date(2023, 6, 3), "#EMPTY"])
    # <0.5 sentinel
    ws.append(["029", "Morlaix", datetime.date(2023, 6, 4), "<0.5"])
    # Commune with (LA) suffix
    ws.append(["029", "Chapelle (LA)", datetime.date(2023, 6, 5), 0.60])
    # Corsican dept code
    ws.append(["2A", "Ajaccio", datetime.date(2023, 6, 6), 0.05])
    out = tmp_path / "Annexe C (Bretagne).xlsx"
    wb.save(out)
    return out


def _make_normandie_xlsx(tmp_path: Path) -> Path:
    """Create a minimal synthetic Normandie Excel file with sheet-based dept."""
    wb = openpyxl.Workbook()
    # Remove default sheet
    ws1 = wb.active
    ws1.title = "Dept 14"
    ws1.append(["Commune", "Date", "CVM (µg/L)"])
    ws1.append(["Caen", datetime.date(2022, 1, 15), 0.55])
    ws2 = wb.create_sheet("Dept 76")
    ws2.append(["Commune", "Date", "CVM (µg/L)"])
    ws2.append(["Rouen", datetime.date(2022, 3, 20), 0.0])
    out = tmp_path / "Annexe F (Normandie).xlsx"
    wb.save(out)
    return out


def _make_aquitaine_xlsx(tmp_path: Path) -> Path:
    """Create a minimal synthetic Nouvelle-Aquitaine Excel file."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "NA"
    ws.append(["Departement", "Commune", "Date", "CVM (µg/L)"])
    ws.append(["33", "Bordeaux", datetime.date(2021, 5, 10), "1,20"])
    out = tmp_path / "Annexe G (Nouvelle-Aquitaine).xlsx"
    wb.save(out)
    return out


# ---------------------------------------------------------------------------
# Integration tests: per-region parsers
# ---------------------------------------------------------------------------

def test_parse_bretagne_basic(tmp_path):
    path = _make_bretagne_xlsx(tmp_path)
    rows = _parse_bretagne(path)
    assert len(rows) == 6

    brest = next(r for r in rows if r["commune_name_raw"] == "Brest")
    assert brest["dept"] == "29"
    assert brest["value_ugl"] == pytest.approx(0.25)
    assert brest["commune_name_norm"] == "BREST"

    # Decimal comma
    quimper = next(r for r in rows if r["commune_name_raw"] == "Quimper")
    assert quimper["value_ugl"] == pytest.approx(0.10)

    # #EMPTY → None
    lander = next(r for r in rows if r["commune_name_raw"] == "Landerneau")
    assert lander["value_ugl"] is None

    # <0.5 → None
    morlaix = next(r for r in rows if r["commune_name_raw"] == "Morlaix")
    assert morlaix["value_ugl"] is None

    # (LA) stripped from norm
    chapelle = next(r for r in rows if r["commune_name_raw"] == "Chapelle (LA)")
    assert chapelle["commune_name_norm"] == "CHAPELLE"
    assert chapelle["value_ugl"] == pytest.approx(0.60)

    # Corsican dept
    ajaccio = next(r for r in rows if r["commune_name_raw"] == "Ajaccio")
    assert ajaccio["dept"] == "2A"


def test_parse_normandie_sheet_dept(tmp_path):
    path = _make_normandie_xlsx(tmp_path)
    rows = _parse_generic(path)
    assert len(rows) == 2
    caen = next(r for r in rows if r["commune_name_raw"] == "Caen")
    assert caen["dept"] == "14"
    rouen = next(r for r in rows if r["commune_name_raw"] == "Rouen")
    assert rouen["dept"] == "76"


def test_parse_aquitaine(tmp_path):
    path = _make_aquitaine_xlsx(tmp_path)
    rows = _parse_generic(path)
    assert len(rows) == 1
    bx = rows[0]
    assert bx["dept"] == "33"
    assert bx["commune_name_norm"] == "BORDEAUX"
    assert bx["value_ugl"] == pytest.approx(1.20)


def test_choose_parser_bretagne(tmp_path):
    path = tmp_path / "Annexe C (Bretagne).xlsx"
    path.touch()
    assert _choose_parser(path) is _parse_bretagne


def test_choose_parser_normandie(tmp_path):
    from pipelines.extract.fr_outline import _parse_normandie
    path = tmp_path / "Annexe F (Normandie).xlsx"
    path.touch()
    assert _choose_parser(path) is _parse_normandie


def test_choose_parser_aquitaine(tmp_path):
    path = tmp_path / "Annexe G (Nouvelle-Aquitaine).xlsx"
    path.touch()
    assert _choose_parser(path).__name__ in ("_parse_nouvelle_aquitaine", "_parse_generic")
