"""Divulgação parcial: comparação correta, integração sem renda inventada e contas."""

import hashlib
import importlib
import json
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from quaest_141026.audit import POLL, ROOT, SLUG, aas, build
from quaest_141026.history import sha256
from quaest_141026.view import render

ENGINE = importlib.import_module("reponderacao-pnad")
SIM = importlib.import_module("reponderacao-simulador")
VALID = importlib.import_module("reponderacao-validos")


def read(path):
    return json.loads((ROOT / path).read_text())


@pytest.fixture(scope="module")
def audit():
    return build()


def test_same_question_precedes_election_and_proportional_change_reproduces_rounding(
    audit,
):
    old, new = audit["serie"][-2:]
    assert old["divulgacao"] == "2026-10-03"
    assert old["gap_total_pp"] == new["gap_total_pp"] == 2
    assert audit["decomposicao"]["variacoes_total_pp"] == {
        "flavio": 2,
        "lula": 2,
        "branco_nulo": -4,
        "indecisos": 0,
    }
    projected = audit["decomposicao"]["proporcao_anterior_aplicada_a_massa_atual"]
    assert projected["flavio"] == pytest.approx(90 * 44 / 86)
    assert projected["lula"] == pytest.approx(90 * 42 / 86)
    assert {k: round(v) for k, v in projected.items()} == {"flavio": 46, "lula": 44}
    assert old["gap_binario_pp"] > new["gap_binario_pp"]
    assert [x["weekday"] for x in audit["campo"]] == [5, 6, 0, 1]
    assert all(x["entrevistas"] is None for x in audit["campo"])


def test_uncertainty_is_for_the_difference_with_multinomial_covariance(audit):
    actual = aas(audit["pesquisa"])
    assert actual["variancia_pp2"] == pytest.approx((0.90 - 0.02**2) / 2154 * 10000)
    assert actual["margem_gap_95_pp"] == pytest.approx(4.00543755)
    lo, hi = actual["intervalo_gap_95_pp"]
    assert lo < 0 < hi
    assert (
        audit["aas"]["margem_mudanca_independente_aas_95_pp"]
        > actual["margem_gap_95_pp"]
    )


def test_historical_income_change_closes_with_disclosed_residual_without_october_imputation(
    audit,
):
    history = audit["evolucao_renda_historica"]
    assert history["inicio"]["id"] == "quaest_2026-07-13"
    assert history["fim"]["id"] == "quaest_2026-09-27"
    assert [r["peso_pct"] for r in history["faixas"]] == [31, 42, 27]
    assert [r["contribuicao_gap_pp"] for r in history["faixas"]] == pytest.approx(
        [-0.31, 3.36, 4.59]
    )
    assert history["mudanca_gap_recomposto_pp"] == pytest.approx(7.64)
    assert history["mudanca_residuo_pp"] == pytest.approx(0.36)
    assert (
        history["mudanca_gap_recomposto_pp"] + history["mudanca_residuo_pp"]
        == pytest.approx(history["mudanca_gap_publicado_pp"])
        == 8
    )
    assert audit["pesquisa"]["cruzamentos"]["2t"]["linhas"][0][:2] == [36, 53]


def test_historical_page_evidence_has_original_and_rendered_hashes(audit):
    sources = audit["evolucao_renda_historica"]["fontes"]
    assert len(sources["originais"]) == 3
    assert [p["pagina_fisica"] for p in sources["paginas"]] == [36, 114, 37, 204]
    for item in sources["paginas"]:
        path = ROOT / item["arquivo"]
        assert path.read_bytes().startswith(b"\x89PNG")
        assert sha256(path) == item["sha256"]
    # PDFs pesados são acervo local/LFS; o build comum usa o manifesto e os PNGs.
    for original in sources["originais"]:
        path = ROOT / original["arquivo"]
        if path.exists():
            assert path.stat().st_size == original["bytes"]
            assert sha256(path) == original["sha256"]


