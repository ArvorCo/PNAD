"""Construtor mínimo de SVG para as figuras dos dossiês da Arvor Intelligence.

Princípio de legibilidade: o viewBox é desenhado na largura real em que a figura
será exibida, de modo que uma unidade do viewBox equivale a um pixel de CSS e os
tamanhos de fonte declarados aqui são os tamanhos que o leitor enxerga. Figuras
espremidas em meia coluna encolhem o texto junto; por isso o padrão é largura
inteira do bloco de leitura.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

INK = "#07111f"
NAVY = "#0b1f36"
BLUE = "#1b54f2"
SKY = "#74a2ff"
RED = "#ef3e36"
CORAL = "#ff8a84"
LIME = "#d9ff43"
OLIVE = "#7e9a12"
AMBER = "#c8811a"
PAPER = "#f2f0e9"
WHITE = "#fffefa"
MUTED = "#687386"
GRAY = "#a8afbb"
LINE = "#d7dae1"

DISPLAY = "Archivo Black, Impact, sans-serif"
SANS = "Inter, system-ui, sans-serif"
MONO = "IBM Plex Mono, ui-monospace, monospace"

FULL = 1180


def _attrs(pairs: dict) -> str:
    out = []
    for key, value in pairs.items():
        if value is None:
            continue
        out.append(f'{key.replace("_", "-")}="{value}"')
    return " ".join(out)


class Canvas:
    """Acumula nós SVG e serializa uma figura responsiva."""

    def __init__(self, width: int = FULL, height: int = 420, aria: str = "") -> None:
        self.width = width
        self.height = height
        self.aria = aria
        self.nodes: list[str] = []
        self.defs: list[str] = []

    def add(self, markup: str) -> None:
        self.nodes.append(markup)

    def define(self, markup: str) -> None:
        self.defs.append(markup)

    def rect(self, x, y, w, h, fill, **kw) -> None:
        self.add(
            f"<rect {_attrs({'x': x, 'y': y, 'width': max(w, 0), 'height': max(h, 0), 'fill': fill, **kw})}/>"
        )

    def line(self, x1, y1, x2, y2, stroke=LINE, width=1, **kw) -> None:
        self.add(
            f"<line {_attrs({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'stroke': stroke, 'stroke_width': width, **kw})}/>"
        )

    def path(self, d, **kw) -> None:
        self.add(f"<path {_attrs({'d': d, **kw})}/>")

    def circle(self, cx, cy, r, fill, **kw) -> None:
        self.add(
            f"<circle {_attrs({'cx': cx, 'cy': cy, 'r': r, 'fill': fill, **kw})}/>"
        )

    def text(
        self,
        x,
        y,
        value,
        size=15,
        fill=INK,
        family=SANS,
        weight=None,
        anchor="start",
        **kw,
    ) -> None:
        payload = escape(str(value))
        self.add(
            f"<text {_attrs({'x': x, 'y': y, 'font-size': size, 'fill': fill, 'font-family': family, 'font-weight': weight, 'text-anchor': anchor, **kw})}>{payload}</text>"
        )

    def label(self, x, y, value, **kw) -> None:
        """Rótulo de eixo: monoespaçado, discreto, legível."""
        self.text(
            x,
            y,
            value,
            size=kw.pop("size", 13),
            fill=kw.pop("fill", MUTED),
            family=MONO,
            **kw,
        )

    def number(self, x, y, value, size=34, fill=INK, **kw) -> None:
        """Número-monstro: a informação que o leitor leva mesmo sem ler o resto."""
        self.text(x, y, value, size=size, fill=fill, family=DISPLAY, **kw)

    def hatch(self, ident: str, color: str, opacity: float = 0.22) -> str:
        """Trama de 45 graus: a marca visual do que é inferência, não medição."""
        self.define(
            f'<pattern id="{ident}" width="7" height="7" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><rect width="7" height="7" fill="{color}" '
            f'opacity="{opacity}"/><line x1="0" y1="0" x2="0" y2="7" stroke="{color}" '
            f'stroke-width="2.6" opacity="0.8"/></pattern>'
        )
        return f"url(#{ident})"

    def render(self) -> str:
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        role = f' role="img" aria-label="{escape(self.aria)}"' if self.aria else ""
        return (
            f'<svg viewBox="0 0 {self.width} {self.height}" '
            f'xmlns="http://www.w3.org/2000/svg"{role}>{defs}{"".join(self.nodes)}</svg>'
        )


def br(value: float, casas: int = 1) -> str:
    """Formata número no padrão brasileiro, com sinal explícito quando pedido."""
    texto = f"{value:,.{casas}f}"
    return texto.replace(",", " ").replace(".", ",").replace(" ", ".")


def signed(value: float, casas: int = 1) -> str:
    return ("+" if value > 0 else "−" if value < 0 else "") + br(abs(value), casas)


def write_fragments(path, figures: dict[str, str]) -> None:
    """Grava as figuras como um dicionário de fragmentos SVG injetáveis no HTML."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(figures, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def inject(html_path, figures: dict[str, str]) -> int:
    """Substitui o conteúdo entre marcadores <!--FIG:nome--> e <!--/FIG:nome-->."""
    import re

    html = html_path.read_text(encoding="utf-8")
    count = 0
    for name, markup in figures.items():
        pattern = re.compile(
            rf"(<!--FIG:{re.escape(name)}-->).*?(<!--/FIG:{re.escape(name)}-->)",
            re.DOTALL,
        )
        html, hits = pattern.subn(
            lambda m, markup=markup: m.group(1) + markup + m.group(2), html
        )
        count += hits
    html_path.write_text(html, encoding="utf-8")
    return count
