"""Figuras SVG do mapa do voto util (setembro de 2026).

Todo grafico e desenhado aqui, em SVG, com os dados embutidos: a pagina abre do
disco, sem rede, e continua completa sem JavaScript. Cada marca leva `<title>`
com o numero exato, que o navegador mostra ao passar o ponteiro. Barras sao
`<rect>`, nunca elemento inline.

Paleta validada (scripts do dataviz, modo claro, todos os pares): Flavio
#1f5f9e, terceira via #0f7f5f, Lula #c8412f. Indecisos e branco/nulo usam
cinzas neutros sempre com rotulo direto.
"""

from __future__ import annotations

import html
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads(
    (ROOT / "docs/assets/voto_util_092026.json").read_text(encoding="utf-8")
)


def _modulo(nome: str):
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


MAPA = _modulo("voto_util_mapa")

INK = "#151812"
MUTED = "#535b54"
LINE = "#d5d2c6"
PAPER = "#ffffff"
FLAVIO = "#1f5f9e"
FLAVIO_TXT = "#1a5189"
TERCEIRA = "#0f7f5f"
TERCEIRA_TXT = "#0b6b56"
LULA = "#c8412f"
LULA_TXT = "#a8321f"
INDEC = "#aab0b6"
BRANCO = "#5f6773"
GOLD = "#7d5b00"
AMARELO = "#f2c230"
MONO = "IBM Plex Mono, ui-monospace, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"
AZUIS = ["#e8eef6", "#c9d8ea", "#9dbbd9", "#6f9bc6", "#437bb1", "#1f5f9e", "#12406f"]


def esc(value) -> str:
    return html.escape(str(value))


def fmt(value, digits=0) -> str:
    if value is None:
        return "n/d"
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(value, digits=0) -> str:
    rounded = round(value, digits)
    return ("+" if rounded > 0 else "") + fmt(rounded, digits)


def mil(n: float | None) -> str:
    if n is None:
        return "n/d"
    if abs(n) >= 1e6:
        return f"{fmt(n / 1e6, 2)} mi"
    return f"{fmt(n / 1e3, 0)} mil"


def svg(body: str, width: float, height: float, label: str, defs: str = "") -> str:
    return (
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{esc(label)}" '
        f'xmlns="http://www.w3.org/2000/svg" class="fig-svg">'
        f"{f'<defs>{defs}</defs>' if defs else ''}{body}</svg>"
    )


def text(
    x,
    y,
    value,
    size: float = 14.0,
    fill=MUTED,
    family=MONO,
    weight=400,
    anchor="start",
    extra="",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-family="{esc(family)}" '
        f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{esc(value)}</text>'
    )


def rect(x, y, w, h, fill, radius=2.0, tip: str = "", extra: str = "") -> str:
    t = f"<title>{esc(tip)}</title>" if tip else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
        f'rx="{radius}" fill="{fill}"{extra}>{t}</rect>'
    )


def line(x1, y1, x2, y2, stroke, width=1.0, dash="") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


def circle(cx, cy, r, fill, tip: str = "", stroke: str = PAPER) -> str:
    t = f"<title>{esc(tip)}</title>" if tip else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2">{t}</circle>'


def hachura(ident: str, cor: str) -> str:
    return (
        f'<pattern id="{ident}" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)">'
        f'<rect width="7" height="7" fill="{cor}" opacity="0.28"/><line x1="0" y1="0" x2="0" y2="7" stroke="{cor}" stroke-width="3"/></pattern>'
    )


def legenda(x, y, itens: list[tuple[str, str]], size: float = 13.0) -> str:
    out, cx = [], x
    for cor, nome in itens:
        out.append(rect(cx, y - 10, 12, 12, cor, 2))
        out.append(text(cx + 17, y, nome, size, INK, SANS, 600))
        cx += 17 + len(nome) * size * 0.52 + 22
    return "".join(out)


