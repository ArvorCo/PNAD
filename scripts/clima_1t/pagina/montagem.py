"""Monta a página: cabeça, herói, navegação, capítulos, rodapé, folha de estilo e script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import figs
from .cap_a import (
    cap1_metodo,
    cap2_bateria,
    cap3_abstencao,
    cap4_bateria_abstencao,
    hero,
)
from .cap_b import cap5_curiosos, cap6_uf, cap7_previsao
from .cap_c import cap8_veredito, cap9_uso, cap10_fontes
from .cenario import secao_cenario
from .estilo import CSS, JS
from .util import ROOT, SITE, SLUG, Dados, dec, esc, ic, inteiro, limpa, pp

sys.path.insert(0, str(ROOT / "scripts"))
from ga_tag import injetar

NAV = [
    ("cenario-abstencao", "Mapas e cenário"),
    ("previsao", "Previsão 25/10"),
    ("metodo", "Método"),
    ("bateria", "Bateria"),
    ("abstencao", "Abstenção"),
    ("bateria-abstencao", "Bateria e abstenção"),
    ("curiosos", "Locais"),
    ("uf", "UF"),
    ("veredito", "Veredito"),
    ("uso", "Seu uso"),
    ("fontes", "Fontes"),
]
FONTES_CSS = (
    "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;"
    "1,9..144,400&family=IBM+Plex+Sans+Condensed:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
)
TITULO = "Chuva no 2º turno: previsão, mapas e abstenção | Arvor"


def resumo(dados: Dados) -> str:
    d = dados.d
    forte = next(
        f
        for f in dados.faixas("chuva_votacao", "bateria_votacao")
        if f["faixa"] == "forte"
    )["razao_vs_ref"]
    b = d["abstencao_x_chuva"]["binario"]["chuva_votacao"]
    mun = next(iter(b["dentro_do_municipio"]["grupos"].values()))["abst_vs_ref_pp"]
    return limpa(
        f"Chuva forte no 1º turno de 2026 se associou a {dec(forte['valor'], 2)}× o registro de bateria nas urnas "
        f"(IC 95% de {dec(forte['ic95'][0], 2)} a {dec(forte['ic95'][1], 2)}), por coincidência entre urnas do município. "
        f"A abstenção, dentro do município, difere {pp(mun['valor'])} ({ic(mun['ic95'])}). "
        f"Previsão para 25/10: {inteiro(dados.previsao_pais()['eleitores']['alto'])} eleitores em células de risco climático alto."
    )


def pagina(dados: Dados) -> str:
    figs.reset_ids()
    capitulos = [
        secao_cenario(dados),
        cap7_previsao(dados),
        cap1_metodo(dados),
        cap2_bateria(dados),
        cap3_abstencao(dados),
        cap4_bateria_abstencao(dados),
        cap5_curiosos(dados),
        cap6_uf(dados),
        cap8_veredito(dados),
        cap9_uso(dados),
        cap10_fontes(dados),
    ]
    nav = "".join(f'<a href="#{i}">{r}</a>' for i, r in NAV)
    desc = resumo(dados)
    url = f"{SITE}/{SLUG}.html"
    img = f"{SITE}/img/og/{SLUG}.png"
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(TITULO)}</title>
<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(TITULO)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{url}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(TITULO)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{img}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTES_CSS}"><link rel="stylesheet" href="assets/{SLUG}.css"></head>
<body><a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="masthead"><a href="index.html">ARVOR / Biblioteca</a><span>Relatório · clima e urna</span></header>
<main id="conteudo">{hero(dados)}<nav class="chapter-nav" aria-label="Capítulos">{nav}</nav>
{"".join(capitulos)}
</main>
<footer><a href="index.html">Arvor / Biblioteca</a><p>Fato medido, inferência e juízo identificados. A leitura é agregada por seção e por local: o voto é secreto e nada aqui identifica eleitor. Registro de bateria é operação prevista da urna.</p><a href="fiscais_mapa.html">Mapa de fiscais</a><a href="mudancas_secoes_abstencoes.html">Mudanças de local no 2º turno</a></footer>
<script defer src="assets/{SLUG}.js"></script></body></html>"""
    html = injetar(limpa(html).replace("<section ", "\n<section "))
    return html + "\n"


def escrever(dados: Dados, docs: Path | None = None) -> list[Path]:
    docs = docs or ROOT / "docs"
    (docs / "assets").mkdir(parents=True, exist_ok=True)
    saidas = {
        docs / f"{SLUG}.html": pagina(dados),
        docs / "assets" / f"{SLUG}.css": CSS,
        docs / "assets" / f"{SLUG}.js": JS,
    }
    for caminho, texto in saidas.items():
        caminho.write_text(texto, encoding="utf-8")
    destino = docs / "assets/clima_1t"
    destino.mkdir(parents=True, exist_ok=True)
    for nome, doc in (
        ("dados.json", {k: v for k, v in dados.d.items() if k != "_interno"}),
        ("cenario_2t.json", dados.territorio),
    ):
        path = destino / nome
        path.write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        )
        saidas[path] = ""
    return list(saidas)
