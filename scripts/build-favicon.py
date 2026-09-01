#!/usr/bin/env python3
"""Gera o favicon do brasil.arvor.co: a bandeira nacional simplificada.

A bandeira inteira é ilegível em 16 px — a esfera azul vira um borrão e as
estrelas somem. O ícone aqui preserva só o que ainda se lê nesse tamanho:
campo verde, losango amarelo, círculo azul e a faixa branca. As cores são as
oficiais da Lei nº 5.700/1971 na conversão usual para tela.

Uso:
  python3 scripts/build-favicon.py

Saídas:
  docs/img/favicon.svg          vetor, usado pelos navegadores modernos
  docs/img/favicon-32.png       fallback bitmap
  docs/img/favicon-180.png      apple-touch-icon
  docs/favicon.ico              16/32/48 px, para o pedido automático da raiz
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw
from PIL.Image import Resampling

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG = DOCS / "img"

VERDE = "#009B3A"
AMARELO = "#FEDF00"
AZUL = "#002776"
BRANCO = "#FFFFFF"

# Frações do lado do ícone. O losango encosta perto das bordas porque, em
# tamanho pequeno, margem grande faz o amarelo desaparecer.
MARGEM = 0.085
RAIO_ESFERA = 0.245
FAIXA = 0.072

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Bandeira do Brasil">
  <defs><clipPath id="esfera"><circle cx="32" cy="32" r="{raio}"/></clipPath></defs>
  <rect width="64" height="64" rx="9" fill="{verde}"/>
  <path d="M32 {m} L{r} 32 L32 {b} L{l} 32 Z" fill="{amarelo}"/>
  <circle cx="32" cy="32" r="{raio}" fill="{azul}"/>
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{branco}" stroke-width="{faixa}" clip-path="url(#esfera)"/>
</svg>
"""


def build_svg() -> str:
    """Mesma construção do bitmap: a faixa é uma corda grossa recortada pela esfera."""
    size = 64.0
    margem = MARGEM * size
    raio = RAIO_ESFERA * size
    return SVG.format(
        verde=VERDE,
        amarelo=AMARELO,
        azul=AZUL,
        branco=BRANCO,
        m=round(margem, 2),
        b=round(size - margem, 2),
        l=round(margem, 2),
        r=round(size - margem, 2),
        raio=round(raio, 2),
        faixa=round(FAIXA * size, 2),
        x1=round(32 - raio, 2),
        y1=round(32 + raio * 0.36, 2),
        x2=round(32 + raio, 2),
        y2=round(32 - raio * 0.36, 2),
    )


def draw_png(size: int) -> Image.Image:
    """Desenha em 8× e reduz, porque o losango só fica limpo com antialias."""
    scale = 8
    side = size * scale
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    radius = int(side * 0.14)
    draw.rounded_rectangle([0, 0, side - 1, side - 1], radius=radius, fill=VERDE)

    margem = MARGEM * side
    draw.polygon(
        [
            (side / 2, margem),
            (side - margem, side / 2),
            (side / 2, side - margem),
            (margem, side / 2),
        ],
        fill=AMARELO,
    )

    raio = RAIO_ESFERA * side
    centro = side / 2
    draw.ellipse(
        [centro - raio, centro - raio, centro + raio, centro + raio], fill=AZUL
    )

    # Faixa branca: uma corda espessa sobre a esfera, recortada pelo círculo.
    faixa = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    faixa_draw = ImageDraw.Draw(faixa)
    espessura = int(FAIXA * side)
    faixa_draw.line(
        [
            (centro - raio, centro + raio * 0.36),
            (centro + raio, centro - raio * 0.36),
        ],
        fill=BRANCO,
        width=espessura,
    )
    mascara = Image.new("L", (side, side), 0)
    ImageDraw.Draw(mascara).ellipse(
        [centro - raio, centro - raio, centro + raio, centro + raio], fill=255
    )
    image.paste(faixa, (0, 0), Image.composite(faixa.split()[3], mascara, mascara))

    return image.resize((size, size), Resampling.LANCZOS)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    (IMG / "favicon.svg").write_text(build_svg(), encoding="utf-8")

    for size in (32, 180):
        draw_png(size).save(IMG / f"favicon-{size}.png", optimize=True)

    icons = [draw_png(s) for s in (48, 32, 16)]
    icons[0].save(
        DOCS / "favicon.ico",
        format="ICO",
        sizes=[(48, 48), (32, 32), (16, 16)],
        append_images=icons[1:],
    )

    print(f"OK: {(IMG / 'favicon.svg').relative_to(ROOT)}")
    print(f"OK: {(IMG / 'favicon-32.png').relative_to(ROOT)}")
    print(f"OK: {(IMG / 'favicon-180.png').relative_to(ROOT)}")
    print(f"OK: {(DOCS / 'favicon.ico').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
