"""Base da super thread da apuração: dados, formato pt-BR, paleta e primitivas SVG.

Todo número que aparece num card ou num post sai daqui, formatado a partir dos
JSONs de ``analysis/apuracao_2026/dados/``. Os textos dos posts são modelos com
campos ``{nome}``; ``digitos_soltos`` acusa qualquer algarismo escrito à mão.
"""

from __future__ import annotations

import json
import re
from functools import cache
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2026/dados"
MEMOS = ROOT / "analysis/apuracao_2026"
SLUG = "apuracao_1o_turno_2026_thread"
DOSSIE = "apuracao_1o_turno_2026"
URL = f"https://brasil.arvor.co/{SLUG}.html"
OG = f"https://brasil.arvor.co/img/og/{SLUG}.png"
PNG_DIR = ROOT / "docs/img/apuracao_2026/thread"

PAPER = "#f4f0e6"
PAPER2 = "#ebe5d6"
INK = "#192e2b"
MUTED = "#535b54"
GRID = "#d6cfbd"
LULA = "#b02f21"
FLAVIO = "#1457aa"
OUTROS = "#0f7f5f"
CINZA = "#5f6773"
GOLD = "#7d5b00"
GOLD_FILL = "#c9a43a"
WHITE = "#ffffff"
CAMPO = {
    "esquerda": "#b02f21",
    "centro-esquerda": "#d9775f",
    "centro": "#8a7a3a",
    "centro-direita": "#4f7fc2",
    "direita": "#1457aa",
}
CAMPOS = list(CAMPO)
ROT_CAMPO = {
    "esquerda": "Esquerda",
    "centro-esquerda": "Centro-esquerda",
    "centro": "Centro",
    "centro-direita": "Centro-direita",
    "direita": "Direita",
}
REGIOES5 = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
COR_REGIAO = {
    "Norte": "#0f7f5f",
    "Nordeste": "#b02f21",
    "Centro-Oeste": "#7d5b00",
    "Sudeste": "#1457aa",
    "Sul": "#5f6773",
    "Exterior": "#8a7a3a",
}

SANS = "IBM Plex Sans Condensed, Arial, sans-serif"
MONO = "IBM Plex Mono, monospace"
DISPLAY = "Fraunces, Georgia, serif"

W, H = 1000, 600


@cache
def dado(nome: str):
    """Lê um JSON de ``dados/`` (ou um caminho relativo à raiz, se tiver barra)."""
    caminho = ROOT / nome if "/" in nome else DADOS / f"{nome}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def tabela(bloco: dict) -> list[dict]:
    """Converte ``{"colunas": [...], "linhas": [[...]]}`` em lista de dicionários."""
    cols = bloco["colunas"]
    return [dict(zip(cols, linha, strict=True)) for linha in bloco["linhas"]]


# ------------------------------------------------------------------ formato


def num(v: float, casas: int = 0) -> str:
    s = f"{v:,.{casas}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(v: float, casas: int = 2) -> str:
    return f"{num(v, casas)}%"


def sinal(v: float, casas: int = 2) -> str:
    v = round(v, casas)
    if v == 0:
        v = 0.0
    if v > 0:
        return "+" + num(v, casas)
    if v < 0:
        return "−" + num(-v, casas)
    return num(v, casas)


def mi(v: float, casas: int = 2) -> str:
    """Milhões por extenso: 2,22 milhões; abaixo de um milhão, mil."""
    a = abs(v)
    if a >= 1_000_000:
        x = num(a / 1e6, casas)
        unidade = "milhão" if x.startswith("1,") and a < 2_000_000 else "milhões"
        return f"{'−' if v < 0 else ''}{x} {unidade}"
    return f"{'−' if v < 0 else ''}{num(a / 1e3, 0)} mil"


def mi_curto(v: float, casas: int = 2) -> str:
    a = abs(v)
    s = "−" if v < 0 else ""
    if a >= 1_000_000:
        return f"{s}{num(a / 1e6, casas)} mi"
    return f"{s}{num(a / 1e3, 0)} mil"


def hora(s: str) -> str:
    """'2026-10-04 18:10:48' ou '18:10:48' vira '18:10'."""
    return s.split(" ")[-1][:5]


def hora_seg(s: str) -> str:
    return s.split(" ")[-1][:8]


def nome_proprio(s: str) -> str:
    minusc = {"de", "da", "do", "das", "dos", "e"}
    partes = []
    for i, p in enumerate(s.lower().split()):
        partes.append(p if (i and p in minusc) else p[:1].upper() + p[1:])
    return " ".join(partes)


