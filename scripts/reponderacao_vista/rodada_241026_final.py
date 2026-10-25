"""Amostra completa e eleitor provável preservados como universos distintos."""


def section(latest=None):
    futura = (
        '<aside class="callout" id="futura-2410"><h3>24/10, 20h32: nova Futura</h3>'
        "<p><b>48,2 × 47,9 nos totais; 50,1 × 49,9 nos válidos oficiais.</b> "
        "Brancos/nulos: 2,3%; indecisos: 1,6%. Campo efetivo 23–24/10, "
        "2.000 entrevistas por telefone, BR-09726/2026. A nova onda substitui "
        "a de 21/10 na Projeção. O relatório traz perfil de renda, mas não voto por faixa: "
        "fica fora da Média PNAD. Os válidos oficiais são preservados separadamente "
        "da divisão dos totais arredondados.</p>"
        '<p class="note">Flávio × Lula. '
        '<a href="https://www.cnnbrasil.com.br/eleicoes/futura-flavio-tem-501-dos-votos-validos-no-2o-turno-lula-499/">CNN, divulgação das 20h32</a> · '
        '<a href="fontes/futura_24102026.pdf">Relatório Futura</a> · '
        '<a href="assets/reponderacao_futura_20261024.json">Fontes e auditoria</a>.</p></aside>'
        if (latest or {}).get("Futura", {}).get("id") == "futura_2026-10-24"
        else ""
    )
    return futura + (
        '<aside class="callout" id="rodada-2410-final">'
        "<h3>24/10, após 19h: Quaest com eleitor provável e AtlasIntel</h3>"
        "<p><b>Quaest: 46 × 45 na amostra completa; 51 × 49 no likely voter oficial.</b> "
        "O primeiro resultado tem 8% de branco/nulo/não vai votar e 1% de indecisos. "
        "O segundo usa o modelo próprio de eleitor provável. A divisão simples dos "
        "totais arredondados é 50,55 × 49,45: a diferença para 51 × 49 não permite "
        "medir o efeito exato do modelo. Campo 23–24/10, 3.702 entrevistas, BR-09158/2026.</p>"
        "<p><b>Na Projeção Arvor, a Quaest entra uma vez pelo 51 × 49 oficial.</b> "
        "Mantém o peso por recência, sem reaplicar presença Nexus, adicional relativo, "
        "PNAD ou indecisos da amostra completa. A casa fica fora da estimação de "
        "tendência para não confundir a troca de universo com movimento eleitoral. "
        "Nos gráficos por instituto, os totais continuam disponíveis e o controle "
        "de válidos mostra o resultado oficial identificado, sem unir a linha na mudança de método.</p>"
        "<p>O G1 disponibiliza voto por renda da amostra completa: F/L de 32/58, "
        "49/42 e 57/36 nas faixas até 2, de 2 a 5 e acima de 5 salários mínimos. "
        "Sem perfil atual e cruzamentos do eleitor provável, não há reponderação "
        "PNAD desta onda nem inclusão da Quaest na Média. Pesos de 21/10 não são transportados.</p>"
        "<p><b>AtlasIntel: 49,9 × 48,4 nos totais e 50,8 × 49,2 nos válidos oficiais.</b> "
        "Campo 18–23/10, 4.990 entrevistas, BR-06380/2026. Íntegra de 18 páginas "
        "arquivada; perfil atual e voto por renda permitem a sensibilidade PNAD "
        "nas duas centrais. O estágio pré/pós-ponderação do perfil não está explicitado.</p>"
        '<p class="note">Placar Flávio × Lula. '
        '<a href="https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Quaest/internal/">Quaest no G1</a> · '
        '<a href="fontes/atlas_24102026.pdf">Íntegra AtlasIntel</a> · '
        '<a href="assets/reponderacao_20261024_final.json">Fontes e auditoria da atualização</a>.</p></aside>'
    )
