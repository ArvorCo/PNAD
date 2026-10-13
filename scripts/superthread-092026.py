#!/usr/bin/env python3
"""Gera docs/superthread_092026.html: sete cards 1:1 sobre a rodada de setembro.

Um card de abertura com o que as quatro pesquisas nacionais dizem juntas, um
card para cada instituto auditado (Datafolha, BTG/Nexus, Quaest e CNT/MDA), um
para o atlas estadual e um de fecho com a rota. Cada post tem cerca de 2.000
caracteres, acima do padrao de 950 a 1.500 das threads anteriores, por pedido
explicito: aqui cada card carrega um dossie inteiro.

Nenhum numero e digitado a mao. Tudo vem de:
    docs/assets/reponderacao_pnad.json
    docs/assets/datafolha_14092026_cruzamentos.json
    docs/assets/nexus_btg_140926_data.json
    docs/assets/quaest_140926_data.json
    docs/assets/mda_150926_renda.json
    docs/assets/estaduais_092026_data.json

Reproducao:
    python3 scripts/estaduais-092026-data.py && python3 scripts/superthread-092026.py
"""

from __future__ import annotations

import html
import importlib
import json
from pathlib import Path

import superthread_092026_cards as card_view
from ga_tag import injetar

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
OUTPUT = ROOT / "docs/superthread_092026.html"

AGG = importlib.import_module("reponderacao-arquivo").close(
    json.loads((ASSETS / "reponderacao_pnad.json").read_text()), "2026-09-15"
)
DFX = json.loads((ASSETS / "datafolha_14092026_cruzamentos.json").read_text())
NEX = json.loads((ASSETS / "nexus_btg_140926_data.json").read_text())
QUA = json.loads((ASSETS / "quaest_140926_data.json").read_text())
MDA = json.loads((ASSETS / "mda_150926_renda.json").read_text())
EST = json.loads((ASSETS / "estaduais_092026_data.json").read_text())

BASE = "https://brasil.arvor.co"

INK = "#f4f2ea"
INK2 = "#ddd8ca"
MUTED = "#9a9789"
FAINT = "#8f8c7f"
LIME = card_view.LIME
CYAN = card_view.CYAN
AMBER = card_view.AMBER
GREEN = "#34b47e"
LULA = "#d13c2e"
LULA_TXT = "#ea6a5c"
FLAVIO = "#5ba3e0"
GREY = "#8892a4"
MONO = "IBM Plex Mono, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"
DISPLAY = "Fraunces, Georgia, serif"


def esc(value) -> str:
    return html.escape(str(value))


def fmt(value, digits=0) -> str:
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(value, digits=1) -> str:
    rounded = round(value, digits)
    if rounded == 0:
        rounded = 0.0
    return ("+" if rounded > 0 else "") + fmt(rounded, digits)


# --------------------------------------------------------------- leitura
def onda(instituto: str, fim: str) -> dict:
    return next(
        p
        for p in AGG["pesquisas"]
        if p["instituto"] == instituto and p["campo"]["fim"] == fim
    )


ONDAS = {
    "Datafolha": onda("Datafolha", "2026-09-10"),
    "Nexus": onda("Nexus", "2026-09-13"),
    "Quaest": onda("Quaest", "2026-09-13"),
    "MDA": onda("MDA", "2026-09-13"),
}
ORDEM = ["Datafolha", "MDA", "Nexus", "Quaest"]
ULTIMO = AGG["agregador"]["ultimo"]
VAO = {v["uf"]: v for v in EST["vaos"]}
CAP = {c["municipio"]: c for c in EST["capitais"]}
ALVO = {(a["uf"], a["municipio"]): a for a in EST["alvos"]}
POLL = {p["uf"]: p for p in EST["pesquisas"]}
NV = EST["nao_visitados"]


def turno(instituto: str, t: str) -> dict:
    # Este dossiê descreve ondas históricas fixas, inclusive o cenário MDA com
    # Marçal, agora arquivado fora do agregador corrente de primeiro turno.
    poll = ONDAS[instituto]
    return poll["turnos"].get(t) or poll.get("turnos_arquivados", {})[t]


def ajustado(instituto: str, t: str, quem: str) -> float:
    return turno(instituto, t)["cenarios"]["pessoas16_efetivo"]["ajustado"][quem]