# ------------------------------------------------------------------ verificação

PLACEHOLDER = re.compile(r"\{[a-z_][a-z0-9_]*\}")
PERMITIDOS = re.compile(
    r"\b[12]º|\b(?:2018|2020|2022|2026|2027)\b|brasil\.arvor\.co|SHA-256|[a-z0-9_]+\.json"
)
PROIBIDOS = {
    "travessão": "—",
    "meia-risca": "–",
    "hashtag": "#",
}
EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿⬀-⯿️]")
PALAVRAS_PROIBIDAS = ("comunista", "ladrão", "ladrao", "venezuela")


def digitos_soltos(modelo: str) -> list[str]:
    """Algarismos do modelo fora dos campos ``{...}`` e da lista de permitidos."""
    limpo = PLACEHOLDER.sub("", modelo)
    limpo = PERMITIDOS.sub("", limpo)
    return re.findall(r"\S*\d\S*", limpo)


def problemas_de_texto(texto: str) -> list[str]:
    out = [nome for nome, c in PROIBIDOS.items() if c in texto]
    if EMOJI.search(texto):
        out.append("emoji")
    baixo = texto.lower()
    out += [p for p in PALAVRAS_PROIBIDAS if p in baixo]
    return out


# ------------------------------------------------------------------ SVG


def esc(s) -> str:
    return escape(str(s))


def svg(corpo: str, titulo: str, w: float = W, h: float = H) -> str:
    return (
        f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(titulo)}" '
        f'xmlns="http://www.w3.org/2000/svg"><title>{esc(titulo)}</title>{corpo}</svg>'
    )


def t(
    x,
    y,
    s,
    size=18,
    fill=INK,
    weight=400,
    anchor="start",
    family=SANS,
    extra="",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{family}" font-weight="{weight}" text-anchor="{anchor}"{extra}>'
        f"{esc(s)}</text>"
    )


def r(x, y, w, h, fill, rx=0, extra="") -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
        f'height="{max(h, 0):.1f}" rx="{rx}" fill="{fill}"{extra}/>'
    )


def ln(x1, y1, x2, y2, stroke=GRID, w=1.0, dash=None, extra="") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{w}"{d}{extra}/>'
    )


def circ(x, y, rr, fill, extra="") -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr:.1f}" fill="{fill}"{extra}/>'


def caminho(pontos: list[tuple[float, float]], stroke, w=3.0, extra="") -> str:
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    return (
        f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{w}" '
        f'stroke-linejoin="round" stroke-linecap="round"{extra}/>'
    )


def area(pontos: list[tuple[float, float]], base: float, fill, opacity=0.18) -> str:
    if not pontos:
        return ""
    d = f"M{pontos[0][0]:.1f},{base:.1f} " + " ".join(
        f"L{x:.1f},{y:.1f}" for x, y in pontos
    )
    d += f" L{pontos[-1][0]:.1f},{base:.1f} Z"
    return f'<path d="{d}" fill="{fill}" fill-opacity="{opacity}"/>'


def hachura(pid: str, cor: str = CINZA, fundo: str = PAPER2) -> str:
    return (
        f'<defs><pattern id="{pid}" width="10" height="10" '
        f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="10" height="10" fill="{fundo}"/>'
        f'<line x1="0" y1="0" x2="0" y2="10" stroke="{cor}" stroke-width="3"/>'
        f"</pattern></defs>"
    )


def etiqueta(x, y, s, size=17, fill=INK, fundo=PAPER, anchor="start", weight=600):
    """Texto com caixa de fundo sólido, para rótulo sobre linha ou área colorida."""
    largura = 0.56 * size * len(str(s)) + 10
    if anchor == "middle":
        x0 = x - largura / 2
    elif anchor == "end":
        x0 = x - largura + 5
    else:
        x0 = x - 5
    return r(x0, y - size * 0.95, largura, size * 1.3, fundo, 3) + t(
        x, y, s, size, fill, weight, anchor
    )


def legenda(itens: list[tuple[str, str]], x, y, size=17, passo=None) -> str:
    out, xx = [], x
    for nome, cor in itens:
        out.append(r(xx, y - size * 0.75, size * 0.85, size * 0.85, cor, 2))
        out.append(t(xx + size * 1.15, y, nome, size, INK, 500))
        xx += passo or (size * 1.15 + 0.53 * size * len(nome) + 26)
    return "".join(out)
