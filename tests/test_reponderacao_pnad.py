"""Contratos do agregador Arvor: régua PNAD, motor de reponderação e média."""

import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLLS = ROOT / "analysis" / "reponderacao" / "pesquisas"
SCENARIO = "pessoas16_efetivo"


def load_module(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def engine():
    return load_module("reponderacao-pnad")


@pytest.fixture(scope="module")
def bench(engine):
    return engine.Benchmark()


@pytest.fixture(scope="module")
def output():
    return json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())


def test_benchmark_reproduces_house_target(bench):
    """Os cortes de 2, 5 e 10 salários de 2026 devolvem a régua já publicada."""
    shares = bench.shares(SCENARIO, [3242.0, 8105.0, 16210.0, None])
    assert shares == pytest.approx([35.43, 39.22, 16.93, 8.43], abs=0.1)
    assert sum(shares) == pytest.approx(100.0, abs=1e-6)


def test_benchmark_universes_are_plausible(bench):
    """Pessoas 16+ perto de 168 milhões; domicílios perto de 79 milhões."""
    assert 160e6 < bench.total("pessoas16_efetivo") < 175e6
    assert 75e6 < bench.total("domicilios_efetivo") < 85e6


def test_reweight_is_identity_when_profiles_match(engine):
    table = {"opcoes": ["lula", "flavio"], "linhas": [[60, 40], [40, 60]]}
    published = {"lula": 50, "flavio": 50}
    result = engine.reweight_table(table, published, [50, 50], {"x": [50, 50]})
    assert result["cenarios"]["x"]["ajustado"] == {"lula": 50.0, "flavio": 50.0}
    assert result["residuo_max"] == 0.0


def test_reweight_moves_toward_richer_band(engine):
    table = {"opcoes": ["lula", "flavio"], "linhas": [[60, 40], [40, 60]]}
    published = {"lula": 50, "flavio": 50}
    result = engine.reweight_table(table, published, [50, 50], {"x": [30, 70]})
    assert result["cenarios"]["x"]["ajustado"]["lula"] == pytest.approx(46.0)
    assert result["cenarios"]["x"]["ajustado"]["flavio"] == pytest.approx(54.0)


def test_band_cuts_convert_minimum_wages_of_the_card_year(engine):
    poll = {
        "id": "x",
        "campo": {"fim": "2026-04-30"},
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": [{"max": 2}, {"max": 5}, {"max": None}],
        },
    }
    cuts = engine.band_cuts_brl(poll, {})
    assert cuts[0] == pytest.approx(3242.0)
    assert cuts[1] == pytest.approx(8105.0)
    assert cuts[2] is None


def test_last_band_must_be_open(engine):
    poll = {
        "id": "x",
        "campo": {"fim": "2026-04-30"},
        "renda": {"unidade": "reais_nominais", "faixas": [{"max": 3000}]},
    }
    with pytest.raises(ValueError):
        engine.band_cuts_brl(poll, {})


def test_difference_margin_matches_datafolha_august(engine):
    """47 × 43 com n = 2.058 dá ±4,1 pontos, o número publicado no dossiê."""
    assert engine.difference_margin(47, 43, 2058) == pytest.approx(4.1, abs=0.05)


def test_every_poll_file_recomposes_its_topline(output):
    """Prova de leitura: o cruzamento de renda recompõe o placar dentro de 1,5 pp."""
    for poll in output["pesquisas"]:
        for turno, result in poll["turnos"].items():
            assert result["residuo_max"] <= 1.5, (
                poll["id"],
                turno,
                result["residuo_max"],
            )


def test_datafolha_series_matches_published_dossier(output):
    """Os quatro gaps ajustados da série Datafolha ficam a 0,2 pp dos publicados no dossiê."""
    expected = {
        "datafolha_2026-05-21": -2.81,
        "datafolha_2026-06-18": -0.16,
        "datafolha_2026-07-23": 0.0,
        "datafolha_2026-08-19": -1.78,
    }
    found = {
        p["id"]: p["turnos"]["2t"]["gap_ajustado"]
        for p in output["pesquisas"]
        if "2t" in p["turnos"]
    }
    for key, value in expected.items():
        assert found[key] == pytest.approx(value, abs=0.2), key


def test_aggregator_series_covers_reference_date(output):
    agg = output["agregador"]
    assert agg["serie"]["datas"][-1] == output["referencia"]
    latest = agg["serie"]["2t"]["ajustado"]["lula"][-1]
    assert latest is not None and 30 < latest < 60


def test_kernel_average_weights_recent_polls_more(engine):
    polls = [
        {
            "instituto": "A",
            "campo": {"fim": "2026-05-01"},
            "turnos": {"2t": {"publicado": {"lula": 40.0}, "cenarios": {}}},
        },
        {
            "instituto": "B",
            "campo": {"fim": "2026-06-01"},
            "turnos": {"2t": {"publicado": {"lula": 50.0}, "cenarios": {}}},
        },
    ]
    value = engine.kernel_average(polls, "2t", "publicado", "lula", date(2026, 6, 1))
    assert 47 < value < 50


def test_poll_files_have_required_fields():
    required = {"instituto", "campo", "n", "renda", "publicado", "cruzamentos", "fonte"}
    for path in POLLS.glob("*.json"):
        poll = json.loads(path.read_text())
        if poll.get("ignorar"):
            assert poll.get("motivo"), path.name
            continue
        missing = required - set(poll)
        assert not missing, (path.name, missing)
        bands = poll["renda"]["faixas"]
        assert bands[-1]["max"] is None, path.name
        for turno, table in poll["cruzamentos"].items():
            assert len(table["linhas"]) == len(bands), (path.name, turno)
            for row in table["linhas"]:
                assert len(row) == len(table["opcoes"]), (path.name, turno)
