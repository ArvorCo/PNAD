"""Fontes, transporte temporal e contabilidade das alternativas históricas."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

T = importlib.import_module("reponderacao-comparecimento")
F = importlib.import_module("reponderacao-comparecimento-fontes")
M = importlib.import_module("reponderacao-simulador")
C = importlib.import_module("reponderacao-contagem")
ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())


def test_central_is_observed_2026_domestic_turnout_and_mass_closes():
    t = T.build()
    assert t == DATA["turnout_model"]
    first = t["first_round"]
    assert first["electorate"] == DATA["electorate"]["total"] == 157_828_968
    assert first["attendance"] == 124_934_069
    assert first["absence"] == 32_894_899
    assert first["attendance"] + first["absence"] == first["electorate"]
    assert DATA["defaults"]["comparecimento"] == pytest.approx(79.15788247440102)
    assert t["central_delta_pp"] == 0
    assert DATA["defaults"]["comparecimento"] != pytest.approx(79.5783)


def test_historical_round_changes_keep_sign_and_recent_exception():
    years = DATA["turnout_model"]["history"]
    assert [r["year"] for r in years] == [2002, 2006, 2010, 2014, 2018, 2022]
    assert all(r["delta_turnout_pp"] < 0 for r in years[:-1])
    assert years[-1]["delta_turnout_pp"] == pytest.approx(0.3645953186844082)
    assert all(r["delta_absence_pp"] == -r["delta_turnout_pp"] for r in years)
    assert years[1]["turnout_1_pct"] == 83.25  # Fonte arredondada preservada.
    for r in DATA["turnout_model"]["scope_checks"]:
        assert abs(r["scope_difference_pp"]) < 0.01


def test_rolling_origin_has_no_future_information_and_selection_is_fragile():
    years = DATA["turnout_model"]["history"]
    results = T.retrospectiva(years)
    for rule in results:
        assert [r["year"] for r in rule["cases"]] == [2014, 2018, 2022]
        assert all(max(r["training_years"]) < r["year"] for r in rule["cases"])
    assert min(results, key=lambda r: r["mae_pp"])["id"] == "sem_mudanca"
    assert (
        min(T.retrospectiva(years, minimum=2), key=lambda r: r["mae_pp"])["id"]
        == "ultima"
    )
    changed = deepcopy(years)
    changed[-1]["delta_turnout_pp"] = 9.0
    for before, after in zip(results, T.retrospectiva(changed), strict=True):
        assert (
            before["cases"][-1]["prediction_delta_pp"]
            == after["cases"][-1]["prediction_delta_pp"]
        )


def test_historical_scenarios_change_volume_without_inventing_candidate_preferences():
    base = DATA["turnout_model"]["first_round"]
    for scenario in DATA["turnout_model"]["scenarios"]:
        assert scenario["attendance"] + scenario["absence"] == pytest.approx(
            base["electorate"]
        )
        assert scenario["attendance"] - base["attendance"] == pytest.approx(
            scenario["delta_attendance"], abs=1e-7
        )
        for centre in ("media", "projecao"):
            result = M.evaluate(
                DATA, {"centro": centre, "comparecimento": scenario["turnout_pct"]}
            )
            total = C.counts(result, DATA["electorate"])
            central = M.evaluate(DATA, {"centro": centre})
            assert total["comparecimento"] == pytest.approx(scenario["attendance"])
            assert total["abstencao"] == pytest.approx(scenario["absence"])
            assert total["validos"] + total["branco_nulo"] + total[
                "abstencao"
            ] == pytest.approx(base["electorate"])
            # Nenhuma taxa satura nestas analogias; ausência comum escala volumes.
            assert result["flavio"] == pytest.approx(central["flavio"])


def sample(**changes):
    return {
        "CD_CARGO": "1",
        "NR_TURNO": "1",
        "SG_UF": "SP",
        "CD_MUNICIPIO": "1",
        "NR_ZONA": "1",
        "NR_SECAO": "1",
        "DT_GERACAO": "01/01/2024",
        "QT_APTOS": "100",
        "QT_COMPARECIMENTO": "80",
        "QT_ABSTENCOES": "20",
        **changes,
    }


def test_source_parser_does_not_double_count_cargos_or_exterior():
    _, totals = F.aggregate(
        [
            sample(),
            sample(CD_CARGO="3"),
            sample(SG_UF="ZZ", QT_APTOS="10", QT_COMPARECIMENTO="4", QT_ABSTENCOES="6"),
            sample(NR_TURNO="2"),
        ]
    )
    domestic = next(r for r in totals if r["scope"] == "Brasil" and r["turno"] == 1)
    whole = next(
        r for r in totals if r["scope"] == "Brasil e exterior" and r["turno"] == 1
    )
    assert domestic["QT_APTOS"] == 100 and whole["QT_APTOS"] == 110
    with pytest.raises(ValueError, match="repetida"):
        F.aggregate([sample(), sample()])
    with pytest.raises(ValueError, match="não fecha"):
        F.aggregate([sample(QT_COMPARECIMENTO="81")])
    _, residual = F.aggregate([sample(QT_COMPARECIMENTO="0", QT_ABSTENCOES="0")])
    assert residual[0]["QT_APTOS"] == 100
    assert residual[0]["QT_ABSTENCOES"] == 0  # Não recodificar o resíduo como ausência.


def test_incomplete_or_unreconciled_first_round_fails(monkeypatch, tmp_path):
    official = json.loads(T.OFFICIAL.read_text())
    path = tmp_path / "presidente.json"
    monkeypatch.setattr(T, "OFFICIAL", path)
    official["ufs"][0]["secoes"] -= 1
    path.write_text(json.dumps(official))
    with pytest.raises(ValueError, match="fechada"):
        T.build()
    official["ufs"][0]["secoes"] += 1
    official["ufs"][0]["abstencao"] += 1
    path.write_text(json.dumps(official))
    with pytest.raises(ValueError, match="não fecha"):
        T.build()


def test_report_explains_history_without_javascript_and_links_data():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    assert page.select_one("#comparecimento-historico svg title") is not None
    assert len(page.select("[data-rs-turnout]")) == 9
    assert "79,16%" in page.select_one("#rs-turnout-readout").get_text()
    text = page.select_one("#comparecimento-historico").get_text()
    assert "não identifica a preferência de quem falta" in text
    assert "não é intervalo de confiança" in text
    assert "a seleção não é robusta ao corte" in text
