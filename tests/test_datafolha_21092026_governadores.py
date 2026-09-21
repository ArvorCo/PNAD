"""Cross-office gaps are not contradictions; overlap bounds need common weights."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "docs/assets/datafolha_21092026_governadores.json").read_text())
STATES = {s["uf"]: s for s in D["states"]}
spec = importlib.util.spec_from_file_location(
    "governors", ROOT / "scripts/datafolha-21092026-governadores.py"
)
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)


def test_all_governor_tables_are_extracted():
    assert len(D["tables"]["SP"]["governor"]) == 13
    assert len(D["tables"]["MG"]["governor"]) == 14
    for state in D["tables"].values():
        for table in state["governor"].values():
            blocks = list(table["blocks"].values())
            assert len(blocks) == 3
            assert all(list(b["rows"]) == list(blocks[0]["rows"]) for b in blocks)


def test_identical_field_bases_and_matching_turns():
    for uf in STATES:
        _g, gb = MOD.FLAT(D["tables"][uf]["governor"]["turno2"])
        _p, pb = MOD.FLAT(D["tables"][uf]["president"]["turno2"])
        assert gb == pb
        assert STATES[uf]["field"] == "08–10/09/2026"
        assert "mesmos pesos" in " ".join(STATES[uf]["assumptions"])
    assert STATES["MG"]["governor"] == [59, 24]
    assert STATES["MG"]["president"] == [46, 45]
    assert STATES["SP"]["governor"] == [56, 35]
    assert STATES["SP"]["president"] == [42, 47]


def test_marginal_difference_is_not_measured_overlap():
    assert STATES["MG"]["gap_governor_flavio"] == 14
    assert STATES["SP"]["gap_governor_flavio"] == 9
    assert STATES["MG"]["overlap_topline"] == [5, 46]
    assert STATES["SP"]["overlap_topline"] == [0, 42]
    assert STATES["MG"]["overlap_topline_rounding"][0] == 4


def test_party_preference_bounds_including_rounding():
    assert STATES["MG"]["pt"]["overlap"] == [31, 34]
    assert STATES["SP"]["pt"]["overlap"] == [14, 19]
    assert STATES["MG"]["pt"]["overlap_rounding"] == [30, 34.5]
    assert STATES["SP"]["pt"]["overlap_rounding"] == [13, 19.5]
    assert STATES["MG"]["pt"]["state_lower_rounding"] == pytest.approx(30 * 291 / 1204)
    assert STATES["SP"]["pt"]["state_lower_rounding"] == pytest.approx(13 * 387 / 1610)
    # Frechet bounds yield nonnegative 2×2 cells and preserve BOTH marginals.
    for uf in STATES:
        a, b = STATES[uf]["pt"]["governor"], STATES[uf]["pt"]["lula"]
        for both in MOD.overlap(a, b):
            cells = [both, a - both, b - both, 100 - a - b + both]
            assert min(cells) >= 0 and sum(cells) == 100
            assert cells[0] + cells[1] == a and cells[0] + cells[2] == b


def test_checks_do_not_claim_rounding_as_fraud():
    checks = [p for state in STATES.values() for p in state["proofs"]]
    assert len(checks) == 486
    assert max(abs(p["residual"]) for p in checks) < 0.9
    assert not any(state["flags_over_1_05pp"] for state in STATES.values())
    html = (ROOT / "docs/datafolha_21092026.html").read_text()
    assert 'id="governadores"' in html
    assert "inconsistência aritmética não demonstrada" in html
    assert "Matriz governador × presidente por estado" in html


def test_public_pdfs_reproduce_archived_tables():
    for uf, offset in [("SP", 23), ("MG", 24)]:
        pdf = ROOT / f"docs/fontes/datafolha_21092026_governador_{uf.lower()}.pdf"
        assert MOD.extract(pdf, MOD.PAGES[uf], offset) == D["tables"][uf]["governor"]
