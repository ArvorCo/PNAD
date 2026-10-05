"""Base das figuras do catálogo: registro, ficha interativa, controles e escalas.

Cada figura do catálogo (`analysis/apuracao_2026/CATALOGO_FIGURAS.md`) é uma
função `fn(d, **op) -> str`, onde `d` é o dicionário de todos os JSONs do dossiê
por nome sem extensão (mais `agregador`). A função devolve um `<figure>` completo:
SVG com `<title>` e `<desc>`, fichas em `<script type="application/json"
class="tips">` e legenda. O SVG é desenhado inteiro em Python; o JavaScript de
`pagina_interativo` só acrescenta a ficha, o realce e as alternâncias, e a figura
continua completa quando o script não roda.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from html import escape

from .pagina_comum import (
    CINZA,
    COR_CAMPO,
    ERROS_DE_DADO,
    FLAVIO,
    INK,
    LINE,
    LULA,
    MUTED,
    OUTROS,
    PAPER,
    ROTULO_CAMPO,
    num,
)

FONTE = "Archivo, Helvetica, Arial, sans-serif"
MONO = "IBM Plex Mono, ui-monospace, monospace"
W = 1100
GRADE = "#ddd6c6"
SOMBRA = "#e6dcc2"
LIMA = "#a4d42b"
OUTROS_TXT = "#0b6650"

COR_CAND = {
    "flavio": FLAVIO,
    "lula": LULA,
    "cury": OUTROS,
    "renan": "#3d8a74",
    "renan_santos": "#3d8a74",
    "caiado": "#6aa392",
    "zema": "#8fb8aa",
    "outros": CINZA,
    "demais": CINZA,
    "terceiros": OUTROS,
}
NOME_CAND = {
    "flavio": "Flávio Bolsonaro",
    "lula": "Lula",
    "cury": "Augusto Cury",
    "renan": "Renan Santos",
    "renan_santos": "Renan Santos",
    "caiado": "Ronaldo Caiado",
    "zema": "Romeu Zema",
    "outros": "Outros",
    "demais": "Demais",
    "terceiros": "Terceiros",
}
COR_PARTIDO = {
    "PL": "#1457aa",
    "NOVO": "#e07b1a",
    "REPUBLICANOS": "#3a6fb8",
    "MISSÃO": "#5a4a9e",
    "UNIÃO": "#2f8fb0",
    "PP": "#6c9bd8",
    "PODE": "#7fb0d6",
    "PRD": "#9cc0e6",
    "PSD": "#a0893a",
    "MDB": "#7d6a2a",
    "AVANTE": "#c2a855",
    "PSDB": "#d9775f",
    "CIDADANIA": "#e3a08c",
    "SOLIDARIEDADE": "#c96f5b",
    "PT": "#b02f21",
    "PSB": "#d8472f",
    "PCDOB": "#8a1c12",
    "PSOL": "#7a2a6e",
    "PDT": "#e05a45",
    "PV": "#4f8a3a",
    "REDE": "#3d8a74",
}
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
COR_REGIAO = {
    "Norte": "#0f7f5f",
    "Nordeste": "#b0562a",
    "Centro-Oeste": "#7d5b00",
    "Sudeste": "#1457aa",
    "Sul": "#6b4a92",
    "Exterior": "#535b54",
}
CAMPOS = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita"]

FIGURAS: dict[str, Callable[..., str]] = {}


# ------------------------------------------------------------------ dados


def dado(d, nome: str):
    """Dataset pelo nome sem extensão; aceita o dicionário ou o leitor `Dados`."""
    v = d.get(nome) if isinstance(d, dict) else d.get(f"{nome}.json")
    if v is None:
        raise KeyError(f"{nome}.json")
    return v


def tabela_linhas(bloco: dict) -> list[dict]:
    """{'colunas': [...], 'linhas': [[...]]} vira lista de dicionários."""
    cols = bloco["colunas"]
    return [dict(zip(cols, r, strict=False)) for r in bloco["linhas"]]


# ------------------------------------------------------------------ registro


def registra(nome: str):
    """Registra a figura; dado ausente vira figura pendente, nunca exceção."""

    def deco(fn):
        def wrapper(d, **op) -> str:
            try:
                return fn(d, **op)
            except ERROS_DE_DADO as erro:
                print(f"aviso: figura {nome}: {type(erro).__name__} {erro}")
                return (
                    f'<figure class="pendente" id="fig-{nome}"><figcaption>figura em preparação: '
                    f"<code>{escape(nome)}</code> ({escape(type(erro).__name__)} {escape(str(erro))})"
                    "</figcaption></figure>"
                )

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        FIGURAS[nome] = wrapper
        return wrapper

    return deco


# ------------------------------------------------------------------ fichas


class Tips:
    """Fichas de uma figura: HTML por chave ou tabela compacta (`_rows`)."""

    def __init__(self) -> None:
        self.html: dict[str, str] = {}
        self.rows: dict | None = None

    def add(self, html: str) -> str:
        k = f"k{len(self.html)}"
        self.html[k] = html
        return k

    def tabela(
        self,
        campos: list[str],
        linhas: list[list],
        sub: int | None = None,
        nota: str | None = None,
        xy: list | None = None,
        grupos: list | None = None,
    ) -> None:
        r: dict = {"campos": campos, "linhas": linhas}
        if sub is not None:
            r["sub"] = sub
        if nota:
            r["nota"] = nota
        if xy is not None:
            r["xy"] = xy
        if grupos is not None:
            r["g"] = grupos
        self.rows = r

    def script(self) -> str:
        obj = dict(self.html)
        if self.rows is not None:
            obj["_rows"] = self.rows
        texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        texto = texto.replace("</", "<\\/")
        return f'<script type="application/json" class="tips">{texto}</script>'


def ficha(
    titulo: str,
    sub: str = "",
    linhas: list[tuple[str, str]] | None = None,
    nota: str = "",
) -> str:
    """HTML da ficha escura da casa: cabeçalho, tabela de rótulo e valor, nota."""
    h = f'<p class="tip-head"><b>{escape(titulo)}</b>'
    if sub:
        h += f"<span>{escape(sub)}</span>"
    h += "</p>"
    if linhas:
        h += '<table class="tip-tab"><tbody>'
        for rot, val in linhas:
            h += f"<tr><th>{escape(rot)}</th><td>{escape(str(val))}</td></tr>"
        h += "</tbody></table>"
    if nota:
        h += f'<p class="tip-nota">{escape(nota)}</p>'
    return h


def hit(conteudo: str, k: str, foco: bool = False, extra: str = "") -> str:
    tab = ' tabindex="0"' if foco else ""
    return f'<g class="hit" data-k="{k}"{tab}{extra}>{conteudo}</g>'


def area(x, y, w, h) -> str:
    """Área transparente de toque."""
    return (
        f'<rect class="hit-area" x="{x:.1f}" y="{y:.1f}" width="{max(w, 0.5):.1f}" '
        f'height="{max(h, 0.5):.1f}" fill="transparent"/>'
    )


# ------------------------------------------------------------------ figura


def botoes(
    opcoes: list[tuple[str, str]],
    ativo: str,
    rotulo: str,
    tipo: str = "alt",
) -> str:
    """Grupo de botões. `tipo`: 'alt' (troca de série), 'tab' (abas), 'filtro'."""
    attr = "data-filtro" if tipo == "filtro" else "data-alt"
    papel = 'role="tablist"' if tipo == "tab" else 'role="group"'
    out = [
        f'<div class="fig-ctl fig-ctl-{tipo}" {papel} aria-label="{escape(rotulo)}">'
        f'<span class="rot">{escape(rotulo)}</span>'
    ]
    for k, nome in opcoes:
        on = "true" if k == ativo else "false"
        extra = f' role="tab" aria-selected="{on}"' if tipo == "tab" else ""
        out.append(
            f'<button type="button" {attr}="{escape(k)}" aria-pressed="{on}"{extra}>{escape(nome)}</button>'
        )
    out.append("</div>")
    return "".join(out)


def figura_html(
    nome: str,
    svg: str,
    legenda: str,
    tips: Tips,
    *,
    controles: str = "",
    modo: str = "scroll",
    minw: int = 760,
    dim: bool = True,
    apos: str = "",
) -> str:
    """`modo`: 'scroll' (rolagem interna abaixo de `minw`), 'fit' (até 760 px) ou 'full'."""
    cls = {"scroll": "chart-scroll", "fit": "chart-fit", "full": "chart-full"}[modo]
    estilo = f' style="--minw:{minw}px"' if modo == "scroll" else ""
    dimattr = " data-dim" if dim else ""
    return (
        f'<figure class="reveal fig-i" id="fig-{nome}" data-fig="{nome}"{dimattr}>'
        f'{controles}<div class="{cls}" tabindex="0"{estilo}>{svg}</div>{apos}{tips.script()}'
        f'<figcaption>{legenda} <span class="dica">ficha ao passar o ponteiro ou tocar</span>'
        "</figcaption></figure>"
    )


def legenda_html(itens: list[tuple[str, str]], titulo: str = "") -> str:
    """Legenda em HTML, legível em qualquer largura. Cor pode ser um `background` CSS."""
    lis = "".join(
        f'<li><span class="sw" style="background:{cor}"></span>{escape(nome)}</li>'
        for nome, cor in itens
    )
    cab = f'<b class="leg-tit">{escape(titulo)}</b>' if titulo else ""
    return f'<div class="fig-leg">{cab}<ul class="legenda-mapa">{lis}</ul></div>'


def svg_abre(w: float, h: float, titulo: str, desc: str, extra: str = "") -> str:
    return (
        f'<svg class="fig" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
        f'aria-label="{escape(titulo)}" xmlns="http://www.w3.org/2000/svg"{extra}>'
        f"<title>{escape(titulo)}</title><desc>{escape(desc)}</desc>"
    )


def t(
    x: float,
    y: float,
    s,
    size: float = 14,
    fill: str = INK,
    anchor: str = "start",
    weight: str | None = None,
    mono: bool = False,
    extra: str = "",
) -> str:
    peso = f' font-weight="{weight}"' if weight else ""
    fam = MONO if mono else FONTE
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{fam}" text-anchor="{anchor}"{peso}{extra}>{escape(str(s))}</text>'
    )


def chip(x: float, y: float, s: str, size: float = 13, anchor: str = "start") -> str:
    """Rótulo com fundo branco, legível sobre qualquer cor."""
    w = 0.53 * size * len(s) + 12
    x0 = x if anchor == "start" else x - w if anchor == "end" else x - w / 2
    return (
        f'<rect x="{x0:.1f}" y="{y - size - 2:.1f}" width="{w:.1f}" height="{size + 8:.1f}" '
        f'rx="3" fill="#ffffff" stroke="{MUTED}" stroke-width="0.6"/>'
        + t(x0 + 5, y + 1, s, size, INK, weight="600")
    )


def r(x, y, w, h, fill, extra: str = "") -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
        f'height="{max(h, 0):.1f}" fill="{fill}"{extra}/>'
    )


def ln(x1, y1, x2, y2, stroke=LINE, w: float = 1, extra: str = "") -> str:
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{w}"{extra}/>'
    )


def legenda(itens: list[tuple[str, str]], x: float, y: float, size: float = 14) -> str:
    out, cx = [], x
    for nome, cor in itens:
        out.append(r(cx, y - 11, 13, 13, cor))
        out.append(t(cx + 18, y, nome, size))
        cx += 34 + 0.56 * size * len(nome)
    return "".join(out)


def luminancia(cor: str) -> float:
    cor = cor.lstrip("#")
    if len(cor) == 3:
        cor = "".join(c * 2 for c in cor)
    canais = [int(cor[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def sobre(fundo: str) -> str:
    """Branco ou tinta, o que der mais contraste sobre o preenchimento."""
    return "#ffffff" if contraste(fundo, "#ffffff") >= contraste(fundo, INK) else INK


# ------------------------------------------------------------------ escalas


def escala(d0: float, d1: float, r0: float, r1: float):
    span = (d1 - d0) or 1.0

    def f(v: float) -> float:
        return r0 + (r1 - r0) * (v - d0) / span

    return f


def ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    """Marcas redondas cobrindo [lo, hi]."""
    if hi <= lo:
        return [lo]
    bruto = (hi - lo) / n
    base = 10 ** math.floor(math.log10(bruto))
    passo = base
    for m in (1, 2, 5, 10):
        if base * m >= bruto:
            passo = base * m
            break
    a = math.ceil(lo / passo - 1e-9) * passo
    out = []
    v = a
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += passo
    return out


def minutos(hhmmss: str) -> float:
    """'2026-10-04 18:48:59' ou '18:48' vira minutos desde 00:00 do dia 04 (05 soma 1440)."""
    s = hhmmss.strip()
    dia = 0
    if " " in s:
        data, s = s.split(" ", 1)
        dia = 1440 if data.endswith("-05") else 0
    partes = [int(x) for x in s.split(":")]
    while len(partes) < 3:
        partes.append(0)
    return dia + partes[0] * 60 + partes[1] + partes[2] / 60


def rot_hora(m: float) -> str:
    m = round(m) % 1440
    return f"{m // 60:02d}h" if m % 60 == 0 else f"{m // 60:02d}:{m % 60:02d}"


def pct(x, casas: int = 2) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def pp(x, casas: int = 2) -> str:
    if x is None:
        return "s/d"
    s = num(abs(x), casas)
    return ("+" if x > 0 else "−" if x < 0 else "") + s + " pp"


def campo_nome(c: str | None) -> str:
    return ROTULO_CAMPO.get(c or "indefinido", "Indefinido")


# Centro e centro-direita um tom mais escuros que a paleta da casa: com rótulo branco
# por cima, a cor original (#8a7a3a, #4f7fc2) não chega a 4,5:1 nem com branco nem com tinta.
COR_CAMPO_FIG = dict(COR_CAMPO, centro="#7d6e33")
COR_CAMPO_FIG["centro-direita"] = "#4373b8"


def cor_campo(c: str | None) -> str:
    return COR_CAMPO_FIG.get(c or "indefinido", COR_CAMPO_FIG["indefinido"])


def nome_bonito(s: str) -> str:
    minus = {"de", "da", "do", "dos", "das", "e", "d'"}
    siglas = {"JHC", "PT", "PL", "DF", "II", "III"}
    out = []
    for i, p in enumerate(str(s).split()):
        if p.upper() in siglas:
            out.append(p.upper())
            continue
        low = p.lower()
        out.append(low if (i and low in minus) else low[:1].upper() + low[1:])
    return " ".join(out)


__all__ = [
    "CAMPOS",
    "CINZA",
    "COR_CAND",
    "COR_PARTIDO",
    "COR_REGIAO",
    "FIGURAS",
    "FLAVIO",
    "GRADE",
    "INK",
    "LIMA",
    "LINE",
    "LULA",
    "MUTED",
    "NOME_CAND",
    "OUTROS",
    "OUTROS_TXT",
    "PAPER",
    "REGIOES",
    "SOMBRA",
    "Tips",
    "W",
    "area",
    "botoes",
    "campo_nome",
    "chip",
    "contraste",
    "cor_campo",
    "dado",
    "escala",
    "ficha",
    "figura_html",
    "hit",
    "legenda",
    "legenda_html",
    "ln",
    "minutos",
    "nome_bonito",
    "pct",
    "pp",
    "r",
    "registra",
    "rot_hora",
    "sobre",
    "svg_abre",
    "t",
    "tabela_linhas",
    "ticks",
]
