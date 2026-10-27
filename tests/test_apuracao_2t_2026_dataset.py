"""Dataset aberto por seção do 2º turno: manifesto, CSV, dicionário e links no dossiê.

Roda no CI sem os bancos: só precisa do CSV versionado, do manifesto e do dicionário.
"""

import gzip
import hashlib
import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import dataset as DS
from apuracao_2t_2026 import pagina_cap_fontes as CF
from apuracao_2t_2026 import pagina_cap_secoes as CS

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "apuracao_2T_2026.html"
TRAVESSAO = "—"


@pytest.fixture(scope="module")
def manifesto():
    assert DS.MANIFESTO.exists(), "manifesto.json do dataset ausente"
    return DS.ler_manifesto()


@pytest.fixture(scope="module")
def csv_info():
    sha = hashlib.sha256(DS.CSV.read_bytes()).hexdigest()
    with gzip.open(DS.CSV, "rt", encoding="utf-8") as f:
        cabecalho = f.readline().rstrip("\n").split(",")
        n = sum(1 for _ in f)
    return sha, cabecalho, n


def test_colunas_iguais_no_manifesto_csv_e_dicionario(manifesto, csv_info):
    _, cabecalho, _ = csv_info
    assert manifesto["colunas"] == DS.NOMES
    assert cabecalho == DS.NOMES
    texto = DS.DICIONARIO.read_text(encoding="utf-8")
    assert DS.colunas_do_dicionario(texto) == DS.NOMES


def test_linhas_e_hash_batem_com_o_arquivo(manifesto, csv_info):
    sha, _, n = csv_info
    assert manifesto["n_linhas"] == n
    assert manifesto["sha256"] == sha
    assert manifesto["bytes"] == DS.CSV.stat().st_size
    assert (
        manifesto["arquivo"]
        == "docs/assets/apuracao_2t/dataset/secoes_1t_2t_2026.csv.gz"
    )


def test_dicionario_sem_travessao_e_com_rotulo():
    texto = DS.DICIONARIO.read_text(encoding="utf-8")
    assert TRAVESSAO not in texto
    assert "fraude" not in texto.lower()
    assert "não prova irregularidade" in texto
    assert "atipicidade estatística não é irregularidade" in texto
    assert DS.LOGS_2T_CSV in texto
    assert "depósito separado" in texto


def test_partes_por_uf_declaradas_quando_existem(manifesto):
    partes = manifesto.get("partes_por_uf")
    if DS.CSV.stat().st_size > DS.LIMITE_PARTES:
        assert partes and len(partes) == len(DS.UFS)
    if partes:
        for p in partes:
            arq = ROOT / p["arquivo"]
            assert (
                arq.exists()
                and p["sha256"] == hashlib.sha256(arq.read_bytes()).hexdigest()
            )
        assert "uf/<UF>.csv.gz" in DS.DICIONARIO.read_text(encoding="utf-8")


def test_gzip_sem_nome_e_sem_data():
    cab = DS.CSV.read_bytes()[:10]
    assert cab[:2] == b"\x1f\x8b"
    assert cab[3] & 0x08 == 0, "cabeçalho gzip com nome de arquivo"
    assert cab[4:8] == b"\x00\x00\x00\x00", "mtime do gzip não é zero"


def test_blocos_da_pagina_com_manifesto_sintetico():
    m = {
        "arquivo": "docs/assets/apuracao_2t/dataset/secoes_1t_2t_2026.csv.gz",
        "bytes": 41_500_000,
        "sha256": "a" * 64,
        "n_linhas": 499_248,
        "partes_por_uf": None,
    }
    bloco = CS.bloco_dataset(m)
    assert 'href="assets/apuracao_2t/dataset/secoes_1t_2t_2026.csv.gz"' in bloco
    assert 'href="assets/apuracao_2t/dataset/DICIONARIO.md"' in bloco
    assert "41,5 MB" in bloco and "499.248 linhas" in bloco
    assert "Baixe os dados por seção (CSV, dicionário e hash)" in bloco
    item = CF.item_dataset(m)
    assert "Dataset aberto por seção" in item and "a" * 64 in item
    assert "deposito_bruto.json" in item and "Internet Archive" in item
    for h in (bloco, item):
        assert TRAVESSAO not in h and "fraude" not in h.lower()


def test_html_publicado_tem_os_links(manifesto):
    if not HTML.exists():
        pytest.skip("HTML do dossiê não está neste checkout")
    html = HTML.read_text(encoding="utf-8")
    assert "Baixe os dados por seção (CSV, dicionário e hash)" in html
    assert "assets/apuracao_2t/dataset/secoes_1t_2t_2026.csv.gz" in html
    assert "assets/apuracao_2t/dataset/DICIONARIO.md" in html
    assert re.search(
        r"Dataset aberto por seção.*?SHA-256 " + manifesto["sha256"], html, re.DOTALL
    )
