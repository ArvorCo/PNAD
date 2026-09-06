#!/usr/bin/env python3
"""Gera docs/sp_092026_thread.html: a thread do atlas de São Paulo em nove cards 1:1.

Cinco pontos, cada um com o gráfico certo e o texto copiável embaixo. Nada é
digitado à mão: placares, fluxos, estoque, excedente de Pontes e índices vêm de
docs/assets/sp_092026_camada2.json e docs/assets/sp_092026_pesquisas.json.

Reprodução:
    python3 scripts/sp-092026-camada2.py && python3 scripts/sp-092026-thread.py
"""

from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
OUTPUT = ROOT / "docs/sp_092026_thread.html"
K = json.loads((ASSETS / "sp_092026_camada2.json").read_text())
P = json.loads((ASSETS / "sp_092026_pesquisas.json").read_text())
FLOWS = {f["nome"].split(":")[0]: f for f in K["fluxos"]}
F3 = {f["nome"].split(":")[0]: f for f in K["fluxos3"]["fluxos"]}
MICRO = K["micro"]
PONTES = K["pontes"]
CORR = K["corredores"]
R = K["reponderacao"]

INK = "#f4f2ea"
INK2 = "#ddd8ca"
MUTED = "#9a9789"
FAINT = "#8f8c7f"
LIME = "#cfe63c"
CYAN = "#45c9c2"
AMBER = "#f0a930"
GREEN = "#34b47e"
LULA = "#e0483a"
LULA_TXT = "#ea6a5c"
FLAVIO = "#3f8fd6"
GREY = "#939cae"
MONO = "IBM Plex Mono, monospace"
SANS = "IBM Plex Sans Condensed, Arial, sans-serif"
DISPLAY = "Fraunces, Georgia, serif"


def fmt(v, n=0):
    return f"{v:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(v, n=1):
    v = round(v, n)
    if v == 0:
        v = 0.0
    return ("+" if v > 0 else "") + fmt(v, n)


def esc(s):
    return html.escape(str(s))


# ------------------------------------------------------------------ SVG helpers
def svg(body, width=1000, height=640, label=""):
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def text(
    x,
    y,
    value,
    size=15,
    fill=MUTED,
    family=MONO,
    weight=400,
    anchor="start",
    halo=False,
):
    h = (
        ' stroke="#0a0b09" stroke-width="6" paint-order="stroke" stroke-linejoin="round"'
        if halo
        else ""
    )
    size = round(size * 1.12)
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-family="{esc(family)}" font-weight="{weight}" text-anchor="{anchor}"{h}>{esc(value)}</text>'


def rect(x, y, w, h, fill, radius=3, opacity=1.0):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" rx="{radius}" fill="{fill}" fill-opacity="{opacity}"/>'


