"""Limites inclusivos, disponibilidade temporal e peso igual por instituto."""

import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "window", ROOT / "scripts/reponderacao-janela.py"
)
WINDOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WINDOW)


def row(ident, institute, release, value, field="2026-09-10"):
    return {
        "id": ident,
        "instituto": institute,
        "divulgacao": release,
        "campo": {"fim": field},
        "publicado": {"lula": value},
    }


def test_seven_days_include_today_and_six_previous_days_only():
    rows = [
        row("old", "A", "2026-09-14", 99),
        row("edge", "B", "2026-09-15", 20),
        row("today", "C", "2026-09-21", 40),
        row("future", "D", "2026-09-22", 99),
    ]
    assert {r["id"] for r in WINDOW.select(rows, date(2026, 9, 21))} == {
        "edge",
        "today",
    }
    assert WINDOW.mean(rows, "publicado", "lula", date(2026, 9, 21)) == 30


def test_equal_weight_per_institute_uses_latest_release_and_never_future():
    rows = [
        row("a1", "A", "2026-09-15", 80),
        row("a2", "A", "2026-09-19", 30),
        row("a3", "A", "2026-09-21", 40),
        row("b", "B", "2026-09-18", 20),
    ]
    assert WINDOW.mean(rows, "publicado", "lula", date(2026, 9, 21)) == 30
    before = WINDOW.mean(rows, "publicado", "lula", date(2026, 9, 20))
    assert before == 25
    assert (
        WINDOW.mean(
            rows + [row("future", "B", "2026-09-22", 100)],
            "publicado",
            "lula",
            date(2026, 9, 20),
        )
        == before
    )
    assert WINDOW.mean(rows, "publicado", "lula", date(2026, 9, 28)) is None
    assert WINDOW.select([row("undated", "A", None, 100)], date(2026, 9, 21)) == []


def test_every_daily_candidate_mean_matches_eligible_institutes():
    data = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    agg = data["agregador"]
    for turn in ("1t", "2t"):
        for i, text in enumerate(agg["serie"]["datas"]):
            day = date.fromisoformat(text)
            selected = {}
            for poll in sorted(
                data["pesquisas"],
                key=lambda p: (p["divulgacao"], p["campo"]["fim"], p["id"]),
            ):
                if (
                    turn in poll["turnos"]
                    and day - timedelta(days=6)
                    <= date.fromisoformat(poll["divulgacao"])
                    <= day
                ):
                    selected[poll["instituto"]] = poll
            coverage = agg["cobertura_movel"][turn][i]
            assert set(coverage["ondas"]) == {p["id"] for p in selected.values()}
            assert coverage["n_institutos"] == len(selected)
            for kind in ("publicado", "ajustado"):
                for key in ("lula", "flavio"):
                    actual = agg["serie"][turn][kind][key][i]
                    if not selected:
                        assert actual is None
                    else:
                        values = [
                            (
                                p["turnos"][turn]["publicado"][key]
                                if kind == "publicado"
                                else p["turnos"][turn]["cenarios"]["pessoas16_efetivo"][
                                    "ajustado"
                                ][key]
                            )
                            for p in selected.values()
                        ]
                        assert actual == pytest.approx(
                            sum(values) / len(values), abs=0.005001
                        )
        assert (
            agg["ultimo"][turn]["kernel"]["ajustado"]["lula"]
            == agg["serie"][turn]["ajustado"]["lula"][-1]
        )


def test_method_and_daily_coverage_are_visible():
    from bs4 import BeautifulSoup

    html = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    for turn in ("1t", "2t"):
        text = html.find(id=f"janela-{turn}").get_text(" ", strip=True)
        assert "dia observado e seis dias anteriores" in text
        assert "Sem média" in text
    assert "meia-vida" not in html.get_text()
