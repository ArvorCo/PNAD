import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/nexus-btg-240826-audit.py"
SPEC = importlib.util.spec_from_file_location("nexus_btg_240826_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def test_income_sensitivity_flips_runoff_gap():
    target = [13.4976847, 21.9424334, 39.2311391, 25.3287428]
    result = AUDIT.reweight(
        AUDIT.CROSSTABS["runoff"]["income"],
        AUDIT.PROFILE["income"],
        target,
        AUDIT.TOPLINES["runoff"],
    )
    assert result["anchored"][0] == 45.405
    assert result["anchored"][1] == 45.835
    assert result["gap"] == -0.43


def test_transfer_ipf_closes_published_margins():
    result = AUDIT.transfer_ipf()
    matrix = np.asarray(result["matrix"])
    assert np.allclose(matrix.sum(axis=0), AUDIT.TRANSFER_COLS, atol=0.003)
    assert np.allclose(matrix.sum(axis=1), AUDIT.TRANSFER_ROWS, atol=0.003)
    assert result["measured_pool"]["ratio_flavio_lula"] == 2.553


def test_first_round_lead_is_fragile_even_under_srs():
    result = AUDIT.margin_of_difference()
    assert result["first"]["interval95_srs"][0] == 0.139
    assert result["first"]["deff_to_erase_lead"] == 1.073
    assert result["runoff"]["srs_already_includes_zero"] is True


def test_question_publication_inventory_keeps_absent_items_explicit():
    result = AUDIT.omissions_summary()
    assert result["fully_absent_items"] == ["P19", "P21", "PF14", "PF17"]
    assert "P25" in result["partial_items"]


def test_migration_and_vote_potential_are_kept_separate():
    result = AUDIT.useful_vote_sensitivity()
    assert result["totals"]["potential"] == 6.7
    assert result["totals"]["migration_printed"] == 7.35
    assert result["totals"]["migration_lula_printed"] == 2.25
    assert result["totals"]["migration_normalized"] == 7.314
    assert result["totals"]["max_entropy"] == 3.859
    assert result["totals"]["max_entropy_lula"] == 1.197
    assert result["totals"]["joint_lower"] == 1.254
    assert result["totals"]["joint_upper"] == 6.27
    assert result["scenarios"]["partial_identification_range"] == [38.254, 43.27]
    assert result["scenarios"]["full_migration_using_printed_cells"] == 44.35
    assert result["scenarios"]["full_migration_lula_using_printed_cells"] == 43.25
    assert result["scenarios"]["maximum_entropy_ns_imputed"] == 40.859
    assert result["scenarios"]["maximum_entropy_lula_ns_imputed"] == 42.197
