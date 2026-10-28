#!/usr/bin/env python3
"""Gera todos os social cards do acervo a partir de um manifesto único.

Antes existiam três convenções ao mesmo tempo: uma galeria com ramificação por
query string (docs/social.html?card=...), fontes soltas em docs/assets/og_*.html
e imagens espalhadas em três padrões de caminho, com metade das páginas sem card
nenhum. Este script substitui as três.

    python3 scripts/social-cards.py            gera HTML e renderiza os PNG
    python3 scripts/social-cards.py --html     só regrava o HTML de cada card
    python3 scripts/social-cards.py --only pnad proposta

Saída: docs/assets/og/<slug>.html (fonte) e docs/img/og/<slug>.png (1200x630).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from html import escape
from pathlib import Path

from social_cards_manifesto import CARDS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE_DIR = DOCS / "assets/og"
IMAGE_DIR = DOCS / "img/og"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8799

ACCENTS = {
    "lime": "#d9ff43",
    "blue": "#74a2ff",
    "red": "#ef3e36",
    "amber": "#e8a33d",
}

# Cada card: título curto, uma linha de leitura e até três números que o dossiê
# sustenta. Os textos vêm das fichas revisadas do acervo em docs/index.html.


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Social card · {slug}</title>
<!-- Gerado por scripts/social-cards.py. Não edite à mão: edite o manifesto. -->
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{width:1200px;height:630px;overflow:hidden;background:#07111f;color:#fffefa;font-family:Inter,system-ui,sans-serif}}
  .card{{position:relative;width:1200px;height:630px;display:grid;grid-template-columns:{columns};overflow:hidden}}
  .card::before{{content:"";position:absolute;inset:0;z-index:0;
    background:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px) 0 0/68px 68px,
               linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px) 0 0/68px 68px;
    -webkit-mask-image:linear-gradient(140deg,#000,transparent 78%)}}
  .left{{position:relative;z-index:2;padding:46px 40px 38px 56px;display:flex;flex-direction:column;justify-content:space-between}}
  .eyebrow{{display:inline-flex;align-items:center;gap:11px;align-self:flex-start;padding:8px 17px;
    border:1px solid rgba(255,255,255,.26);font-family:"IBM Plex Mono",monospace;font-size:15px;
    letter-spacing:.11em;text-transform:uppercase;color:{accent}}}
  .eyebrow i{{width:9px;height:9px;background:{accent};display:block}}
  h1{{font-family:"Archivo Black",sans-serif;font-size:{title_size}px;line-height:.9;letter-spacing:-.03em;
    margin:24px 0 0;text-transform:uppercase}}
  h1 em{{font-style:normal;color:{accent};display:block}}
  .lede{{font-size:21px;line-height:1.36;color:#c3cddd;max-width:{lede_width}px;margin-top:18px}}
  .lede b{{color:#fffefa}}
  .stats{{display:flex;gap:34px}}
  .stats b{{font-family:"Archivo Black",sans-serif;font-size:34px;letter-spacing:-.02em;line-height:1;display:block}}
  .stats span{{display:block;margin-top:6px;font-family:"IBM Plex Mono",monospace;font-size:13px;
    letter-spacing:.07em;text-transform:uppercase;color:#8a95a8}}
  .s0 b{{color:{accent}}}.s1 b{{color:#74a2ff}}.s2 b{{color:#ef3e36}}
  .foot{{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:22px;padding-top:15px;
    border-top:1px solid rgba(255,255,255,.2);font-family:"IBM Plex Mono",monospace;font-size:14.5px;color:#8a95a8}}
  .foot b{{color:{accent}}}
  .right{{position:relative;z-index:1;height:630px;border-left:1px solid rgba(255,255,255,.16);overflow:hidden}}
  .right img{{width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.18) brightness(.7)}}
  .right.logo{{background:#fff;display:grid;place-items:center}}
  .right.logo img{{width:72%;height:auto;object-fit:contain;filter:none}}
  .right::after{{content:"";position:absolute;inset:0;background:{accent};opacity:.2;mix-blend-mode:color}}
  .duo{{display:grid;grid-template-rows:315px 315px}}
  .duo figure{{position:relative;height:315px;overflow:hidden}}
  .duo img{{filter:grayscale(.55) contrast(1.1) brightness(.82)}}
  .duo .l::after{{content:"";position:absolute;inset:0;background:#ef3e36;opacity:.34;mix-blend-mode:multiply}}
  .duo .f::after{{content:"";position:absolute;inset:0;background:#1b54f2;opacity:.34;mix-blend-mode:multiply}}
  .duo figcaption{{position:absolute;left:0;right:0;bottom:0;z-index:3;padding:40px 18px 18px;
    background:linear-gradient(transparent,rgba(0,0,0,.88));font-family:"IBM Plex Mono",monospace;
    font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#e7e3d8}}
  .duo figcaption b{{display:block;font-family:"Archivo Black",sans-serif;font-size:34px;letter-spacing:-.02em;color:#fff}}
  .bg{{position:absolute;inset:0;z-index:0}}
  .bg img{{width:100%;height:100%;object-fit:cover;object-position:center 40%}}
  .bg::after{{content:"";position:absolute;inset:0;
    background:linear-gradient(100deg,rgba(7,17,31,.93) 0%,rgba(7,17,31,.8) 44%,rgba(7,17,31,.18) 100%),
               linear-gradient(0deg,rgba(7,17,31,.9) 0%,rgba(7,17,31,0) 44%)}}
  .card.com-fundo::before{{opacity:.6}}
  .tag{{position:absolute;top:0;right:0;z-index:4;padding:10px 20px;background:{accent};color:#07111f;
    font-family:"IBM Plex Mono",monospace;font-size:14px;font-weight:600;letter-spacing:.14em;text-transform:uppercase}}
</style>
</head>
<body>
  <div class="card{card_class}">{tag}
    <div class="left">
      <div>
        <span class="eyebrow"><i></i>{eyebrow}</span>
        <h1>{title}{title_em}</h1>
        <p class="lede">{lede}</p>
      </div>
      <div>
        <div class="stats">{stats}</div>
        <div class="foot"><span>{foot}</span><span><b>brasil.arvor.co</b></span></div>
      </div>
    </div>{right}
  </div>
</body>
</html>
"""