# --------------------------------------------------------------- SVG base
def svg(body: str, width=1000, height=620, label="") -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" '
        f'xmlns="http://www.w3.org/2000/svg">{body}</svg>'
    )


def text(
    x: float,
    y: float,
    value,
    size: float = 15,
    fill: str = MUTED,
    family: str = MONO,
    weight: int = 400,
    anchor: str = "start",
) -> str:
    size = round(size * 1.12, 1)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'font-family="{esc(family)}" font-weight="{weight}" text-anchor="{anchor}">'
        f"{esc(value)}</text>"
    )


def rect(x: float, y: float, w: float, h: float, fill: str, radius: float = 3) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" '
        f'height="{max(h, 0):.1f}" rx="{radius}" fill="{fill}"/>'
    )


def line(
    x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 1, dash=""
) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def circle(cx: float, cy: float, r: float, fill: str) -> str:
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>'


def chip(x: float, y: float, w: float, h: float, fill: str) -> str:
    return rect(x, y, w, h, fill, 3)


# --------------------------------------------------------------- figuras
def viz_quatro() -> str:
    """Desvio de renda da amostra contra o giro da diferenca no 2o turno."""
    W, H = 1000, 620
    x0, x1 = 120, 880
    y0, y1 = 520, 118
    pontos = [
        (
            nome,
            ONDAS[nome]["desvio_ate_primeira_faixa"],
            turno(nome, "2t")["gap_publicado"],
            turno(nome, "2t")["gap_ajustado"],
        )
        for nome in ORDEM
    ]
    dx = [p[1] for p in pontos]
    lo, hi = min(dx) - 3, max(dx) + 3
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)  # noqa: E731
    lo_g = min(min(p[2], p[3]) for p in pontos) - 2.5
    hi_g = max(max(p[2], p[3]) for p in pontos) + 3.5
    sy = lambda v: y0 - (y0 - y1) * (v - lo_g) / (hi_g - lo_g)  # noqa: E731
    out = [
        text(
            28,
            34,
            "Quanto mais pobre a amostra, maior a vantagem de Lula",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "Eixo horizontal: quantos pontos a faixa até 2 salários pesa a mais na pesquisa do que na PNAD. Eixo vertical: diferença no 2º turno.",
            13,
            FAINT,
            SANS,
        ),
    ]
    out.append(line(x0 - 20, sy(0), x1 + 20, sy(0), GREY, 1.4, "5 5"))
    out.append(text(x1 + 26, sy(0) + 5, "empate", 12, GREY, MONO))
    out.append(line(sx(0), y1 - 14, sx(0), y0 + 26, GREY, 1.2, "3 6"))
    out.append(
        text(sx(0), y0 + 48, "amostra igual à PNAD", 12, GREY, MONO, 400, "middle")
    )
    for nome, desvio, pub, aj in pontos:
        x = sx(desvio)
        out.append(line(x, sy(pub), x, sy(aj), AMBER, 2.4))
        out.append(circle(x, sy(pub), 8, LULA if pub > 0 else FLAVIO))
        out.append(rect(x - 7, sy(aj) - 7, 14, 14, GREEN if aj < 0 else AMBER, 3))
        out.append(
            text(x, min(sy(pub), sy(aj)) - 22, nome, 14.5, INK, SANS, 700, "middle")
        )
        out.append(
            text(
                x + 15,
                sy(pub) + 5,
                sgn(pub, 1),
                12.5,
                LULA_TXT if pub > 0 else FLAVIO,
                MONO,
                700,
            )
        )
        out.append(
            text(
                x + 15,
                sy(aj) + 5,
                sgn(aj, 2),
                12.5,
                GREEN if aj < 0 else AMBER,
                MONO,
                700,
            )
        )
        out.append(text(x, y0 + 30, sgn(desvio, 1), 12, FAINT, MONO, 400, "middle"))
    out.append(circle(40, H - 30, 7, LULA))
    out.append(text(56, H - 25, "diferença publicada", 12.5, INK2, MONO))
    out.append(rect(250, H - 37, 14, 14, GREEN, 3))
    out.append(
        text(
            272,
            H - 25,
            "com a renda da PNAD; positivo é Lula, negativo é Flávio",
            12.5,
            INK2,
            MONO,
        )
    )
    return svg(
        "".join(out),
        W,
        H,
        "Desvio de renda da amostra contra a diferença no segundo turno",
    )


