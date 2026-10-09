"""Vídeo dos fiscais (video/fiscais): dados do Remotion batem com o capítulo 13 e o roteiro cita
as seções reais, sem travessão."""

from __future__ import annotations

import importlib
import json
import re
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "fiscais"
DADOS = VIDEO / "src" / "dados" / "dados.json"
VOZ = VIDEO / "src" / "dados" / "voz.json"
ROTEIRO = VIDEO / "roteiro" / "roteiro.md"
FISCAIS = ROOT / "analysis" / "apuracao_2026" / "dados" / "fiscais.json"

pytestmark = pytest.mark.skipif(not DADOS.exists(), reason="dados do vídeo não gerados")


@pytest.fixture(scope="module")
def dados() -> dict:
    return json.loads(DADOS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roteiro() -> str:
    return ROTEIRO.read_text(encoding="utf-8")


def _sem_acento(texto: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()


def test_doze_criterios_com_exemplo_real(dados: dict) -> None:
    assert [c["id"] for c in dados["criterios"]] == list("abcdefghijkl")
    for c in dados["criterios"]:
        e = c["exemplo"]
        assert c["id"] in e["criterios"], c["id"]
        assert e["votantes"] > 0 and e["aptos"] >= e["votantes"]
        assert e["detalhe"] is not None, c["id"]
        assert 0 <= e["xy"][0] <= 1000 and 0 <= e["xy"][1] <= 1000


def test_resumo_bate_com_o_capitulo_13(dados: dict) -> None:
    if not FISCAIS.exists():
        pytest.skip("fiscais.json pesado ausente")
    fonte = json.loads(FISCAIS.read_text(encoding="utf-8"))["resumo"]
    r = dados["resumo"]
    assert r["secoes_universo"] == fonte["secoes_universo"]
    assert r["secoes_sinalizadas"] == fonte["secoes_sinalizadas"]
    assert r["fiscais_um_por_local"] == fonte["fiscais"]["um_por_local"]
    for nivel in ("alta", "media", "baixa"):
        assert r["por_nivel"][nivel]["secoes"] == fonte["por_nivel"][nivel]["secoes"]


def test_exemplos_seguem_a_regra_declarada(dados: dict) -> None:
    """Uma seção não repete entre critérios e o nível é o mais alto disponível."""
    if not FISCAIS.exists():
        pytest.skip("fiscais.json pesado ausente")
    modulo = importlib.import_module("video-fiscais-dados")
    fonte = json.loads(FISCAIS.read_text(encoding="utf-8"))
    esperado = modulo.exemplo_por_criterio(fonte["secoes"])
    for c in dados["criterios"]:
        e = esperado[c["id"]]
        atual = c["exemplo"]
        assert (atual["uf"], atual["zona"], atual["secao"]) == (
            e["uf"],
            e["zona"],
            e["secao"],
        )


def test_roteiro_sem_travessao_e_com_as_cenas(roteiro: str) -> None:
    assert "—" not in roteiro
    cenas = re.findall(r"^## (\S+)$", roteiro, re.MULTILINE)
    assert cenas[:3] == ["abertura", "pergunta", "niveis"]
    assert cenas[3:15] == [f"c-{letra}" for letra in "abcdefghijkl"]
    assert cenas[15:] == ["mapa", "quantos", "acao1", "acao2", "fecho"]


def test_roteiro_cita_cada_secao_exemplo(dados: dict, roteiro: str) -> None:
    texto = _sem_acento(roteiro)
    for c in dados["criterios"]:
        e = c["exemplo"]
        municipio = _sem_acento(e["municipio"].split(" (")[0])
        bloco = texto.split(f"## c-{c['id']}\n")[1].split("\n## ")[0]
        assert municipio in bloco, f"critério {c['id']} sem {e['municipio']} no bloco"


def test_roteiro_cita_os_links_e_o_rotulo(roteiro: str) -> None:
    assert "fiscais do PL ponto com ponto br" in roteiro
    assert "brasil ponto arvor ponto co" in roteiro
    assert "Atipicidade estatística não é irregularidade" in roteiro
    assert "prioridade de fiscalização, não de acusação" in roteiro
    assert "fraude" not in roteiro.lower()


@pytest.mark.skipif(not VOZ.exists(), reason="narração não gerada")
def test_manifesto_de_voz_cobre_o_roteiro(roteiro: str) -> None:
    voz = json.loads(VOZ.read_text(encoding="utf-8"))
    ids = re.findall(r"^## (\S+)$", roteiro, re.MULTILINE)
    assert [c["id"] for c in voz["cenas"]] == ids
    for c in voz["cenas"]:
        assert c["segundos"] > 5
        assert c["palavras"] and c["palavras"][-1]["f"] <= c["segundos"] + 0.5
        assert (VIDEO / "public" / c["arquivo"]).exists()


def test_redirecionador_politize() -> None:
    pagina = (ROOT / "docs" / "politize" / "index.html").read_text(encoding="utf-8")
    assert 'http-equiv="refresh" content="0; url=/politizesuavizinhanca.html"' in pagina
    assert (
        'rel="canonical" href="https://brasil.arvor.co/politizesuavizinhanca.html"'
        in pagina
    )
    assert 'name="robots" content="noindex"' in pagina
    assert "location.replace" in pagina
