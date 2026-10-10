"""Transferência de indecisos: controle visível, volumes e fontes."""

import importlib
from html import escape as esc

SIM = importlib.import_module("reponderacao-simulador")


def fmt(value):
    return f"{value:.1f}".replace(".", ",")


def controls(data, slider):
    u = SIM.undecided(data)
    return (
        '<div class="rs-undecided" id="transferencia-indecisos">'
        '<p class="rs-unit">Transferência dos indecisos</p>'
        f'<p id="rs-undecided-pool">{fmt(u["survey_pct"])}% na base da central · {fmt(u["present_total"] / 1e6)} milhões de indecisos presentes neste cenário.</p>'
        + slider(
            data,
            "indecisos_validos",
            "Indecisos que escolhem candidato",
            0,
            100,
            1,
            "%",
            "O restante vira branco/nulo. A abstenção tem controle próprio.",
        )
        + '<div class="rs-control rs-undecided-split"><label for="rs-indecisos_flavio">Divisão dos que escolhem'
        f'<output id="rs-out-indecisos_flavio">Flávio {fmt(u["chosen_flavio_pct"])}% · Lula {fmt(100 - u["chosen_flavio_pct"])}%</output></label>'
        f'<input id="rs-indecisos_flavio" data-param="indecisos_flavio" type="range" min="0" max="100" step="0.1" value="{u["chosen_flavio_pct"]}" aria-describedby="rs-undecided-rule">'
        '<div class="rs-undecided-ends"><span>Todos para Lula</span><span>Todos para Flávio</span></div>'
        '<div class="rs-undecided-actions"><button type="button" id="rs-undecided-proportional" aria-pressed="true">Usar proporção da central</button>'
        '<button type="button" data-rs-undecided-share="50">50% / 50%</button>'
        '<label for="rs-indecisos_flavio-number">Para Flávio (%)'
        f'<input id="rs-indecisos_flavio-number" data-param="indecisos_flavio" type="number" min="0" max="100" step="0.1" value="{u["chosen_flavio_pct"]:.1f}"></label></div>'
        '<p id="rs-undecided-rule">Automático: acompanha a proporção Flávio/Lula da base selecionada antes de converter os indecisos. Arraste a régua para testar outra divisão.</p></div>'
        '<div class="rs-undecided-bar" aria-hidden="true"><span data-undecided-part="flavio"></span><span data-undecided-part="lula"></span><span data-undecided-part="invalid"></span></div>'
        '<div class="rs-undecided-destinations" aria-live="polite">'
        + "".join(
            f'<div><span>{name}</span><b id="rs-undecided-to-{key}">{u[field] / 1e6:.2f}</b><small>milhões</small></div>'
            for key, name, field in [
                ("flavio", "Flávio", "to_flavio"),
                ("lula", "Lula", "to_lula"),
                ("invalid", "Branco/nulo", "to_invalid"),
            ]
        )
        + '</div><p class="note">Destino inicial em milhões; saídas extras e erro comum são aplicados depois.</p>'
        '<p id="rs-undecided-impact" aria-live="polite">Divisão proporcional: sem deslocamento em relação à referência.</p>'
        '<p class="note">Destino é hipótese, não migração medida. <a href="#indecisos-fontes">Ver bases e limites</a>.</p></div>'
    )


def evidence(data, table):
    rows = []
    selected = {p["id"]: p for p in data["projection"]["selected"]}
    mean_ids = {p["id"] for p in data["polls"]}
    for row in selected.values():
        rows.append(
            [
                esc(row["instituto"]),
                esc(row["campo"]["inicio"] + " a " + row["campo"]["fim"]),
                fmt(row["published"]["indecisos"]) + "%",
                (
                    fmt(row["pnad"]["indecisos"]) + "%"
                    if row["income_available"]
                    else "Sem cruzamento; publicado"
                ),
                "Média e Projeção" if row["id"] in mean_ids else "Projeção",
            ]
        )
    return (
        '<details class="rs-evidence" id="indecisos-fontes"><summary>Indecisos: tamanho da base, divisão e efeito no placar</summary>'
        f'<p>Fontes da versão de {esc(data["reference"])}. A Média usa peso igual entre as casas elegíveis; a Projeção usa a âncora por recência. O tamanho é recalculado com cada atualização do acervo, com PNAD onde há cruzamento e publicado onde falta.</p>'
        + table(
            ["Instituto", "Campo", "Indecisos publicados", "Na base PNAD", "Central"],
            rows,
        )
        + f'<p>{esc(data["method"]["undecided"])}</p>'
        "<p>A proporção automática usa a relação F/L entre as candidaturas presentes, antes de converter indecisos e antes das saídas extras para branco/nulo ou do erro comum. Ao mudar a central, a base ou a presença relativa, essa proporção acompanha a nova base. Uma divisão livre permanece fixa até restaurar a proporção automática.</p>"
        "<p>“Na base” é percentual antes da seleção de presença; o volume em milhões conta apenas os indecisos que compareceriam no cenário. As transferências são destinos iniciais: as saídas extras e o erro comum podem alterar o placar depois. O impacto final compara a divisão escolhida com a automática, mantendo todos os outros controles, inclusive a parcela que escolhe candidato.</p>"
        "<p>A opção central transforma 100% dos indecisos presentes em votos válidos; é hipótese editável. Não confundimos indecisão com branco/nulo ou ausência. Não há painel individual que acompanhe o destino dos indecisos até a urna. Links antigos preservam a divisão proporcional por pesquisa do motor anterior.</p></details>"
    )
