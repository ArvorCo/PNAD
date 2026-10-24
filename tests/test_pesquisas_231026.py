"""Fontes, reconciliação e cobertura da rodada de 23/10."""

import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.historico_2t import history
from reponderacao_vista.historico_2t_chart import segments
from reponderacao_vista.historico_painel import panel
from reponderacao_vista.historico_projecao import project

ROUND = importlib.import_module("pesquisas-231026-renda")
ROOT = Path(__file__).resolve().parents[1]
NAMES = ["realtime", "alfa", "ipespe", "vox", "verita", "datatrends", "vetor"]


@pytest.mark.parametrize("name", NAMES)
def test_archived_sources_and_saved_transcription(name, assert_json_close):
    poll = getattr(ROUND, name)()  # archive() verifies source size and SHA-256.
    path = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert_json_close(poll, json.loads(path.read_text()))
    assert poll["divulgacao"] == "2026-10-23"
    assert sum(poll["publicado_validos"]["2t"].values()) == pytest.approx(100)


@pytest.mark.parametrize("name", ["realtime", "alfa", "ipespe"])
def test_current_income_recomposes_candidates_and_independent_sex_control(name):
    poll = getattr(ROUND, name)()
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    for control in poll["controles"]["2t"].values():
        assert control["residuo_max_abs"] <= 0.5
    row = next(p for p in history() if p["id"] == poll["id"])
    assert row["pnad"] is not None
    assert row["pnad"]["flavio"] > row["placar"]["flavio"]


def test_inconsistent_or_missing_income_is_never_imputed():
    verita = ROUND.verita()
    profile = verita["perfil_economico_publicado"]
    assert sum(profile["percentuais"]) == pytest.approx(104.3)
    assert sum(profile["frequencias"]) == 16230 > verita["n"]
    rows = {p["id"]: p for p in history()}
    for name in ["verita", "vox", "datatrends", "vetor"]:
        poll = getattr(ROUND, name)()
        assert poll["ignorar"] and not poll["cruzamentos"]
        assert rows[poll["id"]]["pnad"] is None


def test_ipespe_preserves_official_valids_and_current_turnout_selection():
    poll = ROUND.ipespe()
    assert poll["publicado_validos"]["2t"]["flavio"] == 50.5
    assert poll["subconjunto_presenca_publicado"]["validos"]["flavio"] == 51.5
    row = next(p for p in history() if p["id"] == poll["id"])
    projection = project(row)
    assert projection["evidencia"]["taxas"] == {
        "flavio": 0.94,
        "lula": 0.90,
        "indecisos": 0.61,
    }
    assert projection["modos"]["placar"]["validos"]["flavio"] == pytest.approx(
        100 * 48 * 0.94 / (48 * 0.94 + 47 * 0.90)
    )
    assert projection["evidencia"]["subconjunto_validos_publicado"]["flavio"] == 51.5


def test_real_time_now_connects_both_adjusted_post_election_waves():
    rows = [
        p
        for p in history()
        if p["instituto"] == "Real Time Big Data" and p["divulgacao"] <= "2026-10-23"
    ]
    assert [p["id"] for p in segments(rows, "pnad")[-1]] == [
        "realtime_2026-10-19",
        "realtime_2026-10-22",
    ]
    soup = BeautifulSoup(panel("Real Time Big Data", rows), "html.parser")
    for mode in ["total", "validos"]:
        graph = soup.select_one(f'[data-history-view="{mode}"] .fig svg')
        assert len(graph.select('g[aria-label*="pnad"] circle:not(.hit-area)')) == 4
        assert graph.select('path[fill="none"]')


def test_all_seven_enter_projection_once_without_reusing_older_income():
    # O snapshot desta rodada fixa a data; futuras pesquisas não mudam o contrato.
    payload = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/0149cb738f12cc91.json").read_text()
    )
    selected = payload["projection"]["selected"]
    assert len({p["instituto"] for p in selected}) == len(selected) == 19
    assert sum(p["weight"] for p in selected) == pytest.approx(1)
    by_id = {p["id"]: p for p in selected}
    for name in NAMES:
        poll = getattr(ROUND, name)()
        current = by_id[poll["id"]]
        assert current["income_available"] is (not poll.get("ignorar", False))
        if poll.get("ignorar"):
            assert current["pnad"] == current["published"]
    assert len(payload["polls"]) == 10
    assert not {"Veritá", "DataTrends"} & {p["instituto"] for p in payload["polls"]}
