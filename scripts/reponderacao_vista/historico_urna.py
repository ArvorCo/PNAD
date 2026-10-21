"""Urna e comparação com autoria e denominadores visíveis em cada instituto."""

from html import escape

from reponderacao_vista.avaliacao_1t import (
    FROZEN,
    OFF,
    evaluate,
    latest_comparison,
    urna,
)
from reponderacao_vista.context import curto, sinal
from svgkit import br

__all__ = ["OFF", "comparison_html", "latest_comparison", "reference", "urna"]
LABELS = {
    "validos_instituto": "Válidos publicados · instituto",
    "conversao_arvor": "Conversão dos totais · Arvor",
    "pnad_validos": "PNAD em válidos · Arvor",
    "arvor_pre_urna": "PNAD + presença · Arvor pré-urna",
    "total_publicado": "Totais publicados · instituto",
    "pnad_total": "Totais reponderados · Arvor",
}


def reference(projected=False):
    return urna("validos" if projected else "total")


def result_row(label, row):
    values, errors = row["valores"], row["erro_pp"]
    return (
        f'<tr><th>{escape(label)}</th><td>{br(values["flavio"], 2)} / {br(values["lula"], 2)}</td>'
        f'<td>{sinal(errors["flavio"], 2)} / {sinal(errors["lula"], 2)}</td>'
        f'<td>{br(row["eam_fl_pp"], 2)}</td><td>{sinal(row["erro_vantagem_fl_pp"], 2)}</td></tr>'
    )


def comparison_html(name):
    row = evaluate(name)
    if row["id"] is None:
        return '<p class="note history-urna-empty">Urna do 1º turno: sem última onda comparável divulgada antes da votação no acervo. Sem score eleitoral; não significa erro zero. Não há resultado do 2º turno.</p>'
    reads = row["leituras"]
    official, model = reads.get("validos_instituto"), reads.get("arvor_pre_urna")
    title = (
        f'Instituto: {br(official["eam_fl_pp"], 2)} pp'
        if official
        else "Instituto: válidos publicados não disponíveis"
    )
    title += (
        f' · Arvor: {br(model["eam_fl_pp"], 2)} pp'
        if model
        else " · Arvor: sem projeção pré-urna desta onda"
    )
    body = "".join(
        result_row(label, reads[key]) for key, label in LABELS.items() if key in reads
    )
    evidence = row.get("evidencia")
    source = (
        f'<p class="note"><a href="{escape(evidence["fonte"]["url"], quote=True)}">Fonte: {escape(str(evidence["fonte"]["pagina"]))} ↗</a>. '
        f'{escape(evidence["metodo"])}</p>'
        if evidence
        else '<p class="note">Não localizamos válidos publicados para esta onda. A conversão abaixo é nossa.</p>'
    )
    delta = row["delta_pnad_total"]
    difference = (
        f'<p class="note"><b>Δ PNAD − publicado, nos totais:</b> Flávio {sinal(delta["flavio"], 2)} pp; Lula {sinal(delta["lula"], 2)} pp. '
        "O ajuste parte dos totais, não é aplicado por cima do likely voter do instituto.</p>"
        if delta
        else ""
    )
    sensitivity = ""
    if model:
        labels = {
            "idosos60": "60+ com presença de 60%",
            "idosos80": "60+ com presença de 80%",
            "flavio95": "Presença relativa F −5%",
            "flavio105": "Presença relativa F +5%",
        }
        sensitivity = (
            '<details><summary>Sensibilidades Arvor preservadas antes da urna</summary><div class="table-scroll"><table>'
            "<caption>Mesmas colunas da tabela acima. Não escolhemos retrospectivamente o cenário com menor erro.</caption><tbody>"
            + "".join(
                result_row(labels[k], v)
                for k, v in row["sensibilidades_pre_urna"].items()
            )
            + "</tbody></table></div></details>"
        )
    return (
        '<div class="history-error"><span>Último 1º turno × urna · erro médio absoluto F/L</span>'
        f"<b>{title}</b><small>Mesmos candidatos, todas as candidaturas no denominador dos válidos.</small></div>"
        '<details class="history-urna"><summary>Instituto × Arvor × urna: valores, erros e fontes</summary>'
        f'<p class="note">{escape(name)} · campo até {curto(row["campo"]["fim"])} · divulgação {curto(row["divulgacao"])}. '
        "Erro = estimativa − urna. Erro positivo na vantagem F−L favorece Flávio; negativo, Lula.</p>"
        f'{source}<div class="table-scroll" tabindex="0"><table><caption>Flávio / Lula, em %. EAM e erro da vantagem em pp.</caption>'
        "<thead><tr><th>Autoria e base</th><th>F / L</th><th>Erro F / L</th><th>EAM F/L</th><th>Erro vantagem F−L</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>{difference}"
        '<p class="note">PNAD + presença reproduz o cenário central congelado em 04/10, antes da votação, '
        f'no <a href="https://github.com/ArvorCo/PNAD/tree/{FROZEN["commit"]}">commit {FROZEN["commit"][:8]}</a>. '
        "Transportava propensões Nexus entre casas, com indecisos proporcionais; era hipótese, não presença observada. "
        "Sem cruzamento completo, não fabricamos projeção. A distribuição proporcional de indecisos não muda a razão dos válidos. "
        "Totais comparam entrevistados com votos depositados, incluindo brancos/nulos: universos diferentes. "
        "Arredondamentos publicados são preservados, mesmo quando não somam 100%. "
        "A comparação usa a cédula do 1º turno, nunca a simulação binária de 2º turno.</p>"
        f"{sensitivity}</details>"
    )
