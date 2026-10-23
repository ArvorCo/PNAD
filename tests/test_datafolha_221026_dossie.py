"""Contrato documental, ordem do arredondamento e revisão da mesma onda."""

import hashlib
import importlib
import json
import math

import pytest
from bs4 import BeautifulSoup
from datafolha_221026.audit import ROOT, build, rounding
from datafolha_221026.extract import PDF, SHA256, tables
from datafolha_221026.view import render


def test_entire_annex_and_question_specific_denominators():
    data = tables()
    assert len(data) == 11
    assert all(len(t["segments"]) == 31 for t in data.values())
    assert data["voto"]["page"] == 27
    assert data["voto"]["annex_page"] == 8
    assert data["validos"]["segments"]["total"]["base_ponderada"] == 2351
    assert data["decisao"]["segments"]["total"]["base_ponderada"] == 2482
    assert data["motivacao"]["segments"]["total"]["base_ponderada"] == 2351
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == SHA256


def test_rounding_can_explain_tie_without_changing_displayed_totals():
    first = rounding(46.8, 46.49)
    second = rounding(47, 46)
    assert first["total_inteiro"] == second["total_inteiro"] == [47, 46]
    assert first["validos_inteiros"] == [50, 50]
    assert second["validos_inteiros"] == [51, 49]
    assert sum([46.8, 46.49, 5.2, 1.51]) == pytest.approx(100)
    # The illustrative decimals even permit the rounded weighted bases.
    assert math.floor((46.8 + 46.49) * 2520 / 100 + 0.5) == 2351
    assert math.floor((100 - 1.51) * 2520 / 100 + 0.5) == 2482


def test_current_income_replaces_only_borrowed_profile():
    source = importlib.import_module("datafolha-221026-renda")
    old, new = source.previa(), source.completa()
    for key in ("id", "campo", "divulgacao", "publicado", "publicado_validos", "n"):
        assert old[key] == new[key]
    assert new["renda"]["bases"] == [1171, 913, 341]
    assert new["renda"]["perfil_tipo"] == "perfil_ponderado"
    assert new["renda"]["nao_publicada_n"] == 95
    assert new["renda"]["parcela_ajustada_pct"] == pytest.approx(100 * 2425 / 2520)
    archived = json.loads(
        (
            ROOT / "analysis/reponderacao/auditoria_datafolha_20261022_previa.json"
        ).read_text()
    )
    assert archived["pesquisa"] == old
    for c in new["controles"]["2t"].values():
        assert c["residuo_max_abs"] < 1


@pytest.fixture(scope="module")
def audit():
    return build()


def test_registry_distinguishes_field_quotas_and_income(audit):
    assert audit["quota"]["field_variables"] == ["gênero", "idade"]
    assert not audit["quota"]["income_field_quota_declared"]
    assert audit["quota"]["male_weighted_pct"] == pytest.approx(49.1666667)
    assert audit["quota"]["income_factor_planned"] == 1
    assert audit["difference_aas_margin_pp"] == pytest.approx(3.765, abs=0.001)


def test_render_uses_current_pdf_for_every_explorer_question(audit):
    html = render(audit)
    assert html == (ROOT / "docs/datafolha_22102026.html").read_text()
    page = BeautifulSoup(html, "html.parser")
    data = json.loads(page.select_one("#d-explorer-data").string)
    assert data["pdf"] == "fontes/datafolha_22102026.pdf"
    assert data["tables"]["validos"]["page"] == 28
    assert "50% × 50%" in page.select_one(".hero-result").get_text()
    assert "2347" not in str(data["tables"]["validos"]["segments"]["total"])
    assert "—" not in html
    assert [x.get_text() for x in page.select(".section-number")] == [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
    ]
    for link in page.select('a[href^="#"]'):
        assert page.find(id=link["href"][1:])
    for link in page.select('a[href^="fontes/"]'):
        assert (ROOT / "docs" / link["href"].split("#")[0]).is_file()
