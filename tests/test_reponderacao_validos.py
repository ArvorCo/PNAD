"""Prediction identities, consistent cohorts, chronology and source transport."""

import copy
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
M = importlib.import_module("reponderacao-validos")
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
NEXUS = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())


@pytest.mark.parametrize("undecided", [0, 5, 30, 100])
def test_proportional_undecided_preserves_valid_shares_and_conserves_mass(undecided):
    result = M.allocate(
        {"a": 40, "b": 30, "c": 10}, {"a": 0.9, "b": 0.8, "c": 0.6}, undecided, 0.7
    )
    assert result["valid"] == pytest.approx(
        {"a": 100 * 36 / 66, "b": 100 * 24 / 66, "c": 100 * 6 / 66}
    )
    assert sum(result["allocated"].values()) == pytest.approx(0.7 * undecided)
    assert sum(result["valid"].values()) == pytest.approx(100)


@pytest.mark.parametrize("rate", [0.1, 0.5, 1])
def test_uniform_attendance_and_its_scale_cancel(rate):
    result = M.allocate(
        {"a": 45, "b": 35, "c": 10}, dict.fromkeys(["a", "b", "c"], rate)
    )
    assert result["valid"] == pytest.approx({"a": 50, "b": 100 * 35 / 90, "c": 100 / 9})


def test_negative_mass_or_invalid_turnout_fails():
    with pytest.raises(ValueError):
        M.allocate({"a": -1, "b": 40}, {"a": 0.8, "b": 0.8})
    with pytest.raises(ValueError):
        M.allocate({"a": 30}, {"a": 1.1})


def test_no_latest_turnout_information_backdated():
    data = copy.deepcopy(DATA)
    data["referencia"] = "2026-09-24"
    with pytest.raises(ValueError, match="later"):
        M.build(data, NEXUS)


def test_incomplete_positive_candidate_vector_is_excluded_not_called_nonchoice():
    realtime = next(p for p in DATA["pesquisas"] if p["id"] == "realtime_2026-09-23")
    with pytest.raises(ValueError, match="outros"):
        M.prepare(realtime, "1t")


def test_negative_anchored_residue_is_disclosed_without_mutating_original():
    p = next(p for p in DATA["pesquisas"] if p["id"] == "poderdata_2026-09-23")
    original = copy.deepcopy(p)
    row = M.prepare(p, "1t")
    assert row["adjusted"]["avalanche"] == 0
    assert row["negative_mass_removed"]["avalanche"] < 0
    assert p == original


def test_candidate_turnout_template_matches_expected_mass():
    for b in ["1t", "2t"]:
        s = NEXUS["turnout"]["central"][b]
        q = M.template(NEXUS, b, "central")
        values = dict(zip(q, s["population_choice_share"], strict=True))
        assert sum(values[k] * q[k] for k in q) == pytest.approx(s["achieved_turnout"])
        candidates = {k: v for k, v in values.items() if k not in M.NONCHOICE}
        assert list(M.allocate(candidates, q)["valid"].values()) == pytest.approx(
            s["valid"]
        )


def test_equal_house_average_normalizes_each_poll_first():
    # A low nonchoice poll must not receive more weight via denominator pooling.
    rows = [{"v": {"lula": 60, "flavio": 40}}, {"v": {"lula": 20, "flavio": 80}}]
    assert M.average(rows, "v", "2t") == {"lula": 40, "flavio": 60}


def test_all_modes_and_stress_scenarios_have_complete_same_cohort():
    data = copy.deepcopy(DATA)
    data["referencia"] = "2026-09-30"  # Cohort containing the documented PoderData wave.
    result = M.build(data, NEXUS)
    for b, block in result["ballots"].items():
        reference = block["scenarios"]["central"]["polls"]
        ids = [p["id"] for p in reference]
        for scenario in block["scenarios"].values():
            assert [p["id"] for p in scenario["polls"]] == ids
            for mode, values in scenario["aggregate"].items():
                assert sum(values.values()) == pytest.approx(100)
                assert all(0 <= v <= 100 for v in values.values())
                if mode != "modelo":
                    assert values == block["scenarios"]["central"]["aggregate"][mode]
        assert (
            block["scenarios"]["flavio95"]["aggregate"]["modelo"]["flavio"]
            < block["scenarios"]["central"]["aggregate"]["modelo"]["flavio"]
            < block["scenarios"]["flavio105"]["aggregate"]["modelo"]["flavio"]
        )
        if b == "1t":
            values = block["scenarios"]["central"]["aggregate"]["modelo"]
            assert values["lula"] + values["flavio"] < 100
        else:
            pd = next(p for p in reference if p["instituto"] == "PoderData")
            assert not pd["undecided_known"]


@pytest.mark.parametrize("missing_turn", [True, False])
def test_latest_incomplete_wave_does_not_fall_back_to_older_wave(missing_turn):
    data = copy.deepcopy(DATA)
    new = copy.deepcopy(
        next(p for p in data["pesquisas"] if p["id"] == "nexus_2026-09-27")
    )
    new["id"] = "nexus_incomplete"
    new["divulgacao"] = "2026-09-29"
    new["publicado"]["1t"]["missing"] = 1
    if missing_turn:
        del new["turnos"]["1t"]
    data["referencia"] = "2026-09-29"
    data["pesquisas"].append(new)
    result = M.build(data, NEXUS)
    assert all(
        p["instituto"] != "Nexus"
        for p in result["ballots"]["1t"]["scenarios"]["central"]["polls"]
    )
    assert any(
        p["id"] == "nexus_incomplete" for p in result["ballots"]["1t"]["excluded"]
    )
