"""Testes da super thread da apuração do 1º turno de 2026."""

import re
from pathlib import Path

import pytest
from apuracao_2026.thread_base import digitos_soltos, problemas_de_texto
from apuracao_2026.thread_build import (
    CAMPOS_TEXTO,
    CORTES,
    MAX_CHARS,
    MIN_CHARS,
    caminhos_png,
    montar,
    valores,
    verificar,
)
from apuracao_2026.thread_pagina import pagina

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/apuracao_1o_turno_2026_thread.html"


@pytest.fixture(scope="module")
def posts():
    return montar()


@pytest.fixture(scope="module")
def html(posts):
    return pagina(posts, caminhos_png(len(posts)), valores())


def test_quantidade_de_cards(posts):
    assert 20 <= len(posts) <= 25


def test_tamanho_dos_posts(posts):
    for i, p in enumerate(posts, 1):
        assert MIN_CHARS <= len(p["corpo"]) <= MAX_CHARS, (i, len(p["corpo"]))


def test_verificacao_completa_sem_erros(posts):
    assert verificar(posts) == []


def test_sem_travessao_hashtag_emoji(posts, html):
    for p in posts:
        assert problemas_de_texto(p["corpo"]) == []
    assert "—" not in html
    assert "–" not in html


def test_nenhum_algarismo_digitado(posts):
    for p in posts:
        for modelo in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            assert digitos_soltos(modelo) == [], modelo


def test_detector_de_algarismo_pega_numero_solto():
    assert digitos_soltos("Flávio teve 47,03% dos válidos") == ["47,03%"]
    assert digitos_soltos("Flávio teve {f_pct} no 1º turno de 2026") == []


def test_posts_do_segundo_turno_no_fim_com_juizo_editorial(posts):
    finais = posts[-4:]
    for p in finais:
        assert "2º turno" in p["tag_f"]
        assert "juízo editorial" in p["corpo"].lower()


def test_citacoes_so_com_fonte_arquivada(posts):
    corpo = posts[-1]["corpo"]
    for trecho in CORTES.values():
        assert trecho in corpo
    assert "estagnação" not in corpo


def test_numeros_chave_batem_com_os_dados(posts):
    v = valores()
    assert v["f_pct"] in posts[0]["corpo"]
    assert v["dif_votos"] in posts[0]["corpo"]
    assert v["eq_lula_todos"] in posts[-4]["corpo"]


def test_cards_e_svg(html, posts):
    assert html.count('class="card"') == len(posts)
    assert html.count("<svg") == len(posts)
    assert "aspect-ratio:1/1" in html


def test_metatags_sociais(html):
    og = "https://brasil.arvor.co/img/og/apuracao_1o_turno_2026_thread.png"
    assert f'<meta property="og:image" content="{og}">' in html
    assert f'<meta name="twitter:image" content="{og}">' in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html
    assert "noindex" not in html


def test_lista_de_pngs(html, posts):
    caminhos = caminhos_png(len(posts))
    assert caminhos[0] == "img/apuracao_2026/thread/01.png"
    for c in caminhos:
        assert c in html


def test_pagina_publicada_em_dia(html):
    if not PAGINA.exists():
        pytest.skip("página ainda não gerada")
    assert PAGINA.read_text(encoding="utf-8") == html


def test_botao_de_copiar_funciona_sem_clipboard(html):
    assert "execCommand('copy')" in html
    assert len(re.findall(r'data-copy="', html)) >= 20
