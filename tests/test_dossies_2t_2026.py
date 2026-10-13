"""Fontes, universos, transcrições completas e apresentação dos dois dossiês."""

import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from bs4 import BeautifulSoup
from dossies_2t_2026 import audit, extract, view

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    return audit.build()


@pytest.mark.parametrize("house", ["nexus", "datafolha"])
def test_original_pdf_and_public_copy_have_verified_identical_bytes(house):
    source = extract.PDFS[house].read_bytes()
    assert hashlib.sha256(source).hexdigest() == extract.HASHES[house]
    assert source.startswith(b"%PDF")
    copy = ROOT / "docs/fontes" / view.PDF[house]
    assert copy.read_bytes() == source


def test_changed_source_is_rejected_before_extraction(monkeypatch):
    monkeypatch.setitem(extract.HASHES, "nexus", "0" * 64)
    with pytest.raises(ValueError, match="Fonte alterada"):
        extract.verified_document("nexus")


def test_all_datafolha_annex_questions_and_bases_are_preserved(data):
    tables = data["datafolha"]["tables"]
    assert len(tables) == 10
    assert {t["page"] for t in tables.values()} == set(range(25, 35))
    assert all(len(t["segments"]) == 31 for t in tables.values())
    vote, decision, motive = [
        tables[k]["segments"] for k in ["voto", "decisao", "motivacao"]
    ]
    assert vote["total"]["base_ponderada"] == 2520
    assert decision["total"]["base_ponderada"] == 2488
    assert motive["total"]["base_ponderada"] == 2366
    assert (
        sum(vote[k]["base_ponderada"] for k in ["até 2 SM", "2–5 SM", ">5 SM"]) == 2398
    )
    assert vote["PL"]["responses"]["Em branco/ nulo/ nenhum"] is None
    assert vote["mulheres"]["responses"]["Lula (PT)"] == 50
    assert vote["homens"]["responses"]["Flavio Bolsonaro (PL)"] == 53
    assert tables["aprovacao"]["segments"]["evangélica"]["responses"]["Desaprova"] == 68
    assert tables["aprovacao"]["segments"]["Nordeste"]["responses"]["Aprova"] == 64


def test_nexus_matrix_columns_match_printed_categories_and_granularity(data):
    tables = data["nexus"]["tables"]
    assert len(tables) == 9
    assert all(len(t["segments"]) == 29 for t in tables.values())
    vote = tables["voto"]["segments"]
    assert list(vote["mulheres"]["responses"].values()) == [39, 54, 4, 3]
    assert list(vote["até 1 SM"]["responses"].values()) == [32, 58, 3, 7]
    assert list(vote["1–2 SM"]["responses"].values()) == [47, 44, 5, 4]
    assert "25–40" in vote and "41–59" in vote and "35–44" not in vote
    assert "CO/Norte" in vote and "Norte" not in vote
    assert (
        tables["presenca"]["segments"]["16–24"]["responses"][
            "Provavelmente comparecerá"
        ]
        == 14
    )


@pytest.mark.parametrize("house", ["nexus", "datafolha"])
def test_every_crossed_question_recomposes_through_independent_partitions(data, house):
    controls = data[house]["controls"]
    assert set(controls) == set(data[house]["tables"])
    for groups in controls.values():
        assert {"sexo", "idade", "regiao"} <= groups.keys()
        for dimension in groups.values():
            assert dimension["max_residual_pp"] <= 1.25


def test_denominators_do_not_turn_conditioned_percentages_into_national_claims(data):
    d = data["datafolha"]["denominators"]
    assert d["certain_all_pct"] == pytest.approx(94 * 2488 / 2520)
    assert d["motivation_negative_all_pct"] == pytest.approx(19 * 2366 / 2520)
    assert d["certain_all_pct"] < 94
    assert d["motivation_negative_all_pct"] < 19
    assert d["open_all_pct"] == pytest.approx(100 - d["certain_all_pct"])
    nx = data["nexus"]["special"]
    assert nx["second_option"]["rows"]["Branco/nulo"] == 52
    assert nx["decision"]["total"][1] == 7
    assert nx["decision"]["by_vote"]["NS/NR"][1] == 58
    assert sum(nx["decision"]["by_vote"]["Flávio"]) == 99


