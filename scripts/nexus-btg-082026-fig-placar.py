#!/usr/bin/env python3
"""Figuras de placar, movimento e religião da 8ª rodada BTG/Nexus (03/08/2026).

Fonte única: docs/assets/nexus_btg_082026_1_data.json. Nenhum número é digitado
aqui: tudo é lido do JSON ou derivado dele por aritmética explícita.

Uso: python3 scripts/nexus-btg-082026-fig-placar.py
Saída: docs/assets/figuras/nexus_082026_placar.json
"""

from __future__ import annotations

import json
from pathlib import Path

from svgkit import (
    AMBER,
    BLUE,
    DISPLAY,
    FULL,
    GRAY,
    INK,
    LIME,
    LINE,
    MONO,
    MUTED,
    NAVY,
    OLIVE,
    PAPER,
    RED,
    SANS,
    WHITE,
    Canvas,
    br,
    signed,
    write_fragments,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "docs" / "assets" / "nexus_btg_082026_1_data.json"
OUT_PATH = ROOT / "docs" / "assets" / "figuras" / "nexus_082026_placar.json"

MONTHS = {
    "jan.": "01",
    "fev.": "02",
    "mar.": "03",
    "abr.": "04",
    "mai.": "05",
    "jun.": "06",
    "jul.": "07",
    "ago.": "08",
    "set.": "09",
    "out.": "10",
    "nov.": "11",
    "dez.": "12",
}

# Nomes legíveis para os rótulos que o relatório abrevia.
LONG_LABEL = {"B/N": "Branco e nulo", "NS": "Não sabe"}

# Cor por opção de voto. Lula vermelho, Flávio azul, branco/nulo lima, NS cinza.
OPTION_COLOR = {
    "Lula": RED,
    "Flávio": BLUE,
    "B/N": LIME,
    "NS": GRAY,
}

MARGIN_PT = {
    "sex": "Sexo",
    "age": "Idade",
    "education": "Escolaridade",
    "region": "Região",
    "income": "Renda",
    "religion": "Religião",
}


def short_date(value: str) -> str:
    """'30 mar.' vira '30/03', para caber no eixo sem encolher a fonte."""
    day, month = value.split()
    return f"{int(day):02d}/{MONTHS[month]}"


def width_of(value: str, size: float, family: str = SANS) -> float:
    """Estimativa de largura do texto, usada para afastar rótulos que colidem."""
    per_char = 0.60 if family == MONO else 0.56
    return len(str(value)) * size * per_char


def declutter(
    centers: list[float], widths: list[float], gap: float = 12
) -> list[float]:
    """Empurra rótulos para a direita até nenhum encostar no vizinho."""
    placed: list[float] = []
    edge = None
    for center, width in zip(centers, widths):
        left = center - width / 2
        if edge is not None and left < edge + gap:
            left = edge + gap
        placed.append(left + width / 2)
        edge = left + width
    return placed


def arrow(canvas: Canvas, x1, y1, x2, y2, color, width=2.4, head=8) -> None:
    """Seta desenhada como polígono, para não depender de marker com id global."""
    import math

    angle = math.atan2(y2 - y1, x2 - x1)
    bx = x2 - head * math.cos(angle)
    by = y2 - head * math.sin(angle)
    canvas.line(x1, y1, bx, by, stroke=color, width=width, stroke_linecap="round")
    left = (bx - head * 0.55 * math.sin(angle), by + head * 0.55 * math.cos(angle))
    right = (bx + head * 0.55 * math.sin(angle), by - head * 0.55 * math.cos(angle))
    canvas.add(
        f'<polygon points="{x2:.1f},{y2:.1f} {left[0]:.1f},{left[1]:.1f} '
        f'{right[0]:.1f},{right[1]:.1f}" fill="{color}"/>'
    )


def pill(
    canvas: Canvas,
    cx: float,
    cy: float,
    text: str,
    fill: str,
    color: str = WHITE,
    size: float = 14,
    family: str = SANS,
    weight: str = "700",
    pad: float = 11,
    stroke: str | None = None,
) -> float:
    """Etiqueta com fundo próprio, para o número sobreviver a qualquer fundo."""
    width = width_of(text, size, family) + pad * 2
    height = size + 12
    canvas.rect(
        cx - width / 2,
        cy - height / 2,
        width,
        height,
        fill,
        rx=height / 2,
        stroke=stroke,
        stroke_width=1.4 if stroke else None,
    )
    canvas.text(
        cx,
        cy + size * 0.36,
        text,
        size=size,
        fill=color,
        family=family,
        weight=weight,
        anchor="middle",
    )
    return width


def kicker(canvas: Canvas, x: float, y: float, text: str, color: str = MUTED) -> None:
    canvas.text(
        x,
        y,
        text,
        size=14,
        fill=color,
        family=MONO,
        weight="700",
        letter_spacing="0.09em",
    )


def rich_text(
    canvas: Canvas,
    x: float,
    y: float,
    parts: list[tuple[str, str, bool]],
    size: float = 13,
    family: str = MONO,
    anchor: str = "middle",
) -> None:
    """Uma linha de texto com cor por trecho, para marcar só o dígito que mudou."""
    from xml.sax.saxutils import escape

    spans = "".join(
        f'<tspan fill="{fill}"'
        + (' font-weight="700"' if bold else "")
        + f">{escape(chunk)}</tspan>"
        for chunk, fill, bold in parts
    )
    canvas.add(
        f'<text x="{x}" y="{y}" font-size="{size}" font-family="{family}" '
        f'text-anchor="{anchor}">{spans}</text>'
    )


# ---------------------------------------------------------------- figura 1


def fig_serie_duplo(data: dict) -> str:
    series = data["series"]
    dates = [short_date(value) for value in series["dates"]]
    last = len(dates) - 1

    height = 452
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Séries de intenção de voto nas oito rodadas BTG/Nexus, primeiro e "
            "segundo turno, com a diferença entre Lula e Flávio marcada nas duas "
            "últimas rodadas."
        ),
    )

    top, plot_h = 100, 236
    base = top + plot_h

    panels = [
        {
            "x0": 96,
            "x1": 488,
            "label_x": 516,
            "lo": 31.5,
            "hi": 43.5,
            "ticks": [33, 36, 39, 42],
            "kicker": "1º TURNO, VOTO ESTIMULADO",
            "data": series["first"],
        },
        {
            "x0": 668,
            "x1": 1060,
            "label_x": 1088,
            "lo": 40.0,
            "hi": 52.0,
            "ticks": [42, 45, 48, 51],
            "kicker": "2º TURNO, LULA × FLÁVIO",
            "data": series["runoff"],
        },
    ]

    canvas.line(614, 88, 614, base + 44, stroke=LINE, width=1.5)

    for panel in panels:
        x0, x1 = panel["x0"], panel["x1"]
        lo, hi = panel["lo"], panel["hi"]
        step = (x1 - x0) / last

        def px(index: float, x0=x0, step=step) -> float:
            return x0 + index * step

        def py(value: float, lo=lo, hi=hi) -> float:
            return base - (value - lo) / (hi - lo) * plot_h

        kicker(canvas, x0 - 8, 52, panel["kicker"], INK)

        # faixa da última rodada
        canvas.rect(px(last) - 22, top - 12, 44, plot_h + 12, PAPER, opacity=0.85)
        canvas.text(
            px(last),
            top - 20,
            "última rodada",
            size=13,
            fill=MUTED,
            family=MONO,
            anchor="middle",
        )

        for tick in panel["ticks"]:
            canvas.line(x0 - 6, py(tick), x1 + 12, py(tick), stroke=LINE, width=1)
            canvas.label(x0 - 14, py(tick) + 5, f"{tick}%", anchor="end")

        canvas.line(x0 - 6, base, x1 + 12, base, stroke=INK, width=1.6)

        for index, text in enumerate(dates):
            canvas.label(
                px(index),
                base + 26,
                text,
                anchor="middle",
                fill=INK if index == last else MUTED,
                weight="700" if index == last else None,
            )

        for name, color in (("Flávio", BLUE), ("Lula", RED)):
            values = panel["data"][name]
            points = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(values))
            canvas.add(
                f'<polyline points="{points}" fill="none" stroke="{color}" '
                f'stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>'
            )
            for index, value in enumerate(values):
                radius = 8 if index == last else 5
                canvas.circle(px(index), py(value), radius, WHITE)
                canvas.circle(
                    px(index),
                    py(value),
                    radius,
                    "none",
                    stroke=color,
                    stroke_width=3.4,
                )

            first_value = values[0]
            offset = -22 if name == "Lula" else 24
            pill(
                canvas,
                px(0) + 26,
                py(first_value) + offset,
                br(first_value, 0),
                WHITE,
                color=color,
                size=17,
                pad=7,
            )

        ends = {name: py(panel["data"][name][last]) for name in ("Lula", "Flávio")}
        if abs(ends["Lula"] - ends["Flávio"]) < 26:
            middle = (ends["Lula"] + ends["Flávio"]) / 2
            high, low = sorted(ends, key=lambda name: ends[name])
            ends[high], ends[low] = middle - 13, middle + 13
        for name, color in (("Lula", RED), ("Flávio", BLUE)):
            canvas.text(
                panel["label_x"],
                ends[name] + 6,
                f"{name} {br(panel['data'][name][last], 0)}",
                size=17,
                fill=color,
                weight="800",
            )

        for index in (last - 1, last):
            lula = panel["data"]["Lula"][index]
            flavio = panel["data"]["Flávio"][index]
            top_y, bottom_y = py(max(lula, flavio)), py(min(lula, flavio))
            canvas.line(
                px(index),
                top_y,
                px(index),
                bottom_y,
                stroke=INK,
                width=1.6,
                stroke_dasharray="4 4",
            )
            pill(
                canvas,
                px(index),
                (top_y + bottom_y) / 2,
                br(abs(lula - flavio), 0),
                WHITE,
                color=INK,
                size=17,
                stroke=INK,
            )

    canvas.text(
        60,
        base + 68,
        "O número dentro do pino é a diferença entre as duas linhas naquela rodada, em pontos. "
        "Em uma semana ela caiu de 9 para 4 no 1º turno e de 4 para 1 no 2º.",
        size=15,
        fill=INK,
    )
    canvas.text(
        60,
        base + 92,
        "Os dois painéis usam o mesmo tamanho de ponto no eixo vertical, então a "
        "inclinação de um é comparável à do outro.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


# ---------------------------------------------------------------- figura 2


def fig_gap_incerteza(data: dict) -> str:
    unc = data["uncertainty"]
    tops = data["toplines"]["august"]

    height = 356
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Diferença publicada entre Lula e Flávio nos dois turnos, com a margem "
            "de erro da diferença e a margem inflada pelo efeito de desenho."
        ),
    )

    x0, x1 = 250, 1116
    lo, hi = -5.0, 9.0
    scale = (x1 - x0) / (hi - lo)

    def px(value: float) -> float:
        return x0 + (value - lo) * scale

    axis_y = 288
    canvas.line(x0 - 10, axis_y, x1 + 10, axis_y, stroke=INK, width=1.6)
    for tick in range(-4, 9, 2):
        canvas.line(px(tick), axis_y, px(tick), axis_y + 7, stroke=INK, width=1.4)
        canvas.label(
            px(tick), axis_y + 26, signed(tick, 0) if tick else "0", anchor="middle"
        )
    canvas.label(x1 + 10, axis_y + 26, "pontos", anchor="end")

    # eixo do empate
    canvas.line(px(0), 88, px(0), axis_y, stroke=INK, width=3)
    pill(canvas, px(0), 76, "EMPATE", INK, size=14, family=MONO)

    hatch = canvas.hatch("plc-gap-deff", INK, 0.16)
    canvas.rect(690, 26, 26, 14, INK, rx=3)
    canvas.text(
        726,
        38,
        "margem da diferença sob amostra aleatória simples",
        size=14,
        fill=INK,
    )
    canvas.rect(690, 52, 26, 10, hatch, rx=3, stroke=INK, stroke_width=1)
    canvas.text(
        726,
        62,
        f"com o efeito de desenho da calibração por UF "
        f"({br(unc['deff_uf_calibration'], 3)})",
        size=14,
        fill=MUTED,
    )

    rows = [
        {
            "y": 132,
            "title": "1º turno",
            "sub": f"Lula {tops['first'][0]} × Flávio {tops['first'][1]}",
            "gap": unc["first_gap"],
            "srs": unc["first_gap_moe_srs"],
            "deff": unc["first_gap_moe_deff"],
            "note": "a ponta de baixo encosta no empate: sobra 0,1 ponto",
            "tone": AMBER,
        },
        {
            "y": 224,
            "title": "2º turno",
            "sub": f"Lula {tops['runoff'][0]} × Flávio {tops['runoff'][1]}",
            "gap": unc["runoff_gap"],
            "srs": unc["runoff_gap_moe_srs"],
            "deff": unc["runoff_gap_moe_deff"],
            "note": "o intervalo contém o empate e contém Flávio na frente",
            "tone": RED,
        },
    ]

    for row in rows:
        y = row["y"]
        canvas.text(
            232, y - 2, row["title"], size=19, fill=INK, weight="800", anchor="end"
        )
        canvas.label(232, y + 20, row["sub"], anchor="end")

        gap, srs, deff = row["gap"], row["srs"], row["deff"]
        canvas.rect(
            px(gap - deff),
            y + 15,
            (2 * deff) * scale,
            10,
            hatch,
            rx=5,
            stroke=INK,
            stroke_width=1,
        )
        canvas.rect(px(gap - srs), y - 12, (2 * srs) * scale, 24, INK, rx=12)
        pill(canvas, px(gap), y, signed(gap, 0), WHITE, color=INK, size=17, pad=9)
        if row["title"].startswith("1"):
            canvas.label(
                px(gap), y - 26, "diferença publicada", anchor="middle", fill=INK
            )

        low = gap - srs
        if abs(low) < 1.2:
            canvas.text(
                px(low) + 10,
                y - 24,
                signed(low, 1),
                size=17,
                fill=INK,
                weight="800",
            )
        else:
            canvas.text(
                px(low) - 14,
                y + 6,
                signed(low, 1),
                size=17,
                fill=INK,
                weight="800",
                anchor="end",
            )
        canvas.text(
            px(gap + srs) + 14,
            y + 6,
            signed(gap + srs, 1),
            size=17,
            fill=INK,
            weight="800",
        )
        canvas.text(
            px(low) + 8,
            y + 46,
            row["note"],
            size=15,
            fill=row["tone"],
            weight="700",
        )

    canvas.text(
        60,
        336,
        "A calibração por UF alarga a margem em 0,06 ponto. O que sustenta a incerteza "
        "não é o desenho, são as 2.002 entrevistas.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


# ---------------------------------------------------------------- figura 3


def fig_movimento_segmentos(data: dict) -> str:
    july = data["toplines"]["july"]["first"]
    august = data["toplines"]["august"]["first"]
    labels = data["toplines"]["july"]["labels"]
    bands = data["income_mechanics"]["waves"]

    moves = sorted(
        (
            {
                "label": labels[i],
                "july": july[i],
                "august": august[i],
                "delta": august[i] - july[i],
            }
            for i in range(len(labels))
        ),
        key=lambda row: (-row["delta"], -row["august"]),
    )
    lost = -sum(row["delta"] for row in moves if row["delta"] < 0)
    lula_lost = -next(row["delta"] for row in moves if row["label"] == "Lula")

    height = 520
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Variação de cada opção de voto entre 27 de julho e 3 de agosto no "
            "primeiro turno, e vantagem de Lula no segundo turno por faixa de renda."
        ),
    )

    kicker(canvas, 40, 48, "1º TURNO, VARIAÇÃO DE 27/07 PARA 03/08, EM PONTOS", INK)
    kicker(canvas, 700, 48, "2º TURNO, VANTAGEM DE LULA POR FAIXA DE RENDA", INK)
    canvas.line(672, 30, 672, 470, stroke=LINE, width=1.5)

    # ---- painel esquerdo
    ax0, ax1 = 268, 640
    lo, hi = -3.0, 5.0
    scale = (ax1 - ax0) / (hi - lo)

    def apx(value: float) -> float:
        return ax0 + (value - lo) * scale

    row_y, step = 112, 34
    canvas.line(
        apx(0), row_y - 26, apx(0), row_y + step * len(moves) - 14, stroke=INK, width=2
    )
    canvas.label(apx(0), row_y - 34, "sem mudança", anchor="middle")

    for index, move in enumerate(moves):
        y = row_y + index * step
        color = OPTION_COLOR.get(move["label"], MUTED)
        name = LONG_LABEL.get(move["label"], move["label"])
        canvas.text(150, y + 6, name, size=16, fill=INK, weight="700", anchor="end")
        canvas.label(250, y + 6, f"{move['july']} → {move['august']}", anchor="end")

        delta = move["delta"]
        if delta == 0:
            canvas.circle(apx(0), y, 7, WHITE)
            canvas.circle(apx(0), y, 7, "none", stroke=GRAY, stroke_width=3)
            canvas.text(apx(0) + 16, y + 6, "0", size=16, fill=MUTED, weight="700")
            continue
        left = apx(min(0, delta))
        canvas.rect(
            left,
            y - 12,
            abs(delta) * scale,
            24,
            color,
            rx=3,
            stroke=OLIVE if color == LIME else None,
            stroke_width=1.6 if color == LIME else None,
        )
        if delta > 0:
            canvas.text(
                apx(delta) + 12,
                y + 6,
                signed(delta, 0),
                size=17,
                fill=INK,
                weight="800",
            )
        else:
            canvas.text(
                apx(delta) - 12,
                y + 6,
                signed(delta, 0),
                size=17,
                fill=INK,
                weight="800",
                anchor="end",
            )

    canvas.text(
        40,
        row_y + step * len(moves) + 20,
        f"Flávio subiu {br(moves[0]['delta'], 0)}. "
        f"Dos {br(lost, 0)} pontos que saíram de alguma opção, {br(lula_lost, 0)} era de Lula.",
        size=17,
        fill=INK,
        weight="800",
    )

    # ---- painel direito
    bx0, bx1 = 838, 1128
    blo, bhi = -16.0, 38.0
    bscale = (bx1 - bx0) / (bhi - blo)

    def bpx(value: float) -> float:
        return bx0 + (value - blo) * bscale

    canvas.line(bpx(0), 96, bpx(0), 424, stroke=INK, width=2)
    canvas.label(bpx(0), 88, "empate", anchor="middle")

    brow, bstep = 148, 84
    for index, band in enumerate(bands["july"]["bands"]):
        y = brow + index * bstep
        name = band["band"]
        old = band["vote_gap"]
        new = bands["august"]["bands"][index]["vote_gap"]
        canvas.text(824, y + 6, name, size=17, fill=INK, weight="700", anchor="end")

        canvas.line(bpx(old), y, bpx(new), y, stroke=GRAY, width=3)
        arrow(canvas, bpx(old), y, bpx(new), y, INK, width=3, head=10)
        canvas.circle(bpx(old), y, 8, WHITE)
        canvas.circle(bpx(old), y, 8, "none", stroke=GRAY, stroke_width=3)
        canvas.circle(bpx(new), y, 8, RED if new > 0 else BLUE)

        canvas.label(bpx(old), y - 18, f"27/07 {signed(old, 0)}", anchor="middle")
        canvas.text(
            bpx(new),
            y + 34,
            f"03/08 {signed(new, 0)}",
            size=16,
            fill=RED if new > 0 else BLUE,
            weight="800",
            anchor="middle",
        )
        canvas.text(
            824,
            y + 28,
            signed(new - old, 0),
            size=22,
            fill=INK,
            weight="800",
            anchor="end",
            font_family=DISPLAY,
        )

    canvas.text(
        700,
        446,
        "Vantagem = Lula menos Flávio dentro da faixa.",
        size=15,
        fill=MUTED,
    )
    canvas.text(
        700,
        468,
        "Ponto vermelho, Lula à frente; ponto azul, Flávio.",
        size=15,
        fill=MUTED,
    )
    canvas.text(
        40,
        502,
        "Percentuais publicados nas duas rodadas. A Nexus não divulga a matriz que "
        "ligaria uma opção à outra, então nenhuma seta aqui descreve eleitor migrando.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


# ---------------------------------------------------------------- figura 4


def fig_religiao_composicao(data: dict) -> str:
    religion = data["uncontrolled"]["religion"]
    runoff = religion["runoff"]
    names = religion["labels"]
    july, august = runoff["july_profile"], runoff["august_profile"]

    height = 440
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Composição religiosa da amostra nas duas ondas e o segundo turno "
            "recalculado sobre o perfil religioso de julho."
        ),
    )

    kicker(canvas, 40, 44, "COMPOSIÇÃO RELIGIOSA DA AMOSTRA", INK)
    kicker(canvas, 620, 44, "2º TURNO, LULA × FLÁVIO", INK)
    canvas.line(586, 26, 586, 410, stroke=LINE, width=1.5)

    col_top, col_h = 106, 246
    tones = [NAVY, AMBER, MUTED, LINE]
    inks = [WHITE, WHITE, WHITE, INK]

    columns = [(212, july, "27/07"), (404, august, "03/08")]
    centers = {}
    for cx, profile, when in columns:
        canvas.label(
            cx + 58, col_top - 16, when, anchor="middle", fill=INK, weight="700"
        )
        offset = col_top
        for index, value in enumerate(profile):
            band = value / 100 * col_h
            canvas.rect(
                cx, offset, 116, band, tones[index], stroke=WHITE, stroke_width=2
            )
            canvas.text(
                cx + 58,
                offset + band / 2 + 7,
                br(value, 0),
                size=19,
                fill=inks[index],
                weight="800",
                anchor="middle",
            )
            centers.setdefault(when, []).append(offset + band / 2)
            offset += band

    name_y = declutter(
        centers["27/07"],
        [22] * len(names),
        gap=6,
    )
    for index, name in enumerate(names):
        canvas.text(
            200, name_y[index] + 6, name, size=16, fill=INK, weight="700", anchor="end"
        )

    for index, name in enumerate(names):
        delta = august[index] - july[index]
        y = (centers["27/07"][index] + centers["03/08"][index]) / 2
        color = RED if delta < 0 else (OLIVE if delta > 0 else GRAY)
        if delta:
            arrow(
                canvas,
                338,
                centers["27/07"][index],
                396,
                centers["03/08"][index],
                color,
            )
        canvas.text(
            367,
            y + (-12 if delta else 6),
            signed(delta, 0),
            size=19,
            fill=color,
            weight="800",
            anchor="middle",
        )

    # ---- barras do 2º turno
    bx0 = 900
    bscale = 240 / 50
    hatch_lula = canvas.hatch("plc-rel-lula", RED, 0.20)
    hatch_flavio = canvas.hatch("plc-rel-flavio", BLUE, 0.20)
    hatch_gap = canvas.hatch("plc-rel-gap", INK, 0.22)

    groups = [
        {
            "kicker": ["PUBLICADO EM 03/08"],
            "values": runoff["august_published"],
            "solid": True,
        },
        {
            "kicker": ["REPRODUZIDO PELO MODELO"],
            "values": runoff["august_reproduced"],
            "solid": True,
        },
        {
            "kicker": ["MESMAS RESPOSTAS DE 03/08,", "PERFIL RELIGIOSO DE 27/07"],
            "values": runoff["counterfactual_august_on_july_profile"],
            "solid": False,
        },
    ]

    y = 96
    for group in groups:
        lula, flavio = group["values"][0], group["values"][1]
        for line, text in enumerate(group["kicker"]):
            canvas.label(618, y + 12 + line * 18, text, fill=INK)
        number_y = y + 42 + (len(group["kicker"]) - 1) * 18
        canvas.text(
            618,
            number_y,
            f"vantagem {signed(lula - flavio, 1)}",
            size=24,
            fill=INK,
            weight="800",
            family=DISPLAY,
        )
        # a vantagem em escala ampliada: 1 ponto vale 40 px, igual nos três blocos
        span = (lula - flavio) * 40
        canvas.rect(
            618,
            number_y + 10,
            span,
            12,
            INK if group["solid"] else hatch_gap,
            rx=2,
            stroke=None if group["solid"] else INK,
            stroke_width=None if group["solid"] else 1.2,
        )
        if group["solid"] and groups.index(group) == 0:
            canvas.label(618 + span + 10, number_y + 20, "escala ampliada", fill=MUTED)
        if not group["solid"]:
            canvas.label(618 + span + 10, number_y + 20, "inferência", fill=MUTED)
        for offset, (name, value, color, texture) in enumerate(
            (
                ("Lula", lula, RED, hatch_lula),
                ("Flávio", flavio, BLUE, hatch_flavio),
            )
        ):
            by = y + offset * 34
            fill = color if group["solid"] else texture
            canvas.rect(
                bx0,
                by,
                value * bscale,
                28,
                fill,
                rx=3,
                stroke=color if not group["solid"] else None,
                stroke_width=1.6 if not group["solid"] else None,
            )
            canvas.text(
                bx0 + 12,
                by + 20,
                name,
                size=15,
                fill=WHITE if group["solid"] else INK,
                weight="800",
            )
            canvas.text(
                bx0 + value * bscale + 10,
                by + 20,
                br(value, 1),
                size=17,
                fill=color,
                weight="800",
            )
        y += 106

    swing = runoff["gap_august_on_july_profile"] - (
        runoff["august_published"][0] - runoff["august_published"][1]
    )
    canvas.text(
        618,
        424,
        f"Só a troca do perfil religioso devolve {signed(swing, 1)} ponto de vantagem a Lula.",
        size=16,
        fill=INK,
        weight="700",
    )
    canvas.text(
        40,
        424,
        "Perfis publicados na p. 117 de julho e na p. 113 de agosto.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


# ---------------------------------------------------------------- figura 5


def fig_religiao_decomposicao(data: dict) -> str:
    religion = data["uncontrolled"]["religion"]

    height = 416
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Decomposição da variação de cada candidato entre composição religiosa "
            "da amostra, comportamento dentro de cada grupo e interação."
        ),
    )

    kicker(canvas, 40, 44, "1º TURNO", INK)
    kicker(canvas, 616, 44, "2º TURNO", INK)
    canvas.line(594, 26, 594, 320, stroke=LINE, width=1.5)

    lo, hi = -2.6, 4.4
    cells = [
        {"ballot": "first", "x0": 166, "x1": 560},
        {"ballot": "runoff", "x0": 742, "x1": 1136},
    ]
    who_rows = [("Lula", RED, 124), ("Flávio", BLUE, 244)]

    textures = {
        "Lula": canvas.hatch("plc-dec-lula", RED, 0.24),
        "Flávio": canvas.hatch("plc-dec-flavio", BLUE, 0.24),
        "inter": canvas.hatch("plc-dec-inter", MUTED, 0.20),
    }

    for cell in cells:
        entry = religion[cell["ballot"]]
        scale = (cell["x1"] - cell["x0"]) / (hi - lo)

        def px(value: float, x0=cell["x0"], scale=scale) -> float:
            return x0 + (value - lo) * scale

        canvas.label(px(0), 74, "0", anchor="middle", fill=INK, weight="700")
        for who, color, y in who_rows:
            parts = entry[who]
            interaction = round(
                parts["total"] - parts["composition"] - parts["behaviour"], 2
            )
            canvas.line(px(0), y - 34, px(0), y + 24, stroke=INK, width=2)

            canvas.text(
                cell["x0"] - 74,
                y - 6,
                who,
                size=21,
                fill=color,
                weight="800",
                anchor="middle",
            )
            canvas.text(
                cell["x0"] - 74,
                y + 24,
                signed(parts["total"], 2),
                size=26,
                fill=INK,
                weight="800",
                anchor="middle",
                font_family=DISPLAY,
            )
            canvas.label(cell["x0"] - 74, y + 44, "total", anchor="middle")

            steps = [
                ("composição", parts["composition"], textures[who], color, -1),
                ("comportamento", parts["behaviour"], textures[who], color, 1),
                ("interação", interaction, textures["inter"], MUTED, 2),
            ]
            cursor = 0.0
            for name, value, texture, tone, tier in steps:
                left = px(min(cursor, cursor + value))
                canvas.rect(
                    left,
                    y - 18,
                    abs(value) * scale,
                    36,
                    texture,
                    stroke=tone,
                    stroke_width=1.4,
                )
                center = px(cursor + value / 2)
                cursor += value

                text = f"{name} {signed(value, 2)}"
                half = width_of(text, 15) / 2
                spot = min(max(center, cell["x0"] - 60 + half), cell["x1"] - half)
                label_y = {-1: y - 28, 1: y + 40, 2: y + 66}[tier]
                if abs(spot - center) > 2 or tier == 2:
                    canvas.line(
                        center,
                        y + 18 if tier > 0 else y - 18,
                        spot,
                        label_y - (12 if tier > 0 else -6),
                        stroke=tone,
                        width=1.2,
                    )
                canvas.text(
                    spot,
                    label_y,
                    text,
                    size=15,
                    fill=tone,
                    weight="800",
                    anchor="middle",
                )

            canvas.line(px(cursor), y - 24, px(cursor), y + 24, stroke=INK, width=3.4)

    runoff_lula = religion["runoff"]["Lula"]
    runoff_flavio = religion["runoff"]["Flávio"]
    first_flavio = religion["first"]["Flávio"]
    canvas.rect(40, 334, 26, 14, textures["Lula"], stroke=RED, stroke_width=1.2)
    canvas.text(
        76,
        346,
        "trama = decomposição descritiva sobre percentuais publicados, nenhum elo medido",
        size=14,
        fill=MUTED,
    )
    canvas.text(
        40,
        374,
        "No 2º turno a composição responde por "
        f"{br(100 * runoff_lula['composition'] / runoff_lula['total'], 0)}% do recuo de Lula "
        f"e por {br(100 * runoff_flavio['composition'] / runoff_flavio['total'], 0)}% do avanço "
        "de Flávio.",
        size=15,
        fill=INK,
    )
    canvas.text(
        40,
        394,
        "No 1º turno o avanço de Flávio é sobretudo comportamento, "
        f"{br(first_flavio['behaviour'], 2)} contra {br(first_flavio['composition'], 2)}.",
        size=15,
        fill=INK,
    )
    return canvas.render()


