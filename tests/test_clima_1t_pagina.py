"""Relatório público de clima, bateria e abstenção: página gerada, regras de escrita e dados."""

from pathlib import Path

import pytest
from clima_1t.pagina.montagem import pagina
from clima_1t.pagina.util import SLUG, Dados, dec, inteiro
from ga_tag import GA_ID

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML = DOCS / f"{SLUG}.html"


@pytest.fixture(scope="module")
def dados():
    return Dados()


@pytest.fixture(scope="module")
def html():
    return HTML.read_text(encoding="utf-8")


def test_arquivos_existem():
    for caminho in (
        HTML,
        DOCS / "assets" / f"{SLUG}.css",
        DOCS / "assets" / f"{SLUG}.js",
        DOCS / "img" / "og" / f"{SLUG}.png",
    ):
        assert caminho.exists(), caminho


def test_ga_tag_uma_vez_no_head(html):
    assert html.count("gtag/js?id=") == 1
    assert html.count(GA_ID) == 2
    assert GA_ID in html[: html.lower().find("</head>")]


def test_sem_travessao_nem_fraude():
    for nome in (f"{SLUG}.html", f"assets/{SLUG}.css", f"assets/{SLUG}.js"):
        texto = (DOCS / nome).read_text(encoding="utf-8")
        assert "—" not in texto, nome
        assert "fraude" not in texto.lower(), nome


def test_metatags(html):
    assert f'rel="canonical" href="https://brasil.arvor.co/{SLUG}.html"' in html
    assert f'og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"' in html
    assert 'og:image:width" content="1200"' in html
    assert 'og:image:height" content="630"' in html


def test_capitulos(html):
    for i in (
        "metodo",
        "bateria",
        "abstencao",
        "bateria-abstencao",
        "curiosos",
        "uf",
        "previsao",
        "veredito",
        "uso",
        "fontes",
    ):
        assert f'id="{i}"' in html
        assert f'href="#{i}"' in html


def test_totais_do_json_na_pagina(dados, html):
    d = dados.d
    for n in (
        d["cobertura"]["archive"]["celulas"],
        d["cobertura"]["urnas_amostra"],
        d["previsao_25_10"]["pais"]["eleitores"]["alto"],
        d["previsao_25_10"]["pais"]["eleitores"]["medio"],
    ):
        assert inteiro(n) in html
    forte = dados.faixas("chuva_votacao", "bateria_votacao")[3]
    assert dec(forte["razao_vs_ref"]["valor"], 2) + "×" in html
    assert dec(forte["parcela_pct"]["valor"], 2) in html
    assert (
        dec(dados.reg_bateria("bateria_votacao", "chuva_votacao_x")["odds_ratio"], 2)
        in html
    )
    assert d["previsao_25_10"]["gerado_em"][11:13] in html
    for it in d["locais_curiosos"]["b_bateria_em_predio_seco_e_sozinho"]["itens"][:10]:
        assert it["mapa"].replace("&", "&amp;") in html


def test_mapa_de_fiscais_linkado(html):
    assert "fiscais_mapa.html#uf=BA&amp;l=BA-34312-64-1031" in html


def test_build_idempotente(dados, html):
    assert pagina(dados) == html


def test_publicacao_de_abril_sem_js_completa(html):
    # a página inteira existe sem JavaScript: capítulos e tabelas estão no HTML
    assert html.count("<table") >= 15
    assert "<svg" in html
