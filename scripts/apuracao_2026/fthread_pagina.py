"""Página da thread dos fiscais: mesmo card 1:1 e mesmo CSS da super thread."""

from __future__ import annotations

from ga_tag import injetar

from .fthread_base import CAPITULO, DOSSIE, OG, SLUG, URL
from .thread_base import esc
from .thread_pagina import CSS, JS, render_card


def pagina(posts: list[dict], pngs: list[str], v: dict) -> str:
    total = len(posts)
    cards = "".join(render_card(i + 1, total, p) for i, p in enumerate(posts))
    rail = "".join(f'<a href="#p{i + 1:02d}">{i + 1}</a>' for i in range(total))
    lista = "".join(f'<li><a href="{esc(p)}">{esc(p)}</a></li>' for p in pngs)
    titulo = "Onde colocar fiscal no 2º turno: a thread"
    desc = (
        f"{total} cards quadrados com o texto pronto para o X: {v['n_secoes']} seções atípicas em "
        f"{v['n_locais']} locais de votação, os cenários clássicos de manipulação do voto, os casos "
        "documentados no Brasil e o kit do fiscal. Atipicidade não é irregularidade."
    )
    return injetar(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} · Arvor</title>
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
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · thread dos fiscais</div>
    <a class="back" href="{CAPITULO}">Abrir o capítulo</a>
  </div>
  <h1>Onde colocar fiscal no 2º turno. <em>A thread, card a card.</em></h1>
  <p class="deck">{esc(v["n_secoes"])} seções atípicas em {esc(v["n_locais"])} locais de votação, em três níveis de prioridade, com endereço. Esta thread explica como a lista foi feita, o que ela não diz, os cenários clássicos que o fiscal existe para impedir, o que já aconteceu no Brasil com data e tribunal, e o que levar e conferir no dia. {esc(v["rot_atipico"])} {esc(v["rot_prioridade"])}</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado de 1080 por 1080 pixels; os PNGs estão listados no fim da página. Embaixo de cada card está o texto do post, para X premium, com o botão de copiar. Nenhum número foi digitado à mão: todos saem de fiscais.json e de fontes_fiscais.json, e o gerador recusa texto com algarismo solto, travessão, hashtag ou emoji. Cenário é hipótese de risco; caso é passado documentado; nada disso é atribuído à eleição de 2026.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{cards}</main>
<footer class="wrap">
  <h2>Baixar a lista</h2>
  <p><a href="assets/fiscais_2026.xlsx">Planilha Excel</a> ({esc(v["xlsx_tam"])}), <a href="assets/fiscais_2026.csv">CSV por seção</a> e <a href="assets/fiscais_2026_por_local.csv">CSV por local</a>. O capítulo completo, com mapa navegável, critérios e fontes, está em <a href="{CAPITULO}">{DOSSIE}.html#fiscais</a>.</p>
  <h2>Imagens para anexar</h2>
  <p>Os {total} cards em PNG, 1080 por 1080 pixels, na ordem dos posts:</p>
  <ol class="pngs">{lista}</ol>
  <h2>Reprodução</h2>
  <p>python3 scripts/apuracao-2026-fiscais-thread.py (com --png para regerar as imagens). Os números vêm de analysis/apuracao_2026/dados/fiscais.json; cenários, casos e base legal, de analysis/apuracao_2026/fontes_fiscais.json, com veículo ou tribunal, data e endereço de cada fonte.</p>
</footer>
<script>{JS}</script>
</body>
</html>
""")


__all__ = ["SLUG", "pagina"]
