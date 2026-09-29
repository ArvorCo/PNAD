"""Scientific invariants: turnout calibration, partial identification and fixed flows."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


AUDIT = load("nexus-btg-28092026-audit")
LV = load("nexus-btg-28092026-turnout")
D = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())


@pytest.mark.parametrize("retention", [0.97, 0.98, 1])
def test_measured_transitions_stay_fixed_and_margins_close(retention):
    t = AUDIT.transfer(retention)
    m = np.array(t["matrix"])
    np.testing.assert_allclose(m.sum(0), t["column_targets"], atol=1e-9)
    np.testing.assert_allclose(m.sum(1), t["row_targets"], atol=1e-9)
    for i, v in AUDIT.MEASURED.items():
        np.testing.assert_allclose(m[i] / m[i].sum(), np.array(v) / sum(v))
    assert m[0, 1] == m[1, 0] == 0
    assert m[0, 0] / m[0].sum() == pytest.approx(retention)


def test_infeasible_retention_is_rejected():
    with pytest.raises(ValueError, match="leakage"):
        AUDIT.transfer(0.95)


@pytest.mark.parametrize("ballot", ["1t", "2t"])
def test_alternative_associations_preserve_observed_margins(ballot):
    j, t = LV.joint_table(D["poll"]["publicado"][ballot], D["tables"], ballot)
    for seed in [-1, 1]:
        other, _ = LV.joint_table(
            D["poll"]["publicado"][ballot], D["tables"], ballot, seed
        )
        assert not np.allclose(j, other)
        for d, target in enumerate(t):
            np.testing.assert_allclose(
                other.sum(tuple(k for k in range(4) if k not in (d, 3))),
                target,
                atol=1e-10,
            )


@pytest.mark.parametrize("ballot", ["1t", "2t"])
def test_calibration_and_valid_denominator(ballot):
    c = D["turnout"]["central"][ballot]
    assert c["target_turnout"] == pytest.approx(c["achieved_turnout"])
    assert sum(c["valid"]) == pytest.approx(100)
    assert sum(c["share_among_attendees"]) == pytest.approx(100)
    for v in c["segments"].values():
        for key in ["population_share", "voter_share", "absentee_share"]:
            assert sum(v[key]) == pytest.approx(100)
        assert all(0 < x < 100 for x in v["turnout"])
    assert len([s for s in D["turnout"]["scenarios"] if s["ballot"] == ballot]) == 54


def test_first_round_other_candidates_remain_valid_votes():
    out = LV.candidate_valid([42, 37, 5, 5, 4, 1, 1, 3, 2])
    assert out[0] == pytest.approx(100 * 42 / 95)
    assert len(out) == 7


@pytest.mark.parametrize("ballot", ["1t", "2t"])
def test_age_stress_preserves_national_total_and_hits_older_target(ballot):
    for scenario in D["turnout"]["age_stress"][ballot]:
        assert scenario["achieved_turnout"] == pytest.approx(
            D["turnout"]["central"][ballot]["target_turnout"]
        )
        assert scenario["segments"]["idade"]["turnout"][3] == pytest.approx(
            100 * scenario["older_turnout"]
        )
        assert sum(scenario["valid"]) == pytest.approx(100)


def test_uniform_turnout_cancels_from_valid_votes():
    j, _ = LV.joint_table(D["poll"]["publicado"]["1t"], D["tables"], "1t")
    weights = [D["tables"][d]["weights"] for d in LV.DIMS]
    for target in [0.6, 0.8, 0.95]:
        r = LV.scenario(j, D["tables"], "1t", weights, target, [0.5] * 5, strength=0)
        np.testing.assert_allclose(r["valid"], r["before_valid"])


def test_frechet_bounds_on_known_two_candidate_example():
    # Half vote each; 80% attend. At least 30%/at most 50% of the electorate vote L.
    lo, hi = LV.frechet_runoff([[0.5, 0.5, 0, 0]], [0.8])
    assert lo == pytest.approx(37.5)
    assert hi == pytest.approx(62.5)


def test_income_adjustment_is_delta_anchored_not_renormalized():
    p = D["poll"]
    r = D["reweight"]
    source = LV.norm(p["renda"]["amostra_pct"])
    target = LV.norm(r["renda"]["pnad_pct"]["pessoas16_efetivo"])
    for b in ["1t", "2t"]:
        delta = (target - source) @ np.array(p["cruzamentos"][b]["linhas"])
        for i, k in enumerate(p["cruzamentos"][b]["opcoes"]):
            assert r["turnos"][b]["cenarios"]["pessoas16_efetivo"]["ajustado"][
                k
            ] == pytest.approx(p["publicado"][b][k] + delta[i], abs=0.001)


def test_published_evidence_and_aggregate_entry():
    html = (ROOT / "docs/nexus_btg_28092026.html").read_text()
    assert "—" not in html
    assert "intervalo de confiança" in html and "sem validação" in html
    assert "nexus_2026-09-27" in (ROOT / "docs/reponderacao_pnad.html").read_text()
    assert all(
        c[b]["max_residual"] < 1.1 for c in D["controls"].values() for b in ["1t", "2t"]
    )
