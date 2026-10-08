"""Histórico de cada casa em válidos, com referências horizontais da urna."""

import math

from reponderacao_vista.context import (
    COR,
    LINE,
    MUTED,
    PANEL,
    PAR,
    PESQUISAS,
    curto,
)
from reponderacao_vista.markers import alvo_onda, area_alvo, fecha_alvo
from reponderacao_vista.urna_dados import URNA, comparison
from svgkit import Canvas, br


def instituto_svg(name):
    rows = [(p, comparison(p)) for p in PESQUISAS if p["instituto"] == name]
    rows = [(p, c) for p, c in rows if c is not None]
    cv = Canvas(
        380,
        270,
        aria=f"{name}, primeiro turno em votos válidos. Referências horizontais: resultado da urna; círculos: publicado e PNAD.",
    )
    cv.rect(0, 0, 380, 270, PANEL)
    if not rows:
        cv.text(16, 90, "Sem vetor compatível para comparar", size=13, fill=MUTED)
        cv.text(16, 112, "com os votos válidos da urna.", size=13, fill=MUTED)
        return cv.render()
    values = [
        c[m]["validos"][k] for _, c in rows for m in ("publicado", "pnad") for k in PAR
    ] + [URNA[k] for k in PAR]
    low = math.floor((min(values) - 2) / 5) * 5
    high = math.ceil((max(values) + 2) / 5) * 5
    left, right, top, bottom = 38, 363, 26, 208

    def y(v):
        return bottom - (bottom - top) * (v - low) / (high - low)

    def x(i):
        return (
            (left + right) / 2
            if len(rows) == 1
            else left + 12 + (right - left - 24) * i / (len(rows) - 1)
        )

    for tick in range(low, high + 1, 5):
        cv.line(left, y(tick), right, y(tick), stroke=LINE)
        cv.label(left - 6, y(tick) + 4, str(tick), anchor="end", size=11)
    for k in PAR:
        cv.line(
            left,
            y(URNA[k]),
            right,
            y(URNA[k]),
            stroke=COR[k],
            width=1.5,
            stroke_dasharray="2 4",
        )
        for mode in ("publicado", "pnad"):
            points = [(x(i), y(c[mode]["validos"][k])) for i, (_, c) in enumerate(rows)]
            if len(points) > 1:
                cv.path(
                    "M" + "L".join(f"{px:.2f} {py:.2f}" for px, py in points),
                    fill="none",
                    stroke=COR[k],
                    stroke_width=1.5,
                    stroke_dasharray="4 3" if mode == "publicado" else None,
                )
            for (p, _), (px, py) in zip(rows, points, strict=True):
                alvo_onda(cv, p, "1t")
                cv.circle(
                    px,
                    py,
                    4.2,
                    PANEL if mode == "publicado" else COR[k],
                    stroke=COR[k],
                    stroke_width=1.5,
                )
                area_alvo(cv, px, py, 8)
                fecha_alvo(cv)
    step = max(1, math.ceil(len(rows) / 6))
    for i, (p, _) in enumerate(rows):
        if (len(rows) - 1 - i) % step == 0:
            cv.label(x(i), 229, curto(p["campo"]["fim"]), anchor="middle", size=10)
    cv.text(
        left,
        253,
        f'Urna: Lula {br(URNA["lula"], 2)} · Flávio {br(URNA["flavio"], 2)}',
        size=12,
        fill=MUTED,
    )
    return cv.render()