def test_transfer_remainders_are_not_imputed_and_household_is_not_individual(data):
    df = data["datafolha"]["transfer"]
    assert (
        df["unreported_residual"]
        == 100 - df["flavio"] - df["lula"] - df["invalid"]
        == 7
    )
    assert "indecisos" not in df
    nx = data["nexus"]["special"]
    assert nx["transfer_detail"]["rows"]["Zema"] == [80, 0, 12, 8]
    assert nx["transfer_detail"]["rows"]["Cury"] == [43, 41, 13, 4]
    assert nx["cluster_vote"]["rows"]["Não polarizados"] == [37, 44, 14, 5]
    assert list(nx["bolsa_familia"]["rows"].values()) == [
        [23, 68, 4, 6],
        [52, 41, 5, 2],
    ]
    assert "alguém" in nx["bolsa_familia"]["universe"]


def test_economic_horizons_and_multiple_issue_mentions_remain_separate(data):
    s = data["nexus"]["special"]
    assert s["economy"]["current"]["country"] == [17, 31, 51, 2]
    assert s["economy"]["future"]["country"] == [54, 17, 12, 16]
    assert s["economy"]["future_vote"]["country"]["Melhorará"] == [52, 43, 2, 2]
    assert s["problems"]["rows"]["Saúde"] == [12, 17, 29]
    assert s["problems"]["rows"]["Corrupção"] == [13, 5, 18]
    assert s["problems"]["rows"]["Segurança pública"] == [19, 14, 33]


def test_income_revision_is_known_mass_delta_not_new_wave_or_hidden_weight(data):
    df, nx = data["datafolha"], data["nexus"]
    assert df["reweight"]["turn"]["parcela_ajustada_pct"] == pytest.approx(
        100 * 2398 / 2520
    )
    assert df["income_history"]["declared_income_factor"] == 1
    assert df["income_history"]["declared_target"] == [49, 47, 4]
    assert (
        df["reweight"]["turn"]["cenarios"]["pessoas16_efetivo"]["ajustado"]["flavio"]
        == 50.934
    )
    assert (
        nx["income_history"]["prior"]["amostra_pct"]
        == nx["reweight"]["profile"]["amostra_pct"]
    )
    assert (
        nx["reweight"]["turn"]["cenarios"]["pessoas16_efetivo"]["ajustado"]["flavio"]
        == 49.067
    )
    for house in [df, nx]:
        assert "Não declarada" in house["source"]["weighting_first_round"]
        assert "não exportação" in house["source"]["registry_status"]


@pytest.mark.parametrize("house", ["nexus", "datafolha"])
def test_published_payload_and_page_sources_cover_the_actual_goal(data, house):
    d = data[house]
    saved = json.loads((ROOT / "docs/assets" / (d["slug"] + "_data.json")).read_text())
    assert saved == d
    page = BeautifulSoup(
        (ROOT / "docs" / (d["slug"] + ".html")).read_text(), "html.parser"
    )
    assert page.select_one("#d-explorer-data")
    assert page.select_one("#tabelas-completas")
    assert len(page.select("#tabelas-completas details")) == len(d["tables"])
    for ident in [
        "renda",
        "transferencias",
        "segmentos",
        "perguntas",
        "metodo",
        "fontes",
    ]:
        assert page.find(id=ident)
    method = page.select_one("#metodo").get_text(" ", strip=True)
    assert "Não há declaração" in method and "não prova" in method
    for link in page.select("a[href]"):
        href = urlsplit(link["href"])
        if href.scheme or not href.path:
            continue
        assert (ROOT / "docs" / href.path).is_file(), link["href"]
    assert page.select_one('meta[property="og:image"]')["content"].endswith(
        d["slug"] + ".png"
    )
    assert "G-ZPYEE8P9YC" in str(page)
    assert (ROOT / "docs/img/og" / (d["slug"] + ".png")).is_file()


def test_new_source_modules_and_data_stay_below_line_limit():
    paths = list((ROOT / "scripts/dossies_2t_2026").glob("*.py")) + list(
        (ROOT / "analysis/dossies_2t_2026").glob("*.json")
    )
    assert all(len(p.read_text().splitlines()) < 1000 for p in paths)
