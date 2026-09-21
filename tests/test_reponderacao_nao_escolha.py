"""Cobertura, somas e ponderação temporal das duas linhas de não escolha."""

import copy
import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "pessoas16_efetivo"
SPEC = importlib.util.spec_from_file_location(
    "non_choice", ROOT / "scripts/reponderacao-nao-escolha.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
OUTPUT = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


@pytest.mark.parametrize("turn", ["1t", "2t"])
def test_average_reproduces_time_weights_and_same_cohort(turn):
    group = OUTPUT["agregador"]["nao_escolha"][turn]
    polls = {p["id"]: p for p in OUTPUT["pesquisas"]}
    selected_ids = set(group["cobertura_movel"][-1]["ondas"])
    for kind in ["publicado", "ajustado"]:
        for key in MODULE.LABELS:
            values = []
            for row in group["ondas"]:
                result = polls[row["id"]]["turnos"][turn]
                source = (
                    result["publicado"]
                    if kind == "publicado"
                    else result["cenarios"][SCENARIO]["ajustado"]
                )
                assert row[kind][key] == pytest.approx(
                    sum(source[k] for k in row["componentes"][key])
                )
                if row["id"] in selected_ids:
                    values.append(row[kind][key])
            expected = sum(values) / len(values)
            assert group["ultimo"][kind][key] == pytest.approx(expected, abs=0.005)
            assert (
                OUTPUT["agregador"]["serie"][turn][kind][key][-1]
                == group["ultimo"][kind][key]
            )


def test_missing_data_are_not_zero_and_separate_nonvoting_is_summed():
    q = next(p for p in OUTPUT["pesquisas"] if p["id"] == "quaest_2026-09-20")
    assert MODULE.extract(q, "1t", SCENARIO)[0] is None
    p = copy.deepcopy(
        next(p for p in OUTPUT["pesquisas"] if p["id"] == "datafolha_2026-09-17")
    )
    result = p["turnos"]["2t"]
    result["opcoes"].append("nao_vai_votar")
    result["publicado"]["nao_vai_votar"] = 2
    result["cenarios"][SCENARIO]["ajustado"]["nao_vai_votar"] = 3
    row, _ = MODULE.extract(p, "2t", SCENARIO)
    assert row["publicado"]["branco_nulo"] == result["publicado"]["branco_nulo"] + 2
    assert (
        row["ajustado"]["branco_nulo"]
        == result["cenarios"][SCENARIO]["ajustado"]["branco_nulo"] + 3
    )
    result["publicado"]["indecisos"] = 0
    assert MODULE.extract(p, "2t", SCENARIO)[0]["publicado"]["indecisos"] == 0
    del result["publicado"]["indecisos"]
    assert MODULE.extract(p, "2t", SCENARIO)[0] is None


def test_empty_series_stays_missing_and_does_not_extrapolate_backwards():
    q = next(p for p in OUTPUT["pesquisas"] if p["id"] == "quaest_2026-09-20")
    empty = MODULE.aggregate([q], "1t", ["2026-09-21"], date(2026, 9, 21), SCENARIO, 7)
    assert empty["serie"]["ajustado"]["indecisos"] == [None]
    for t in ["1t", "2t"]:
        g = OUTPUT["agregador"]["nao_escolha"][t]
        for day, value in zip(
            OUTPUT["agregador"]["serie"]["datas"], g["serie"]["ajustado"]["indecisos"]
        ):
            assert (value is not None) == bool(
                next(c for c in g["cobertura_movel"] if c["data"] == day)["ondas"]
            )


def test_both_charts_have_distinct_lines_and_auditable_coverage():
    html = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    for turn, slug, count in [("1t", "primeiro", 6), ("2t", "segundo", 4)]:
        chart = html.find(id=f"{slug}-turno-chart")
        assert len(chart.select("g[data-serie]")) == count
        for key, color in [("indecisos", "#8350a0"), ("branco_nulo", "#28705f")]:
            paths = chart.select(f'g[data-serie="{key}"] path')
            assert len(paths) >= 2 and all(p["stroke"] == color for p in paths)
            assert sum(p.has_attr("stroke-dasharray") for p in paths) * 2 == len(paths)
        text = html.find(id=f"nao-escolha-{turn}").get_text(" ", strip=True)
        assert (
            "Não vai votar é declaração" in text and "não formam uma partição" in text
        )
