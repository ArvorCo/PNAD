"""Static, accessible SVG figures; all numbers come from the audit JSON."""

from html import escape

RED = "#a52630"
BLUE = "#164d88"
GRAY = "#535b54"
PAPER = "#f7f1e5"


def text(x, y, value, size=16, color="#18231d", anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="Archivo, sans-serif">{escape(str(value))}</text>'


def svg(body, height, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {height}" role="img" aria-label="{escape(label)}"><rect width="1100" height="{height}" fill="{PAPER}"/>{body}</svg>'


def history(data):
    h = data["published_history"]
    body = ""
    for panel, prefix, name in [(0, "first", "1º TURNO"), (1, "second", "2º TURNO")]:
        x0 = 60 + panel * 555
        body += text(x0, 40, name, 22)
        for tick in [30, 35, 40, 45, 50]:
            y = 320 - (tick - 30) * 11
            body += f'<path d="M{x0} {y}h465" stroke="#cfc7b8"/>' + text(
                x0 - 8, y + 5, tick, 13, GRAY, "end"
            )
        for candidate, color in [("lula", RED), ("flavio", BLUE)]:
            vals = h[f"{prefix}_{candidate}"]
            pts = [(x0 + i * 33, 320 - (v - 30) * 11) for i, v in enumerate(vals)]
            body += f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="3"/>'
            for i, ((x, y), v) in enumerate(zip(pts, vals, strict=True)):
                body += f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"><title>{h["dates"][i]}: {candidate.title()} {v}%</title></circle>'
            x, y = pts[-1]
            body += text(
                x + 8,
                y + (-10 if candidate == "lula" else 22),
                f"{vals[-1]}%",
                19,
                color,
            )
        for i in [0, 3, 6, 9, 13]:
            body += text(x0 + i * 33, 350, h["dates"][i], 13, GRAY, "middle")
    body += text(60, 390, "Lula", 17, RED) + text(125, 390, "Flávio", 17, BLUE)
    body += text(
        1070,
        390,
        "14 rodadas · março a setembro de 2026 · pp. 21 e 53",
        14,
        GRAY,
        "end",
    )
    return svg(body, 420, "Série de quatorze rodadas, Lula e Flávio nos dois turnos")


def income(data):
    r = data["reweight"]["renda"]
    body = text(32, 36, "A distribuição publicada e a régua da PNAD", 24)
    for i, (name, a, b) in enumerate(
        zip(
            ["Até 1 SM", "1 a 2 SM", "2 a 5 SM", "Mais de 5 SM"],
            r["amostra_pct"],
            r["pnad_pct"]["pessoas16_efetivo"],
            strict=True,
        )
    ):
        y = 90 + i * 85
        body += text(32, y + 18, name, 19)
        for offset, v, c in [(0, a, GRAY), (28, b, BLUE)]:
            body += (
                f'<rect x="205" y="{y+offset}" width="{v*16}" height="20" fill="{c}"/>'
            )
            body += text(
                215 + v * 16, y + offset + 16, f"{v:.2f}%".replace(".", ","), 16, c
            )
    body += text(205, 455, "Perfil publicado", 16, GRAY) + text(
        410, 455, "PNAD pessoas 16+, efetivo", 16, BLUE
    )
    return svg(body, 490, "Perfil de renda publicado versus PNAD anual 2025")


def sankey(data):
    d = data["transfer"]
    matrix = d["matrix"]
    scale = 5.6
    gap = 25
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
    colors = [RED, BLUE, GRAY, "#76633d"]
    body = "<defs>"
    for j, c in enumerate(colors):
        body += f'<pattern id="hatch{j}" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(35)"><rect width="9" height="9" fill="{PAPER}"/><rect width="4" height="9" fill="{c}"/></pattern>'
    body += "</defs>" + text(30, 30, "1º TURNO", 18) + text(880, 30, "2º TURNO", 18)
    lo = left.copy()
    ro = right.copy()
    for i, row in enumerate(matrix):
        for j, v in enumerate(row):
            if v < 1e-9:
                continue
            a, b, h = lo[i], ro[j], v * scale
            lo[i] += h
            ro[j] += h
            path = f"M230 {a} C480 {a} 600 {b} 850 {b} L850 {b+h} C600 {b+h} 480 {a+h} 230 {a+h}Z"
            kind = (
                "Medido (normalizado)"
                if i in d["measured_rows"]
                else (
                    "Base consolidada: retenção integral por hipótese"
                    if i in d["consolidated_rows"]
                    else "Estimado por IPF"
                )
            )
            label = f'{d["sources"][i]} → {d["destinations"][j]}: {v:.2f} pontos do eleitorado. {kind}.'
            fill = f"url(#hatch{j})" if i in d["estimated_rows"] else colors[j]
            border = (
                'stroke="#18231d" stroke-width="2" stroke-dasharray="3 5"'
                if i in d["consolidated_rows"]
                else ""
            )
            body += f'<path d="{path}" fill="{fill}" {border} opacity="0.8" tabindex="0" class="flow" aria-label="{escape(label)}"><title>{escape(label)}</title></path>'
    for label, v, y in zip(d["sources"], d["row_targets"], left, strict=True):
        body += f'<rect x="220" y="{y}" width="10" height="{v*scale}" fill="#18231d"/>'
        body += text(208, y + v * scale / 2 + 6, f"{label} {v:g}%", 17, anchor="end")
    for j, (label, v, y) in enumerate(
        zip(d["destinations"], d["column_targets"], right, strict=True)
    ):
        body += (
            f'<rect x="850" y="{y}" width="10" height="{v*scale}" fill="{colors[j]}"/>'
        )
        body += text(875, y + v * scale / 2 + 6, f"{label} {v:g}%", 20, colors[j])
    body += text(
        30,
        855,
        "Sólida: 5 medidas. Contorno pontilhado: 2 bases fixadas. Hachura: 2 estimadas.",
        18,
    )
    body += text(
        30,
        885,
        "Espessura em pontos do eleitorado total. Passe o ponteiro ou use Tab para consultar.",
        16,
        GRAY,
    )
    return svg(
        body,
        920,
        "Transferência agregada do primeiro para o segundo turno: cinco origens medidas, duas bases consolidadas por hipótese e duas origens estimadas",
    )


def economics():
    rows = [
        ("Segurança", 24, 45),
        ("Poder de compra", 36, 43),
        ("Poupança", 30, 36),
        ("Saúde", 35, 32),
        ("Crédito", 35, 28),
        ("Educação", 40, 31),
        ("Renda", 41, 29),
        ("Bem-estar", 40, 27),
    ]
    body = text(32, 36, "Condições de vida desde 2023", 24)
    for i, (label, up, down) in enumerate(rows):
        y = 80 + i * 46
        body += text(32, y + 19, label, 18)
        body += f'<rect x="{550-down*6}" y="{y}" width="{down*6}" height="25" fill="{RED}"/><rect x="550" y="{y}" width="{up*6}" height="25" fill="{BLUE}"/>'
        body += text(540 - down * 6, y + 19, f"{down}%", 16, RED, "end") + text(
            560 + up * 6, y + 19, f"{up}%", 16, BLUE
        )
    body += text(400, 480, "Piorou", 17, RED) + text(600, 480, "Melhorou", 17, BLUE)
    return svg(body, 510, "Melhora e piora declaradas por dimensão, página 99")