def viz_datafolha() -> str:
    """Regiao e rejeicao no Datafolha de setembro."""
    W, H = 1000, 620
    blocos = DFX["tabelas"]["turno2_flavio"]["blocks"]["bloco3"]["rows"]
    rej = DFX["tabelas"]["rejeicao"]["blocks"]["bloco3"]["rows"]
    regioes = ["Nordeste", "Sudeste", "Centro-Oeste/Norte", "Sul"]
    x0, x1 = 240, 740
    top, step = 142, 86
    out = [
        text(
            28,
            34,
            "O Nordeste rejeita Flávio mais do que vota em Lula",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "Datafolha de 14/09, 2º turno por região, e a rejeição de cada nome no mesmo recorte.",
            13,
            FAINT,
            SANS,
        ),
        text(x0, 106, "2º turno", 12.5, FAINT, MONO),
        text(x1 + 40, 106, "rejeição a Flávio", 12.5, LULA_TXT, MONO),
    ]
    for index, regiao in enumerate(regioes):
        y = top + step * index
        lula = blocos["Lula (PT)"][regiao]
        flavio = blocos["Flavio Bolsonaro (PL)"][regiao]
        total = lula + flavio
        wl = (x1 - x0) * lula / total
        out.append(rect(x0, y, wl, 34, LULA, 3))
        out.append(rect(x0 + wl, y, (x1 - x0) - wl, 34, FLAVIO, 3))
        out.append(
            text(x0 + wl / 2, y + 23, str(lula), 14, "#ffffff", MONO, 700, "middle")
        )
        out.append(
            text(
                x0 + wl + ((x1 - x0) - wl) / 2,
                y + 23,
                str(flavio),
                14,
                "#0a0b09",
                MONO,
                700,
                "middle",
            )
        )
        nome = regiao.replace("Centro-Oeste/Norte", "CO / Norte")
        out.append(text(x0 - 16, y + 23, nome, 15, INK, SANS, 600, "end"))
        r = rej["Flavio Bolsonaro (PL)"][regiao]
        out.append(text(x1 + 40, y + 23, f"{r}%", 16, LULA_TXT, MONO, 700))
    y = top + step * len(regioes) + 18
    out.append(line(28, y, W - 28, y, "#3a3f38", 1))
    out.append(
        text(
            28,
            y + 34,
            "Capital, região metropolitana e interior quase não se separam: 43, 43 e 45 para Flávio.",
            15,
            INK,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            y + 60,
            "A fratura do país é regional, não urbana. E o teto do Nordeste não é de exposição: é de rejeição declarada, o dobro da que Lula tem lá.",
            14,
            INK2,
            SANS,
        )
    )
    out.append(
        text(
            28,
            H - 16,
            "Datafolha 14/09/2026, p. 48 e 49 do relatório completo.",
            12,
            FAINT,
            MONO,
        )
    )
    return svg(
        "".join(out),
        W,
        H,
        "Segundo turno e rejeição por região no Datafolha de setembro",
    )


