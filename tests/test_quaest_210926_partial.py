"""A fonte parcial não vira perfil final, distribuição completa ou segundo turno."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_partial_quaest_anchors_delta_and_keeps_rounds_separate():
    data = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    spec = importlib.util.spec_from_file_location("engine", ROOT / "scripts/reponderacao-pnad.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    archived = json.loads((ROOT / "analysis/reponderacao/atualizacao_20260924/quaest-fonte-parcial-anterior.json").read_text())
    poll = engine.process_poll(archived, engine.Benchmark(), engine.load_ipca())
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
    assert "2t" not in poll["turnos"]


def test_quaest_source_archive_and_visible_qualifications():
    source = json.loads((ROOT / "docs/assets/quaest_210926_fontes.json").read_text())
    for item in source["arquivos"]:
        path = ROOT / "docs/fontes/quaest_21092026" / item["arquivo"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    html = BeautifulSoup((ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser")
    text = html.find(id="pesquisa-quaest_2026-09-20").get_text(" ", strip=True)
    assert "Perfil final confirmado" in text
    assert "COTA REGISTRADA" not in text
    assert "0,94" in text
    assert "2º turno" in text
    update = html.find(id="atualizacao").get_text(" ", strip=True)
    assert "Quaest" in update and "Substitui a fonte parcial" in update
