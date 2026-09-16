"""Texto analítico, documentação e limites, segunda parte."""

from html import escape


def chapters(b):
    d, t, table, ref, num, section = (
        b.d,
        b.d["tables"],
        b.table,
        b.ref,
        b.num,
        b.section,
    )
    out = []
    out.append(
        section(
            "governo",
            "O governo é desaprovado por 50%. <em>Isso não dá 50% à oposição.</em>",
            "A aprovação está em 43%, a desaprovação em 50% e 7% não respondem. As três parcelas ficaram iguais às da semana anterior.",
            table(
                ["Renda", "Desaprova", "Flávio 2T", "Diferença", "Não escolha 2T"],
                [
                    [label, r[1], v[1], r[1] - v[1], v[2] + v[3]]
                    for label, r, v in zip(
                        ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"],
                        t["APPROVAL_INCOME"],
                        t["SECOND_INCOME"],
                        strict=True,
                    )
                ],
            )
            + "<p>As três faixas formam uma partição de renda. A diferença ponderada entre desaprovação e voto em Flávio é 8,19 pontos; os placares nacionais arredondados dão 50 − 42 = 8. É um contraste útil entre duas medidas, mas não revela quem respondeu simultaneamente às duas perguntas de determinada maneira.</p>"
            + "<p><strong>Correção de interpretação:</strong> esse contraste não é um estoque identificado, nem um teto de votos capturáveis. Com apenas 50% de desaprovação e 42% de voto, a fração que desaprova e não vota em Flávio pode estar entre 8% e 50%, pelos limites de interseção. Para estreitar o intervalo é necessário o cruzamento individual. Mesmo saber que há não escolha em uma faixa não prova que ela é dos mesmos entrevistados que desaprovam.</p>"
            + "<p>Para a leitura de campanha, o fato favorável é que o adversário enfrenta desaprovação maior que aprovação. O limite é que essa insatisfação pode coexistir com rejeição a Flávio, preferência por outro candidato ou recusa de votar. Não se deve prometer conversão a partir de uma subtração de percentuais.</p>"
            + ref(28, 33, 154, 159),
        )
    )

    out.append(
        section(
            "agenda",
            "Corrupção ganha saliência. <em>Violência continua no topo.</em>",
            "A hierarquia de preocupações é espontânea. Ela oferece contexto para a disputa, mas não mede a competência atribuída a cada candidato para resolver esses problemas.",
            table(
                ["Maior preocupação", "07/09", "14/09"],
                [
                    ["Violência", 31, 31],
                    ["Corrupção", 20, 22],
                    ["Economia", 19, 19],
                    ["Saúde", 12, 10],
                    ["Problemas sociais", 9, 9],
                    ["Educação", 7, 7],
                ],
            )
            + "<p>O gráfico exibe as seis categorias mais citadas, e não uma partição completa: a coluna atual soma 98. Corrupção sobe dois pontos, mas a violência permanece nove pontos à frente. Reduzir toda a agenda ao escândalo da semana apagaria o principal problema espontaneamente mencionado.</p>"
            + "<h3>A pesquisa mede exposição, não eficácia da propaganda</h3>"
            + table(
                ["Indicador", "Resultado atual"],
                [
                    ["Assistiu a algum programa eleitoral", 42],
                    ["Não assistiu", 58],
                    ["Muito interessado na eleição", 37],
                    ["Pouco interessado", 40],
                    ["Nada interessado", 22],
                    ["Principal fonte: redes sociais", 35],
                    ["Principal fonte: televisão", 34],
                    ["Principal fonte: sites/blogs/portais", 10],
                ],
            )
            + "<p>A Q61 não pergunta qual programa foi visto, em que frequência ou se mudou o voto. Não há teste experimental de mensagem nem atribuição de efeito a um candidato. Assim, não é possível dizer que o horário eleitoral de Flávio “funcionou” apenas porque ele cresceu e 42% viram algum programa. Redes e TV também são fontes principais declaradas, não alcance acumulado ou eficácia de campanha. Os 62% pouco ou nada interessados mostram atenção limitada; não definem uma lista de pessoas persuadíveis.</p>"
            + ref(133, 144, 174, 184),
        )
    )

    ext = d["external"]
    out.append(
        section(
            "stf",
            "A crise aparece mais como reforço <em>do que como troca declarada.</em>",
            "A Q50 está fora do PDF eleitoral, mas foi publicada no g1 em 14/9. Ela entra na análise com a fonte externa identificada.",
            table(
                ["Influência declarada da crise no STF", "%"],
                [
                    ["Não tem influência sobre o voto", 67],
                    ["Reforça a escolha atual", 22],
                    ["Faz considerar mudar", 7],
                    ["Não sabe/não respondeu", 4],
                ],
            )
            + "<p>Essas respostas não são um experimento. Perguntar se um caso influenciou alguém mede percepção retrospectiva, sujeita a racionalização. “Não influencia” não prova ausência de todo efeito; “faz considerar mudar” não informa a direção nem confirma que a mudança aconteceu. O resultado sustenta uma leitura de reforço declarado mais frequente que reconsideração, e não uma estimativa causal de votos produzidos pela crise.</p>"
            + "<p>O g1 também publicou confiança no STF e propostas institucionais: 56% dizem não confiar, 9% confiar muito e 30% confiar pouco; 53% apoiam mandato fixo e 68% maiores exigências de nomeação. Por isso, não chamamos esses itens de resultados escondidos. A crítica é à fragmentação entre o instrumento registrado, o PDF e matérias avulsas, sem uma tabela-mestra que amarre pergunta, base e resultado.</p>"
            + f'<p class="source">Fontes externas: <a href="{ext["stf"]}">g1, efeito declarado sobre o voto</a>; <a href="{ext["reforms"]}">g1, confiança e reformas</a>. Consultadas em 15/09/2026.</p>'
            + '<div class="plain-language">Falha de divulgação a reconciliar: a enumeração textual da Q47 na matéria sobre reformas soma 108% para uma pergunta de resposta única. O problema foi encontrado no texto jornalístico consultado; não foi atribuído à base da Quaest. Essa enumeração não entra nas contas do dossiê.</div>'
            + "<p>A sequência do instrumento importa: os cenários de voto estão nas Q22–29; os textos sobre Master e o conflito no STF entram nas Q46–50. Não há base para afirmar que esse bloco posterior induziu as respostas de voto anteriores, supondo execução da ordem registrada. Já as respostas de conhecimento e avaliação do caso vêm depois de estímulos narrativos lidos pelo entrevistador. Elas não devem ser tratadas como opinião espontânea sem contexto.</p>",
        )
    )

    groups = [
        [
            "Q9–21",
            "Potencial dos candidatos",
            "12 nomes no PDF; Marçal sem resultado próprio.",
            "pp.74–83",
        ],
        [
            "Q22–23",
            "Dois cenários de primeiro turno",
            "Um conjunto de resultados, sem Marçal; identificação renumerada.",
            "pp.16–25",
        ],
        [
            "Q37–42",
            "Honestidade dos seis candidatos",
            "Nenhum resultado localizado no PDF eleitoral.",
            "Instrumento p.12",
        ],
        [
            "Q43–45",
            "Confiança institucional",
            "Fora do PDF; confiança no STF confirmada no g1.",
            "Instrumento p.13",
        ],
        [
            "Q46–50",
            "Master e conflito no STF",
            "Fora do PDF; Q47 e Q50 confirmadas nas matérias consultadas.",
            "Instrumento pp.13–15",
        ],
        [
            "Q51–56",
            "Reformas do STF",
            "Fora do PDF; divulgação externa de várias propostas confirmada.",
            "Instrumento p.15",
        ],
        [
            "Q58–59",
            "Conflitos familiares e expressão do voto",
            "Sem resultado localizado no PDF.",
            "Instrumento p.16",
        ],
        [
            "Q65",
            "Voto recordado no segundo turno de 2022",
            "Sem resultado localizado no PDF.",
            "Instrumento p.18",
        ],
    ]
    rows = []
    for q in d["questions"]:
        p = q["report_page"]
        rp = ref(p) if p else "Não consta"
        rows.append(
            [
                q["question"],
                escape(q["title"]),
                f"p.{q['questionnaire_page']}",
                q["status"],
                rp,
            ]
        )
    out.append(
        section(
            "perguntas-fantasma",
            "O que ficou fora do PDF <em>não é automaticamente secreto.</em>",
            "Há 66 itens numerados no questionário. Contamos cada nome e cenário numerado como item; a recodificação automática 3A não é uma pergunta adicional.",
            b.cards(
                [
                    (
                        "Inventário",
                        "37",
                        "Correspondências diretas",
                        "Itens com resultado identificável no PDF.",
                    ),
                    (
                        "Correspondência condicional",
                        "1",
                        "Lista sem Marçal",
                        "Compatível com Q23, mas o relatório a chama de cenário 1.",
                    ),
                    (
                        "Fora do PDF",
                        "25",
                        "Itens substantivos",
                        "Incluem resultados divulgados à parte. Não são 25 provas de retenção.",
                    ),
                    (
                        "Separados da conta",
                        "3",
                        "Cadastro, perfil e controle",
                        "Q1 elegibilidade, Q5 ocupação e Q7 gravação.",
                    ),
                ]
            )
            + table(["Itens", "Assunto", "Situação documental", "Localizador"], groups)
            + "<p>Para chamar uma pergunta de “fantasma”, é preciso dizer de qual acervo ela está ausente. O diagnóstico verificável aqui é <strong>ausência de resultado próprio neste PDF</strong>. Foram consultados também o catálogo de PDFs da Quaest e matérias públicas. A busca externa não é exaustiva: “não localizado” não significa “nunca divulgado”. Registro prova que o item estava previsto, não que foi efetivamente aplicado a todos.</p>"
            + "<p>A lacuna de maior valor para auditar recrutamento é a Q65: o voto recordado em 2022 pode ser comparado com o resultado eleitoral conhecido, embora sofra erro de memória e de declaração. Sua publicação por base bruta e ponderada ajudaria a avaliar composição. Não permitiria simplesmente forçar o passado recordado a coincidir com a urna.</p>"
            + "<p>A bateria de honestidade é pertinente justamente quando corrupção ganha espaço na agenda. Sem os seis resultados, as bases e a fração que não conhece o suficiente para avaliar, o PDF não permite testar se o tema favorece um candidato específico. Não substituímos essa falta por uma conclusão partidária.</p>"
            + '<details id="inventario"><summary>Conferir os 66 itens, pergunta por pergunta</summary>'
            + table(["Q", "Tema", "Questionário", "Estado", "Relatório"], rows)
            + '</details><p><a href="assets/quaest_140926_data.json">Baixar o inventário com os blocos do instrumento em JSON</a>. Cada item preserva página, status e correspondência; a classificação pode ser atualizada quando aparecer nova publicação.</p>',
            "paper-grid",
        )
    )

    out.append(
        section(
            "instrumento",
            "As palavras medem coisas diferentes. <em>A legenda precisa acompanhar.</em>",
            "A maior crítica ao questionário não exige adivinhar a intenção de quem o escreveu. Exige identificar o que cada formulação permite medir.",
            table(
                ["Ponto", "Evidência registrada", "Consequência para a leitura"],
                [
                    [
                        "Potencial de voto",
                        "Q9–21: conhece e poderia votar; gráfico abrevia para conhece e votaria.",
                        "Disponibilidade hipotética não equivale a intenção de votar.",
                    ],
                    [
                        "Melhor resultado",
                        "Q34 combina Lula/PT, família Bolsonaro, moderado e alguém de fora.",
                        "Nomes e atributos valorativos no mesmo conjunto; não é escala neutra de ideologia.",
                    ],
                    [
                        "Medo",
                        "Q35 contrapõe novo governo Lula à volta da família Bolsonaro. Ambos/nenhum não são lidos.",
                        "A resposta pode depender da assimetria das alternativas e do esforço de oferecer uma resposta espontânea.",
                    ],
                    [
                        "Conhecimento do caso",
                        "Q46 e Q48 vêm depois de textos sobre o assunto.",
                        "Pergunta-se se já sabia após apresentar informação; não é lembrança espontânea sem estímulo.",
                    ],
                    [
                        "Identificação política",
                        "Q57 distingue lulista/esquerda não lulista e bolsonarista/direita não bolsonarista.",
                        "É mais detalhado que uma divisão binária, mas vem depois do bloco STF no instrumento. Sem experimento, priming é hipótese.",
                    ],
                    [
                        "Roteamento de convicção",
                        "Q24 remete a cen1t_pres1, com Marçal no registro; gráfico atual mostra lista sem Marçal.",
                        "Falta informar qual variável condiciona o denominador e os cruzamentos da p.94.",
                    ],
                    [
                        "Renda não declarada",
                        "Q6 prevê recusa, mas o perfil de três faixas fecha 100%.",
                        "Sem quantidade de recusas e regra de tratamento, não se reproduz a calibração inteira.",
                    ],
                ],
            )
            + "<p>A ordem dos nomes e dos cenários de segundo turno é aleatorizada no instrumento, um cuidado metodológico que merece crédito. Aleatorizar ordem ajuda contra efeitos de posição; não elimina diferenças de significado entre “moderado”, “família” e “partido”.</p>"
            + "<h3>O que mudou na pauta entre as duas semanas</h3><p>O instrumento de 7/9 tem 59 itens. Pergunta sobre economia nos últimos 12 meses, renda diante dos preços, dívidas e Desenrola (Q33–36); inclui sabatinas (Q40–41) e onze afirmações de motivação política (Q42–52). O de 14/9 tem 66 e acrescenta honestidade, confiança, Master, STF, reformas e convivência política. A economia sai como bateria própria; continua como opção espontânea de preocupação. Isso muda o que o levantamento permite diagnosticar, sem provar por si só intenção de favorecer alguém.</p>"
            + "<p>A medição de 48% que concordam com derrotar o atual presidente, na rodada anterior, pode iluminar o mecanismo de voto útil. Sua ausência como pergunta repetida impede afirmar que esse mecanismo se intensificou nesta semana. Uma manchete sobre a causa da alta precisaria dessa repetição ou de evidência mais forte.</p>"
            + b.questionref(7, 10, 12, 13, 14, 15, 16),
        )
    )

    terr = d["territory"]
    out.append(
        section(
            "territorio",
            "Quase todos os setores mudaram. <em>O desenho precisa ser auditável.</em>",
            "Os dois anexos territoriais foram extraídos por programa e comparados pelo código IBGE de 15 dígitos. Nomes de bairro não foram usados como equivalentes de setor censitário.",
            b.cards(
                [
                    (
                        "Em cada onda",
                        "334",
                        "Setores sem duplicação",
                        "Seis entrevistas por setor, total 2.004.",
                    ),
                    (
                        "Em cada onda",
                        "120",
                        "Municípios",
                        "26 reaparecem; 94 saem e outros 94 entram.",
                    ),
                    (
                        "Interseção exata",
                        "4",
                        "Setores repetidos",
                        "330 novos setores: 98,80% de renovação.",
                    ),
                    (
                        "Onda atual",
                        "600",
                        "Entrevistas em cidades comuns",
                        "29,94% das entrevistas ficam nos 26 municípios presentes nas duas ondas.",
                    ),
                ]
            )
            + table(
                ["Região", "Entrevistas em 14/9", "Participação %"],
                [[r, n, num(100 * n / 2004)] for r, n in terr["regions"].items()],
            )
            + "<p>As quantidades por macrorregião são idênticas entre as duas ondas. Portanto, a mudança municipal não equivale a uma mudança do peso regional. Uma amostra repetida pode rotacionar unidades legitimamente; alta rotação não é evidência de manipulação. O que falta para reproduzir o sorteio é o cadastro de seleção, os estratos, as probabilidades e a regra de rotação.</p>"
            + "<p>Essa configuração também impede tratar os dois relatórios como se acompanhassem as mesmas pessoas. Mudanças semanais misturam movimento de opinião, composição de amostras distintas e ruído. O anexo fecha aritmeticamente; a auditoria atual verifica códigos, consistência de UF, contagens e repetição, sem afirmar validação cartográfica independente de cada setor no cadastro IBGE vigente.</p>"
            + '<p><a href="assets/quaest_140926_territorio.csv">Baixar os 668 registros territoriais das duas ondas</a>. Os quatro setores repetidos e as contagens completas também estão no JSON analítico.</p>',
        )
    )

    mar = d["derived"]["difference_margin_2t_aas"]
    m1 = d["derived"]["difference_margin_1t_aas"]
    out.append(
        section(
            "incerteza",
            "Dois pontos de distância <em>não identificam liderança.</em>",
            "A margem da diferença entre candidatos não é a mesma margem exibida ao lado de um percentual isolado.",
            table(
                [
                    "Medida",
                    "Diferença L − F",
                    "Margem 95% sob AAS",
                    "Intervalo ilustrativo",
                ],
                [
                    [
                        "2º turno publicado",
                        "−2,00",
                        f"±{num(mar)}",
                        f"[{num(-2 - mar)}; {num(-2 + mar)}]",
                    ],
                    [
                        "1º turno publicado",
                        "+5,00",
                        f"±{num(m1)}",
                        f"[{num(5 - m1)}; {num(5 + m1)}]",
                    ],
                ],
            )
            + "<p>Para duas categorias mutuamente exclusivas, usamos 1,96 × √[(pL + pF − (pL − pF)²) / n], em proporções e depois convertido em pontos percentuais. A aproximação de amostragem aleatória simples é um diagnóstico, não o erro real do desenho domiciliar por conglomerados e cotas. O segundo turno já inclui zero nessa aproximação. No primeiro, cinco pontos superam a margem AAS, mas um efeito de desenho de aproximadamente 1,95 seria suficiente para o intervalo alcançar zero.</p>"
            + "<p>A variação semanal de Flávio, de 41 para 42 no segundo turno, tem margem ilustrativa de cerca de três pontos para a diferença entre duas amostras independentes de 2.004. A independência é uma aproximação, não uma característica demonstrada dos pesos. Um ponto não sustenta diagnóstico causal de sucesso de campanha.</p>"
            + "<p>O relatório publica margens por vários recortes, um mérito. Isso não substitui tamanhos brutos e efetivos das bases, covariância entre cenários ou erro do desenho. O gráfico de definição indica margens de 9 pontos para Cury, 12 para Caiado, 14 para Renan e 26 para Zema. Não atribuímos esses valores automaticamente à matriz de transferência, mas eles alertam para a fragilidade dos percentuais em candidaturas pequenas.</p>"
            + "<p>Não anexamos a margem publicada ao resultado PNAD como se ele fosse uma nova pesquisa. A sensibilidade altera pesos e incorpora incerteza do benchmark, arredondamento e diferenças de mensuração. Sem microdados e desenho, um intervalo formal para ela seria uma precisão inventada.</p>"
            + ref(2, 3, 27, 94),
        )
    )

    latest = {}
    for p in b.aggregate["pesquisas"]:
        latest[p["instituto"]] = p
    comp = []
    for name in ["Quaest", "Datafolha", "Nexus"]:
        p = latest[name]
        z = p["turnos"]["2t"]
        v = z["publicado"]
        a = z["cenarios"]["pessoas16_efetivo"]["ajustado"]
        comp.append(
            [
                name,
                p["campo"]["fim"],
                num(v["lula"]),
                num(v["flavio"]),
                num(100 * v["lula"] / (v["lula"] + v["flavio"])),
                num(100 * v["flavio"] / (v["lula"] + v["flavio"])),
                num(a["lula"]),
                num(a["flavio"]),
            ]
        )
    b.aggregate["agregador"]["ultimo"]
    out.append(
        section(
            "agregados",
            "A Quaest cabe no conjunto. <em>O conjunto não apaga o método.</em>",
            "Primeiro turno acrescentado, segundo turno confirmado e fonte integral identificada no agregador Arvor. A referência de cálculo foi atualizada para 15/09/2026.",
            table(
                [
                    "Instituto",
                    "Fim do campo",
                    "L pub.",
                    "F pub.",
                    "L válidos",
                    "F válidos",
                    "L PNAD",
                    "F PNAD",
                ],
                comp,
            )
            + "<p>Os percentuais totais devem ser lidos junto com a não escolha: Quaest tem 18% no segundo turno, contra 9% no Datafolha e 7% na Nexus. Por isso mostramos também válidos, normalizados somente entre os dois finalistas. Essa normalização retira a compressão mecânica provocada pela não escolha; não elimina diferenças de modo, seleção ou mensuração.</p>"
            + b.aggregate_table()
            + "<p>A média ponderada usa todas as ondas elegíveis com meia-vida de 14 dias; institutos que divulgam mais frequentemente contribuem mais observações. O painel também mostra a média da última onda de cada instituto, com pesos iguais. A série histórica usa alisamento simétrico e, portanto, não deve ser lida como um backtest em tempo real. Nenhuma dessas médias é uma probabilidade de vitória ou elimina erro sistemático compartilhado.</p>"
            + '<p><a href="reponderacao_pnad.html#pesquisa-quaest_2026-09-13">Ficha completa desta Quaest</a> · <a href="reponderacao_pnad.html#institutos">Comparação dos institutos</a> · <a href="assets/reponderacao_pnad.csv">CSV atualizado</a></p>',
        )
    )

    out.append(
        section(
            "diagnostico",
            "O que ajuda Flávio. <em>O que ainda não se converteu.</em>",
            "Leitura editorial, apoiada nos números publicados. Os dados descrevem resultados associados à campanha; não isolam o efeito causal de suas ações.",
            table(
                ["Dimensão", "Sinal favorável", "Limite ou contraponto"],
                [
                    [
                        "Presença eleitoral",
                        "Espontânea 20 → 23; estimulada 29 → 31.",
                        "41% ainda não escolhem espontaneamente. Não se sabe qual ação gerou a alta.",
                    ],
                    [
                        "Confronto final",
                        "Flávio 42, maior resultado entre os cinco adversários testados.",
                        "Diferença de dois pontos sobre Lula não identifica liderança estatística.",
                    ],
                    [
                        "Consolidação",
                        "Quatro origens menores medidas dão 7,03 pontos a Flávio contra 3,65 a Lula.",
                        "Zema tem distribuição pontual diferente e base muito pequena.",
                    ],
                    [
                        "Adesão",
                        "Potencial cresce de 40 a 43.",
                        "Rejeição fica em 55; convicção entre seus eleitores cai de 78 a 72.",
                    ],
                    [
                        "Ambiente de governo",
                        "Desaprovação 50 supera aprovação 43.",
                        "Essa distância não é voto disponível automaticamente.",
                    ],
                    [
                        "Expectativa de vitória",
                        "Flávio passa de 27 em 14/8 para 31 em 14/9.",
                        "Lula ainda é apontado vencedor por 54%. Expectativa não é intenção.",
                    ],
                    [
                        "Medo",
                        "Novo governo Lula é citado por 44, volta dos Bolsonaro por 42.",
                        "Pergunta contrapõe pessoa a família; ambos e nenhum não são lidos.",
                    ],
                    [
                        "Agenda",
                        "Corrupção é a segunda preocupação espontânea, 22%.",
                        "Violência segue em 31; honestidade por candidato está ausente do PDF.",
                    ],
                    [
                        "Comunicação",
                        "42% dizem ter visto algum programa eleitoral.",
                        "Não há medição por programa ou candidato para atribuir eficácia.",
                    ],
                    [
                        "Renda",
                        "O placar pontual continua favorável a Flávio na régua principal.",
                        "A vantagem encolhe a 0,74 ponto; não se deve tratar renda como argumento sempre pró-oposição.",
                    ],
                ],
            )
            + '<div class="plain-language">Juízo editorial: o retrato é melhor para Flávio do que o de julho, mas sua aceitação continua estreita e parte da adesão é condicional ao adversário. Uma interpretação séria publica a alta e a fragilidade juntas. Celebrar o segundo turno como vitória assegurada distorce o diagnóstico tanto quanto negar todo avanço.</div>'
            + ref(6, 27, 28, 75, 94, 96, 122, 144, 154),
        )
    )

    out.append(
        section(
            "cobranca",
            "A cobrança à Quaest <em>pode ser precisa.</em>",
            "O instituto oferece bastante material. A abundância de gráficos não substitui as peças necessárias para reproduzir o desenho e relacionar cada resposta à pergunta correta.",
            table(
                ["Documento ou informação", "Por que faz falta"],
                [
                    [
                        "Correspondência Q22/Q23/Q24 → cenários e bases publicados",
                        "Resolve renumeração do cenário, lista com/sem Marçal e denominador de convicção.",
                    ],
                    [
                        "Tabela-mestra de publicação dos 66 itens",
                        "Separa não aplicado, não divulgado, divulgado em suplemento e divulgado em notícia.",
                    ],
                    [
                        "Bases brutas, bases ponderadas e tamanho efetivo por recorte",
                        "Permite avaliar pequenos eleitorados e transparência da calibração.",
                    ],
                    [
                        "Variável, universo, cortes e rotina PNAD que produzem 31/42/27",
                        "Permite reproduzir a margem, que cita PNAD 2025 mas difere do benchmark Arvor.",
                    ],
                    [
                        "Método efetivamente usado: rake, MrP ou combinação definida",
                        "São procedimentos diferentes; informar “MrP ou rake” não especifica um estimador reproduzível.",
                    ],
                    [
                        "Estratos, probabilidades de seleção e regra de rotação",
                        "Torna auditáveis os 94 municípios substituídos e os 330 novos setores.",
                    ],
                    [
                        "Pesos ou estatísticas de sua dispersão e efeito de desenho",
                        "Dá fundamento à incerteza além da aproximação de amostra aleatória simples.",
                    ],
                    [
                        "Matriz completa 1T × 2T e covariância entre cenários",
                        "Substitui hipóteses sobre fidelidade e permite testar diferenças entre adversários.",
                    ],
                    [
                        "Voto recordado em 2022 antes e depois da ponderação",
                        "Cria uma verificação externa de composição, com ressalva de erro de memória.",
                    ],
                ],
            )
            + "<p><strong>O crédito devido:</strong> referências sociais atualizadas, questionário registrado, anexos territoriais que fecham, cruzamentos de renda que recompõem o placar e quatro linhas de transferência publicadas. <strong>A crítica central:</strong> o material é rico para leitura, mas incompleto para reprodução independente do estimador.</p>"
            + "<p>A ficha desta rodada aponta Globo Comunicação e Participações e Editora Globo como contratantes, por R$ 314.628,00. O contratante merece identificação, não presunção de manipulação. A crítica ao patrocinador e à referência PNAD do dossiê de agosto não pode ser transplantada para setembro. Há insuficiências documentais específicas; não há prova apresentada aqui de fraude ou fabricação.</p>"
            + ref(2, 3),
        )
    )
    return out
