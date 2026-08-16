import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts/quaest-globo-140826-estrategia.py"
SPEC = importlib.util.spec_from_file_location("quaest_globo_140826_estrategia", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

AUDIT = MODULE.load_audit()


def test_transcribed_crossbreaks_close():
    MODULE.validate(AUDIT)


def test_third_way_weighted_sum_recomposes_published_total():
    partitions = MODULE.third_way_geography(AUDIT)["partitions"]

    for label in ("region", "income"):
        assert partitions[label]["recomposed_third_way"] == pytest.approx(12, abs=0.5)


def test_third_way_sits_inside_flavio_territory():
    partitions = MODULE.third_way_geography(AUDIT)["partitions"]

    assert partitions["region"]["share_where_flavio_leads_or_ties_pct"] == 59.9
    assert partitions["income"]["share_where_flavio_leads_or_ties_pct"] == 81.2


def test_rejection_crossbreak_recomposes_published_rejection():
    control = MODULE.rejection_control(AUDIT)

    assert control["Flávio"]["recomposed_pct"] == pytest.approx(54, abs=0.2)
    assert control["Lula"]["recomposed_pct"] == pytest.approx(52, abs=0.3)
    assert control["independent_bloc"]["difference"] == -1


def test_single_round_threshold():
    single = MODULE.single_round_equation(AUDIT)

    assert single["base"]["declared_valid"] == 82
    assert single["points_needed"] == 10.0
    assert single["third_way_only_threshold_pct"] == 83.3
    assert single["non_choice_only_threshold_points"] == 20.0
    assert single["non_choice_route_possible"] is False


def test_soft_third_way_alone_is_not_enough():
    single = MODULE.single_round_equation(AUDIT)
    route = single["soft_vote_route"]

    assert route["mutable_points_available"] < single["points_needed"]
    assert route["non_choice_points_required"] == pytest.approx(7.86, abs=0.01)
    assert route["non_choice_share_required_pct"] == pytest.approx(43.6, abs=0.1)


def test_historic_consolidation_is_insufficient_by_itself():
    benchmark = MODULE.single_round_equation(AUDIT)["historic_benchmark"]

    for year in ("2018", "2022"):
        assert benchmark[year]["enough_even_if_all_went_to_flavio"] is False


def test_inevitability_premium_is_negative_in_every_published_cut():
    premium = MODULE.inevitability_premium(AUDIT)

    assert premium["national"]["Lula"] == 18
    assert premium["national"]["Flávio"] == -4
    for cut in premium["cuts"].values():
        assert cut["flavio_premium"] < 0
        assert cut["lula_premium"] > 0


def test_substitution_has_no_segment_where_caiado_beats_flavio():
    substitution = MODULE.substitution_by_segment(AUDIT)

    assert substitution["caiado_better_than_flavio"] == []
    assert substitution["tied"] == ["Superior"]


def test_interest_counterpoint_holds():
    interest = MODULE.interest_profile()

    assert interest["cuts"]["Muito interessado"]["lula_lead"] == 10
    assert interest["cuts"]["Nada interessado"]["non_choice"] == 35


def test_plan_crosswalk_cites_pages_on_both_sides():
    for row in MODULE.PLAN_CROSSWALK:
        assert row["plan_pages"]
        assert row["quaest_pages"]
        assert row["segments"]
