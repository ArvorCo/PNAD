"""Laudo público das mudanças de local de votação: página gerada, regras de escrita e dados."""

import importlib
import re
from pathlib import Path

import pytest
from ga_tag import GA_ID
from mudancas_secoes_2t.pagina.contexto import Contexto
from mudancas_secoes_2t.pagina.montagem import escrever, pagina
from mudancas_secoes_2t.pagina.motivos import GERAL, SEM, classificar_par, resumo
from mudancas_secoes_2t.pagina.util import SLUG, dec, inteiro, lista_secoes, sinal

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML = DOCS / f"{SLUG}.html"


@pytest.fixture(scope="module")
def ctx():
    return Contexto()


@pytest.fixture(scope="module")
def html():
    return HTML.read_text(encoding="utf-8")


def test_pagina_e_assets_existem():
    for caminho in (
        HTML,
        DOCS / "assets" / f"{SLUG}.css",
        DOCS / "assets" / f"{SLUG}.js",
    ):
        assert caminho.exists(), caminho


def test_tag_do_analytics_uma_vez_no_head(html):
    assert html.count(GA_ID) == 2
    assert html.count("gtag/js?id=") == 1
    assert GA_ID in html[: html.lower().find("</head>")]


def test_sem_travessao_nem_palavra_vetada(html):
    for nome in (f"{SLUG}.html", f"assets/{SLUG}.css", f"assets/{SLUG}.js"):
        texto = (DOCS / nome).read_text(encoding="utf-8")
        assert "—" not in texto, nome
        assert "fraude" not in texto.lower(), nome


def test_metatags(html):
    assert f'rel="canonical" href="https://brasil.arvor.co/{SLUG}.html"' in html
    assert f'og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"' in html
    assert 'og:image:width" content="1200"' in html
    assert 'og:image:height" content="630"' in html
    assert 'twitter:card" content="summary_large_image"' in html
    assert "<title>" in html


def test_onze_capitulos_e_navegacao(html):
    for i in (
        "numeros",
        "mudou",
        "distancias",
        "motivos",
        "clima",
        "primeiro-turno",
        "efeito",
        "votos",
        "veredito",
        "eleitor",
        "fontes",
    ):
        assert f'id="{i}"' in html
        assert f'href="#{i}"' in html


def test_totais_do_json_aparecem_na_pagina(ctx, html):
    d = ctx.d
    mr = d["resumo"]["mudanca_real"]
    dd = d["efeito_1t"]["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    esperados = [
        inteiro(mr["secoes"]),
        inteiro(mr["eleitores"]),
        inteiro(mr["por_categoria"]["A"]["secoes"]),
        inteiro(mr["distancia_mediana_m"]),
        inteiro(d["resumo"]["fora_do_original"]["secoes_2t"]),
        sinal(dd["valor"]),
        sinal(dd["ic95"][0]),
        sinal(dd["ic95"][1]),
        dec(
            d["comportamento_1t"]["grupos"]["mudanca_real"]["metricas"][
                "flavio_validos"
            ]["pais"]["diferenca_pp"]["valor"]
        ).replace("-", "−"),
        inteiro(d["confronto_painel"]["ambos"]),
        inteiro(d["confronto_painel"]["so_painel"]),
        inteiro(d["confronto_painel"]["so_zip"]),
    ]
    esperados += [
        inteiro(n["secoes"]["publico"])
        for n in d["confronto_publico"]["numeros_publicos"]
    ]
    esperados += [
        inteiro(d["efeito_1t"]["tratamento"]["urnas"]),
        inteiro(
            d["cenarios_abstencao"]["estimativa_brasileira"]["saldo_1t_para_2t"][
                "central"
            ]["variacao_diferenca_flavio_menos_lula_votos"]
            * -1
        ),
    ]
    faltam = [x for x in esperados if x not in html]
    assert not faltam, faltam


def test_toda_linha_de_locais_tem_link_do_google_maps(ctx, html):
    tabela = html.split('id="tabela-locais"', 1)[1].split("</table>", 1)[0]
    linhas = re.findall(r"<tr data-uf=.*?</tr>", tabela, flags=re.DOTALL)
    assert len(linhas) == len(ctx.reais) == 334
    for linha in linhas:
        assert "https://www.google.com/maps/" in linha
    assert sum(len(x["secoes"]) for x in ctx.reais) == ctx.mr["secoes"]


def test_motivos_somam_e_sem_motivo_e_a_maior(ctx):
    r = resumo(ctx.d["locais"])
    assert r["linhas"][0]["chave"] == SEM
    assert r["linhas"][0]["secoes"] == max(x["secoes"] for x in r["linhas"])
    assert r["sem_nota"]["secoes"] + r["com_nota"]["secoes"] == r["secoes_total"]
    assert classificar_par({"motivo_tre": None}) == [SEM]
    geral = {"motivo_tre": {"texto": "Motivos gerais da nota (não por local): idem"}}
    assert classificar_par(geral) == [GERAL]
    reforma = {"motivo_tre": {"texto": "reformas em escolas"}}
    assert classificar_par(reforma) == ["reforma"]


def test_formatadores():
    assert inteiro(1234567) == "1.234.567"
    assert dec(1.5) == "1,50"
    assert sinal(-0.5) == "−0,50"
    assert lista_secoes([126, 127, 128, 129, 130, 131, 132, 224]) == "126 a 132, 224"


def test_build_e_idempotente_e_igual_ao_publicado(ctx, tmp_path):
    primeira = escrever(ctx, tmp_path)
    copia = {p.name: p.read_bytes() for p in primeira}
    segunda = escrever(ctx, tmp_path)
    assert {p.name: p.read_bytes() for p in segunda} == copia
    assert pagina(ctx) == HTML.read_text(
        encoding="utf-8"
    ), "rode mudancas-secoes-2t-build.py"


def test_cards_sociais_registrados():
    mod = importlib.import_module("social-card-mudancas")
    card = mod.card(ROOT)
    thread = mod.card_thread(ROOT)
    assert card["slug"] == SLUG
    assert thread["slug"] == "mudancas_secoes_thread"
    assert thread["thread"] is True and thread["accent"] == "blue"
    for c in (card, thread):
        assert "—" not in repr(c)
        assert len(c["stats"]) == 3
    assert (ROOT / "docs" / "img" / "og" / f"{SLUG}.png").exists()
