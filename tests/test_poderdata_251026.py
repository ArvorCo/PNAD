"""Integração da última PoderData, com denominadores e onda única conferidos."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module("poderdata-251026-renda")


def read(rel):
    return json.loads((ROOT / rel).read_text())


def test_report_and_recomposition(assert_json_close):
    poll = MODULE.poll()
    assert_json_close(
        poll, read("analysis/reponderacao/pesquisas/poderdata_2026-10-24.json")
    )
    assert poll["registro_tse"] == "BR-02828/2026"
    assert poll["campo"] == {"inicio": "2026-10-23", "fim": "2026-10-24"}
    assert poll["divulgacao"] == "2026-10-25" and poll["n"] == 4000
    assert poll["publicado"]["2t"] == {
        "flavio": 49,
        "lula": 47,
        "branco_nulo": 3,
        "indecisos": 1,
    }
    assert poll["publicado_validos"]["2t"] == {"flavio": 51, "lula": 49}
    assert poll["renda"]["perfil_tipo"] == "perfil_ponderado"
    controls = poll["controles"]["2t"]
    assert controls["renda"]["recomposto"]["flavio"] == pytest.approx(48.72)
    assert controls["renda"]["recomposto"]["lula"] == pytest.approx(47.28)
    assert controls["sexo"]["recomposto"]["flavio"] == pytest.approx(48.58)
    assert controls["sexo"]["recomposto"]["lula"] == pytest.approx(47.36)
    raw = (ROOT / poll["fonte"]["arquivo"]).read_bytes()
    assert raw.startswith(b"%PDF")
    assert hashlib.sha256(raw).hexdigest() == poll["fonte"]["sha256"]


def test_current_wave_adjustment_and_presence():
    data = read("docs/assets/reponderacao_pnad.json")
    poll = next(p for p in data["pesquisas"] if p["id"] == "poderdata_2026-10-24")
    scenario = poll["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]
    # Delta por renda ancorado no publicado: não trocar pela soma direta PNAD.
    assert scenario["ajustado"]["flavio"] == pytest.approx(49 + 50.052 - 48.72)
    assert scenario["ajustado"]["lula"] == pytest.approx(47 + 45.948 - 47.28)
    payload = read("docs/assets/reponderacao_simulador.json")
    for rows in [payload["polls"], payload["projection"]["selected"]]:
        selected = [p for p in rows if p["instituto"] == "PoderData"]
        assert len(selected) == 1 and selected[0]["id"] == poll["id"]
    assert payload["projection"]["official"]["flavio"] == 51
    presence = read("analysis/reponderacao/historico_2t/presenca.json")
    assert presence["ondas"][poll["id"]]["taxas"] == {
        "flavio": 0.96,
        "lula": 0.94,
        "indecisos": 0.56,
    }
    # A confirmação do perfil ponderado vale para esta onda, sem rever o passado.
    old = read("analysis/reponderacao/pesquisas/poderdata_2026-10-21.json")
    assert old["renda"]["perfil_tipo"] == "perfil_publicado"
    assert presence["ondas"][old["id"]]["taxas"]["flavio"] == 0.97
    assert 'id="poderdata-2510"' in (ROOT / "docs/reponderacao_pnad.html").read_text()
