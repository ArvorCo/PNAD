#!/usr/bin/env python3
"""Figuras do capítulo de renda do dossiê BTG/Nexus de 3 de agosto de 2026.

Quatro peças, na ordem em que o argumento se fecha:
  renda_penhasco  a composição da amostra contra a PNAD, ao lado do gradiente de
                  voto de cada faixa. O excesso está exatamente onde a vantagem
                  de Lula é enorme, e o resto da escala é praticamente plano.
  renda_cascata   a decomposição do deslocamento, faixa a faixa, do placar
                  publicado até o reponderado.
  renda_alavanca  o teorema: o que uma margem pode mover é limitado pelo produto
                  entre seu erro de calibração e sua inclinação política. Derruba
                  a hipótese de que renda seria a margem mais determinante.
  renda_virada    o ponto de virada e a comparação com a onda anterior.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import (  # noqa: E402
    AMBER,
    BLUE,
    FULL,
    GRAY,
    INK,
    LINE,
    MUTED,
    RED,
    SKY,
    Canvas,
    br,
    signed,
    write_fragments,
)

DATA = ROOT / "docs/assets/nexus_btg_082026_1_data.json"
OUTPUT = ROOT / "docs/assets/figuras/nexus_082026_renda.json"


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def penhasco(data: dict) -> str:
    """Composição por faixa contra a PNAD, com o gradiente de voto embaixo."""
    mech = data["income_mechanics"]["waves"]["august"]
    bands = mech["bands"]
    pnad = data["benchmarks"]["pnad_income_2025"]["distribution"]
    faixas = ["Até 1 SM", "1 a 2 SM", "2 a 5 SM", "Mais de 5 SM"]

    canvas = Canvas(
        FULL,
        640,
        aria="Composição de renda da amostra contra a PNAD e vantagem de Lula em cada faixa",
    )
    left, right = 96, 92
    span = FULL - left - right
    slot = span / 4

    top_y, top_h = 96, 190
    top_max = 45.0

    canvas.text(left, 40, "Quanto pesa cada faixa", size=19, weight=700)
    canvas.label(left, 62, "% do eleitorado de 16 anos ou mais")
    canvas.text(
        FULL - right, 40, "amostra Nexus", size=15, fill=RED, weight=700, anchor="end"
    )
    canvas.text(
        FULL - right,
        62,
        "PNAD Contínua 2025",
        size=15,
        fill=BLUE,
        weight=700,
        anchor="end",
    )

    for tick in range(0, 50, 10):
        y = top_y + top_h - top_h * tick / top_max
        canvas.line(left, y, FULL - right, y, stroke=LINE)
        canvas.label(left - 12, y + 4, f"{tick}%", anchor="end")

    for i, band in enumerate(bands):
        cx = left + slot * i + slot / 2
        bar_w = 76
        poll = band["poll_pct"]
        target = band["pnad_pct"]
        ph = top_h * poll / top_max
        th = top_h * target / top_max
        canvas.rect(cx - bar_w - 6, top_y + top_h - ph, bar_w, ph, RED)
        canvas.rect(cx + 6, top_y + top_h - th, bar_w, th, BLUE)
        canvas.text(
            cx - bar_w / 2 - 6,
            top_y + top_h - ph - 12,
            f"{br(poll)}%",
            size=17,
            fill=RED,
            weight=700,
            anchor="middle",
        )
        canvas.text(
            cx + bar_w / 2 + 6,
            top_y + top_h - th - 12,
            f"{br(target)}%",
            size=17,
            fill=BLUE,
            weight=700,
            anchor="middle",
        )

        ci = pnad.get(
            faixas[i]
            .replace(" a ", "-")
            .replace("Mais de 5 SM", "5+ SM")
            .replace("Até 1 SM", "Até 1 SM")
        )
        if ci and "moe" in ci:
            scale = top_h / top_max
            y_low = top_y + top_h - ci["low"] * scale
            y_high = top_y + top_h - ci["high"] * scale
            xw = cx + 6 + bar_w / 2
            canvas.line(xw, y_low, xw, y_high, stroke="#0b2a86", width=2)
            canvas.line(xw - 7, y_high, xw + 7, y_high, stroke="#0b2a86", width=2)
            canvas.line(xw - 7, y_low, xw + 7, y_low, stroke="#0b2a86", width=2)

        canvas.line(
            left + slot * i,
            top_y + top_h,
            left + slot * (i + 1),
            top_y + top_h,
            stroke=INK,
            width=2,
        )
        canvas.text(
            cx, top_y + top_h + 28, faixas[i], size=17, weight=700, anchor="middle"
        )
        erro = band["error_pp"]
        cor = AMBER if abs(erro) >= 4 else MUTED
        canvas.text(
            cx,
            top_y + top_h + 50,
            f"erro {signed(erro, 2)} pp",
            size=14,
            fill=cor,
            family="IBM Plex Mono, ui-monospace, monospace",
            anchor="middle",
        )

    canvas.text(left, 410, "Quem cada faixa elege", size=19, weight=700)
    canvas.text(
        FULL - right,
        410,
        "vantagem no 2º turno: vermelho, Lula; azul, Flávio",
        size=15,
        fill=MUTED,
        anchor="end",
    )

    zero = 512
    scale = 74 / 26.0
    canvas.line(left, zero, FULL - right, zero, stroke=INK, width=2)

    for i, band in enumerate(bands):
        cx = left + slot * i + slot / 2
        gap = band["vote_gap"]
        height = abs(gap) * scale
        cor = RED if gap > 0 else BLUE
        y = zero - height if gap > 0 else zero
        canvas.rect(cx - 58, y, 116, height, cor)
        if gap > 0:
            canvas.number(
                cx,
                y + height / 2 + 11,
                signed(gap, 0),
                size=30,
                fill="#ffffff",
                anchor="middle",
            )
        else:
            canvas.number(
                cx, y + height + 28, signed(gap, 0), size=30, fill=cor, anchor="middle"
            )

    canvas.rect(left, 566, FULL - left - right, 2, AMBER)
    canvas.text(
        left,
        596,
        "A amostra tem 8,3 pontos a mais exatamente na única faixa em que Lula vence, e por 26.",
        size=17,
        weight=700,
    )
    canvas.text(
        left,
        620,
        "Nas outras três, a vantagem é de Flávio e praticamente idêntica: a escala é um degrau, não uma rampa.",
        size=16,
        fill=MUTED,
    )
    return canvas.render()


def cascata(data: dict) -> str:
    """Do placar publicado ao reponderado, uma faixa por degrau."""
    mech = data["income_mechanics"]["waves"]["august"]
    bands = mech["bands"]
    published = mech["published_gap"]
    final = mech["reweighted_gap"]

    canvas = Canvas(
        FULL, 572, aria="Decomposição do deslocamento da vantagem, faixa a faixa"
    )
    hatch = canvas.hatch("cascata-azul", BLUE, 0.20)
    hatch_red = canvas.hatch("cascata-vermelho", RED, 0.20)

    left, right = 104, 60
    span = FULL - left - right
    steps = len(bands) + 2
    slot = span / steps
    top, height = 88, 260
    lo, hi = -2.6, 1.6
    scale = height / (hi - lo)

    def ypos(value: float) -> float:
        return top + (hi - value) * scale

    canvas.label(left, 52, "vantagem de Lula sobre Flávio no 2º turno, em pontos")

    for tick in (1, 0, -1, -2):
        y = ypos(tick)
        canvas.line(
            left - 14,
            y,
            FULL - right,
            y,
            stroke=LINE if tick else INK,
            width=2 if tick == 0 else 1,
        )
        canvas.label(left - 22, y + 4, signed(tick, 0) if tick else "0", anchor="end")
    canvas.text(FULL - right, ypos(0) - 10, "empate", size=13, fill=MUTED, anchor="end")

    cursor = published
    x = left
    canvas.rect(
        x + slot * 0.16, ypos(published), slot * 0.68, ypos(0) - ypos(published), RED
    )
    canvas.number(
        x + slot / 2,
        ypos(published) - 14,
        signed(published, 1),
        size=28,
        fill=RED,
        anchor="middle",
    )
    canvas.text(
        x + slot / 2,
        top + height + 34,
        "publicado",
        size=16,
        weight=700,
        anchor="middle",
    )
    canvas.label(x + slot / 2, top + height + 56, "46 × 45", anchor="middle")

    for i, band in enumerate(bands):
        x = left + slot * (i + 1)
        contribution = band["contribution"]
        start, end = cursor, cursor + contribution
        y0, y1 = ypos(max(start, end)), ypos(min(start, end))
        cor = BLUE if contribution < 0 else RED
        fill = hatch if contribution < 0 else hatch_red
        canvas.rect(x + slot * 0.16, y0, slot * 0.68, max(y1 - y0, 3), fill)
        canvas.line(
            x + slot * 0.16,
            y0 if contribution < 0 else y1,
            x + slot * 0.84,
            y0 if contribution < 0 else y1,
            stroke=cor,
            width=2.5,
        )
        canvas.line(
            x + slot * 0.84,
            ypos(start),
            x + slot * 1.16,
            ypos(start),
            stroke=GRAY,
            width=1,
            stroke_dasharray="4 3",
        )
        canvas.text(
            x + slot / 2,
            top + height + 34,
            band["band"].replace("-", " a "),
            size=16,
            weight=700,
            anchor="middle",
        )
        canvas.label(
            x + slot / 2,
            top + height + 58,
            f"erro {signed(band['error_pp'], 1)} pp",
            anchor="middle",
            size=14,
        )
        canvas.label(
            x + slot / 2,
            top + height + 80,
            f"× voto {signed(band['vote_gap'], 0)}",
            anchor="middle",
            size=14,
        )
        canvas.text(
            x + slot / 2,
            top + height + 108,
            f"= {signed(contribution, 3)}",
            size=18,
            fill=cor,
            weight=700,
            anchor="middle",
        )
        cursor = end

    x = left + slot * (steps - 1)
    canvas.rect(x + slot * 0.16, ypos(0), slot * 0.68, ypos(final) - ypos(0), BLUE)
    canvas.number(
        x + slot / 2,
        ypos(final) + 30,
        signed(final, 1),
        size=28,
        fill=BLUE,
        anchor="middle",
    )
    canvas.text(
        x + slot / 2,
        top + height + 34,
        "reponderado",
        size=16,
        weight=700,
        anchor="middle",
    )
    canvas.label(x + slot / 2, top + height + 56, "44,7 × 46,4", anchor="middle")

    canvas.rect(left, 496, FULL - left - right, 2, AMBER)
    canvas.text(
        left,
        526,
        "A faixa até 1 salário mínimo responde por 80% do deslocamento. As outras três somam meio ponto.",
        size=17,
        weight=700,
    )
    canvas.text(
        left,
        550,
        "Barra sólida: número publicado pela Nexus. Barra hachurada: conta desta auditoria.",
        size=15,
        fill=MUTED,
    )
    return canvas.render()


def alavanca(data: dict) -> str:
    """O teorema: erro de calibração vezes inclinação limita o que a margem move."""
    margins = data["margin_leverage"]["margins"]
    canvas = Canvas(
        FULL,
        580,
        aria="Amplitude e erro de calibração de cada margem, e o deslocamento que cada uma produz",
    )

    left, top = 96, 108
    plot_w, plot_h = 606, 340
    xmax, ymax = 42.0, 9.6

    def px(value: float) -> float:
        return left + plot_w * value / xmax

    def py(value: float) -> float:
        return top + plot_h - plot_h * value / ymax

    canvas.label(
        left,
        66,
        "cada margem: o quanto ela inclina o voto × o quanto a amostra erra nela",
    )

    for tick in range(0, 10, 2):
        y = py(tick)
        canvas.line(left, y, left + plot_w, y, stroke=LINE)
        canvas.label(left - 12, y + 4, f"{tick}%", anchor="end")
    for tick in range(0, 45, 10):
        x = px(tick)
        canvas.line(x, top, x, top + plot_h, stroke=LINE)
        canvas.label(x, top + plot_h + 24, str(tick), anchor="middle")

    canvas.text(
        left + plot_w / 2,
        top + plot_h + 52,
        "amplitude do gradiente de voto, em pontos",
        size=15,
        fill=MUTED,
        anchor="middle",
    )
    canvas.text(
        0,
        0,
        "erro de calibração da amostra",
        size=15,
        fill=MUTED,
        anchor="middle",
        transform=f"translate(38 {top + plot_h / 2}) rotate(-90)",
    )

    for bound, dash in ((1.0, "3 4"), (2.0, "3 4")):
        pts = []
        for step in range(0, 121):
            amp = 3 + step * (xmax - 3) / 120
            tvd = 100 * bound / amp
            if tvd <= ymax:
                pts.append(f"{px(amp):.1f},{py(tvd):.1f}")
        if pts:
            canvas.path(
                "M " + " L ".join(pts),
                fill="none",
                stroke=GRAY,
                stroke_width=1.2,
                stroke_dasharray=dash,
            )
            amp_start = float(pts[0].split(",")[0])
            canvas.label(
                amp_start + 8,
                float(pts[0].split(",")[1]) + 16,
                f"limite {br(bound, 0)}",
                size=12,
            )

    for margin in margins:
        x, y = px(margin["amplitude"]), py(margin["tvd_pct"])
        radius = 9 + 17 * math.sqrt(abs(margin["swing"]) / 2.7)
        cor = AMBER if not margin["quota_controlled"] else SKY
        canvas.circle(x, y, radius, cor, opacity=0.85, stroke=INK, stroke_width=1.5)
        anchor, dx = (
            ("end", -radius - 10)
            if margin["label"] in ("Idade", "Sexo", "Ocupação")
            else ("start", radius + 10)
        )
        canvas.text(x + dx, y - 2, margin["label"], size=16, weight=700, anchor=anchor)
        canvas.text(
            x + dx,
            y + 18,
            f"move {signed(margin['swing'], 2)}",
            size=14,
            fill=MUTED,
            anchor=anchor,
        )

    canvas.text(
        left,
        top + plot_h + 84,
        "Bolha âmbar: margem sem cota. Bolha azul: margem travada por cota.",
        size=14,
        fill=MUTED,
    )
    canvas.text(
        left,
        top + plot_h + 106,
        "O tamanho da bolha é o deslocamento que a margem produz.",
        size=14,
        fill=MUTED,
    )

    bx = left + plot_w + 96
    bw = FULL - bx - 108
    canvas.text(bx, 108, "Deslocamento produzido", size=17, weight=700)
    canvas.label(bx, 130, "em pontos de vantagem")
    ordered = sorted(margins, key=lambda m: abs(m["swing"]), reverse=True)
    zero_x = bx + bw * 2.7 / 3.7
    canvas.line(zero_x, 150, zero_x, 160 + len(ordered) * 52, stroke=INK, width=1.5)
    canvas.label(zero_x - 8, 146, "para Flávio", anchor="end", size=11)
    canvas.label(zero_x + 8, 146, "para Lula", size=11)
    for i, margin in enumerate(ordered):
        y = 164 + i * 52
        swing = margin["swing"]
        width = max(abs(swing) / 2.7 * (zero_x - bx), 4)
        cor = AMBER if not margin["quota_controlled"] else SKY
        x0 = zero_x - width if swing < 0 else zero_x
        canvas.rect(x0, y, width, 22, cor)
        canvas.text(bx, y - 6, margin["label"], size=15, weight=700)
        canvas.label(
            bx + bw,
            y - 6,
            "cota" if margin["quota_controlled"] else "sem cota",
            size=12,
            anchor="end",
        )
        inside = width > 84
        if inside:
            tx, anchor, fill = x0 + 10, "start", "#ffffff"
        elif swing < 0:
            tx, anchor, fill = x0 - 8, "end", INK
        else:
            tx, anchor, fill = x0 + width + 8, "start", INK
        canvas.text(
            tx, y + 17, signed(swing, 2), size=15, fill=fill, weight=700, anchor=anchor
        )

    canvas.rect(bx, 492, bw, 2, AMBER)
    canvas.text(bx, 518, "As duas margens sem cota erram muito", size=14.5, weight=700)
    canvas.text(bx, 538, "e puxam para lados opostos. Somadas,", size=14.5, weight=700)
    canvas.text(bx, 558, "ainda invertem o sinal: −0,89.", size=14.5, weight=700)
    return canvas.render()


def virada(data: dict) -> str:
    """O ponto de virada e a onda anterior sob a mesma régua."""
    waves = data["income_mechanics"]["waves"]
    canvas = Canvas(
        FULL,
        480,
        aria="Vantagem de Lula conforme a composição de renda caminha da amostra para a PNAD",
    )

    left, right = 108, 344
    top, height = 116, 268
    plot_w = FULL - left - right
    lo, hi = -2.4, 4.6

    def px(lam: float) -> float:
        return left + plot_w * lam

    def py(value: float) -> float:
        return top + height - height * (value - lo) / (hi - lo)

    canvas.label(
        left,
        54,
        "vantagem de Lula no 2º turno conforme a renda caminha do perfil da amostra ao da PNAD",
    )

    canvas.rect(left, py(0), plot_w, top + height - py(0), "#eef1fb")
    for tick in (4, 3, 2, 1, 0, -1, -2):
        y = py(tick)
        canvas.line(
            left,
            y,
            left + plot_w,
            y,
            stroke=INK if tick == 0 else LINE,
            width=2 if tick == 0 else 1,
        )
        canvas.label(left - 16, y + 4, signed(tick, 0) if tick else "0", anchor="end")

    canvas.text(left + 12, py(0) - 12, "Lula na frente", size=14, fill=RED, weight=700)
    canvas.text(
        left + 12, py(0) + 24, "Flávio na frente", size=14, fill=BLUE, weight=700
    )

    for tick in (0, 0.25, 0.5, 0.75, 1.0):
        x = px(tick)
        canvas.line(x, top, x, top + height, stroke=LINE, stroke_dasharray="3 4")
        canvas.label(x, top + height + 26, f"{int(tick * 100)}%", anchor="middle")
    canvas.label(left, top + height + 52, "perfil da amostra")
    canvas.label(left + plot_w, top + height + 52, "perfil da PNAD", anchor="end")

    for wave, cor, nome in (("august", BLUE, "03/08"), ("july", GRAY, "27/07")):
        info = waves[wave]
        start = info["published_gap"]
        end = info["reweighted_gap"]
        canvas.path(
            f"M {px(0)} {py(start)} L {px(1)} {py(end)}",
            fill="none",
            stroke=cor,
            stroke_width=4.5,
            stroke_linecap="round",
        )
        canvas.circle(px(0), py(start), 8, cor)
        canvas.circle(px(1), py(end), 8, cor)
        canvas.number(
            px(0) - 18, py(start) + 8, signed(start, 1), size=24, fill=cor, anchor="end"
        )
        canvas.number(
            px(1) - 14, py(end) - 20, signed(end, 1), size=24, fill=cor, anchor="end"
        )
        canvas.text(
            px(0.46),
            py(start + (end - start) * 0.46) - 16,
            nome,
            size=16,
            fill=cor,
            weight=700,
            anchor="middle",
        )

    lam = waves["august"]["tipping_lambda"]
    x = px(lam)
    canvas.line(x, py(0), x, top - 10, stroke=AMBER, width=2.5, stroke_dasharray="6 4")
    canvas.circle(x, py(0), 9, AMBER, stroke=INK, stroke_width=1.5)
    canvas.text(
        x,
        top - 22,
        f"{br(100 * lam, 1)}% do caminho basta",
        size=16,
        fill=AMBER,
        weight=700,
        anchor="middle",
    )

    bx = FULL - right + 52
    canvas.line(bx - 26, 100, bx - 26, 440, stroke=LINE)
    canvas.text(bx, 122, "O ponto de virada", size=17, weight=700)
    canvas.number(bx, 168, f"{br(100 * lam, 1)}%", size=46, fill=AMBER)
    canvas.text(bx, 194, "da correção já zera a vantagem", size=14, fill=MUTED)
    canvas.text(
        bx,
        222,
        f"A faixa até 1 SM teria de valer {br(waves['august']['tipping_bottom_band_pct'], 1)}%",
        size=14,
    )
    canvas.text(bx, 242, "em vez dos 21,8% da amostra.", size=14)

    canvas.text(bx, 292, "O viés não cresceu", size=17, weight=700)
    canvas.number(bx, 330, signed(waves["july"]["swing"], 2), size=30, fill=GRAY)
    canvas.text(bx + 106, 330, "em 27/07", size=14, fill=MUTED)
    canvas.number(bx, 372, signed(waves["august"]["swing"], 2), size=30, fill=BLUE)
    canvas.text(bx + 106, 372, "em 03/08", size=14, fill=MUTED)
    canvas.text(bx, 406, "Em julho o desvio era maior e Lula", size=14, weight=700)
    canvas.text(bx, 426, "seguia na frente. O que encolheu", size=14, weight=700)
    canvas.text(bx, 446, "foi a vantagem, não o viés.", size=14, weight=700)
    return canvas.render()


def main() -> None:
    data = load()
    figures = {
        "renda_penhasco": penhasco(data),
        "renda_cascata": cascata(data),
        "renda_alavanca": alavanca(data),
        "renda_virada": virada(data),
    }
    write_fragments(OUTPUT, figures)
    print(
        json.dumps(
            {"output": str(OUTPUT), "figuras": list(figures)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
