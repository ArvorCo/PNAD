"""Veritá final: candidatos, denominadores e entrada única nas duas centrais."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module("verita-241026-renda")


def test_transcription_and_conditional_income(assert_json_close):
    poll = MODULE.poll()
    saved = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/verita_2026-10-23.json").read_text()
    )
    assert_json_close(poll, saved)
    assert poll["publicado"]["2t"] == {
        "flavio": 49.44,
        "lula": 46.46,
        "branco_nulo": 1.43,
        "indecisos": 2.67,
    }
    assert poll["publicado_validos"]["2t"] == {"flavio": 51.56, "lula": 48.44}
    assert poll["registro_tse"] == "BR-03181/2026"
    assert poll["campo"] == {"inicio": "2026-10-19", "fim": "2026-10-23"}
    raw = (ROOT / poll["fonte"]["arquivo"]).read_bytes()
    assert raw.startswith(b"%PDF")
    assert hashlib.sha256(raw).hexdigest() == poll["fonte"]["sha256"]
    assert sum(poll["perfil_economico_publicado"]["frequencias"]) == 15814
    assert sum(poll["perfil_economico_publicado"]["percentuais"]) == pytest.approx(
        101.7
    )
    assert poll["renda"]["perfil_tipo"] == "hipotese_perfil_condicional"
    assert poll["renda"]["parcela_ajustada_pct"] == pytest.approx(100 * 15294 / 15554)
    # Conferência independente do placar por sexo e pelas três rendas.
    assert poll["controles"]["2t"]["renda"]["recomposto"]["flavio"] == pytest.approx(
        49.46
    )
    assert poll["controles"]["2t"]["sexo"]["residuo_max_abs"] < 0.05


def test_income_adjustment_and_latest_wave_in_both_centers():
    current = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    poll = next(p for p in current["pesquisas"] if p["id"] == "verita_2026-10-23")
    turn = poll["turnos"]["2t"]
    fraction = 15294 / 15554
    for scenario in turn["cenarios"].values():
        for candidate in ["flavio", "lula"]:
            # O delta integral fica limitado à parcela declarada; não se ajustam os sem renda.
            expected = turn["publicado"][candidate] + fraction * (
                scenario["contrafactual"][candidate] - turn["recomposto"][candidate]
            )
            assert scenario["ajustado"][candidate] == pytest.approx(expected, abs=0.002)
    payload = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())
    for rows in [payload["polls"], payload["projection"]["selected"]]:
        verita = [p for p in rows if p["instituto"] == "Veritá"]
        assert len(verita) == 1 and verita[0]["id"] == "verita_2026-10-23"
    assert payload["projection"]["official"]["flavio"] == 51
    html = (ROOT / "docs/reponderacao_pnad.html").read_text()
    assert 'id="verita-2410"' in html
    assert "hipótese de perfil condicional" in html
