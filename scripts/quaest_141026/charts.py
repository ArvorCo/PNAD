"""Gráficos editoriais: escalas explícitas, valores visíveis e fontes locais."""

from datetime import date
from html import escape as esc

from dossies_2t_2026.view import fmt, signed

BLUE, RED = "#386ba6", "#a74247"
SOURCE = "Fonte: Quaest / painel G1, divulgação de 14/10/2026. Percentuais dentro de cada grupo; bases não publicadas."


def frame(title, content, source=SOURCE):
    return (
        '<figure class="chart q-chart"><figcaption>'
        + esc(title)
        + "</figcaption>"
        + content
        + '<p class="note">'
        + esc(source)
        + "</p></figure>"
    )


def pairs(title, rows, labels=("Flávio", "Lula"), digits=0, source=SOURCE):
    """Barras independentes de 0 a 100, inclusive quando a soma excede 100."""
    body = '<p class="q-scale">Escala comum: 0–100%</p>'
    for name, values in rows.items():
        body += '<div class="q-pair"><b>' + esc(name) + "</b>"
        for label, value, color in zip(labels, values, (BLUE, RED), strict=True):
            body += (
                f'<div class="q-pair-line"><span>{esc(label)}</span>'
                f'<div class="q-track"><i style="width:{value}%;background:{color}"></i></div>'
                f"<strong>{fmt(value,digits)}%</strong></div>"
            )
        body += "</div>"
    return frame(title, body, source)


def gaps(title, rows, limit, digits=0, source=SOURCE):
    body = (
        '<div class="q-gap-legend"><span>← favorece Lula</span>'
        "<span>favorece Flávio →</span></div>"
        f'<p class="q-scale">Diferença F−L em pontos percentuais · escala −{fmt(limit,0)} a +{fmt(limit,0)}</p>'
    )
    for label, value in rows.items():
        width = 50 * abs(value) / limit
        left = 50 if value >= 0 else 50 - width
        color = BLUE if value >= 0 else RED
        body += (
            f'<div class="q-gap-row"><b>{esc(label)}</b>'
            f'<div class="q-gap-track"><i style="left:{left}%;width:{width}%;background:{color}"></i></div>'
            f"<strong>{signed(value,digits)} pp</strong></div>"
        )
    return frame(title, body, source)


def timeline(data):
    waves = data["serie"]
    start = date.fromisoformat(waves[0]["divulgacao"])
    end = date.fromisoformat(waves[-1]["divulgacao"])

    def x(day):
        return 50 + 760 * (date.fromisoformat(day) - start).days / (end - start).days

    def y(value):
        return 270 - (value - 30) * 11

    svg = [
        '<svg viewBox="0 0 900 330" role="img" aria-label="Série de intenção de voto de maio a outubro"><title>Flávio e Lula: percentuais publicados em doze ondas</title>'
    ]
    for v in range(30, 51, 5):
        svg.append(
            f'<path d="M50 {y(v)}H830" stroke="#d3d1c6"/><text x="38" y="{y(v)+4}" text-anchor="end">{v}%</text>'
        )
    election = x("2026-10-04")
    svg.append(
        f'<path d="M{election} 40V275" stroke="#5e6c63" stroke-dasharray="4 4"/><text x="{election-5}" y="24" text-anchor="end">04/10 · urna do 1º turno</text>'
    )
    for key, color, label in [("flavio", BLUE, "Flávio"), ("lula", RED, "Lula")]:
        points = " ".join(
            f'{x(w["divulgacao"])},{y(w["publicado"][key])}' for w in waves
        )
        svg.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>'
        )
        for w in waves:
            value = w["publicado"][key]
            day = w["divulgacao"]
            svg.append(
                f'<circle cx="{x(day)}" cy="{y(value)}" r="4" fill="{color}"><title>{day}: {label} {value}%</title></circle>'
            )
        svg.append(
            f'<text x="825" y="{y(waves[-1]["publicado"][key])+5}" fill="{color}" font-weight="600">{label} {waves[-1]["publicado"][key]}</text>'
        )
    for i, w in enumerate(waves):
        label = w["divulgacao"][8:10] + "/" + w["divulgacao"][5:7]
        svg.append(
            f'<text x="{x(w["divulgacao"])}" y="{295+(i%2)*18}" text-anchor="middle">{label}</text>'
        )
    svg.append("</svg>")
    mobile = (
        '<div class="q-timeline-mobile">'
        + "".join(
            f'<div><span>{w["divulgacao"][8:10]}/{w["divulgacao"][5:7]}</span><b class="q-blue">F {w["publicado"]["flavio"]}%</b><b class="q-red">L {w["publicado"]["lula"]}%</b><span>{signed(w["gap_total_pp"],0)} pp</span></div>'
            for w in waves
        )
        + "</div>"
    )
    return frame(
        "A mesma pergunta de segundo turno, em 12 ondas",
        '<div class="q-timeline">' + "".join(svg) + "</div>" + mobile,
        "Fonte: acervo Quaest, maio–outubro de 2026. Eixo vertical de 30% a 50%; datas de divulgação no eixo horizontal. Linhas apenas ligam as ondas, sem interpolar pesquisas. No celular, cada ponto aparece com seu valor e diferença F−L.",
    )


