"""Comparações temporais sem duplicar casas, revisões ou ondas fora do recorte."""

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
HOUSE = importlib.import_module("reponderacao-efeito-casa")
VIEW = importlib.import_module("reponderacao-metodos")


def poll(name, day, lula=45, flavio=45, *, ident=None, release=None):
    return {
        "id": ident or f"{name}_{day}",
        "instituto": name,
        "campo": {"inicio": day, "fim": day},
        "divulgacao": release or day,
        "publicado": {"2t": {"lula": lula, "flavio": flavio}},
    }


def peers():
    return [
        poll("B", "2026-09-10"),
        poll("C", "2026-09-10", 44, 46),
        poll("D", "2026-09-10", 46, 44),
    ]


def test_valid_vote_normalization_removes_nonchoice_scale():
    assert HOUSE.valid_gap(poll("A", "2026-09-10", 50, 40)) == pytest.approx(100 / 9)
    assert HOUSE.valid_gap(poll("A", "2026-09-10", 40, 32)) == pytest.approx(100 / 9)


def test_one_nearest_wave_per_other_house_and_no_self_comparison():
    rows = [
        *peers(),
        poll("A", "2026-09-10", 50, 40),
        poll("A", "2026-09-09", 90, 10),
        poll("B", "2026-09-09", 90, 10),
        poll("B", "2026-09-11", 90, 10),
    ]
    result = HOUSE.compare(rows, "2026-09-21")["A"]
    wave = next(w for w in result["ondas"] if w["id"] == "A_2026-09-10")
    assert wave["mediana_outros"] == 0
    assert wave["desvio"] == pytest.approx(100 / 9)
    assert {p["id"] for p in wave["pares"]} == {
        "B_2026-09-10",
        "C_2026-09-10",
        "D_2026-09-10",
    }


def test_minimum_three_distinct_peers_not_three_polls():
    rows = [
        poll("A", "2026-09-10"),
        poll("B", "2026-09-10"),
        poll("B", "2026-09-11"),
        poll("C", "2026-09-10"),
    ]
    result = HOUSE.compare(rows, "2026-09-21")["A"]
    assert result["n_ondas"] == 0
    assert result["desvio_mediano"] is None


def test_window_and_publication_cutoff_are_enforced():
    rows = [
        *peers(),
        poll("A", "2026-09-10"),
        poll("E", "2026-09-18"),
        poll("F", "2026-09-10", release="2026-09-22"),
        poll("A", "2026-07-01"),
    ]
    result = HOUSE.compare(rows, "2026-09-21")["A"]
    assert result["n_ondas"] == 1
    assert {p["instituto"] for p in result["ondas"][0]["pares"]} == {"B", "C", "D"}


def test_announced_poll_without_confirmed_release_is_not_a_peer():
    announced = poll("Pending", "2026-09-10", 90, 10)
    announced["divulgacao"] = None
    rows = [*peers(), poll("A", "2026-09-10"), announced]
    result = HOUSE.compare(rows, "2026-09-24")
    assert "Pending" not in result
    assert {p["instituto"] for p in result["A"]["ondas"][0]["pares"]} == {"B", "C", "D"}


def test_field_midpoint_controls_matching_and_boundary_is_inclusive():
    a = poll("A", "2026-09-16")
    a["campo"]["inicio"] = "2026-09-04"  # central date September 10
    rows = [*peers(), a, poll("E", "2026-09-17"), poll("F", "2026-09-18")]
    result = HOUSE.compare(rows, "2026-09-21")["A"]["ondas"][0]
    assert {p["instituto"] for p in result["pares"]} == {"B", "C", "D", "E"}


def test_revisions_replace_same_sample_even_when_excluded_from_income():
    first = poll("A", "2026-09-10", 50, 40, ident="a", release="2026-09-11")
    revised = poll("A", "2026-09-10", 40, 50, ident="a_v2", release="2026-09-21")
    revised["ignorar"] = True
    result = HOUSE.compare([*peers(), first, revised], "2026-09-21")["A"]
    assert result["n_ondas"] == 1
    assert result["ondas"][0]["id"] == "a_v2"
    assert result["desvio_mediano"] == pytest.approx(-100 / 9)
    old = HOUSE.compare([*peers(), first, revised], "2026-09-20")["A"]
    assert old["desvio_mediano"] == pytest.approx(100 / 9)


def test_house_summary_is_median_not_weighted_by_frequency_or_sample_size():
    rows = [
        *peers(),
        poll("A", "2026-09-09", 40, 50),
        poll("A", "2026-09-10"),
        poll("A", "2026-09-11", 90, 10),
    ]
    result = HOUSE.compare(rows, "2026-09-21")["A"]
    assert result["desvio_mediano"] == 0
    assert result["direcao"] == "Próximo da mediana"
    assert result["n_ondas"] == 3


def test_manifest_sources_and_questionnaire_hashes_are_complete():
    data = VIEW.load_data()
    assert len(data["institutos"]) == 13
    for row in data["institutos"]:
        assert len(row["criterios"]) == 10
        assert 0 <= row["nota"] <= 10
        q = ROOT / "docs" / row["fonte_questionario"]
        assert (
            hashlib.sha256(q.read_bytes()).hexdigest()
            == row["proveniencia"]["questionario_sha256"]
        )
        registry = (ROOT / "docs" / row["fonte_registro"]).read_text()
        assert row["registro_tse"] in registry
        assert "Metodologia de pesquisa:" in registry
        assert "Sistema interno de controle" in registry
    names = {r["instituto"] for r in data["institutos"]}
    assert {"Futura", "Meio/Ideia", "Vox Brasil"} <= names


def test_published_comparisons_keep_only_latest_palver_revision():
    data = VIEW.load_data()
    palver = next(r for r in data["institutos"] if r["instituto"] == "Palver")
    ids = {w["id"] for w in palver["sinal"]["ondas"]}
    assert "palver_2026-09-07_v2" in ids
    assert "palver_2026-09-07" not in ids
    assert all(
        p["instituto"] != "Palver" for w in palver["sinal"]["ondas"] for p in w["pares"]
    )
    assert VIEW.date_label("2026-09-21") == "21/09"


def test_invalid_scores_and_impossible_poll_percentages_fail_closed():
    with pytest.raises(ValueError):
        VIEW.score({"criterios": []})
    with pytest.raises(ValueError):
        HOUSE.valid_gap(poll("A", "2026-09-10", 65, 65))