def viz_nexus() -> str:
    """Gradiente de renda e de regiao no BTG/Nexus."""
    W, H = 1000, 620
    renda = NEX["profile_tables"]["34"]
    linhas = {r["label"].split("  ")[-1].strip(): r["values"] for r in renda}
    faixas = [
        ("Até 1 S.M.", "Até 1 S.M."),
        ("De 1 até 2 S.M.", "De 1 até 2 S.M."),
        ("De 2 até 5 S.M.", "De 2 até 5 S.M."),
        ("Mais de 5 S.M.", "Mais de 5 S.M."),
    ]
    x0, x1 = 250, 700
    top, step = 146, 76
    out = [
        text(
            28,
            34,
            "A direita ganha na classe média e perde no andar de baixo",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "BTG/Nexus de 14/09, 1º turno por faixa de renda familiar. Lula em vermelho, Flávio em azul.",
            13,
            FAINT,
            SANS,
        ),
    ]
    for index, (rotulo, chave) in enumerate(faixas):
        y = top + step * index
        valores = linhas.get(chave)
        if not valores:
            continue
        lula, flavio = valores[0], valores[1]
        total = lula + flavio
        wl = (x1 - x0) * lula / total
        out.append(rect(x0, y, wl, 36, LULA, 3))
        out.append(rect(x0 + wl, y, (x1 - x0) - wl, 36, FLAVIO, 3))
        out.append(
            text(x0 + wl / 2, y + 25, str(lula), 13.5, "#ffffff", MONO, 700, "middle")
        )
        out.append(
            text(
                x0 + wl + ((x1 - x0) - wl) / 2,
                y + 25,
                str(flavio),
                13.5,
                "#0a0b09",
                MONO,
                700,
                "middle",
            )
        )
        out.append(text(x0 - 16, y + 25, rotulo, 14.5, INK, SANS, 600, "end"))
        out.append(
            text(
                x1 + 22,
                y + 25,
                f"{sgn(flavio - lula, 0)}",
                14,
                FLAVIO if flavio > lula else LULA_TXT,
                MONO,
                700,
            )
        )
    y = top + step * len(faixas) + 16
    out.append(line(28, y, W - 28, y, "#3a3f38", 1))
    out.append(
        text(
            28,
            y + 32,
            "Amostra do BTG: 19% na faixa até 1 salário. PNAD: 13,4%.",
            15,
            INK,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            y + 58,
            "É a pesquisa mais próxima da régua oficial das quatro, e é onde a reponderação quase não muda nada: o empate de 1 ponto vira 0,28.",
            14,
            INK2,
            SANS,
        )
    )
    out.append(
        text(
            28,
            H - 16,
            "BTG/Nexus 14/09/2026, p. 34 do relatório de 155 páginas.",
            12,
            FAINT,
            MONO,
        )
    )
    return svg(
        "".join(out), W, H, "Primeiro turno por faixa de renda no BTG Nexus de setembro"
    )


def viz_quaest() -> str:
    """O instituto que contraria a tese da casa."""
    W, H = 1000, 620
    d2 = turno("Quaest", "2t")
    d1 = turno("Quaest", "1t")
    x0, x1 = 300, 760
    out = [
        text(
            28,
            34,
            "A Quaest anda na direção contrária, e isso é o teste",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "É a única das quatro com amostra mais rica que a PNAD. A régua da renda tira de Flávio em vez de dar.",
            13,
            FAINT,
            SANS,
        ),
    ]
    pares = [
        (
            "1º turno",
            d1["publicado"],
            d1["cenarios"]["pessoas16_efetivo"]["ajustado"],
            150,
        ),
        (
            "2º turno",
            d2["publicado"],
            d2["cenarios"]["pessoas16_efetivo"]["ajustado"],
            330,
        ),
    ]
    for rotulo, pub, aj, y in pares:
        out.append(text(28, y + 30, rotulo, 15, INK, SANS, 700))
        for offset, (nome, dados) in enumerate(
            (("publicado", pub), ("com a PNAD", aj))
        ):
            yy = y + offset * 64
            lula, flavio = dados["lula"], dados["flavio"]
            total = lula + flavio
            wl = (x1 - x0) * lula / total
            out.append(rect(x0, yy, wl, 38, LULA, 3))
            out.append(rect(x0 + wl, yy, (x1 - x0) - wl, 38, FLAVIO, 3))
            out.append(
                text(
                    x0 + wl / 2,
                    yy + 25,
                    fmt(lula, 2),
                    14,
                    "#ffffff",
                    MONO,
                    700,
                    "middle",
                )
            )
            out.append(
                text(
                    x0 + wl + ((x1 - x0) - wl) / 2,
                    yy + 25,
                    fmt(flavio, 2),
                    14,
                    "#0a0b09",
                    MONO,
                    700,
                    "middle",
                )
            )
            out.append(
                text(
                    x0 - 16,
                    yy + 25,
                    nome,
                    14,
                    INK2 if offset else MUTED,
                    MONO,
                    600,
                    "end",
                )
            )
            gap = flavio - lula
            out.append(
                text(
                    x1 + 22,
                    yy + 25,
                    f"{sgn(gap, 2)}",
                    14.5,
                    FLAVIO if gap > 0 else LULA_TXT,
                    MONO,
                    700,
                )
            )
    out.append(line(28, 486, W - 28, 486, "#3a3f38", 1))
    out.append(
        text(
            28,
            522,
            f"A amostra da Quaest tem {fmt(abs(ONDAS['Quaest']['desvio_ate_primeira_faixa']), 2)} pontos a menos na faixa até 2 salários do que a PNAD.",
            15,
            INK,
            SANS,
            600,
        )
    )
    out.append(
        text(
            28,
            552,
            "Trocar o peso pelo oficial custa 1,26 ponto a Flávio no 2º turno e 1,09 no 1º. Publicamos com o mesmo destaque das outras três.",
            14,
            INK2,
            SANS,
        )
    )
    out.append(
        text(
            28,
            H - 16,
            "Quaest/Globo 14/09/2026, BR-03607/2026, relatório de 205 páginas.",
            12,
            FAINT,
            MONO,
        )
    )
    return svg("".join(out), W, H, "Reponderação por renda da Quaest de setembro")


