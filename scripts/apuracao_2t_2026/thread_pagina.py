"""Página da thread do 2º turno: reaproveita CSS, JS e card 1:1 da thread do 1º turno."""

from __future__ import annotations

from apuracao_2026.thread_pagina import CSS, JS
from apuracao_2026.thread_pagina import render_card as _render_card
from ga_tag import injetar

from .thread_base import DOSSIE, OG, SLUG, URL

ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}

CSS_EXTRA = ""


def esc(s) -> str:
    return "".join(ESC.get(c, c) for c in str(s))


def render_card(i: int, total: int, post: dict) -> str:
    html = _render_card(i, total, post).replace(
        "Arvor · Apuração 2026", "Arvor · Apuração 2º turno"
    )
    return html


def pagina(posts: list[dict], pngs: list[str], v: dict) -> str:
    total = len(posts)
    cards = "".join(render_card(i + 1, total, p) for i, p in enumerate(posts))
    rail = "".join(f'<a href="#p{i + 1:02d}">{i + 1}</a>' for i in range(total))
    lista = "".join(f'<li><a href="{esc(p)}">{esc(p)}</a></li>' for p in pngs)
    titulo = "A apuração do 2º turno de 2026: a thread"
    desc = (
        f"{total} cards quadrados com gráficos e o texto pronto para o X: Lula "
        f"{v['l_pct']} contra {v['f_pct']}, {v['sil_min']} minutos sem arquivo do TSE, "
        "a prorrogação que não encontrou urna aberta, a projeção da noite e o que mudou "
        "entre o último campo das pesquisas e a urna."
    )
    return injetar(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thread da apuração do 2º turno · Arvor</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{URL}">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#192e2b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{OG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:title" content="{esc(titulo)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{OG}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,800;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;600;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
<style>{CSS}{CSS_EXTRA}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · thread</div>
    <a class="back" href="{DOSSIE}.html">Abrir o dossiê</a>
  </div>
  <h1>A apuração do 2º turno de 2026. <em>A thread, card a card.</em></h1>
  <p class="deck">Lula terminou o 2º turno com {esc(v["l_pct"])} dos válidos contra {esc(v["f_pct"])} de Flávio Bolsonaro, {esc(v["dif_mi"])} de votos à frente. Esta é a thread do dossiê da apuração: a parada de {esc(v["sil_min"])} minutos sem arquivo do TSE, a prorrogação do STF e o atraso na transmissão, a projeção da noite, cedo contra tarde, 1º contra 2º turno, a abstenção, a análise seção por seção, as pesquisas contra a urna, o que mudou entre sábado e domingo, a hipótese do autor, a paralela, os limites, os municípios em que Flávio teve menos votos no 2º turno e a pendência documental com o TSE.</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado que sai em 1080 por 1080 pixels; os PNGs prontos para anexar estão listados no fim da página. Embaixo de cada card está o texto do post, com o botão de copiar. Nenhum número foi digitado à mão: todos saem dos arquivos de dados do dossiê, e o gerador recusa texto com algarismo solto, travessão, hashtag ou emoji. Onde há opinião da casa, o próprio texto diz juízo editorial.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{cards}</main>
<footer class="wrap">
  <h2>Imagens para anexar</h2>
  <p>Os {total} cards em PNG, 1080 por 1080 pixels, na ordem dos posts:</p>
  <ol class="pngs">{lista}</ol>
  <h2>Reprodução</h2>
  <p>python3 scripts/apuracao-2t-2026-thread.py (com --png para regerar as imagens). Os números vêm de analysis/apuracao_2t_2026/dados/ e da cronologia de notícias da noite, com veículo, hora e cópia arquivada. O dossiê completo está em <a href="{DOSSIE}.html">{DOSSIE}.html</a>.</p>
</footer>
<script>{JS}</script>
</body>
</html>
""")


__all__ = ["CSS_EXTRA", "SLUG", "pagina", "render_card"]
