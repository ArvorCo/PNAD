#!/usr/bin/env python3
"""Diagrama de transferência do 1º para o 2º turno, BTG/Nexus de 03/08/2026.

A Nexus publica o cruzamento de voto para o eleitorado dos seis candidatos
menores (relatório, p. 51). Essas fitas são medição e aparecem sólidas. As quatro
linhas que o instituto não abre (base do próprio Lula, base do próprio Flávio,
branco/nulo e NS do 1º turno) são estimadas por IPF e aparecem hachuradas. A
distinção é a informação mais importante do gráfico.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import (  # noqa: E402
    AMBER,
    FULL,
    GRAY,
    LIME,
    MUTED,
    RED,
    SKY,
    Canvas,
    br,
    write_fragments,
)

DATA = ROOT / "docs/assets/nexus_btg_082026_1_data.json"
OUTPUT = ROOT / "docs/assets/figuras/nexus_082026_transferencia.json"

DEST_COLORS = [RED, SKY, LIME, GRAY]
LIGHT = "#e8ecf4"


def sankey(data: dict) -> str:
    transfer = data["transfer"]
    matrix = transfer["matrix"]
    rows = transfer["row_targets_scaled"]
    cols = transfer["column_targets"]
    sources = transfer["sources"]
    destinations = transfer["destinations"]
    measured = set(transfer["measured_rows"])

    canvas = Canvas(
        FULL, 740, aria="Transferência estimada do primeiro para o segundo turno"
    )
    solid = {}
    hatched = {}
    for j, color in enumerate(DEST_COLORS):
        hatched[j] = canvas.hatch(f"sank-h{j}", color, 0.16)
        solid[j] = color

    top, bottom = 92, 60
    usable = 740 - top - bottom
    bar_w = 15
    x_left, x_right = 250, 900
    total = sum(rows)
    gap_s, gap_t = 19, 22
    k = min(
        (usable - gap_s * (len(rows) - 1)) / total,
        (usable - gap_t * (len(cols) - 1)) / total,
    )

    src_pos, dst_pos = [], []
    cursor = top
    for value in rows:
        src_pos.append({"y": cursor, "h": value * k, "off": 0.0})
        cursor += value * k + gap_s
    cursor = top + (usable - sum(cols) * k - gap_t * (len(cols) - 1)) / 2
    for value in cols:
        dst_pos.append({"y": cursor, "h": value * k, "off": 0.0})
        cursor += value * k + gap_t

    canvas.text(
        x_left,
        44,
        "1º TURNO",
        size=13,
        fill=MUTED,
        family="IBM Plex Mono, ui-monospace, monospace",
        anchor="middle",
    )
    canvas.text(
        x_right + bar_w,
        44,
        "2º TURNO",
        size=13,
        fill=MUTED,
        family="IBM Plex Mono, ui-monospace, monospace",
        anchor="middle",
    )

    mid = (x_right - x_left - bar_w) * 0.46
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value < 0.06:
                continue
            h = value * k
            sy = src_pos[i]["y"] + src_pos[i]["off"]
            ty = dst_pos[j]["y"] + dst_pos[j]["off"]
            src_pos[i]["off"] += h
            dst_pos[j]["off"] += h
            x0, x1 = x_left + bar_w, x_right
            is_measured = i in measured
            canvas.path(
                f"M {x0} {sy} C {x0 + mid} {sy}, {x1 - mid} {ty}, {x1} {ty} "
                f"L {x1} {ty + h} C {x1 - mid} {ty + h}, {x0 + mid} {sy + h}, {x0} {sy + h} Z",
                fill=solid[j] if is_measured else hatched[j],
                opacity=0.62 if is_measured else 1,
                stroke=DEST_COLORS[j] if not is_measured else "none",
                stroke_width=0.6,
                stroke_opacity=0.5,
            )

    for i, value in enumerate(rows):
        pos = src_pos[i]
        is_measured = i in measured
        color = (
            RED
            if sources[i] == "Lula"
            else SKY if sources[i] == "Flávio" else (AMBER if is_measured else LIGHT)
        )
        canvas.rect(x_left, pos["y"], bar_w, max(pos["h"], 2), color)
        label = f"{sources[i]} {br(value, 1)}"
        canvas.text(
            x_left - 16,
            pos["y"] + pos["h"] / 2 + 5,
            label,
            size=15,
            weight=700,
            fill=AMBER if is_measured else "#07111f",
            anchor="end",
        )

    for j, value in enumerate(cols):
        pos = dst_pos[j]
        canvas.rect(x_right, pos["y"], bar_w, max(pos["h"], 2), DEST_COLORS[j])
        canvas.text(
            x_right + bar_w + 14,
            pos["y"] + pos["h"] / 2 + 5,
            f"{destinations[j]} {int(value)}",
            size=15,
            weight=700,
        )

    canvas.rect(60, 678, 22, 12, AMBER)
    canvas.text(
        90,
        688,
        "fita e rótulo em âmbar: cruzamento publicado pela Nexus na p. 51, medição do instituto",
        size=14,
        fill=MUTED,
    )
    canvas.rect(60, 704, 22, 12, canvas.hatch("sank-legend", SKY, 0.16))
    canvas.text(
        90,
        714,
        "fita hachurada: estimativa por IPF nas quatro origens que a Nexus não publica",
        size=14,
        fill=MUTED,
    )
    return canvas.render()


def pool_medido(data: dict) -> str:
    """O que o próprio instituto mediu sobre o pool dos candidatos menores."""
    pool = data["transfer"]["measured_pool"]
    canvas = Canvas(
        FULL, 340, aria="Destino medido do eleitorado dos seis candidatos menores"
    )

    left, right = 60, 60
    span = FULL - left - right
    total = pool["pool_points"]
    parts = [
        ("Flávio", pool["to_flavio"], SKY),
        ("Branco ou nulo", pool["to_blank_or_null"], LIME),
        ("Lula", pool["to_lula"], RED),
        ("Não sabe", pool["to_undecided"], GRAY),
    ]

    canvas.text(
        left,
        44,
        "Para onde vai o eleitorado dos seis candidatos menores",
        size=19,
        weight=700,
    )
    canvas.label(
        left,
        68,
        f"{br(total, 1)} pontos do 1º turno, repartidos pelo cruzamento publicado na p. 51",
    )

    y, h = 104, 74
    x = left
    for name, value, color in parts:
        w = span * value / total
        canvas.rect(x, y, w, h, color)
        pct = 100 * value / total
        if w > 110:
            canvas.number(
                x + w / 2,
                y + h / 2 + 2,
                f"{br(pct, 1)}%",
                size=30,
                fill="#ffffff" if color != LIME else "#07111f",
                anchor="middle",
            )
            canvas.text(
                x + w / 2,
                y + h / 2 + 26,
                f"{br(value, 2)} pontos",
                size=13,
                fill="#ffffff" if color != LIME else "#07111f",
                anchor="middle",
            )
        canvas.text(x + w / 2, y - 14, name, size=15, weight=700, anchor="middle")
        x += w

    canvas.rect(left, 224, span, 2, AMBER)
    canvas.text(
        left,
        254,
        "Flávio capta 45,9% do pool. Para vencer no 1º turno precisaria de cerca de 68%.",
        size=18,
        weight=700,
    )
    canvas.text(
        left,
        282,
        "Quase um terço desse eleitorado escolhe branco ou nulo em vez dos dois finalistas.",
        size=16,
        fill=MUTED,
    )
    canvas.text(
        left,
        314,
        "Razão medida entre os dois finalistas: 2,35 a 1 para Flávio. Não é estimativa desta auditoria.",
        size=15,
        fill=AMBER,
        weight=700,
    )
    return canvas.render()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    figures = {
        "transferencia_sankey": sankey(data),
        "transferencia_pool": pool_medido(data),
    }
    write_fragments(OUTPUT, figures)
    print(
        json.dumps(
            {"output": str(OUTPUT), "figuras": list(figures)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