# ---------------------------------------------------------------- figura 6


def fig_margens_congeladas(data: dict) -> str:
    unc = data["uncontrolled"]
    quota_report = {name.lower() for name in unc["declared_quota_report"]}
    quota_tse = {name.lower() for name in unc["declared_quota_tse"]}
    weighting = {name.lower() for name in unc["declared_weighting_extra_tse"]}

    waves = []
    for key in ("sex", "age", "education", "region"):
        pair = unc["controlled_values"][key]
        waves.append((key, pair[0], pair[1]))
    waves.append(
        (
            "income",
            unc["income"]["first"]["july_profile"],
            unc["income"]["first"]["august_profile"],
        )
    )
    waves.append(
        (
            "religion",
            unc["religion"]["first"]["july_profile"],
            unc["religion"]["first"]["august_profile"],
        )
    )

    margins = []
    for key, july, august in waves:
        name = MARGIN_PT[key]
        low = name.lower()
        if low in quota_report and low in quota_tse:
            badge, tone = "cota", NAVY
        elif low in quota_tse:
            badge, tone = "cota só no TSE", NAVY
        elif low in weighting:
            badge, tone = "ponderação", AMBER
        else:
            badge, tone = "livre", RED
        margins.append(
            {
                "name": name,
                "shift": max(abs(a - j) for j, a in zip(july, august)),
                "july": july,
                "august": august,
                "badge": badge,
                "tone": tone,
            }
        )
    margins.sort(key=lambda row: row["shift"])

    height = 396
    canvas = Canvas(
        FULL,
        height,
        aria=(
            "Maior variação de categoria em cada margem da amostra entre as duas "
            "ondas: as margens travadas por cota repetem os mesmos dígitos, a "
            "religião muda 5 pontos."
        ),
    )

    base, top = 244, 78
    lo, hi = 0.0, 5.6

    def py(value: float) -> float:
        return base - (value - lo) / (hi - lo) * (base - top)

    for tick in range(0, 6):
        canvas.line(110, py(tick), 1140, py(tick), stroke=LINE, width=1)
        canvas.label(100, py(tick) + 5, br(tick, 0), anchor="end")
    canvas.line(110, base, 1140, base, stroke=INK, width=1.8)
    canvas.label(
        110, 44, "VARIAÇÃO MÁXIMA DE UMA CATEGORIA, EM PONTOS", fill=INK, weight="700"
    )

    canvas.label(100, 326, "27/07", anchor="end", fill=INK, weight="700")
    canvas.label(100, 348, "03/08", anchor="end", fill=INK, weight="700")

    width = (1180 - 140) / len(margins)

    frozen = [index for index, margin in enumerate(margins) if not margin["shift"]]
    if frozen:
        left = 100 + frozen[0] * width + 12
        right = 100 + (frozen[-1] + 1) * width - 12
        canvas.rect(
            left,
            208,
            right - left,
            44,
            "none",
            rx=10,
            stroke=NAVY,
            stroke_width=1.6,
            stroke_dasharray="7 6",
        )
        canvas.text(
            (left + right) / 2,
            198,
            "as margens de cota repetem os mesmos dígitos nas duas ondas",
            size=16,
            fill=NAVY,
            weight="700",
            anchor="middle",
        )

    for index, margin in enumerate(margins):
        cx = 100 + width / 2 + index * width
        shift = margin["shift"]
        if shift:
            canvas.rect(cx - 40, py(shift), 80, base - py(shift), margin["tone"], rx=3)
            canvas.text(
                cx,
                py(shift) - 14,
                br(shift, 1),
                size=34 if shift >= 5 else 24,
                fill=margin["tone"],
                weight="800",
                anchor="middle",
                font_family=DISPLAY,
            )
        else:
            canvas.rect(cx - 40, base - 5, 80, 5, margin["tone"], rx=2)
            canvas.text(
                cx,
                base - 16,
                br(0, 1),
                size=22,
                fill=margin["tone"],
                weight="800",
                anchor="middle",
                font_family=DISPLAY,
            )

        canvas.text(
            cx, 274, margin["name"], size=19, fill=INK, weight="800", anchor="middle"
        )
        pill(
            canvas,
            cx,
            296,
            margin["badge"],
            margin["tone"],
            size=13,
            family=MONO,
            pad=10,
        )
        canvas.label(
            cx,
            326,
            " · ".join(str(value) for value in margin["july"]),
            anchor="middle",
            fill=INK,
        )
        parts: list[tuple[str, str, bool]] = []
        for position, value in enumerate(margin["august"]):
            if position:
                parts.append((" · ", MUTED, False))
            moved = value != margin["july"][position]
            parts.append((str(value), margin["tone"] if moved else INK, moved))
        rich_text(canvas, cx, 348, parts)

    canvas.text(
        40,
        380,
        "Cota é a margem que o instituto obriga a bater. Ponderação é declarada na ficha "
        "do TSE sem virar cota. Livre não aparece em nenhum dos dois documentos.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    figures = {
        "serie_duplo": fig_serie_duplo(data),
        "gap_incerteza": fig_gap_incerteza(data),
        "movimento_segmentos": fig_movimento_segmentos(data),
        "religiao_composicao": fig_religiao_composicao(data),
        "religiao_decomposicao": fig_religiao_decomposicao(data),
        "margens_congeladas": fig_margens_congeladas(data),
    }
    write_fragments(OUT_PATH, figures)
    print(f"{OUT_PATH.relative_to(ROOT)}: {len(figures)} figuras")


if __name__ == "__main__":
    main()
