"""A fonte parcial não vira perfil final, distribuição completa ou segundo turno."""

import hashlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_partial_quaest_anchors_delta_and_keeps_rounds_separate():
    data = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    poll = next(p for p in data["pesquisas"] if p["id"] == "quaest_2026-09-20")
    assert set(poll["turnos"]) == {"1t"}
    assert poll["renda"]["perfil_tipo"] == "cota_registrada"
    assert poll["renda"]["amostra_pct"] == [31, 42, 27]
    turn = poll["turnos"]["1t"]
    assert turn["recomposto"] == pytest.approx(
        {"lula": 37.3, "flavio": 32.06, "cury": 5.92, "caiado": 4}
    )
    assert turn["residuo_max"] == pytest.approx(0.94)
    weights = poll["renda"]["pnad_pct"]["pessoas16_efetivo"]
    adjusted = turn["cenarios"]["pessoas16_efetivo"]["ajustado"]
    for candidate, votes, published, reproduced in [
        ("lula", [49, 34, 29], 37, 37.3),
        ("flavio", [23, 33, 41], 33, 32.06),
    ]:
        expected = published + sum(w * v for w, v in zip(weights, votes)) / 100 - reproduced
        assert adjusted[candidate] == pytest.approx(expected, abs=0.002)
    # Não fechar a tabela parcial em 100 nem inventar os candidatos ocultos.
    assert set(adjusted) == {"lula", "flavio", "cury", "caiado"}
    assert sum(adjusted.values()) < 85
    latest_runoff = max(
        p["campo"]["fim"] for p in data["pesquisas"]
        if p["instituto"] == "Quaest" and "2t" in p["turnos"]
    )
    assert latest_runoff == "2026-09-13"


def test_quaest_source_archive_and_visible_qualifications():
    source = json.loads((ROOT / "docs/assets/quaest_210926_fontes.json").read_text())
    for item in source["arquivos"]:
        path = ROOT / "docs/fontes/quaest_21092026" / item["arquivo"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    html = BeautifulSoup((ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser")
    text = html.find(id="pesquisa-quaest_2026-09-20").get_text(" ", strip=True)
    assert "Fonte parcial" in text
    assert "COTA REGISTRADA" in text
    assert "0,94" in text
    assert "não foram imputadas" in text
    update = html.find(id="atualizacao").get_text(" ", strip=True)
    assert "Quaest" in update and "perfil final" in update
