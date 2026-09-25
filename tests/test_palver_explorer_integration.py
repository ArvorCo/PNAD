"""Full historical coverage must not contaminate the eligible polling averages."""

import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"


def test_all_versions_visible_but_only_unique_eligible_waves_enter_means():
    data = json.loads((ASSETS / "reponderacao_pnad.json").read_text())
    active = {p["id"]: p for p in data["pesquisas"] if p["instituto"] == "Palver"}
    assert set(active) == {
        "palver_2026-08-09",
        "palver_2026-09-07_v2",
        "palver_2026-09-18",
        "palver_2026-09-23",
    }
    assert set(active["palver_2026-09-07_v2"]["turnos"]) == {"2t"}
    assert all("2t" in p["turnos"] for p in active.values())
    assert sum("1t" in p["turnos"] for p in active.values()) == 3
    history = json.loads((ASSETS / "palver_explorer_historico.json").read_text())[
        "pesquisas"
    ]
    assert len(history) == 4
    assert sum(p["substituida"] for p in history) == 1
    assert sum(p["primeiro_turno_com_marcal"] for p in history) == 2
    assert all(set(p["turnos"]) == {"1t", "2t"} for p in history)
    for p in active.values():
        assert all(t["residuo_max"] < 0.001 for t in p["turnos"].values())
    latest = active["palver_2026-09-18"]["turnos"]["2t"]["cenarios"][
        "pessoas16_efetivo"
    ]["ajustado"]
    assert latest["lula"] == pytest.approx(43.104, abs=0.001)
    assert latest["flavio"] == pytest.approx(46.889, abs=0.001)


def test_institute_panels_show_every_version_in_both_turns():
    soup = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    panels = soup.select('#institutos [data-instituto="Palver"]')
    assert len(panels) == 2
    for panel in panels:
        assert "4 ondas · 5 versões" in panel.get_text()
        svg_text = panel.find("svg").get_text()
        for label in ["09/08", "07/09 v1", "07/09 v2", "18/09", "23/09"]:
            assert label in svg_text
        assert "fora das médias" in panel.get_text()
    assert "com Marçal" in panels[1].get_text()
    chapter = soup.select_one("#palver-pesos").get_text()
    assert "revisada só entra como placar publicado" not in chapter
    assert "não há diagnóstico público da aderência" not in chapter
