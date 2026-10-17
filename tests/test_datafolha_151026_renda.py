"""Íntegra de 15/10: bases ponderadas, não resposta e tendência comparável."""

import importlib
import json
from datetime import date
from pathlib import Path

import pytest

M = importlib.import_module("datafolha-151026-renda")
ENGINE = importlib.import_module("reponderacao-pnad")
PROJECTION = importlib.import_module("reponderacao-projecao")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


def test_official_report_reproduces_manifest_and_keeps_wave_identity():
    poll = M.datafolha()  # Verifica também os hashes das fontes congeladas.
    saved = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-14.json").read_text()
    )
    assert poll == saved
    assert poll["divulgacao"] == "2026-10-15"
    assert poll["campo"] == {"inicio": "2026-10-13", "fim": "2026-10-14"}
    assert poll["registro_tse"] == "BR-00466/2026"
    assert poll["fonte"]["publicado_em"] == "2026-10-16"
    assert poll["fonte"]["total_paginas"] == 42
    assert poll["fonte"]["paginas"]["2t_renda"] == 30
    assert not poll.get("ignorar")
    assert not poll["conferencia_painel"]["usado_na_onda_nova"]


def test_weighted_bases_preserve_unknown_income_mass_and_recompose_independent_margins():
    poll = M.datafolha()
    assert poll["renda"]["bases"] == [1172, 918, 335]
    assert poll["renda"]["perfil_tipo"] == "perfil_ponderado"
    assert poll["renda"]["nao_publicada_n"] == 95
    fraction = poll["renda"]["parcela_ajustada_pct"] / 100
    assert fraction == pytest.approx(2425 / 2520)
    assert set(poll["controles"]["2t"]) == {"renda", "sexo", "regiao"}
    assert max(v["residuo_max_abs"] for v in poll["controles"]["2t"].values()) < 1
    result = ENGINE.process_poll(poll, ENGINE.Benchmark(), ENGINE.load_ipca())
    for scenario in result["turnos"]["2t"]["cenarios"].values():
        for candidate, actual in scenario["ajustado"].items():
            expected = poll["publicado"]["2t"][candidate] + fraction * (
                scenario["contrafactual"][candidate]
                - poll["controles"]["2t"]["renda"]["recomposto"][candidate]
            )
            assert actual == pytest.approx(expected, abs=0.001)


def test_both_datafolha_waves_now_supply_adjusted_preferences_to_trend():
    data = ENGINE.build(date(2026, 10, 16))
    waves = [
        r
        for r in data["pesquisas"]
        if r["id"] in {"datafolha_2026-10-08", "datafolha_2026-10-14"}
    ]
    assert len(waves) == 2
    for wave in waves:
        row = PROJECTION.observation(wave, SIM.preferences, date(2026, 10, 16))
        assert row["income_available"]
        assert row["pnad"] != row["published"]
        expected = wave["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
        assert row["pnad"] == SIM.preferences(expected, wave["publicado"]["2t"])
    projection = PROJECTION.build(data, SIM.preferences)
    selected = [r for r in projection["selected"] if r["instituto"] == "Datafolha"]
    assert len(selected) == 1 and selected[0]["id"] == "datafolha_2026-10-14"
    assert selected[0]["income_available"]
