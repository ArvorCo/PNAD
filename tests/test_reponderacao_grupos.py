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
HISTORY = load("reponderacao-historico-1t")
ENTRIES = json.loads(HISTORY.MANIFEST.read_text())
OUTPUT = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def test_groups_sum_candidates_before_averaging():
    polls = {p["id"]: p for p in OUTPUT["pesquisas"]}
    for row in OUTPUT["agregador"]["grupos_1t"]["ondas"]:
        result = polls[row["id"]]["turnos"]["1t"]
        center = set(row["componentes"]["outros_centro_direita"])
        residual = set(row["componentes"]["outros_esquerda_nanicos"])
        assert center == set(result["opcoes"]) & GROUPS.CENTER
        assert residual == set(result["opcoes"]) & GROUPS.LEFT_NANICOS
        assert not center & residual
        assert center | residual == (
            set(result["opcoes"]) - GROUPS.LEADERS - GROUPS.NON_CHOICE
        )
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


def test_historical_classification_matches_approved_partition():
    assert {"aecio", "aldo", "avalanche"} <= GROUPS.CENTER
    assert {"joaquim", "ciro", "daciolo", "hero"} <= GROUPS.LEFT_NANICOS
    assert not GROUPS.CENTER & GROUPS.LEFT_NANICOS


def test_historical_series_reaches_may_without_requiring_future_candidates():
    group = OUTPUT["agregador"]["grupos_1t"]
    first = min(group["ondas"], key=lambda p: p["campo"]["fim"])
    assert first["id"] == "realtime_2026-05-04"
    assert "clariana" not in first["componentes"]["outros_centro_direita"]
    assert {p["campo"]["fim"][5:7] for p in group["ondas"]} == {
        "05",
        "06",
        "07",
        "08",
        "09",
    }
    for kind in ["publicado", "ajustado"]:
        for key in GROUPS.GROUPS:
            for day, value in zip(
                OUTPUT["agregador"]["serie"]["datas"],
                group["serie"][kind][key],
                strict=True,
            ):
                assert (value is not None) == (day >= "2026-05-04")


@pytest.mark.parametrize(
    "ident", ["atlas_2026-05-18", "poderdata_2026-07-15", "poderdata_2026-07-29"]
)
def test_empty_group_only_when_verified_roster_offers_no_candidate(ident):
    poll = next(p for p in OUTPUT["pesquisas"] if p["id"] == ident)
    row, reason = GROUPS.split_poll(poll, SCENARIO)
    assert reason is None
    key = "outros_esquerda_nanicos"
    assert row["componentes"][key] == []
    assert row["publicado"][key] == row["ajustado"][key] == 0
    unverified = copy.deepcopy(poll)
    unverified.pop("grupos_1t_fonte")
    assert GROUPS.split_poll(unverified, SCENARIO)[0] is None


def test_historical_decomposition_is_pure_and_preserves_leaders():
    engine = load("reponderacao-pnad")
    selection = load("reponderacao-cenarios")
    bench, ipca = engine.Benchmark(), engine.load_ipca()
    for ident in ENTRIES:
        raw = selection.select_first_round(HISTORY.raw(ident))
        before = copy.deepcopy(raw)
        refined = HISTORY.refine(raw, ENTRIES)
        assert raw == before
        old = engine.process_poll(raw, bench, ipca)
        new = engine.process_poll(refined, bench, ipca)
        assert old["turnos"].get("2t") == new["turnos"].get("2t")
        for key in ["lula", "flavio"]:
            assert (
                old["turnos"]["1t"]["publicado"][key]
                == new["turnos"]["1t"]["publicado"][key]
            )
            for scenario, result in old["turnos"]["1t"]["cenarios"].items():
                assert (
                    result["ajustado"][key]
                    == new["turnos"]["1t"]["cenarios"][scenario]["ajustado"][key]
                )


def test_decomposition_rejects_unreconciled_income_or_topline():
    ident = "atlas_2026-06-30"
    for field in ["publicado", "renda"]:
        entries = copy.deepcopy(ENTRIES)
        column = entries[ident]["decomposicao_outros"]["joaquim"]
        if field == "renda":
            column[field][0] += 1
        else:
            column[field] += 1
        with pytest.raises(AssertionError):
            HISTORY.refine(HISTORY.raw(ident), entries)


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
    assert "28 ondas de 7 institutos" in text
    assert "04/05/2026" in text
    assert "10/09/2026" in text
    assert "Grassi integra o residual" in text
    assert html.find(id="selecao-primeiro-turno")
