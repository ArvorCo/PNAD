"""Íntegra Atlas, leitura independente e separação do campo misto de outubro."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
M = importlib.import_module("pesquisas-091026-renda")


def read(relative):
    return json.loads((ROOT / relative).read_text())


def test_atlas_transcription_reproduces_topline_on_three_independent_margins():
    raw = read("analysis/reponderacao/pesquisas/atlas_2026-10-08.json")
    source = raw["fonte"]
    assert (
        hashlib.sha256((ROOT / source["pdf"]).read_bytes()).hexdigest()
        == source["sha256"]
    )
    assert raw == M.atlas(M.COMMON.archive("atlas_102026_09"))
    assert raw["renda"]["amostra_pct"] == [19.4, 12.2, 26.3, 26.1, 16.1]
    assert raw["n"] == 5026 and raw["divulgacao"] == "2026-10-09"
    assert raw["registro_tse"] == "BR-03663/2026"
    for margin in raw["controles"]["2t"].values():
        assert margin["residuo_max_abs"] < 0.1
    for candidate in ["flavio", "lula"]:
        pub = raw["publicado"]["2t"]
        valid = 100 * pub[candidate] / (pub["flavio"] + pub["lula"])
        assert valid == pytest.approx(
            raw["publicado_validos"]["2t"][candidate], abs=0.05
        )
    assert "indecisos" not in raw["cruzamentos"]["2t"]["opcoes"]


def test_atlas_mixed_field_has_sensitivity_but_cannot_enter_post_first_round_central():
    data = read("docs/assets/reponderacao_pnad.json")
    poll = next(p for p in data["pesquisas"] if p["id"] == "atlas_2026-10-08")
    assert set(poll["turnos"]) == {"2t"}
    result = poll["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]
    assert set(result["ajustado"]) == {"flavio", "lula", "branco_nulo"}
    sim = read("docs/assets/reponderacao_simulador.json")
    assert all(p["id"] != poll["id"] for p in sim["polls"])
    excluded = next(p for p in sim["excluded"] if p["id"] == poll["id"])
    assert "atravessa o 1º turno" in excluded["reason"]
    assert any(p["id"] == "vox_brasil_2026-10-07" for p in sim["excluded"])
    previous = read("docs/assets/reponderacao_cenarios/43b90fe501f43fcd.json")
    assert sim["central"]["flavio"] == pytest.approx(previous["central"]["flavio"])


def test_new_wave_is_linked_and_journal_records_one_incorporation():
    page = BeautifulSoup(
        (ROOT / "docs/reponderacao_pnad.html").read_text(), "html.parser"
    )
    assert page.select_one("#pesquisa-atlas_2026-10-08")
    tips = json.loads(page.select_one("script.tips").string)
    assert "Branco/nulo/não sei (agregado) 3,2" in tips["atlas_2026-10-08|2t"]
    coverage = page.select_one("#cobertura-atlas_2026-10-08").get_text()
    assert "campo atravessa o 1º turno; fora da central" in coverage
    diary = read("analysis/reponderacao/log.json")
    rows = [row for row in diary["waves"] if row["id"] == "atlas_2026-10-08"]
    assert len(rows) == 1 and rows[0]["added"] == "2026-10-09"
    audit = read("docs/assets/reponderacao_20261009.json")
    assert audit["vox"]["registro"]["alvos_renda_pct"][0] == 83.89
    assert (
        "Atlas" in next(s for s in audit["varredura"] if s.get("resumo"))["conclusao"]
    )
