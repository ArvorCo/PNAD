"""Contratos das bases públicas do atlas paulista: fontes, universos e fechamento."""

import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def asset(name):
    return json.loads((ROOT / "docs/assets" / name).read_text())


def test_geographic_coverage_and_aggregation():
    data = asset("sp_092026_data.json")
    rows = data["municipios"]
    geo = asset("sp_092026_municipios.geojson")
    assert len(rows) == len({r["id"] for r in rows}) == 645
    assert {r["id"] for r in rows} == {
        f["properties"]["codarea"] for f in geo["features"]
    }
    assert len(data["regioes"]) == 11
    assert sum(r["eleitorado"] for r in rows) == data["eleitorado"]["total"] == 34105333
    assert sum(r["municipios"] for r in data["regioes"]) == 645
    for region in data["regioes"]:
        group = [r for r in rows if r["regiao"] == region["nome"]]
        for key in ("eleitorado", "jair_2022_2", "2022_PRESIDENTE_2_total"):
            assert region[key] == sum(r[key] for r in group)


def test_ties_are_not_opposition_wins():
    rows = asset("sp_092026_data.json")["municipios"]
    assert Counter(r["virada"] for r in rows) == {
        "Jair → Jair": 547,
        "Jair → PT": 83,
        "PT → PT": 14,
        "Jair → Empate": 1,
    }
    guara = next(r for r in rows if r["nome"] == "Guará")
    assert guara["jair_2022_2"] == guara["pt_2022_2"] == 5529
    flips = [r for r in rows if r["virada"] == "Jair → PT"]
    assert sum(r["jair_2018_2"] for r in flips) == 5384832
    assert sum(r["pt_2022_2"] for r in flips) == 5476948


def test_historical_votes_and_distinct_office_denominators():
    rows = asset("sp_092026_data.json")["municipios"]
    expected = {
        "jair_2018_2": 15306023,
        "jair_2022_2": 14216587,
        "tarcisio_2022_2": 13480643,
        "eduardo_2018_1": 1843735,
        "eduardo_2022_1": 741701,
        "carla_2018_1": 76306,
        "carla_2022_1": 946244,
        "mario_2022_1": 122564,
        "gil_2018_1": 214037,
        "gil_2022_1": 196215,
    }
    for key, value in expected.items():
        assert sum(r.get(key, 0) for r in rows) == value
    assert all("mario_2018_1" not in r for r in rows)
    for r in rows:
        assert r["tarcisio_2022_2_pct"] == pytest.approx(
            100 * r["tarcisio_2022_2"] / r["2022_GOVERNADOR_2_total"]
        )
        assert r["jair_2022_2_pct"] == pytest.approx(
            100 * r["jair_2022_2"] / r["2022_PRESIDENTE_2_total"]
        )


def test_polls_keep_unavailable_questions_and_source_limits():
    data = asset("sp_092026_pesquisas.json")
    polls = {p["id"]: p for p in data["pesquisas"]}
    assert "presidente2" not in polls["quaest"]
    assert "Notícias" in polls["rt_gov"]["status"]
    assert polls["rt_gov"]["presidente2"] == [44, 49]
    assert len(data["arquivos"]) == 4
    assert all(len(f["sha256"]) == 64 for f in data["arquivos"])
    for dimensions in data["validacoes"]["datafolha_p27"].values():
        assert all(abs(v["residuo_pp"]) < 1 for v in dimensions.values())


def test_income_partition_and_no_private_dependencies():
    pnad = asset("sp_092026_pnad.json")["anual_2025_visita1"]
    assert sum(
        v["pct"] for v in pnad["renda_domiciliar_16_mais"].values()
    ) == pytest.approx(100, abs=0.02)
    for v in pnad["renda_domiciliar_16_mais"].values():
        assert v["low"] <= v["pct"] <= v["high"]
    for path in [ROOT / "docs/sp_092026.html", *ROOT.glob("scripts/sp-092026-*.py")]:
        text = path.read_text()
        assert "campanhas/" not in text
        assert "/Downloads/" not in text
        assert "SP_Amarelos" not in text
