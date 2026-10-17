"""Duas centrais comparáveis, explicação progressiva e trilha do algoritmo."""

from html import escape as esc


def fmt(number):
    return f"{number:.1f}".replace(".", ",")


def futura_inclusion(data):
    row = next(
        (p for p in data["projection"]["selected"] if p["instituto"] == "Futura"),
        None,
    )
    if not row:
        return ""
    return (
        f' A Futura está incluída pelo placar publicado, com {fmt(100 * row["weight"])}% '
        "do peso nesta rodada, mesmo sem cruzamento de voto por renda."
    )


def central_cards(data):
    states = data["projection"]["states"]
    runs = f'{data["projection"]["mc"]["runs"]:,}'.replace(",", ".")
    unadjusted = ", ".join(
        p["instituto"]
        for p in data["projection"]["selected"]
        if not p["income_available"]
    )
    values = [
        (
            "media",
            "Central Média Arvor",
            data["central"],
            "Peso igual entre casas com renda. A referência simples que já usávamos.",
            "Cada pesquisa é reponderada pela renda da PNAD, passa pelas hipóteses de comparecimento e tem seus votos válidos calculados. Depois fazemos a média: cada instituto pesa o mesmo. Entram apenas as casas com cruzamento de renda compatível. "
            + (
                f"{unadjusted} entram pelo publicado somente na Projeção."
                if unadjusted
                else ""
            ),
        ),
        (
            "projecao",
            "Central Projeção Arvor",
            data["central_projection"],
            'Nacionais na central; <a href="#estados-projecao">estaduais no diagnóstico</a>. Recência e simulações de incerteza.',
            "A predição original do 1º turno combinava pesquisas nacionais e estaduais, com calibração nacional e ponderação por eleitorado. Nesta versão do 2º turno, o placar central usa pesquisas nacionais. "
            f'As estaduais pós-urna cobrem {fmt(states["coverage_pct"])}% do eleitorado e entram no <a href="#estados-projecao">diagnóstico territorial</a>; ainda não alteram o placar central. '
            f"Recência significa dar mais peso ao campo recente. Tendência é a mudança ao longo do tempo dentro da mesma casa; reduzimos a inclinação quando ela é incerta, para evitar extrapolar ruído. PNAD onde há cruzamento; publicado onde falta, identificado como tal. Monte Carlo faz {runs} contas variando amostras, pesos das casas e um erro que pode atingir todas juntas. A faixa mostra como o resultado muda nessas hipóteses; não mede a chance real de vitória. Não é machine learning supervisionado. As partes territoriais e a validação do primeiro turno não são transferidas."
            + futura_inclusion(data),
        ),
    ]
    return (
        '<div class="rs-centrals" role="group" aria-label="Escolha a central de referência">'
        + "".join(
            f'<article class="rs-central-card" data-central-card="{key}"><button type="button" data-rs-central="{key}" aria-pressed="{str(key == "media").lower()}"><span>{name}</span><b id="rs-central-score-{key}">{fmt(c["flavio"])}% × {fmt(c["lula"])}%</b><small>Flávio × Lula · votos válidos</small></button><p>{description}</p><details><summary aria-label="Entender {name}"><span aria-hidden="true">?</span> Como funciona</summary><p>{detail}</p></details></article>'
            for key, name, c, description, detail in values
        )
        + "</div>"
    )


