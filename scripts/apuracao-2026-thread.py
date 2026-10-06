#!/usr/bin/env python3
"""Gera docs/apuracao_1o_turno_2026_thread.html: a super thread do dossiê da apuração.

Vinte e poucos cards 1:1 (largura de trabalho de 1080 px) com gráfico SVG desenhado
em Python a partir de analysis/apuracao_2026/dados/, e o texto de cada post, de
2.000 a 2.700 caracteres, pronto para copiar. Falha se algum post sair da faixa,
se houver travessão, hashtag, emoji ou palavra vetada, ou se algum algarismo dos
modelos de texto não vier de um campo preenchido pelos dados.

Reprodução:
    python3 scripts/apuracao-2026-thread.py          gera a página
    python3 scripts/apuracao-2026-thread.py --png    também renderiza os PNGs 1080x1080
"""

from __future__ import annotations

import argparse
import sys

from apuracao_2026.thread_base import PNG_DIR, ROOT, SLUG
from apuracao_2026.thread_build import caminhos_png, montar, valores, verificar
from apuracao_2026.thread_pagina import pagina

SAIDA = ROOT / "docs" / f"{SLUG}.html"


def renderizar_png(n: int) -> None:
    from playwright.sync_api import sync_playwright

    PNG_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(
            viewport={"width": 1200, "height": 1300}, device_scale_factor=1
        )
        pg.goto(SAIDA.as_uri(), wait_until="networkidle")
        pg.add_style_tag(
            content=".rail{display:none!important}"
            ".card{width:1080px!important;height:1080px!important;max-width:none!important;"
            "aspect-ratio:auto!important;border-radius:0!important;border:0!important}"
        )
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(800)
        for i in range(1, n + 1):
            card = pg.locator(f"#p{i:02d} .card")
            topo = card.evaluate(
                "el => Math.round(el.getBoundingClientRect().top + window.scrollY)"
            )
            pg.evaluate(f"window.scrollTo(0, {topo} - 40)")
            caixa = card.bounding_box()
            pg.screenshot(
                path=str(PNG_DIR / f"{i:02d}.png"),
                clip={
                    "x": round(caixa["x"]),
                    "y": round(caixa["y"]),
                    "width": 1080,
                    "height": 1080,
                },
            )
        nav.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--png", action="store_true", help="renderiza os cards em PNG")
    args = ap.parse_args()
    posts = montar()
    erros = verificar(posts)
    for i, post in enumerate(posts, 1):
        print(f"{i:02d} {len(post['corpo']):5d}  {post['tag_f']}")
    if erros:
        print("\n".join(erros), file=sys.stderr)
        sys.exit(1)
    html = pagina(posts, caminhos_png(len(posts)), valores())
    if "—" in html or "–" in html:
        sys.exit("travessão ou meia-risca na página")
    SAIDA.write_text(html, encoding="utf-8")
    print(SAIDA, len(posts), "cards")
    if args.png:
        renderizar_png(len(posts))
        print(PNG_DIR, "PNGs gerados")


if __name__ == "__main__":
    main()
