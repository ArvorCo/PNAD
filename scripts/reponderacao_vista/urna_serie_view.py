"""Série principal e placares finais, sem depender de JavaScript."""

from __future__ import annotations

import math
from datetime import date
from html import escape

from reponderacao_vista.charts import caminho, meses_no_intervalo
from reponderacao_vista.context import (
    COR,
    GREEN,
    INK,
    LINE,
    MESES,
    MUTED,
    PANEL,
    curto,
    sinal,
)
from reponderacao_vista.gaps import draw_bridges
from reponderacao_vista.urna_serie import KEYS, MODES, write
from svgkit import Canvas, br

LABELS = {"flavio": "Flávio", "lula": "Lula", "demais": "Demais candidaturas"}


def draw_segment(cv, points, color, mode):
    if points:
        cv.path(
            caminho(points),
            fill="none",
            stroke=color,
            stroke_width=3 if mode == "pnad" else 1.8,
            stroke_dasharray="7 5" if mode == "publicado" else None,
            opacity="0.7" if mode == "publicado" else "1",
        )


def series_svg(data):
    rows = data["serie"]
    dates = [date.fromisoformat(row["data"]) for row in rows]
    final, urn = data["final"], data["urna"]["validos"]
    values = [
        row[mode][key]
        for row in rows
        for mode in MODES
        for key in ("flavio", "lula")
        if row[mode] is not None
    ] + [urn[key] for key in ("flavio", "lula")]
    low = math.floor((min(values) - 2) / 5) * 5
    high = math.ceil((max(values) + 2) / 5) * 5
    left, right, top, bottom = 58, 858, 48, 337
    urn_x = 966
    span = max((dates[-1] - dates[0]).days, 1)

    def x(day):
        return left + (right - left) * (day - dates[0]).days / span

    def y(value):
        return bottom - (bottom - top) * (value - low) / (high - low)

    cv = Canvas(
        1180,
        430,
        aria="Agregador principal do primeiro turno em votos válidos. Média publicada tracejada e PNAD contínua até 03/10; resultado oficial de 04/10 em losangos separados à direita. A urna não entra na média.",
    )
    cv.rect(0, 0, cv.width, cv.height, PANEL)
    for tick in range(low, high + 1, 5):
        cv.line(left, y(tick), right, y(tick), stroke=LINE)
        cv.label(left - 9, y(tick) + 4, f"{tick}%", anchor="end", size=13)
    cv.line(left, bottom, right, bottom, stroke=INK)
    cv.label(left, bottom + 24, curto(rows[0]["data"]), size=13)
    for month in meses_no_intervalo(dates[0], dates[-1]):
        if (dates[-1] - month).days < 10:
            continue
        cv.label(
            x(month),
            bottom + 24,
            f"{MESES[month.month - 1]}/26",
            anchor="middle",
            size=13,
        )
    cv.label(right, bottom + 24, curto(final["data"]), anchor="end", size=13)
    cv.rect(904, 36, 252, 328, "#192e2b06", rx=8)
    cv.text(925, 25, "URNA · 04/10", size=13, weight=700, fill=INK)
    cv.text(left, 25, "MÉDIA MÓVEL · 7 DIAS · MESMAS CASAS", size=12, fill=MUTED)
    cv.line(
        right, top, right, bottom, stroke=INK, stroke_dasharray="3 5", opacity="0.4"
    )
    for key in ("flavio", "lula"):
        color = COR[key]
        for mode in MODES:
            series = [row[mode][key] if row[mode] else None for row in rows]
            draw_bridges(cv, dates, series, x, y, color, mode, LABELS[key])
            segment = []

            for day, value in zip(dates, series, strict=True):
                if value is None:
                    draw_segment(cv, segment, color, mode)
                    segment = []
                else:
                    segment.append((x(day), y(value)))
            draw_segment(cv, segment, color, mode)
            cv.circle(
                right,
                y(final[mode][key]),
                4.5,
                color if mode == "pnad" else PANEL,
                stroke=color,
                stroke_width=2,
            )
        # Ponte descritiva PNAD→urna; não acrescenta o observado à média.
        cv.line(
            right + 8,
            y(final["pnad"][key]),
            urn_x - 10,
            y(urn[key]),
            stroke=color,
            width=1.5,
            stroke_dasharray="5 5",
            opacity="0.55",
        )
        cy = y(urn[key])
        cv.add(
            f'<g data-urna-candidato="{key}" data-validos="{urn[key]}"><title>{LABELS[key]} na urna: {br(urn[key], 2)}% dos válidos</title>'
        )
        cv.path(
            f"M{urn_x} {cy-7}L{urn_x+7} {cy}L{urn_x} {cy+7}L{urn_x-7} {cy}Z", fill=color
        )
        cv.add("</g>")
    # Rótulos independentes evitam colisões quando os líderes ficam próximos.
    positions = sorted((y(urn[k]), k) for k in ("flavio", "lula"))
    placed = max(top + 20, positions[0][0] - 19)
    for cy, key in positions:
        label_y = max(cy - 19, placed)
        cv.line(urn_x + 10, cy, 995, label_y + 14, stroke=COR[key], width=1)
        cv.text(1005, label_y, LABELS[key], size=14, fill=COR[key], weight=700)
        cv.text(
            1005,
            label_y + 26,
            f"{br(urn[key], 2)}%",
            size=23,
            fill=COR[key],
            weight=700,
        )
        placed = label_y + 68
    cv.line(left, 389, left + 32, 389, stroke=INK, width=3)
    cv.text(left + 42, 394, "PNAD", size=13, fill=MUTED)
    cv.line(172, 389, 204, 389, stroke=INK, width=1.8, stroke_dasharray="7 5")
    cv.text(214, 394, "Publicada", size=13, fill=MUTED)
    cv.text(
        337, 394, "Azul: Flávio · vermelho: Lula · losango: urna", size=13, fill=MUTED
    )
    cv.text(
        left,
        417,
        "Pontilhado: lacuna sem média. Ponte à direita: diferença até a urna; fora da média.",
        size=12,
        fill=MUTED,
    )
    return cv.render()


