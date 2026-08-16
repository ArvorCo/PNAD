import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/quaest-globo-140826-audit.py"
SPEC = importlib.util.spec_from_file_location("quaest_globo_140826_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_transcribed_partitions_close():
    MODULE.validate_transcriptions()


def test_ipf_closes_published_margins():
    payload = MODULE.transfer_payload()
    matrix = payload["matrix"]

    for source, expected in payload["sources"].items():
        assert sum(matrix[source].values()) == pytest.approx(expected, abs=0.003)
    for target, expected in payload["targets"].items():
        observed = sum(row[target] for row in matrix.values())
        assert observed == pytest.approx(expected, abs=0.004)
    assert payload["outside_base_gain"]["Flávio_to_Lula_ratio"] == 1.768


def test_positioning_crossbreak_recomposes_topline():
    control = MODULE.positioning_control()

    assert control["recomposed"]["Lula"] == 37.4
    assert control["recomposed"]["Flávio"] == 31.09
    assert control["published"] == {"Lula": 38, "Flávio": 31}


def test_runoff_difference_is_not_clear_under_srs():
    uncertainty = MODULE.uncertainty_payload()

    assert uncertainty["runoff"]["difference_interval_95"] == [-0.99, 6.99]
    assert uncertainty["runoff"]["statistically_clear_under_srs"] is False


def test_region_partition_yields_addressable_ceiling():
    region = MODULE.conversion_gaps()["closed_partitions"]["region"]

    assert region["addressable_ceiling_gap"] == 7.44
