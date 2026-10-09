"""Comparecimento entre turnos: leitura em milhões e gráfico sem JavaScript."""

from html import escape as esc


def fmt(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


def signed(value, digits=2):
    return ("+" if value > 0 else "−" if value < 0 else "") + fmt(abs(value), digits)


def readout(data):
    t = data["turnout_model"]["first_round"]
    return (
        '<p id="rs-turnout-readout" class="rs-turnout-readout" aria-live="polite">'
        f'1º turno observado: <b>{fmt(t["turnout_pct"])}%</b> compareceram. '
        "Neste cenário: <b>0,00 pp</b> e <b>0,0 milhão</b> de mudança no comparecimento.</p>"
    )


def controls(data):
    t = data["turnout_model"]
    return (
        '<div id="rs-turnout-options" class="rs-turnout-options">'
        '<p class="rs-unit">Compare com as eleições anteriores</p>'
        '<div class="rs-turnout-choices" role="group" aria-label="Variação histórica de comparecimento">'
        + "".join(
            f'<button type="button" data-rs-turnout="{row["id"]}" aria-pressed="{str(row["id"] == "central").lower()}">'
            f'<span>{esc(row["name"])}</span><b>{fmt(row["turnout_pct"])}%</b>'
            f'<small>{signed(row["delta_turnout_pp"])} pp vs. 1º turno</small></button>'
            for row in t["scenarios"]
        )
        + '</div><p class="note">Cada botão muda somente o comparecimento nacional. '
        "A presença relativa e as outras hipóteses ficam como você as definiu. "
        '<a href="#comparecimento-historico">Ver a série, os testes e os limites</a>.</p></div>'
    )


def chart(years):
    # Os dois pontos são taxas de abstenção sobre aptos, nunca sobre votantes.
    def x(value):
        return 150 + (value - 15) * 45

    svg = [
        '<svg viewBox="0 0 680 310" role="img" aria-label="Abstenção presidencial no primeiro e segundo turnos de 2002 a 2022">'
        "<title>Abstenção entre turnos: sobe em cinco eleições, cai em 2022</title>"
        '<text x="150" y="24" fill="#65706b" font-size="15">○ 1º turno</text>'
        '<text x="280" y="24" fill="#235e54" font-size="15">● 2º turno</text>'
        '<text x="640" y="24" text-anchor="end" fill="#65706b" font-size="15">Δ abstenção</text>'
    ]
    for tick in (16, 18, 20, 22):
        svg.append(
            f'<line x1="{x(tick)}" x2="{x(tick)}" y1="40" y2="275" stroke="#dcded5"/><text x="{x(tick)}" y="300" text-anchor="middle" fill="#65706b" font-size="15">{tick}%</text>'
        )
    for i, r in enumerate(years):
        y = 61 + i * 40
        a, b = 100 - r["turnout_1_pct"], 100 - r["turnout_2_pct"]
        svg.append(
            f'<g><title>{r["year"]}: 1º turno {fmt(a)}%; 2º turno {fmt(b)}%; variação {signed(b-a)} pp</title>'
            f'<text x="25" y="{y+5}" fill="#203b34" font-size="18">{r["year"]}</text>'
            f'<line x1="{x(a)}" x2="{x(b)}" y1="{y}" y2="{y}" stroke="#97b8a9" stroke-width="3"/>'
            f'<circle cx="{x(a)}" cy="{y}" r="5" fill="#f4f0e7" stroke="#65706b" stroke-width="2"/>'
            f'<circle cx="{x(b)}" cy="{y}" r="5" fill="#235e54"/>'
            f'<text x="640" y="{y+5}" text-anchor="end" fill="#235e54" font-size="18">{signed(b-a)} pp</text></g>'
        )
    return "".join(svg) + "</svg>"


def evidence(data, table):
    t = data["turnout_model"]
    b = t["first_round"]
    low, high = t["observed_delta_range_pp"]
    rows = [
        [
            str(r["year"]),
            fmt(r["turnout_1_pct"]) + "%",
            fmt(r["turnout_2_pct"]) + "%",
            signed(r["delta_turnout_pp"]) + " pp",
            f'<a href="{esc(r["source"]["url"])}">Fonte</a>',
        ]
        for r in t["history"]
    ]
    return (
        '<details class="rs-evidence" id="comparecimento-historico"><summary>Abstenção entre turnos: história, calibração de 2026 e testes</summary>'
        "<h3>O segundo turno costuma perder presença. Em 2022, ganhou.</h3>"
        '<div class="rs-turnout-chart">' + chart(t["history"]) + "</div>"
        f'<p>2026 começa em um dado observado: <b>{fmt(b["turnout_pct"])}% de comparecimento</b> '
        f'({fmt(b["attendance"]/1e6, 2)} milhões) e <b>{fmt(b["absence_pct"])}% de abstenção</b> '
        f'({fmt(b["absence"]/1e6, 2)} milhões), nas 27 UFs. '
        "A referência antiga de 79,58% da Nexus foi substituída por essa apuração. "
        '<a href="apuracao_1o_turno_2026.html">Consultar a apuração do 1º turno</a>.</p>'
        f"<p>Nas seis eleições, a mudança do comparecimento variou de <b>{signed(low)} a {signed(high)} pp</b>. "
        f'Aplicada à base de 2026, daria <b>{fmt(b["turnout_pct"]+low)}% a {fmt(b["turnout_pct"]+high)}%</b> '
        "de comparecimento. É o envelope de cenários observados, não um intervalo preditivo ou limite para 2026.</p>"
        f'<p>{esc(t["method"])}</p>'
        + table(
            ["Regra de transporte", "MAE / pp", "Viés / pp"],
            [
                [esc(r["name"]), fmt(r["mae_pp"]), signed(r["bias_pp"])]
                for r in t["retrospective"]
            ],
        )
        + "<p>Teste em ordem de ano: prever 2014 com 2002–2010, 2018 com dados até 2014 e 2022 com dados até 2018. "
        "Erro medido no comparecimento, sem pesquisas eleitorais ou voto por candidato. "
        "A central conserva o 1º turno porque não encontramos sustentação robusta para um desconto automático.</p>"
        f'<p>{esc(t["limits"])}</p>'
        "<p><b>Abstenção nacional e relativa são coisas diferentes.</b> A série estima quantas pessoas comparecem no total. "
        "Ela não identifica a preferência de quem falta. Não usamos o crescimento da ausência para inferir vantagem de Flávio ou Lula. "
        "As propensões Nexus continuam somente como hipótese de taxas relativas, recalibradas ao total escolhido. "
        "Brancos/nulos continuam separados: quem não comparece não deposita voto inválido.</p>"
        "<details><summary>Totais históricos, fontes e diferenças de universo</summary>"
        + table(
            [
                "Eleição",
                "Comparecimento 1º",
                "Comparecimento 2º",
                "Δ comparecimento",
                "Documento",
            ],
            rows,
        )
        + f'<p>{esc(t["scope_note"])}</p>'
        + "<p>Em 2018 e 2022, incluir ou excluir o exterior muda a variação entre turnos em menos de 0,01 pp. "
        "Isso é uma conferência nesses dois anos; não prova identidade para os anteriores. "
        "A série guarda a precisão disponível: taxas arredondadas permanecem arredondadas.</p></details>"
        '<p><a href="assets/reponderacao_comparecimento.json">Série, cenários, retrospectivas e hashes (JSON)</a>.</p></details>'
    )
