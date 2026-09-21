"""Proveniência, universos e limites da atualização de 21/09/2026."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUTPUT = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
AUDIT = json.loads((ROOT / "docs/assets/reponderacao_20260921.json").read_text())


def test_new_waves_recompose_by_two_independent_partitions():
    for ident in ["palver_2026-09-18", "nexus_2026-09-20"]:
        poll = next(p for p in OUTPUT["pesquisas"] if p["id"] == ident)
        for turn in ["1t", "2t"]:
            control = AUDIT["controles"][ident][turn]
            assert control["residuo_max"] < 0.8
            assert control["residuo_renda"] < 0.8
            assert sum(control["pesos"]) == pytest.approx(100)
            assert poll["turnos"][turn]["residuo_max"] == control["residuo_renda"]


def test_revised_wave_never_reuses_old_income_crossbreaks():
    assert "palver_2026-09-07" not in {p["id"] for p in OUTPUT["pesquisas"]}
    revised = next(
        p for p in OUTPUT["nao_reponderaveis"] if p["id"] == "palver_2026-09-07_v2"
    )
    assert revised["publicado"]["2t"] == {
        "lula": 44,
        "flavio": 47,
        "branco_nulo": 8,
        "indecisos": 1,
    }
    assert "turnos" not in revised
    assert revised["campo"]["fim"] == "2026-09-07"
    assert revised["divulgacao"] == "2026-09-21"


def test_targets_are_not_mislabelled_as_observed_weighted_sample():
    poll = next(p for p in OUTPUT["pesquisas"] if p["id"] == "palver_2026-09-18")
    assert poll["renda"]["perfil_tipo"] == "alvo_de_calibracao"
    assert poll["renda"]["amostra_pct"] == pytest.approx(
        [42.124, 39.564, 18.312], abs=0.001
    )
    assert AUDIT["palver"]["pnad"]["ano"] == 2024
    assert AUDIT["palver"]["voto_2022"]["usa"] is True
    assert AUDIT["palver"]["microdados_publicos"] is False


def test_state_surveys_never_enter_national_averages():
    registries = {p["registro_tse"] for p in OUTPUT["pesquisas"]}
    for state in AUDIT["estaduais"]:
        assert state["registro"] not in registries
    pr = next(s for s in AUDIT["estaduais"] if s["uf"] == "PR")
    assert pr["divulgacao_pdf"] == "2026-09-16"


def test_skip_home_preserves_home_and_its_chart(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "reponderacao_build_test", ROOT / "scripts/reponderacao-build.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    for name in [
        "PAGE",
        "SHEET",
        "TABLE_CSV",
        "TIP_SCRIPT",
        "TIP_SHEET",
        "INDEX",
        "HOME_SVG",
    ]:
        monkeypatch.setattr(builder, name, tmp_path / getattr(builder, name).name)
    monkeypatch.setattr(builder, "ASSETS", tmp_path)
    builder.INDEX.write_bytes(b"home deliberately frozen")
    builder.HOME_SVG.write_bytes(b"chart deliberately frozen")
    builder.build(update_home=False)
    assert builder.INDEX.read_bytes() == b"home deliberately frozen"
    assert builder.HOME_SVG.read_bytes() == b"chart deliberately frozen"
    html = builder.PAGE.read_text()
    assert 'id="palver-pesos"' in html
    assert "palver_2026-09-18" in html
    assert "META DE CALIBRAÇÃO" in html