def evidence(data, table):
    p = data["projection"]
    rows = [
        [
            f'<a href="{("#pesquisa-" + esc(row["id"])) if row["income_available"] else "#cobertura-atual"}">{esc(row["instituto"])}</a>',
            esc(row["campo"]["inicio"] + " a " + row["campo"]["fim"]),
            fmt(100 * row["weight"]) + "%",
            (
                "PNAD · sensibilidade de renda"
                if row["income_available"]
                else "Publicado · sem ajuste de renda compatível"
            ),
        ]
        for row in p["selected"]
    ]
    u = p["uncertainty"]
    return (
        '<details class="rs-evidence" id="modelo-projecao"><summary>Motor da Projeção Arvor: dados, pesos, tendência e simulações</summary>'
        f'<p>{esc(p["method"])}</p>'
        '<p><b>Nacionais e estaduais:</b> as pesquisas nacionais abaixo alimentam o placar central do 2º turno. As estaduais pós-urna permitem conferir o quadro por UF no <a href="#estados-projecao">diagnóstico territorial</a>, sem alterar esta central. A predição original do 1º turno combinava as duas camadas com calibração nacional e ponderação por eleitorado.</p>'
        + table(["Instituto", "Campo", "Peso por recência", "Base usada"], rows)
        + (
            "<p><b>Futura incluída:</b>"
            + futura_inclusion(data)
            + " Na última onda do 1º turno, o erro na diferença F−L foi +0,24 pp; os percentuais de Flávio e Lula ficaram 2,29 e 2,53 pp abaixo da urna nos válidos. "
            '<a href="apuracao_1o_turno_2026.html#pesquisas">Consultar a auditoria das pesquisas contra a urna</a>. '
            "O peso segue a mesma regra de recência das demais casas; uma eleição não basta para estimar confiabilidade futura.</p>"
            if futura_inclusion(data)
            else ""
        )
        + f'<p><b>Tendência atual:</b> {esc(p["trend"]["pnad"]["status"])} Horizonte: {fmt(p["trend"]["pnad"]["horizonte_dias"])} dias desde o campo efetivo até <a href="{esc(p["election_source"])}">25/10/2026</a>.</p>'
        f'<p><b>Indecisos:</b> {esc(p["undecided"])}</p>'
        f'<p>Central Projeção: Flávio {fmt(data["central_projection"]["flavio"])}% × Lula {fmt(data["central_projection"]["lula"])}%. Faixa central de 90% dos {p["mc"]["runs"]} sorteios: Flávio {fmt(u["flavio"]["p05"])}–{fmt(u["flavio"]["p95"])}%; Lula {fmt(u["lula"]["p05"])}–{fmt(u["lula"]["p95"])}%. Estes limites não são um intervalo com cobertura validada contra a urna.</p>'
        "<p>O tamanho amostral é limitado a 2.000 por casa e dividido pelo efeito de desenho assumido de 1,5. Erro comum: desvio de 2 pp na diferença F−L; são parâmetros herdados, não estimados para o 2º turno. Os sorteios e a semente ficam na versão do link e são reaplicados aos controles; não há sorteio novo a cada movimento.</p>"
        "<p><b>Por que difere da Média?</b> Mudam os pesos e a cobertura: casas sem ajuste compatível de renda entram pelo publicado nesta central. A diferença não é atribuível só ao algoritmo. A hipótese relativa transportada do 1º turno é compartilhada.</p>"
        f'<p>{esc(p["limits"])}</p><p><a href="predicao_2026_1T_presidente.html">Consultar a predição original do 1º turno</a> · <a href="assets/reponderacao_simulador.json">Dados e sorteios das duas centrais</a>.</p></details>'
        + states_evidence(p["states"], table)
    )


def states_evidence(data, table):
    rows = []
    metrics = []
    for row in data["selected"]:
        p = row["publicado"]
        rows.append(
            [
                f'<a href="{esc(row["source"]["url"])}">{esc(row["instituto"])} · {esc(row["uf"])}</a>',
                esc(row["campo"]["inicio"] + " a " + row["campo"]["fim"]),
                esc(row["divulgacao"]),
                f'{p["flavio"]}% × {p["lula"]}% · B/N {p["branco_nulo"]}% · indecisos {p["indecisos"]}%',
                str(row["n"]),
            ]
        )
        v, q = row.get("validos_publicados"), row["validos_normalizados"]
        if v:
            metrics.append(
                f'<p>{esc(row["instituto"])} {esc(row["uf"])} declara {fmt(v["flavio"])}% × {fmt(v["lula"])}% nos válidos. Normalizar os totais inteiros dá {fmt(q["flavio"])}% × {fmt(q["lula"])}%; arredondamentos independentes podem produzir valores diferentes. Preservamos as duas métricas. {"Sem voto por renda disponível, não há sensibilidade PNAD nesta onda." if not row["income_available"] else ""}</p>'
            )
    return (
        '<details class="rs-evidence" id="estados-projecao"><summary>Pesquisas estaduais: diagnóstico territorial</summary>'
        f'<p>Conferência em {esc(data["reference"])}: {len(data["selected"])} pesquisas em {len(data["covered_ufs"])} UF com campo pós-04/10, cobrindo {fmt(data["coverage_pct"])}% do eleitorado brasileiro. {esc(data["use"])}</p>'
        + table(
            [
                "Instituto / UF",
                "Campo",
                "Divulgação",
                "Flávio × Lula / total",
                "Amostra",
            ],
            rows,
        )
        + "".join(metrics)
        + f'<p>{esc(data["reason"])}</p>'
        "<p>Varredura de 13/10: incorporada Quaest DF, divulgada em 12/10 com campo 08–11/10, junto da Datafolha DF de 09/10. Não foi localizado outro placar estadual presidencial verificável com campo pós-04/10 nas fontes consultadas. A publicação Datafolha SP de 05/10 e as íntegras Quaest de véspera incluem campo anterior à urna. A agenda contém pesquisas futuras; registro não é resultado divulgado. Data de upload não vira data de campo. A lista de fontes e limites está no histórico.</p>"
        '<p><a href="assets/reponderacao_estaduais.json">Dados estaduais, fontes e hashes</a>.</p></details>'
    )