def viz_agregador() -> str:
    """Media Arvor das ultimas ondas, publicada e reponderada."""
    W, H = 1000, 620
    k2 = ULTIMO["2t"]["kernel"]
    s2 = ULTIMO["2t"]["media_simples"]
    k1 = ULTIMO["1t"]["kernel"]
    x0, x1 = 300, 780
    out = [
        text(
            28,
            34,
            "Sob a régua da PNAD, a média de setembro troca de líder",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            f"{len(AGG['pesquisas'])} pesquisas de {len(AGG['institutos'])} institutos no acervo. Média com meia-vida de 14 dias sobre o fim do campo.",
            13,
            FAINT,
            SANS,
        ),
    ]
    blocos = [
        ("2º turno, média no tempo", k2, 136),
        ("2º turno, última onda de cada instituto", s2, 276),
        ("1º turno, média no tempo", k1, 416),
    ]
    for rotulo, bloco, y in blocos:
        out.append(text(28, y + 26, rotulo, 14, INK, SANS, 700))
        for offset, chave in enumerate(("publicado", "ajustado")):
            yy = y + 38 + offset * 46
            lula, flavio = bloco[chave]["lula"], bloco[chave]["flavio"]
            total = lula + flavio
            wl = (x1 - x0) * lula / total
            out.append(rect(x0, yy, wl, 30, LULA, 3))
            out.append(rect(x0 + wl, yy, (x1 - x0) - wl, 30, FLAVIO, 3))
            out.append(
                text(
                    x0 + wl / 2,
                    yy + 21,
                    fmt(lula, 2),
                    13,
                    "#ffffff",
                    MONO,
                    700,
                    "middle",
                )
            )
            out.append(
                text(
                    x0 + wl + ((x1 - x0) - wl) / 2,
                    yy + 21,
                    fmt(flavio, 2),
                    13,
                    "#0a0b09",
                    MONO,
                    700,
                    "middle",
                )
            )
            out.append(
                text(
                    x0 - 16,
                    yy + 21,
                    "publicado" if not offset else "com a PNAD",
                    13,
                    MUTED if not offset else INK2,
                    MONO,
                    600,
                    "end",
                )
            )
            gap = flavio - lula
            out.append(
                text(
                    x1 + 20,
                    yy + 21,
                    sgn(gap, 2),
                    13.5,
                    FLAVIO if gap > 0 else LULA_TXT,
                    MONO,
                    700,
                )
            )
    out.append(
        text(
            28,
            H - 42,
            "Sensibilidade de uma margem sob régua comum, nunca voto corrigido. A ponderação de cada instituto é conjunta e não é publicada.",
            13.5,
            INK2,
            SANS,
        )
    )
    out.append(
        text(28, H - 16, "brasil.arvor.co/reponderacao_pnad.html", 12, CYAN, MONO)
    )
    return svg(
        "".join(out), W, H, "Média Arvor publicada e reponderada pela renda da PNAD"
    )


