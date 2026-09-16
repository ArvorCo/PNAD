"""Texto analítico e tabelas do dossiê, primeira parte."""


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
            "veredito",
            "O avanço existe no retrato. <em>A certeza, ainda não.</em>",
            "A renda é a primeira prova. A transferência é a segunda. A terceira é o que a própria pesquisa ainda não permite concluir.",
            b.cards(
                [
                    (
                        "Sensibilidade",
                        "40,66 × 41,40",
                        "Lula × Flávio sob a PNAD",
                        "O 40 × 42 publicado se estreita. Trocar apenas a renda reduz a diferença de 2 para 0,74 ponto.",
                    ),
                    (
                        "Medição + hipótese",
                        "2,75:1",
                        "Consolidação fora das bases",
                        "Com as bases dos finalistas retidas, Flávio recebe 11 pontos e Lula 4. Quatro origens menores têm transferência publicada.",
                    ),
                    (
                        "Fato publicado",
                        "78 → 72",
                        "Convicção de Flávio",
                        "Seu voto de 1º turno sobe de 29 para 31, mas a proporção que diz ter escolha definitiva diminui. Lula permanece em 80.",
                    ),
                    (
                        "Auditoria documental",
                        "66",
                        "Itens registrados",
                        "Inventário integral: resultado no PDF, divulgação externa, cadastro/controle e resultado não localizado são estados diferentes.",
                    ),
                ]
            )
            + '<div class="plain-language">A leitura mais sustentada é de consolidação eleitoral com adesão ainda frágil. Não há prova de uma vitória assegurada, de um efeito causal de propaganda ou de fraude no levantamento.</div>'
            + ref(22, 27, 28, 33, 94, 199),
            "paper-grid",
        )
    )

    income_rows = []
    targets = d["reweight"]["renda"]["pnad_pct"]["pessoas16_efetivo"]
    for i, label in enumerate(["Até 2 SM", "Mais de 2 a 5 SM", "Mais de 5 SM"]):
        income_rows.append(
            [label, num(t["PROFILE"][i]), num(targets[i]), *t["SECOND_INCOME"][i]]
        )
    out.append(
        section(
            "renda",
            "A PNAD <em>reduz a vantagem numérica de Flávio.</em>",
            "A mesma regra aplicada aos outros institutos favorece Lula nesta Quaest. A régua tem de sobreviver ao resultado de que o analista gosta.",
            b.figure(
                b.fig.profiles(d),
                "Perfil de renda ponderado da Quaest, p.199, versus pessoas de 16 anos ou mais na PNADC anual 2025, visita 1. Rendimento domiciliar efetivo; cortes de 2026 sob a regra de preços do agregador.",
            )
            + table(
                ["Faixa", "Quaest %", "PNAD %", "Lula", "Flávio", "B/N/não vota", "NS"],
                income_rows,
            )
            + "<p>A Quaest dá 31% de peso à faixa até dois salários mínimos. A referência Arvor dá 35,19%. Nesse grupo, Lula tem 51% contra 32%. A substituição aumenta o peso de um segmento em que Lula vai melhor e reduz o peso dos outros dois. O sentido da conta é previsível; seu tamanho precisa ser calculado.</p>"
            + b.cards(
                [
                    (
                        "Publicado",
                        "40 × 42",
                        "Segundo turno",
                        "Diferença Lula menos Flávio: −2 pontos.",
                    ),
                    (
                        "PNAD pessoas 16+",
                        "40,66 × 41,40",
                        "Segundo turno",
                        "Diferença: −0,74 ponto. Branco/nulo/não vota 12,94%; indecisos 5%.",
                    ),
                    (
                        "PNAD pessoas 16+",
                        "36,53 × 30,44",
                        "Primeiro turno",
                        "Publicado: 36 × 31. Diferença passa de +5 para +6,09 pontos.",
                    ),
                ]
            )
            + "<p><strong>A fonte deixou de ser parcial.</strong> O PDF confirma os mesmos votos por renda que o g1 havia divulgado e o perfil final 31/42/27. A atualização do agregador mantém o resultado anterior do segundo turno e acrescenta o primeiro. Não se reutilizou o cruzamento de 7/9 na rodada de 14/9.</p>"
            + "<details><summary>Conferir o primeiro turno por renda</summary>"
            + table(
                ["Faixa", "Lula", "Flávio", "Cury", "Outros", "NS", "B/N"],
                [
                    [label, *row]
                    for label, row in zip(
                        ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"],
                        t["FIRST_INCOME"],
                        strict=True,
                    )
                ],
            )
            + "<p>Percentuais impressos na p.22. Somas 101, 101 e 100; arredondamentos preservados. Na p.16, os 9% de outros são Renan 4, Caiado 4 e Zema 1; Clariana, Edmilson, Hertz, Rui, Samara e Grassi aparecem com 0% arredondado.</p></details>"
            + ref(16, 22, 28, 33, 199),
        )
    )

    rows = []
    for key, label in [
        ("pessoas16_efetivo", "Pessoas 16+, efetivo: principal"),
        ("pessoas16_habitual", "Pessoas 16+, habitual"),
        ("domicilios_efetivo", "Domicílios, efetivo: universo alternativo"),
    ]:
        vals = [
            d["reweight"]["turnos"][r]["cenarios"][key]["ajustado"]
            for r in ["1t", "2t"]
        ]
        rows.append(
            [
                label,
                *[num(v[k]) for v in vals for k in ["lula", "flavio"]],
                num(vals[1]["lula"] - vals[1]["flavio"]),
            ]
        )
    proof = []
    for turno in ["1t", "2t"]:
        x = d["proofs"][turno]
        p = d["reweight"]["turnos"][turno]["publicado"]
        r = x["income_recomposed"]
        s = x["sex_recomposed"]
        proof.append(
            [
                turno.upper(),
                f"{num(p['lula'])} / {num(p['flavio'])}",
                f"{num(r['lula'])} / {num(r['flavio'])}",
                f"{num(s[0])} / {num(s[1])}",
            ]
        )
    out.append(
        section(
            "metodo-renda",
            "Uma margem trocada. <em>Três universos à vista.</em>",
            "Sensibilidade não é voto corrigido. O cálculo conserva a âncora publicada e muda apenas a composição por renda.",
            '<div class="formula">ajustado = publicado + composição PNAD − composição Quaest</div>'
            + table(
                [
                    "Cenário",
                    "Lula 1T",
                    "Flávio 1T",
                    "Lula 2T",
                    "Flávio 2T",
                    "L − F no 2T",
                ],
                rows,
            )
            + "<p>O universo principal conta pessoas de 16 anos ou mais, ponderadas por V1032, na PNADC anual 2025, visita 1. A renda efetiva é VD5001; a variante habitual usa VD5007. Domicílios entram apenas como teste: dar um voto a cada casa altera o universo, e não substitui um eleitor por um domicílio. Essa variante inverte o sinal, o que reforça a necessidade de declarar o denominador.</p>"
            + "<p>As faixas são renda total do domicílio, não per capita e não apenas renda do trabalho. O cartão usa R$ 3.242 e R$ 8.105, dois e cinco salários de R$ 1.621. O histograma de referência está em reais de abril de 2026; o motor consulta o IPCA disponível para converter o corte. A última competência disponível nesta reprodução é <strong>"
            + d["meta"]["price_month"]
            + "</strong>; depois dela, o motor mantém o último índice conhecido, sem inventar inflação.</p>"
            + "<h3>Prova de leitura em duas dimensões independentes</h3>"
            + table(
                [
                    "Turno",
                    "Publicado L / F",
                    "Recomposto por renda",
                    "Recomposto por sexo",
                ],
                proof,
            )
            + "<p>Sexo usa 53% de mulheres e 47% de homens, p.196. Os resíduos dos finalistas são menores que meio ponto nas duas provas. No primeiro turno, duas linhas de renda somam 101%; preservamos os números impressos. A soma do resultado ajustado pode, por isso, diferir ligeiramente de 100%. Não escondemos o arredondamento em uma categoria residual.</p>"
            + "<p><strong>Crítica que cabe:</strong> a documentação precisa permitir reproduzir os 31/42/27 a partir da PNAD declarada. <strong>Crítica que não cabe:</strong> dizer que esta onda usa PNAD 2024. O relatório e o registro citam PNAD anual 2025, visita 1. A diferença pode envolver universo, variável, preços, tratamento da não resposta e calibração conjunta; os agregados publicados não identificam qual combinação foi usada.</p>"
            + ref(2, 3, 19, 22, 30, 33, 196, 199),
        )
    )

    series = []
    for p in b.aggregate["pesquisas"]:
        if p["instituto"] != "Quaest" or "2t" not in p["turnos"]:
            continue
        z = p["turnos"]["2t"]
        a = z["cenarios"]["pessoas16_efetivo"]["ajustado"]
        series.append(
            [
                p["divulgacao"],
                num(z["publicado"]["lula"]),
                num(z["publicado"]["flavio"]),
                num(a["lula"]),
                num(a["flavio"]),
                num(a["lula"] - a["flavio"]),
            ]
        )
    out.append(
        section(
            "historico",
            "A distância caiu. <em>Isso não começou nesta semana.</em>",
            "Desde julho, o segundo turno sai de Lula 45 × Flávio 37 para 40 × 42: dez pontos de mudança na diferença, distribuídos entre queda de um e alta do outro.",
            b.figure(
                b.fig.history(d),
                "Série publicada no PDF de 14/9, p.28. Mesma dupla; contratação e composição de ondas anteriores não são presumidas idênticas.",
            )
            + table(
                [
                    "Divulgação",
                    "Lula publicado",
                    "Flávio publicado",
                    "Lula PNAD",
                    "Flávio PNAD",
                    "L − F PNAD",
                ],
                series,
            )
            + "<p>A régua comum de renda preserva o estreitamento ao longo das ondas disponíveis. De 7 para 14/9, a distância publicada passa de zero a −2 pontos; a ajustada, de +1,29 a −0,74. O movimento semanal é pequeno diante da incerteza. A sequência é informativa; não transforma cada oscilação em mudança individual comprovada.</p><p>O histórico impresso já registra Lula 40 × Flávio 42 em abril. A expressão “primeira vez na campanha”, usada na <a href='https://www.cnnbrasil.com.br/eleicoes/quaest-flavio-aparece-numericamente-a-frente-de-lula-pela-1a-vez/'>cobertura da CNN</a> com essa ressalva, se refere ao período iniciado em agosto. Não equivale a primeira vantagem numérica no ano.</p>"
            + "<h3>Primeiro turno: comparar a mesma lista</h3>"
            + table(
                ["Cenário sem Marçal", "Lula", "Flávio", "Cury", "Outros", "NS", "B/N"],
                [
                    [date, *r]
                    for date, r in zip(
                        ["02/09", "07/09", "14/09"], t["FIRST_HISTORY"], strict=True
                    )
                ],
            )
            + "<p>O PDF de 7/9 publica o cenário <strong>com Marçal</strong> nas pp.16–22 e o <strong>sem Marçal</strong> na p.27. O PDF de 14/9 chama o cenário sem Marçal de “cenário 1” e repete a série equivalente. Isso explica por que o histórico acima tem 10% de indecisos em 7/9, enquanto o registro anterior do agregador, com Marçal, tem 9%. Não é revisão arbitrária de um número.</p>"
            + b.oldref(16, 17, 22, 27)
            + ref(16, 17, 28),
        )
    )

    measured = [[r["name"], r["share"], *r["row"]] for r in t["TRANSFERS"]]
    matrix = [
        [name, *[num(v) for v in row], kind]
        for name, row, kind in zip(
            d["transfer"]["origins"],
            d["transfer"]["matrix"],
            d["transfer"]["kinds"],
            strict=True,
        )
    ]
    out.append(
        section(
            "transferencia",
            "Quatro origens medidas. <em>O resto tem nome e hipótese.</em>",
            "O Sankey preserva a medição da Quaest e fixa as bases de Lula e Flávio integralmente no próprio candidato. Só indecisos e branco/nulo do primeiro turno são ajustados pelo modelo.",
            b.figure(
                b.fig.sankey(d),
                "Larguras em pontos do eleitorado total. Passe o ponteiro ou use Tab para consultar os fluxos. O desenho é agregado, não um acompanhamento dos mesmos indivíduos entre datas.",
            )
            + table(
                ["Origem", "Peso no 1T", "→ Lula %", "→ Flávio %", "→ NS %", "→ B/N %"],
                measured,
            )
            + "<p>A matriz publicada cobre Cury, Renan, Caiado e Zema, que juntos somam 16 pontos no primeiro turno. Aplicados os cruzamentos, eles entregam <strong>3,65 pontos a Lula e 7,03 a Flávio</strong>; 0,81 fica indeciso e 4,51 vai para branco/nulo/não voto. É transferência entre respostas de cenários na mesma entrevista, não movimento temporal já realizado.</p>"
            + "<p>As bases L36 e F31 ficam 100% fiéis por <strong>hipótese estrutural explícita</strong>. Não há fita de Lula ou Flávio para branco, nulo, indecisão ou adversário. A Quaest não publicou essas duas linhas na p.27; o desenho não transforma essa ausência em medição de fidelidade perfeita.</p>"
            + "<p>Depois dos seis blocos fixos, os 17 pontos de indecisos e não voto do primeiro turno precisam preencher 0,35 ponto de Lula, 3,97 de Flávio, 4,19 de indecisão e 8,49 de não voto. O IPF/RAS fecha essas margens, partindo de uma distribuição declarada no JSON que preserva mais não voto em quem já não escolhia. Outra prior muda o corte entre essas duas origens, mas não seus totais de chegada. A PNAD não foi aplicada a cada fita: falta o cruzamento conjunto de primeiro turno, segundo turno e renda. Este Sankey fecha os placares publicados.</p>"
            + "<details><summary>Matriz completa em pontos do eleitorado</summary>"
            + table(["Origem", "Lula", "Flávio", "NS", "B/N", "Natureza"], matrix)
            + "</details>"
            + '<div class="plain-language">A razão 11 ÷ 4 = 2,75:1 é imposta pelas margens sob a hipótese de bases retidas. Era 12 ÷ 5 = 2,40:1 em 7/9. O detalhamento dos dois resíduos depende da prior. Se a retenção das bases for relaxada, a interpretação de “ganho fora da base” também muda.</div>'
            + ref(16, 27, 28),
            "paper-grid",
        )
    )

    out.append(
        section(
            "voto-util",
            "Voto útil é compatível com os dados. <em>Não explica tudo sozinho.</em>",
            "Flávio cresce dois pontos no primeiro turno e um no segundo. A redução da distância entre seus dois resultados combina consolidação com alteração do confronto direto.",
            table(
                ["Medida", "07/09", "14/09", "Variação"],
                [
                    ["Flávio 1º turno sem Marçal", 29, 31, "+2"],
                    ["Flávio 2º turno", 41, 42, "+1"],
                    ["Distância 2T − 1T", 12, 11, "−1"],
                    ["Cury + Renan + Caiado + Zema no 1T", 16, 16, "0"],
                ],
            )
            + "<p>Os quatro candidatos menores tinham 8 + 3 + 3 + 2 = 16 pontos; agora têm 7 + 4 + 4 + 1 = 16. Logo, a alta de Flávio não pode ser descrita simplesmente como esvaziamento líquido desse conjunto. Dentro dele, Cury e Zema recuam, enquanto Renan e Caiado avançam. Margens iguais podem esconder trocas em vários sentidos; a pesquisa não oferece painel longitudinal para rastreá-las.</p>"
            + "<p>Há uma pergunta direta na rodada anterior: 38% concordam totalmente e 10% parcialmente que o mais importante é votar em quem tem mais chance de derrotar o atual presidente. Os 48% medem uma disposição declarada diante de uma frase explicitamente anti-incumbente. Não medem 48% já convertidos para Flávio. Essa bateria não aparece no questionário de 14/9, portanto não temos uma nova leitura semanal da motivação.</p>"
            + b.oldref(164)
            + "<p><strong>Contraponto medido:</strong> entre os eleitores de Zema, a p.27 mostra 38% para Lula e 32% para Flávio. Não se deve substituir essa linha por uma preferência ideológica do analista. Ao mesmo tempo, Zema tem só 1% no primeiro turno; a própria Quaest indica margem de 26 pontos para esse eleitorado no gráfico de definição da p.94. Esse recorte não sustenta uma ordenação estatística precisa.</p>"
            + ref(16, 27, 94),
        )
    )

    out.append(
        section(
            "adesao",
            "Mais lembrança e mais voto. <em>Menos convicção dentro da base.</em>",
            "O crescimento de Flávio vem acompanhado de uma base proporcionalmente mais aberta a mudar. Isso é consistente com a chegada de apoios menos consolidados; não prova a origem desses apoios.",
            table(
                [
                    "Indicador",
                    "Lula 7/9",
                    "Lula 14/9",
                    "Flávio 7/9",
                    "Flávio 14/9",
                    "Página",
                ],
                [[*x[:5], x[5]] for x in t["MOVEMENT"]],
            )
            + "<p>A espontânea de Flávio sobe de 20 a 23 e a estimulada de 29 a 31. Sua distância entre reconhecimento espontâneo e escolha estimulada cai de nove para oito pontos. É sinal descritivo de presença maior na memória do eleitorado, sem permitir atribuir o efeito a uma peça, entrevista ou canal.</p>"
            + "<p>O potencial declarado cresce de 40 a 43, mas a rejeição fica em 55. Lula também chega a 55 de rejeição. A melhora de Flávio, portanto, não veio acompanhada de queda semanal da rejeição. “Poderia votar”, a redação do instrumento, tampouco é a mesma coisa que “votaria”, a abreviação usada em parte dos gráficos.</p>"
            + "<p>Uma conta exploratória multiplica voto pela certeza: Flávio tinha 29 × 78% = 22,62 pontos de escolha declarada definitiva e passa a 31 × 72% = 22,32. Lula tem 36 × 80% = 28,80. Isso <strong>não é piso garantido</strong>, e a comparação pressupõe que o cruzamento de definição corresponda à lista de candidatos publicada. O instrumento ainda roteia Q24 pelo cenário com Marçal; falta uma correspondência inequívoca entre variável registrada e gráfico renumerado.</p>"
            + "<h3>O mercado aberto exige o denominador correto</h3><p>Na p.85, 27% dizem poder mudar entre quem escolheu candidato. Usando os 83% de voto nominal do cenário publicado, a tradução aproximada é 83% × 27% + 10% de indecisos = <strong>32,41% do eleitorado</strong>. Somar diretamente 27 + 10 produz 37 e mistura universos. A conta de 32,41 também depende da correspondência de cenários acima; não inclui automaticamente os 7% de branco/nulo. Abertura não é direção de migração.</p>"
            + ref(6, 75, 85, 94),
        )
    )

    altrows = []
    for a in d["alternatives"]:
        z = a["sensitivity"]["cenarios"]["pessoas16_efetivo"]["ajustado"]
        v = a["published"]
        altrows.append(
            [
                a["name"],
                v[0],
                v[1],
                v[2] + v[3],
                num(z["lula"]),
                num(z["adversario"]),
                num(z["lula"] - z["adversario"]),
            ]
        )
    out.append(
        section(
            "substitutos",
            "Flávio é o mais forte no agregado. <em>Não em todo recorte.</em>",
            "Cinco confrontos na mesma amostra permitem comparar nomes com recrutamento, momento e ponderação compartilhados. As respostas são condicionais aos cenários, não previsão de substituição na urna.",
            table(
                [
                    "Adversário",
                    "Lula pub.",
                    "Adversário pub.",
                    "Não escolha",
                    "Lula PNAD",
                    "Adversário PNAD",
                    "L − adversário PNAD",
                ],
                altrows,
            )
            + "<p>Flávio marca 42, três acima de Caiado, quatro de Renan, seis de Cury e nove de Zema. Porém Lula não fica imóvel: varia de 38 contra Cury a 45 contra Zema. A troca do adversário altera tanto o desafiante quanto Lula e a não escolha. Não cabe importar automaticamente a tese de que toda a perda do substituto vira branco/nulo.</p>"
            + "<p><strong>O contraponto que uma leitura favorável a Flávio precisa publicar:</strong> acima de cinco salários mínimos, Caiado marca 51, Renan 48 e Flávio 47. São estimativas pontuais; a diferença entre cenários na mesma amostra exige covariância individual para um teste adequado. Ainda assim, a tabela impede afirmar que Flávio domina todos os segmentos. Essa comparação descreve o levantamento, sem prescrever persuasão dirigida por renda.</p>"
            + "<p>Nas alternativas, a reponderação também mantém a âncora nacional. Os resíduos de recomposição ficam entre 0,11 e 0,68 ponto nos finalistas. Em Caiado, o resíduo de 0,68 recomenda cautela adicional com centésimos; eles servem à reprodução da conta, não representam precisão amostral.</p>"
            + ref(28, 33, 37, 42, 46, 51, 55, 60, 64, 69),
        )
    )

    out.append(
        section(
            "blocos",
            "Desejar a volta da família é diferente <em>de votar no candidato.</em>",
            "A pergunta sobre o melhor resultado separa quatro aspirações. Não é uma escala neutra de ideologia: as alternativas carregam nomes, experiência e o atributo positivo de moderação.",
            table(
                [
                    "Melhor resultado para o país",
                    "Peso",
                    "Lula 1T",
                    "Flávio 1T",
                    "Lula 2T",
                    "Flávio 2T",
                    "B/N 2T",
                    "NS 2T",
                ],
                [
                    [
                        name,
                        t["BEST_RESULT"][i],
                        *t["BEST_FIRST"][i],
                        *t["BEST_SECOND"][i],
                    ]
                    for i, name in enumerate(
                        [
                            "Lula/PT vencer",
                            "Família Bolsonaro voltar",
                            "Moderado fora da polarização",
                            "Nome de fora da política",
                        ]
                    )
                ],
            )
            + "<p>Somados, moderado e outsider representam 35% do eleitorado. Nesses dois grupos, Flávio tem 24 e 26 no primeiro turno e 47 e 39 no segundo. Isso documenta adesão condicional a um confronto, não entusiasmo uniforme por uma restauração da família Bolsonaro. No grupo que deseja essa volta, seus resultados são 81 e 93. Os 8% sem resposta à pergunta de melhor resultado não têm coluna no cruzamento: não agregamos essas quatro colunas como se cobrissem o país inteiro.</p>"
            + "<p>O outro eixo, identificação política, distribui 19% lulistas, 14% esquerda não lulista, 32% independentes, 21% direita não bolsonarista e 12% bolsonaristas, mais 2% sem posição. Entre independentes, o segundo turno sai de Lula 28 × Flávio 32 para 26 × 36. É o movimento pontual publicado, com margem de quatro pontos no recorte; não identifica conversões individuais. Os dois eixos se sobrepõem e nunca devem ser somados.</p>"
            + ref(25, 36, 106, 115, 116, 194),
        )
    )
    return out
