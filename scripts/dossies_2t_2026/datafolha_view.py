"""Leitura editorial da Datafolha, com denominadores e anexo completo."""

from .view import (
    callout,
    details,
    explorer,
    fmt,
    frame,
    income_section,
    methodology,
    note,
    raw_tables,
    ref,
    section,
    sources,
    stacks,
    stats,
    table,
    vote_profiles,
)


def render(d):
    chapters = []
    denom, hist = d["denominators"], d["income_history"]
    current_low = 100 * hist["current_bases"][0] / hist["current_n"]
    prior_low = 100 * hist["prior_bases"][0] / hist["prior_n"]
    chapters.append(
        section(
            1,
            "renda",
            "O perfil mudou um pouco.<br><em>A regra declarada, não.</em>",
            f"A renda até 2 salários corresponde a {fmt(current_low)}% da base ponderada total, contra {fmt(prior_low)}% na onda anterior com íntegra. O registro continua usando referência de 49% e fator de renda previsto igual a 1.",
            income_section(d, "datafolha")
            + "<p>A apresentação publica renda familiar até 2 salários em 47%. O anexo dá as bases ponderadas precisas: <b>1.187, 874 e 337</b> nos três grupos, somando 2.398. Restam 122 de 2.520, cerca de 4,8%, sem renda nesses cruzamentos. O perfil entre declarantes é 49,5% / 36,4% / 14,1%; não deve ser confundido com 47,1% da amostra total na primeira faixa.</p>"
            + table(
                ["Base", "Até 2 SM", "2–5 SM", ">5 SM", "Sem renda na tabela"],
                [
                    ["Onda anterior / n=2.523", "1.209", "856", "344", "114"],
                    ["Atual / n=2.520", "1.187", "874", "337", "122"],
                ],
            )
            + "<p>A PNAD desloca a diferença F−L de +4 para +7,73 pp sobre o total. A conta é <b>publicado + q × (PNAD − recomposto)</b>, com q = 2.398/2.520. A massa sem renda conserva o topline; o seu voto por faixa não é inventado. Aplicar a PNAD dos declarantes à parcela conhecida é uma hipótese de sensibilidade, não identificação da renda de quem recusou.</p>"
            + callout(
                "Revisão documental, não nova onda",
                "A primeira integração desta pesquisa usou as bases 1.209/856/344 da onda anterior como hipótese, porque faltava a íntegra. Agora usamos as atuais e limitamos o delta à parcela com renda. A redução do ajuste frente à primeira versão tem essas duas causas; não é prova de alteração dos pesos internos do instituto.",
            )
            + note(
                'O alvo 49/47/4 e o fator previsto 1 também constam nos <a href="fontes/datafolha_14092026_registro.txt">registros de 14/09</a> e <a href="fontes/datafolha_21092026_registro.txt">21/09</a>. A referência permanece PNADC-A 2024. O perfil final pode mudar por seleção, outros pesos e arredondamentos; não demonstra uma nova regra de renda.'
            )
            + ref("datafolha", 23, 26),
        )
    )
    chapters.append(
        section(
            2,
            "perguntas",
            "Mudar a pergunta<br><em>muda a fotografia.</em>",
            "Flávio tem 46% na espontânea e 49% na estimulada; Lula, 44% e 45%. A diferença é de 2 pontos no primeiro formato e 4 no segundo, dentro da mesma pesquisa.",
            stacks(
                "Espontânea e estimulada / total da amostra",
                {"Espontânea": [46, 44, 5, 4, 1], "Estimulada": [49, 45, 5, 1, 0]},
                ["Flávio", "Lula", "Branco/nulo", "Indecisos", "Outro nome"],
            )
            + "<p>Na estimulada, os nomes e as opções são apresentados; na espontânea, o anexo identifica resposta sem essa escolha assistida. A diferença não é uma onda nova nem uma migração de campanha medida no tempo. A incerteza cai de 4% para 1%, enquanto outra resposta espontânea ocupa 1%.</p>"
            + note(
                "A p. 7 tem título de espontânea e subtítulo de estimulada; usamos a identificação e a tabela do anexo, p. 25. O anexo p. 26 abre a pergunta estimulada com os nomes. Não reconstruímos a ordem do instrumento a partir da ordem da apresentação."
            )
            + ref("datafolha", 7, 8, 25, 26)
            + stats(
                [
                    ("52% × 48%", "votos válidos publicados / Flávio × Lula"),
                    ("49% × 45%", "votos totais / mesma base de 2.520"),
                    ("6%", "branco/nulo + indecisos no total"),
                ]
            )
            + "<p>Normalizar os inteiros 49 e 45 dá 52,13% e 47,87%; o instituto publica 52% e 48%, arredondados separadamente. Não se deve tratar a diferença de casas decimais como nova informação eleitoral.</p>"
            + ref("datafolha", 8, 9, 27),
        )
    )
    t = d["transfer"]
    chapters.append(
        section(
            3,
            "transferencias",
            "A terceira via<br><em>não desapareceu por inteiro.</em>",
            "No grupo que declara voto em Cury, Renan Santos, Caiado ou Zema no 1º turno, 46% escolhem Flávio e 32% Lula; 15% indicam branco/nulo. A apresentação não informa o destino completo do restante nem a base desse grupo.",
            stacks(
                "Destino declarado de quatro candidaturas eliminadas",
                {
                    "Cury/Renan/Caiado/Zema": [
                        t["flavio"],
                        t["lula"],
                        t["invalid"],
                        t["unreported_residual"],
                    ]
                },
                ["Flávio", "Lula", "Branco/nulo", "Não detalhado"],
            )
            + note(
                "O 7% cinza é resíduo aritmético de 100−46−32−15, sujeito aos arredondamentos, não uma taxa de indecisos publicada. A apresentação traz esse agregado; o anexo não abre a matriz por candidatura anterior. Não imputamos uma retenção individual de cada candidato."
            )
            + ref("datafolha", 5)
            + "<p>A margem declarada de 14 pontos a favor de Flávio nesse grupo não equivale a 14 pontos no país. Sem sua base ponderada, não há fluxo nacional em milhões. A Nexus publica 45% × 32% para o agregado de outras candidaturas: as definições e os campos são diferentes, mas a direção dos dois retratos é semelhante.</p>"
            + callout(
                "O grupo continua mais aberto",
                "A apresentação informa 77% totalmente decididos e 22% que ainda podem mudar entre eleitores das quatro candidaturas eliminadas. Isso mostra menor firmeza declarada que na base geral, sem indicar que toda mudança irá para um dos finalistas. O placar atual já incorpora as transferências medidas.",
            )
            + ref("datafolha", 5)
            + '<div class="split"><div><h3>94% usa uma base específica</h3>'
            + stats(
                [
                    ("2.488", "base ponderada com candidatura ou branco/nulo"),
                    (
                        fmt(denom["certain_all_pct"]) + "%",
                        "voto firme reexpresso em toda a amostra",
                    ),
                ]
            )
            + f'<p>O anexo aplica 94% a 2.488 entrevistados ponderados que deram alguma opção, excluindo os indecisos. Reexpressar dá aproximadamente {fmt(denom["certain_all_pct"])}% da base de 2.520. O público aberto, somando quem pode mudar nessa base com o restante sem escolha, fica em torno de {fmt(denom["open_all_pct"])}%; é uma conta com percentuais arredondados, não previsão de migração.</p>'
            + ref("datafolha", 31)
            + "</div><div><h3>Comparação com a Nexus</h3><p>A Nexus pergunta certeza a toda a amostra, inclusive a quem está sem candidato, e publica 92% firmes. A proximidade com 92,8% na reexpressão Datafolha é mais informativa que comparar diretamente 94% e 92%. Os campos ainda são diferentes.</p><p>O texto da p. 5 traz 96%/97% de certeza por candidato e o gráfico da p. 10 mostra 94%/94%. As bases não são identificadas como equivalentes; preservamos a diferença documental.</p>"
            + ref("datafolha", 5, 10)
            + "</div></div>",
        )
    )
    chapters.append(
        section(
            4,
            "segmentos",
            "A média nacional<br><em>esconde os contrastes.</em>",
            "Mulheres, renda baixa, escolaridade fundamental e Nordeste favorecem Lula nesta fotografia. Homens, renda acima de dois salários, evangélicos e Sul favorecem Flávio. Os recortes se sobrepõem.",
            '<div class="split"><div><h3>Gênero</h3>'
            + vote_profiles(d, ["homens", "mulheres"])
            + "</div><div><h3>Renda familiar</h3>"
            + vote_profiles(d, ["até 2 SM", "2–5 SM", ">5 SM"])
            + "</div></div>"
            + "<p>Entre homens, Flávio 53% × Lula 41%; entre mulheres, 44% × 50%. Na renda até 2 salários, Lula tem 52% e Flávio 41%. Acima desse corte, Flávio tem 56% na faixa intermediária e 55% na superior, contra 38% e 39% de Lula. A faixa superior tem base ponderada de 337, com incerteza maior.</p>"
            + vote_profiles(d, ["16–24", "25–34", "35–44", "45–59", "60+"])
            + "<p>Na idade, o desenho é menos intenso: Flávio marca 50% nos dois grupos mais jovens; Lula chega a 50% entre 60+, contra 46% do adversário. Descrever essas diferenças não prova que os jovens mudaram desde outra pesquisa. A Nexus, com campo posterior e por telefone, mede Lula 57% × Flávio 39% nos mesmos 16–24 anos; a discordância entre casas precisa de acompanhamento.</p>"
            + '<div class="split"><div><h3>Regiões</h3>'
            + vote_profiles(d, ["Nordeste", "Sudeste", "Sul", "CO/Norte"])
            + "</div><div><h3>Religião e cor</h3>"
            + vote_profiles(d, ["católica", "evangélica", "branca", "preta", "parda"])
            + "</div></div>"
            + "<p>No Nordeste, Lula 61% × Flávio 35%; no Sul, 35% × 58%. Entre católicos, Lula 53% × Flávio 41%; entre evangélicos, 25% × 69%. Entre autodeclarados pretos, Lula 56% × Flávio 37%; entre brancos, 39% × 55%, e pardos, 47% × 48%. São associações, não efeitos isolados de religião ou cor.</p>"
            + "<p>Nas regiões metropolitanas, Lula tem 49% e Flávio 45%; no interior, 43% e 51%. A pergunta de ocupação separa PEA (Flávio 50%, Lula 43%) e não PEA (45% e 51%). O anexo não fornece a distribuição conjunta desses eixos; somar seus tamanhos contaria pessoas repetidas.</p>"
            + ref("datafolha", 23, 24, 26)
            + explorer(d, "datafolha")
            + note(
                "O anexo informa bases ponderadas, não tamanho amostral efetivo. Margens dos segmentos são maiores que ±2 pp nacional; a ficha apresenta, por exemplo, ±3 pp por gênero, ±5 pp na renda acima de 5 salários e ±5 pp no Sul e CO/Norte."
            )
            + ref("datafolha", 22),
        )
    )
    mot = d["motivation_candidates"]
    chapters.append(
        section(
            5,
            "motivacao",
            "O voto negativo<br><em>é parte da escolha.</em>",
            "25% dos eleitores de Flávio dizem votar para derrotar Lula, contra 13% dos de Lula para derrotar Flávio. A maioria de cada grupo diz escolher o melhor candidato: 69% e 83%.",
            stacks(
                "Motivação entre eleitores atuais de cada candidato",
                {
                    "Eleitores de Flávio": mot["flavio"],
                    "Eleitores de Lula": mot["lula"],
                },
                ["Melhor candidato", "Derrotar adversário", "Outra resposta", "NS/NR"],
            )
            + ref("datafolha", 6, 11)
            + "<p>A motivação combinada do anexo é 76% melhor candidato e 19% derrotar o adversário, mas a base é de 2.366 pessoas ponderadas que escolheram uma candidatura. Não são 19% de toda a população nem 25% de todos os eleitores para o voto negativo de Flávio.</p>"
            + stats(
                [
                    (
                        fmt(denom["motivation_positive_all_pct"]) + "%",
                        "melhor candidato, reexpresso na amostra total",
                    ),
                    (
                        fmt(denom["motivation_negative_all_pct"]) + "%",
                        "derrotar adversário, reexpresso na amostra total",
                    ),
                    ("2.366", "base ponderada da pergunta de motivação"),
                ]
            )
            + note(
                "Reexpressão: percentual da pergunta × 2.366/2.520. Números aproximados por arredondamento. As bases da apresentação (2.378 total; 1.261/1.117 por candidato) diferem das bases ponderadas do anexo; a natureza das primeiras não é explicitada. Não usamos essas contagens para inferir que a amostra tem mais apoiadores de um candidato."
            )
            + ref("datafolha", 11, 32)
            + "<p>Entre quem tem preferência partidária PT, 86% dizem escolher o melhor candidato; no PL, 79%. Entre os que não têm partido, 67%, e 26% apontam derrotar o outro. Estes percentuais são da pergunta de motivação, cuja base partidária é diferente da pergunta de intenção de voto. Não são todos os sem-partido do país.</p>"
            + ref("datafolha", 32)
            + callout(
                "Rejeitar e escolher são perguntas diferentes",
                "A rejeição exclusiva é 46% a Lula e 43% a Flávio; 3% rejeitam ambos e 8% nenhum. A pergunta individual mede 49% que não votariam em Lula e 46% em Flávio. A diferença de 3 pontos vem de quem rejeita os dois, não de um erro no ranking. “Talvez vote” (8% e 7%) também não é voto garantido.",
            )
            + stacks(
                "Rejeição combinada / total",
                {"Amostra": [46, 43, 3, 8]},
                [
                    "Só rejeita Lula",
                    "Só rejeita Flávio",
                    "Rejeita ambos",
                    "Não rejeita",
                ],
            )
            + ref("datafolha", 28, 29, 30),
        )
    )
    chapters.append(
        section(
            6,
            "governo",
            "Aprovar o presidente<br><em>não é avaliá-lo como ótimo.</em>",
            "48% aprovam o trabalho de Lula e 49% desaprovam. Na escala de avaliação do governo, 35% dizem ótimo/bom, 24% regular e 40% ruim/péssimo.",
            stacks(
                "Aprovação ao trabalho de Lula",
                {"Aprovação": [48, 49, 2]},
                ["Aprova", "Desaprova", "NS/NR"],
                ["#28705f", "#a74247", "#9a9c96"],
            )
            + stacks(
                "Avaliação do governo Lula",
                {"Avaliação": [35, 24, 40, 1]},
                ["Ótimo/bom", "Regular", "Ruim/péssimo", "NS/NR"],
                ["#28705f", "#a39153", "#a74247", "#9a9c96"],
            )
            + note(
                "As partes da aprovação somam 99% por arredondamento. A avaliação em cinco categorias e a aprovação binária usam escalas distintas; as respostas regular e não sabe ficam identificadas."
            )
            + ref("datafolha", 33, 34)
            + "<p>A avaliação não virou o espelho exato do voto. Entre renda até 2 salários, 56% aprovam Lula e 52% o escolhem; no Nordeste, 64% aprovam e 61% votam nele. Já entre evangélicos, 69% escolhem Flávio e 68% desaprovam Lula. Essas são duas margens do mesmo grupo; não identificam quais pessoas cruzam respostas nem quantos votos estão disponíveis.</p>"
            + '<p>A aprovação nacional permanece 48% desde a onda de 29/09–01/10 e a desaprovação, 49%. A intenção para um segundo turno efetivamente definido não deve ser atribuída automaticamente a melhora da avaliação do governo. A pesquisa publicada não traz um ranking próprio de problemas nacionais ou uma bateria de expectativas econômicas; esse panorama adicional está na <a href="nexus_btg_13102026.html#agenda">Nexus de 13/10</a>.</p>'
            + ref("datafolha", 18, 33, 34)
            + callout(
                "O diagnóstico desta rodada",
                "A escolha declarada já é firme para a grande maioria da base elegível. A terceira via ainda conserva menos decisão e parte sem candidato. A vantagem numérica de Flávio convive com contrastes de gênero, renda, religião e região. O plano de renda não mostra revisão após a urna; a íntegra melhora nossa conta ao revelar o perfil ponderado atual.",
            ),
        )
    )
    checks = "".join("<li>" + text + "</li>" for text in d["editorial_checks"])
    chapters.append(
        section(
            7,
            "metodo",
            "Uma base por pergunta.<br><em>Uma fonte por afirmação.</em>",
            "O registro prevê um método; o anexo revela bases ponderadas e respostas. A documentação não permite reconstruir os pesos individuais ou comprovar calibração pelo voto do 1º turno.",
            methodology(d, "datafolha")
            + callout(
                "A diferença não tem margem de ±2 pontos",
                f'Para 49% × 45%, a margem de 95% da diferença F−L sob amostragem aleatória simples seria aproximadamente ±{fmt(d["difference_margin_aas"],2)} pp. É uma referência calculada, não um intervalo com desenho real identificado: o registro combina estratos, municípios e cotas, e não abre o efeito de desenho final.',
            )
            + details(
                "Divergências e ambiguidades preservadas na íntegra",
                "<ul>"
                + checks
                + "</ul>"
                + note(
                    "Esses pontos pedem explicação documental. Diferença de base e arredondamento não demonstram fraude ou viés eleitoral. As contas usam os quadros explicitamente identificados e mantêm a apresentação como fonte paralela."
                ),
            )
            + raw_tables(d, "datafolha"),
        )
    )
    chapters.append(
        section(
            8,
            "fontes",
            "O anexo inteiro.<br><em>As contas à vista.</em>",
            "Dez perguntas, 31 recortes por pergunta, bases ponderadas e controles independentes.",
            sources(d, "datafolha"),
        )
    )
    return frame(
        d,
        "datafolha",
        "A escolha é firme.<br><em>A renda pesa.</em>",
        "A primeira Datafolha após a urna traz Flávio numericamente à frente, transferências agregadas da terceira via e fortes contrastes sociais. A íntegra permite conferir as bases e distinguir voto, certeza, motivação e aprovação do governo.",
        chapters,
        [
            (
                "Renda: regra estável, perfil atual",
                "A referência declarada continua 49/47/4, com fator de renda previsto 1. A sensibilidade agora usa as bases atuais, sem repetir a onda anterior.",
            ),
            (
                "94% depende da base",
                "O voto firme é medido entre quem deu uma opção. No total da amostra, a reexpressão fica próxima de 92,8%.",
            ),
            (
                "A transferência é agregada",
                "A apresentação traz 46% para Flávio e 32% para Lula em quatro candidaturas eliminadas. Bases e fluxos individuais não estão abertos.",
            ),
        ],
    )
