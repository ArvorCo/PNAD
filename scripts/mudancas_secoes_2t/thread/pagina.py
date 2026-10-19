"""Página da thread das mudanças de local: card 1:1 da casa, com marca e cores próprias."""

from __future__ import annotations

from apuracao_2026.thread_base import esc
from apuracao_2026.thread_pagina import CSS, JS
from ga_tag import injetar

from .base import LAUDO, OG, URL, valores

ACENTO = {"ouro": "#7d5b00", "verde": "#0b6650", "marinho": "#22305a"}
TITULO = "Mudança de local de votação: a thread"

CSS_EXTRA = """
a{color:#0b6650}
h1 em{color:#7d5b00}
.back{color:#0b6650;border-color:#0b6650}
.howto{border-left-color:#7d5b00}
.copy-btn:focus-visible{outline-color:#0b6650}
.c-head{padding:1.6cqw 3.4cqw}
.c-top{padding-top:2.8cqw}
.c-top h2{font-size:4.3cqw;line-height:1.06}
.c-metric span{font-size:1.85cqw}
.c-viz{padding:1.6cqw 3.4cqw .6cqw}
.c-foot{font-size:1.6cqw;padding:1.4cqw 3.4cqw}
@media (width <= 720px){
  .c-top h2{font-size:1.5rem}
  .c-foot{font-size:.74rem}
}
"""


def _tamanho_metrica(s: str) -> float:
    n = len(s)
    return 7.0 if n <= 6 else round(max(3.6, min(7.0, 44 / n)), 1)


def render_card(i: int, total: int, p: dict) -> str:
    cor = ACENTO[p["tom"]]
    corpo = p["corpo"]
    return f"""
<section class="post" id="p{i:02d}">
  <div class="post-label">Post {i:02d}/{total:02d} · <b>{esc(p["tag_f"])}</b></div>
  <article class="card" style="--accent:{cor}" aria-label="Card {i} de {total}: {esc(p["titulo_f"])}">
    <header class="c-head"><span class="c-brand">Arvor · Locais de votação</span><span class="c-pno">{i:02d} / {total:02d}</span></header>
    <div class="c-top">
      <div class="c-tag">{esc(p["tag_f"])}</div>
      <h2>{esc(p["titulo_f"])}</h2>
      <div class="c-metric"><b style="font-size:{_tamanho_metrica(p["metrica_f"])}cqw">{esc(p["metrica_f"])}</b><span>{esc(p["metrica_rot_f"])}</span></div>
    </div>
    <div class="c-viz" tabindex="0" role="region" aria-label="Gráfico do card {i}">{p["svg"]}</div>
    <footer class="c-foot"><span>Fonte: {esc(p["fonte_f"])}</span><b>brasil.arvor.co</b></footer>
  </article>
  <div class="copy" data-copy="{esc(corpo)}"><span class="cc">{len(corpo)} caracteres</span>{esc(corpo)}</div>
  <button class="copy-btn" type="button" onclick="cp(this)">Copiar texto do post {i:02d}</button>
</section>"""


def pagina(posts: list[dict], pngs: list[str]) -> str:
    v = valores()
    total = len(posts)
    cards = "".join(render_card(i + 1, total, p) for i, p in enumerate(posts))
    rail = "".join(f'<a href="#p{i + 1:02d}">{i + 1}</a>' for i in range(total))
    lista = "".join(f'<li><a href="{esc(p)}">{esc(p)}</a></li>' for p in pngs)
    desc = (
        f"{total} cards quadrados com o texto pronto para o X: quatro números oficiais que não "
        f"batem, {v['n_mr']} seções com mudança real de prédio pela nossa conta, o alerta no "
        "Politize sua vizinhança e o que a abstenção a mais faria com os votos."
    )
    return injetar(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITULO)} · Arvor</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{URL}">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#192e2b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="{esc(TITULO)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{OG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:title" content="{esc(TITULO)}">
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
    <a class="back" href="{LAUDO}.html">Abrir o laudo</a>
  </div>
  <h1>Mudança de local de votação entre os turnos. <em>A thread, card a card.</em></h1>
  <p class="deck">Três posts: o problema dos números, a ferramenta para conferir a própria seção e o que a abstenção a mais faria com os votos. Pela nossa conta, {esc(v["n_mr"])} seções e {esc(v["e_mr"])} eleitores trocam de prédio de verdade entre os turnos, e {esc(v["n_fora"])} seções seguem fora do prédio original em {esc(v["dia_2t"])}. O efeito nacional é pequeno; o que falta é transparência.</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado de 1080 por 1080 pixels; os PNGs estão listados no fim da página. Embaixo de cada card está o texto do post, com o botão de copiar. Nenhum número foi digitado à mão: todos saem de mudancas.json, e o gerador recusa texto com algarismo solto, travessão, hashtag ou emoji. O efeito medido é diferença com controles, não efeito causal; os cenários são conta de tamanho, não previsão.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{cards}</main>
<footer class="wrap">
  <h2>Imagens para anexar</h2>
  <p>Os {total} cards em PNG, 1080 por 1080 pixels, na ordem dos posts:</p>
  <ol class="pngs">{lista}</ol>
  <h2>Reprodução</h2>
  <p>python3 scripts/mudancas-secoes-2t-thread.py (com --png para regerar as imagens). Os números vêm de analysis/mudancas_secoes_2t/mudancas.json, gerado por scripts/mudancas-secoes-2t.py. O laudo completo está em <a href="{LAUDO}.html">{LAUDO}.html</a>.</p>
</footer>
<script>{JS}</script>
</body>
</html>
""")
