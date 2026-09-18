"""Alternativas sem Marçal: leitura, universo e preservação do segundo turno."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


SELECTION = module("reponderacao-cenarios")
ENGINE = module("reponderacao-pnad")


def raw(ident):
    path = ROOT / "analysis/reponderacao/pesquisas" / f"{ident}.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("ident", SELECTION.ALTERNATIVES)
def test_alternative_has_own_income_crossing_and_preserves_second_round(ident):
    poll = raw(ident)
    original = copy.deepcopy(poll)
    selected = SELECTION.select_first_round(poll, exclude_only_marcal=True)
    assert poll == original
    assert "marcal" not in selected["publicado"]["1t"]
    assert "marcal" not in selected["cruzamentos"]["1t"]["opcoes"]
    assert selected["cruzamentos"].get("2t") == original["cruzamentos"].get("2t")
    assert selected["publicado"].get("2t") == original["publicado"].get("2t")
    assert selected["renda"] == original["renda"]
    assert selected["selecao_1t"]["status"] == "alternativa_sem_marcal"
    result = ENGINE.process_poll(selected, ENGINE.Benchmark(), ENGINE.load_ipca())
    assert result["turnos"]["1t"]["residuo_max"] < 1.5


@pytest.mark.parametrize(
    "ident", ["gerp_2026-09-16", "poderdata_2026-09-16", "mda_2026-09-13"]
)
def test_excluding_scenario_never_excludes_second_round(ident):
    poll = raw(ident)
    selected = SELECTION.select_first_round(poll, exclude_only_marcal=True)
    assert "1t" not in selected["cruzamentos"]
    assert selected["publicado"]["1t"] == poll["publicado"]["1t"]
    assert selected["cruzamentos"]["2t"] == poll["cruzamentos"]["2t"]
    assert selected["selecao_1t"]["status"] == "excluido_com_marcal"


def test_mentions_of_alternative_marcal_scenario_do_not_exclude_selected_scenario():
    poll = raw("palver_2026-09-07")
    assert "com Marçal" in poll["cruzamentos"]["1t"]["nota"]
    assert SELECTION.select_first_round(poll, exclude_only_marcal=True) == poll


def test_switch_uses_observed_votes_instead_of_removing_marcal_and_rescaling():
    poll = SELECTION.select_first_round(raw("datafolha_2026-08-19"))
    assert poll["publicado"]["1t"]["lula"] == 39
    assert poll["publicado"]["1t"]["flavio"] == 33
    assert poll["cruzamentos"]["1t"]["linhas"][0][:2] == [46, 27]
