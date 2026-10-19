"""Contratos da fonte decimal e integração das duas ondas de 19/10."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from dossies_2t_2026.view import stacks
from nexus_191026 import extract

ROOT = Path(__file__).resolve().parents[1]
INGEST = importlib.import_module("pesquisas-191026-renda")


@pytest.fixture(scope="module")
def data():
    return extract.extract()


def test_current_decimal_tables_recompose_with_current_profiles(data):
    assert len(data["tables"]) == 11
    assert len(data["catalog"]) == 128
    assert all(len(t["segments"]) == 29 for t in data["tables"].values())
    vote = data["tables"]["voto"]["segments"]
    assert list(vote["total"]["responses"].values()) == [46.5, 45.9, 4.7, 2.9]
    assert list(vote["1–2 SM"]["responses"].values()) == [36.5, 55.4, 5.4, 2.7]
    assert list(data["profile"]["renda"].values()) == [21, 16, 40, 23]
    assert all(row["base_ponderada"] is None for row in vote.values())
    assert (
        max(
            row["residuo_max_pp"]
            for dims in data["controls"].values()
            for row in dims.values()
        )
        < 0.47
    )
    assert data["reweight"]["turn"]["cenarios"]["pessoas16_efetivo"]["ajustado"][
        "flavio"
    ] == pytest.approx(47.292)


def test_changed_pdf_is_rejected(monkeypatch):
    monkeypatch.setattr(extract, "SHA256", "0" * 64)
    with pytest.raises(ValueError, match="fonte auditada"):
        extract.extract()


def test_public_sources_are_identical_and_distinct_from_prior_wave():
    for house, slug, n in [
        ("nexus", extract.SLUG, 128),
        ("poderdata", "poderdata_19102026", 33),
    ]:
        folder = ROOT / f"data/originals/{house}_102026_19"
        source = (folder / "relatorio.pdf").read_bytes()
        assert source == (ROOT / f"docs/fontes/{slug}.pdf").read_bytes()
        manifest = json.loads((folder / "fonte.json").read_text())
        assert hashlib.sha256(source).hexdigest() == manifest["arquivos"][0]["sha256"]
        with extract.pymupdf.open(folder / "relatorio.pdf") as doc:
            assert len(doc) == n
    assert (
        ROOT / "docs/fontes/nexus_btg_13102026.pdf"
    ).read_bytes() != extract.PDF.read_bytes()


def test_income_ingestion_preserves_rounding_and_profile_uncertainty():
    nx, pd = INGEST.nexus(), INGEST.poderdata()
    assert nx["publicado_validos"]["2t"] == {"flavio": 50.3, "lula": 49.7}
    assert pd["publicado_validos"]["2t"] == {"flavio": 52, "lula": 48}
    assert nx["fonte"]["conferido_em"] == pd["fonte"]["conferido_em"] == "2026-10-19"
    assert (
        nx["renda"]["perfil_tipo"] == pd["renda"]["perfil_tipo"] == "perfil_publicado"
    )
    assert pd["metodologia_onda"]["ponderacao_voto_1t_2026"] is True
    assert sum(nx["comparecimento_publicado"]["pct"][:2]) == pytest.approx(92.9)


def test_accessible_chart_does_not_round_away_decimal_votes():
    soup = BeautifulSoup(
        stacks("Voto", {"total": [46.5, 45.9]}, ["Flávio", "Lula"]), "html.parser"
    )
    assert [x.get_text() for x in soup.select("tbody td")] == [
        "total",
        "46,5%",
        "45,9%",
    ]


def test_dossier_payload_and_links_use_new_source(data):
    soup = BeautifulSoup(
        (ROOT / f"docs/{extract.SLUG}.html").read_text(), "html.parser"
    )
    payload = json.loads(soup.select_one("#d-explorer-data").string)
    assert payload["profile_page"] == 125
    assert payload["pdf"] == f"fontes/{extract.SLUG}.pdf"
    assert list(
        payload["tables"]["voto"]["segments"]["total"]["responses"].values()
    ) == [46.5, 45.9, 4.7, 2.9]
    assert "19/10/2026" in soup.title.get_text()
    assert soup.select_one('a[href="fontes/poderdata_19102026.pdf"]')
    for a in soup.select("a[href]"):
        href = a["href"]
        if href.startswith("#"):
            assert soup.find(id=href[1:]) is not None
        elif not href.startswith("http"):
            assert (ROOT / "docs" / href.split("#")[0]).exists(), href


def test_conditioned_motivation_and_economic_horizons_stay_distinct(data):
    special = data["special"]
    motivation = special["motivation"]
    on_total = (
        45.9 * motivation["rows"]["Eleitores de Lula"][1] / 100
        + 46.5 * motivation["rows"]["Eleitores de Flávio"][1] / 100
    )
    assert on_total == pytest.approx(motivation["rejection_all_published"], abs=0.05)
    assert set(special["economy"]) == {"current", "past", "future"}
    assert {x["page"] for x in special["economy"].values()} == {118, 120, 122}
    for horizon in special["economy"].values():
        for row in horizon["rows"].values():
            assert sum(row) == pytest.approx(100, abs=0.11)
    for first, second, total in special["issues"]["top8"].values():
        assert first + second == pytest.approx(total)