def uncertainty(data):
    low, high = data["aas"]["intervalo_gap_95_pp"]
    point = data["serie"][-1]["gap_total_pp"]
    # Escala fixa e simétrica: −7 a +7 pp.
    left = (low + 7) / 14 * 100
    width = (high - low) / 14 * 100
    body = (
        '<p class="q-gap-legend"><span>← Lula numericamente à frente</span><span>Flávio à frente →</span></p>'
        f'<div class="q-interval"><span class="q-zero"></span><span class="q-range" style="left:{left}%;width:{width}%"></span><span class="q-point" style="left:{(point+7)/14*100}%"></span></div>'
        '<div class="q-axis"><span>−7 pp</span><span>0</span><span>+7 pp</span></div>'
        f'<div class="q-interval-values"><span>Limite inferior <b>{signed(low,2)} pp</b></span><span>Diferença publicada <b>{signed(point,0)} pp</b></span><span>Limite superior <b>{signed(high,2)} pp</b></span></div>'
    )
    return frame(
        "Dois pontos de diferença; o intervalo de referência cruza zero",
        body,
        "Cálculo Arvor sob amostragem aleatória simples (AAS), n = 2.154, referência de 95%. Não é um intervalo validado para o desenho efetivo da Quaest; não inclui cotas, conglomerados ou seleção.",
    )


def income_charts(data):
    income = data["identificacao_renda"]
    labels = [r["rotulo"] for r in data["pesquisa"]["renda"]["faixas"]]
    profile = pairs(
        "O peso de cada faixa: perfil publicado × régua PNAD",
        dict(
            zip(
                labels,
                zip(income["pesos_registro_pct"], income["pnad_pct"], strict=True),
                strict=True,
            )
        ),
        labels=("Perfil", "PNAD"),
        digits=2,
        source="Fontes: perfil Quaest, p. 147 (31/42/27), e PNADC anual 2025, pessoas 16+. Etapa antes/depois dos pesos não indicada no perfil; seu uso como margem dos cruzamentos continua hipótese.",
    )
    adj = income["reponderacao_pontual"]
    comparison = pairs(
        "Como muda o placar sob essa hipótese",
        {"Publicado": (46, 44), "Sensibilidade PNAD": (adj["flavio"], adj["lula"])},
        digits=2,
        source="Percentuais sobre o total. Ajustado = publicado + diferença entre recomposições PNAD e perfil. Sensibilidade a uma margem; não é resultado corrigido nem previsão.",
    )
    change = gaps(
        "03/10 → 14/10: movimentos opostos dentro das faixas",
        {r["faixa"]: r["mudanca_gap_pp"] for r in income["evolucao_0310"]},
        5,
        source="Fonte: cruzamentos Quaest de 03/10 e 14/10. Mudança da diferença F−L dentro de cada faixa; não são contribuições ao total nem variações estatisticamente identificadas.",
    )
    return '<div class="q-chart-grid">' + profile + comparison + "</div>" + change


def historical_income_chart(history):
    return gaps(
        "Julho → setembro: contribuição de cada faixa para a mudança F−L",
        {r["faixa"]: r["contribuicao_gap_pp"] for r in history["faixas"]},
        5,
        digits=2,
        source="Conta Arvor com pesos publicados 31/42/27 fixos. Soma +7,64 pp contra +8 pp no total; resíduo +0,36 pp preservado. Fonte: Quaest, 15/07 e 28/09. Não identifica migração individual.",
    )
