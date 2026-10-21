"""Score eleitoral em unidades de erro; documentação permanece dimensão separada."""

from html import escape

from reponderacao_vista.avaliacao_1t import evaluate, write
from reponderacao_vista.context import curto
from svgkit import br


def badge(name):
    row = evaluate(name)
    value = row["score_arvor_pp"]
    return (
        '<p class="history-rank"><span>Score Arvor · 1º turno</span>'
        + (
            f"<b>{br(value, 2)} pp</b><small>erro médio F/L · menor é melhor</small>"
            if value is not None
            else "<b>Sem classificação</b><small>válidos finais da casa não confirmados</small>"
        )
        + "</p>"
    )


def section(names):
    data = write(names)
    rows = data["institutos"]
    body = []
    for row in rows:
        score = row["score_arvor_pp"]
        model = row["leituras"].get("arvor_pre_urna")
        conversion = row["leituras"].get("conversao_arvor")
        note = row["nota_documental"]
        body.append(
            f'<tr data-score-house="{escape(row["instituto"])}"><td>{str(row["posicao"]) + "º" if row["posicao"] else "s/d"}</td>'
            f'<th>{escape(row["instituto"])}<small>{curto(row["campo"]["fim"]) if row.get("campo") else "Sem onda pré-urna elegível"}</small></th>'
            f'<td>{br(score, 2) if score is not None else "s/d"}<small>{escape(row["status"])}</small></td>'
            f'<td>{br(conversion["eam_fl_pp"], 2) if conversion else "s/d"}</td>'
            f'<td>{br(model["eam_fl_pp"], 2) if model else "s/r"}</td>'
            f'<td>{br(note, 1) + "/10" if note is not None else "s/d"}</td></tr>'
        )
    central = data["arvor_central_presidencial"]
    v = central["valores"]
    return (
        '<section class="history-ranking" id="score-arvor"><p class="kicker">Auditoria do primeiro turno · 04/10/2026</p>'
        "<h3>Score Arvor: menor erro primeiro.</h3>"
        "<p>O score mede <b>erro médio absoluto de Flávio e Lula, em pontos dos válidos publicados pelo instituto</b>: "
        "(|erro F| + |erro L|) ÷ 2. Zero reproduz ambos. Não é uma nota de 0 a 10 nem percentual de acerto. "
        "O erro da vantagem aparece nas fichas, mas não ordena o ranking: dois erros no mesmo sentido podem se cancelar na diferença.</p>"
        f'<p class="note"><b>{sum(r["posicao"] is not None for r in rows)} casas classificadas.</b> '
        "Última onda comparável, com campo encerrado de 25/09 a 04/10 e publicação anterior à votação. "
        "Válidos da casa têm prioridade, inclusive likely voter próprio, sem novo ajuste nosso. "
        "Sem publicação confirmada, a casa fica ao final, em ordem alfabética e sem posição; isso não significa pior desempenho. "
        "Empates a 0,01 pp compartilham posição. Datas e arredondamentos afetam a comparação; a ordem numérica não demonstra diferença estatística.</p>"
        '<div class="table-scroll" tabindex="0" role="region" aria-label="Ranking por erro no primeiro turno"><table>'
        "<caption>Erros em pp dos válidos. Conversão e projeção Arvor não são resultados do instituto.</caption>"
        "<thead><tr><th>Posição</th><th>Instituto / fim do campo</th><th>Score Arvor<br>Válidos da casa ↓</th>"
        "<th>Erro da conversão<br>Arvor</th><th>Erro PNAD + presença<br>Arvor pré-urna</th><th>Nota documental<br>21/09</th></tr></thead>"
        f'<tbody>{"".join(body)}</tbody></table></div>'
        '<p class="note">A nota documental anterior continua separada, na escala de 0 a 10: mede transparência dos documentos de setembro. '
        "Não somamos transparência com erro eleitoral nem recalculamos essa nota pelo resultado. "
        '<a href="reponderacao_pnad_1o_turno_2026.html#comparar-metodos">Consultar rubrica e evidências documentais →</a>. '
        "Uma eleição não estabelece qualidade permanente nem prevê o acerto no segundo turno. s/d: dado não confirmado; s/r: sem projeção completa.</p>"
        '<aside class="history-own-error"><b>Nosso erro também está na mesa.</b> '
        f'A Central Projeção Arvor presidencial publicada antes da votação marcou F {br(v["flavio"], 2)}% / L {br(v["lula"], 2)}%: '
        f'<strong>EAM F/L {br(central["eam_fl_pp"], 2)} pp</strong>. '
        "É o agregado com recência e tendência, distinto das projeções individuais PNAD + presença na tabela. "
        "Os cálculos individuais usam o cenário central então exibido; todas as sensibilidades originais ficam nas fichas, sem selecionar a melhor depois da urna.</aside>"
        '<p class="note"><a href="assets/reponderacao_score_arvor.json">Baixar score, erros, fontes e cenários congelados (JSON)</a></p></section>'
    )
