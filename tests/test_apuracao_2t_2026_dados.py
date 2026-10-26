"""Esquema e identidades aritméticas dos dados do dossiê da apuração do 2º turno.

Os JSONs saem de `scripts/apuracao-2t-2026-dados.py`, que precisa do banco local
pesado; sem eles os testes são pulados.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest
from apuracao_2t_2026.base import ROTULO, d2, p2
from apuracao_2t_2026.resumo import n

DADOS = Path(__file__).resolve().parents[1] / "analysis/apuracao_2t_2026/dados"
ARQUIVOS = (
    "presidente.json",
    "linha_do_tempo.json",
    "cedo_tarde.json",
    "comparacao_1t.json",
    "comparacao_2022.json",
    "abstencao.json",
    "exterior.json",
    "governadores.json",
    "projecao_noite.json",
    "paralela.json",
)
TRAVESSAO = chr(0x2014)

pytestmark = pytest.mark.skipif(
    not all((DADOS / a).exists() for a in ARQUIVOS),
    reason="dados do 2º turno não gerados (exigem o banco local da apuração)",
)


def ler(nome: str) -> dict[str, Any]:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def linhas(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(doc["colunas"], r, strict=True)) for r in doc["linhas"]]


def identidade(r: dict[str, Any]) -> None:
    assert r["aptos_apurados"] == (
        r["validos"] + r["brancos"] + r["nulos"] + r["abstencao"]
    ), r.get("uf", r.get("cd_tse"))


def test_formatadores() -> None:
    assert p2(1, 3) == 33.33
    assert p2(1, 0) is None
    assert d2(51.78, 48.22) == 3.56
    assert n(1234567) == "1.234.567"
    assert n(48.2) == "48,20"


@pytest.mark.parametrize("nome", ARQUIVOS)
def test_meta_rotulo_e_sem_travessao(nome: str) -> None:
    texto = (DADOS / nome).read_text(encoding="utf-8")
    assert TRAVESSAO not in texto
    doc = json.loads(texto)
    assert doc["meta"]["rotulo"] == ROTULO
    assert doc["meta"]["arquivo"] == nome
    assert doc["meta"]["versao_nacional_gerada_em"].endswith("Z")


def test_resumo_sem_travessao() -> None:
    texto = (DADOS / "resumo.md").read_text(encoding="utf-8")
    assert TRAVESSAO not in texto
    assert ROTULO in texto


def test_presidente_identidades() -> None:
    doc = ler("presidente.json")
    nac = doc["nacional"]
    identidade(nac)
    assert nac["flavio"] + nac["lula"] == nac["validos"]
    assert abs(nac["pct_flavio"] + nac["pct_lula"] - 100) <= 0.011
    for u in doc["ufs"]:
        identidade(u)
        assert u["flavio"] + u["lula"] == u["validos"]
    muns = linhas(doc["municipios"])
    assert len(muns) > 5500
    for m in muns:
        identidade(m)
        if m["completo"]:
            assert m["aptos"] == m["aptos_apurados"]
            assert m["fechou_min"] is not None
    for r in doc["regioes"]:
        ufs = [u for u in doc["ufs"] if u["uf"] in r["ufs"]]
        assert r["flavio"] == sum(u["flavio"] for u in ufs)
        assert r["abstencao"] == sum(u["abstencao"] for u in ufs)
    assert sum(r["n"] for r in doc["regioes"]) == len(doc["ufs"]) == 28


def test_percentuais_com_duas_casas() -> None:
    doc = ler("presidente.json")
    for u in doc["ufs"]:
        for k in (
            "pct_flavio",
            "pct_lula",
            "pct_abstencao",
            "pct_brancos",
            "pct_nulos",
        ):
            assert round(u[k], 2) == u[k]


def test_linha_do_tempo_monotona() -> None:
    doc = ler("linha_do_tempo.json")
    serie = linhas(doc["nacional"]["serie"])
    assert all(a["min"] <= b["min"] for a, b in pairwise(serie))
    assert all(a["st"] <= b["st"] for a, b in pairwise(serie))
    assert sum(r["lote_st"] for r in serie) == serie[-1]["st"]
    assert sum(r["lote_flavio"] for r in serie) == serie[-1]["flavio"]
    sil = doc["pausas"]["silencio_geral"]
    assert sil["versoes_geradas_dentro"] == 0
    assert sil["minutos"] > 100
    assert len(doc["ufs"]) == 28
    assert doc["regressoes"]["contagem_regressiva"] == []


def test_cedo_tarde_decis() -> None:
    doc = ler("cedo_tarde.json")
    decis = doc["decis_2t"]
    assert len(decis) == 10
    assert sum(d["n"] for d in decis) == doc["n_municipios"]
    for d in decis:
        assert d["swing_h2h_flavio_pp"] == d2(d["h2h_flavio"], d["t1_h2h_flavio"])
    matriz = doc["transicao_decil_1t_para_2t"]["matriz"]
    assert len(matriz) == 10
    assert all(len(linha) == 10 for linha in matriz)
    assert len(doc["ultimos_50"]) == 50


def test_comparacao_1t_contas() -> None:
    doc = ler("comparacao_1t.json")
    pares = linhas(doc["municipios"])
    for p in pares:
        assert p["delta_votos_flavio"] == p["t2_flavio"] - p["t1_flavio"]
        assert p["delta_votos_lula"] == p["t2_lula"] - p["t1_lula"]
        assert p["t1_terceiros"] == p["t1_validos"] - p["t1_flavio"] - p["t1_lula"]
    b = doc["brasil"]
    assert b["delta_votos_flavio"] == b["t2_flavio"] - b["t1_flavio"]
    g, q = doc["flavio_ganhou_votos"]["n"], doc["flavio_perdeu_votos"]["n"]
    assert g + q <= doc["n_municipios_completos"]
    cols = doc["abstencao_caiu_5pp"]["lista"]["colunas"]
    for r in doc["abstencao_caiu_5pp"]["lista"]["linhas"]:
        x = dict(zip(cols, r, strict=True))
        assert x["delta_abstencao_pp"] <= -5
        assert x["aptos"] >= 5000


def test_comparacao_2022() -> None:
    doc = ler("comparacao_2022.json")
    b = doc["brasil"]
    assert b["swing_lula_pp"] == d2(b["pct_lula"], b["r22_pct_lula"])
    assert b["r22_lula"] + b["r22_bolsonaro"] == b["r22_validos"]
    vr = doc["viraram"]
    assert vr["n"] == len(vr["lista"]["linhas"])


def test_abstencao_histograma_fecha() -> None:
    doc = ler("abstencao.json")
    total = doc["brasil"]["n_municipios"]
    assert sum(c["n"] for c in doc["histograma_pa_2t"]["caixas"]) == total
    assert (
        sum(c["aptos"] for c in doc["histograma_pa_2t"]["caixas"])
        == doc["brasil"]["aptos"]
    )
    rk = [r["pa_2t"] for r in doc["ranking_ufs_menor_abstencao"]]
    assert rk == sorted(rk)


def test_exterior_e_governadores() -> None:
    ext = ler("exterior.json")
    assert ext["total"]["cidades"] == len(ext["cidades"])
    assert sum(p["cidades"] for p in ext["paises"]) == len(ext["cidades"])
    gov = ler("governadores.json")
    assert [u["uf"] for u in gov["ufs"]] == ["AC", "AM", "DF", "ES", "RN", "TO"]
    for u in gov["ufs"]:
        assert sum(c["votos"] for c in u["candidatos"]) == u["validos"]
        assert len(u["candidatos"]) == 2


def test_paralela_e_projecao() -> None:
    par = ler("paralela.json")
    assert par["rotulo"] == "soma dos BUs recebidos, não projeção"
    assert len(par["bus"]) == par["recebidos"]["bus"]
    assert sum(par["conferencia"].values()) == par["recebidos"]["bus"]
    pj = ler("projecao_noite.json")
    assert "não é resultado" in pj["rotulo"]
    for p in pj["pontos"]:
        if p["faixa90"]:
            assert p["faixa90"][0] <= p["faixa90"][1]
