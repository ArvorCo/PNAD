#!/usr/bin/env python3
"""Generate the static SVG evidence figures for the 24 Aug. BTG/Nexus dossier."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from svgkit import FULL, MONO, Canvas, br, signed, write_fragments  # noqa: E402

DATA = ROOT / "docs/assets/nexus_btg_240826_data.json"
OUTPUT = ROOT / "docs/assets/figuras/nexus_btg_240826.json"

INK = "#171713"
MUTED = "#6f7068"
PAPER = "#f5f0e6"
LINE = "#d8d0c0"
ORANGE = "#f28b22"
BLUE = "#1e54a8"
RED = "#d13b32"
GREEN = "#537c45"
GRAY = "#98988f"


def profile_comparison(data: dict) -> str:
    canvas = Canvas(
        FULL, 760, aria="Perfil publicado da Nexus comparado com TSE e PNAD"
    )
    panels = [
        ("sex", 36, 64),
        ("age", 604, 64),
        ("region", 36, 392),
        ("income", 604, 392),
    ]
    titles = {
        "sex": "SEXO · TSE",
        "age": "IDADE · TSE",
        "region": "REGIÃO · TSE",
        "income": "RENDA FAMILIAR · PNADC 16+",
    }
    for dimension, x0, y0 in panels:
        block = data["target_comparison"][dimension]
        canvas.text(
            x0, y0, titles[dimension], size=15, family=MONO, weight=700, fill=INK
        )
        canvas.text(
            x0 + 508,
            y0,
            f"TVD {br(block['total_variation_distance_pp'], 2)} pp",
            size=13,
            family=MONO,
            fill=ORANGE,
            anchor="end",
        )
        maximum = max(max(block["published"]), max(block["target"]))
        scale = 310 / maximum
        for i, label in enumerate(block["labels"]):
            y = y0 + 46 + i * 56
            poll, target = block["published"][i], block["target"][i]
            canvas.text(x0, y + 6, label, size=15, fill=INK, weight=700)
            canvas.rect(x0 + 155, y - 14, poll * scale, 12, ORANGE, rx=2)
            canvas.rect(x0 + 155, y + 5, target * scale, 12, BLUE, rx=2)
            canvas.text(
                x0 + 155 + poll * scale + 7,
                y - 3,
                br(poll, 1),
                size=12,
                family=MONO,
                fill=ORANGE,
            )
            canvas.text(
                x0 + 155 + target * scale + 7,
                y + 16,
                br(target, 1),
                size=12,
                family=MONO,
                fill=BLUE,
            )
        canvas.line(x0, y0 + 290, x0 + 508, y0 + 290, LINE, 1)
    canvas.rect(36, 714, 16, 10, ORANGE, rx=2)
    canvas.text(60, 724, "perfil publicado", size=14, fill=MUTED)
    canvas.rect(196, 714, 16, 10, BLUE, rx=2)
    canvas.text(220, 724, "alvo oficial", size=14, fill=MUTED)
    canvas.text(
        1144,
        724,
        "TVD: distância total de variação",
        size=13,
        family=MONO,
        fill=MUTED,
        anchor="end",
    )
    return canvas.render()


def reweight_gaps(data: dict) -> str:
    canvas = Canvas(
        FULL, 560, aria="Vantagem de Lula publicada e após reponderações univariadas"
    )
    dimensions = [
        ("Publicado", None),
        ("Sexo", "sex"),
        ("Idade", "age"),
        ("Região", "region"),
        ("Renda", "income"),
    ]
    panels = [("first", "1º TURNO", 52), ("runoff", "2º TURNO", 610)]
    scale_min, scale_max = -1.5, 5.0
    for ballot, title, x0 in panels:
        width = 500

        def project(value: float, x0: float = x0, width: float = width) -> float:
            return x0 + (value - scale_min) / (scale_max - scale_min) * width

        canvas.text(x0, 42, title, size=16, family=MONO, weight=700)
        canvas.text(
            x0 + width,
            42,
            "vantagem Lula, pp",
            size=13,
            family=MONO,
            fill=MUTED,
            anchor="end",
        )
        for tick in range(-1, 6):
            x = project(tick)
            canvas.line(x, 64, x, 458, LINE, 1, stroke_dasharray="3 5")
            canvas.text(
                x,
                486,
                signed(tick, 0),
                size=12,
                family=MONO,
                fill=MUTED,
                anchor="middle",
            )
        canvas.line(project(0), 62, project(0), 458, INK, 2)
        published = data["margin_of_difference"][ballot]["gap_pp"]
        for i, (label, key) in enumerate(dimensions):
            y = 100 + i * 76
            gap = published if key is None else data["reweighting"][ballot][key]["gap"]
            color = INK if key is None else RED if key == "income" else BLUE
            canvas.text(x0, y - 13, label, size=15, fill=INK, weight=700)
            if key:
                canvas.line(
                    project(published),
                    y,
                    project(gap),
                    y,
                    color,
                    5,
                    stroke_linecap="round",
                )
                canvas.circle(
                    project(published), y, 6, PAPER, stroke=INK, stroke_width=2
                )
            canvas.circle(project(gap), y, 9 if key == "income" else 7, color)
            value = signed(gap, 2)
            label_width = 9 * len(value) + 12
            if gap <= 4.4:
                label_x = project(gap) + 12
                canvas.rect(label_x - 3, y - 13, label_width, 26, PAPER, rx=3)
                canvas.text(
                    label_x, y + 5, value, size=13, family=MONO, fill=color, weight=700
                )
            else:
                label_x = project(gap) - 12
                canvas.rect(
                    label_x - label_width + 3, y - 13, label_width, 26, PAPER, rx=3
                )
                canvas.text(
                    label_x,
                    y + 5,
                    value,
                    size=13,
                    family=MONO,
                    fill=color,
                    weight=700,
                    anchor="end",
                )
        note = (
            "vermelho: maior correção observada"
            if ballot == "first"
            else "vermelho: única margem que muda o sinal"
        )
        canvas.text(x0, 525, note, size=13, fill=RED, weight=700)
    return canvas.render()


def strategic_reservoirs(data: dict) -> str:
    reservoirs = data["strategic_reservoirs"]
    canvas = Canvas(FULL, 600, aria="Reservatórios estratégicos medidos pela Nexus")
    panels = [
        ("bolsonaristas_convictos", "BOLSONARISTAS CONVICTOS", 44),
        ("bolsonaro_como_alternativa", "BOLSONARO COMO ALTERNATIVA", 610),
    ]
    labels = [
        ("lula", "Lula", RED),
        ("flavio", "Flávio", BLUE),
        ("third_way", "3ª via", ORANGE),
        ("nonchoice", "não escolha", GRAY),
    ]
    for key, title, x0 in panels:
        block = reservoirs[key]
        canvas.text(x0, 44, title, size=15, family=MONO, weight=700, fill=INK)
        canvas.text(
            x0,
            78,
            f"{block['share_sample']}% da amostra",
            size=25,
            weight=700,
            fill=INK,
        )
        canvas.text(
            x0 + 526,
            78,
            f"{block['can_change']}% podem mudar",
            size=15,
            family=MONO,
            weight=700,
            fill=ORANGE,
            anchor="end",
        )
        cursor = x0
        total = sum(block["first_round"].values())
        for field, label, color in labels:
            value = block["first_round"][field]
            width = 526 * value / total
            canvas.rect(cursor, 106, width, 82, color)
            if width > 54:
                canvas.text(
                    cursor + width / 2,
                    140,
                    f"{value}%",
                    size=22,
                    weight=700,
                    fill="#fff",
                    anchor="middle",
                )
                canvas.text(
                    cursor + width / 2,
                    166,
                    label,
                    size=13,
                    fill="#fff",
                    anchor="middle",
                )
            cursor += width
        third = block["first_round"]["third_way"]
        canvas.text(
            x0,
            226,
            f"3ª via: {third}% dentro do grupo",
            size=18,
            weight=700,
            fill=ORANGE,
        )
        if key == "bolsonaristas_convictos":
            sample_points = block["share_sample"] * third / 100
            canvas.text(
                x0,
                254,
                f"≈ {br(sample_points, 1)} pontos da amostra",
                size=14,
                family=MONO,
                fill=MUTED,
            )
        else:
            canvas.text(
                x0, 254, "linha publicada soma 101%", size=14, family=MONO, fill=MUTED
            )
    canvas.line(44, 302, 1136, 302, LINE, 1)
    benefit = reservoirs["bolsa_familia"]
    canvas.text(
        44,
        348,
        "BENEFICIÁRIOS DO BOLSA FAMÍLIA",
        size=15,
        family=MONO,
        weight=700,
        fill=INK,
    )
    canvas.text(44, 395, "Flávio", size=17, weight=700, fill=BLUE)
    canvas.text(
        164, 395, f"{benefit['flavio_previous_wave']}%", size=27, weight=700, fill=MUTED
    )
    canvas.line(224, 384, 328, 384, BLUE, 4, stroke_linecap="round")
    canvas.text(
        350, 395, f"{benefit['flavio_current']}%", size=34, weight=700, fill=BLUE
    )
    canvas.text(
        450,
        392,
        f"+{benefit['flavio_change']} pp",
        size=17,
        family=MONO,
        weight=700,
        fill=BLUE,
    )
    canvas.text(650, 395, "Lula", size=17, weight=700, fill=RED)
    canvas.text(
        750, 395, f"{benefit['lula_previous_wave']}%", size=27, weight=700, fill=MUTED
    )
    canvas.line(810, 384, 914, 384, RED, 4, stroke_linecap="round")
    canvas.text(936, 395, f"{benefit['lula_current']}%", size=34, weight=700, fill=RED)
    canvas.text(44, 458, "17/08 → 24/08/2026", size=14, family=MONO, fill=MUTED)
    canvas.text(
        44,
        504,
        "Sinal descritivo, não teste de significância",
        size=21,
        weight=700,
        fill=INK,
    )
    canvas.text(
        44,
        538,
        "A Nexus não publica base não ponderada nem intervalo do subgrupo.",
        size=15,
        fill=MUTED,
    )
    canvas.text(
        1136,
        570,
        "Fonte: relatório, pp. 23, 27 e 35",
        size=13,
        family=MONO,
        fill=MUTED,
        anchor="end",
    )
    return canvas.render()


def useful_vote_model(data: dict) -> str:
    model = data["useful_vote"]
    canvas = Canvas(FULL, 760, aria="Migração, potencial e modelo de voto útil")
    canvas.text(
        44,
        40,
        "TRÊS OBJETOS, TRÊS CONTAS",
        size=15,
        family=MONO,
        weight=700,
        fill=ORANGE,
    )
    headers = [
        (44, "ORIGEM"),
        (248, "BASE"),
        (352, "PODE MUDAR"),
        (540, "FLÁVIO NO 2º"),
        (746, "MIGRAÇÃO INTEGRAL"),
        (984, "MODELO CONJUNTO"),
    ]
    for x, label in headers:
        canvas.text(x, 88, label, size=12, family=MONO, weight=700, fill=MUTED)
    canvas.line(44, 104, 1136, 104, LINE, 1)
    for index, row in enumerate(model["rows"]):
        y = 148 + index * 72
        canvas.text(44, y, row["candidate"], size=20, weight=700, fill=INK)
        canvas.text(
            248, y, f"{row['first_round']}%", size=18, family=MONO, weight=700, fill=INK
        )
        canvas.text(
            352,
            y,
            f"{row['can_change']}%",
            size=18,
            family=MONO,
            weight=700,
            fill=ORANGE,
        )
        canvas.text(
            540,
            y,
            f"{row['runoff_flavio']}%",
            size=18,
            family=MONO,
            weight=700,
            fill=BLUE,
        )
        canvas.text(
            746,
            y,
            f"+{br(row['migration_printed_points'], 2)} pp",
            size=18,
            family=MONO,
            weight=700,
            fill=BLUE,
        )
        canvas.text(
            984,
            y,
            f"+{br(row['max_entropy_points'], 2)} pp",
            size=18,
            family=MONO,
            weight=700,
            fill=GREEN,
        )
        canvas.line(44, y + 23, 1136, y + 23, LINE, 1)
    totals = model["totals"]
    canvas.text(44, 445, "TOTAL", size=15, family=MONO, weight=700, fill=INK)
    canvas.text(
        352,
        445,
        f"+{br(totals['potential'], 2)} pp",
        size=20,
        family=MONO,
        weight=700,
        fill=ORANGE,
    )
    canvas.text(
        746,
        445,
        f"+{br(totals['migration_printed'], 2)} pp",
        size=20,
        family=MONO,
        weight=700,
        fill=BLUE,
    )
    canvas.text(
        984,
        445,
        f"+{br(totals['max_entropy'], 2)} pp",
        size=20,
        family=MONO,
        weight=700,
        fill=GREEN,
    )
    canvas.line(44, 472, 1136, 472, INK, 2)
    scenarios = model["scenarios"]
    canvas.text(
        44, 516, "FLÁVIO NO 1º TURNO", size=14, family=MONO, weight=700, fill=MUTED
    )
    scale_left, scale_width, scale_min, scale_max = 260, 820, 37, 45

    def project(value: float) -> float:
        return scale_left + (value - scale_min) / (scale_max - scale_min) * scale_width

    for tick in range(37, 46):
        x = project(tick)
        canvas.line(x, 542, x, 650, LINE, 1, stroke_dasharray="3 5")
        canvas.text(
            x, 674, str(tick), size=12, family=MONO, fill=MUTED, anchor="middle"
        )
    canvas.line(project(37), 542, project(37), 650, INK, 2)
    canvas.text(
        44,
        570,
        f"Pool ativo: L {br(scenarios['maximum_entropy_lula_ns_imputed'], 2)} × F",
        size=15,
        weight=700,
        fill=GREEN,
    )
    estimate = scenarios["maximum_entropy_ns_imputed"]
    canvas.line(
        project(37), 565, project(estimate), 565, GREEN, 8, stroke_linecap="round"
    )
    canvas.circle(project(estimate), 565, 9, GREEN)
    canvas.text(
        project(estimate) + 14,
        571,
        br(estimate, 2),
        size=16,
        family=MONO,
        weight=700,
        fill=GREEN,
    )
    canvas.text(
        44,
        626,
        f"Integral: Lula {br(scenarios['full_migration_lula_using_printed_cells'], 2)} × Flávio",
        size=15,
        weight=700,
        fill=BLUE,
    )
    integral = scenarios["full_migration_using_printed_cells"]
    canvas.line(
        project(37), 621, project(integral), 621, BLUE, 8, stroke_linecap="round"
    )
    canvas.circle(project(integral), 621, 9, BLUE)
    canvas.text(
        project(integral) - 12,
        606,
        br(integral, 2),
        size=16,
        family=MONO,
        weight=700,
        fill=BLUE,
        anchor="end",
    )
    lower, upper = scenarios["partial_identification_range"]
    canvas.text(
        44,
        718,
        f"Limites sem supor dependência: {br(lower, 2)}% a {br(upper, 2)}%. OR 0,5–2: {br(scenarios['odds_ratio_sensitivity_0_5_to_2'][0], 2)}% a {br(scenarios['odds_ratio_sensitivity_0_5_to_2'][1], 2)}%.",
        size=14,
        family=MONO,
        fill=MUTED,
    )
    canvas.text(
        1136,
        744,
        "NS/NR imputado; branco/nulo preservado",
        size=13,
        family=MONO,
        fill=MUTED,
        anchor="end",
    )
    return canvas.render()


def transfer_sankey(data: dict) -> str:
    transfer = data["transfer"]
    matrix = transfer["matrix"]
    rows = transfer["row_targets"]
    cols = transfer["column_targets"]
    sources = transfer["sources"]
    destinations = transfer["destinations"]
    measured = set(transfer["measured_rows"])
    colors = [RED, BLUE, GREEN, GRAY]
    canvas = Canvas(
        FULL, 760, aria="Transferência estimada do primeiro para o segundo turno"
    )
    patterns = [
        canvas.hatch(f"n2408-h{i}", color, 0.14) for i, color in enumerate(colors)
    ]
    x_left, x_right, bar_w = 270, 900, 16
    top, gap = 76, 15
    scale = (610 - gap * (len(rows) - 1)) / sum(rows)
    src, dst = [], []
    cursor = top
    for value in rows:
        src.append({"y": cursor, "h": value * scale, "off": 0.0})
        cursor += value * scale + gap
    cursor = top + 30
    dst_gap = 24
    for value in cols:
        dst.append({"y": cursor, "h": value * scale, "off": 0.0})
        cursor += value * scale + dst_gap
    mid = (x_right - x_left) * 0.45
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value < 0.035:
                continue
            height = value * scale
            sy = src[i]["y"] + src[i]["off"]
            ty = dst[j]["y"] + dst[j]["off"]
            src[i]["off"] += height
            dst[j]["off"] += height
            x0, x1 = x_left + bar_w, x_right
            canvas.path(
                f"M{x0},{sy} C{x0+mid},{sy} {x1-mid},{ty} {x1},{ty} L{x1},{ty+height} C{x1-mid},{ty+height} {x0+mid},{sy+height} {x0},{sy+height} Z",
                fill=colors[j] if i in measured else patterns[j],
                opacity=0.58 if i in measured else 1,
                stroke=colors[j] if i not in measured else "none",
                stroke_width=0.6,
            )
    for i, value in enumerate(rows):
        color = (
            RED
            if sources[i] == "Lula"
            else BLUE if sources[i] == "Flávio" else ORANGE if i in measured else GRAY
        )
        canvas.rect(x_left, src[i]["y"], bar_w, max(2, src[i]["h"]), color)
        canvas.text(
            x_left - 16,
            src[i]["y"] + src[i]["h"] / 2 + 5,
            f"{sources[i]} {br(value, 0)}",
            size=15,
            fill=ORANGE if i in measured else INK,
            weight=700,
            anchor="end",
        )
    for j, value in enumerate(cols):
        canvas.rect(x_right, dst[j]["y"], bar_w, max(2, dst[j]["h"]), colors[j])
        canvas.text(
            x_right + 28,
            dst[j]["y"] + dst[j]["h"] / 2 + 5,
            f"{destinations[j]} {br(value, 0)}",
            size=16,
            fill=INK,
            weight=700,
        )
    canvas.text(
        x_left,
        38,
        "1º TURNO",
        size=14,
        family=MONO,
        fill=MUTED,
        weight=700,
        anchor="middle",
    )
    canvas.text(
        x_right,
        38,
        "2º TURNO",
        size=14,
        family=MONO,
        fill=MUTED,
        weight=700,
        anchor="middle",
    )
    canvas.rect(36, 704, 20, 11, ORANGE)
    canvas.text(
        66,
        715,
        "linha e fita sólidas: cinco origens medidas pela Nexus na p. 52",
        size=14,
        fill=MUTED,
    )
    canvas.rect(36, 730, 20, 11, canvas.hatch("n2408-legend", BLUE, 0.14))
    canvas.text(
        66,
        741,
        "fita hachurada: quatro origens fechadas por IPF; não são medição individual",
        size=14,
        fill=MUTED,
    )
    return canvas.render()


def measured_pool(data: dict) -> str:
    pool = data["transfer"]["measured_pool"]
    values = pool["destinations_pct"]
    names = ["Lula", "Flávio", "B/N", "NS"]
    colors = [RED, BLUE, GREEN, GRAY]
    canvas = Canvas(
        FULL, 330, aria="Destino medido do eleitorado de cinco candidaturas menores"
    )
    canvas.text(
        44, 42, "O QUE A NEXUS MEDIU", size=15, family=MONO, fill=ORANGE, weight=700
    )
    canvas.text(
        44,
        76,
        "14 pontos do 1º turno, repartidos no cenário Lula × Flávio",
        size=23,
        fill=INK,
        weight=700,
    )
    left, width, y, height = 44, 1092, 118, 76
    cursor = left
    for name, value, color in zip(names, values, colors, strict=False):
        part = width * value / 100
        canvas.rect(cursor, y, part, height, color)
        if part > 70:
            canvas.text(
                cursor + part / 2,
                y + 34,
                f"{br(value, 1)}%",
                size=22,
                fill="#fff",
                weight=700,
                anchor="middle",
            )
            canvas.text(
                cursor + part / 2, y + 58, name, size=13, fill="#fff", anchor="middle"
            )
        cursor += part
    canvas.text(
        44,
        240,
        f"Flávio capta {br(values[1], 1)}% do pool; Lula, {br(values[0], 1)}%.",
        size=26,
        fill=INK,
        weight=700,
    )
    canvas.text(
        44,
        278,
        f"Razão medida: {br(pool['ratio_flavio_lula'], 2)} a 1 para Flávio. Base aproximada: n ≈ {pool['approx_unweighted_n']}, sem base não ponderada publicada.",
        size=16,
        fill=MUTED,
    )
    return canvas.render()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    figures = {
        "profile_comparison": profile_comparison(data),
        "reweight_gaps": reweight_gaps(data),
        "strategic_reservoirs": strategic_reservoirs(data),
        "useful_vote_model": useful_vote_model(data),
        "transfer_sankey": transfer_sankey(data),
        "measured_pool": measured_pool(data),
    }
    write_fragments(OUTPUT, figures)
    print(
        json.dumps(
            {"output": str(OUTPUT), "figures": sorted(figures)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
