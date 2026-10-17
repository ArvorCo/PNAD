"""Veritá: denominadores, margem de renda e entrada temporal nas centrais."""

import importlib
import json
from datetime import date
from pathlib import Path

import pytest

M = importlib.import_module("verita-171026-renda")
ENGINE = importlib.import_module("reponderacao-pnad")
PROJECTION = importlib.import_module("reponderacao-projecao")
SIM = importlib.import_module("reponderacao-simulador")
ROOT = Path(__file__).resolve().parents[1]


def test_frozen_source_and_public_copy_reproduce_manifest():
    poll = M.verita()  # Inclui a validação de tamanho e SHA-256 das fontes.
    saved = ROOT / "analysis/reponderacao/pesquisas/verita_2026-10-16.json"
    assert poll == json.loads(saved.read_text())
    assert (ROOT / poll["fonte"]["arquivo"]).read_bytes() == (
        ROOT / "docs/fontes/verita_17102026.pdf"
    ).read_bytes()
    assert poll["fonte"]["paginas"]["2t_renda"] == 10
    assert poll["fonte"]["paginas_impressas"]["2t_renda"] == 14


def test_absent_subtotal_is_not_abstention_or_an_extra_category():
    poll = M.verita()
    pub = poll["publicado"]["2t"]
    assert sum(pub.values()) == pytest.approx(100)
    assert pub == {"flavio": 49.7, "lula": 47.7, "branco_nulo": 1.5, "indecisos": 1.1}
    assert SIM.preferences(pub, pub) == pub
    valid = poll["publicado_validos"]["2t"]
    assert valid["flavio"] == 51.1
    assert 100 * pub["flavio"] / (pub["flavio"] + pub["lula"]) != valid["flavio"]
    audit = poll["conferencia_denominadores"]
    assert not audit["abstencao_2t_medida"]
    assert pub["branco_nulo"] + pub["indecisos"] == audit["subtotal_ausente_pct"]
    counts = audit["frequencias_publicadas"]
    assert (
        counts["flavio"] + counts["lula"] == audit["subtotal_candidatos_publicado"] - 1
    )


def test_current_income_and_sex_recompose_and_adjust_total_vote():
    poll = M.verita()
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert sum(poll["renda"]["frequencias_publicadas"]) == poll["n"] == 15554
    assert max(c["residuo_max_abs"] for c in poll["controles"]["2t"].values()) < 0.07
    result = ENGINE.process_poll(poll, ENGINE.Benchmark(), ENGINE.load_ipca())
    adjusted = result["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
    assert adjusted["flavio"] == pytest.approx(50.431, abs=0.001)
    assert adjusted["lula"] == pytest.approx(47.015, abs=0.001)
    assert sum(adjusted.values()) == pytest.approx(100)


def test_new_wave_enters_projection_once_only_after_release():
    data = ENGINE.build(date(2026, 10, 17))
    projection = PROJECTION.build(data, SIM.preferences)
    selected = [p for p in projection["selected"] if p["instituto"] == "Veritá"]
    assert len(selected) == 1
    assert selected[0]["id"] == "verita_2026-10-16"
    assert selected[0]["income_available"]
    assert selected[0]["pnad"] != selected[0]["published"]
    data["referencia"] = "2026-10-16"
    yesterday = PROJECTION.build(data, SIM.preferences)
    assert not any(p["instituto"] == "Veritá" for p in yesterday["selected"])
