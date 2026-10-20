"""Cobertura documental sem imputar PNAD nem misturar totais e válidos."""

import hashlib
import json
from copy import deepcopy

import pytest
from bs4 import BeautifulSoup
from reponderacao_vista.context import ROOT, D
from reponderacao_vista.historico_2t import SUPPLEMENT, history, phase, wave_count
from reponderacao_vista.historico_2t_chart import chart, segments


def history_at_update():
    data = deepcopy(D)
    data["referencia"] = "2026-10-20"
    return history(data)


def test_every_available_national_total_is_shown_even_without_income():
    actual = {p["id"]: p for p in history(palver=[])}
    for p in D["pesquisas"] + D["nao_reponderaveis"]:
        if p.get("publicado", {}).get("2t"):
            assert p["id"] in actual
            if "2t" not in p.get("turnos", {}):
                assert actual[p["id"]]["pnad"] is None


def test_real_time_keeps_seven_waves_but_only_one_income_adjustment():
    rows = [p for p in history_at_update() if p["instituto"] == "Real Time Big Data"]
    assert len(rows) == 7
    assert sum(p["pnad"] is not None for p in rows) == 1
    assert rows[0]["campo"]["fim"] == "2026-05-04"
    assert rows[0]["placar"]["flavio"] == 44
    assert rows[-1]["campo"]["fim"] == "2026-10-19"


def test_valid_only_wave_has_its_own_denominator_and_never_becomes_total():
    row = next(p for p in history() if p["id"] == "verita_2026-10-02")
    assert row["denominador"] == "validos"
    assert row["pnad"] is None
    assert row["placar"] == {"flavio": 51.56, "lula": 48.44}
    assert phase(row) == "Simulação antes do 1º turno"


def test_palver_versions_remain_documentary_without_duplicate_wave_count():
    rows = [p for p in history_at_update() if p["instituto"] == "Palver"]
    assert len(rows) == wave_count(rows) + 1
    assert sum(bool(p.get("substituida")) for p in rows) == 1
    assert not any(p.get("substituida") for s in segments(rows, "placar") for p in s)


def test_history_is_read_only_and_respects_publication_cutoff():
    data = deepcopy(D)
    before = deepcopy(data)
    history(data)
    assert data == before
    data["referencia"] = "2026-10-04"
    assert all(p["divulgacao"] <= "2026-10-04" for p in history(data))
    assert "verita_2026-10-02" not in {p["id"] for p in history(data)}


def test_missing_values_and_round_boundary_break_lines():
    rows = [p for p in history_at_update() if p["instituto"] == "Real Time Big Data"]
    assert [len(s) for s in segments(rows, "placar")] == [6, 1]
    assert [len(s) for s in segments(rows, "pnad")] == [1]
    synthetic = deepcopy(rows[:3])
    synthetic[0]["pnad"] = synthetic[0]["placar"]
    synthetic[2]["pnad"] = synthetic[2]["placar"]
    assert [len(s) for s in segments(synthetic, "pnad")] == [1, 1]


def test_chart_positions_are_elapsed_days_and_not_equal_wave_spacing():
    rows = [p for p in history_at_update() if p["instituto"] == "Real Time Big Data"]
    soup = BeautifulSoup(chart(rows), "html.parser")
    coordinates = [
        float(soup.select_one(f'[data-k="history2t|{p["id"]}"] circle')["cx"])
        for p in rows[:3]
    ]
    assert (coordinates[2] - coordinates[1]) / (
        coordinates[1] - coordinates[0]
    ) == pytest.approx(51 / 26)
    assert "04/10 · 1º turno" in soup.get_text()


def test_supplement_sources_match_archived_bytes_and_dates():
    rows = json.loads(SUPPLEMENT.read_text())["pesquisas"]
    assert len(rows) == 17
    assert len({p["id"] for p in rows}) == len(rows)
    for row in rows:
        assert row["campo"]["inicio"] <= row["campo"]["fim"] <= row["divulgacao"]
        assert row["campo"]["fim"] < "2026-10-04"
        ref = row["fonte"]
        blob = (ROOT / ref["arquivo"]).read_bytes()
        assert len(blob) == ref["bytes"]
        assert hashlib.sha256(blob).hexdigest() == ref["sha256"]
        assert 99 <= sum(row["publicado"]["2t"].values()) <= 101


def test_gerp_decimals_and_alfa_opponent_are_not_confused():
    rows = {p["id"]: p for p in history()}
    assert rows["gerp_2026-06-18"]["placar"]["flavio"] == 41.5
    assert rows["gerp_2026-06-18"]["placar"]["lula"] == 40.2
    assert rows["alfa_2026-07-28"]["placar"]["flavio"] == 41
    assert rows["alfa_2026-07-28"]["placar"]["lula"] == 48


def test_generated_page_and_exports_have_all_rows_and_valid_only_separate():
    soup = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    section = soup.select_one("#institutos-2t")
    rows = history()
    assert len(section.select("article")) == len({p["instituto"] for p in rows})
    assert {p["id"] for p in rows} == {
        r["data-history-id"] for r in section.select("tr[data-history-id]")
    }
    verita = section.select_one('[data-instituto="Veritá"]')
    main_svg = verita.select_one(".fig svg")
    assert main_svg.select_one('[data-k="history2t|verita_2026-10-02"]') is None
    assert (
        verita.select_one('details [data-k="history2t|verita_2026-10-02"]') is not None
    )
    exported = json.loads(
        (ROOT / "docs/assets/reponderacao_historico_2t.json").read_text()
    )
    assert {p["id"] for p in exported["pesquisas"]} == {p["id"] for p in rows}
