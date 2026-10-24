"""Conservação dos universos e ausência de imputação no cenário climático."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from clima_1t import previsao, territorio
from clima_1t.pagina.util import PREVISAO_JSON, Dados

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fontes():
    p = {
        "ufs": [
            {"uf": "SP", "eleitores": 40000, "comparecimento": 32000},
            {"uf": "ZZ", "eleitores": 10000, "comparecimento": 100},
        ],
        "municipios": {
            "colunas": [
                "uf",
                "cd_tse",
                "ibge",
                "nome",
                "eleitores",
                "comparecimento",
                "completo",
            ],
            "linhas": [
                ["SP", "1", "100", "A", 20000, 14000, True],
                ["SP", "2", "200", "B", 20000, 18000, True],
                ["ZZ", "3", "300", "Exterior", 10000, 100, True],
            ],
        },
    }
    i = {
        "celulas": {
            "a": [["SP", "00001", "A", 2, 10000]],
            "b": [["SP", "00001", "A", 2, 10000]],
            "c": [["SP", "00002", "B", 2, 18000]],
        }
    }
    f = {
        "gerado_em": "2026-10-24T20:00:00+00:00",
        "alvo": "2026-10-25",
        "celulas": {
            "a": {"risco": "alto", "chuva_mm": 30},
            "b": {"risco": "baixo", "chuva_mm": 0},
        },
    }
    return p, i, f


def test_persistencia_nao_converte_exposicao_em_abstencao(fontes):
    d = territorio.calcular(*fontes)
    a, b = d["municipios"]
    assert d["brasil"]["aptos"] == 40000
    assert d["brasil"]["abstencao_pct"] == pytest.approx(20)
    assert len(d["municipios"]) == 2
    assert a["abstencao_1t_pct"] == pytest.approx(30)
    assert a["cenario_persistencia_2t_pct"] == a["abstencao_1t_pct"]
    assert a["chuva_media_mm"] == 15
    assert a["risco_alto_pct"] == 50
    assert a["atencao_conjunta"]
    assert b["chuva_media_mm"] is None
    assert b["cobertura_previsao_pct"] == 0
    assert not b["atencao_conjunta"]
    p, i, f = deepcopy(fontes)
    f["celulas"]["b"] = {"risco": "alto", "chuva_mm": 70}
    novo = territorio.calcular(p, i, f)["municipios"][0]
    assert novo["risco_alto_pct"] == 100
    assert novo["cenario_persistencia_2t_pct"] == a["cenario_persistencia_2t_pct"]


def test_celula_sem_previsao_nao_passa_como_risco_baixo(fontes):
    p, i, f = fontes
    del f["celulas"]["b"]
    a = territorio.calcular(p, i, f)["municipios"][0]
    assert a["cobertura_previsao_pct"] == 50
    assert a["risco_alto_pct"] == 50
    assert not a["atencao_conjunta"]


def test_pagina_e_payload_usam_mesma_rodada_sem_regravar_analise():
    path = ROOT / "analysis/clima_1t_2026/clima.json"
    antes = path.read_bytes()
    d = Dados()
    assert path.read_bytes() == antes
    assert d.d["previsao_25_10"]["gerado_em"] == d.previsao["gerado_em"]
    assert d.d["previsao_25_10"]["pais"] == d.previsao["resumo"]["pais"]
    f = next(f for f in d.d["fontes"] if f["chave"] == "previsao")
    assert f["sha256"] == hashlib.sha256(PREVISAO_JSON.read_bytes()).hexdigest()
    assert d.territorio["brasil"]["abstencao_pct"] == pytest.approx(20.8421175256)


def test_resposta_fora_do_alvo_preserva_previsao_anterior(tmp_path, monkeypatch):
    saida = tmp_path / "previsao.json"
    anterior = {"coleta": {"completa": True}, "gerado_em": "ontem"}
    saida.write_text(json.dumps(anterior))
    monkeypatch.setattr(previsao, "SAIDA", saida)
    monkeypatch.setattr(previsao, "ler_indice", lambda: {"celulas": {"0.0,0.0": []}})

    def baixar(_cliente, _url, _params, _centros, _lote, guardar):
        guardar("0.0,0.0", {"daily": {"time": ["2026-10-26"]}}, "", 0)
        return {"parada": None}

    monkeypatch.setattr(previsao.coleta, "baixar_lotes", baixar)
    doc, escreveu = previsao.gerar()
    assert not doc["coleta"]["completa"]
    assert not escreveu
    assert json.loads(saida.read_text()) == anterior


def test_home_destaca_clima_e_quadro_antes_dos_dossies():
    html = (ROOT / "docs/index.html").read_text()
    assert (
        html.index('id="clima-1t"')
        < html.index('id="agregador"')
        < html.index('id="dossies-segundo-turno"')
    )
    assert html.count('id="agregador"') == 1
    assert html.count("<!--FIG:reponderacao_home-->") == 1
