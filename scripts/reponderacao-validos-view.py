"""Two current forecast charts, usable without JS, with paired universe controls."""

import importlib
import json
from html import escape

MODEL = importlib.import_module("reponderacao-validos")


def fmt(value):
    return f"{value:.1f}".replace(".", ",")


def signed(value):
    return ("+" if value > 0 else "−" if value < 0 else "") + fmt(abs(value))


def bars(values, labels, urna=None):
    return "".join(
        f'<div class="vf-row{ " vf-row-audit" if urna else ""}" data-candidate="{k}"><span>{escape(labels[k])}</span>'
        f'<span class="vf-track"><span class="vf-bar vf-{k}" style="width:{v:.6f}%"></span>'
        + (
            f'<span class="vf-urna-tick" style="left:{urna[k]:.6f}%" title="Urna: {fmt(urna[k])}%"></span>'
            if urna
            else ""
        )
        + f'</span><b class="vf-value">{fmt(v)}%</b>'
        + (
            f'<span class="vf-urna-value">{fmt(urna[k])}%</span><span class="vf-error">{signed(v - urna[k])}</span>'
            if urna
            else ""
        )
        + "</div>"
        for k, v in values.items()
    )


def gap(values):
    diff = values["lula"] - values["flavio"]
    if abs(diff) < 0.05:
        return "Empate na projeção arredondada"
    return f'{"Lula" if diff > 0 else "Flávio"} +{fmt(abs(diff))} pontos'


def card(data, ballot):
    block = data["ballots"][ballot]
    defaults = data["display_defaults"]
    mode = defaults["mode"]
    scenario = block["scenarios"][defaults["scenario"]]
    values = scenario["aggregate"][mode]
    mode_label = (
        data["modes"][mode] + ": " + data["scenario_labels"][defaults["scenario"]]
    )
    turn = "Primeiro" if ballot == "1t" else "Segundo"
    urna = block.get("urna")
    reference = block["reference"]
    houses = ", ".join(p["instituto"] for p in scenario["polls"])
    title = "1º turno: projeção × urna" if urna else f"{turn} turno, votos válidos"
    columns = (
        '<div class="vf-columns" aria-hidden="true"><span>Candidatura</span><span>Projeção</span><span>Urna</span><span>Erro / pp</span></div>'
        if urna
        else ""
    )
    gap_error = (
        f'<p class="vf-gap-error">Urna: {gap(urna)}. Erro L−F: <b>{signed(scenario["erros"][mode]["diferenca_lula_flavio_pp"])} pp</b>.</p>'
        if urna
        else ""
    )
    precision = (
        'Janela fechada em 04/10; parâmetros de comparecimento da Nexus de 28/09. Sem recalibrar pela urna. <a href="#primeiro-turno">Erros dos institutos</a> · <a href="apuracao_1o_turno_2026.html#pesquisas">Apuração completa</a>.'
        if urna
        else "Projeção condicional, sem intervalo preditivo validado."
    )
    aria = "; ".join(
        f"{data['labels'][k]} {fmt(v)}%"
        + (f"; urna {fmt(urna[k])}%; erro {signed(v - urna[k])} pontos" if urna else "")
        for k, v in values.items()
    )
    return (
        f'<article class="vf-card" data-ballot="{ballot}"><p class="kicker">{turn} turno · {block["n_houses"]} institutos · {reference}</p>'
        f'<h3>{title}</h3><p class="vf-mode-label">{escape(mode_label)}</p>{columns}'
        f'<div class="vf-bars" role="img" aria-label="{escape(aria, quote=True)}">'
        f'{bars(values, data["labels"], urna)}</div>'
        f'<p class="vf-gap">{gap(values)}</p>'
        f"{gap_error}"
        f'<p class="vf-coverage">{escape(houses)}. Peso igual por instituto.</p>'
        f'<p class="vf-precision">{precision}</p></article>'
    )


