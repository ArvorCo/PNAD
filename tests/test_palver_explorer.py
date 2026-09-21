"""Public-table evidence checks, including excluded universes and weight moments."""

import json
from pathlib import Path

import numpy as np
import pytest

BASE = (
    Path(__file__).resolve().parents[1]
    / "analysis/reponderacao/palver_explorer_20260921"
)


def read(name):
    return json.loads((BASE / name).read_text())


def test_inventory_does_not_relabel_fallbacks_as_breakdowns():
    manifest = read("manifest.json")
    assert len(manifest["queries"]) == 196
    assert sum(q["tables"] for q in manifest["queries"]) == 186
    for q in manifest["queries"]:
        payload = read(q["file"])
        assert len(payload["tables"]) == q["tables"]
        assert len(q["html_sha256"]) == 64
        for table in payload["tables"]:
            assert table["wave_id"] == payload["selected"]["waveId"]
            assert table["breakdown_key"] == payload["selected"]["breakdownKey"]
            assert table["question_key"] == payload["selected"]["questionKey"]
            assert sum(s["n"] for s in table["group_stats"]) == table["base"]
            for s in table["group_stats"]:
                assert 0 < s["n_eff"] <= s["n"] + 1e-8


def test_income_margin_reproduces_independent_questions_and_kish():
    audit = read("audit.json")
    latest = audit["waves"][audit["latest_wave"]]
    margin = latest["margins"]["inc_std"]
    assert margin["raw_n"] == [1321, 2203, 1476]
    np.testing.assert_allclose(
        margin["weighted_pct"], [42.12294137, 39.56309619, 18.31396244]
    )
    assert len(audit["income_checks"]) == 43
    assert max(c["max_residual_pp"] for c in audit["income_checks"]) < 1e-9
    assert margin["reconstructed_neff"] == pytest.approx(1231.71085058142)
    assert audit["conditional_questions_not_recomposed"] == [
        {"question": "party_affiliated", "base": 556}
    ]
    assert latest["margins"]["identification_h"]["identified"] is False
    assert latest["margins"]["identification_h"]["base"] == 4924


def test_full_transfer_matrix_closes_against_measured_topline():
    audit = read("audit.json")
    latest = audit["waves"][audit["latest_wave"]]
    t = audit["transfer_1t_2t"]
    margin = latest["margins"]["stimulated_1r_vote_1_h"]
    weights = dict(
        zip(margin["groups"], np.array(margin["weighted_pct"]) / 100, strict=True)
    )
    total = latest["turns"]["2t"]["published_exact"]
    for answer in t["answers"]:
        recomposed = sum(
            weights[c["group"]] * c["share"] * 100
            for c in t["cells"]
            if c["answer"] == answer
        )
        assert recomposed == pytest.approx(total[answer], abs=1e-9)
    renan = {
        c["answer"]: c["share"]
        for c in t["cells"]
        if c["group"] == "Renan Santos (Missão)"
    }
    assert renan["Flávio Bolsonaro (PL)"] == pytest.approx(0.2529, abs=0.0001)
    assert renan["Lula (PT)"] == pytest.approx(0.0577, abs=0.0001)


def test_revised_wave_preserves_counts_and_marcal_scenario():
    audit = read("audit.json")
    assert audit["wave2_same_raw_vote_income_counts"] is True
    revised = audit["waves"]["02_pesquisa_2026_09_21"]["turns"]
    assert revised["1t"]["published_exact"]["Pablo Marçal (PRTB)"] > 0
    assert revised["1t"]["published_exact"]["Lula (PT)"] < 40.5
    assert revised["2t"]["income_standardized"]["pessoas16_efetivo"][
        "Flávio Bolsonaro (PL)"
    ] == pytest.approx(47.14, abs=0.01)


def test_exact_and_pdf_anchored_sensitivities_remain_distinct():
    audit = read("audit.json")
    t = audit["waves"][audit["latest_wave"]]["turns"]["2t"]
    exact = t["income_standardized"]["pessoas16_efetivo"]
    assert exact["Lula (PT)"] == pytest.approx(43.1039414)
    assert exact["Flávio Bolsonaro (PL)"] == pytest.approx(46.8893372)
    assert t["pdf_anchored_pair"]["lula"] == pytest.approx(43.18, abs=0.01)
    assert t["pdf_anchored_pair"]["flavio"] == pytest.approx(46.50, abs=0.01)
