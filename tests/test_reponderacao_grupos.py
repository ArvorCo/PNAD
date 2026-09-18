"""Grupos do 1º turno: partição auditável e mesma ponderação para as duas linhas."""

import copy
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "pessoas16_efetivo"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GROUPS = load("reponderacao-grupos")
OUTPUT = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def test_groups_sum_candidates_before_averaging():
    polls = {p["id"]: p for p in OUTPUT["pesquisas"]}
    for row in OUTPUT["agregador"]["grupos_1t"]["ondas"]:
        result = polls[row["id"]]["turnos"]["1t"]
        center = set(row["componentes"]["outros_centro_direita"])
        residual = set(row["componentes"]["outros_esquerda_nanicos"])
        assert center == {"zema", "cury", "caiado", "renan_santos", "clariana"}
        assert residual == {"samara", "rui", "edmilson", "hertz", "grassi"}
        assert not center & residual
        for kind in ("publicado", "ajustado"):
            values = (
                result["publicado"]
                if kind == "publicado"
                else result["cenarios"][SCENARIO]["ajustado"]
            )
            assert row[kind]["outros_centro_direita"] == pytest.approx(
                sum(values[k] for k in center), abs=0.001
            )
            assert row[kind]["outros_esquerda_nanicos"] == pytest.approx(
                sum(values[k] for k in residual), abs=0.001
            )


def test_both_lines_use_same_time_weights_and_match_endpoint():
    agg = OUTPUT["agregador"]
    group = agg["grupos_1t"]
    today = date.fromisoformat(OUTPUT["referencia"])
    weights = [
        0.5 ** ((today - date.fromisoformat(p["campo"]["fim"])).days / 14)
        for p in group["ondas"]
    ]
    for kind in ("publicado", "ajustado"):
        for key in GROUPS.GROUPS:
            expected = sum(
                w * p[kind][key] for w, p in zip(weights, group["ondas"], strict=True)
            ) / sum(weights)
            assert group["ultimo"]["kernel"][kind][key] == pytest.approx(
                expected, abs=0.005
            )
            assert (
                agg["serie"]["1t"][kind][key][-1]
                == group["ultimo"]["kernel"][kind][key]
            )


def test_ambiguous_residual_and_missing_candidate_are_not_imputed():
    realtime = next(p for p in OUTPUT["pesquisas"] if p["id"] == "realtime_2026-08-31")
    row, reason = GROUPS.split_poll(realtime, SCENARIO)
    assert row is None and "Residual outros" in reason
    atlas = next(p for p in OUTPUT["pesquisas"] if p["id"] == "atlas_2026-09-16")
    row, reason = GROUPS.split_poll(atlas, SCENARIO)
    assert row is None and "clariana" in reason


def test_marcal_cannot_leak_into_a_group_even_at_zero():
    poll = copy.deepcopy(
        next(p for p in OUTPUT["pesquisas"] if p["id"] == "datafolha_2026-09-10")
    )
    poll["turnos"]["1t"]["opcoes"].append("marcal")
    poll["turnos"]["1t"]["publicado"]["marcal"] = 0
    assert GROUPS.split_poll(poll, SCENARIO)[0] is None


def test_every_second_round_is_preserved_and_first_round_selection_is_enforced():
    engine = load("reponderacao-pnad")
    selection = load("reponderacao-cenarios")
    bench, ipca = engine.Benchmark(), engine.load_ipca()
    for poll in OUTPUT["pesquisas"]:
        raw = json.loads((ROOT / poll["arquivo"]).read_text())
        original = engine.process_poll(raw, bench, ipca)
        assert poll["turnos"].get("2t") == original["turnos"].get("2t")
        if "1t" in poll["turnos"]:
            assert "marcal" not in poll["turnos"]["1t"]["opcoes"]
            assert (
                not selection.contains_marcal(raw)
                or poll["id"] in selection.ALTERNATIVES
            )
        elif selection.contains_marcal(raw):
            assert poll["selecao_1t"]["status"] == "excluido_com_marcal"


def test_page_has_gray_and_black_lines_and_explicit_coverage():
    html = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    chart = html.find(id="primeiro-turno-chart")
    assert len(chart.select("g[data-serie]")) == 4
    for key, color in [
        ("outros_centro_direita", "#626262"),
        ("outros_esquerda_nanicos", "#000000"),
    ]:
        paths = chart.select(f'g[data-serie="{key}"] path')
        assert len(paths) == 2
        assert all(p["stroke"] == color for p in paths)
    text = html.find(id="grupos-primeiro-turno").get_text(" ", strip=True)
    assert "4 ondas de 2 institutos" in text
    assert "10/09/2026" in text
    assert "Grassi integra o residual" in text
    assert html.find(id="selecao-primeiro-turno")