DUO_PANEL = """
    <div class="right duo">
      <figure class="l"><img src="../../img/atlas_072026/web/lula.jpg" alt=""><figcaption>Lula<b>{left_value}</b></figcaption></figure>
      <figure class="f"><img src="../../img/atlas_072026/web/flavio.jpg" style="object-position:center 18%" alt=""><figcaption>Flávio<b>{right_value}</b></figcaption></figure>
    </div>"""


def render_card(card: dict) -> str:
    accent = ACCENTS[card.get("accent", "lime")]
    has_panel = bool(card.get("photo") or card.get("duo") or card.get("logo"))
    stats = "".join(
        f'<div class="s{i}"><b>{escape(value)}</b><span>{escape(label)}</span></div>'
        for i, (value, label) in enumerate(card.get("stats", []))
    )
    if card.get("bg"):
        right = f'\n    <div class="bg"><img src="../../{card["bg"]}" alt=""></div>'
    elif card.get("duo"):
        values = card.get("duo_values", ("41", "37"))
        right = DUO_PANEL.format(left_value=values[0], right_value=values[1])
    elif card.get("photo"):
        right = (
            f'\n    <div class="right"><img src="../../{card["photo"]}" alt=""></div>'
        )
    elif card.get("logo"):
        right = '\n    <div class="right logo"><img src="../../img/arvor_logo_text.png" alt="Arvor"></div>'
    else:
        right = ""
    title = escape(card["title"])
    title_em = f"<em>{escape(card['title_em'])}</em>" if card.get("title_em") else ""
    longest = max(len(card["title"]), len(card.get("title_em", "")))
    title_size = 68 if longest <= 20 else 58 if longest <= 26 else 50
    tag = '\n    <span class="tag">Thread</span>' if card.get("thread") else ""
    return TEMPLATE.format(
        slug=card["slug"],
        accent=accent,
        columns="1fr 392px" if has_panel else "1fr",
        lede_width=620 if has_panel else 740 if card.get("bg") else 900,
        card_class=" com-fundo" if card.get("bg") else "",
        title_size=title_size,
        eyebrow=escape(card["eyebrow"]),
        title=title,
        title_em=title_em,
        lede=card["lede"],
        stats=stats,
        foot=escape(card["foot"]),
        right=right,
        tag=tag,
    )


def write_sources(cards: list[dict]) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for card in cards:
        (SOURCE_DIR / f"{card['slug']}.html").write_text(
            render_card(card), encoding="utf-8"
        )


def shoot(cards: list[dict]) -> list[str]:
    if not Path(CHROME).exists():
        sys.exit(f"Chrome não encontrado em {CHROME}")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=DOCS,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    done = []
    try:
        time.sleep(1.5)
        for card in cards:
            slug = card["slug"]
            target = IMAGE_DIR / f"{slug}.png"
            subprocess.run(
                [
                    CHROME,
                    "--headless",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--window-size=1200,630",
                    "--virtual-time-budget=8000",
                    f"--screenshot={target}",
                    f"http://localhost:{PORT}/assets/og/{slug}.html",
                ],
                check=True,
                capture_output=True,
            )
            done.append(slug)
    finally:
        server.terminate()
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", action="store_true", help="só regrava as fontes HTML")
    parser.add_argument("--only", nargs="*", help="gera apenas estes slugs")
    args = parser.parse_args()

    cards = CARDS
    if args.only:
        wanted = set(args.only)
        cards = [card for card in CARDS if card["slug"] in wanted]
        missing = wanted - {card["slug"] for card in cards}
        if missing:
            sys.exit(f"slug desconhecido: {sorted(missing)}")

    write_sources(cards)
    report = {"cards": len(cards), "fontes": str(SOURCE_DIR)}
    if not args.html:
        report["renderizados"] = len(shoot(cards))
        report["imagens"] = str(IMAGE_DIR)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    if shutil.which("python3") is None:
        sys.exit("python3 não encontrado")
    main()
