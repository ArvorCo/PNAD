"""Duas centrais comparáveis, explicação progressiva e trilha do algoritmo."""

from html import escape as esc


def fmt(number):
    return f"{number:.1f}".replace(".", ",")


def central_cards(data):
    values = [
        (
            "media",
            "Central Média Arvor",
            data["central"],
            "Peso igual entre casas com renda. A referência simples que já usávamos.",
            "Cada pesquisa é reponderada pela renda da PNAD, passa pelas hipóteses de comparecimento e tem seus votos válidos calculados. Depois fazemos a média: cada instituto pesa o mesmo. Entram apenas as casas com cruzamento de renda elegível; Vox sem cruzamento não entra nesta central.",
        ),
        (
            "projecao",
            "Central Projeção Arvor",
            data["central_projection"],
            "Prioriza pesquisas recentes e simula incerteza. Usa também publicados sem renda.",
            "Adapta o motor nacional da predição do primeiro turno. Recência significa dar mais peso ao campo recente. Tendência é a mudança ao longo do tempo dentro da mesma casa; reduzimos a inclinação quando ela é incerta, para evitar extrapolar ruído. PNAD onde há cruzamento; publicado onde falta, identificado como tal. Monte Carlo faz 2.000 contas variando amostras, pesos das casas e um erro que pode atingir todas juntas. A faixa mostra como o resultado muda nessas hipóteses; não mede a chance real de vitória. Não é machine learning supervisionado. As partes territoriais e a validação do primeiro turno não são transferidas.",
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
                else "Publicado · sem voto por renda"
            ),
        ]
        for row in p["selected"]
    ]
    u = p["uncertainty"]
    return (
        '<details class="rs-evidence" id="modelo-projecao"><summary>Motor da Projeção Arvor: dados, pesos, tendência e simulações</summary>'
        f'<p>{esc(p["method"])}</p>'
        + table(["Instituto", "Campo", "Peso por recência", "Base usada"], rows)
        + f'<p><b>Tendência atual:</b> {esc(p["trend"]["pnad"]["status"])} Horizonte: {fmt(p["trend"]["pnad"]["horizonte_dias"])} dias desde o campo efetivo até <a href="{esc(p["election_source"])}">25/10/2026</a>.</p>'
        f'<p><b>Indecisos:</b> {esc(p["undecided"])}</p>'
        f'<p>Central Projeção: Flávio {fmt(data["central_projection"]["flavio"])}% × Lula {fmt(data["central_projection"]["lula"])}%. Faixa central de 90% dos {p["mc"]["runs"]} sorteios: Flávio {fmt(u["flavio"]["p05"])}–{fmt(u["flavio"]["p95"])}%; Lula {fmt(u["lula"]["p05"])}–{fmt(u["lula"]["p95"])}%. Estes limites não são um intervalo com cobertura validada contra a urna.</p>'
        "<p>O tamanho amostral é limitado a 2.000 por casa e dividido pelo efeito de desenho assumido de 1,5. Erro comum: desvio de 2 pp na diferença F−L; são parâmetros herdados, não estimados para o 2º turno. Os sorteios e a semente ficam na versão do link e são reaplicados aos controles; não há sorteio novo a cada movimento.</p>"
        "<p><b>Por que difere da Média?</b> Mudam os pesos e a cobertura: a Vox entra pelo placar publicado nesta central. A diferença não é atribuível só ao algoritmo. A hipótese de presença relativa +5% é compartilhada.</p>"
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
        '<details class="rs-evidence" id="estados-projecao"><summary>Estaduais atualizadas: cobertura e uso na predição</summary>'
        f'<p>Conferência em {esc(data["reference"])}: {len(data["covered_ufs"])} UF com campo pós-04/10 incorporada ao diagnóstico, cobrindo {fmt(data["coverage_pct"])}% do eleitorado brasileiro. {esc(data["use"])}</p>'
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
        "<p>Varredura de 09/10: os painéis presidenciais consultados para SP, MG, RJ e DF ainda traziam colunas até 03/10. A confirmação do novo DF veio da matéria da Folha de 09/10. A agenda anunciava RJ em 08/10, mas não foi encontrado novo placar presidencial verificável. PDFs Quaest enviados depois de 04/10 incluem campos anteriores à urna: a ficha da Paraíba, publicada no site em 08/10, declara coleta em 02–03/10. Data de upload não vira data de campo.</p>"
        '<p><a href="assets/reponderacao_estaduais.json">Dados estaduais, fontes e hashes</a>.</p></details>'
    )
