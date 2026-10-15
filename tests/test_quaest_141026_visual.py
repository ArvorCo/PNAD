"""Contrato dos gráficos: perguntas distintas, ordem explícita e escalas honestas."""

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from quaest_141026.charts import gaps, pairs
from quaest_141026.explorer import DIMENSIONS, OPTIONS, payload, rows
from quaest_141026.g1 import panel


@pytest.mark.parametrize("question", OPTIONS)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_explorer_preserves_each_source_value_and_every_segment(question, dimension):
    source = panel()[question]
    actual = payload()["questions"][question]
    assert actual["total"] == source["total"]
    assert set(actual["opcoes"]) == set(source["total"]["valores_pct"])
    assert actual["independente"] is (question == "rejeicao")
    selected = rows(actual, dimension)
    assert [r["recorte"] for r in selected] == DIMENSIONS[dimension]
    assert selected == [
        next(
            r
            for r in source["estratos"]
            if r["recorte"] == name and r["dimensao"] == dimension
        )
        for name in DIMENSIONS[dimension]
    ]
    assert all(r["base"] is None for r in selected)
    assert all(set(r["valores_pct"]) == set(actual["opcoes"]) for r in selected)


def test_rejection_is_independent_and_historical_precision_is_not_lost():
    chart = BeautifulSoup(pairs("Rejeição", {"Total": (54, 53)}), "html.parser")
    assert [b["style"].split(";")[0] for b in chart.select(".q-track i")] == [
        "width:54%",
        "width:53%",
    ]
    change = BeautifulSoup(
        gaps(
            "Contribuição", {"Baixa": -0.31, "Média": 3.36, "Alta": 4.59}, 5, digits=2
        ),
        "html.parser",
    )
    assert [b.get_text() for b in change.select(".q-gap-row strong")] == [
        "−0,31 pp",
        "+3,36 pp",
        "+4,59 pp",
    ]


def test_published_page_has_all_chapters_charts_and_local_explorer_data():
    page = BeautifulSoup(Path("docs/quaest_14102026.html").read_text(), "html.parser")
    chapters = page.select("section.chapter")
    assert [s["id"] for s in chapters] == [
        "renda",
        "mudanca",
        "serie",
        "segmentos",
        "perguntas",
        "incerteza",
        "campo",
        "painel",
        "fontes",
    ]
    assert [s.select_one(".section-number").get_text() for s in chapters] == [
        f"{n:02}" for n in range(1, 10)
    ]
    assert len(page.select("figure.chart")) >= 15
    assert json.loads(page.select_one("#q-explorer-data").string) == payload()
    assert page.select_one('script[src="assets/quaest_14102026.js"][defer]')
    assert len(page.select("#q-painel-raw tbody tr")) == 130
    assert len(page.select("#q-dimension option")) == 8
    assert "Sem cruzar" in page.get_text()
