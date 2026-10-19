"""Monta a página: cabeça, herói, navegação, capítulos, rodapé, folha de estilo e script."""

from __future__ import annotations

import sys
from pathlib import Path

from . import figuras
from .capitulos_a import (
    cap1_numeros,
    cap2_mudou,
    cap3_distancias,
    cap4_motivos,
    cap5_clima,
)
from .capitulos_b import cap6_primeiro_turno, cap7_efeito, cap8_votos
from .capitulos_c import cap9_veredito, cap10_eleitor, cap11_fontes
from .contexto import Contexto
from .estilo import CSS, JS
from .util import ROOT, SITE, SLUG, data_br, esc, ic, inteiro, limpa, pp

sys.path.insert(0, str(ROOT / "scripts"))
from ga_tag import injetar

NAV = [
    ("numeros", "Números"),
    ("mudou", "O que mudou"),
    ("distancias", "Distâncias"),
    ("motivos", "Motivos"),
    ("clima", "Clima"),
    ("primeiro-turno", "1º turno"),
    ("efeito", "Efeito"),
    ("votos", "Votos"),
    ("veredito", "Veredito"),
    ("eleitor", "Seu local"),
    ("fontes", "Fontes"),
]
FONTES_CSS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;"
    "1,9..144,400&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
)


def textos_meta(c: Contexto) -> tuple[str, str, str]:
    d = c.d
    dd = d["efeito_1t"]["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    painel = next(
        n for n in d["confronto_publico"]["numeros_publicos"] if n["id"] == "painel_tse"
    )
    titulo = "Mudanças de local de votação e abstenção no 2º turno | Arvor"
    resumo = (
        f"O painel do TSE lista {inteiro(painel['secoes']['publico'])} seções alteradas; o cadastro de 18/10 mostra "
        f"{inteiro(c.secoes_real())} com mudança real, {inteiro(c.mr['por_categoria']['A']['secoes'])} delas de volta ao prédio original. "
        f"Efeito medido no 1º turno: {pp(dd['valor'])} de abstenção ({ic(dd['ic95'])})."
    )
    return titulo, resumo, limpa(resumo)


def hero(c: Contexto) -> str:
    d = c.d
    cp = d["confronto_publico"]
    pan = next(n for n in cp["numeros_publicos"] if n["id"] == "painel_tse")
    dd = d["efeito_1t"]["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    return (
        '<section class="hero"><div>'
        f'<p class="eyebrow">Laudo · 2º turno de 2026 · {esc(data_br(d["gerado_em"]))}</p>'
        "<h1>Mudanças de local de votação<br><em>entre os turnos e abstenção.</em></h1>"
        f'<p class="deck">Falou-se em mais de 4 mil seções. O painel do próprio TSE diz {inteiro(pan["secoes"]["publico"])}. '
        f"Nossa conta, sobre o cadastro oficial de 18/10, achou <b>{inteiro(c.secoes_real())} seções e {inteiro(c.mr['eleitores'])} eleitores</b> "
        "que mudam de prédio. A maioria volta ao local original. O efeito sobre a abstenção, medido no 1º turno, é pequeno no agregado.</p>"
        '<div class="chips">'
        f'<span>{inteiro(c.mr["por_categoria"]["A"]["secoes"])} voltam ao prédio original</span>'
        f'<span>distância mediana de {inteiro(c.mr["distancia_mediana_m"])} m</span>'
        "<span>quatro números públicos que não batem</span></div></div>"
        '<aside class="placar" aria-label="Placar do laudo">'
        '<p class="eyebrow">Eleitores em jogo</p>'
        f"<b>{inteiro(c.mr['eleitores'])}</b><small>em {inteiro(c.secoes_real())} seções com mudança real de prédio</small><hr>"
        '<p class="eyebrow">Efeito medido no 1º turno</p>'
        f"<b>{pp(dd['valor'])}</b><small>de abstenção ({ic(dd['ic95'])}). Diferença em diferenças contra 2022. Não é efeito causal identificado.</small>"
        "</aside></section>"
    )


def guia(c: Contexto) -> str:
    return (
        '<section class="guia" aria-label="Três caminhos de leitura">'
        '<article><span>Capítulo 1</span><h3><a href="#numeros">Quanto mudou?</a></h3><p>Quatro números públicos, quatro tamanhos, e o recorte do cadastro que mais se aproxima de cada um.</p></article>'
        '<article><span>Capítulo 9</span><h3><a href="#veredito">O que o dado sustenta</a></h3><p>Fato medido, inferência e juízo separados, com o que contraria a tese.</p></article>'
        '<article><span>Capítulo 10</span><h3><a href="#eleitor">Qual é o meu local?</a></h3><p>Lista filtrável dos 334 pares de local, com link de mapa e rota.</p></article>'
        "</section>"
    )


def pagina(c: Contexto) -> str:
    figuras.reset_ids()
    titulo, resumo, _ = textos_meta(c)
    capitulos = [
        cap1_numeros(c),
        cap2_mudou(c),
        cap3_distancias(c),
        cap4_motivos(c),
        cap5_clima(c),
        cap6_primeiro_turno(c),
        cap7_efeito(c),
        cap8_votos(c),
        cap9_veredito(c),
        cap10_eleitor(c),
        cap11_fontes(c),
    ]
    nav = "".join(f'<a href="#{i}">{r}</a>' for i, r in NAV)
    url = f"{SITE}/{SLUG}.html"
    img = f"{SITE}/img/og/{SLUG}.png"
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(titulo)}</title>
<meta name="description" content="{esc(resumo)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(titulo)}"><meta property="og:description" content="{esc(resumo)}"><meta property="og:type" content="article"><meta property="og:url" content="{url}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(titulo)}"><meta name="twitter:description" content="{esc(resumo)}"><meta name="twitter:image" content="{img}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTES_CSS}"><link rel="stylesheet" href="assets/{SLUG}.css"></head>
<body><a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="masthead"><a href="index.html">ARVOR / Biblioteca</a><span>Laudo · locais de votação</span></header>
<main id="conteudo">{hero(c)}<nav class="chapter-nav" aria-label="Capítulos">{nav}</nav>{guia(c)}
{"".join(capitulos)}
</main>
<footer><a href="index.html">Arvor / Biblioteca</a><p>Fato medido, inferência e juízo identificados. A leitura é agregada por seção: o voto é secreto e nada aqui identifica eleitor.</p><a href="politizesuavizinhanca.html">Politize sua vizinhança</a><a href="reponderacao_pnad.html">Centrais e simulador</a></footer>
<script defer src="assets/{SLUG}.js"></script></body></html>"""
    html = injetar(limpa(html).replace("<section ", "\n<section "))
    return html + "\n"


def escrever(c: Contexto, docs: Path | None = None) -> list[Path]:
    docs = docs or ROOT / "docs"
    (docs / "assets").mkdir(parents=True, exist_ok=True)
    saidas = {
        docs / f"{SLUG}.html": pagina(c),
        docs / "assets" / f"{SLUG}.css": CSS,
        docs / "assets" / f"{SLUG}.js": JS,
    }
    for caminho, texto in saidas.items():
        caminho.write_text(texto, encoding="utf-8")
    return list(saidas)
