"""Testes da thread das mudanças de local de votação (três posts, três cards)."""

from pathlib import Path

import pytest
from apuracao_2026.thread_base import digitos_soltos, problemas_de_texto
from mudancas_secoes_2t.thread.base import (
    JSON_MOTOR,
    OG,
    URL,
    URL_LAUDO,
    URL_POLITIZE,
    caminhos_png,
    valores,
)
from mudancas_secoes_2t.thread.pagina import pagina
from mudancas_secoes_2t.thread.posts import (
    CAMPOS_TEXTO,
    MAX_CHARS,
    MIN_CHARS,
    montar,
    verificar,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def posts():
    if not JSON_MOTOR.exists():
        pytest.skip("mudancas.json ainda não gerado")
    return montar()


@pytest.fixture(scope="module")
def html(posts):
    return pagina(posts, caminhos_png(len(posts)))


def test_tres_posts_na_faixa(posts):
    assert len(posts) == 3
    for i, p in enumerate(posts, 1):
        assert MIN_CHARS <= len(p["corpo"]) <= MAX_CHARS, (i, len(p["corpo"]))


def test_verificacao_completa_sem_erros(posts):
    assert verificar(posts) == []


def test_sem_travessao_hashtag_emoji_palavra_vetada(posts, html):
    for p in posts:
        assert problemas_de_texto(p["corpo"]) == []
        assert "fraude" not in p["corpo"].lower()
        assert "—" not in p["svg"] and "–" not in p["svg"]
    assert "—" not in html and "–" not in html


def test_nenhum_algarismo_digitado_nos_modelos(posts):
    for p in posts:
        for campo in CAMPOS_TEXTO:
            assert digitos_soltos(p[campo]) == []
        for par in p["texto"]:
            assert digitos_soltos(par) == []


def test_links_certos(posts):
    assert "http" not in posts[0]["corpo"]
    assert URL_POLITIZE in posts[1]["corpo"]
    assert URL_LAUDO not in posts[1]["corpo"]
    assert URL_LAUDO in posts[2]["corpo"]
    assert URL_POLITIZE not in posts[2]["corpo"]


def test_numeros_chave_saem_do_json(posts):
    v = valores()
    assert v["n_mr"] == "1.211" and v["n_a"] == "781" and v["n_fora"] == "6.036"
    assert v["dif_votos"] == "568" and v["saldo"] == "102"
    assert v["n_tse"] == "4.352" and v["n_col"] == "4.864" and v["n_pai"] == "1.106"
    assert v["pct_l"] == "49,69%" and v["pct_f"] == "43,32%"
    for chave in ("n_mr", "n_tse", "n_col", "n_con", "n_pai"):
        assert v[chave] in posts[0]["corpo"]
    assert v["dif_votos"] in posts[2]["corpo"] and v["saldo"] in posts[2]["corpo"]


def test_figuras_sem_cor_de_candidato_fora_do_voto(posts):
    for p in posts[:2]:
        assert "#b02f21" not in p["svg"].lower()
        assert "#1457aa" not in p["svg"].lower()
    assert "#b02f21" in posts[2]["svg"].lower()


def test_pagina_completa(html):
    assert html.count("G-ZPYEE8P9YC") >= 1
    assert html.count("googletagmanager.com/gtag/js") == 1
    assert f'rel="canonical" href="{URL}"' in html
    assert f'property="og:image" content="{OG}"' in html
    assert html.count('class="card"') == 3
    assert "1.211" in html


def test_pngs_listados():
    assert caminhos_png(3) == [
        "img/mudancas_secoes/thread/01.png",
        "img/mudancas_secoes/thread/02.png",
        "img/mudancas_secoes/thread/03.png",
    ]