def test_registered_quotas_remain_a_conditional_assumption_after_crosses_arrive(audit):
    raw = audit["pesquisa"]
    assert not raw.get("ignorar")
    assert raw["renda"]["perfil_tipo"] == "cota_registrada"
    assert raw["perfil_economico_publicado"]["tipo"] == "cotas_previstas_registro_tse"
    result = audit["identificacao_renda"]
    assert result["tipo"] == "sensibilidade_condicional_cotas_registradas"
    assert result["reponderacao_pontual"]["flavio"] == 45.398
    assert result["reponderacao_pontual"]["lula"] == 44.531
    assert "perfil final" in result["hipotese"].lower()


def test_conditional_poll_enters_both_centers_once_without_previous_wave(audit):
    data = ENGINE.build(date(2026, 10, 15))
    row = next(p for p in data["pesquisas"] if p["id"] == POLL.stem)
    assert row["dossie"] == f"{SLUG}.html"
    assert POLL.stem not in {p["id"] for p in data["nao_reponderaveis"]}
    nexus = read("docs/assets/nexus_btg_28092026_data.json")
    simulation = SIM.build(data, VALID.build(data, nexus), nexus)
    assert POLL.stem in {p["id"] for p in simulation["polls"]}
    selected = simulation["projection"]["selected"]
    quaest = [p for p in selected if p["instituto"] == "Quaest"]
    assert len(quaest) == 1 and quaest[0]["id"] == POLL.stem
    assert quaest[0]["income_available"]
    assert quaest[0]["pnad"]["flavio"] == pytest.approx(45.398, abs=0.001)
    assert quaest[0]["pnad"]["lula"] == pytest.approx(44.531, abs=0.001)
    assert quaest[0]["published"] == audit["pesquisa"]["publicado"]["2t"]
    assert sum(p["weight"] for p in selected) == pytest.approx(1)
    for result in (simulation["central"], simulation["central_projection"]):
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)


def test_page_is_reproducible_sources_are_hashed_and_limits_are_visible(audit):
    html = render(audit)
    assert (ROOT / f"docs/{SLUG}.html").read_text() == html
    page = BeautifulSoup(html, "html.parser")
    assert page.select_one("html")["lang"] == "pt-BR"
    assert len(page.select("main section.chapter")) == 7
    assert len(page.select("#painel details")) == 5
    assert len(page.select("#painel details tbody tr")) == 130
    assert page.select_one('a[href="assets/quaest_14102026_painel/recortes.csv"]')
    assert page.select_one('meta[property="og:image"]')["content"].endswith(
        f"/{SLUG}.png"
    )
    assert len(page.select('script[src*="googletagmanager.com/gtag/js"]')) == 1
    assert "não significa que 75%" in page.get_text(" ", strip=True)
    assert "não os pesos finais" in page.get_text(" ", strip=True)
    assert "Não é resultado corrigido nem previsão" in page.get_text(" ", strip=True)
    manifest = read(f"docs/assets/{SLUG}_sources.json")
    for item in manifest["arquivos"]:
        path = Path(ROOT / item["arquivo"])
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_building_current_companions_preserves_closed_first_round(
    tmp_path, monkeypatch
):
    pages = importlib.import_module("reponderacao-paginas")
    archive = tmp_path / pages.ARCHIVE
    archive.write_text("arquivo fechado")
    monkeypatch.setattr(pages, "log_html", lambda ns: "<html><head></head></html>")

    def forbidden(ns):
        raise AssertionError("Atualização corrente tentou regerar o 1º turno")

    monkeypatch.setattr(pages, "archive_html", forbidden)
    pages.write_companions({"PAGE": tmp_path / pages.CURRENT})
    assert archive.read_text() == "arquivo fechado"
    assert (tmp_path / pages.LOG).exists()


def test_rendering_first_round_series_has_no_persistence_side_effect():
    view = importlib.import_module("reponderacao_vista.urna_serie_view")
    paths = [
        ROOT / f"docs/assets/reponderacao_urna_serie_1t.{ext}"
        for ext in ("json", "csv")
    ]
    before = [path.read_bytes() for path in paths]
    html = view.section(read("docs/assets/reponderacao_pnad.json"))
    assert "agregador-urna" in html
    assert [path.read_bytes() for path in paths] == before
