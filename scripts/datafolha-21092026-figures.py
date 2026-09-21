"""Accessible SVG figures for the 21 September Datafolha dossier."""

from html import escape

RED, BLUE, GRAY, PAPER = "#a52630", "#164d88", "#535b54", "#f7f1e5"


def fmt(v, n=2):
    return f"{v:.{n}f}".replace(".", ",")


def text(x, y, value, size=16, color="#18231d", anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="Archivo, sans-serif">{escape(str(value))}</text>'


def svg(body, height, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {height}" role="img" aria-label="{escape(label)}"><rect width="1100" height="{height}" fill="{PAPER}"/>{body}</svg>'


def income(data):
    r = data["reweight"]["renda"]
    body = text(30, 40, "A renda declarada e o benchmark da PNAD", 26)
    for i, (name, a, b) in enumerate(
        zip(
            ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"],
            r["amostra_pct"],
            r["pnad_pct"]["pessoas16_efetivo"],
            strict=True,
        )
    ):
        y = 85 + i * 95
        body += text(30, y + 23, name, 20)
        for offset, v, c in [(0, a, GRAY), (30, b, BLUE)]:
            body += f'<rect x="230" y="{y + offset}" width="{v * 13}" height="23" fill="{c}"/>'
            body += text(240 + v * 13, y + offset + 19, f"{fmt(v)}%", 17, c)
    body += text(230, 410, "Perfil ponderado, renda declarada", 17, GRAY) + text(
        670, 410, "PNAD 2025, pessoas 16+", 17, BLUE
    )
    return svg(
        body,
        440,
        "Renda: perfil de 51,86/34,24/13,90% contra PNAD de 35,19/39,26/25,55%",
    )


def sankey(data):
    d = data["transfer"]
    scale = 5.5
    gap = 24
    left = []
    y = 60
    for v in d["row_targets"]:
        left.append(y)
        y += v * scale + gap
    right = []
    y = 60
    for v in d["column_targets"]:
        right.append(y)
        y += v * scale + gap
    colors = [RED, BLUE, GRAY]
    body = "<defs>"
    for j, c in enumerate(colors):
        body += f'<pattern id="hatch{j}" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(35)"><rect width="9" height="9" fill="{PAPER}"/><rect width="4" height="9" fill="{c}"/></pattern>'
    body += "</defs>" + text(30, 30, "1º TURNO", 18) + text(860, 30, "2º TURNO", 18)
    lo = left.copy()
    ro = right.copy()
    for i, row in enumerate(d["matrix"]):
        for j, v in enumerate(row):
            if v < 1e-9:
                continue
            a, b, h = lo[i], ro[j], v * scale
            lo[i] += h
            ro[j] += h
            kind = (
                "Estimado por IPF"
                if i in d["estimated_rows"]
                else (
                    "Base consolidada por hipótese"
                    if i in d["consolidated_rows"]
                    else (
                        "Complemento da medição" if j == 2 else "Medido pelo Datafolha"
                    )
                )
            )
            label = f"{d['sources'][i]} → {d['destinations'][j]}: {fmt(v)} pontos. {kind}. Origens reescaladas de 101 para 99."
            fill = f"url(#hatch{j})" if i not in d["measured_rows"] else colors[j]
            border = (
                'stroke="#18231d" stroke-width="2" stroke-dasharray="3 5"'
                if i in d["consolidated_rows"]
                else ""
            )
            body += f'<path d="M230 {a} C475 {a} 590 {b} 825 {b} L825 {b + h} C590 {b + h} 475 {a + h} 230 {a + h}Z" fill="{fill}" {border} opacity=".8" tabindex="0" class="flow" aria-label="{escape(label)}"><title>{escape(label)}</title></path>'
    for name, v, y in zip(d["sources"], d["row_targets"], left, strict=True):
        body += (
            f'<rect x="220" y="{y}" width="10" height="{v * scale}" fill="#18231d"/>'
            + text(208, y + v * scale / 2 + 5, f"{name} {fmt(v, 1)}", 16, anchor="end")
        )
    for j, (name, v, y) in enumerate(
        zip(d["destinations"], d["column_targets"], right, strict=True)
    ):
        body += (
            f'<rect x="825" y="{y}" width="10" height="{v * scale}" fill="{colors[j]}"/>'
            + text(842, y + v * scale / 2 + 5, f"{name} {v:g}", 19, colors[j])
        )
    body += text(
        30,
        845,
        "Sólida: 2 origens medidas. Hachura: 8 origens por hipótese, incluindo 2 bases fixadas.",
        17,
    )
    return svg(
        body,
        885,
        "Transferência agregada: Cury e Caiado medidos, bases dos finalistas consolidadas e seis origens estimadas",
    )
