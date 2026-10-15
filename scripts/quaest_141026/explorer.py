"""Payload e primeira vista do explorador; todos os dados ficam disponíveis sem JS."""

import json
from html import escape as esc

from .charts import SOURCE, pairs
from .g1 import panel

DIMENSIONS = {
    "Renda": ["Até 2 sm", "Mais de 2 a 5 sm", "Mais de 5 sm"],
    "Sexo": ["Masculino", "Feminino"],
    "Idade": ["16 a 34 anos", "35 a 59 anos", "60 anos ou mais"],
    "Escolaridade": ["Fundamental", "Médio", "Superior"],
    "Região": ["Norte", "Nordeste", "Centro-oeste", "Sudeste", "Sul"],
    "Cor": ["Branca", "Parda", "Preta"],
    "Religião": ["Católica", "Evangélica"],
    "Identificação política": [
        "Bolsonarista",
        "Direita não bolsonarista",
        "Independente",
        "Esquerda não lulista",
        "Lulista",
    ],
}
OPTIONS = {
    "estimulada": [
        "Flávio Bolsonaro",
        "Lula",
        "Branco/Nulo/Não Vai Votar",
        "Indecisos",
    ],
    "espontanea": [
        "Flávio Bolsonaro",
        "Lula",
        "Outros",
        "Branco/Nulo/Não Vai Votar",
        "Indecisos",
    ],
    "aprovacao": ["Aprova", "Desaprova", "Não Sabe / Não Respondeu"],
    "avaliacao": ["Positivo", "Regular", "Negativo", "Não Sabe / Não Respondeu"],
    "rejeicao": ["Flávio Bolsonaro", "Lula"],
}
COLORS = {
    "Flávio Bolsonaro": "#386ba6",
    "Lula": "#a74247",
    "Branco/Nulo/Não Vai Votar": "#818b78",
    "Indecisos": "#c3b598",
    "Outros": "#53695f",
    "Aprova": "#28705f",
    "Desaprova": "#a74247",
    "Não Sabe / Não Respondeu": "#c3b598",
    "Positivo": "#28705f",
    "Regular": "#b09a5b",
    "Negativo": "#a74247",
}


def rows(question, dimension):
    by_name = {
        r["recorte"]: r for r in question["estratos"] if r["dimensao"] == dimension
    }
    if set(by_name) != set(DIMENSIONS[dimension]):
        raise ValueError(f"Recortes inesperados: {dimension}")
    return [by_name[name] for name in DIMENSIONS[dimension]]


def payload():
    questions = panel()
    for key, question in questions.items():
        question["opcoes"] = OPTIONS[key]
        question["independente"] = key == "rejeicao"
        for dimension in DIMENSIONS:
            rows(question, dimension)
    return {"questions": questions, "dimensions": DIMENSIONS, "colors": COLORS}


def render():
    data = payload()
    initial = data["questions"]["estimulada"]
    chart = pairs(
        "Intenção estimulada · renda",
        {
            "Total": (46, 44),
            **{
                r["recorte"]: (
                    r["valores_pct"]["Flávio Bolsonaro"],
                    r["valores_pct"]["Lula"],
                )
                for r in rows(initial, "Renda")
            },
        },
        source=SOURCE
        + " Brancos/nulos e indecisos estão nas tabelas completas abaixo.",
    )
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    return (
        '<div class="explorer" id="q-explorer"><div class="explorer-head"><h3>Explore as perguntas e os grupos</h3>'
        "<p>Selecione uma pergunta e uma dimensão. O total acompanha cada comparação; percentuais pertencem ao próprio grupo.</p></div>"
        '<div class="explorer-controls" id="q-controls" hidden><label>Pergunta<select id="q-question">'
        + "".join(
            f'<option value="{k}">{esc(q["rotulo"])}</option>'
            for k, q in data["questions"].items()
        )
        + '</select></label><label>Comparar por<select id="q-dimension">'
        + "".join(f"<option>{esc(dim)}</option>" for dim in DIMENSIONS)
        + '</select></label></div><p id="q-status" class="note" role="status" aria-live="polite"></p>'
        '<div id="q-explorer-result">' + chart + "</div>"
        '<p class="note" id="q-explorer-note">Bases por recorte não publicadas. As tabelas completas preservam todos os valores.</p>'
        '<a id="q-share" href="?pergunta=estimulada&amp;recorte=Renda#painel" hidden>Link para esta comparação</a>'
        "<noscript><p>O seletor precisa de JavaScript. As cinco perguntas e os 130 recortes continuam disponíveis nas tabelas abaixo.</p></noscript></div>"
        '<script type="application/json" id="q-explorer-data">' + encoded + "</script>"
    )
