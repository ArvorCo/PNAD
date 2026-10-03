"""Ondas estaduais de véspera do Datafolha: fontes arquivadas e entrada na previsão."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predicao_2026 import base  # noqa: E402

ARQ = ROOT / "data/originals/estaduais_102026_03"
ONDAS = {
    "SP": ("datafolha_SP_20260930.json", "2026-09-30", "BR-02676/2026", 1610),
    "MG": ("datafolha_MG_20261001.json", "2026-10-01", "BR-03604/2026", 1204),
    "RJ": ("datafolha_RJ_20261001.json", "2026-10-01", "BR-01272/2026", 1204),
    "PE": ("datafolha_PE_20261001.json", "2026-10-01", "BR-00950/2026", 1204),
    "DF": ("datafolha_DF_20260930.json", "2026-09-30", "BR-09530/2026", 910),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def previsao():
    return json.loads(
        (ROOT / "docs/assets/predicao_2026_1T_presidente.json").read_text()
    )


@pytest.mark.parametrize("uf", sorted(ONDAS))
def test_fontes_arquivadas_conferem_hash(uf):
    fonte = json.loads((ARQ / f"datafolha_{uf}/fonte.json").read_text())
    itens = [fonte["painel"], fonte["materia_datafolha"], *fonte["api"].values()]
    assert len(itens) == 4
    for item in itens:
        path = ROOT / item["arquivo"]
        assert path.stat().st_size == item["bytes"]
        assert sha256(path) == item["sha256"]
    assert fonte["relatorio_pdf"] is None


def test_materia_resumo_arquivada_confere_hash():
    item = json.loads((ARQ / "comum/fonte.json").read_text())["materia_folha_resumo"]
    path = ROOT / item["arquivo"]
    assert sha256(path) == item["sha256"]
    assert path.stat().st_size == item["bytes"]


@pytest.mark.parametrize("uf", sorted(ONDAS))
def test_transcricao_aponta_para_a_resposta_arquivada(uf):
    nome, fim, registro, n = ONDAS[uf]
    doc = json.loads((ROOT / "analysis/predicao_2026/estaduais" / nome).read_text())
    assert doc["sha256"] == sha256(ROOT / doc["arquivo"])
    assert doc["pres_2t"]["sha256"] == sha256(ROOT / doc["pres_2t"]["arquivo"])
    assert base.field_dates(doc["campo"])["fim"] == fim
    assert (doc["registro_tse"], doc["n"]) == (registro, n)
    for valores in (doc["pres_1t"]["valores"], doc["pres_2t"]["cenarios"][0]):
        assert abs(sum(valores.values()) - 100) <= 3
        assert all(isinstance(v, int) for v in valores.values())
    assert "Avalanche" not in doc["pres_1t"]["valores"]
    assert "comparecimento_compacto" not in doc


@pytest.mark.parametrize("uf", sorted(ONDAS))
def test_onda_de_vespera_entra_na_previsao(previsao, uf):
    nome, fim, registro, n = ONDAS[uf]
    estado = next(s for s in previsao["estados"] if s["uf"] == uf)
    linhas = [p for p in estado["pesquisas"] if p["instituto"] == "Datafolha"]
    assert len(linhas) == 1
    linha = linhas[0]
    assert linha["arquivo"].endswith(nome)
    assert linha["campo"]["fim"] == fim
    assert linha["divulgacao"] == "2026-10-02"
    assert (linha["registro"], linha["n"]) == (registro, n)
    assert linha["reserva_pagina_2t"].endswith("SEGTURNO-PRE-001&instituto=Datafolha")
