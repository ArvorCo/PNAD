"""Two current forecast charts, usable without JS, with paired universe controls."""

import importlib
import json
from html import escape

MODEL = importlib.import_module("reponderacao-validos")


def fmt(value):
    return f"{value:.1f}".replace(".", ",")


def bars(values, labels):
    return "".join(
        f'<div class="vf-row" data-candidate="{k}"><span>{escape(labels[k])}</span>'
        f'<span class="vf-track"><span class="vf-bar vf-{k}" style="width:{v:.6f}%"></span></span>'
        f"<b>{fmt(v)}%</b></div>"
        for k, v in values.items()
    )


def gap(values):
    diff = values["lula"] - values["flavio"]
    if abs(diff) < 0.05:
        return "Empate na projeção arredondada"
    return f'{"Lula" if diff > 0 else "Flávio"} +{fmt(abs(diff))} pontos'


def card(data, ballot):
    block = data["ballots"][ballot]
    scenario = block["scenarios"]["central"]
    values = scenario["aggregate"]["modelo"]
    turn = "Primeiro" if ballot == "1t" else "Segundo"
    houses = ", ".join(p["instituto"] for p in scenario["polls"])
    return (
        f'<article class="vf-card" data-ballot="{ballot}"><p class="kicker">{turn} turno · {block["n_houses"]} institutos</p>'
        f"<h3>{turn} turno, votos válidos</h3>"
        '<p class="vf-mode-label">PNAD + comparecimento</p>'
        '<div class="vf-bars" role="img" aria-label="'
        + escape(
            "; ".join(f"{data['labels'][k]} {fmt(v)}%" for k, v in values.items()),
            quote=True,
        )
        + '">'
        + bars(values, data["labels"])
        + "</div>"
        f'<p class="vf-gap">{gap(values)}</p>'
        f'<p class="vf-coverage">{escape(houses)}. Peso igual por instituto.</p>'
        '<p class="vf-precision">Projeção condicional, sem intervalo preditivo validado.</p></article>'
    )


def section_html(source, table):
    data = MODEL.write(source)
    rows, excluded, corrections = [], [], []
    for ballot, block in data["ballots"].items():
        s = block["scenarios"]["central"]
        for p in s["polls"]:
            values = "".join(
                f'<td data-mode="{m}">{fmt(p[m]["lula"])} × {fmt(p[m]["flavio"])}</td>'
                for m in MODEL.MODES
            )
            rows.append(
                f'<tr data-poll="{p["id"]}" data-ballot="{ballot}"><th scope="row">{escape(p["instituto"])} · {ballot}</th><td>{escape(p["divulgacao"])}</td>{values}</tr>'
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
        f'<option value="{k}">{escape(v)}</option>' for k, v in MODEL.SCENARIOS.items()
    )
    buttons = "".join(
        f'<button type="button" data-vf-mode="{k}" aria-pressed="{str(k == "modelo").lower()}">{escape(v)}</button>'
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
    for ballot in ["1t", "2t"]:
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
        '<p class="lead">Dois turnos, todos os votos válidos. O modelo combina a renda da PNAD com propensões de comparecimento estimadas a partir da Nexus de 28/09. Os indecisos que comparecem são distribuídos proporcionalmente entre os candidatos.</p>'
        '<div class="vf-controls" hidden><div role="group" aria-label="Modelo dos votos válidos">'
        + buttons
        + "</div>"
        '<label>Hipótese de comparecimento<select id="vf-scenario">'
        + age_options
        + "</select></label></div>"
        '<p id="vf-state" aria-live="polite">Modelo central. Preferências declaradas mantidas até a eleição; sem antecipar voto útil ou mudanças na última semana.</p>'
        '<div class="vf-grid">' + card(data, "1t") + card(data, "2t") + "</div>"
        '<p class="note"><b>Mesmas casas nos três modos, dentro de cada turno.</b> Normalizamos cada pesquisa antes de calcular a média. Demais candidatos também contam no denominador do primeiro turno; Lula e Flávio não são reescalados sozinhos para 100%. Só aparecem individualmente os nomes identificados em todas as casas; os demais são agrupados, pois a Quaest reúne os candidatos menores no cruzamento de renda. Ausência de detalhamento não vira voto zero. Diferenças de arredondamento podem fazer os rótulos somarem 99,9% ou 100,1%. A diferença entre os líderes usa os valores antes de arredondar.</p>'
        '<p class="note"><b>Fora desta projeção:</b> '
        + escape(coverage_short)
        + '. Os motivos estão nos detalhes abaixo e na <a href="#atualizacao">cobertura documental</a>. Os gráficos históricos preservam sua cobertura original; compare o efeito do modelo pelos três botões acima.</p>'
        '<aside class="vf-caution"><b>O efeito de comparecimento é pequeno no cenário central.</b> Isso é resultado da informação disponível. A projeção não permite afirmar que a liderança está identificada. O teste de presença relativa de Flávio mostra o que acontece quando a associação entre candidato e comparecimento difere da hipótese central.</aside>'
        '<details><summary>Conferir os placares e as pesquisas usadas</summary><div class="table-scroll" tabindex="0"><table id="vf-polls"><thead><tr><th>Instituto e turno</th><th>Divulgação</th><th>Publicado / válidos</th><th>PNAD / válidos</th><th>PNAD + comparecimento</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
        "<p>Todos os pares são Lula × Flávio. A última coluna acompanha a hipótese escolhida. Janela: divulgação nos sete dias até a referência, última onda de cada instituto e turno.</p>"
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
        + table(["Turno", "Eleitorado", "Comparecimento inferido na Nexus"], rate_rows)
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
