"""Ruído de ponto flutuante não esconde mudança de dado, tipo ou estrutura."""

from math import inf, nextafter

import pytest


def test_snapshot_accepts_machine_roundoff_only(assert_json_close):
    assert_json_close(
        {"votos": [{"pct": nextafter(45.3377321637154, inf)}], "n": 2154},
        {"votos": [{"pct": 45.3377321637154}], "n": 2154},
    )


@pytest.mark.parametrize(
    "changed",
    [
        {"pct": 45.0 + 1e-8, "fonte": "Quaest", "n": 2154},
        {"pct": 45.0, "fonte": "Outra", "n": 2154},
        {"pct": 45.0, "fonte": "Quaest", "n": 2154.0},
        {"pct": 45.0, "fonte": "Quaest"},
        {"pct": float("nan"), "fonte": "Quaest", "n": 2154},
    ],
)
def test_snapshot_rejects_material_or_structural_changes(assert_json_close, changed):
    with pytest.raises(AssertionError):
        assert_json_close(changed, {"pct": 45.0, "fonte": "Quaest", "n": 2154})
