"""Painéis dos institutos organizados por turno, sem misturar denominadores."""

import importlib
from html import escape as esc

from reponderacao_vista.charts import instituto_svg
from reponderacao_vista.context import (
    INSTITUTOS,
    PESQUISAS,
    TURNOS,
    ajustado,
    curto,
    plural,
)
from reponderacao_vista.urna_dados import comparison
from reponderacao_vista.urna_view import institute_note
from svgkit import br


def _painel_instituto(nome: str, turno: str) -> str:
    if nome == "Palver":
        palver_view = importlib.import_module("reponderacao-palver-view")
        historico = palver_view.history_polls()
        return (
            f'<article class="panel reveal" data-instituto="Palver" data-turno="{turno}">'
            f"<h3>Palver <small>{TURNOS[turno]}</small></h3>"
            f'<div class="fig">{instituto_svg(nome, turno) if turno == "1t" else instituto_svg(nome, turno, historico)}</div>'
            + (
                institute_note(nome)
                + '<p class="note">Votos válidos; pontilhado horizontal é a urna.</p><details><summary>Histórico original, sobre o total</summary>'
                + f'<div class="fig">{instituto_svg(nome, turno, historico)}</div>'
                if turno == "1t"
                else ""
            )
            + f'<p class="note"><b>{palver_view.history_count()}.</b> A onda 2 original (v1) foi substituída '
            "pela revisada (v2). Todos os pontos estão visíveis; a v1 fica fora das médias. "
            + (
                "Os dois cenários de 07/09 incluem Marçal e também ficam fora da média do 1º turno. "
                if turno == "1t"
                else ""
            )
            + "Vazado é publicado, cheio é reponderado. "
            '<a href="reponderacao_pnad_1o_turno_2026.html#palver-pesos">Fontes, valores e critérios</a>.</p>'
            + ("</details>" if turno == "1t" else "")
            + "</article>"
        )
    ondas = sum(1 for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"])
    total = sum(1 for p in PESQUISAS if p["instituto"] == nome)
    if turno == "2t" and ondas < total:
        cobertura = f"{ondas} de {total} ondas cruzam o 2º turno por renda"
    elif turno == "1t" and not any(
        "2t" in p["turnos"] for p in PESQUISAS if p["instituto"] == nome
    ):
        cobertura = f"{plural(ondas, 'onda', 'ondas')}; o instituto não cruza o 2º turno por renda"
    else:
        cobertura = plural(ondas, "onda auditada", "ondas auditadas")
    if turno == "1t":
        shown = sum(
            comparison(p) is not None for p in PESQUISAS if p["instituto"] == nome
        )
        cobertura = f"{shown} de {ondas} ondas do 1º turno compatíveis com a cédula"
    ultimas = [p for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"]]
    resumo = ""
    if ultimas:
        onda = ultimas[-1]
        resultado = onda["turnos"][turno]
        pub, adj = resultado["publicado"], ajustado(resultado)
        resumo = (
            f'<p class="note"><b>Última onda · campo até {curto(onda["campo"]["fim"])}'
            f" · divulgação {curto(onda['divulgacao'])}.</b><br>"
            f"Flávio × Lula: publicado <b>{br(pub['flavio'], 0)} × {br(pub['lula'], 0)}</b>; "
            f"reponderado <b>{br(adj['flavio'], 2)} × {br(adj['lula'], 2)}</b> (%).</p>"
        )
    return (
        f'<article class="panel reveal" data-instituto="{esc(nome)}" data-turno="{turno}"><h3>{esc(nome)} <small>{TURNOS[turno]}</small></h3>'
        f'<div class="fig">{instituto_svg(nome, turno)}</div>{resumo if turno == "2t" else institute_note(nome)}'
        f'<p class="note">{cobertura}. Vazado é publicado, cheio é reponderado.'
        + (
            " Primeiro turno em válidos; pontilhado horizontal é a urna. Ondas históricas medem preferências em suas datas; só a última onda elegível entra no balanço final."
            if turno == "1t"
            else " Percentuais sobre o total de entrevistados."
        )
        + "</p></article>"
    )


def body(turns=("2t", "1t")):
    groups = []
    for turn in turns:
        names = [
            name
            for name in INSTITUTOS
            if any(p["instituto"] == name and turn in p["turnos"] for p in PESQUISAS)
        ]
        panels = "".join(_painel_instituto(name, turn) for name in names)
        title = (
            "2º turno · em andamento"
            if turn == "2t"
            else "1º turno · resultado conhecido"
        )
        description = (
            "Publicado e PNAD sobre o total de entrevistados. Cada painel reúne as ondas da mesma casa."
            if turn == "2t"
            else "Publicado e PNAD em votos válidos, com a urna como referência. Só são desenhados cenários compatíveis com a cédula; opções sem cruzamento de renda conservam o publicado, como na auditoria da apuração. O histórico documental da Palver fica nos detalhes do seu painel."
        )
        groups.append(
            f'<div id="institutos-{turn}" class="instituto-group"><header><p class="kicker">{len(names)} institutos com renda</p><h3>{title}</h3><p class="note">{description}</p></header><div class="grid-3">{panels}</div></div>'
        )
    return (
        '<nav class="instituto-turnos" aria-label="Institutos por turno">'
        + "".join(f'<a href="#institutos-{turn}">{TURNOS[turn]}</a>' for turn in turns)
        + "</nav>"
        + "".join(groups)
        + '<p class="note">Uma só onda produz pontos, sem linha. A escala vertical é própria de cada painel; a comparação entre casas está no gráfico de erros do primeiro turno.</p>'
    )
