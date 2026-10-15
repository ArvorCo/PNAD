#!/usr/bin/env python3
"""Card de compartilhamento dos logs, com números do mesmo índice publicado."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def gerar():
    d = json.loads((ROOT / "docs/assets/logs_urnas_2026/indice.json").read_text())
    c = d["cobertura"]
    n = len(d["criterios"])

    def br(x):
        return f"{x:,}".replace(",", ".")

    status = (
        "Cobertura em andamento"
        if not d["concluido"]
        else "Primeiro turno · 4 de outubro de 2026"
    )
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Card · Logs das urnas</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;700&amp;family=IBM+Plex+Sans:wght@400;600;700&amp;family=IBM+Plex+Mono:wght@500;600&amp;display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}}body{{margin:0;width:1200px;height:630px;background:#f4f1e8;color:#182e34;font-family:'IBM Plex Sans',sans-serif}}
.card{{height:630px;padding:42px 54px;display:flex;flex-direction:column;justify-content:space-between;border-top:10px solid #216577}}
header,footer{{display:flex;align-items:center;justify-content:space-between;gap:30px}}header{{font-size:17px;letter-spacing:.035em}}.brand{{display:flex;align-items:center;gap:10px;font-weight:700}}.brand img{{width:32px;height:32px}}
.middle{{display:grid;grid-template-columns:3fr 2fr;align-items:center;gap:36px}}h1{{font-family:'Fraunces',serif;font-size:65px;line-height:1.03;letter-spacing:-.035em;margin:16px 0}}h1 em{{font-style:normal;color:#216577}}.intro{{font-size:22px;line-height:1.4;max-width:600px;margin:14px 0}}
.sequence{{border-left:1px solid #b7c4c4;padding-left:36px}}.sequence p{{font-size:21px;margin:16px 0;padding-bottom:16px;border-bottom:1px solid #b7c4c4}}.sequence b{{color:#216577;font:500 30px 'IBM Plex Mono',monospace;margin-right:12px}}.sequence small{{display:block;margin:7px 0 0 58px;font-size:16px;color:#485d62}}
.stats{{display:flex;gap:38px;border-top:1px solid #182e34;padding-top:18px}}.stats b{{display:block;font:500 39px 'IBM Plex Mono',monospace}}.stats span{{display:block;font-size:15px;margin-top:5px;color:#485d62}}footer{{font-size:15px;color:#485d62}}footer strong{{color:#216577}}
</style></head><body><div class="card">
<header><span class="brand"><img src="../../img/arvor_logo.png" alt="">Arvor Intelligence</span><span>{status}</span></header>
<div class="middle"><div><h1>O ritmo da votação.<br><em>O registro das urnas.</em></h1><p class="intro">Processo do mesário ao cômputo, cadência e ocorrências. Brasil e exterior, com cobertura e limites explícitos.</p></div>
<div class="sequence"><p><b>01</b>Processo completo<small>Do identificador ao cômputo</small></p><p><b>02</b>Cadência<small>Intervalos e trechos rápidos</small></p><p><b>03</b>Conferência<small>Ocorrências, logs e boletins</small></p></div></div>
<div class="stats"><div><b>{br(c["lidos"])}</b><span>logs lidos</span></div><div><b>{br(c["contagem_confere"])}</b><span>contagens reconciliadas com o BU</span></div><div><b>+{n}</b><span>diagnósticos operacionais</span></div></div>
<footer><span>Diagnóstico não é prova de irregularidade.</span><strong>brasil.arvor.co</strong></footer>
</div></body></html>"""
    fonte = ROOT / "docs/assets/og/logs_urnas_2026.html"
    destino = ROOT / "docs/img/og/logs_urnas_2026.png"
    fonte.write_text(html, encoding="utf-8")
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1200, "height": 630}, device_scale_factor=1
        )
        page.goto(fonte.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        assert page.evaluate("document.documentElement.scrollHeight <= 630")
        page.screenshot(path=str(destino))
        browser.close()
    print(destino)


if __name__ == "__main__":
    gerar()
