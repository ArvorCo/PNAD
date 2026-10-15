"""Arquivo fornecido pelo usuário: números visíveis, ausências e hipótese de pesos."""

import gzip
import hashlib
import json

import pytest
from bs4 import BeautifulSoup
from quaest_141026.income import build as income_build
from quaest_141026.panel import ARCHIVE, EXTRACT, ROOT, evidence, parse


def test_local_svg_extraction_ignores_transient_donut_and_preserves_missing_labels():
    raw = gzip.decompress(ARCHIVE.read_bytes())
    saved = json.loads(EXTRACT.read_text())
    assert (
        hashlib.sha256(raw).hexdigest()
        == saved["arquivo_original"]["sha256_descomprimido"]
    )
    result = parse(raw)
    assert len(result["graficos"]) == 27
    assert sum(g["completo"] for g in result["graficos"]) == 26
    total = next(g for g in result["graficos"] if g["dimensao"] == "total")
    assert total["votos"] == {
        "flavio": 46,
        "lula": 44,
        "indecisos": 1,
        "branco_nulo": 9,
    }
    missing = next(g for g in result["graficos"] if g["rotulo"] == "Lulista")
    assert not missing["completo"]
    assert set(missing["votos"].values()) == {None}
    income = [g for g in result["graficos"] if g["dimensao"] == "renda"]
    assert [list(g["votos"].values()) for g in income] == [
        [36, 53, 1, 10],
        [49, 41, 1, 9],
        [53, 39, 0, 8],
    ]
    with pytest.raises(ValueError, match="ficha"):
        parse(raw.replace(b"BR-08729/2026", b"BR-00000/2026"))


def test_conditional_income_uses_current_crosses_preserves_topline_and_closes_changes():
    folder = ROOT / "analysis/reponderacao/pesquisas"
    poll = json.loads((folder / "quaest_2026-10-13.json").read_text())
    before = json.loads((folder / "quaest_2026-10-03.json").read_text())
    data = income_build(poll, before)
    assert poll["renda"]["perfil_tipo"] == "perfil_publicado"
    assert data["recomposto"]["flavio"] == 46.05
    assert data["recomposto"]["lula"] == 44.18
    assert data["reponderacao_pontual"]["flavio"] == 45.398
    assert data["reponderacao_pontual"]["lula"] == 44.531
    assert data["gap_ajustado_pp"] == pytest.approx(0.867)
    assert [r["mudanca_gap_pp"] for r in data["evolucao_0310"]] == [4, -2, -3]
    assert data["mudanca_gap_recomposto_pp"] == pytest.approx(-0.41)
    assert data["mudanca_residuo_pp"] == pytest.approx(0.41)
    assert data["mudanca_gap_recomposto_pp"] + data[
        "mudanca_residuo_pp"
    ] == pytest.approx(data["mudanca_gap_publicado_pp"])
    for control in data["controles"].values():
        residual = control["residuo_recomposto_menos_publicado"]
        assert max(abs(v) for v in residual.values()) <= 0.47


def test_public_evidence_keeps_original_svg_numbers_without_active_external_content():
    raw = gzip.decompress(ARCHIVE.read_bytes())
    html = evidence(raw)
    page = BeautifulSoup(html, "html.parser")
    assert len(page.select("svg.chart-bars")) == 5
    assert not page.select("script, iframe, img, image, foreignObject")
    assert not page.select("[src], [href], [onload]")
    assert [n.get_text() for n in page.select("text.label-flavio-bolsonaro")] == [
        "42",
        "51",
        "36",
        "49",
        "53",
    ]