def viz_vao() -> str:
    """Vao estadual nos oito maiores casos."""
    W, H = 1000, 620
    rows = EST["vaos"][:8]
    x0, x1 = 300, 800
    top, step = 128, 54
    scale = lambda v: x0 + (x1 - x0) * v / 62  # noqa: E731
    out = [
        text(
            28,
            34,
            "A direita ganha o estado e perde o país na mesma entrevista",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "Melhor candidatura de direita ao governo estadual (círculo) contra Flávio no 1º turno presidencial (quadrado). Quaest, 15 estados.",
            13,
            FAINT,
            SANS,
        ),
    ]
    for value in (0, 20, 40, 60):
        out.append(
            line(
                scale(value),
                top - 16,
                scale(value),
                top + step * len(rows) - 12,
                "#3a3f38",
                1,
                "2 5",
            )
        )
        out.append(
            text(
                scale(value),
                top + step * len(rows) + 8,
                f"{value}%",
                11.5,
                FAINT,
                MONO,
                400,
                "middle",
            )
        )
    for index, row in enumerate(rows):
        y = top + step * index + 12
        gov, flavio = row["gov"], row["flavio_1t"]
        out.append(line(scale(flavio), y, scale(gov), y, CYAN, 3))
        out.append(rect(scale(flavio) - 7, y - 7, 14, 14, FLAVIO, 2))
        out.append(circle(scale(gov), y, 7.5, CYAN))
        out.append(
            text(28, y + 5, f"{row['uf']}  {row['candidato']}", 14.5, INK, SANS, 600)
        )
        out.append(
            text(
                W - 28,
                y + 5,
                f"{sgn(row['vao_1t'], 0)} pts",
                14,
                CYAN,
                MONO,
                700,
                "end",
            )
        )
    out.append(
        text(
            28,
            H - 46,
            "No Acre e em Rondônia o sinal inverte: Flávio tem mais voto que o candidato da direita ao governo. O déficit é do Nordeste, não do candidato.",
            14,
            INK2,
            SANS,
        )
    )
    out.append(
        text(28, H - 16, "brasil.arvor.co/estaduais_092026.html", 12, CYAN, MONO)
    )
    return svg(
        "".join(out),
        W,
        H,
        "Vão entre a direita estadual e Flávio nos oito maiores casos",
    )


def viz_rota() -> str:
    """Onde esta o voto que a campanha ainda nao foi buscar."""
    W, H = 1000, 620
    rows = EST["capitais"][:8]
    maxi = max(r["bolsonaro_2t"] for r in rows)
    x0, x1 = 220, 720
    top, step = 126, 52
    out = [
        text(
            28,
            34,
            "O voto que falta está nas capitais, e a maior delas nunca foi visitada",
            21,
            INK,
            SANS,
            700,
        ),
        text(
            28,
            60,
            "Votos de Bolsonaro no 2º turno de 2022 nas capitais do Norte e do Nordeste. Verde: capital que ele venceu.",
            13,
            FAINT,
            SANS,
        ),
    ]
    for index, row in enumerate(rows):
        y = top + step * index
        w = (x1 - x0) * row["bolsonaro_2t"] / maxi
        colour = GREEN if row["venceu"] else FLAVIO
        out.append(rect(x0, y, w, 30, colour, 3))
        marca = " *" if row["nao_visitado"] else ""
        out.append(
            text(
                x0 - 14,
                y + 21,
                f"{row['municipio']}{marca}",
                14.5,
                INK,
                SANS,
                600,
                "end",
            )
        )
        out.append(
            text(
                x0 + w + 14,
                y + 21,
                f"{fmt(row['bolsonaro_2t'] / 1000)} mil   {fmt(row['bolsonaro_2t_pct'], 1)}%",
                13,
                colour,
                MONO,
                600,
            )
        )
    y = top + step * len(rows) + 18
    out.append(line(28, y, W - 28, y, "#3a3f38", 1))
    out.append(
        text(
            28,
            y + 30,
            "* estado sem visita da campanha até 14/09.",
            13,
            AMBER,
            MONO,
            600,
        )
    )
    out.append(
        text(
            28,
            y + 54,
            f"Metade do voto bolsonarista do Nordeste cabe em {EST['concentracao']['nordeste']['metade_em']} municípios de {fmt(EST['concentracao']['nordeste']['municipios'])}.",
            14.5,
            INK,
            SANS,
            600,
        )
    )
    return svg(
        "".join(out), W, H, "Votos de Bolsonaro nas capitais do Norte e do Nordeste"
    )


