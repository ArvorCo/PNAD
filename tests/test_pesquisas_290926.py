"""New-wave provenance, recomposition and aggregation of published candidate groups."""

import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
BASE = ROOT / "analysis/reponderacao"
AUDIT = json.loads((BASE / "atualizacao_20260929/auditoria.json").read_text())
DATA = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
M = importlib.import_module("reponderacao-validos")
NEXUS = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())


def test_five_new_reports_are_archived_and_checksummed():
    assert len(AUDIT["fontes"]) == 5
    for item in AUDIT["fontes"]:
        src = item["fonte"]
        payload = (ROOT / src["pdf"]).read_bytes()
        assert payload.startswith(b"%PDF")
        assert len(payload) == src["bytes"]
        assert hashlib.sha256(payload).hexdigest() == src["sha256"]


def test_seven_new_crossbreaks_recompose_with_independent_sex_controls():
    assert len(AUDIT["controles"]) == 7
    for check in AUDIT["controles"]:
        assert check["renda_residuo_max_pp"] < 0.7
        assert check["controle_independente"]["residuo_max_pp"] < 0.5
    margins = json.loads(
        (BASE / "atualizacao_20260929/palver-margens.json").read_text()
    )
    for m in margins.values():
        assert m["identified"] and m["rank"] == len(m["groups"])
        assert m["max_residual"] < 1e-10
        assert m["reconstructed_neff"] == pytest.approx(m["published_neff"], abs=1e-6)


def test_quaest_other_group_matches_original_topline_without_double_counting():
    p = json.loads((BASE / "pesquisas/quaest_2026-09-27.json").read_text())
    detailed = p["publicado_detalhado"]["1t"]
    assert p["publicado"]["1t"]["outros"] == sum(
        v for k, v in detailed.items() if k not in M.NONCHOICE | {"lula", "flavio"}
    )
    assert sum(p["publicado"]["1t"].values()) == 100
    assert "cury" not in p["cruzamentos"]["1t"]["opcoes"]


def test_latest_quaest_enters_both_forecasts_at_its_actual_release():
    result = M.build(DATA, NEXUS)
    for ballot in ["1t", "2t"]:
        polls = result["ballots"][ballot]["scenarios"]["central"]["polls"]
        p = next(p for p in polls if p["instituto"] == "Quaest")
        # The election-eve wave (G1 panel) replaces 27/09 at its own release.
        assert p["id"] == "quaest_2026-10-03"
        assert p["divulgacao"] == "2026-10-03"
        assert not any(
            p["id"] in {"quaest_2026-09-20", "quaest_2026-09-27"} for p in polls
        )
    atlas = next(p for p in DATA["pesquisas"] if p["id"] == "atlas_2026-09-28")
    assert set(atlas["turnos"]) == {"1t"}
    assert any(p["id"] == "vox_brasil_2026-09-28" for p in DATA["nao_reponderaveis"])


def test_shared_partition_does_not_impute_unpublished_candidate_to_zero():
    rows = [
        {"v": {"lula": 40, "flavio": 40, "cury": 10, "caiado": 10}},
        {"v": {"lula": 50, "flavio": 40, "outros": 10}},
    ]
    assert M.average(rows, "v", "1t") == {"lula": 45, "flavio": 40, "demais": 15}


def test_aggregate_turnout_conserves_source_expected_attendees():
    p = next(p for p in DATA["pesquisas"] if p["id"] == "quaest_2026-09-27")
    row = M.prepare(p, "1t")
    rates = M.template(NEXUS, "1t", "central")
    q, pool = M.candidate_rates(row, NEXUS, "1t", rates)
    shares = dict(
        zip(
            NEXUS["poll"]["publicado"]["1t"],
            NEXUS["turnout"]["central"]["1t"]["population_choice_share"],
            strict=True,
        )
    )
    assert {"cury", "caiado", "renan_santos", "zema"} <= set(pool)
    assert not set(pool) & (M.NONCHOICE | {"lula", "flavio"})
    assert q["outros"] * sum(shares[k] for k in pool) == pytest.approx(
        sum(shares[k] * rates[k] for k in pool)
    )
    assert q["lula"] == rates["lula"] and q["flavio"] == rates["flavio"]


def test_gerp_conflicting_undecided_total_remains_explicit():
    p = json.loads((BASE / "pesquisas/gerp_2026-09-28.json").read_text())
    assert p["publicado"]["2t"]["indecisos"] == 1
    assert "2%" in p["fonte"]["nota"] and "1%" in p["fonte"]["nota"]
    assert p["fonte"]["paginas"]["2t_topline"] == 22
    assert p["fonte"]["paginas"]["2t_renda"] == 24