def section_html(source, table, ballots=("1t", "2t")):
    data = MODEL.write(source)
    data["ballots"] = {b: data["ballots"][b] for b in ballots}
    defaults = data["display_defaults"]
    rows, excluded, corrections = [], [], []
    for ballot, block in data["ballots"].items():
        s = block["scenarios"][defaults["scenario"]]
        for p in s["polls"]:
            values = "".join(
                f'<td data-mode="{m}">{fmt(p[m]["lula"])} × {fmt(p[m]["flavio"])}</td>'
                for m in MODEL.MODES
            )
            extra = ""
            if "urna" in block:
                u = block["urna"]
                diff = (p[defaults["mode"]]["lula"] - p[defaults["mode"]]["flavio"]) - (
                    u["lula"] - u["flavio"]
                )
                extra = f'<td>{fmt(u["lula"])} × {fmt(u["flavio"])}</td><td data-poll-error>{signed(diff)}</td>'
            else:
                extra = '<td colspan="2">2º turno em andamento</td>'
            rows.append(
                f'<tr data-poll="{p["id"]}" data-ballot="{ballot}"><th scope="row">{escape(p["instituto"])} · {ballot}</th><td>{escape(p["divulgacao"])}</td>{values}{extra}</tr>'
            )
            if p["negative_mass_removed"]:
                corrections.append(
                    f'{p["instituto"]}, {ballot}: '
                    + ", ".join(
                        f"{k} = {v:.3f}".replace(".", ",")
                        for k, v in p["negative_mass_removed"].items()
                    )
                )
        excluded += [
            f'{p["instituto"]}, {ballot}: {p["reason"]}.' for p in block["excluded"]
        ]
    age_options = "".join(
        f'<option value="{k}"{ " selected" if k == defaults["scenario"] else ""}>{escape(v)}</option>'
        for k, v in MODEL.SCENARIOS.items()
    )
    buttons = "".join(
        f'<button type="button" data-vf-mode="{k}" aria-pressed="{str(k == defaults["mode"]).lower()}">{escape(v)}</button>'
        for k, v in MODEL.MODES.items()
    )
    coverage_note = " ".join(excluded) or "Nenhuma exclusão adicional na janela atual."
    coverage_short = (
        "; ".join(
            ("1º turno" if b == "1t" else "2º turno")
            + ": "
            + ", ".join(p["instituto"] for p in block["excluded"])
            for b, block in data["ballots"].items()
            if block["excluded"]
        )
        or "Nenhuma exclusão adicional."
    )
    negative_note = "; ".join(corrections) or "Nenhuma massa negativa nesta janela."
    rate_rows = []
    for ballot in data["ballots"]:
        rates = data["ballots"][ballot]["scenarios"]["central"]["rates"]
        rate_rows.extend(
            [
                [ballot, data["labels"].get(k, "Demais candidatos"), fmt(100 * v) + "%"]
                for k, v in rates.items()
                if k not in MODEL.NONCHOICE
            ]
        )
    loo_rows = [
        [b, p["without"], fmt(p["valid"]["lula"]), fmt(p["valid"]["flavio"])]
        for b, block in data["ballots"].items()
        for p in block["scenarios"]["central"]["leave_one_out"]
    ]
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    return (
        '<section id="projecao-validos" class="chapter vf-section"><div class="wrap">'
        '<p class="eyebrow">PROJEÇÃO CONDICIONAL · VOTOS VÁLIDOS · '
        + escape(data["reference"])
        + "</p>"
        "<h2>Da pesquisa<br><em>à urna.</em></h2>"
        '<p class="lead">O primeiro turno já tem resultado: confrontamos a projeção com a urna. O segundo segue em andamento. Os três modos usam as mesmas casas em cada turno; o modelo de comparecimento mantém as propensões estimadas a partir da Nexus de 28/09.</p>'
        '<div class="vf-controls" hidden><div role="group" aria-label="Modelo dos votos válidos">'
        + buttons
        + "</div>"
        '<label>Hipótese de comparecimento<select id="vf-scenario">'
        + age_options
        + "</select></label></div>"
        f'<p id="vf-state" aria-live="polite">{escape(data["modes"][defaults["mode"]])}: {escape(data["scenario_labels"][defaults["scenario"]])}.</p>'
        '<p class="note">A exibição inicial usa Flávio +5%, escolha feita após o resultado do primeiro turno. O fator multiplica sua propensão de comparecimento por 1,05; é uma hipótese do modelo, não uma taxa por candidato medida na urna. O cenário central permanece disponível no seletor.</p>'
        '<div class="vf-grid">' + ''.join(card(data, b) for b in ballots) + "</div>"
        '<p class="note"><b>Mesmas casas nos três modos, dentro de cada turno.</b> Normalizamos cada pesquisa antes de calcular a média. Demais candidatos também contam no denominador do primeiro turno; Lula e Flávio não são reescalados sozinhos para 100%. Só aparecem individualmente os nomes identificados em todas as casas; os demais são agrupados, pois a Quaest reúne os candidatos menores no cruzamento de renda. Ausência de detalhamento não vira voto zero. Diferenças de arredondamento podem fazer os rótulos somarem 99,9% ou 100,1%. A diferença entre os líderes usa os valores antes de arredondar.</p>'
        '<p class="note"><b>Fora desta projeção:</b> '
        + escape(coverage_short)
        + '. Os motivos estão nos detalhes abaixo e na <a href="#atualizacao">cobertura documental</a>. Os gráficos históricos preservam sua cobertura original; compare o efeito do modelo pelos três botões acima.</p>'
        '<aside class="vf-caution"><b>Primeiro turno encerrado; segundo turno ainda é hipótese.</b> A comparação com a urna usa votos válidos, com todas as candidaturas no denominador. Os cenários de comparecimento são sensibilidades com parâmetros anteriores à eleição; alterná-los depois do resultado não valida uma previsão. No segundo turno, ainda não há resultado para medir o erro.</aside>'
        '<details><summary>Conferir os placares e as pesquisas usadas</summary><div class="table-scroll" tabindex="0"><table id="vf-polls"><thead><tr><th>Instituto e turno</th><th>Divulgação</th><th>Publicado / válidos</th><th>PNAD / válidos</th><th>PNAD + comparecimento</th><th>Urna / válidos</th><th>Erro do modo selecionado L−F / pp</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
        "<p>Todos os pares são Lula × Flávio. Erro = diferença do modo selecionado menos a da urna. Janela: divulgação nos sete dias até a referência, última onda de cada instituto e turno. No primeiro turno, a referência fica fechada em 04/10; no segundo, acompanha a atualização. O traço preto nas barras do primeiro turno marca o resultado oficial.</p>"
        "<p><b>Cobertura diferente dos gráficos históricos:</b> "
        + escape(coverage_note)
        + " Não substituímos a onda incompatível por uma anterior. Não misturamos a média de candidatos de cinco casas com a não escolha de outro conjunto.</p>"
        "<p><b>Resíduo impossível retirado antes de normalizar:</b> "
        + escape(negative_note)
        + ". Um valor negativo produzido pelo delta ancorado vira zero somente nesta projeção de válidos; o ajuste original continua auditável.</p></details>"
        "<details><summary>Como a matemática transforma a pesquisa em projeção</summary>"
        "<ol><li><b>Base eleitoral.</b> Usar o vetor completo de candidaturas após a sensibilidade de renda PNAD, em cada pesquisa. Branco/nulo, indecisos e respostas de ausência não são candidatos.</li>"
        "<li><b>Comparecimento.</b> A tabela sintética da Nexus cruza renda, idade e região, reproduz as margens publicadas e aplica a renda PNAD. Probabilidades de presença por célula geram q(candidato), a presença esperada dentro de cada eleitorado. São inferências ecológicas, não cruzamentos medidos.</li>"
        "<li><b>Transporte.</b> Multiplicar o voto de cada candidato em todas as casas pelo mesmo q estimado na Nexus. É uma hipótese de transporte entre amostras e métodos. Não se reaplica a distribuição conjunta Nexus às outras casas nem se ajusta sua renda uma segunda vez. Quando uma pesquisa agrupa candidaturas em Outros, calculamos a propensão conjunta dos nomes correspondentes na Nexus, ponderada por sua massa de voto após a PNAD. Nomes individuais sem equivalente usam a propensão residual Outros da Nexus, aproximada por Samara; essa aproximação fica registrada no JSON.</li>"
        "<li><b>Indecisos.</b> Distribuir os que comparecem na proporção dos votos já ajustados pelo comparecimento. Isso preserva a proporção final; não dá bônus oculto a nenhum nome.</li>"
        "<li><b>Agregação.</b> Excluir não escolha do denominador, normalizar cada pesquisa e dar peso igual às casas. A hipótese temporal mantém essas preferências até a eleição, sem modelo de mudança tardia.</li></ol>"
        '<div class="vf-equation">Aₖ = voto PNADₖ × qₖ<br>Vₖ = Aₖ / Σⱼ Aⱼ<br>Indecisos alocadosₖ = U × qᵤ × Vₖ<br>(Aₖ + U × qᵤ × Vₖ) / (Σⱼ Aⱼ + U × qᵤ) = Vₖ</div>'
        "<p>Assim, repartir indecisos proporcionalmente ou retirá-los do denominador dá o mesmo percentual válido, depois de ajustar presença. Não subtraímos 20% de cada candidato: comparecimento uniforme cancela na divisão. Quando o cruzamento de indecisos não é publicado, como no PoderData de segundo turno, não inventamos seu tamanho; a identidade acima preserva o resultado válido.</p>"
        "<p>As âncoras históricas do modelo Nexus são "
        + fmt(data["method"]["turnout_anchor"]["1t"])
        + "% e "
        + fmt(data["method"]["turnout_anchor"]["2t"])
        + "% de comparecimento por turno. Elas usam o TSE de 2022 com a composição regional de 2026. Não são previsão observada da abstenção de 2026, e o transporte das propensões não impõe esse mesmo total em cada instituto.</p>"
        + table(
            ["Turno", "Eleitorado", "Comparecimento inferido na Nexus · central"],
            rate_rows,
        )
        + "<p>Os testes de 60+ fixam sua presença em 60% ou 80%, mantendo a âncora nacional dentro da Nexus. O teste de presença relativa multiplica apenas q de Flávio por 0,95 ou 1,05. São ±5% relativos, não ±5 pontos percentuais, e não são estimativas observadas. Esse teste altera a associação com o candidato além do que as margens demográficas identificam.</p>"
        "<p>O segundo turno reutiliza a pergunta de presença do primeiro, com outra âncora histórica. Não há validação fora da amostra, microdados individuais ou modelo do erro comum entre institutos. Por isso não calculamos chance de vitória nem um intervalo preditivo artificialmente estreito.</p></details>"
        "<details><summary>Dependência de cada instituto e dados para reprodução</summary>"
        "<p>Retiramos uma casa por vez, mantendo o modelo central. É um diagnóstico de dependência da média, não intervalo de confiança. O teste não representa erros compartilhados pelas casas.</p>"
        + table(
            ["Turno", "Casa retirada", "Lula válidos %", "Flávio válidos %"], loo_rows
        )
        + '<p><a href="assets/reponderacao_validos.json">Modelo, parcelas, taxas e fontes (JSON)</a> · <a href="assets/reponderacao_validos.csv">Todos os modos e cenários (CSV)</a> · <a href="nexus_btg_28092026.html#modelo">Construção e limitações da tabela Nexus</a> · <a href="https://www.pewresearch.org/methods/2016/01/07/measuring-the-likelihood-to-vote/">Referência: modelos probabilísticos de comparecimento</a>.</p>'
        "<p>Os cenários foram calculados com os documentos disponíveis na data da referência. Não aplicamos o modelo de 28/09 às datas anteriores dos gráficos históricos. Reproduzir: <code>python3 scripts/reponderacao-build.py --skip-home</code>.</p></details>"
        '<script id="vf-data" type="application/json">'
        + encoded
        + "</script></div></section>"
    )
