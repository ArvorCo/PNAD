#!/usr/bin/env python3
"""Figuras SVG do atlas estadual de setembro de 2026.

Todo grafico e desenhado aqui, em SVG, com os dados embutidos no proprio
elemento: a pagina abre do disco, sem rede e sem JavaScript, e continua
completa. As barras usam `display:block` por regra do projeto, porque elemento
inline ignora largura e o desenho some sem que a revisao de codigo veja.

Importado por `estaduais-092026-build.py` e por `superthread-092026.py`.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs/assets/estaduais_092026_data.json").read_text())

INK = "#151812"
INK_DARK = "#f4f2ea"
MUTED = "#535b54"
MUTED_DARK = "#9a9789"
FAINT_DARK = "#8f8c7f"
LULA = "#c8412f"
LULA_DARK = "#ea6a5c"
FLAVIO = "#2f6fae"
FLAVIO_DARK = "#5ba3e0"
DIREITA = "#0c7a72"
GOLD = "#7d5b00"
GOLD_DARK = "#f0a930"
GREEN = "#2f7d52"
GREY = "#5f6773"
MONO = "IBM Plex Mono, ui-monospace, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"


def esc(value) -> str:
    return html.escape(str(value))


def fmt(value, digits=0) -> str:
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(value, digits=0) -> str:
    rounded = round(value, digits)
    return ("+" if rounded > 0 else "") + fmt(rounded, digits)


def svg(body: str, width: float, height: float, label: str, extra: str = "") -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" '
        f'xmlns="http://www.w3.org/2000/svg" class="fig-svg">{extra}{body}</svg>'
    )


def text(
    x: float,
    y: float,
    value,
    size: float = 14,
    fill: str = MUTED,
    family: str = MONO,
    weight: int = 400,
    anchor: str = "start",
    cls: str = "",
) -> str:
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{esc(family)}" font-weight="{weight}" text-anchor="{anchor}"{klass}>'
        f"{esc(value)}</text>"
    )


def rect(
    x: float, y: float, w: float, h: float, fill: str, radius: float = 2, cls: str = ""
) -> str:
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
        f'rx="{radius}" fill="{fill}"{klass}/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str,
    width: float = 1,
    dash: str = "",
) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def circle(cx: float, cy: float, r: float, fill: str, cls: str = "") -> str:
    klass = f' class="{cls}"' if cls else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"{klass}/>'


# ----------------------------------------------------------------- figura 1
def fig_vao(dark=False, width=1000, height=760) -> str:
    """Barra da direita estadual contra o voto de Flavio, na mesma amostra."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    rows = list(DATA["vaos"])
    x0, x1 = 232, width - 118
    top, step = 78, (height - 128) / len(rows)
    scale = lambda v: x0 + (x1 - x0) * v / 62  # noqa: E731
    out = [
        text(
            28,
            30,
            "O teto da direita no estado e o voto de Flávio, na mesma entrevista",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Melhor candidatura de direita ao governo (círculo) contra Flávio no 1º turno presidencial (quadrado). Quaest, agosto e setembro de 2026.",
            13,
            faint,
            SANS,
        ),
    ]
    for value in (0, 20, 40, 60):
        out.append(
            line(scale(value), top - 12, scale(value), height - 44, faint, 1, "2 5")
        )
        out.append(
            text(scale(value), height - 26, f"{value}%", 11, faint, MONO, 400, "middle")
        )
    for index, row in enumerate(rows):
        y = top + step * index + step / 2
        gov, flavio = row["gov"], row["flavio_1t"]
        lo, hi = min(gov, flavio), max(gov, flavio)
        colour = DIREITA if gov >= flavio else GOLD_DARK if dark else GOLD
        out.append(line(scale(lo), y, scale(hi), y, colour, 3))
        out.append(
            rect(scale(flavio) - 6, y - 6, 12, 12, FLAVIO_DARK if dark else FLAVIO, 2)
        )
        out.append(circle(scale(gov), y, 6.5, colour))
        out.append(
            text(28, y + 4, f"{row['uf']}  {row['candidato']}", 13, ink, SANS, 600)
        )
        out.append(
            text(width - 104, y + 4, f"{sgn(row['vao_1t'])} pts", 13, colour, MONO, 700)
        )
    out.append(
        text(
            28,
            height - 8,
            "Vão positivo: a direita estadual vai mais longe que a candidatura presidencial. Vão negativo: Flávio puxa a chapa.",
            12,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Vão entre o voto da direita estadual e o voto de Flávio, por estado",
    )


# ----------------------------------------------------------------- figura 2
def fig_nao_visitados(dark=False, width=1000, height=560) -> str:
    """Eleitorado e estoque bolsonarista dos dez estados fora do roteiro."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    rows = DATA["nao_visitados"]["detalhe"]
    maxi = max(r["eleitores_2026"] for r in rows)
    x0, x1 = 150, width - 250
    top, step = 96, (height - 150) / len(rows)
    out = [
        text(
            28,
            30,
            "Dez estados fora do roteiro: 26,6 milhões de eleitores",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Barra clara: eleitorado de 2026. Barra cheia: votos de Bolsonaro no 2º turno de 2022. Três desses estados ele venceu.",
            13,
            faint,
            SANS,
        ),
    ]
    for index, row in enumerate(rows):
        y = top + step * index
        full = (x1 - x0) * row["eleitores_2026"] / maxi
        part = (x1 - x0) * row["bolsonaro_2t"] / maxi
        out.append(
            rect(
                x0,
                y,
                full,
                step * 0.62,
                "#c9cfc6" if not dark else "#2b302a",
                2,
                "bar-bg",
            )
        )
        colour = GREEN if row["venceu_2022"] else (FLAVIO_DARK if dark else FLAVIO)
        out.append(rect(x0, y, part, step * 0.62, colour, 2, "bar-fill"))
        out.append(text(28, y + step * 0.44, row["uf"], 15, ink, MONO, 700))
        out.append(
            text(
                58,
                y + step * 0.44,
                f"{fmt(row['eleitores_2026'] / 1e6, 2)} mi",
                12,
                faint,
                MONO,
            )
        )
        label = f"{fmt(row['bolsonaro_2t'] / 1000)} mil  ({fmt(row['bolsonaro_2t_pct'], 1)}%)"
        if row["venceu_2022"]:
            label += "  venceu"
        out.append(text(x1 + 14, y + step * 0.44, label, 12.5, colour, MONO, 600))
    total = DATA["nao_visitados"]
    out.append(
        text(
            28,
            height - 34,
            f"Somados: {fmt(total['bolsonaro_2t'] / 1e6, 2)} milhões de votos de Bolsonaro em 2022, 16,9% do eleitorado nacional.",
            13,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 12,
            "Fonte: TSE, resultado de 2022 por município, e eleitorado de 2026. Roteiro: Revista Fórum e BPMoney.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Eleitorado e voto de Bolsonaro nos dez estados fora do roteiro",
    )


# ----------------------------------------------------------------- figura 3
def fig_capitais(dark=False, width=1000, height=600) -> str:
    """Onde esta o voto de direita no Norte e no Nordeste: nas capitais."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    rows = DATA["capitais"][:14]
    maxi = max(r["bolsonaro_2t"] for r in rows)
    x0, x1 = 176, width - 210
    top, step = 96, (height - 150) / len(rows)
    out = [
        text(
            28,
            30,
            "O voto bolsonarista do Norte e do Nordeste é urbano",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Votos de Bolsonaro no 2º turno de 2022 nas capitais das duas regiões. Verde: capital que ele venceu. Azul: capital que Lula venceu.",
            13,
            faint,
            SANS,
        ),
    ]
    for index, row in enumerate(rows):
        y = top + step * index
        w = (x1 - x0) * row["bolsonaro_2t"] / maxi
        colour = GREEN if row["venceu"] else (FLAVIO_DARK if dark else FLAVIO)
        out.append(rect(x0, y, w, step * 0.6, colour, 2, "bar-fill"))
        mark = " *" if row["nao_visitado"] else ""
        out.append(
            text(
                x0 - 12,
                y + step * 0.43,
                f"{row['municipio']}{mark}",
                13,
                ink,
                SANS,
                600,
                "end",
            )
        )
        out.append(
            text(
                x0 + w + 12,
                y + step * 0.43,
                f"{fmt(row['bolsonaro_2t'] / 1000)} mil   {fmt(row['bolsonaro_2t_pct'], 1)}%",
                12,
                colour,
                MONO,
                600,
            )
        )
    out.append(
        text(
            28,
            height - 34,
            "* estado que a campanha não visitou até 14/09. Manaus sozinha guarda mais voto de Bolsonaro que qualquer outra cidade das duas regiões.",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 12,
            "Fonte: TSE, 2º turno de 2022 por município.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Votos de Bolsonaro em 2022 nas capitais do Norte e do Nordeste",
    )


# ----------------------------------------------------------------- figura 4
def fig_concentracao(dark=False, width=1000, height=470) -> str:
    """Curva de concentração do voto bolsonarista no Nordeste."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    ne = DATA["concentracao"]["nordeste"]
    curve = ne["curva"]
    x0, x1, y0, y1 = 92, width - 40, height - 78, 96
    total = ne["municipios"]
    sx = lambda i: x0 + (x1 - x0) * i / total  # noqa: E731
    sy = lambda p: y0 - (y0 - y1) * p / 100  # noqa: E731
    points = " ".join(f"{sx(i):.1f},{sy(p):.1f}" for i, p in curve)
    out = [
        text(
            28,
            30,
            "54 municípios de 1.794 concentram metade do voto bolsonarista do Nordeste",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Curva acumulada dos votos de Bolsonaro no 2º turno de 2022, dos municípios de maior volume para os de menor.",
            13,
            faint,
            SANS,
        ),
    ]
    for value in (0, 25, 50, 75, 100):
        out.append(line(x0, sy(value), x1, sy(value), faint, 1, "2 6"))
        out.append(
            text(x0 - 12, sy(value) + 4, f"{value}%", 11, faint, MONO, 400, "end")
        )
    out.append(
        f'<polyline points="{points}" fill="none" stroke="{DIREITA}" stroke-width="2.6"/>'
    )
    mark = ne["metade_em"]
    out.append(
        line(sx(mark), sy(0), sx(mark), sy(50), LULA_DARK if dark else LULA, 1.6, "4 4")
    )
    out.append(circle(sx(mark), sy(50), 5.5, LULA_DARK if dark else LULA))
    out.append(
        text(
            sx(mark) + 12,
            sy(50) - 10,
            f"{mark} municípios = 50% dos votos",
            13,
            LULA_DARK if dark else LULA,
            MONO,
            700,
        )
    )
    out.append(
        text(
            sx(mark) + 12,
            sy(50) + 10,
            f"{fmt(ne['metade_pct_municipios'], 1)}% das cidades do Nordeste",
            12,
            faint,
            MONO,
        )
    )
    out.append(
        text(
            x0,
            height - 44,
            "municípios, do maior volume para o menor",
            11.5,
            faint,
            SANS,
        )
    )
    out.append(
        text(
            28,
            height - 12,
            f"Total: {fmt(ne['votos'])} votos de Bolsonaro no Nordeste em 2022. Fonte: TSE.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Curva de concentração do voto bolsonarista no Nordeste",
    )


# ----------------------------------------------------------------- figura 5
def fig_temas(dark=False, width=1000, height=500) -> str:
    """O tema mais citado como maior problema, estado a estado."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    ordem = [
        "Saúde",
        "Violência",
        "Infraestrutura",
        "Desemprego",
        "Corrupção",
        "Educação",
    ]
    cores = {
        "Saúde": DIREITA,
        "Violência": LULA_DARK if dark else LULA,
        "Infraestrutura": GOLD_DARK if dark else GOLD,
        "Desemprego": FLAVIO_DARK if dark else FLAVIO,
        "Corrupção": "#6b4a92",
        "Educação": GREY,
    }
    ufs = [p["uf"] for p in DATA["pesquisas"] if p["uf"] in DATA["temas"]]
    ufs.sort(key=lambda u: -dict(DATA["temas"][u]).get("Saúde", 0))
    x0 = 92
    colw = (width - x0 - 40) / len(ufs)
    top, rowh = 118, 58
    out = [
        text(28, 30, "O que cada estado chama de maior problema", 19, ink, SANS, 700),
        text(
            28,
            54,
            "Quaest, pergunta aberta com cartão: qual é o problema mais grave que o seu estado enfrenta hoje. Percentual de citações.",
            13,
            faint,
            SANS,
        ),
    ]
    for index, uf in enumerate(ufs):
        out.append(
            text(x0 + colw * index + colw / 2, 96, uf, 12.5, ink, MONO, 700, "middle")
        )
    for r, tema in enumerate(ordem):
        y = top + rowh * r
        out.append(text(x0 - 12, y + 26, tema, 12.5, ink, SANS, 600, "end"))
        for index, uf in enumerate(ufs):
            value = dict(DATA["temas"][uf]).get(tema, 0)
            size = 6 + 20 * (value / 54) ** 0.72
            cx = x0 + colw * index + colw / 2
            out.append(circle(cx, y + 20, size, cores[tema]))
            if value >= 10:
                out.append(
                    text(cx, y + 25, str(value), 11.5, "#ffffff", MONO, 700, "middle")
                )
    out.append(
        text(
            28,
            height - 30,
            "Saúde lidera em 11 dos 14 estados. Violência lidera no Ceará (54), na Bahia (38) e empata na Paraíba. Infraestrutura só aparece no topo no Maranhão (21).",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 10,
            "Fonte: relatórios estaduais Quaest, página declarada no dossiê.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Tema mais citado como maior problema do estado, por estado",
    )


# ----------------------------------------------------------------- figura 6
def fig_aliado(dark=False, width=1000, height=560) -> str:
    """Quem o eleitor quer que o proximo governador seja aliado."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    rows = [(p["uf"], p["aliado"]) for p in DATA["pesquisas"] if "aliado" in p]
    rows.sort(key=lambda r: -r[1]["Flávio"])
    x0, x1 = 92, width - 40
    top, step = 110, (height - 170) / len(rows)
    out = [
        text(
            28,
            30,
            "Aliado de quem? A pergunta que mede o rabo da chapa",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "De modo geral, você gostaria que a pessoa eleita governador fosse aliada do Lula, aliada de Flávio Bolsonaro ou independente?",
            13,
            faint,
            SANS,
        ),
        text(x0, 92, "Flávio", 12, FLAVIO_DARK if dark else FLAVIO, MONO, 700),
        text(x0 + 90, 92, "Independente", 12, GOLD_DARK if dark else GOLD, MONO, 700),
        text(x0 + 240, 92, "Lula", 12, LULA_DARK if dark else LULA, MONO, 700),
    ]
    for index, (uf, item) in enumerate(rows):
        y = top + step * index
        cursor = x0
        for key, colour in (
            ("Flávio", FLAVIO_DARK if dark else FLAVIO),
            ("Independente", GOLD_DARK if dark else GOLD),
            ("Lula", LULA_DARK if dark else LULA),
            ("NS/NR", GREY),
        ):
            w = (x1 - x0) * item[key] / 100
            out.append(rect(cursor, y, w, step * 0.62, colour, 1.5, "bar-fill"))
            if item[key] >= 12:
                out.append(
                    text(
                        cursor + w / 2,
                        y + step * 0.44,
                        str(item[key]),
                        12,
                        "#ffffff",
                        MONO,
                        700,
                        "middle",
                    )
                )
            cursor += w
        out.append(text(28, y + step * 0.44, uf, 13.5, ink, MONO, 700))
    out.append(
        text(
            28,
            height - 36,
            "No Acre, em Rondônia e em Roraima, o eleitor quer o governador aliado de Flávio. Na Bahia, no Ceará, na Paraíba e no Maranhão, a soma de independente com Lula passa de 75%.",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 12,
            "Fonte: relatórios estaduais Quaest, página declarada no dossiê.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg(
        "".join(out),
        width,
        height,
        "Preferência por governador aliado de Lula, de Flávio ou independente",
    )


# ----------------------------------------------------------------- figura 7
def fig_matopiba(dark=False, width=1000, height=430) -> str:
    """A rota do agro comparada a uma unica cidade."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    mat = DATA["matopiba"]
    manaus = next(c for c in DATA["capitais"] if c["municipio"] == "Manaus")
    fortaleza = next(c for c in DATA["capitais"] if c["municipio"] == "Fortaleza")
    itens = [
        (
            f"MATOPIBA, {mat['municipios']} cidades",
            mat["bolsonaro_2t"],
            mat["bolsonaro_2t_pct"],
            GOLD_DARK if dark else GOLD,
        ),
        (
            "Manaus, uma cidade",
            manaus["bolsonaro_2t"],
            manaus["bolsonaro_2t_pct"],
            GREEN,
        ),
        (
            "Fortaleza, uma cidade",
            fortaleza["bolsonaro_2t"],
            fortaleza["bolsonaro_2t_pct"],
            FLAVIO_DARK if dark else FLAVIO,
        ),
    ]
    maxi = max(i[1] for i in itens)
    x0, x1 = 300, width - 220
    top, step = 128, 76
    out = [
        text(
            28,
            30,
            "A rota do cerrado vale menos que uma tarde em Manaus",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Votos de Bolsonaro no 2º turno de 2022. O MATOPIBA soma 38 municípios de Bahia, Maranhão, Piauí e Tocantins.",
            13,
            faint,
            SANS,
        ),
    ]
    for index, (label, votes, share, colour) in enumerate(itens):
        y = top + step * index
        w = (x1 - x0) * votes / maxi
        out.append(rect(x0, y, w, 40, colour, 3, "bar-fill"))
        out.append(text(x0 - 14, y + 26, label, 14, ink, SANS, 600, "end"))
        out.append(
            text(
                x0 + w + 14,
                y + 26,
                f"{fmt(votes / 1000)} mil   {fmt(share, 1)}%",
                13,
                colour,
                MONO,
                700,
            )
        )
    out.append(
        text(
            28,
            height - 46,
            f"O MATOPIBA tem {fmt(mat['eleitores_2026'] / 1000)} mil eleitores em 2026 e dá 43,4% a Bolsonaro. É território amigo, e é pequeno.",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 24,
            "A escolha entre os dois não é ideológica: é de calendário. Uma agenda no cerrado custa o mesmo dia que uma agenda na maior cidade bolsonarista das duas regiões.",
            12.5,
            faint,
            SANS,
        )
    )
    out.append(
        text(
            28,
            height - 6,
            "Fonte: TSE, 2º turno de 2022. Delimitação do MATOPIBA: Embrapa.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg("".join(out), width, height, "MATOPIBA comparado a Manaus e Fortaleza")


# ----------------------------------------------------------------- figura 8
def fig_troca(dark=False, width=1000, height=400) -> str:
    """As duas trocas de agenda da semana, medidas em voto de 2022."""
    ink = INK_DARK if dark else INK
    faint = FAINT_DARK if dark else MUTED
    index = {(c["uf"], c["municipio"]): c for c in DATA["alvos"]}
    salvador = index[("BA", "Salvador")]
    conquista = index[("BA", "Vitória da Conquista")]
    recife = index[("PE", "Recife")]
    pares = [
        (
            "Bahia, 17/09",
            "Salvador, trocada",
            salvador,
            "Vitória da Conquista, escolhida",
            conquista,
        ),
        (
            "Pernambuco, 16/09",
            "Recife, escolhida",
            recife,
            "Santa Cruz do Capibaribe, retirada",
            None,
        ),
    ]
    out = [
        text(
            28,
            30,
            "As duas trocas de agenda da semana, medidas em voto",
            19,
            ink,
            SANS,
            700,
        ),
        text(
            28,
            54,
            "Votos de Bolsonaro no 2º turno de 2022 em cada cidade. A escolha da Bahia troca o maior estoque do estado por um quinto dele.",
            13,
            faint,
            SANS,
        ),
    ]
    maxi = salvador["bolsonaro_2t"]
    x0, x1 = 330, width - 170
    y = 104
    for titulo, rot_a, a, rot_b, b in pares:
        out.append(text(28, y + 4, titulo, 13, ink, MONO, 700))
        for rot, item, colour in (
            (rot_a, a, LULA_DARK if dark else LULA),
            (rot_b, b, GREEN),
        ):
            votes = item["bolsonaro_2t"] if item else 26632
            share = item["bolsonaro_2t_pct"] if item else 52.1
            w = (x1 - x0) * votes / maxi
            out.append(rect(x0, y, w, 30, colour, 3, "bar-fill"))
            out.append(text(x0 - 14, y + 20, rot, 12.5, ink, SANS, 600, "end"))
            out.append(
                text(
                    x0 + w + 12,
                    y + 20,
                    f"{fmt(votes / 1000)} mil  ({fmt(share, 1)}%)",
                    12,
                    colour,
                    MONO,
                    600,
                )
            )
            y += 42
        y += 26
    out.append(
        text(
            28,
            height - 46,
            "Santa Cruz do Capibaribe é o único município de Pernambuco que Bolsonaro venceu em 2022, e tem 26 mil votos dele. Sair de lá para o Recife foi acerto de volume.",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 24,
            "Salvador tem 5,4 vezes o voto de Vitória da Conquista. Trocar uma pela outra é escolher o palanque confortável em vez do estoque.",
            12.5,
            ink,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            height - 6,
            "Fonte: TSE 2022. Agenda: A Tarde, Diario de Pernambuco e O Povo, com link no capítulo de fontes.",
            11.5,
            faint,
            SANS,
        )
    )
    return svg("".join(out), width, height, "Trocas de agenda medidas em voto de 2022")


FIGURES = {
    "vao": fig_vao,
    "nao_visitados": fig_nao_visitados,
    "capitais": fig_capitais,
    "concentracao": fig_concentracao,
    "temas": fig_temas,
    "aliado": fig_aliado,
    "matopiba": fig_matopiba,
    "troca": fig_troca,
}


if __name__ == "__main__":
    for name, builder in FIGURES.items():
        print(name, len(builder()), "bytes")
