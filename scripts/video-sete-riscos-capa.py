#!/usr/bin/env python3
"""Capas (thumbnails) do vídeo "Sete riscos, um fiscal", 16:9 e 9:16.

Compõe HTML com a marca da casa sobre a imagem da escola ao amanhecer
(`video/sete_riscos/public/midia/rua_escola_amanhecer_still_<fmt>.png`) e renderiza PNG com
Playwright. Fontes ficam em `video/sete_riscos/capa/capa_<fmt>.html`; saídas em
`video/sete_riscos/out/capa_<fmt>.png`. Uso:

  python3 scripts/video-sete-riscos-capa.py            # as duas capas
  python3 scripts/video-sete-riscos-capa.py --so 9x16  # uma só
"""

from __future__ import annotations

import argparse
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "sete_riscos"
CAPA = VIDEO / "capa"
SAIDA = VIDEO / "out"
LOGO = ROOT / "docs" / "img" / "arvor_logo.png"

FORMATOS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}

# Imagem de fundo (`public/midia/<FUNDO>_<fmt>.png`) e nome da capa no <title>; os vídeos irmãos trocam.
FUNDO = "rua_escola_amanhecer_still"
NOME_CAPA = "sete riscos"

TITULO = ("Sete riscos, ", "um fiscal", "")
SUBTITULO = "Boca de urna, compra de voto, transporte, medo, mesário, pianista e totalização: o que a lei deixa você fazer no dia 25"
KICKER = "GUIA DO FISCAL · 2º TURNO 2026"
CHIPS = ("10 min", "2º turno · 25/10", "brasil.arvor.co")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap');
:root { --fundo:#060b1a; --tinta:#eef2ff; --suave:#9aa6c4; --teal:#2a9ab0; --tealc:#5fd3e6; --ouro:#f0c86b; }
* { box-sizing:border-box; margin:0; padding:0; }
html, body { width:__W__px; height:__H__px; overflow:hidden; background:var(--fundo); }
body { font-family:'Space Grotesk', system-ui, sans-serif; color:var(--tinta); position:relative; }
.foto { position:absolute; inset:0; background:url('__FOTO__') center/cover no-repeat; }
.veu { position:absolute; inset:0; background:__VEU__; }
.grade { position:absolute; inset:0; opacity:.14;
  background-image:linear-gradient(rgba(95,211,230,.35) 1px, transparent 1px), linear-gradient(90deg, rgba(95,211,230,.35) 1px, transparent 1px);
  background-size:80px 80px; mask-image:linear-gradient(__MASK__); -webkit-mask-image:linear-gradient(__MASK__); }
.canto { position:absolute; width:56px; height:56px; border:3px solid var(--tealc); opacity:.9; }
.canto.a { left:44px; top:44px; border-right:0; border-bottom:0; }
.canto.b { right:44px; top:44px; border-left:0; border-bottom:0; }
.canto.c { left:44px; bottom:44px; border-right:0; border-top:0; }
.canto.d { right:44px; bottom:44px; border-left:0; border-top:0; }
.marca { position:absolute; left:96px; top:84px; display:flex; align-items:center; gap:18px; }
.marca img { width:60px; height:60px; filter:brightness(0) invert(1); }
.marca b { display:block; font-size:30px; letter-spacing:.18em; line-height:1; }
.marca small { display:block; font-family:'JetBrains Mono', monospace; font-size:15px; letter-spacing:.32em; color:var(--tealc); margin-top:6px; }
.bloco { position:absolute; left:96px; right:96px; }
.kicker { display:inline-block; font-family:'JetBrains Mono', monospace; font-weight:700; font-size:__KICK__px; letter-spacing:.22em;
  color:#06121c; background:var(--ouro); padding:12px 20px; border-radius:8px; }
h1 { font-weight:700; font-size:__H1__px; line-height:.98; letter-spacing:-.02em; margin-top:34px; max-width:__H1W__px;
  text-shadow:0 6px 40px rgba(0,0,0,.6); }
h1 em { font-style:normal; color:var(--ouro); white-space:nowrap; }
p.sub { font-weight:500; font-size:__SUB__px; line-height:1.22; color:var(--tinta); margin-top:30px; max-width:__SUBW__px;
  text-shadow:0 4px 24px rgba(0,0,0,.7); }
.chips { display:flex; gap:14px; margin-top:__CHIPT__px; flex-wrap:wrap; }
.chips span { font-family:'JetBrains Mono', monospace; font-weight:700; font-size:__CHIP__px; letter-spacing:.08em;
  padding:12px 18px; border:2px solid rgba(95,211,230,.7); border-radius:999px; color:var(--tinta);
  background:rgba(6,11,26,.6); backdrop-filter:blur(6px); }
.chips span.t { background:var(--teal); border-color:var(--teal); color:#041018; }
.faixa { position:absolute; left:0; right:0; bottom:0; height:12px;
  background:linear-gradient(90deg, var(--tealc), var(--ouro) 40%, #4f8ff0 70%, #ea6a5c); }
"""

HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Capa __NOME__ __FMT__</title>
<style>__CSS__</style></head>
<body>
<div class="foto"></div><div class="veu"></div><div class="grade"></div>
<i class="canto a"></i><i class="canto b"></i><i class="canto c"></i><i class="canto d"></i>
<div class="marca"><img src="__LOGO__" alt=""><div><b>ARVOR</b><small>INTELLIGENCE</small></div></div>
<div class="bloco" style="__BLOCO__">
  <span class="kicker">__KICKER__</span>
  <h1>__T1__<em>__T2__</em>__T3__</h1>
  <p class="sub">__SUB__</p>
  <div class="chips"><span class="t">__C1__</span><span>__C2__</span><span>__C3__</span></div>
</div>
<div class="faixa"></div>
</body></html>
"""

AJUSTES = {
    "16x9": {
        "VEU": "linear-gradient(90deg, rgba(6,11,26,.96) 0%, rgba(6,11,26,.86) 38%, rgba(6,11,26,.35) 62%, rgba(6,11,26,.12) 100%)",
        "MASK": "90deg, #000 0%, transparent 55%",
        "BLOCO": "top:250px;",
        "KICK": 24,
        "H1": 150,
        "H1W": 1080,
        "SUB": 42,
        "SUBW": 900,
        "CHIP": 24,
        "CHIPT": 44,
    },
    "9x16": {
        "VEU": "linear-gradient(180deg, rgba(6,11,26,.55) 0%, rgba(6,11,26,.15) 28%, rgba(6,11,26,.55) 50%, rgba(6,11,26,.97) 72%, rgba(6,11,26,1) 100%)",
        "MASK": "180deg, transparent 45%, #000 100%",
        "BLOCO": "top:960px;",
        "KICK": 24,
        "H1": 136,
        "H1W": 900,
        "SUB": 44,
        "SUBW": 900,
        "CHIP": 24,
        "CHIPT": 40,
    },
}


def _dados_uri(caminho: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(caminho.read_bytes()).decode()}"


def fonte_html(fmt: str) -> str:
    largura, altura = FORMATOS[fmt]
    foto = VIDEO / "public" / "midia" / f"{FUNDO}_{fmt}.png"
    if not foto.exists():
        raise SystemExit(f"falta a imagem de fundo {foto}")
    aj = AJUSTES[fmt]
    css = CSS.replace("__W__", str(largura)).replace("__H__", str(altura))
    css = css.replace("__FOTO__", _dados_uri(foto, "image/png"))
    for chave, valor in aj.items():
        css = css.replace(f"__{chave}__", str(valor))
    html = (
        HTML.replace("__CSS__", css)
        .replace("__FMT__", fmt)
        .replace("__NOME__", NOME_CAPA)
    )
    html = html.replace("__LOGO__", _dados_uri(LOGO, "image/png"))
    html = html.replace("__BLOCO__", aj["BLOCO"]).replace("__KICKER__", KICKER)
    html = (
        html.replace("__T1__", TITULO[0])
        .replace("__T2__", TITULO[1])
        .replace("__T3__", TITULO[2])
    )
    html = html.replace("__SUB__", SUBTITULO)
    for i, chip in enumerate(CHIPS, start=1):
        html = html.replace(f"__C{i}__", chip)
    return html


def renderizar(fmt: str) -> Path:
    largura, altura = FORMATOS[fmt]
    CAPA.mkdir(parents=True, exist_ok=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    origem = CAPA / f"capa_{fmt}.html"
    origem.write_text(fonte_html(fmt), encoding="utf-8")
    destino = SAIDA / f"capa_{fmt}.png"
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(
            viewport={"width": largura, "height": altura}, device_scale_factor=1
        )
        pagina.goto(origem.as_uri())
        pagina.wait_for_function("document.fonts.ready.then(() => true)")
        pagina.wait_for_timeout(600)
        pagina.screenshot(path=str(destino), full_page=False)
        navegador.close()
    return destino


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--so", choices=sorted(FORMATOS), help="renderiza só um formato"
    )
    args = parser.parse_args(argv)
    for fmt in [args.so] if args.so else sorted(FORMATOS):
        destino = renderizar(fmt)
        print(f"capa {fmt}: {destino} ({destino.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