def line(x1, y1, x2, y2, stroke, width=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>'


# ------------------------------------------------------------------ vizes
def viz_dumbbell_vao():
    """Tarcísio no 2º turno estadual e Flávio no 2º turno presidencial, por instituto."""
    rows = []
    for nome, key in (
        ("Datafolha", "Datafolha"),
        ("Atlas", "Atlas"),
        ("Real Time", "Real Time"),
    ):
        f = FLOWS[key]
        rows.append(
            (
                nome,
                f["origem"]["Tarcísio"],
                f["destino"]["Flávio"],
                f["origem"]["Haddad"],
                f["destino"]["Lula"],
            )
        )
    W, H = 1000, 640
    x0, x1 = 210, 900
    sx = lambda v: x0 + (x1 - x0) * v / 60  # noqa: E731
    out = [
        text(
            x0,
            34,
            "TARCÍSIO (GOVERNO 2º) E FLÁVIO (PRESIDÊNCIA 2º), MESMA AMOSTRA",
            15,
            MUTED,
        )
    ]
    for t in (30, 40, 50, 60):
        out.append(line(sx(t), 60, sx(t), H - 120, "rgb(244 242 234 / 14%)"))
        out.append(text(sx(t), H - 98, f"{t}%", 14, FAINT, anchor="middle"))
    y = 110
    for nome, t, fl, h, lu in rows:
        out.append(text(x0 - 18, y + 6, nome, 22, INK, SANS, 600, "end"))
        out.append(text(x0 - 18, y + 30, "vão " + sgn(t - fl), 15, AMBER, anchor="end"))
        out.append(line(sx(fl), y, sx(t), y, INK2, 6))
        out.append(f'<circle cx="{sx(t):.1f}" cy="{y}" r="15" fill="{GREEN}"/>')
        out.append(f'<circle cx="{sx(fl):.1f}" cy="{y}" r="15" fill="{FLAVIO}"/>')
        out.append(text(sx(t) + 24, y + 7, fmt(t, 1), 20, GREEN, MONO, 600))
        out.append(text(sx(fl) - 24, y + 7, fmt(fl, 1), 20, FLAVIO, MONO, 600, "end"))
        y2 = y + 52
        out.append(line(sx(h), y2, sx(lu), y2, INK2, 6))
        out.append(
            f'<circle cx="{sx(h):.1f}" cy="{y2}" r="12" fill="{LULA}" fill-opacity="0.6"/>'
        )
        out.append(f'<circle cx="{sx(lu):.1f}" cy="{y2}" r="12" fill="{LULA}"/>')
        out.append(
            text(sx(h) - 20, y2 + 6, "Haddad " + fmt(h, 1), 15, LULA_TXT, anchor="end")
        )
        out.append(text(sx(lu) + 20, y2 + 6, "Lula " + fmt(lu, 1), 15, LULA_TXT))
        y += 150
    out.append(
        f'<circle cx="{x0}" cy="{H - 50}" r="9" fill="{GREEN}"/>'
        + text(x0 + 18, H - 44, "Tarcísio, governo", 15, INK2)
    )
    out.append(
        f'<circle cx="{x0 + 220}" cy="{H - 50}" r="9" fill="{FLAVIO}"/>'
        + text(x0 + 238, H - 44, "Flávio, Presidência", 15, INK2)
    )
    out.append(
        f'<circle cx="{x0 + 470}" cy="{H - 50}" r="9" fill="{LULA}"/>'
        + text(x0 + 488, H - 44, "Haddad e Lula", 15, INK2)
    )
    out.append(
        text(
            x0,
            H - 14,
            "Fontes: Datafolha p. 6 e Poder360; Atlas p. 12 e 21; Real Time p. 12.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Vão entre Tarcísio e Flávio por instituto")


def viz_stack_destinos():
    """Onde termina o eleitor de Tarcísio: Flávio, Lula, não escolha, por instituto (IPF)."""
    W, H = 1000, 640
    out = [
        text(
            60,
            34,
            "DESTINO DO ELEITOR DE TARCÍSIO NO 2º TURNO PRESIDENCIAL, EM % (IPF)",
            15,
            MUTED,
        )
    ]
    y = 90
    for key in ("Datafolha", "Atlas", "Real Time"):
        e = FLOWS[key]["estimado"]
        parts = [
            (e["tarcisio_para_direita_pct"], FLAVIO, "Flávio"),
            (e["tarcisio_para_esquerda_pct"], LULA, "Lula"),
            (e["tarcisio_para_nao_escolha_pct"], GREY, "nulo ou não sabe"),
        ]
        out.append(text(60, y + 34, key, 24, INK, SANS, 600))
        out.append(
            text(
                60,
                y + 60,
                f"{fmt(100 - e['tarcisio_para_direita_pct'], 1)}% não votam Flávio",
                15,
                AMBER,
            )
        )
        x = 300
        for v, color, _lab in parts:
            w = (W - 400) * v / 100
            out.append(rect(x, y, w, 56, color, 4))
            if w > 70:
                out.append(
                    text(
                        x + w / 2,
                        y + 35,
                        f"{fmt(v, 1)}%",
                        20,
                        "#0c0d0b",
                        MONO,
                        700,
                        "middle",
                    )
                )
            x += w
        out.append(
            text(
                x + 10,
                y + 26,
                f"Lula {fmt(e['tarcisio_para_esquerda_pct'], 1)}%",
                13,
                LULA_TXT,
            )
        )
        out.append(
            text(
                x + 10,
                y + 46,
                f"nulo {fmt(e['tarcisio_para_nao_escolha_pct'], 1)}%",
                13,
                GREY,
            )
        )
        y += 120
    y += 10
    out.append(
        text(
            60,
            y + 10,
            "O que as margens impõem (não depende da prior):",
            16,
            INK2,
            SANS,
            600,
        )
    )
    yy = y + 44
    for key in ("Datafolha", "Atlas", "Real Time"):
        rb = FLOWS[key]["robusto"]
        out.append(
            text(
                60,
                yy,
                f"{key}: Flávio {sgn(-rb['diferenca_tarcisio_menos_direita_pp'], 1)} sobre Tarcísio; Lula {sgn(rb['diferenca_esquerda_menos_haddad_pp'], 1)} sobre Haddad; não escolha {sgn(rb['variacao_nao_escolha_pp'], 1)}.",
                15,
                INK2,
            )
        )
        yy += 28
    lx = 60
    for color, lab in (
        (FLAVIO, "Flávio"),
        (LULA, "Lula"),
        (GREY, "nulo, branco ou não sabe"),
    ):
        out.append(
            rect(lx, H - 46, 18, 14, color, 2) + text(lx + 26, H - 34, lab, 15, INK2)
        )
        lx += 60 + 8.5 * len(lab)
    out.append(
        text(
            60,
            H - 8,
            "Prior empírica: Atlas p. 23, voto de 2022 cruzado com 2026. Fitas estimadas; nós medidos.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Destino do eleitor de Tarcísio")


def viz_sankey3_datafolha():
    f = F3["Datafolha"]
    W, H = 1000, 700
    top, bottom = 70, 610
    xs = (150, 460, 770)
    node_w = 26
    color_of = {
        "Flávio": FLAVIO,
        "Lula": LULA,
        "Tarcísio": GREEN,
        "Haddad": LULA,
        "Não escolha": GREY,
        "Outros": "#7f9aa8",
        "Cury": AMBER,
        "Renan": AMBER,
        "Zema": AMBER,
        "Caiado": AMBER,
        "Marçal": AMBER,
    }
    levels = [f["niveis"]["gov1"], f["niveis"]["pres1"], f["niveis"]["pres2"]]
    out = [
        text(xs[0], 34, "GOVERNADOR 1º", 14, MUTED),
        text(xs[1], 34, "PRESIDENTE 1º", 14, MUTED),
        text(xs[2], 34, "PRESIDENTE 2º", 14, MUTED),
    ]
    pos = []
    labels = []
    for li, level in enumerate(levels):
        scale = (bottom - top - 7 * (len(level) - 1)) / sum(level.values())
        y = top
        cur = {}
        for name, v in level.items():
            h = v * scale
            cur[name] = {"y0": y, "h": h, "in": y, "out": y, "scale": scale}
            out.append(
                rect(xs[li], y, node_w, max(h, 1), color_of.get(name, "#7f9aa8"), 2)
            )
            anchor = "end" if li == 0 else "start"
            lx = xs[li] - 10 if li == 0 else xs[li] + node_w + 10
            fill = INK
            label = f"{name} {fmt(v)}"
            if li == 1:
                labels.append(
                    rect(
                        lx - 6,
                        y + h / 2 - 9,
                        9.6 * len(label) + 12,
                        24,
                        "#0a0b09",
                        4,
                        0.88,
                    )
                )
            (labels if li == 1 else out).append(
                text(lx, y + h / 2 + 6, label, 16, fill, SANS, 600, anchor)
            )
            y += h + 7
        pos.append(cur)

    def ribbon(x1, x2, y1, y2, h, fill, op):
        xm = (x1 + x2) / 2
        return f'<path d="M{x1},{y1:.1f} C{xm},{y1:.1f} {xm},{y2:.1f} {x2},{y2:.1f} L{x2},{y2 + h:.1f} C{xm},{y2 + h:.1f} {xm},{y1 + h:.1f} {x1},{y1 + h:.1f} Z" fill="{fill}" fill-opacity="{op}"/>'

    rib = []
    for o, row in f["estagio1"].items():
        for c, v in row.items():
            if v < 0.1:
                continue
            h1, h2 = v * pos[0][o]["scale"], v * pos[1][c]["scale"]
            y1, y2 = pos[0][o]["out"], pos[1][c]["in"]
            pos[0][o]["out"] += h1
            pos[1][c]["in"] += h2
            rib.append(
                ribbon(
                    xs[0] + node_w,
                    xs[1],
                    y1,
                    y2,
                    (h1 + h2) / 2,
                    GREEN if o == "Tarcísio" else color_of.get(c, GREY),
                    0.85 if o == "Tarcísio" else 0.28,
                )
            )
    for c, row in f["estagio2"].items():
        for d, v in row.items():
            vt = f["estagio2_origem_tarcisio"][c][d]
            for part, fill, op in (
                (vt, GREEN, 0.85),
                (v - vt, color_of.get(d, GREY), 0.28),
            ):
                if part < 0.1:
                    continue
                h1, h2 = part * pos[1][c]["scale"], part * pos[2][d]["scale"]
                y1, y2 = pos[1][c]["out"], pos[2][d]["in"]
                pos[1][c]["out"] += h1
                pos[2][d]["in"] += h2
                rib.append(
                    ribbon(xs[1] + node_w, xs[2], y1, y2, (h1 + h2) / 2, fill, op)
                )
    out.extend(rib)
    out.extend(labels)
    r = f["resumo"]
    out.append(
        rect(xs[0], H - 62, 18, 14, GREEN, 2, 0.85)
        + text(xs[0] + 26, H - 50, "parcela que saiu de Tarcísio", 15, INK2)
    )
    out.append(
        text(
            xs[0],
            H - 30,
            f"Tarcísio para terceira via no 1º turno: {fmt(r['tarcisio_para_terceira_via'], 1)} pontos.",
            14,
            AMBER,
        )
    )
    out.append(
        text(
            xs[0],
            H - 10,
            f"Dali, {fmt(r['terceira_via_para_flavio'], 1)} voltam a Flávio, {fmt(r['terceira_via_para_nao_escolha'], 1)} anulam e {fmt(r['terceira_via_para_lula'], 1)} vão a Lula.",
            14,
            AMBER,
        )
    )
    return svg("".join(out), W, H, "Três níveis do voto de Tarcísio no Datafolha")


def viz_bars_estoque():
    top = MICRO["trabalho"][:12]
    dens = MICRO["densidade"][:5]
    W, H = 1000, 700
    out = [
        text(
            40,
            34,
            "ESTOQUE LOCALIZADO: ELEITORES DE TARCÍSIO QUE NÃO SÃO DE FLÁVIO",
            15,
            MUTED,
        )
    ]
    mx = top[0]["estoque_votos"]
    y = 66
    for r in top:
        w = 520 * r["estoque_votos"] / mx
        out.append(text(230, y + 15, r["nome"], 16, INK, SANS, 600, "end"))
        out.append(rect(245, y, max(w, 3), 20, GREEN, 3, 0.9))
        out.append(
            text(
                245 + w + 10,
                y + 15,
                f"{fmt(r['estoque_votos'])}  ·  {fmt(r['estoque_pct'], 1)}%",
                14,
                INK2,
            )
        )
        y += 31
    x = 40
    y = 466
    out.append(
        text(x, y, "ONDE O ESTOQUE É MAIS DENSO (40 MIL ELEITORES OU MAIS)", 14, MUTED)
    )
    y += 30
    for r in dens:
        out.append(text(x, y, f"{r['nome']}", 16, INK, SANS, 600))
        out.append(
            text(
                x + 230,
                y,
                f"{fmt(r['estoque_pct'], 2)}% · Garcia {fmt(r['garcia1'], 1)}% em 2022 · {r['regiao']}",
                14,
                INK2,
            )
        )
        y += 26
    e = MICRO["estado"]
    out.append(
        text(
            x,
            H - 30,
            f"Total localizado: {fmt(e['estoque_votos_total'] / 1e6, 2)} mi ({fmt(e['estoque_pct'], 2)}% do 1º turno de 2022), {fmt(e['estoque_garcia_total'] / 1e3)} mil do eleitor de Garcia.",
            12,
            FAINT,
        )
    )
    out.append(
        text(
            x,
            H - 12,
            "Coeficientes: Atlas p. 14, 19 e 23 (voto declarado de 2022). Votos: TSE 2022.",
            12,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Estoque localizado por cidade")


def viz_pontes():
    top = PONTES["top"][:10]
    W, H = 1000, 660
    out = [
        text(
            40,
            34,
            "PONTES MENOS BOLSONARO, 1º TURNO DE 2022, EM PONTOS (40 MIL ELEITORES OU MAIS)",
            15,
            MUTED,
        )
    ]
    y = 66
    for r in top:
        w = 360 * r["pontes_menos_bol1_pp"] / 12.5
        out.append(text(230, y + 15, r["nome"], 16, INK, SANS, 600, "end"))
        out.append(rect(245, y, w, 20, CYAN, 3, 0.9))
        out.append(
            text(
                245 + w + 10,
                y + 15,
                f"{sgn(r['pontes_menos_bol1_pp'])} pp  ·  estoque {fmt(r['estoque_pct'], 1)}%",
                14,
                INK2,
            )
        )
        y += 30
    y = 380
    out.append(
        text(
            40,
            y,
            "OUTROS PUXADORES E ONDE RENDEM ACIMA DO TOPO (ÍNDICE 100 = BOLSONARO)",
            14,
            MUTED,
        )
    )
    cards = []
    by = {c["slug"]: c["resumo"] for c in CORR}
    cards.append(
        ("Derrite", by["sorocaba"]["i_derrite"], "corredor de Sorocaba", AMBER)
    )
    cards.append(("André do Prado", by["leste"]["i_prado"], "ABC e Alto Tietê", AMBER))
    cards.append(("Tarcísio", by["porto"]["i_tarcisio"], "Baixada Santista", GREEN))
    cards.append(
        ("Pontes", by["agro_oeste"]["i_pontes"], "Agro do Oeste e Bauru", CYAN)
    )
    x = 40
    for nome, idx, onde, color in cards:
        out.append(rect(x, y + 20, 222, 110, "rgb(244 242 234 / 6%)", 6))
        out.append(text(x + 16, y + 68, fmt(idx), 40, color, DISPLAY, 900))
        out.append(text(x + 16, y + 94, nome, 16, INK, SANS, 600))
        out.append(text(x + 16, y + 116, onde, 13, INK2))
        x += 236
    alvos = ", ".join(r["nome"] for r in PONTES["alvos"][:8])
    out.append(
        text(
            40,
            H - 60,
            "Agendas conjuntas Flávio e Pontes (excedente de 4 pontos e estoque de 4,9% ou mais):",
            15,
            INK2,
            SANS,
            600,
        )
    )
    out.append(
        text(40, H - 36, alvos + ("..." if len(PONTES["alvos"]) > 8 else ""), 15, CYAN)
    )
    out.append(
        text(
            40,
            H - 10,
            "Índice mede alcance, não repasse. TSE 2022, votos nominais por cargo.",
            12,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Pontes e os puxadores")


COMPANHIA = {
    "capital": ("Tarcísio e Derrite", "Nunes soma máquina, não imagem"),
    "leste": ("Tarcísio e André do Prado", "Pontes no chão de fábrica"),
    "oeste_metro": ("Tarcísio e André do Prado", "Bruna Furlan, Gerson Pessoa"),
    "porto": ("Tarcísio sozinho", "Rosana Valle, Paulo A. Barbosa"),
    "tecnologia": ("Tarcísio e Pontes (ex-MCTI)", "Valéria Bolsonaro, R. Nogueira"),
    "aeroespacial": (
        "Pontes (ITA, DCTA) e Tarcísio",
        "Eduardo Bolsonaro, Letícia Aguiar",
    ),
    "sorocaba": ("Derrite e Pontes", "Vitor Lippi, Simone Marquetto"),
    "cana": ("Tarcísio, Salles e Carla", "Ricardo Silva, Rafael Silva"),
    "agro_oeste": ("Pontes, em casa", "Derrite, Salles, Dani Alonso, Bragato"),
}


def viz_companhia():
    W, H = 1000, 660
    out = [
        text(
            40, 34, "QUEM SOBE COM FLÁVIO EM CADA CORREDOR, E COM QUE ÍNDICE", 15, MUTED
        )
    ]
    cols = [
        (40, "corredor"),
        (300, "eleitores"),
        (400, "Bolsonaro 1T"),
        (510, "quem acompanha"),
        (760, "índices"),
    ]
    y = 74
    for x, lab in cols:
        out.append(text(x, y, lab.upper(), 12, FAINT))
    out.append(line(40, y + 10, 960, y + 10, "rgb(244 242 234 / 26%)"))
    y += 40
    for c in CORR:
        r = c["resumo"]
        principal, apoio = COMPANHIA[c["slug"]]
        out.append(
            text(
                40,
                y,
                c["nome"]
                .replace("Corredor ", "")
                .replace("do ", "")
                .replace("da ", "")
                .replace("de ", ""),
                16,
                INK,
                SANS,
                600,
            )
        )
        out.append(text(300, y, fmt(r["eleitores"] / 1e6, 2) + " mi", 15, INK2))
        out.append(text(400, y, fmt(r["bol1"], 1) + "%", 15, INK2))
        out.append(text(510, y, principal, 15, LIME, SANS, 600))
        out.append(text(510, y + 20, apoio, 12, INK2))
        idx = f"T {fmt(r['i_tarcisio'])} · P {fmt(r['i_pontes'])} · D {fmt(r['i_derrite'])} · Pr {fmt(r['i_prado'])}"
        out.append(text(760, y, idx, 11, INK2))
        out.append(line(40, y + 32, 960, y + 32, "rgb(244 242 234 / 12%)"))
        y += 60
    out.append(
        text(
            40,
            H - 12,
            "T Tarcísio · P Pontes · D Derrite · Pr André do Prado. Índice 100 = rende como Bolsonaro no corredor, 1º turno de 2022.",
            12,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Companhia de jornada por corredor")


def viz_renda():
    W, H = 1000, 640
    rows = []
    for inst, lab in (
        ("datafolha", "Datafolha"),
        ("quaest", "Quaest"),
        ("atlas", "Atlas"),
        ("realtime", "Real Time"),
    ):
        for q, qlab in (
            ("gov2", "governo 2º"),
            ("gov1", "governo 1º"),
            ("pres2", "Presidência 2º"),
            ("pres1", "Presidência 1º"),
        ):
            b = R[inst].get(q)
            if b and (
                q in ("gov2", "pres2")
                or (inst in ("quaest", "realtime") and q in ("gov1", "pres1"))
            ):
                rows.append(
                    (
                        f"{lab} · {qlab}",
                        b["diferenca_publicada"],
                        b["diferenca_sensibilidade"],
                    )
                )
    out = [
        text(
            40,
            34,
            "DIFERENÇA DIREITA MENOS ESQUERDA: PUBLICADA E COM A RENDA DA PNAD",
            15,
            MUTED,
        )
    ]
    x0, x1 = 330, 940
    sx = lambda v: x0 + (x1 - x0) * (v + 2) / 24  # noqa: E731
    for t in (0, 5, 10, 15, 20):
        out.append(
            line(
                sx(t),
                60,
                sx(t),
                H - 110,
                "rgb(244 242 234 / 14%)" if t else "rgb(244 242 234 / 45%)",
            )
        )
        out.append(text(sx(t), H - 92, sgn(t, 0), 13, FAINT, anchor="middle"))
    y = 76
    for lab, pub, sens in rows:
        out.append(text(x0 - 14, y + 20, lab, 15, INK, SANS, 600, "end"))
        out.append(rect(sx(min(0, pub)), y, abs(sx(pub) - sx(0)), 14, INK2, 2))
        out.append(text(sx(pub) + 6, y + 11, sgn(pub), 12, INK2))
        out.append(rect(sx(min(0, sens)), y + 17, abs(sx(sens) - sx(0)), 14, AMBER, 2))
        out.append(text(sx(sens) + 6, y + 28, sgn(sens), 12, AMBER))
        y += 52
    out.append(
        rect(x0, H - 68, 18, 12, INK2, 2) + text(x0 + 26, H - 57, "publicada", 14, INK2)
    )
    out.append(
        rect(x0 + 140, H - 68, 18, 12, AMBER, 2)
        + text(x0 + 166, H - 57, "com os pesos de renda da PNADC 2025", 14, INK2)
    )
    out.append(
        text(
            40,
            H - 26,
            "Sensibilidade de uma margem: o voto por faixa fica, só o peso muda. Nunca voto corrigido.",
            12,
            FAINT,
        )
    )
    out.append(
        text(
            40,
            H - 8,
            "Datafolha p. 27 e 33; Quaest p. 9, 24 e 79; Atlas p. 10, 14, 18 e 23; Real Time p. 10.",
            12,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Reponderação por renda")


def viz_ordem():
    W, H = 1000, 640
    steps = [
        (
            "01",
            "Fechar o vão antes de abrir frente",
            "1 em 7 eleitores de Tarcísio não vota Flávio: 2,4 mi de votos; 1,1 mi já têm cidade.",
        ),
        (
            "02",
            "Tarcísio abre, Flávio fecha",
            "Aprovação 52% e imagem +10 contra imagem −13 e rejeição 48,3%. A ordem do palanque não é detalhe.",
        ),
        (
            "03",
            "Metrópole primeiro",
            "Capital e RM são 47% do eleitorado e o vão é de 5,2 e 9,9 pontos. Trem, PCC e tarifa, não bandeira.",
        ),
        (
            "04",
            "Puxador certo no lugar certo",
            "Pontes em Bauru, Marília, Sorocaba, Vale; Derrite em Sorocaba; Prado no Alto Tietê. Nenhum deles na Baixada.",
        ),
        (
            "05",
            "Voto útil no 1º turno",
            "A terceira via carrega 8 a 14 pontos de Tarcísio e devolve um terço ao nulo. O argumento que o eleitor já aceitou para governador.",
        ),
    ]
    out = [
        text(
            40,
            34,
            "O QUE TARCÍSIO, PONTES E OS PUXADORES PRECISAM FAZER, NA ORDEM DOS NÚMEROS",
            15,
            MUTED,
        )
    ]
    y = 80
    for n, t, d in steps:
        out.append(text(40, y + 30, n, 40, LIME, DISPLAY, 900))
        out.append(text(120, y + 12, t, 21, INK, SANS, 700))
        for k, chunk in enumerate(textwrap.wrap(d, 76)[:2]):
            out.append(text(120, y + 40 + 22 * k, chunk, 15, INK2))
        out.append(line(40, y + 84, 960, y + 84, "rgb(244 242 234 / 12%)"))
        y += 104
    out.append(
        text(
            40,
            H - 12,
            "Sem datas. A ordem é de prioridade e vale enquanto os números de agosto valerem.",
            13,
            FAINT,
        )
    )
    return svg("".join(out), W, H, "Ordem de marcha")


def viz_fecho():
    W, H = 1000, 640
    out = [
        text(500, 120, "brasil.arvor.co/sp_092026.html", 36, LIME, MONO, 700, "middle")
    ]
    items = [
        "645 municípios com TSE 2018 e 2022, PNAD, PIB e eleitorado",
        "Cinco pesquisas auditadas, com página e hash de cada PDF",
        "Quatro Sankeys de dois níveis e três de três níveis",
        "Reponderação por renda das quatro amostras, com série",
        "Estoque localizado por cidade e o excedente de Pontes",
        "Nove corredores com pauta da imprensa local, com link",
        "Mapa interativo com 26 camadas e zoom na Grande São Paulo",
    ]
    y = 190
    for it in items:
        out.append(text(140, y, "▸", 18, CYAN))
        out.append(text(170, y, it, 18, INK2, SANS))
        y += 44
    out.append(
        text(
            500,
            H - 60,
            "Todo número tem fonte, página e script ao lado. Se algum estiver errado, dá para provar.",
            16,
            INK,
            SANS,
            600,
            "middle",
        )
    )
    return svg("".join(out), W, H, "Fecho")


# ------------------------------------------------------------------ cards
def build_cards():
    df, at, rt = FLOWS["Datafolha"], FLOWS["Atlas"], FLOWS["Real Time"]
    f3d = F3["Datafolha"]["resumo"]
    e = MICRO["estado"]
    pe = PONTES["estado"]
    ra2 = R["atlas"]["pres2"]["candidatos"]
    rd2 = R["datafolha"]["gov2"]["candidatos"]
    cards = [
        {
            "kind": "tese",
            "tag": "A tese",
            "metric": "1 em 7",
            "title": "O voto de Tarcísio que ainda não é de Flávio",
            "t": f"Em São Paulo, Tarcísio vence o 2º turno estadual com folga em todas as pesquisas. Flávio vence o presidencial por menos, ou perde. A diferença entre os dois, na mesma amostra, é o maior estoque de voto de direita disponível no país: {fmt(df['origem']['Tarcísio'] - df['destino']['Flávio'], 1)} pontos no Datafolha, {fmt(at['origem']['Tarcísio'] - at['destino']['Flávio'], 1)} na Atlas, {fmt(rt['origem']['Tarcísio'] - rt['destino']['Flávio'], 1)} na Real Time.",
            "chips": [
                ("g", "Datafolha 54 × 47"),
                ("g", "Atlas 53,2 × 46,8"),
                ("g", "Real Time 54 × 44"),
            ],
            "viz": viz_dumbbell_vao(),
            "copy": [
                "São Paulo tem 34,1 milhões de eleitores, um quarto do país. Tarcísio vence o 2º turno para governador em todas as pesquisas de agosto: 54 × 35 no Datafolha, 53,2 × 42,6 na Atlas, 54 × 36 na Real Time. Flávio, na mesma amostra e no mesmo dia, faz 47 × 42, 46,8 × 43,3 e 44 × 49.",
                f"A distância entre o governador e o candidato a presidente, dentro da mesma pesquisa, é o que chamamos de vão: {fmt(df['origem']['Tarcísio'] - df['destino']['Flávio'], 1)} pontos no Datafolha, {fmt(at['origem']['Tarcísio'] - at['destino']['Flávio'], 1)} na Atlas, {fmt(rt['origem']['Tarcísio'] - rt['destino']['Flávio'], 1)} na Real Time. Cada ponto vale 341 mil eleitores. Sete pontos são 2,4 milhões de votos: mais que a margem de Lula sobre Bolsonaro no país inteiro em 2022.",
                "Esta thread mostra cinco coisas com dados do TSE, da PNAD e de cinco institutos: para onde vai esse eleitor quando Tarcísio não está na urna; se a terceira via está levando voto de Tarcísio para Lula, como muita gente supõe; em que cidades ele mora; quais puxadores rendem acima de Bolsonaro e onde; e quem deve subir no palanque com Flávio em cada região do estado.",
                "A tese em uma frase: Tarcísio não pode ter voto fora do voto Tarcísio-Flávio, e isso depende dele, de Pontes e de meia dúzia de nomes que rendem em lugares diferentes. O dossiê inteiro, com fonte e página em cada número, está em brasil.arvor.co/sp_092026.html.",
            ],
            "foot": "Datafolha 18 e 19/08; Atlas 26 a 31/08; Real Time 19 a 22/08. Votos totais, em %.",
        },
        {
            "kind": "ponto",
            "tag": "Ponto 1 · o vazamento",
            "metric": f"{fmt(100 - at['estimado']['tarcisio_para_direita_pct'], 1)}% a {fmt(100 - rt['estimado']['tarcisio_para_direita_pct'], 1)}%",
            "title": "Do eleitor de Tarcísio não vota Flávio, e o destino muda com o método",
            "t": "As margens publicadas impõem o tamanho do vazamento. A prior é medida pela Atlas no voto de 2022, e o IPF só fecha as contas. O que muda entre institutos não é quanto sai, é para onde vai: presencial e telefone mandam para Lula, digital manda para o nulo.",
            "chips": [
                (
                    "b",
                    f"Datafolha: {fmt(df['estimado']['tarcisio_para_esquerda_pct'], 1)}% a Lula",
                ),
                (
                    "a",
                    f"Atlas: {fmt(at['estimado']['tarcisio_para_nao_escolha_pct'], 1)}% ao nulo",
                ),
                (
                    "l",
                    f"Real Time: {fmt(rt['estimado']['tarcisio_para_esquerda_pct'], 1)}% a Lula",
                ),
            ],
            "viz": viz_stack_destinos(),
            "copy": [
                f"Ponto 1. Entre um em sete e um em cinco eleitores de Tarcísio no 2º turno não votam Flávio no 2º turno: {fmt(100 - df['estimado']['tarcisio_para_direita_pct'], 1)}% no Datafolha, {fmt(100 - at['estimado']['tarcisio_para_direita_pct'], 1)}% na Atlas, {fmt(100 - rt['estimado']['tarcisio_para_direita_pct'], 1)}% na Real Time.",
                f"O tamanho do vazamento não depende de modelo: é a diferença entre o que Tarcísio tem e o que Flávio tem, publicada pelo próprio instituto. O destino depende, e aí os institutos divergem. No Datafolha, Lula recebe {sgn(df['robusto']['diferenca_esquerda_menos_haddad_pp'], 1)} sobre Haddad e a não escolha fica parada: o eleitor de Tarcísio que falta prefere Lula a Flávio. Na Atlas, Lula recebe {sgn(at['robusto']['diferenca_esquerda_menos_haddad_pp'], 1)} e a não escolha salta {sgn(at['robusto']['variacao_nao_escolha_pp'], 1)}: o eleitor que falta anula. Na Real Time, Lula recebe {sgn(rt['robusto']['diferenca_esquerda_menos_haddad_pp'], 1)}, o maior salto dos três.",
                "Presencial em ponto de fluxo e telefone contam a mesma história; a pesquisa digital conta outra. As duas leituras convergem numa só instrução para a campanha: esse eleitor é conquistável, porque nenhum dos institutos o dá como petista convicto nem como abstencionista convicto. Ele está no meio.",
                "E está no meio por causa de Tarcísio. O governador tem 52% de aprovação e a menor rejeição entre os nomes nacionais, 34,5%. O eleitor dele que ainda não é de Flávio não é um problema de Flávio. É uma tarefa de Tarcísio: não deixar voto próprio fora do voto conjunto.",
            ],
            "foot": "Nós = margens publicadas. Fitas = IPF com prior da Atlas p. 23. Base: sp_092026_camada2.json.",
        },
        {
            "kind": "ponto",
            "tag": "Ponto 2 · a terceira via",
            "metric": f"{fmt(f3d['terceira_via_para_lula'], 1)} de {fmt(f3d['tarcisio_para_terceira_via'], 1)}",
            "title": "A hipótese Tarcísio-Lula via terceira via não passa no teste",
            "t": f"Testamos com três colunas no Datafolha: governador no 1º turno, presidente no 1º turno, presidente no 2º turno. A terceira via carrega {fmt(f3d['tarcisio_para_terceira_via'], 1)} pontos de eleitores de Tarcísio no 1º turno. No 2º turno, {fmt(f3d['terceira_via_para_flavio'], 1)} voltam a Flávio, {fmt(f3d['terceira_via_para_nao_escolha'], 1)} anulam e {fmt(f3d['terceira_via_para_lula'], 1)} vão a Lula.",
            "chips": [
                ("a", "Caiado, Zema, Renan, Cury"),
                ("c", "custo: o nulo do 2º turno"),
                ("l", "Haddad para Flávio: zero"),
            ],
            "viz": viz_sankey3_datafolha(),
            "copy": [
                "Ponto 2. A hipótese que muita gente na direita repete: parte do voto de Tarcísio que termina em Lula passaria por Renan Santos ou outro nome da terceira via no 1º turno. Faz sentido na cabeça. Testamos.",
                "Montamos o diagrama com três colunas no Datafolha: governador no 1º turno, presidente no 1º turno, presidente no 2º turno. A prior do primeiro estágio é medida pela Atlas de agosto, que pergunta em quem o entrevistado votou em 2022 e cruza com 2026. A regra ideológica está embutida porque foi medida: eleitor de Haddad não vai a Flávio (zero), eleitor de Tarcísio vai a Lula em proporção pequena (0,5% no 1º turno, 2,3% no 2º).",
                f"Resultado: a terceira via carrega {fmt(f3d['tarcisio_para_terceira_via'], 1)} pontos de eleitores de Tarcísio no 1º turno do Datafolha, sobretudo Caiado e Zema. No 2º turno, {fmt(f3d['terceira_via_para_flavio'], 1)} desses pontos voltam a Flávio, {fmt(f3d['terceira_via_para_nao_escolha'], 1)} anulam e {fmt(f3d['terceira_via_para_lula'], 1)} vão a Lula. Na Atlas é igual: 10,8 carregados, 6,0 de volta, 4,6 no nulo, 0,3 em Lula. Só na Real Time, onde Lula tem 49, a terceira via entrega 2,6 pontos a ele.",
                "O custo da terceira via para a direita paulista é o nulo do 2º turno, não o voto em Lula. Renan e Cury não alimentam Lula com o voto de Tarcísio; eles seguram um eleitor que, sem o candidato do 1º turno, não vota em ninguém. O remédio é o argumento que esse eleitor já aceitou para governador: voto útil desde o 1º turno.",
            ],
            "foot": "Datafolha p. 8 e Poder360 22/08. Dois estágios de IPF; prior empírica Atlas p. 10, 19 e 23. Estimativa.",
        },
        {
            "kind": "ponto",
            "tag": "Ponto 3 · onde ele mora",
            "metric": f"{fmt(e['estoque_votos_total'] / 1e6, 2)} mi",
            "title": "Eleitores de Tarcísio sem Flávio com endereço, cidade a cidade",
            "t": f"A urna de 2022 não separa Tarcísio de Bolsonaro: 55,27 × 55,24 no 2º turno, mesmo eleitorado em toda cidade. O que separa é o mandato, medido pela Atlas: {fmt(100 * MICRO['coeficientes']['Rodrigo Garcia'], 1)}% de quem votou Rodrigo Garcia em 2022, {fmt(100 * MICRO['coeficientes']['Tarcísio'], 1)}% de quem votou Tarcísio e {fmt(100 * MICRO['coeficientes']['Haddad'], 1)}% de quem votou Haddad hoje votam Tarcísio e não votam Flávio.",
            "chips": [
                (
                    "g",
                    f"{fmt(e['estoque_garcia_total'] / 1e3)} mil vêm do eleitor de Garcia",
                ),
                ("c", "densidade máxima: Olímpia e Cruzeiro"),
                ("a", "capital: 283 mil, um quarto"),
            ],
            "viz": viz_bars_estoque(),
            "copy": [
                "Ponto 3. Onde mora esse eleitor. Primeiro o que não funciona: procurar em 2022 a cidade em que Tarcísio teve voto que Bolsonaro não teve. No 2º turno de 2022, mesmo universo, os dois fizeram 55,27% e 55,24% no estado e ficaram a menos de um ponto em toda cidade grande. Eram o mesmo eleitorado. O eleitor de Tarcísio que não é de Flávio nasceu no mandato.",
                f"O que funciona: a Atlas de agosto pergunta em quem o entrevistado votou em 2022 e cruza com 2026. Disso saem três fatias medidas: {fmt(100 * MICRO['coeficientes']['Rodrigo Garcia'], 1)}% de quem votou Rodrigo Garcia no 1º turno de 2022, {fmt(100 * MICRO['coeficientes']['Tarcísio'], 1)}% de quem votou Tarcísio e {fmt(100 * MICRO['coeficientes']['Haddad'], 1)}% de quem votou Haddad hoje votam Tarcísio e não votam Flávio. Aplicadas aos votos de 2022 de cada cidade, dado do TSE, dão {fmt(e['estoque_votos_total'] / 1e6, 2)} milhão de eleitores com endereço, {fmt(e['estoque_garcia_total'] / 1e3)} mil deles vindos do eleitor tucano.",
                f"Em volume, a capital tem {fmt(MICRO['trabalho'][0]['estoque_votos'] / 1e3)} mil, um quarto do total; depois Guarulhos, Campinas, São Bernardo, Santo André, São José dos Campos e Osasco. Em densidade, a lista muda: Olímpia ({fmt(MICRO['densidade'][0]['estoque_pct'], 1)}%), Cruzeiro, Bragança Paulista, Porto Ferreira e Boituva, cidades em que Garcia fez de 24% a 39%. É o interior rico de tradição tucana.",
                "Volume decide onde gastar tempo. Densidade decide onde a mensagem certa rende mais por evento. Metade do vão não tem endereço, porque quem anulou ou não votou em 2022 não aparece na base municipal; a metade que votou em candidato está mapeada.",
            ],
            "foot": "Coeficientes: Atlas p. 14, 19 e 23 (voto declarado de 2022). Votos: TSE 2022 por município. Estimativa.",
        },
        {
            "kind": "ponto",
            "tag": "Ponto 4 · os puxadores",
            "metric": sgn(PONTES["top"][0]["pontes_menos_bol1_pp"]),
            "title": "Pontes em Bauru, Derrite em Sorocaba, Prado no Alto Tietê: cada puxador rende num lugar",
            "t": f"Marcos Pontes fez {fmt(pe['pontes'], 2)}% para o Senado contra {fmt(pe['bolsonaro_1t'], 2)}% de Bolsonaro na mesma cédula e ficou acima em {pe['municipios_pontes_acima']} municípios. A diferença tem geografia: máxima em Bauru, cidade natal, e no eixo Jaú, Ourinhos, Botucatu, Marília, Sorocaba e Itu; zero ou negativa na capital e na Baixada.",
            "chips": [
                ("c", "Pontes: Bauru, Marília, Sorocaba, Vale"),
                ("a", "Derrite: Sorocaba, índice 434"),
                ("a", "Prado: Alto Tietê, índice 344"),
            ],
            "viz": viz_pontes(),
            "copy": [
                f"Ponto 4. Quem puxa voto onde Bolsonaro não puxou. Marcos Pontes fez {fmt(pe['pontes'], 2)}% para o Senado em 2022 contra {fmt(pe['bolsonaro_1t'], 2)}% de Bolsonaro para presidente, na mesma cédula e no mesmo dia. É o único nome da direita paulista com prova de voto acima do topo da chapa no estado inteiro, e não está na cédula de 2026 como candidato.",
                f"A diferença tem geografia. Em Bauru, cidade natal dele, {sgn(PONTES['top'][0]['pontes_menos_bol1_pp'])} pontos sobre Bolsonaro. Em Ourinhos, Jaú, Botucatu, Lins, Marília e Assis, de 5 a 7 pontos. Em Sorocaba, +6,0; em Itu, +5,7; em Guaratinguetá e Caçapava, no Vale, +5,9 e +4,9. Na capital, na Baixada e em Santana de Parnaíba, zero ou negativo. Pontes é um nome do interior, com excedente próprio no eixo Bauru, Marília e Sorocaba, e uma biografia (ITA, DCTA, Ciência) que só vira pauta nos corredores de tecnologia.",
                f"Cruzando o excedente de Pontes com o estoque de eleitores de Tarcísio sem Flávio, saem {len(PONTES['alvos'])} cidades para agendas conjuntas: Marília, Itu, Botucatu, Jaú, Guaratinguetá, Barretos, Caçapava e mais seis. Derrite rende quatro vezes o topo no corredor de Sorocaba e 37 na Baixada; André do Prado, 344 no Alto Tietê e 7 no oeste.",
                "O índice mede alcance, não repasse. Pontes é PL de origem militar e científica, não bolsonarista de primeira hora, e o eleitor que votou nele e não em Bolsonaro pode ser exatamente o que recusa a marca. É isso que a agenda conjunta testa, e nenhuma pesquisa publicada mede. O empenho de Pontes vale onde ele existe; na metrópole, ele não soma.",
            ],
            "foot": "TSE 2022, votos nominais por cargo e município. Índice 100 = rende como Bolsonaro rendeu ali.",
        },
        {
            "kind": "ponto",
            "tag": "Ponto 5 · a companhia",
            "metric": "9",
            "title": "Nove corredores, nove palanques diferentes: quem sobe com Flávio em cada um",
            "t": "Agrupamos os municípios por base econômica, imprensa e formato de encontro possível. Para cada corredor, quem tem base medida em 2022, com que índice, e quem não deve subir porque rende abaixo do topo ali. O palanque que serve em Sorocaba atrapalha em Santos.",
            "chips": [
                ("g", "Tarcísio abre em todos"),
                ("c", "Pontes no Vale, em Campinas e no oeste"),
                ("a", "Derrite em Sorocaba e na capital"),
            ],
            "viz": viz_companhia(),
            "copy": [
                "Ponto 5. Quem acompanha Flávio em cada região. O estado cabe em nove corredores, agrupados por economia, imprensa e tipo de encontro que a região comporta. Em cada um, o índice diz quem rende acima do topo da chapa e quem rende abaixo.",
                "Capital: Tarcísio abre e Derrite fala de segurança, o nome da direita com imagem positiva (+7) e menor rejeição (30,2%) na Atlas. Nunes soma máquina, não imagem. ABC, Guarulhos e Alto Tietê: Tarcísio com André do Prado, que rende 344 na região de origem, e Pontes no chão de fábrica. Oeste metropolitano: Tarcísio e Prado. Baixada: Tarcísio sozinho, o corredor em que ele mais rende acima de Bolsonaro; Pontes e Derrite ficam fora da foto.",
                "Campinas e Jundiaí: Tarcísio e Pontes como ex-ministro de Ciência diante de Unicamp, CPqD e Viracopos. Vale do Paraíba: Pontes é o nome do corredor, formado no ITA e treinado no DCTA de São José dos Campos, com Tarcísio e Eduardo Bolsonaro. Sorocaba: Derrite e Pontes, os dois carregadores acima do topo ao mesmo tempo. Ribeirão, Franca e Araraquara: Tarcísio, Salles e Carla. Bauru, Marília, Rio Preto e Prudente: Pontes em casa, com Derrite e Salles.",
                "A regra que decide o alvo: topo da chapa abaixo da média em 2022, carregador acima, e pauta material com valor e devedor na imprensa local. Em São Paulo isso é a metrópole, com trem, PCC e tarifa, e a Baixada, com o porto no limite e o Tecon 10 adiado nove vezes. O interior de direita não precisa de conversão: precisa de calendário e de voto útil no 1º turno.",
            ],
            "foot": "Índices e âncoras: TSE 2022. Imagem e rejeição: Atlas p. 37 e 39. Pauta: imprensa local, com link no dossiê.",
        },
        {
            "kind": "limite",
            "tag": "Antes da conclusão · os limites",
            "metric": f"{fmt(ra2['Flávio']['sensibilidade'], 1)} × {fmt(ra2['Lula']['sensibilidade'], 1)}",
            "title": "O achado que contraria a tese, e o que é estimativa",
            "t": f"Trocar o peso de cada faixa de renda pelo peso da PNAD 2025 quase não move Datafolha, Quaest e Real Time. Na Atlas, tira a liderança de Flávio: 46,8 × 43,3 vira {fmt(ra2['Flávio']['sensibilidade'], 1)} × {fmt(ra2['Lula']['sensibilidade'], 1)}, porque nela a direita é mais forte entre os pobres, sinal oposto ao das outras três. Publicamos com o mesmo destaque.",
            "chips": [
                ("a", "fitas são estimativa, nós são medição"),
                ("a", "memória de voto tem erro"),
                ("a", "metade do vão não tem endereço"),
            ],
            "viz": viz_renda(),
            "copy": [
                "Antes da conclusão, os limites, porque sem eles a thread não sobrevive a leitura hostil.",
                f"Primeiro, o achado que contraria a tese. A hipótese de partida era que a amostra mais pobre do Datafolha (38% até dois salários, contra 23% na PNAD) escondia voto de direita. Reponderada pela renda oficial, a diferença de Tarcísio sobe de 19 para {fmt(rd2['Tarcísio']['sensibilidade'] - rd2['Haddad']['sensibilidade'], 1)}: quase nada. Na Real Time sobe de 17 para 19,7. Na Quaest cai um ponto. Na Atlas o sinal inverte e a régua tira a liderança de Flávio: 46,8 × 43,3 vira {fmt(ra2['Flávio']['sensibilidade'], 1)} × {fmt(ra2['Lula']['sensibilidade'], 1)}, porque na pesquisa digital Flávio faz 65,7% entre quem ganha até R$ 2 mil e 28,5% acima de R$ 10 mil, o oposto do que Quaest, Datafolha e Real Time medem. O gradiente de renda com sinal oposto entre métodos é um problema que os institutos precisam explicar.",
                "Segundo, o que é medição e o que é estimativa. Os placares são medição. As fitas dos diagramas são IPF: fecham exatamente as margens publicadas, mas o corte fita a fita depende da prior, que é empírica (Atlas, voto declarado de 2022) e está publicada. O estoque por cidade aplica coeficientes de uma pesquisa com 1.810 entrevistas ao voto de 2022, e memória de voto tem erro. Metade do vão não tem endereço, porque quem anulou ou não votou em 2022 não aparece na base municipal.",
                "Terceiro, o que não está medido: nenhum instituto publica o cruzamento direto do voto de 2026 para governador com o de 2026 para presidente. Se publicasse, esta thread teria metade do tamanho. O pedido fica registrado.",
            ],
            "foot": "PNADC anual 2025, pessoas 16+, SM de R$ 1.621, preços de abril de 2026. Sensibilidade de uma margem, nunca voto corrigido.",
        },
        {
            "kind": "ordem",
            "tag": "O que fazer",
            "metric": "2,4 mi",
            "title": "Tarcísio não pode ter voto fora do voto Tarcísio-Flávio",
            "t": "É a instrução que sai dos cinco pontos, e ela não é de Flávio: é do governador, de Pontes e dos puxadores regionais. Cinco movimentos, na ordem em que os números pedem, com o número ao lado de cada um.",
            "chips": [
                ("g", "Tarcísio abre, Flávio fecha"),
                ("c", "Pontes no eixo Bauru-Marília-Sorocaba e no Vale"),
                ("a", "voto útil desde o 1º turno"),
            ],
            "viz": viz_ordem(),
            "copy": [
                "O que fazer, na ordem em que os números pedem.",
                "Um: fechar o vão antes de abrir frente nova. Um em sete eleitores de Tarcísio não vota Flávio; são 2,4 milhões de votos, 1,1 milhão deles com cidade. Nenhuma outra frente no país rende isso. Dois: Tarcísio abre, Flávio fecha, sempre nessa ordem. Aprovação de 52%, imagem +10 e rejeição de 34,5% de um lado; imagem −13 e rejeição de 48,3% do outro. O palanque que começa pelo nome nacional expõe a rejeição antes de mostrar a entrega.",
                "Três: metrópole primeiro. Capital e região são 47% do eleitorado, o vão é de 5,2 e 9,9 pontos, e o que converte ali é serviço: a Linha 8 que descarrilou duas vezes na mesma semana, a barreira do PCC removida, a tarifa. Quatro: puxador certo no lugar certo. Pontes em Bauru, Marília, Sorocaba, Itu e no Vale; Derrite em Sorocaba e na segurança da capital; André do Prado no Alto Tietê. Nenhum dos três na Baixada, onde Tarcísio sozinho rende mais.",
                "Cinco: voto útil desde o 1º turno. A terceira via carrega de 8 a 14 pontos do eleitor de Tarcísio e devolve um terço ao nulo. O eleitor já aceitou o argumento para governador, com 99% de fidelidade; falta aceitar para presidente. É tarefa do governador dizer isso em voz alta, cidade por cidade. Sem datas: a ordem é de prioridade e vale enquanto os números de agosto valerem.",
            ],
            "foot": "Leitura estratégica declarada. Cada movimento tem o número e a página ao lado no dossiê.",
        },
        {
            "kind": "fecho",
            "tag": "Refaça a conta",
            "metric": "645",
            "title": "Tudo aberto: municípios, pesquisas, scripts e a trilha para conferir",
            "t": "O dossiê inteiro está publicado com fonte e página em cada número, os PDFs com hash, os scripts que geram cada gráfico e a base municipal para baixar. Se algum número estiver errado, dá para provar.",
            "chips": [
                ("c", "brasil.arvor.co/sp_092026.html"),
                ("g", "TSE · IBGE · PNAD · 5 institutos"),
            ],
            "viz": viz_fecho(),
            "copy": [
                "Tudo o que está nesta thread está publicado e aberto em brasil.arvor.co/sp_092026.html: os 645 municípios com TSE 2018 e 2022, PNAD, PIB e eleitorado; as cinco pesquisas com página e hash de cada PDF; os quatro diagramas de dois níveis e os três de três níveis; a reponderação por renda das quatro amostras e a série; o estoque por cidade; o excedente de Pontes; os nove corredores com a pauta da imprensa local e link; o mapa com 26 camadas e zoom na Grande São Paulo.",
                "O que é medição está marcado como medição. O que é estimativa está marcado como estimativa, com a prior publicada. O achado que contraria a tese está no capítulo 9 com o mesmo destaque dos que a sustentam.",
                "Se você é de campanha, a lista curta está nos capítulos 16 a 18: cidades, corredores e ordem. Se você é de instituto, o pedido está no capítulo 10: publiquem o cruzamento do voto para governador com o voto para presidente. Se você só quer conferir, os scripts estão no repositório e refazem cada gráfico a partir dos arquivos oficiais. Refaça a conta.",
            ],
            "foot": "Arvor Intelligence · São Paulo · setembro de 2026 · corte em 05/09.",
        },
    ]
    return cards


KIND = {
    "tese": (LIME, "tese"),
    "ponto": (CYAN, "ponto"),
    "limite": (AMBER, "limites"),
    "ordem": (LIME, "ordem"),
    "fecho": (CYAN, "fecho"),
}

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--bg:#0c0d0b;--bg2:#131512;--bg3:#191c18;--ink:#f4f2ea;--ink2:#ddd8ca;--muted:#9a9789;--faint:#8f8c7f;
  --lime:#cfe63c;--cyan:#45c9c2;--amber:#f0a930;--green:#34b47e;--lula:#e0483a;--flavio:#3f8fd6;
  --line:rgb(244 242 234 / 13%);--line2:rgb(244 242 234 / 26%);
  --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
  --wrap:min(1080px,calc(100% - 40px))}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:var(--cyan)}
.top{padding:34px 0 8px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.brand-lockup{display:flex;align-items:center;gap:11px;font-family:var(--mono);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.brand-lockup img{width:26px;height:26px;border-radius:4px}
.top .back{font-family:var(--mono);font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--lime);text-decoration:none;border:1px solid var(--line2);border-radius:999px;padding:7px 15px}
h1{font-family:var(--display);font-size:clamp(2.3rem,6.4vw,4.4rem);line-height:.98;letter-spacing:-.028em;margin:18px 0 0;font-weight:900}
h1 em{display:block;font-style:italic;color:var(--lime);font-weight:500}
.deck{max-width:76ch;color:var(--ink2);margin:20px 0 0;font-size:1.06rem}
.howto{margin:26px 0 0;border:1px solid var(--line);border-left:3px solid var(--cyan);border-radius:4px;background:var(--bg3);padding:18px 20px;color:var(--ink2);font-size:.95rem}
.howto b{color:var(--ink)}
.rail{position:sticky;top:0;z-index:30;margin:30px 0 0;padding:11px 0;background:rgb(12 13 11 / 93%);backdrop-filter:blur(10px);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.rail .wrap{display:flex;gap:5px;align-items:center;overflow-x:auto;scrollbar-width:none}
.rail b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);margin-right:8px;white-space:nowrap}
.rail a{width:26px;height:26px;flex:0 0 auto;display:grid;place-items:center;border-radius:5px;border:1px solid var(--line);color:var(--muted);text-decoration:none;font-family:var(--mono);font-size:.72rem}
.post{margin:52px 0 0;scroll-margin-top:64px}
.post-label{width:min(100%,760px);margin-left:auto;margin-right:auto;font-family:var(--mono);font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--faint);margin-bottom:11px}
.post-label b{color:var(--ink)}
/* O card é quadrado: 1:1, na largura de trabalho de 1080px, que é o que se anexa. */
.card{position:relative;aspect-ratio:1/1;width:min(100%,760px);margin:0 auto;border:1px solid var(--line2);border-radius:8px;overflow:hidden;background:#0a0b09;container-type:inline-size;display:flex;flex-direction:column}
.card::before{content:"";position:absolute;inset:0;background:radial-gradient(120% 80% at 100% 0%,rgb(69 201 194 / 10%) 0,transparent 55%),radial-gradient(90% 70% at 0% 100%,rgb(207 230 60 / 8%) 0,transparent 60%)}
.card>*{position:relative;z-index:2}
.stripe{position:absolute;inset:0 0 auto 0;height:4px;z-index:3;background:var(--accent)}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:2.2cqw 2.6cqw 0}
.chead{display:flex;align-items:center;gap:9px}
.chead img{width:2.6cqw;height:2.6cqw;min-width:22px;min-height:22px;border-radius:4px}
.chead b{display:block;font-size:1.7cqw;line-height:1.2}
.chead span{display:block;font-family:var(--mono);font-size:1.3cqw;color:var(--muted)}
.pno{font-family:var(--mono);font-size:1.4cqw;color:var(--accent);letter-spacing:.1em}
.card-body{flex:1;min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr);gap:1.6cqw;padding:1.4cqw 2.6cqw}
.said{display:grid;grid-template-columns:auto minmax(0,1fr);gap:0 2.4cqw;align-items:start}
.said .num{grid-row:1/3}
.lead-tag{display:inline-block;font-family:var(--mono);font-size:1.25cqw;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);border:1px solid currentcolor;border-radius:999px;padding:.45cqw 1cqw}
.metric{font-family:var(--display);font-weight:900;font-size:6cqw;line-height:.95;letter-spacing:-.03em;color:var(--accent);margin:.8cqw 0 0;white-space:nowrap}
.card h2{font-family:var(--display);font-size:2.9cqw;line-height:1.1;margin:.6cqw 0 .7cqw;font-weight:700}
.card .t{font-size:1.62cqw;line-height:1.42;color:var(--ink2);margin:0}
.kchips{display:flex;flex-wrap:wrap;gap:.6cqw;margin-top:.9cqw}
.kchip{font-family:var(--mono);font-size:1.22cqw;border:1px solid currentcolor;border-radius:999px;padding:.4cqw .85cqw;white-space:nowrap}
.kchip.l{color:#ea6a5c}.kchip.b{color:var(--flavio)}.kchip.a{color:var(--amber)}.kchip.c{color:var(--cyan)}.kchip.g{color:var(--green)}
.viz{border:1px solid var(--line);border-radius:6px;background:rgb(244 242 234 / 5%);padding:1.4cqw;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center}
.viz svg{width:100%;height:100%;max-height:100%;display:block}
.card-foot{flex:0 0 auto;display:flex;justify-content:space-between;gap:12px;padding:1.2cqw 2.6cqw;font-family:var(--mono);font-size:1.2cqw;color:var(--faint);border-top:1px solid var(--line)}
.copy{margin:14px auto 0;width:min(100%,760px);border:1px solid var(--line);border-radius:6px;background:var(--bg2);padding:20px 22px;font-family:var(--mono);font-size:.9rem;line-height:1.72;color:var(--ink2);white-space:pre-wrap;position:relative}
.cc{position:absolute;top:12px;right:18px;font-size:.7rem;color:var(--faint);letter-spacing:.09em}
.copy-btn{margin:10px auto 0;display:block;width:min(100%,760px);text-align:left;font-family:var(--mono);font-size:.74rem;letter-spacing:.11em;text-transform:uppercase;background:transparent;color:var(--lime);border:1px solid var(--line2);border-radius:999px;padding:9px 18px;cursor:pointer}
.copy-btn:hover{border-color:var(--lime)}
footer{margin:72px 0 0;border-top:1px solid var(--line);padding:34px 0 60px;color:var(--muted);font-size:.92rem}
footer h2{font-family:var(--display);font-size:1.6rem;margin:0 0 10px;color:var(--ink)}
@media (width <= 720px){
  body{font-size:16px}
  .card{aspect-ratio:auto}
  .card-head{padding:16px 18px 0}
  .chead img{width:26px;height:26px}
  .chead b{font-size:.92rem}
  .chead span{font-size:.72rem}
  .pno{font-size:.8rem}
  .card-body{gap:16px;padding:16px 18px 20px}
  .said{grid-template-columns:1fr}
  .said .num{grid-row:auto}
  .lead-tag{font-size:.68rem;padding:5px 11px}
  .metric{font-size:2.5rem;margin:12px 0 4px}
  .card h2{font-size:1.5rem;margin-bottom:9px}
  .card .t{font-size:.98rem;line-height:1.55}
  .kchips{gap:7px;margin-top:13px}
  .kchip{font-size:.7rem;padding:4px 9px}
  .viz{padding:14px}
  .viz svg{height:auto}
  .card-foot{padding:12px 18px;font-size:.68rem;flex-direction:column;gap:4px}
  .copy{padding:16px 15px;font-size:.84rem}
  .cc{position:static;display:block;text-align:right;margin-bottom:8px}
}
"""

JS = """
function cp(button){
  const node = button.previousElementSibling;
  const text = node.getAttribute('data-copy') || node.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const original = button.textContent;
    button.textContent = 'copiado';
    setTimeout(() => { button.textContent = original; }, 1600);
  });
}
"""


def render_card(index, total, card):
    accent, kind_label = KIND[card["kind"]]
    chips = "".join(
        f'<span class="kchip {tone}">{esc(label)}</span>'
        for tone, label in card["chips"]
    )
    body = "\n\n".join(card["copy"])
    return f"""
<section class="post" id="p{index}">
  <div class="post-label">Post {index}/{total} · <b>{esc(card["tag"])}</b> · {esc(kind_label)}</div>
  <div class="card" style="--accent:{accent}">
    <div class="stripe"></div>
    <div class="card-head">
      <div class="chead"><img src="img/arvor_logo.png" alt=""><div><b>Arvor Intelligence</b><span>brasil.arvor.co · São Paulo 2026</span></div></div>
      <div class="pno">{index:02d} / {total:02d}</div>
    </div>
    <div class="card-body">
      <div class="said">
        <div class="num"><span class="lead-tag">{esc(card["tag"])}</span><div class="metric">{esc(card["metric"])}</div></div>
        <div><h2>{esc(card["title"])}</h2><p class="t">{esc(card["t"])}</p><div class="kchips">{chips}</div></div>
      </div>
      <div class="viz">{card["viz"]}</div>
    </div>
    <div class="card-foot"><span>{esc(card["foot"])}</span><span>{index:02d}/{total:02d}</span></div>
  </div>
  <div class="copy" data-copy="{esc(body)}"><span class="cc">{len(body)} chars</span>{esc(body)}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
</section>"""


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
<title>São Paulo 2026: a thread do voto de Tarcísio que ainda não é de Flávio · Arvor</title>
<meta name="description" content="Nove cards quadrados e o texto pronto para publicar: o vão entre Tarcísio e Flávio, o teste da terceira via, as cidades onde o eleitor mora, os puxadores que rendem acima de Bolsonaro e quem acompanha Flávio em cada corredor de São Paulo.">
<link rel="canonical" href="https://brasil.arvor.co/sp_092026_thread.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0c0d0b">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="São Paulo 2026: a thread do voto de Tarcísio que ainda não é de Flávio">
<meta property="og:description" content="Cinco pontos em nove cards quadrados: o vão, a terceira via, as cidades, os puxadores e a companhia de jornada. Texto pronto para publicar.">
<meta property="og:url" content="https://brasil.arvor.co/sp_092026_thread.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/sp_092026_thread.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/sp_092026_thread.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
  <div class="top">
    <div class="brand-lockup"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · thread</div>
    <a class="back" href="sp_092026.html">Abrir o dossiê</a>
  </div>
  <h1>O voto de Tarcísio que ainda não é de Flávio. <em>Cinco pontos, nove cards.</em></h1>
  <p class="deck">A thread do atlas de São Paulo. Cada card é quadrado, 1:1, denso de propósito: o gráfico carrega a informação e o texto embaixo é o post, pronto para copiar. Os cinco pontos: o vazamento e seus destinos, o teste da terceira via, as cidades onde o eleitor mora, os puxadores que rendem acima de Bolsonaro e quem acompanha Flávio em cada corredor. Antes da conclusão, os limites, inclusive o achado que contraria a tese.</p>
  <div class="howto"><b>Como usar.</b> Cada card é a imagem do post, um quadrado de 760 pixels que cabe na tela de um notebook para o print; acima de 720 pixels de janela o quadrado é exato. O texto embaixo tem de 950 a 1.400 caracteres e cabe num post longo. Nenhum número foi digitado à mão: todos vêm dos arquivos <code>sp_092026_camada2.json</code> e <code>sp_092026_pesquisas.json</code>, gerados pelos scripts do dossiê.</div>
</header>
<nav class="rail" aria-label="Posts"><div class="wrap"><b>Posts</b>{rail}</div></nav>
<main class="wrap">{posts}</main>
<footer class="wrap">
  <h2>Reprodução</h2>
  <p>python3 scripts/sp-092026-camada2.py e python3 scripts/sp-092026-thread.py. O dossiê completo está em <a href="sp_092026.html">sp_092026.html</a>; a base pública, em <a href="assets/sp_092026_camada2.json">sp_092026_camada2.json</a>.</p>
</footer>
<script>{JS}</script>
</body>
</html>
"""
    assert "—" not in page and "–" not in page
    for c in cards:
        n = len("\n\n".join(c["copy"]))
        assert 900 <= n <= 1500, (c["tag"], n)
    OUTPUT.write_text(page)
    print(OUTPUT, total, "cards")


if __name__ == "__main__":
    main()