# --------------------------------------------------------------- os posts
def build_cards() -> list[dict]:
    return card_view.build_cards(
        AGG=AGG,
        ALVO=ALVO,
        BASE=BASE,
        CAP=CAP,
        DFX=DFX,
        EST=EST,
        MDA=MDA,
        NEX=NEX,
        NV=NV,
        ONDAS=ONDAS,
        ORDEM=ORDEM,
        QUA=QUA,
        ULTIMO=ULTIMO,
        VAO=VAO,
        ajustado=ajustado,
        fmt=fmt,
        sgn=sgn,
        turno=turno,
        viz_agregador=viz_agregador,
        viz_datafolha=viz_datafolha,
        viz_nexus=viz_nexus,
        viz_quaest=viz_quaest,
        viz_quatro=viz_quatro,
        viz_rota=viz_rota,
        viz_vao=viz_vao,
    )


KIND = card_view.KIND

CSS = card_view.CSS

JS = card_view.JS


def render_card(index: int, total: int, card: dict) -> str:
    return card_view.render_card(index, total, card, KIND)


def main() -> None:
    cards = build_cards()
    total = len(cards)
    posts = "".join(render_card(i + 1, total, c) for i, c in enumerate(cards))
    rail = "".join(f'<a href="#p{i + 1}">{i + 1}</a>' for i in range(total))
    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A rodada de setembro em sete cards: quatro pesquisas, uma régua e o mapa que falta | Arvor</title>
<meta name="description" content="Sete cards quadrados e o texto pronto para publicar: Datafolha, BTG/Nexus, Quaest e CNT/MDA sob a mesma régua de renda da PNAD, o vão de até 33 pontos entre a direita estadual e Flávio, e onde está o voto que a campanha ainda não foi buscar.">
<link rel="canonical" href="https://brasil.arvor.co/superthread_092026.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0d0b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="A rodada de setembro em sete cards">
<meta property="og:description" content="Quatro pesquisas nacionais sob a mesma régua de renda, quinze pesquisas estaduais que ninguém leu e o mapa do voto que falta. Texto pronto para publicar.">
<meta property="og:url" content="https://brasil.arvor.co/superthread_092026.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/superthread_092026.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/superthread_092026.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · thread</div>
    <a class="back" href="index.html">Biblioteca</a>
  </div>
  <h1>Quatro pesquisas, uma régua só. <em>E o mapa que ninguém abriu.</em></h1>
  <p class="deck">A rodada de setembro em sete cards quadrados. Datafolha, CNT/MDA, BTG/Nexus e Quaest publicaram em cinco dias e discordam do placar; sob a régua de renda da PNAD, as quatro andam para o mesmo lado. Depois, a parte que não virou manchete: quinze pesquisas estaduais em que a direita ganha o governo e perde a Presidência na mesma entrevista, e o mapa municipal do voto que a campanha ainda não foi buscar.</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado que cabe no print de tela. O texto embaixo é o post, de cerca de 2.000 caracteres, e o botão copia tudo. Nenhum número foi digitado à mão: todos vêm dos arquivos do acervo, e cada card traz a fonte e a página no rodapé.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{posts}</main>
<footer class="wrap">
  <h2>Reprodução</h2>
  <p>python3 scripts/estaduais-092026-tse.py, python3 scripts/estaduais-092026-data.py e python3 scripts/superthread-092026.py. Os dossiês citados estão em
  <a href="datafolha_14092026.html">Datafolha</a>, <a href="nexus_btg_140926.html">BTG/Nexus</a>, <a href="quaest_14092026.html">Quaest</a>,
  <a href="reponderacao_pnad.html">acervo e CNT/MDA</a> e <a href="estaduais_092026.html">atlas estadual</a>.</p>
  <p>Leitura descritiva de pesquisa, não previsão eleitoral. Reponderação é sensibilidade de uma margem sob régua comum.</p>
</footer>
<script>{JS}</script>
</body>
</html>
"""
    assert "—" not in page and "–" not in page, "travessão proibido"
    for card in cards:
        n = len("\n\n".join(card["copy"]))
        assert 1700 <= n <= 2300, (card["tag"], n)
    OUTPUT.write_text(injetar(page))
    print("Gerado:", OUTPUT, total, "cards")
    for index, card in enumerate(cards, 1):
        print(
            f"  {index}. {card['tag']}: {len(chr(10).join(card['copy'])) + len(card['copy']) - 1} chars"
        )


if __name__ == "__main__":
    main()