def candidate_card(key, data):
    final, urn = data["final"], data["urna"]["validos"]
    rows = []
    color = COR.get(key, GREEN)
    for mode, label in (("publicado", "Média publicada"), ("pnad", "Média PNAD")):
        value = final[mode][key]
        change = final["urna_menos_media_pp"][mode][key]
        rows.append(
            f'<div class="us-comparison" data-modo="{mode}" data-validos="{value}">'
            f"<div><span>{label}</span><b>{br(value, 2)}%</b></div>"
            f'<div class="us-bar" aria-hidden="true"><i style="width:{value}%"></i><em style="left:{urn[key]}%"></em></div>'
            f"<small>Urna − média: <strong>{sinal(change, 2)} pp</strong></small></div>"
        )
    return (
        f'<article class="us-candidate" data-candidato="{key}" style="--us-color:{color}">'
        f'<h3>{LABELS[key]}</h3><p class="us-score">{br(urn[key], 2)}<span>%</span></p>'
        '<p class="us-score-label">Resultado na urna · 04/10</p>'
        + "".join(rows)
        + "</article>"
    )


def section(data):
    history = write(data)
    final, urn = history["final"], history["urna"]["validos"]
    gaps = {mode: final[mode]["flavio"] - final[mode]["lula"] for mode in MODES}
    urn_gap = urn["flavio"] - urn["lula"]
    notes = []
    for poll in final["pesquisas"]:
        tags = []
        if poll["sem_cruzamento"]:
            tags.append("cruzamento parcial; demais nomes mantidos no publicado")
        if poll["perfil_renda"] == "hipotese_onda_anterior":
            tags.append("perfil de renda assumido da onda anterior")
        note = " · " + "; ".join(tags) if tags else ""
        notes.append(
            f'<li><a href="#pesquisa-{escape(poll["id"], quote=True)}">{escape(poll["instituto"])}</a>'
            f' · divulgada em {curto(poll["divulgacao"])}{note}</li>'
        )
    return (
        '<section id="agregador-urna" class="chapter us-section"><div class="wrap">'
        '<p class="eyebrow">1º turno · agregador principal · votos válidos</p>'
        "<h2>Das pesquisas<br><em>à urna.</em></h2>"
        '<p class="lead">A trajetória das médias e o resultado oficial, sob o mesmo denominador.</p>'
        '<div class="us-summary">'
        f'<div><span>Média final · {curto(final["data"])}</span><strong>{final["n_institutos"]} casas</strong>'
        f'<small>Janela {curto(final["inicio_janela"])} a {curto(final["data"])} · peso igual</small></div>'
        f"<div><span>Diferença Flávio − Lula</span><strong>{sinal(urn_gap, 2)} pp <small>na urna</small></strong>"
        f'<small>Publicada: {sinal(gaps["publicado"], 2)} pp · PNAD: {sinal(gaps["pnad"], 2)} pp</small></div>'
        f'<div><span>Da média PNAD à urna</span><strong>{sinal(urn_gap-gaps["pnad"], 2)} pp</strong>'
        "<small>Mudança na diferença Flávio − Lula</small></div></div>"
        '<figure class="chart-shell"><h3>A série principal até o resultado</h3>'
        f'<div class="fig us-timeline" tabindex="0" role="region" aria-label="Evolução das médias até a urna">{series_svg(history)}</div>'
        '<figcaption class="note">Linhas: médias das pesquisas em válidos, com todas as candidaturas no denominador. '
        "Losangos: urna de 04/10, separada da curva. A ponte mostra a mudança desde a média PNAD final; o resultado não entra na média. "
        "No celular, deslize para ver o fechamento à direita.</figcaption></figure>"
        '<h3>Média das últimas pesquisas × urna</h3><div class="us-candidates">'
        + "".join(candidate_card(key, history) for key in KEYS)
        + f'</div><p class="note">Barra: média; marca vertical: urna. Todas as parcelas em % dos válidos. '
        "Urna − média positivo indica que a votação final ficou acima da média; negativo, abaixo. "
        "A diferença reúne erro das pesquisas e escolhas finais; não identifica transferência individual de votos. "
        f'A comparação publicada/PNAD usa as mesmas {final["n_institutos"]} casas com renda; não é a média inclusiva de todos os institutos.</p>'
        '<details class="urna-details"><summary>Conferir as casas, a regra e os dados da série</summary>'
        f'<p>{escape(history["regra"])}</p><p class="note">{escape(history["limite"])}</p>'
        '<ul class="us-houses">' + "".join(notes) + "</ul>"
        '<p class="note">Perfil de renda final não publicado: Datafolha e Quaest condicionam o ajuste ao perfil assumido da onda anterior. '
        "Isso continua sendo uma hipótese, mesmo após a urna. A predição algorítmica arquivada permanece separada desta média descritiva. "
        '<a href="predicao_2026_1T_presidente.html">Ver a predição do 1º turno →</a></p>'
        '<p><a href="assets/reponderacao_urna_serie_1t.json">Série e auditoria (JSON)</a> · '
        '<a href="assets/reponderacao_urna_serie_1t.csv">Série e urna (CSV)</a> · '
        '<a href="apuracao_1o_turno_2026.html#pesquisas">Resultado oficial e auditoria completa</a></p>'
        "</details></div></section>"
    )
