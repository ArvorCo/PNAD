"""Divulgação Futura sem transportar perfil ou duplicar a casa."""

import gzip
import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module("futura-241026-renda")


def test_sources_and_transcription(assert_json_close):
    p = MODULE.poll()
    saved = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/futura_2026-10-24.json").read_text()
    )
    assert_json_close(p, saved)
    assert p["campo"] == {"inicio": "2026-10-23", "fim": "2026-10-24"}
    assert sum(p["publicado"]["2t"].values()) == pytest.approx(100)
    assert p["publicado_validos"]["2t"]["flavio"] == 50.1
    assert p["ignorar"] and "renda" not in p and not p["cruzamentos"]
    for ref in [p["fonte"], *p["fonte"]["complementos"]]:
        raw = (ROOT / ref["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == ref["sha256"]
        if ref["arquivo"].endswith(".pdf"):
            assert raw.startswith(b"%PDF")
            continue
        text = gzip.decompress(raw).decode()
        assert "BR-09726/2026" in text and "50,1%" in text


def test_futura_replaces_previous_wave_only_in_projection():
    data = json.loads((ROOT / "docs/assets/reponderacao_simulador.json").read_text())
    rows = [p for p in data["projection"]["selected"] if p["instituto"] == "Futura"]
    assert len(rows) == 1 and rows[0]["id"] == "futura_2026-10-24"
    assert rows[0]["published"]["flavio"] == pytest.approx(48.2)
    assert not rows[0]["income_available"]
    assert "Futura" not in {p["instituto"] for p in data["polls"]}
    before = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/7b8ef4f4a3b871ce.json").read_text()
    )
    futura_snapshot = json.loads(
        (ROOT / "docs/assets/reponderacao_cenarios/1b2c2ca5884932ac.json").read_text()
    )
    assert futura_snapshot["central"] == before["central"]
    assert data["projection"]["official"]["flavio"] == 51
