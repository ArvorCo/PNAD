"""Notas documentais da atualização noturna de 24/10."""


def section(latest):
    if latest.get("Palver", {}).get("id") != "palver_2026-10-24":
        return ""
    poll = latest["Datafolha"]
    adjusted = poll["turnos"]["2t"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
    flavio, lula = adjusted["flavio"], adjusted["lula"]

    def number(value):
        return f"{value:.2f}".replace(".", ",")

    preview = (
        "<p><b>Datafolha, prévia PNAD:</b> voto por renda de 24/10 baixado do G1. "
        "O perfil de referência é o da íntegra de 22/10: bases 1.171/913/341, "
        "equivalentes a 48,29%/37,65%/14,06% entre declarantes. A PNAD usa "
        "35,19%/39,26%/25,55%. A cobertura de renda assumida é 2.425/2.520 "
        "(96,23%); os demais conservam o topline. São composição e cobertura "
        "emprestadas, não bases observadas nas 4.050 entrevistas de hoje.</p>"
        '<div class="table-scroll"><table><thead><tr><th>Renda familiar</th>'
        "<th>Flávio</th><th>Lula</th><th>Branco/nulo</th><th>Indecisos</th>"
        "</tr></thead><tbody><tr><td>Até 2 SM</td><td>41%</td><td>53%</td><td>3%</td><td>3%</td></tr>"
        "<tr><td>Mais de 2 a 5 SM</td><td>55%</td><td>41%</td><td>4%</td><td>1%</td></tr>"
        "<tr><td>Mais de 5 SM</td><td>57%</td><td>39%</td><td>3%</td><td>0%</td></tr>"
        "</tbody></table></div>"
        f"<p>O total publicado de 48 × 47 passa a <b>{number(flavio)} × {number(lula)}</b> "
        f"na prévia, ou <b>{number(100*flavio/(flavio+lula))} × {number(100*lula/(flavio+lula))}</b> "
        "entre os candidatos, antes de ajustes de presença. Os válidos oficiais "
        "51 × 49 permanecem registrados separadamente. A prévia entra nas duas "
        "centrais sob estabilidade provisória do perfil; será substituída pelas "
        "bases atuais quando publicadas.</p>"
    )
    return (
        '<aside class="callout" id="rodada-2410-noite">'
        "<h3>24/10 à noite: Palver, Gerp, Nexus, Datafolha e Colectta</h3>"
        "<p><b>Palver e Gerp:</b> íntegras e perfis ponderados atuais conferidos. "
        "Palver publica 50 × 49 nos totais; Gerp, 49 × 46. Ambas entram com renda "
        "atual nas duas centrais. Palver mantém o método v3; Gerp informa campo "
        "efetivo de 22 a 24/10 e perfil de renda 13/22/40/17/6/2, sem recusa publicada.</p>"
        "<p><b>Nexus:</b> 47 × 46 nos totais e 50,5 × 49,5 nos válidos da amostra "
        "completa. O perfil atual 21/16/40/23 permite a sensibilidade PNAD, condicionada "
        "à etapa não explicitada do perfil. O modelo próprio de eleitor provável "
        "seleciona 79% da amostra e publica 52,4 × 47,6 nos válidos. Esse segundo "
        "resultado fica documentado separadamente: não é a base das centrais Arvor "
        "e não recebe nossos ajustes de presença de novo.</p>"
        + preview
        + "<p><b>Colectta:</b> campo 23/10, "
        "3.000 entrevistas; 46 × 46,5 nos totais e 49,7 × 50,3 nos válidos. "
        "Sem íntegra e perfil atual de renda, entra somente pelo publicado na Projeção.</p>"
        '<p class="note">Consulta encerrada às 18h48 de 24/10. Não foi confirmado '
        "novo resultado nacional de Quaest, AtlasIntel, Futura, Veritá, Phoenix ou "
        "Simplex até esse corte; anúncios e registros não são observações. "
        "Placar Flávio × Lula. "
        '<a href="fontes/palver_24102026.pdf">Palver, 112 páginas</a> · '
        '<a href="fontes/gerp_24102026.pdf">Gerp, 28 páginas</a> · '
        '<a href="fontes/nexus_24102026.pdf">Nexus, 72 páginas</a> · '
        '<a href="https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Datafolha/internal/">Datafolha, painel G1</a> · '
        '<a href="assets/reponderacao_20261024_noite.json">Inventário, fontes e controles</a>.'
        "</p></aside>"
    )
