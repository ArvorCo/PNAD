"""Resíduo do 1T, universo comparável e limites de identificação."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

P = importlib.import_module("reponderacao-presenca")
M = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())
FORECAST = json.loads((ROOT / "docs/assets/reponderacao_validos.json").read_text())
NEXUS = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())


def test_reference_is_frozen_pre_election_and_uses_domestic_counts():
    model = P.build(FORECAST, NEXUS)
    assert model == DATA["presence_model"]
    assert model["forecast_generated_at"] == "2026-10-04T01:22:40-03:00"
    assert model["forecast_published_commit"] == "1688f007"
    assert hashlib.sha256(P.PREDICTION.read_bytes()).hexdigest() == P.FORECAST_SHA256
    assert model["observed_votes"]["flavio"] == 55_960_603
    assert model["observed_votes"]["lula"] == 53_722_151
    assert model["predicted_votes"]["flavio"] == pytest.approx(54_116_051.386426955)
    assert model["central"]["equivalent_extra_pct"] == pytest.approx(3.8295536732134483)
    assert DATA["defaults"]["presenca_relativa"] == model["central_extra_pct"] == 3.8
    assert 100 * (model["nexus_1t_base_ratio"] - 1) == pytest.approx(
        0.030656719021848744
    )


def test_ratio_calibration_recovers_known_multiplier_but_not_full_vector():
    known = P.comparison(
        {"flavio": 40, "lula": 40, "validos": 100},
        {"flavio": 42, "lula": 40, "validos": 102},
    )
    assert known["equivalent_extra_pct"] == pytest.approx(5)
    c = DATA["presence_model"]["central"]
    after, target = c["after_multiplier_valid_pct"], c["observed_valid_pct"]
    assert after["flavio"] / after["lula"] == pytest.approx(
        target["flavio"] / target["lula"]
    )
    assert after["flavio"] != pytest.approx(target["flavio"], abs=0.1)
    assert c["flavio_vs_all_others_pct"] == pytest.approx(7.384683242224632)


def test_same_vote_and_absence_counts_allow_opposite_relative_presence():
    # Dois conjuntos de preferências dos ausentes reproduzem a mesma urna.
    f, lula, absence = 40, 40, 20
    all_absent_prefer_f = (f / (f + absence)) / 1
    all_absent_prefer_l = 1 / (lula / (lula + absence))
    assert all_absent_prefer_f < 1 < all_absent_prefer_l
    assert (f + absence) * all_absent_prefer_f == pytest.approx(f)
    assert (lula + absence) / all_absent_prefer_l == pytest.approx(lula)


def test_anchor_and_house_disagreement_is_exposed_not_an_interval():
    model = DATA["presence_model"]
    assert model["alternatives"][0]["equivalent_extra_pct"] == pytest.approx(
        4.34733759002206
    )
    assert len(model["houses"]) == 7
    assert model["house_range_pct"][0] == pytest.approx(-7.0773779099769225, abs=1e-8)
    assert model["house_range_pct"][1] == pytest.approx(16.60793776449254, abs=1e-8)
    assert "não é IC" in model["limits"]
    assert "podem já absorver" in model["limits"]


def test_rounding_and_old_five_percent_scenario_preserve_all_other_parameters():
    archived = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/0e0f4566cb2fd88a.json").read_text()
    )
    assert archived["defaults"]["presenca_relativa"] == 5
    for centre in ("media", "projecao"):
        actual = M.evaluate(
            {**DATA, "undecided_policy": "per_poll"},
            {"centro": centre, "presenca_relativa": 5},
        )
        previous = M.evaluate(archived, {"centro": centre})
        for k in ("flavio", "lula", "validos", "branco_nulo", "abstencao"):
            assert actual[k] == pytest.approx(previous[k], abs=1e-9, rel=0)
        central = M.evaluate(DATA, {"centro": centre})
        assert central["flavio"] < actual["flavio"]
        assert central["comparecimento"] == actual["comparecimento"]
        assert sum(central["por_100_eleitores"].values()) == pytest.approx(100)


def test_public_explanation_works_without_js_and_preserves_neutral_preset():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    section = page.select_one("#presenca-primeiro-turno")
    assert "+3,83%" in section.get_text()
    assert "não mede a presença real por candidato" in section.get_text()
    assert page.select_one('[data-rs-preset="igual"]')
    assert page.select_one('[data-rs-preset="fcinco"]')
    assert page.select_one('[data-param="presenca_relativa"]')["step"] == "0.1"


def test_modified_forecast_fails_instead_of_backdating_fit(tmp_path, monkeypatch):
    changed = tmp_path / "prediction.json"
    changed.write_bytes(P.PREDICTION.read_bytes() + b"\n")
    monkeypatch.setattr(P, "PREDICTION", changed)
    with pytest.raises(ValueError, match="versão publicada antes"):
        P.build(FORECAST, NEXUS)
