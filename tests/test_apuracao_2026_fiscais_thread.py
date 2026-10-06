"""Testes da thread dos fiscais (capítulo 13 do dossiê da apuração)."""

import re
from pathlib import Path

import pytest
from apuracao_2026.fthread_build import (
    CAMPOS_TEXTO,
    MAX_CHARS,
    MIN_CHARS,
    caminhos_png,
    montar,
    valores,
    verificar,
)
from apuracao_2026.fthread_pagina import pagina
from apuracao_2026.thread_base import digitos_soltos, problemas_de_texto

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/fiscais_thread.html"


@pytest.fixture(scope="module")
def posts():
    if not (ROOT / "analysis/apuracao_2026/dados/fiscais.json").exists():
        pytest.skip("fiscais.json ainda não gerado")
    return montar()


@pytest.fixture(scope="module")
def html(posts):
    return pagina(posts, caminhos_png(len(posts)), valores())


def test_quantidade_e_tamanho(posts):
    assert 5 <= len(posts) <= 7
    for i, p in enumerate(posts, 1):
        assert MIN_CHARS <= len(p["corpo"]) <= MAX_CHARS, (i, len(p["corpo"]))


def test_verificacao_completa_sem_erros(posts):
    assert verificar(posts) == []


def test_sem_travessao_hashtag_emoji(posts, html):
    for p in posts:
        assert problemas_de_texto(p["corpo"]) == []
    assert "—" not in html and "–" not in html


def test_nenhum_algarismo_digitado(posts):
    for p in posts:
        for modelo in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            assert digitos_soltos(modelo) == [], modelo


def test_arco_da_thread(posts):
    tags = [p["tag"] for p in posts]
    assert tags[0] == "A lista" and tags[-1] == "O kit do fiscal"
    assert "O que já aconteceu" in tags
    corpo = " ".join(p["corpo"] for p in posts)
    for termo in (
        "pianista",
        "Boca de urna",
        "Transporte irregular",
        "zerésima",
        "contingência",
        "cabresto",
        "facção",
    ):
        assert termo in corpo, termo
    assert "validar com a PM e o TRE local" in posts[-1]["corpo"]


def test_numeros_chave(posts):
    v = valores()
    assert v["n_secoes"] in posts[0]["corpo"] and v["n_locais"] in posts[0]["corpo"]
    assert v["xlsx_tam"] in posts[-1]["corpo"]


def test_verificar_reprova_texto_fora_da_regra(posts):
    ruim = [dict(p) for p in posts]
    ruim[0] = dict(ruim[0], corpo=ruim[0]["corpo"] + " — #fraude")
    erros = verificar(ruim)
    assert any("travessão" in e for e in erros)
    assert any("hashtag" in e for e in erros)


def test_metatags_e_pngs(html, posts):
    og = "https://brasil.arvor.co/img/og/fiscais_thread.png"
    assert f'<meta property="og:image" content="{og}">' in html
    assert f'<meta name="twitter:image" content="{og}">' in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert html.count('class="card"') == len(posts)
    assert caminhos_png(len(posts))[0] == "img/apuracao_2026/fiscais_thread/01.png"
    assert len(re.findall(r'data-copy="', html)) == len(posts)


def test_pagina_publicada_em_dia(html):
    if not PAGINA.exists():
        pytest.skip("página ainda não gerada")
    assert PAGINA.read_text(encoding="utf-8") == html


def test_card_dos_casos_tem_rotulo_curto(posts):
    from apuracao_2026.fthread_base import cenarios

    svg = next(p["svg"] for p in posts if p["tag"] == "O que já aconteceu")
    for c in cenarios()["casos"]:
        assert c["rotulo_curto"] in svg.replace("&#x27;", "'"), c["id"]
