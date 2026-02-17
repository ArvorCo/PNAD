import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from pnad import (  # type: ignore
    _extract_relative_hrefs,
    _group_latest_anual_by_year,
    _group_latest_by_quarter,
    _latest_local_raw,
    _parse_pnadc_anual_visita5_zip_name,
    _parse_pnadc_zip_name,
    _select_tse_resources,
)


def test_parse_pnadc_zip_name_accepts_revision_suffix():
    parsed = _parse_pnadc_zip_name("PNADC_042015_20251210.zip")
    assert parsed is not None
    assert parsed["quarter"] == 4
    assert parsed["year"] == 2015
    assert parsed["revision"] == "20251210"


def test_group_latest_by_quarter_prefers_latest_revision():
    files = [
        "PNADC_012015_20250815.zip",
        "PNADC_012015_20251201.zip",
        "PNADC_022015_20250815.zip",
        "PNADC_032015_20250815.zip",
    ]
    grouped = _group_latest_by_quarter(files)
    assert grouped[1]["name"] == "PNADC_012015_20251201.zip"
    assert grouped[2]["name"] == "PNADC_022015_20250815.zip"


def test_extract_relative_hrefs_filters_absolute_and_query_links():
    html = """
    <a href="?C=N;O=D">sort</a>
    <a href="/Trabalho_e_Rendimento/">parent</a>
    <a href="2025/">2025</a>
    <a href="Documentacao/">Documentacao</a>
    <a href="PNADC_032025.zip">PNADC</a>
    <a href="https://www.ibge.gov.br/">portal</a>
    """
    hrefs = _extract_relative_hrefs(html)
    assert "2025/" in hrefs
    assert "Documentacao/" in hrefs
    assert "PNADC_032025.zip" in hrefs
    assert "?C=N;O=D" not in hrefs
    assert "/Trabalho_e_Rendimento/" not in hrefs
    assert "https://www.ibge.gov.br/" not in hrefs


def test_latest_local_raw_chooses_newest_year_and_quarter(tmp_path: Path):
    (tmp_path / "PNADC_012024.txt").write_text("x", encoding="utf-8")
    (tmp_path / "PNADC_042024.txt").write_text("x", encoding="utf-8")
    (tmp_path / "PNADC_022025.txt").write_text("x", encoding="utf-8")
    (tmp_path / "PNADC_012025.txt").write_text("x", encoding="utf-8")
    latest = _latest_local_raw(tmp_path)
    assert latest is not None
    assert latest.name == "PNADC_022025.txt"


def test_parse_pnadc_anual_visita5_zip_name_accepts_revision_suffix():
    parsed = _parse_pnadc_anual_visita5_zip_name("PNADC_2024_visita5_20250822.zip")
    assert parsed is not None
    assert parsed["year"] == 2024
    assert parsed["revision"] == "20250822"


def test_group_latest_anual_by_year_prefers_latest_revision():
    files = [
        "PNADC_2023_visita5_20240101.zip",
        "PNADC_2023_visita5_20250822.zip",
        "PNADC_2024_visita5.zip",
    ]
    grouped = _group_latest_anual_by_year(files)
    assert grouped[2023]["name"] == "PNADC_2023_visita5_20250822.zip"
    assert grouped[2024]["name"] == "PNADC_2024_visita5.zip"


def test_select_tse_resources_latest_by_kind_when_no_year():
    resources = [
        {"kind": "perfil_eleitorado", "year": 2024, "resource_name": "A", "url": "u1"},
        {"kind": "perfil_eleitorado", "year": 2025, "resource_name": "B", "url": "u2"},
        {"kind": "perfil_rae", "year": 2025, "resource_name": "C", "url": "u3"},
    ]
    picked = _select_tse_resources(resources, year=None, all_years=False)
    assert len(picked) == 2
    assert any(r["kind"] == "perfil_eleitorado" and r["year"] == 2025 for r in picked)
    assert any(r["kind"] == "perfil_rae" and r["year"] == 2025 for r in picked)


def test_select_tse_resources_all_years_keeps_one_per_kind_year():
    resources = [
        {"kind": "perfil_eleitorado", "year": 2025, "resource_name": "X1", "url": "u1"},
        {"kind": "perfil_eleitorado", "year": 2025, "resource_name": "X2", "url": "u2"},
        {"kind": "perfil_eleitorado", "year": 2024, "resource_name": "Y", "url": "u3"},
    ]
    picked = _select_tse_resources(resources, year=None, all_years=True)
    assert len(picked) == 2
    assert any(r["year"] == 2024 for r in picked)
    assert any(r["year"] == 2025 and r["url"] == "u2" for r in picked)
