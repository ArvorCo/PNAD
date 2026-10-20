"""Séries documentais em tempo real, com lacunas de renda explícitas."""

from datetime import date
from math import ceil, floor

from reponderacao_vista.context import COR, INK, LINE, MUTED, PANEL
from reponderacao_vista.historico_2t import CUTOFF, tip
from reponderacao_vista.markers import (
    abre_alvo,
    area_alvo,
    fecha_alvo,
    registra_tip,
)
from svgkit import Canvas


def ordinal(value):
    return date.fromisoformat(value).toordinal()


def segments(rows, key):
    """Não interpolar renda ausente, versões substituídas ou mudança de turno."""
    result, current = [], []
    for row in rows:
        if row.get("substituida"):
            continue
        if row[key] is None:
            if current:
                result.append(current)
            current = []
            continue
        if current and current[-1]["fase"] != row["fase"]:
            result.append(current)
            current = []
        current.append(row)
    if current:
        result.append(current)
    return result


def chart(rows):
    if not rows:
        return ""
    cv = Canvas(380, 270, f'{rows[0]["instituto"]}: histórico Flávio versus Lula')
    left, right, top, bottom = 34, 362, 38, 210
    first, last = ordinal(rows[0]["campo"]["fim"]), ordinal(rows[-1]["campo"]["fim"])
    low_x, high_x = (first - 1, last + 1) if first == last else (first, last)

    def x(day):
        return left + (ordinal(day) - low_x) / (high_x - low_x) * (right - left)

    values = [
        p[k][c]
        for p in rows
        for k in ("placar", "pnad")
        if p[k]
        for c in COR
        if c in ("flavio", "lula")
    ]
    low, high = floor(min(values) / 5) * 5 - 2, ceil(max(values) / 5) * 5 + 2

    def y(value):
        return bottom - (value - low) / (high - low) * (bottom - top)

    cutoff = ordinal(CUTOFF)
    if first <= cutoff < last:
        boundary = x(CUTOFF)
        cv.rect(left, top, boundary - left, bottom - top, "#eeede4")
        cv.line(boundary, top, boundary, bottom, MUTED, 1, stroke_dasharray="3 3")
        cv.text(
            boundary - 4, top - 8, "04/10 · 1º turno", size=10, anchor="end", fill=MUTED
        )
    else:
        cv.text(
            left,
            top - 8,
            "Simulações pré-1º turno" if last <= cutoff else "Disputa após o 1º turno",
            size=11,
            fill=MUTED,
        )
    for value in range(ceil(low / 5) * 5, floor(high / 5) * 5 + 1, 5):
        cv.line(left, y(value), right, y(value), LINE, 0.7)
        cv.label(left - 6, y(value) + 4, str(value), size=11, anchor="end", fill=MUTED)
    for index in range(5 if first != last else 1):
        day = round(first + (last - first) * index / 4)
        day_date = date.fromordinal(day)
        cv.label(
            x(day_date.isoformat()),
            bottom + 19,
            day_date.strftime("%d/%m"),
            size=10,
            anchor="middle",
            fill=MUTED,
        )
    for candidate in ("flavio", "lula"):
        color = COR[candidate]
        for key in ("placar", "pnad"):
            for segment in segments(rows, key):
                if len(segment) < 2:
                    continue
                path = "M" + "L".join(
                    f'{x(p["campo"]["fim"]):.2f},{y(p[key][candidate]):.2f}'
                    for p in segment
                )
                cv.path(
                    d=path,
                    fill="none",
                    stroke=color,
                    stroke_width=1.5 if key == "placar" else 2,
                    stroke_dasharray="4 3" if key == "placar" else None,
                )
    for poll in rows:
        key = registra_tip(f'history2t|{poll["id"]}', tip(poll))
        for candidate in ("flavio", "lula"):
            color = COR[candidate]
            for kind in ("placar", "pnad"):
                if poll[kind] is None:
                    continue
                px, py = x(poll["campo"]["fim"]), y(poll[kind][candidate])
                label = f'{poll["campo"]["fim"]}: {candidate}, {kind}, {poll[kind][candidate]:.2f}%'
                abre_alvo(cv, key, label)
                cv.circle(
                    px,
                    py,
                    3.5 if kind == "placar" else 2.5,
                    PANEL if kind == "placar" else color,
                    stroke=color,
                    stroke_width=1.5,
                )
                area_alvo(cv, px, py, 5)
                fecha_alvo(cv)
    base = (
        "votos válidos"
        if rows[0]["denominador"] == "validos"
        else "total de entrevistados"
    )
    cv.text(
        left,
        250,
        f"% do {base}" if base.startswith("total") else f"% dos {base}",
        size=11,
        fill=INK,
    )
    return cv.render()
