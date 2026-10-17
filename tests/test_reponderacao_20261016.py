"""Rodada de 16/10: fontes, denominadores, cortes temporais e quatro casas."""

import importlib
import json
from datetime import date
from pathlib import Path

import pytest

M = importlib.import_module("pesquisas-161026-renda")
ENGINE = importlib.import_module("reponderacao-pnad")
PROJECTION = importlib.import_module("reponderacao-projecao")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", ["gerp", "poderdata", "mda", "futura"])
def test_sources_and_independent_recomposition(name):
    poll = getattr(M, name)()  # Verifica também bytes e SHA-256 das fontes.
    saved = ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json")
    assert poll == json.loads(saved.read_text())
    assert poll["divulgacao"] == "2026-10-16"
    assert poll["fonte"]["conferido_em"] == "2026-10-16"
    assert sum(poll["publicado"]["2t"].values()) == pytest.approx(100, abs=0.11)
    assert max(c["residuo_max_abs"] for c in poll["controles"]["2t"].values()) < 0.7


@pytest.mark.parametrize("name,fraction", [("gerp", 96 / 99), ("mda", 0.99)])
def test_nonresponse_mass_is_not_reassigned(name, fraction):
    poll = getattr(M, name)()
    assert poll["renda"]["parcela_ajustada_pct"] / 100 == pytest.approx(fraction)
    result = ENGINE.process_poll(poll, ENGINE.Benchmark(), ENGINE.load_ipca())
    for scenario in result["turnos"]["2t"]["cenarios"].values():
        for key, value in scenario["ajustado"].items():
            expected = poll["publicado"]["2t"][key] + fraction * (
                scenario["contrafactual"][key]
                - poll["controles"]["2t"]["renda"]["recomposto"][key]
            )
            assert value == pytest.approx(expected, abs=0.001)


def test_gerp_preserves_report_categories_and_separate_valid_rounding():
    poll = M.gerp()
    assert poll["publicado"]["2t"] == {
        "flavio": 50,
        "lula": 45,
        "branco_nulo": 2,
        "indecisos": 3,
    }
    assert poll["renda"]["amostra_pct"] == [22, 22, 32, 13, 5, 2]
    assert poll["publicado_validos"]["2t"]["flavio"] == 52
    assert 100 * 50 / 95 != 52


def test_futura_does_not_turn_profile_or_previous_wave_into_crossbreaks():
    poll = M.futura()
    assert poll["ignorar"] and not poll["cruzamentos"] and "renda" not in poll
    assert poll["campo"] == {"inicio": "2026-10-14", "fim": "2026-10-15"}
    assert poll["divergencia_campo"]["capa"] == "13–15/10"
    assert not poll["metodologia_onda"]["nova_mudanca_escolaridade_identificada"]
    assert poll["metodologia_onda"]["nota_ja_presente_em"] == "2026-10-13"
    assert poll["perfil_economico_publicado"]["ns_nr"] == 10.6


def test_profiles_and_first_round_weighting_are_explicit():
    for poll in [M.poderdata(), M.mda()]:
        assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
        assert poll["metodologia_onda"]["ponderacao_voto_1t_2026"]
    assert M.mda()["n"] == 2014


def test_new_waves_replace_houses_once_and_never_enter_yesterday():
    data = ENGINE.build(date(2026, 10, 16))
    current = PROJECTION.build(data, SIM.preferences)
    selected = {p["instituto"]: p for p in current["selected"]}
    assert len(selected) == len(current["selected"]) == 11
    for name in ["gerp", "poderdata", "mda", "futura"]:
        poll = getattr(M, name)()
        assert selected[poll["instituto"]]["id"] == poll["id"]
    assert not selected["Futura"]["income_available"]
    assert selected["Futura"]["pnad"] == selected["Futura"]["published"]
    assert sum(p["weight"] for p in selected.values()) == pytest.approx(1)
    data["referencia"] = "2026-10-15"
    yesterday = PROJECTION.build(data, SIM.preferences)
    assert not {
        M.gerp()["id"],
        M.poderdata()["id"],
        M.mda()["id"],
        M.futura()["id"],
    } & {p["id"] for p in yesterday["selected"]}


def test_published_snapshot_preserves_accounting_and_four_new_sources(
    assert_json_close,
):
    data = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/b1a3a422ac5f34e5.json").read_text()
    )
    assert data["reference"] == "2026-10-16"
    assert len(data["polls"]) == 7
    for key, params in [
        ("central", {}),
        ("central_projection", {"centro": "projecao"}),
    ]:
        result = SIM.evaluate(data, params)
        assert_json_close(result, data[key])
        assert result["flavio"] + result["lula"] == pytest.approx(100)
        assert sum(result["por_100_eleitores"].values()) == pytest.approx(100)