# ------------------------------------------------------------ o fenomeno
def fig_fenomeno(width=1000) -> str:
    """Terceira via caindo e para onde foi: variacao por instituto."""
    rows = DATA["nacional"]["fenomeno"]["institutos"]
    top, row_h = 78, 46
    height = top + row_h * len(rows) + 60
    x0, x1 = 250, width - 40
    lo = min(min(r["delta_terceira"], 0) for r in rows) - 1
    hi = max(max(r["delta_flavio"], r["delta_lula"]) for r in rows) + 1

    def sx(v: float) -> float:
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)

    body = [
        text(
            20,
            26,
            "Variação em pontos entre a primeira onda desde 26/08 e a mais recente de cada instituto",
            14,
            INK,
            SANS,
            700,
        ),
        legenda(
            20, 54, [(TERCEIRA, "terceira via"), (FLAVIO, "Flávio"), (LULA, "Lula")]
        ),
    ]
    for tick in range(int(lo // 5 * 5), int(hi) + 1, 5):
        body.append(
            line(
                sx(tick),
                top - 8,
                sx(tick),
                height - 46,
                LINE if tick else INK,
                1 if tick else 1.4,
            )
        )
        body.append(
            text(sx(tick), height - 26, sgn(tick), 12, MUTED, MONO, 400, "middle")
        )
    for i, r in enumerate(rows):
        y = top + i * row_h
        body.append(text(20, y + 21, r["instituto"], 15, INK, SANS, 700))
        body.append(
            text(
                20,
                y + 37,
                f"{r['de'][8:10]}/{r['de'][5:7]} a {r['ate'][8:10]}/{r['ate'][5:7]}",
                11.5,
                MUTED,
            )
        )
        for j, (chave, cor, nome) in enumerate(
            (
                ("delta_terceira", TERCEIRA, "terceira via"),
                ("delta_flavio", FLAVIO, "Flávio"),
                ("delta_lula", LULA, "Lula"),
            )
        ):
            v = r[chave]
            yy = y + 4 + j * 12
            a, b = sorted((sx(0), sx(v)))
            body.append(
                rect(
                    a,
                    yy,
                    b - a,
                    10,
                    cor,
                    2,
                    f"{r['instituto']}: {nome} {sgn(v, 1)} ponto(s)",
                )
            )
            lx = b + 5 if v >= 0 else a - 5
            body.append(
                text(
                    lx,
                    yy + 9,
                    sgn(v, 1),
                    11,
                    INK,
                    MONO,
                    600,
                    "start" if v >= 0 else "end",
                )
            )
    return svg(
        "".join(body),
        width,
        height,
        "Queda da terceira via e ganho de Flávio e Lula por instituto",
    )


# --------------------------------------------------------------- o modelo
def _painel_modelo(
    curva: list[dict], x0: float, x1: float, y0: float, y1: float, titulo: str, sub: str
) -> str:
    lo, hi = 34.0, 54.0

    def sx(lam: float) -> float:
        return x0 + lam * (x1 - x0)

    def sy(v: float) -> float:
        return y1 - (v - lo) / (hi - lo) * (y1 - y0)

    body = [
        text(x0, y0 - 34, titulo, 15, INK, SANS, 700),
        text(x0, y0 - 16, sub, 12, MUTED, SANS, 400),
    ]
    for v in range(int(lo), int(hi) + 1, 4):
        destaque = v == 50
        body.append(
            line(
                x0,
                sy(v),
                x1,
                sy(v),
                INK if destaque else LINE,
                1.6 if destaque else 1,
                "5 4" if destaque else "",
            )
        )
        body.append(text(x0 - 8, sy(v) + 4, f"{v}%", 11.5, MUTED, MONO, 400, "end"))
    body.append(
        rect(
            x0,
            sy(hi),
            x1 - x0,
            sy(50) - sy(hi),
            AMARELO,
            0,
            "Acima de 50% dos válidos a eleição acaba no 1º turno",
            ' opacity="0.16"',
        )
    )
    body.append(
        text(
            x1 - 4,
            sy(50) - 6,
            "acima daqui, acaba no 1º turno",
            11,
            GOLD,
            MONO,
            700,
            "end",
        )
    )
    for k in range(0, 101, 25):
        body.append(
            text(sx(k / 100), y1 + 20, f"{k}%", 11.5, MUTED, MONO, 400, "middle")
        )
    for chave, cor, cor_txt, nome in (
        ("flavio_validos", FLAVIO, FLAVIO_TXT, "Flávio"),
        ("lula_validos", LULA, LULA_TXT, "Lula"),
    ):
        pts = " ".join(f"{sx(p['lam']):.1f},{sy(p[chave]):.1f}" for p in curva)
        body.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="3" stroke-linejoin="round"/>'
        )
        for p in curva[::5]:
            body.append(
                circle(
                    sx(p["lam"]),
                    sy(p[chave]),
                    5,
                    cor,
                    f"{nome}: {fmt(p[chave], 1)}% dos válidos com {fmt(100 * p['lam'])}% do voto útil da direita",
                )
            )
        ini, fim = curva[0][chave], curva[-1][chave]
        body.append(
            text(
                sx(0) + 8,
                sy(ini) + (-9 if chave == "lula_validos" else 17),
                f"{nome} {fmt(ini, 1)}%",
                12.5,
                cor_txt,
                SANS,
                700,
            )
        )
        body.append(
            text(
                sx(1),
                sy(fim)
                + (
                    -9
                    if fim
                    > curva[-1][
                        (
                            "lula_validos"
                            if chave == "flavio_validos"
                            else "flavio_validos"
                        )
                    ]
                    else 17
                ),
                f"{fmt(fim, 1)}%",
                12.5,
                cor_txt,
                SANS,
                700,
                "end",
            )
        )
    return "".join(body)


def fig_modelo(width=1000, height=520) -> str:
    """Dois paineis: so a direita antecipa; Lula antecipa tudo e a direita varia."""
    cur = DATA["modelos"]["media"]["curvas"]
    meio = width / 2
    body = [
        _painel_modelo(
            cur["so_direita"],
            70,
            meio - 30,
            90,
            height - 70,
            "Se só a direita fizer voto útil",
            "Lula fica parado no que tem hoje",
        ),
        _painel_modelo(
            cur["lula_consolida"],
            meio + 60,
            width - 30,
            90,
            height - 70,
            "Se Lula também fizer o dele",
            "a esquerda antecipa toda a reserva de 2º turno",
        ),
        text(
            width / 2,
            height - 18,
            "Eixo horizontal: parcela da reserva de 2º turno de Flávio que já vota nele no 1º turno",
            12.5,
            INK,
            SANS,
            600,
            "middle",
        ),
    ]
    return svg(
        "".join(body),
        width,
        height,
        "Votos válidos de Flávio e Lula conforme a fração do voto útil antecipada, em dois cenários para Lula",
    )


# ------------------------------------------------------------------ mapa
def _classe(v: float, cortes: list[float]) -> int:
    for i, c in enumerate(cortes):
        if v < c:
            return i
    return len(cortes)


def fig_mapa_reserva(width=660, height=660) -> str:
    res = DATA["auxiliar"]["reserva_uf"]
    cortes = [50e3, 100e3, 250e3, 500e3, 1e6, 2e6]

    def cor(uf: str, v) -> str:
        if v is None or uf not in res:
            return "#e3e0d6"
        return AZUIS[_classe(v, cortes)]

    def lab(uf: str, v) -> str:
        return uf

    def tip(uf: str, v) -> str:
        r = res.get(uf, {})
        fontes = (
            " e ".join(
                {"quaest": "Quaest", "realtime": "Real Time"}.get(c["casa"], c["casa"])
                for c in r.get("casas", [])
            )
            or "estimativa sem pesquisa"
        )
        return f"{uf}: {mil(v)} de eleitores votam Flávio no 2º turno e ainda não no 1º ({fmt(r.get('reserva_pp'), 1)} pontos; {fontes})"

    valores = {uf: r["reserva_eleitores"] for uf, r in res.items()}
    lx, ly = 16, height - 180
    leg = [
        text(lx, ly - 30, "Reserva de 2º turno", 12.5, INK, SANS, 700),
        text(lx, ly - 14, "de Flávio, em eleitores", 12.5, INK, SANS, 700),
    ]
    rot = [
        "menos de 50 mil",
        "50 a 100 mil",
        "100 a 250 mil",
        "250 a 500 mil",
        "500 mil a 1 mi",
        "1 a 2 mi",
        "2 mi ou mais",
    ]
    for i, r in enumerate(rot):
        leg.append(rect(lx, ly + i * 20, 16, 14, AZUIS[i], 2))
        leg.append(text(lx + 22, ly + i * 20 + 11, r, 11, MUTED))
    return MAPA.choropleth(
        valores,
        cor,
        lab,
        tip,
        width=width,
        height=height,
        label="Mapa da reserva de 2º turno de Flávio por estado",
        legend="".join(leg),
        escuro=lambda uf, v: v is not None and _classe(v, cortes) >= 4,
    )


def fig_ranking_reserva(width=560) -> str:
    res = DATA["auxiliar"]["reserva_uf"]
    linhas = sorted(res.items(), key=lambda kv: -kv[1]["reserva_eleitores"])
    top, row = 36, 22
    height = top + row * len(linhas) + 30
    x0, x1 = 62, width - 110
    mx = max(r["reserva_eleitores"] for _, r in linhas)
    body = [
        text(
            0,
            18,
            "Eleitores com Flávio no 2º turno e fora dele no 1º",
            13,
            INK,
            SANS,
            700,
        )
    ]
    defs = hachura("h-azul", FLAVIO)
    for i, (uf, r) in enumerate(linhas):
        y = top + i * row
        w = (x1 - x0) * r["reserva_eleitores"] / mx
        fill = "url(#h-azul)" if r.get("estimado") else FLAVIO
        body.append(text(0, y + 12, uf, 12.5, INK, SANS, 700))
        body.append(
            rect(
                x0,
                y + 2,
                w,
                13,
                fill,
                2,
                f"{uf}: {mil(r['reserva_eleitores'])}, {fmt(r['reserva_pp'], 1)} pontos",
            )
        )
        body.append(
            text(
                x0 + w + 6,
                y + 13,
                f"{mil(r['reserva_eleitores'])} · {fmt(r['reserva_pp'], 1)} pp",
                11,
                INK,
                MONO,
            )
        )
    if any(r.get("estimado") for _, r in linhas):
        body.append(
            text(0, height - 6, "Hachura: estimativa sem pesquisa estadual.", 11, MUTED)
        )
    return svg(
        "".join(body),
        width,
        height,
        "Ranking da reserva de 2º turno de Flávio por estado",
        hachura("h-azul", FLAVIO) if defs else "",
    )


# ----------------------------------------------------------- governadores
def fig_governadores(width=1000) -> str:
    linhas = []
    for uf, e in DATA["estados"].items():
        for g in e["indicadores"].get("governador_cruzamento", []):
            if (
                g["campo"] in ("direita", "centro-direita", "centro")
                and g["voto_governador"] >= 5
            ):
                linhas.append((uf, g))
    linhas.sort(key=lambda x: -(x[1]["enderecavel_eleitores"] or 0))
    top, row = 70, 34
    height = top + row * len(linhas) + 40
    x0, x1 = 260, width - 150
    body = [
        text(
            0,
            20,
            "Como vota, para presidente, o eleitor de cada candidato a governador fora da esquerda",
            14,
            INK,
            SANS,
            700,
        ),
        legenda(
            0,
            48,
            [
                (FLAVIO, "Flávio"),
                (TERCEIRA, "terceira via"),
                (INDEC, "indecisos"),
                (BRANCO, "branco/nulo"),
                (LULA, "Lula"),
            ],
        ),
        text(width, 48, "fora de Flávio e de Lula", 12, INK, SANS, 700, "end"),
    ]
    for i, (uf, g) in enumerate(linhas):
        y = top + i * row
        e = DATA["estados"][uf]
        col = next(
            (
                c
                for n, c in (e["pres_x_governador"] or {}).get("colunas", {}).items()
                if n.split(" (")[0] == g["nome"] or n.split()[0] == g["nome"].split()[0]
            ),
            None,
        )
        gr = (
            col["grupos"]
            if col
            else {
                "F": g["flavio_entre_eleitores"],
                "Tdir": 0,
                "I": 0,
                "B": 0,
                "L": g["lula_entre_eleitores"],
            }
        )
        partes = [
            ("F", FLAVIO, "Flávio"),
            ("Tdir", TERCEIRA, "terceira via"),
            ("I", INDEC, "indecisos"),
            ("B", BRANCO, "branco/nulo"),
            ("L", LULA, "Lula"),
        ]
        tot = sum(gr[k] for k, _, _ in partes) or 1
        body.append(
            text(0, y + 14, f"{g['nome']} ({g['partido']}) · {uf}", 13, INK, SANS, 700)
        )
        body.append(
            text(0, y + 28, f"{fmt(g['voto_governador'])}% no governo", 11, MUTED)
        )
        cx = x0
        for k, cor, nome in partes:
            w = (x1 - x0) * gr[k] / tot
            body.append(
                rect(
                    cx,
                    y + 4,
                    max(w - 1.5, 0),
                    20,
                    cor,
                    2,
                    f"{g['nome']}: {nome} {fmt(gr[k])}% dos eleitores dele",
                )
            )
            if w > 26:
                body.append(
                    text(
                        cx + w / 2,
                        y + 18,
                        fmt(gr[k]),
                        11.5,
                        "#ffffff" if k in ("F", "Tdir", "B", "L") else INK,
                        MONO,
                        700,
                        "middle",
                    )
                )
            cx += w
        body.append(
            text(
                width,
                y + 18,
                mil(g["enderecavel_eleitores"]),
                13,
                INK,
                MONO,
                700,
                "end",
            )
        )
    return svg(
        "".join(body),
        width,
        height,
        "Voto presidencial dos eleitores de candidatos a governador fora da esquerda",
    )


# ----------------------------------------------------------- eleitor provavel
def fig_provavel(width=1000) -> str:
    linhas = []
    for uf, e in DATA["estados"].items():
        lv = e.get("lv")
        if lv:
            a, b = lv["sempre"], lv["outros"]
            linhas.append((uf, a["F"] - a["L"], b["F"] - b["L"], lv))
    linhas.sort(key=lambda x: -x[1])
    top, row = 64, 30
    height = top + row * len(linhas) + 50
    x0, x1 = 90, width - 40
    lo = min(min(a, b) for _, a, b, _ in linhas) - 4
    hi = max(max(a, b) for _, a, b, _ in linhas) + 4

    def sx(v: float) -> float:
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)

    body = [
        text(
            0,
            20,
            "Diferença Flávio menos Lula no 1º turno, por hábito de comparecimento",
            14,
            INK,
            SANS,
            700,
        ),
        circle(8, 44, 6, FLAVIO),
        text(20, 48, "sempre vota e vai votar", 12, INK, SANS, 600),
        circle(210, 44, 6, "#ffffff", stroke=INK),
        text(222, 48, "já deixou de votar ou diz que não vai", 12, INK, SANS, 600),
    ]
    for t in range(int(lo // 10 * 10), int(hi) + 1, 10):
        body.append(
            line(
                sx(t),
                top - 6,
                sx(t),
                height - 40,
                INK if t == 0 else LINE,
                1.4 if t == 0 else 1,
            )
        )
        body.append(text(sx(t), height - 20, sgn(t), 11.5, MUTED, MONO, 400, "middle"))
    for i, (uf, a, b, lv) in enumerate(linhas):
        y = top + i * row + 10
        body.append(text(0, y + 5, f"{uf}", 13, INK, SANS, 700))
        body.append(line(sx(a), y, sx(b), y, LINE, 3))
        body.append(
            circle(
                sx(b),
                y,
                6,
                "#ffffff",
                f"{uf}: {sgn(b)} entre quem já deixou de votar ou diz que não vai ({fmt(lv['p_outros'])}% da amostra)",
                stroke=INK,
            )
        )
        body.append(
            circle(
                sx(a),
                y,
                6,
                FLAVIO if a >= 0 else LULA,
                f"{uf}: {sgn(a)} entre quem sempre vota ({fmt(lv['p_sempre'])}% da amostra)",
            )
        )
        body.append(
            text(
                sx(a) + (10 if a >= b else -10),
                y + 4,
                sgn(a),
                11.5,
                INK,
                MONO,
                700,
                "start" if a >= b else "end",
            )
        )
    return svg(
        "".join(body),
        width,
        height,
        "Margem de Flávio sobre Lula entre quem sempre vota e entre quem pode faltar",
    )


# ----------------------------------------------------------- voto resiliente
def fig_definitiva(width=1000) -> str:
    linhas = []
    for uf, e in DATA["estados"].items():
        c = e["definitiva"]["candidatos"]
        if "Flávio" in c and c["Flávio"]["definitiva"] is not None:
            linhas.append(
                (
                    uf,
                    c["Flávio"],
                    c.get("Lula"),
                    {k: v for k, v in c.items() if k not in ("Flávio", "Lula")},
                )
            )
    linhas.sort(key=lambda x: -x[1]["definitiva"])
    top, row = 64, 26
    height = top + row * len(linhas) + 46
    x0, x1 = 70, width - 40
    lo, hi = 30, 100

    def sx(v: float) -> float:
        return x0 + (v - lo) / (hi - lo) * (x1 - x0)

    body = [
        text(
            0,
            20,
            "Entre quem vota em cada candidato, quantos dizem que o voto é definitivo",
            14,
            INK,
            SANS,
            700,
        ),
        circle(8, 44, 6, FLAVIO),
        text(20, 48, "Flávio", 12, INK, SANS, 600),
        circle(90, 44, 6, LULA),
        text(102, 48, "Lula", 12, INK, SANS, 600),
        circle(160, 44, 6, TERCEIRA),
        text(172, 48, "terceira via (quando o instituto publica)", 12, INK, SANS, 600),
    ]
    for t in range(lo, hi + 1, 10):
        body.append(line(sx(t), top - 6, sx(t), height - 36, LINE, 1))
        body.append(text(sx(t), height - 16, f"{t}%", 11.5, MUTED, MONO, 400, "middle"))
    for i, (uf, f, lu, outros) in enumerate(linhas):
        y = top + i * row + 8
        body.append(text(0, y + 5, uf, 13, INK, SANS, 700))
        for nome, v in outros.items():
            if v["definitiva"] is not None:
                body.append(
                    circle(
                        sx(v["definitiva"]),
                        y,
                        5,
                        TERCEIRA,
                        f"{uf}: {fmt(v['definitiva'])}% do eleitor de {nome} diz que o voto é definitivo",
                    )
                )
        if lu and lu["definitiva"] is not None:
            body.append(
                circle(
                    sx(lu["definitiva"]),
                    y,
                    5,
                    LULA,
                    f"{uf}: {fmt(lu['definitiva'])}% do eleitor de Lula",
                )
            )
        if f.get("anterior") is not None:
            body.append(line(sx(f["anterior"]), y, sx(f["definitiva"]), y, FLAVIO, 2))
            body.append(
                circle(
                    sx(f["anterior"]),
                    y,
                    3,
                    "#ffffff",
                    f"{uf}: {fmt(f['anterior'])}% na rodada anterior",
                    stroke=FLAVIO,
                )
            )
        body.append(
            circle(
                sx(f["definitiva"]),
                y,
                6,
                FLAVIO,
                f"{uf}: {fmt(f['definitiva'])}% do eleitor de Flávio diz que o voto é definitivo",
            )
        )
    return svg("".join(body), width, height, "Voto definitivo por candidato e estado")


# ----------------------------------------------------------- expectativa
def fig_expectativa(width=1000) -> str:
    linhas = []
    for uf, e in DATA["estados"].items():
        q = (e.get("quem_ganha") or {}).get("valores")
        p2 = e.get("pres_2t")
        if q and p2:
            linhas.append((uf, p2["valores"], q))
    linhas.sort(key=lambda x: -(x[1]["Flávio"] - x[1]["Lula"]))
    top, row = 70, 58
    height = top + row * len(linhas) + 30
    x0, x1 = 60, width - 60
    body = [
        text(
            0,
            20,
            "Quem o eleitor escolhe no 2º turno e quem ele acha que vai ganhar, no mesmo estado",
            14,
            INK,
            SANS,
            700,
        ),
        legenda(0, 48, [(FLAVIO, "Flávio"), (LULA, "Lula")]),
    ]
    for i, (uf, v2, q) in enumerate(linhas):
        y = top + i * row
        body.append(text(0, y + 22, uf, 15, INK, SANS, 700))
        for j, (rot, f, lu) in enumerate(
            (
                ("vota", v2["Flávio"], v2["Lula"]),
                ("acha que ganha", q.get("Flávio", 0), q.get("Lula", 0)),
            )
        ):
            yy = y + j * 24
            body.append(text(x0, yy + 14, rot, 11.5, MUTED))
            bx = x0 + 110
            escala = (x1 - bx) / 100
            body.append(
                rect(
                    bx,
                    yy + 3,
                    f * escala,
                    16,
                    FLAVIO,
                    2,
                    f"{uf}, {rot}: Flávio {fmt(f)}%",
                )
            )
            body.append(text(bx + 6, yy + 15, f"{fmt(f)}", 11.5, "#ffffff", MONO, 700))
            body.append(
                rect(
                    bx + f * escala + 2,
                    yy + 3,
                    lu * escala,
                    16,
                    LULA,
                    2,
                    f"{uf}, {rot}: Lula {fmt(lu)}%",
                )
            )
            body.append(
                text(
                    bx + f * escala + 8,
                    yy + 15,
                    f"{fmt(lu)}",
                    11.5,
                    "#ffffff",
                    MONO,
                    700,
                )
            )
    return svg(
        "".join(body),
        width,
        height,
        "Voto no 2º turno contra expectativa de vitória por estado",
    )


# ----------------------------------------------------------- segmentos
def fig_segmentos(segmentos: list[dict], width=1000) -> str:
    top, row = 40, 26
    height = top + row * len(segmentos) + 30
    x0, x1 = 210, width - 140
    mx = max(s["reserva"] for s in segmentos)
    body = [
        text(
            0,
            20,
            "Flávio no 2º turno menos Flávio no 1º turno, na mesma amostra (Datafolha, 15 a 17/09)",
            14,
            INK,
            SANS,
            700,
        )
    ]
    for i, s in enumerate(segmentos):
        y = top + i * row
        w = (x1 - x0) * s["reserva"] / mx
        body.append(text(0, y + 13, s["nome"], 13, INK, SANS, 600))
        body.append(
            rect(
                x0,
                y + 2,
                w,
                15,
                FLAVIO,
                2,
                f"{s['nome']}: {fmt(s['f1'])}% no 1º turno, {fmt(s['f2'])}% no 2º turno, base {fmt(s['base'])} entrevistas",
            )
        )
        body.append(
            text(
                x0 + w + 6,
                y + 14,
                f"+{fmt(s['reserva'])} ({fmt(s['f1'])} → {fmt(s['f2'])})",
                11.5,
                INK,
                MONO,
                600,
            )
        )
    return svg(
        "".join(body),
        width,
        height,
        "Reserva de 2º turno de Flávio por segmento do eleitorado",
    )


# ----------------------------------------------------------- contribuicao
def fig_contribuicao(width=1000) -> str:
    casas = DATA["auxiliar"].get("casas", ["quaest", "realtime"])
    por_casa = [
        {
            r["uf"]: r["ganho_flavio_eleitores"]
            for r in DATA["modelos"][c]["contribuicao"]
        }
        for c in casas
    ]
    ufs = set.intersection(*(set(x) for x in por_casa))
    todos = sorted(
        ((uf, sum(x[uf] for x in por_casa) / len(por_casa)) for uf in ufs),
        key=lambda x: -x[1],
    )
    total = sum(v for _, v in todos)
    linhas = todos[:14]
    top, row = 40, 28
    height = top + row * len(linhas) + 24
    x0, x1 = 60, width - 260
    mx = linhas[0][1]
    body = [
        text(
            0,
            20,
            "Votos que Flávio ganha em cada estado se toda a reserva de 2º turno votar nele no 1º turno",
            14,
            INK,
            SANS,
            700,
        )
    ]
    acum = 0.0
    for i, (uf, v) in enumerate(linhas):
        acum += v
        y = top + i * row
        w = (x1 - x0) * v / mx
        body.append(text(0, y + 15, uf, 13.5, INK, SANS, 700))
        body.append(
            rect(
                x0,
                y + 3,
                w,
                17,
                FLAVIO,
                2,
                f"{uf}: {mil(v)} de votos a mais para Flávio",
            )
        )
        body.append(
            text(
                x0 + w + 6,
                y + 16,
                f"{mil(v)} · {fmt(100 * acum / total)}% do total acumulado",
                11.5,
                INK,
                MONO,
            )
        )
    return svg(
        "".join(body),
        width,
        height,
        "Ganho de Flávio por estado com voto útil completo",
    )


FIGURAS = {
    "fenomeno": fig_fenomeno,
    "modelo": fig_modelo,
    "mapa_reserva": fig_mapa_reserva,
    "ranking_reserva": fig_ranking_reserva,
    "governadores": fig_governadores,
    "provavel": fig_provavel,
    "definitiva": fig_definitiva,
    "expectativa": fig_expectativa,
    "contribuicao": fig_contribuicao,
}
