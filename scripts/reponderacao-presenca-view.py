"""Explicação progressiva da referência residual de presença relativa."""

from html import escape as esc


def fmt(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


def signed(value, digits=2):
    return ("+" if value > 0 else "−" if value < 0 else "") + fmt(abs(value), digits)


def note(data):
    m = data["presence_model"]
    return (
        '<p id="rs-presence-note" class="note"><span id="rs-presence-origin">Referência: '
        f'<b>{signed(m["central_extra_pct"], 1)}%</b> extra, a partir do resíduo do 1º turno. </span>'
        '<a href="#presenca-primeiro-turno">Entender a conta e os limites</a>. '
        "Hipótese para o 2º turno; não é presença medida por candidato.</p>"
    )


def evidence(data, table):
    m = data["presence_model"]
    rows = [
        [
            "Predição arquivada · central",
            signed(m["central"]["equivalent_extra_pct"]) + "%",
        ]
    ] + [
        [esc(r["name"]), signed(r["equivalent_extra_pct"]) + "%"]
        for r in m["alternatives"]
    ]
    houses = [
        [
            esc(r["instituto"]),
            esc(r["campo"]["inicio"] + " a " + r["campo"]["fim"]),
            signed(r["equivalent_extra_pct"]) + "%",
        ]
        for r in m["houses"]
    ]
    c = m["central"]
    before, observed, after = (
        c[k]
        for k in (
            "predicted_valid_pct",
            "observed_valid_pct",
            "after_multiplier_valid_pct",
        )
    )
    return (
        '<details class="rs-evidence" id="presenca-primeiro-turno"><summary>Por que a referência de presença relativa é +3,8%?</summary>'
        f'<p><b>Ajuste equivalente do 1º turno: {signed(c["equivalent_extra_pct"])}%.</b> A predição arquivada, gerada em {esc(m["forecast_generated_at"])}, projetava Flávio {fmt(before["flavio"])}% × Lula {fmt(before["lula"])}% nos válidos. A urna registrou {fmt(observed["flavio"])}% × {fmt(observed["lula"])}%. Ambos os recortes excluem o exterior.</p>'
        f'<p class="rs-presence-formula">{esc(m["formula"])}</p>'
        f'<p>Essa conta dá o multiplicador {fmt(c["multiplier"], 4)} necessário para igualar a razão F/L da previsão à urna, mantendo o restante fixo. A referência do simulador usa {signed(m["central_extra_pct"], 1)}%, arredondado. As duas centrais usam a mesma hipótese para facilitar a comparação.</p>'
        "<p><b>Isso não mede a presença real por candidato.</b> A urna conta votos e ausências, mas não registra a preferência dos ausentes. A razão de votos depende tanto das preferências quanto da presença; o resíduo também pode vir de erro das pesquisas, voto útil e decisões finais. Aqui ele é uma calibração descritiva depois da eleição, sem validação fora da amostra.</p>"
        f'<p><b>O que a Nexus previa?</b> Sua tabela sintética do 1º turno dava uma razão de presença F/L apenas {signed(100 * (m["nexus_1t_base_ratio"] - 1))}% acima de um. É uma projeção demográfica condicional às margens e às hipóteses da tabela, sem presença individual observada em 2026. O resíduo de +3,83% é outra métrica.</p>'
        f'<p><b>O resíduo depende da referência.</b> A média PNAD com Nexus dá {signed(m["alternatives"][0]["equivalent_extra_pct"])}%. Nas {len(houses)} casas da média, vai de {signed(m["house_range_pct"][0])}% a {signed(m["house_range_pct"][1])}%. Essa dispersão não é intervalo de confiança nem distribuição da presença real.</p>'
        + table(["Referência do 1º turno", "Ajuste equivalente F/L"], rows)
        + "<details><summary>Conferir cada casa da média</summary>"
        + table(["Instituto", "Campo", "Ajuste equivalente F/L"], houses)
        + "</details>"
        f'<p><b>Uma só taxa não explica todo o placar.</b> Aplicar o multiplicador apenas a Flávio e conservar as outras candidaturas dá {fmt(after["flavio"])}% × {fmt(after["lula"])}%, com a razão F/L correta, mas sem reproduzir os percentuais da urna. Igualar Flávio contra todas as outras candidaturas exigiria {signed(c["flavio_vs_all_others_pct"])}%, outra conta. Portanto, não atribuímos todo o erro à abstenção.</p>'
        f'<p><b>No 2º turno, transporte explícito.</b> {esc(m["limits"])} A base Nexus já contém uma diferença sintética de {signed(100 * (m["nexus_2t_base_ratio"] - 1))}% entre as taxas F/L; o controle acrescenta seu fator a essa base e recalibra o total nacional.</p>'
        '<p><a href="predicao_2026_1T_presidente.html">Predição original, preservada</a> · <a href="apuracao_1o_turno_2026.html#pesquisas">Urna e erros das pesquisas</a> · <a href="assets/reponderacao_presenca.json">Cálculo, votos e hashes</a> · '
        f'<a href="{esc(m["method_source"])}">Jiang et al.: identificação parcial com dados agregados</a>.</p></details>'
    )
