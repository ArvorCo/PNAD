"""Contratos do atlas estadual de setembro de 2026 e da super thread.

O material vem de duas fontes que precisam continuar concordando: a transcricao
declarada em `scripts/estaduais-092026-data.py`, feita pagina a pagina sobre os
relatorios em imagem, e a leitura de maquina que `estaduais-092026-extract.py`
guarda em `analysis/estaduais_092026/`. Divergencia entre as duas quebra aqui.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
OCR = ROOT / "analysis" / "estaduais_092026"
DATA_JSON = ASSETS / "estaduais_092026_data.json"

# Totais oficiais do 2o turno de 2022, para provar que a agregacao municipal
# nao perdeu nem inventou voto.
BOLSONARO_2T_BRASIL = 58_206_354
LULA_2T_BRASIL = 60_345_999


def load_module(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def data() -> dict:
    if not DATA_JSON.exists():
        pytest.skip("rode scripts/estaduais-092026-data.py antes")
    return json.loads(DATA_JSON.read_text())


@pytest.fixture(scope="module")
def municipios() -> list[dict]:
    path = ROOT / "data" / "outputs" / "estaduais2026" / "municipios.csv"
    if not path.exists():
        pytest.skip("rode scripts/estaduais-092026-tse.py antes")
    import csv

    with path.open() as handle:
        return list(csv.DictReader(handle))


def test_transcricao_fecha_em_cem(data):
    """Toda tabela de escolha unica transcrita precisa somar 100."""
    for poll in data["pesquisas"]:
        for chave in ("pres", "pres_2t", "aliado", "problema"):
            bloco = poll.get(chave)
            if not bloco:
                continue
            total = sum(v for k, v in bloco.items() if k != "pagina")
            assert 98 <= total <= 102, (poll["uf"], chave, total)


def test_aprovacao_declarada_e_coerente(data):
    for poll in data["pesquisas"]:
        lula = poll.get("lula") or {}
        if not lula.get("aprova"):
            continue
        assert 0 < lula["aprova"] < 100
        assert 0 < lula["desaprova"] < 100
        assert lula["aprova"] + lula["desaprova"] <= 100


def test_vao_e_diferenca_das_duas_medidas(data):
    for vao in data["vaos"]:
        assert vao["vao_1t"] == vao["gov"] - vao["flavio_1t"]
        if "vao_2t" in vao:
            assert vao["vao_2t"] == vao["gov"] - vao["flavio_2t"]


def test_vao_inverte_onde_o_bolsonarismo_e_hegemonico(data):
    """O achado que impede a leitura preguicosa: o sinal muda de lado."""
    por_uf = {v["uf"]: v for v in data["vaos"]}
    assert por_uf["CE"]["vao_1t"] > 25
    assert por_uf["BA"]["vao_1t"] > 20
    assert por_uf["AC"]["vao_1t"] < 0
    assert por_uf["RO"]["vao_1t"] < 0


def test_agregacao_municipal_reproduz_o_resultado_oficial(municipios):
    bolsonaro = sum(int(m["bolsonaro_2t"]) for m in municipios)
    lula = sum(int(m["lula_2t"]) for m in municipios)
    # O arquivo municipal nao inclui voto no exterior nem em transito agrupado
    # fora de municipio, entao a diferenca esperada e pequena e para menos.
    assert 0 <= BOLSONARO_2T_BRASIL - bolsonaro <= 700_000
    assert 0 <= LULA_2T_BRASIL - lula <= 700_000


def test_nao_visitados_sao_dez_e_tres_foram_vencidos(data):
    nv = data["nao_visitados"]
    assert len(nv["ufs"]) == 10
    venceu = [d for d in nv["detalhe"] if d["venceu_2022"]]
    assert {d["uf"] for d in venceu} == {"AC", "AP", "RR"}
    assert nv["bolsonaro_2t"] > 7_000_000


def test_concentracao_do_voto_no_nordeste(data):
    ne = data["concentracao"]["nordeste"]
    assert ne["municipios"] > 1_700
    assert ne["metade_em"] < 100
    assert ne["curva"][-1][1] > 99


def test_matopiba_e_menor_que_manaus(data):
    """O achado que contraria a tese de partida, e que precisa continuar valendo."""
    manaus = next(c for c in data["capitais"] if c["municipio"] == "Manaus")
    assert data["matopiba"]["bolsonaro_2t"] < manaus["bolsonaro_2t"]
    assert data["matopiba"]["municipios"] >= 30


def test_maquina_confere_a_transcricao(data):
    """Onde o OCR fechou em 100, os dois precisam dar o mesmo numero."""
    conferidos = 0
    for poll in data["pesquisas"]:
        caminho = OCR / f"{poll['uf']}_w1.json"
        if not caminho.exists():
            continue
        leitura = json.loads(caminho.read_text())
        tabela = leitura["tables"].get("pres_1t")
        if not tabela or tabela["page"] != poll["pres"]["pagina"]:
            continue
        maquina = {}
        for linha in tabela["rows"]:
            rotulo = linha["label"].lower()
            if "lula" in rotulo:
                maquina["Lula"] = linha["value"]
            elif "flavio" in rotulo or "flávio" in rotulo:
                maquina["Flávio"] = linha["value"]
        for nome, valor in maquina.items():
            assert poll["pres"].get(nome) == valor, (poll["uf"], nome, valor)
            conferidos += 1
    assert conferidos >= 10, "a conferencia de maquina cobriu pouca coisa"


def test_thread_tem_sete_posts_no_tamanho_declarado():
    module = load_module("superthread-092026")
    cards = module.build_cards()
    assert len(cards) == 7
    for card in cards:
        corpo = "\n\n".join(card["copy"])
        assert 1700 <= len(corpo) <= 2300, (card["tag"], len(corpo))
        assert "—" not in corpo, card["tag"]
        assert "brasil.arvor.co" in corpo or card["kind"] == "limite"


@pytest.mark.parametrize(
    "pagina",
    ["estaduais_092026.html", "superthread_092026.html"],
)
def test_pagina_publicada_sem_travessao(pagina):
    caminho = ROOT / "docs" / pagina
    if not caminho.exists():
        pytest.skip(f"{pagina} ainda nao foi gerada")
    texto = caminho.read_text()
    assert "—" not in texto
    assert "estaduais_092026_data.json" in texto or "superthread" in pagina


def test_camada_de_campanha_entrou_nos_tres_dossies():
    for pagina in (
        "quaest_14092026.html",
        "datafolha_14092026.html",
        "nexus_btg_140926.html",
    ):
        caminho = ROOT / "docs" / pagina
        if not caminho.exists():
            pytest.skip(f"{pagina} ainda nao foi gerada")
        texto = caminho.read_text()
        assert 'id="campanha"' in texto, pagina
        assert "camada-campanha" in texto, pagina
        assert "estaduais_092026.html" in texto, pagina
