"""Leituras visuais dos segmentos e das perguntas, sem inferir fluxos individuais."""

from dossies_2t_2026.view import callout, note, section, stacks

from .charts import gaps, pairs
from .explorer import OPTIONS, rows
from .g1 import panel


def candidate_pairs(question, dimension):
    return {
        r["recorte"]: (r["valores_pct"]["Flávio Bolsonaro"], r["valores_pct"]["Lula"])
        for r in rows(question, dimension)
    }


def segments():
    question = panel()["estimulada"]
    regional = {
        name: values[0] - values[1]
        for name, values in candidate_pairs(question, "Região").items()
    }
    return section(
        4,
        "segmentos",
        "O total aproxima.<br><em>Os grupos separam.</em>",
        "O 46 × 44 reúne diferenças amplas por região, sexo, religião e identificação política.",
        '<div class="q-chart-grid">'
        + pairs(
            "Sexo: vantagem numérica muda de lado", candidate_pairs(question, "Sexo")
        )
        + pairs(
            "Idade: empate entre os mais jovens", candidate_pairs(question, "Idade")
        )
        + "</div>"
        + gaps("Região: do Nordeste ao Sul, diferenças de sinais opostos", regional, 35)
        + '<div class="q-chart-grid">'
        + pairs(
            "Religião: dois grupos publicados", candidate_pairs(question, "Religião")
        )
        + pairs(
            "Identificação política: bases e independentes",
            candidate_pairs(question, "Identificação política"),
        )
        + "</div>"
        + callout(
            "Entre independentes, a não escolha chega a 25%",
            "Flávio tem 39%, Lula 36%, branco/nulo/não vai votar 23% e indecisos 2%. É um grupo com mais respostas fora das candidaturas; não são 25% de votos disponíveis nem um fluxo identificado para qualquer lado.",
        )
        + note(
            "Os grupos se sobrepõem. Católicos e evangélicos não esgotam as religiões; não completamos os grupos ausentes. Bases por segmento não publicadas: diferenças e mudanças numéricas não substituem testes de significância. Escolaridade, cor e todos os demais recortes estão no explorador."
        ),
    )


def opinions():
    questions = panel()
    vote_options = OPTIONS["estimulada"]
    votes = {
        questions[k]["rotulo"]: [
            questions[k]["total"]["valores_pct"][o] for o in vote_options
        ]
        for k in ("espontanea", "estimulada")
    }
    rejection = questions["rejeicao"]
    rej_rows = {"Total": (54, 53), **candidate_pairs(rejection, "Renda")}
    gov = ""
    for key in ("aprovacao", "avaliacao"):
        q = questions[key]
        gov += (
            "<div><h3>"
            + q["rotulo"]
            + "</h3>"
            + stacks(
                q["rotulo"],
                {"Total": [q["total"]["valores_pct"][o] for o in OPTIONS[key]]},
                OPTIONS[key],
                colors=(
                    ["#28705f", "#a74247", "#c3b598"]
                    if key == "aprovacao"
                    else ["#28705f", "#b09a5b", "#a74247", "#c3b598"]
                ),
            )
            + "</div>"
        )
    return section(
        5,
        "perguntas",
        "Voto, rejeição e governo.<br><em>Medidas diferentes.</em>",
        "A leitura melhora quando as perguntas conversam sem virarem a mesma coisa.",
        "<h3>Espontânea e estimulada: a escolha depende da pergunta</h3>"
        + stacks("Voto espontâneo e estimulado", votes, vote_options)
        + note(
            "Fonte: Quaest / G1, 14/10. Na espontânea, “outros” é 0%. Indecisos: 7% na espontânea e 1% na estimulada. Não acompanhamos pessoas de uma resposta à outra; a diferença não identifica conversão nem transferência."
        )
        + pairs(
            "Rejeição: ambos podem ser rejeitados pela mesma pessoa",
            rej_rows,
            source="Fonte: Quaest / G1, 14/10. Percentual que rejeita cada candidato no próprio grupo. Respostas independentes: 54% e 53% não se somam, não são votos e não medem a rejeição simultânea.",
        )
        + '<div class="q-chart-grid q-stacks-grid">'
        + gov
        + "</div>"
        + note(
            "Fonte: Quaest / G1, 14/10. Aprovação: 45% aprovam, 48% desaprovam e 7% não sabem/não respondem. Avaliação: 34% positiva, 24% regular, 40% negativa e 2% NS/NR. Os rótulos e universos seguem o painel; a formulação integral permanece pendente."
        )
        + "<p>A diferença entre aprovação e intenção de voto não mede “votos a conquistar”. Sem cruzar as duas respostas na mesma entrevista, não sabemos quantos aprovam e votam em Flávio ou desaprovam e votam em Lula.</p>",
    )
