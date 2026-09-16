"""SVG estático: os dados continuam legíveis sem JavaScript ou rede."""

from html import escape

COLORS = ["#af302b", "#195ccc", "#666c75", "#343e49"]


def text(x, y, value, size=16, color="#102438", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-family="Arial,sans-serif">{escape(str(value))}</text>'


def svg(body, h, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 {h}" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><rect width="1080" height="{h}" fill="#fffdf8"/>{body}</svg>'


def history(d):
    h = d["tables"]["HISTORY"]
    b = ""
    for v in [35, 40, 45, 50]:
        y = 300 - (v - 35) * 14
        b += f'<path d="M60 {y}H930" stroke="#d1d5d6"/>' + text(
            48, y + 5, v, 14, anchor="end"
        )
    for key, color, name in [
        ("lula", COLORS[0], "Lula"),
        ("flavio", COLORS[1], "Flávio"),
    ]:
        pts = [(70 + i * 76, 300 - (v - 35) * 14) for i, v in enumerate(h[key])]
        b += f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="4"/>'
        for (x, y), v in zip(pts, h[key], strict=True):
            b += f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>' + text(
                x, y + (-13 if key == "lula" else 24), v, 15, color, "middle"
            )
        b += text(935, pts[-1][1] + 5, name, 20, color)
    for i, date in enumerate(h["dates"]):
        b += text(70 + i * 76, 340, date, 13, anchor="middle")
    b += text(
        60,
        385,
        "2º turno publicado · série do relatório de 14/9, p.28 · percentuais totais",
        15,
    )
    return svg(
        b,
        410,
        "Série Quaest: Lula vai de 45 a 40 e Flávio de 38 a 42 entre janeiro e setembro.",
    )


def profiles(d):
    rows = [
        ("Quaest · perfil publicado", d["tables"]["PROFILE"]),
        ("PNAD · pessoas 16+", d["reweight"]["renda"]["pnad_pct"]["pessoas16_efetivo"]),
    ]
    b = ""
    colors = ["#196047", "#8b6109", "#195ccc"]
    for i, (name, vals) in enumerate(rows):
        y = 55 + i * 110
        b += text(24, y, name, 20)
        x = 24
        for j, v in enumerate(vals):
            width = v * 10
            b += (
                f'<rect x="{x}" y="{y + 15}" width="{width}" height="48" fill="{colors[j]}"/>'
                + text(
                    x + width / 2,
                    y + 46,
                    f"{v:.2f}%".replace(".", ","),
                    18,
                    "white",
                    "middle",
                )
            )
            x += width
    for j, label in enumerate(["Até 2 SM", "Mais de 2 a 5 SM", "Mais de 5 SM"]):
        b += text(30 + j * 345, 285, label, 18, colors[j])
    return svg(
        b, 310, "Quaest usa 31, 42 e 27 por cento por renda; PNAD 35,19, 39,26 e 25,55."
    )


def sankey(d):
    s = d["transfer"]
    scale = 3.9
    left = []
    right = []
    y = 65
    for v in s["shares"]:
        left.append(y)
        y += v * scale + 16
    y = 100
    for v in s["targets"]:
        right.append(y)
        y += v * scale + 22
    b = '<defs><pattern id="estimated" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M-2 2L2 -2M0 8L8 0M6 10L10 6" stroke="#102438" stroke-width="1.5"/></pattern><pattern id="assumed" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="1.4" fill="#fffdf8"/></pattern></defs>'
    lc = left[:]
    rc = right[:]
    for i, row in enumerate(s["matrix"]):
        for j, v in enumerate(row):
            if v < 1e-10:
                continue
            a, z = lc[i], rc[j]
            w = v * scale
            path = f"M205 {a} C440 {a},640 {z},860 {z} L860 {z + w} C640 {z + w},440 {a + w},205 {a + w} Z"
            title = escape(
                f"{s['origins'][i]} → {s['destinations'][j]}: {v:.2f} pontos do eleitorado; {s['kinds'][i]}"
            )
            b += f'<g tabindex="0"><title>{title}</title><path d="{path}" fill="{COLORS[j]}" opacity=".48"/>'
            if s["kinds"][i] != "medido":
                b += f'<path d="{path}" fill="url(#{"estimated" if i >= 6 else "assumed"})" opacity=".55"/>'
            b += "</g>"
            lc[i] += w
            rc[j] += w
    for i, v in enumerate(s["shares"]):
        b += f'<rect x="195" y="{left[i]}" width="10" height="{v * scale}" fill="#102438"/>'
        b += text(
            182,
            left[i] + v * scale / 2 + 5,
            f"{s['origins'][i]} {v}%",
            16,
            anchor="end",
        )
    for j, v in enumerate(s["targets"]):
        b += (
            f'<rect x="860" y="{right[j]}" width="12" height="{v * scale}" fill="{COLORS[j]}"/>'
            + text(
                882, right[j] + v * scale / 2 + 5, f"{s['destinations'][j]} {v}%", 16
            )
        )
    b += text(24, 28, "1º turno", 18) + text(875, 28, "2º turno", 18)
    b += text(
        24,
        602,
        "Sólido: 4 origens medidas · pontos: 2 bases fixadas · hachura: 2 origens estimadas",
        17,
    )
    return svg(
        b,
        630,
        "Transferência de votos. Bases Lula e Flávio integralmente retidas por hipótese; quatro linhas medidas pela Quaest; indecisos e não voto estimados.",
    )
