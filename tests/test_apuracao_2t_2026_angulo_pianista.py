"""Contrato de ``angulo_pianista.json`` e regras de texto do bloco do pianista."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from apuracao_2t_2026 import angulo_pianista as A
from apuracao_2t_2026 import pagina_texto_angulo_pianista as P
from apuracao_2t_2026.angulo_pianista_log import p_rajada
from apuracao_2t_2026.angulo_pianista_texto import markdown

ROOT = Path(__file__).resolve().parents[1]
JSON = ROOT / "analysis/apuracao_2t_2026/dados/angulo_pianista.json"
MD = ROOT / "analysis/apuracao_2t_2026/dados/angulo_pianista.md"


@pytest.fixture(scope="module")
def d() -> dict:
    if not JSON.exists():
        pytest.skip("angulo_pianista.json ausente")
    return json.loads(JSON.read_text(encoding="utf-8"))


def test_sem_json_bloco_vazio():
    assert P.bloco(None) == ""
    assert P.bloco({}) == ""


def test_p_rajada():
    assert p_rajada(100, 0, 0) is None
    assert p_rajada(100, 100, 100) == 1.0
    curta, longa = p_rajada(300, 30, 3), p_rajada(300, 30, 8)
    assert 0 < longa < curta <= 1


def test_derivar_marca():
    base = {
        "n": 200,
        "n_nbio": 40,
        "nbio_ultima_hora": 30,
        "pct_nbio_na_ultima_hora": 75.0,
        "pct_todos_na_ultima_hora": 20.0,
        "maior_sequencia_nbio": 25,
        "p_sequencia": 1e-9,
        "intervalo_nbio_p50_s": 20.0,
        "intervalo_p50_s": 80.0,
        "cv_intervalo_nbio": 0.5,
        "pares_nbio": 30,
        "hab_nbio_p50_s": 8.0,
        "hab_bio_p50_s": 15.0,
        "reinicios_votacao": 0,
        "contingencia": False,
        "urnas": 1,
    }
    x = A.derivar(base)
    assert x["marca"] and x["marca_forte"]
    assert not A.derivar({**base, "reinicios_votacao": 1})["marca"]
    lento = {**base, "intervalo_nbio_p50_s": 120.0, "hab_nbio_p50_s": 60.0}
    assert not A.derivar(lento)["marca"]
    assert A.derivar({"erro": "sem_original"}) == {}


def test_contrato(d):
    for k in ("rotulo", "regras", "metricas", "celula", "grupos", "comparacoes", "top"):
        assert k in d
    assert d["rotulo"] == A.ROTULO
    assert set(d["grupos"]) == {"celula", "vizinhas", "salto_sem_delta"}
    c = d["celula"]
    assert c["com_log_2t"] <= c["secoes"] and c["com_log_1t"] <= c["com_log_2t"]
    assert d["grupos"]["celula"]["secoes"] == c["com_log_2t"]
    assert d["bootstrap"]["reamostragens"] == 2000
    for m in A.METRICAS:
        bloco = d["comparacoes"][m]
        for k in ("did_vizinhas", "did_salto_sem_delta", "celula_2t_menos_1t"):
            x = bloco[k]
            if x.get("estimativa") is not None and x["ic95"][0] is not None:
                assert x["ic95"][0] <= x["ic95"][1]
    assert len(d["top"]) <= A.TOP
    for t in d["top"]:
        assert (
            t["link"]
            == f"politizese.html#uf={t['uf']}&zona={t['zona']}&secao={t['secao']}"
        )
        assert t["aptos"] > 0
    g = d["grupos"]["celula"]
    assert g["marca_forte_2t"] <= g["marca_2t"] <= g["secoes"]


def test_texto(d):
    html = P.bloco(d)
    md = markdown(d)
    assert html.startswith("<h3>") and "<section" not in html
    for t in (html, md):
        assert "—" not in t
        assert "fraude" not in t.lower()
        assert "não prova irregularidade" in t
    assert 'class="selo selo-verificado"' in html
    assert 'class="selo selo-inferencia"' in html
    assert 'class="selo selo-hipotese"' in html
    assert "politizese.html#uf=" in html
    if MD.exists():
        assert MD.read_text(encoding="utf-8") == md
