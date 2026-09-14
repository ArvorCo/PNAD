"""Guard the September dossier against transposed columns and invented flows."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/nexus_btg_140926_data.json").read_text())


def test_income_reading_and_anchor():
    r = DATA["reweight"]["turnos"]["2t"]
    assert r["recomposto"]["lula"] == pytest.approx(47.35)
    assert r["recomposto"]["flavio"] == pytest.approx(45.72)
    a = r["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert a["lula"] == pytest.approx(46.688, abs=0.001)
    assert a["flavio"] == pytest.approx(46.404, abs=0.001)
    assert 0 < a["lula"] - a["flavio"] < 0.3  # Does NOT reverse this wave.
    for ballot in ["1t", "2t"]:
        assert DATA["reweight"]["turnos"][ballot]["residuo_max"] < 0.6


def test_sankey_preserves_all_measured_rows_and_margins():
    for d in [DATA["transfer"], *DATA["transfer_alternatives"]]:
        m = np.array(d["matrix"])
        np.testing.assert_allclose(m.sum(axis=0), [47, 46, 6, 1], atol=1e-8)
        np.testing.assert_allclose(
            m.sum(axis=1), [42, 37, 6, 5, 2, 1, 1, 4, 2], atol=1e-8
        )
        assert np.all(m >= 0)
        np.testing.assert_array_equal(m[0], [42, 0, 0, 0])
        np.testing.assert_array_equal(m[1], [0, 37, 0, 0])
        assert d["consolidated_rows"] == [0, 1]
        assert d["estimated_rows"] == [7, 8]
        for i in d["measured_rows"]:
            published = np.array(d["published_conditional"][d["sources"][i]])
            np.testing.assert_allclose(m[i] / m[i].sum(), published / published.sum())
    # Priors actually change the unknown paths, so they are not measured.
    assert (
        DATA["transfer"]["matrix"][7] != DATA["transfer_alternatives"][0]["matrix"][7]
    )


def test_frechet_bounds_do_not_assume_independence():
    b = DATA["useful_vote_bounds"]
    assert sum(r["lower_pp"] for r in b) == pytest.approx(0.65)
    assert sum(r["upper_pp"] for r in b) == pytest.approx(5.97)
    for r in b:
        assert 0 <= r["lower_pp"] <= r["upper_pp"] <= r["share"]


def test_history_matches_each_original_wave():
    h = DATA["published_history"]
    for p in DATA["history"]:
        date = p["divulgacao"][8:] + "/" + p["divulgacao"][5:7]
        i = h["dates"].index(date)
        for ballot, prefix in [("1t", "first"), ("2t", "second")]:
            for name in ["lula", "flavio"]:
                assert (
                    p["turnos"][ballot]["publicado"][name] == h[f"{prefix}_{name}"][i]
                )
    assert len(h["dates"]) == 14


def test_pdf_parser_fails_closed_on_missing_label():
    spec = importlib.util.spec_from_file_location(
        "audit", ROOT / "scripts/nexus-btg-140926-audit.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with pytest.raises(ValueError):
        mod.table(["Wrong 1% 2%"], 1, ["Lula"], 2)
    with pytest.raises(ValueError):
        mod.table(["Lula 1% 2%"], 1, ["Lula"], 3)


def test_aggregator_and_dossier_use_identical_result():
    aggregator = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    entry = next(p for p in aggregator["pesquisas"] if p["id"] == "nexus_2026-09-13")
    assert entry["turnos"] == DATA["reweight"]["turnos"]
    assert entry["dossie"] == "nexus_btg_140926.html"
    assert len(DATA["profile_tables"]) == 32
