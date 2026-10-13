"""Leitura editorial da Nexus: transferências, mobilização e agenda pública."""

import json

from .view import (
    bars,
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
    s = d["special"]
    chapters = []
    chapters.append(
        section(
            1,
            "renda",
            "A composição é a mesma.<br><em>O efeito da renda cresceu.</em>",
            "O perfil continua 19% até um salário, 18% entre um e dois, 40% entre dois e cinco e 23% acima de cinco, como em 28/09. Isso não mantém constante o efeito eleitoral da margem.",
            income_section(d, "nexus")
            + "<p>Os dois estratos de renda baixa se compensam em parte: até 1 salário, a pesquisa tem 19% contra 13,44% na PNAD; de 1 a 2, 18% contra 21,75%. Juntos, são 37% contra 35,19%. O voto dentro dessas duas faixas, porém, é muito diferente: <b>Flávio 32% × Lula 58%</b> na primeira e <b>47% × 44%</b> na segunda.</p>"
            + vote_profiles(d, ["até 1 SM", "1–2 SM", "2–5 SM", ">5 SM"])
            + "<p>Com o mesmo perfil de renda, a sensibilidade da diferença F−L era de +0,44 pp no duelo hipotético de 28/09 e agora é de +1,94 pp. A mudança vem dos cruzamentos de voto, não de uma alteração demonstrada na composição de renda. São amostras distintas, em fases diferentes da eleição.</p>"
            + note(
                'A Nexus já declarava PNADC anual 2025, visita 1, no <a href="fontes/nexus_btg_28092026/registro-metodologia.txt">registro de 28/09</a>, e mantém a referência. O perfil em quatro faixas fecha em 100%; o relatório não quantifica renda sem resposta nem esclarece seu tratamento. A conta conserva a regra comum da casa, sem inventar essa parcela.'
            )
            + ref("nexus", 4, 41, 99),
        )
    )
    transfer = s["transfer_1t"]
    chapters.append(
        section(
            2,
            "transferencias",
            "Bases retidas.<br><em>Transferências desiguais.</em>",
            "98% de quem lembra ter votado em cada finalista mantém o mesmo candidato. Entre os demais candidatos, Flávio recebe 45% e Lula 32%; 19% preferem branco/nulo.",
            stacks(
                "Voto lembrado no 1º turno e intenção atual",
                transfer["rows"],
                transfer["options"],
            )
            + note(
                "Cada linha é percentual dentro de um grupo de voto lembrado, não o tamanho nacional do fluxo. A Nexus não publica as bases desses grupos; não há painel seguindo as mesmas pessoas no tempo."
            )
            + ref("nexus", 25)
            + "<p>O conjunto da terceira via não é homogêneo. A transferência declarada é mais favorável a Flávio entre eleitores de Zema e Caiado; entre os de Cury, os dois aparecem próximos. Renan tem uma fração elevada de branco/nulo. O residual de outras candidaturas aparece 100% com Lula, mas sua base não é informada e pode ser muito pequena.</p>"
            + stacks(
                "Transferências por candidatura anterior",
                s["transfer_detail"]["rows"],
                transfer["options"],
            )
            + ref("nexus", 26)
            + callout(
                "Quem não foi à urna também tem preferência",
                "Entre os que dizem ter faltado no 1º turno, são 49% para Flávio e 41% para Lula. Essa é preferência declarada dos respondentes alcançados; não demonstra que eles comparecerão, nem identifica o voto de todos os ausentes do país.",
            )
            + details(
                "O recorte de 2022 conta outra história",
                stacks(
                    "Voto lembrado em 2022",
                    s["transfer_2022"]["rows"],
                    transfer["options"],
                )
                + note(
                    "Retenção declarada de 90% de Lula e 91% de Bolsonaro; 6% cruzam para o outro lado em cada grupo. Memória de quatro anos e memória de uma semana são medições diferentes. Os dois conjuntos se sobrepõem e não podem ser somados."
                )
                + ref("nexus", 24),
            )
            + note(
                'Essas transferências já estão refletidas no placar 48% × 45%. Acrescentá-las ao placar novamente contaria os mesmos votos duas vezes. A Datafolha publica 46% × 32% para um conjunto de quatro candidaturas eliminadas; as definições e bases não são idênticas. <a href="datafolha_08102026.html#transferencias">Comparar a leitura</a>.'
            ),
        )
    )
    chapters.append(
        section(
            3,
            "firmeza",
            "Decisão cedo.<br><em>Presença ainda declarada.</em>",
            "92% dizem não pretender mudar o voto e 83% dizem ter decidido o segundo turno antes de 04/10. São respostas retrospectivas; não garantias sobre o dia da eleição.",
            stats(
                [
                    (
                        "95%",
                        "dos eleitores atuais de cada finalista dizem manter a escolha",
                    ),
                    (
                        "7%",
                        "do total admite mudar; inclui eleitores ainda sem candidato",
                    ),
                    (
                        "95%",
                        "declara presença certa ou provável; não é previsão de comparecimento",
                    ),
                ]
            )
            + stacks(
                "Firmeza por intenção atual",
                s["decision"]["by_vote"],
                s["decision"]["labels"],
            )
            + ref("nexus", 33, 34, 42, 43)
            + '<div class="split"><div><h3>Mudar não significa ir ao adversário</h3>'
            + bars("Segunda opção entre os que podem mudar", s["second_option"]["rows"])
            + "<p>Entre os 7% que admitem mudar, 52% indicam branco/nulo como segunda opção. Multiplicar os dois percentuais dá cerca de 3,6% da amostra, sob os números arredondados. É uma possibilidade declarada, não perda prevista de votos.</p>"
            + ref("nexus", 38)
            + "</div><div><h3>Piso e teto não são intervalo estatístico</h3>"
            + table(
                ["Candidato", "Piso", "Intenção", "Teto"],
                [["Flávio", "46%", "48%", "49%"], ["Lula", "43%", "45%", "46%"]],
            )
            + "<p>A Nexus combina certeza e segunda opção para construir esses limites. Eles não incluem erro amostral, mudanças de quem hoje se diz firme ou novos fatos. O teto não limita a votação real.</p>"
            + ref("nexus", 39)
            + "</div></div>"
            + callout(
                "Intenção de comparecer não é comparecimento calibrado",
                '89% dizem já ter decidido ir e 6% dizem que provavelmente irão. No 1º turno, o comparecimento efetivo no Brasil sem exterior foi 79,16%. São turnos e medições diferentes; a distância mostra por que declaração não deve virar automaticamente uma previsão de 95%. O simulador Arvor conserva o <a href="reponderacao_pnad.html#comparecimento-historico">controle de comparecimento e a história eleitoral</a>.',
            )
            + note(
                "Na mesma pergunta, 100% dos jovens de 16–24 anos declaram ida certa/provável; entre católicos, 98%, e evangélicos, 92%. Percentuais arredondados e respostas condicionais não identificam a presença por candidato. As duas casas não publicam voto × presença diretamente nesta rodada."
            )
            + ref("nexus", 15, 17, 18),
        )
    )
    chapters.append(
        section(
            4,
            "segmentos",
            "O mesmo país.<br><em>Clivagens muito diferentes.</em>",
            "Homens e mulheres, Nordeste e restante do país, renda muito baixa e renda superior produzem quadros distintos. Os números descrevem respondentes de cada recorte, com margens maiores que a nacional.",
            '<div class="split"><div><h3>Gênero</h3>'
            + vote_profiles(d, ["homens", "mulheres"])
            + ref("nexus", 40)
            + "</div><div><h3>Regiões</h3>"
            + vote_profiles(d, ["Nordeste", "Sudeste", "Sul", "CO/Norte"])
            + ref("nexus", 41)
            + "</div></div>"
            + "<p>Flávio − Lula vai de +21 pp entre homens a −15 pp entre mulheres: diferença descritiva de 36 pontos entre os grupos. No Nordeste, Lula tem 61% contra 32%; no Sul, Flávio tem 57% contra 36%. Norte e Centro-Oeste são publicados juntos: não há estimativa separada para cada um nesse quadro.</p>"
            + vote_profiles(d, ["16–24", "25–40", "41–59", "60+"])
            + ref("nexus", 40)
            + "<p>A maior vantagem de Lula por idade aparece nos jovens (57% × 39%). Os intervalos centrais da Nexus são 25–40 e 41–59, enquanto a Datafolha usa 25–34, 35–44 e 45–59; não se deve subtrair esses grupos como se fossem iguais. Mesmo entre os jovens comparáveis, as casas divergem: a Datafolha mede Flávio 50% × Lula 43% em 06–07/10. Diferença de casa, campo e recrutamento impede chamar isso de migração individual em cinco dias.</p>"
            + "<p>Escolaridade fundamental favorece Lula (52% × 39%); médio e superior favorecem Flávio. Católicos medem Lula 51% × Flávio 44%; evangélicos, Flávio 58% × Lula 32%. No trabalho formal, Flávio tem 54% contra 39%; no informal, 46% contra 48%. Isso não separa os efeitos de renda, religião, região, gênero e escolaridade, que se cruzam.</p>"
            + details(
                "Bolsa Família: a pergunta é sobre o domicílio",
                stacks(
                    "Voto por presença de Bolsa Família no domicílio",
                    s["bolsa_familia"]["rows"],
                    ["Flávio", "Lula", "Branco/nulo", "NS/NR"],
                )
                + note(
                    s["bolsa_familia"]["universe"] + " " + s["bolsa_familia"]["limit"]
                )
                + ref("nexus", 31, 32),
            )
            + explorer(d, "nexus")
            + note(
                "Margens publicadas: 3 pp por gênero, 6 pp nos jovens, 5 pp em cada uma das duas faixas de menor renda, 3 pp no Sudeste e 6 pp no Sul e CO/Norte. São margens por percentual do instituto, não da diferença entre candidatos."
            )
            + ref("nexus", 40, 41, 100),
        )
    )
    motivation = s["motivation"]
    chapters.append(
        section(
            5,
            "perguntas",
            "Rejeição existe.<br><em>Não explica tudo.</em>",
            "71% dos eleitores de Flávio e 81% dos de Lula dizem escolher o melhor candidato. Votar para derrotar o adversário é a motivação principal de 23% e 15%, respectivamente.",
            stacks(
                "Motivação dentro de cada eleitorado",
                {
                    "Eleitores de Flávio": motivation["flavio"],
                    "Eleitores de Lula": motivation["lula"],
                },
                motivation["labels"],
            )
            + "<p>A p. 55 tem título “amostra total”, mas as barras 71%/23% e 81%/15% usam cada eleitorado. As setas de 11% e 7% reexpressam a rejeição no total, e a p. 59 publica o consolidado de 18%. Portanto, 23% dos eleitores de Flávio não significa 23% dos brasileiros.</p>"
            + ref("nexus", 55, 56, 59)
            + '<div class="split"><div><h3>O público sem candidato é pequeno e diverso</h3>'
            + bars("Motivos entre os 7% sem escolha", s["nonchoice"]["rows"])
            + note(
                "35% desse grupo diz que nenhum candidato o representa; são cerca de 2,5% da amostra ao reexpressar os percentuais arredondados. Rejeição de ambos corresponde a cerca de 2,0%. Esses motivos não garantem conversão futura."
            )
            + ref("nexus", 57)
            + "</div><div><h3>Cansaço com a polarização não é indecisão</h3>"
            + bars("Sentimento no total da amostra", s["polarization"]["rows"])
            + note(
                "38% estão cansados/desconfortáveis, mas 92% dizem ter voto firme. Não há cruzamento dessas duas respostas publicado; não se pode converter o cansaço em migração. A pergunta apresenta a avaliação de analistas antes de solicitar concordância."
            )
            + ref("nexus", 52)
            + "</div></div>"
            + details(
                "Aceitar dois candidatos, rejeitar dois e ser ‘antiambos’ são medidas diferentes",
                table(
                    ["Medida", "Percentual", "O que significa"],
                    [
                        [
                            "Rejeita os dois candidatos",
                            "4%",
                            "Potencial/rejeição por candidato, p. 67",
                        ],
                        [
                            "Aceita os dois candidatos",
                            "4%",
                            "Poderia votar; não é intenção atual",
                        ],
                        [
                            "Anti-Lula e anti-Bolsonaro/família",
                            "8%",
                            "Cluster derivado de duas escalas, pp. 11/13",
                        ],
                        [
                            "Não polarizados",
                            "20%",
                            "Cluster das escalas; não significa sem voto",
                        ],
                    ],
                )
                + "<p>No grupo “antiambos”, 50% declaram Lula e 37% Flávio; entre não polarizados, 44% Lula, 37% Flávio, 14% branco/nulo e 5% NS/NR. Os nomes dos clusters não determinam a escolha e não equivalem à pergunta de rejeição. A p. 13 ainda preserva 7% NS/NR na classificação.</p>"
                + ref("nexus", 10, 11, 13, 27, 67),
            )
            + callout(
                "Expectativa de vitória mede percepção, não voto",
                "59% acham que Flávio vencerá, mas 48% pretendem votar nele. Entre mulheres, 50% esperam vitória dele, enquanto só 39% o escolhem. A crença sobre quem vence pode coexistir com voto no adversário; não é probabilidade de vitória validada.",
            )
            + ref("nexus", 48, 50),
        )
    )
    economy = s["economy"]
    chapters.append(
        section(
            6,
            "economia",
            "O país preocupa.<br><em>O futuro ganhou otimismo.</em>",
            "51% avaliam mal a economia nacional, contra 20% que avaliam mal as próprias finanças. Ao mesmo tempo, a expectativa de melhora do país em seis meses sobe de 46% para 54% na série Nexus.",
            stacks(
                "Economia atual e finanças pessoais",
                {
                    "Economia do país": economy["current"]["country"],
                    "Finanças pessoais": economy["current"]["personal"],
                },
                economy["current"]["labels"],
            )
            + ref("nexus", 92)
            + stacks(
                "Expectativa para os próximos seis meses",
                {
                    "Economia do país": economy["future"]["country"],
                    "Finanças pessoais": economy["future"]["personal"],
                },
                economy["future"]["labels"],
            )
            + ref("nexus", 96)
            + "<p>O otimismo não é uma medida automática de apoio ao governo atual. Entre quem espera melhora da economia nacional, Flávio tem 52% e Lula 43%. Entre quem considera a economia atual ótima/boa, Lula tem 96% e Flávio 3%. São perguntas com horizontes diferentes; a expectativa pode conter antecipação de uma troca de governo, mas essa hipótese não foi testada no cruzamento expectativa econômica × expectativa de vitória.</p>"
            + stacks(
                "Voto e expectativa econômica nacional",
                economy["future_vote"]["country"],
                ["Flávio", "Lula", "Branco/nulo", "NS/NR"],
            )
            + ref("nexus", 93, 97)
            + details(
                "Comparação com o governo anterior",
                stacks(
                    "Avaliação em relação ao governo anterior",
                    {
                        "Economia do país": economy["past"]["country"],
                        "Finanças pessoais": economy["past"]["personal"],
                    },
                    economy["past"]["labels"],
                )
                + note(
                    "44% avaliam a economia nacional pior que no governo anterior, contra 38% melhor. Nas próprias finanças, 43% melhor e 32% pior. Opinião econômica e voto aparecem associados; esta pesquisa transversal não identifica o sentido da causalidade."
                )
                + ref("nexus", 94, 95),
            )
            + "<h3>Regular não é oposição automática</h3>"
            + stacks(
                "Voto dentro de cada avaliação do governo",
                s["government_vote"]["rows"],
                ["Flávio", "Lula", "Branco/nulo", "NS/NR"],
            )
            + "<p>O governo recebe 34% ótimo/bom, 20% regular e 45% ruim/péssimo. Entre os regulares, Lula tem 59% e Flávio 24%. Na pergunta binária, 45% aprovam e 50% desaprovam; 93% dos aprovadores votam Lula e 91% dos desaprovadores votam Flávio. Avaliação em cinco categorias, aprovação binária e intenção de voto não são a mesma régua.</p>"
            + ref("nexus", 72, 74, 80, 82),
        )
    )
    problems = s["problems"]
    initial = {name: values[2] for name, values in problems["rows"].items()}
    chapters.append(
        section(
            7,
            "agenda",
            "Segurança e saúde.<br><em>Demandas que atravessam os polos.</em>",
            "Segurança aparece em 33% das duas menções e saúde em 29%. Corrupção vem depois, com 18%. A posição muda quando se considera apenas a primeira resposta.",
            '<div class="issue-controls" hidden role="group" aria-label="Tipo de menção"><button data-issue-mode="2" aria-pressed="true">Duas menções</button><button data-issue-mode="0" aria-pressed="false">Só a primeira</button></div><div id="d-issues-chart">'
            + bars("Principais problemas / duas menções", initial)
            + '</div><script type="application/json" id="d-issues-data">'
            + json.dumps(problems["rows"], ensure_ascii=False)
            + "</script>"
            + note(
                "Pergunta espontânea e múltipla: cada entrevistado pode citar dois problemas. As menções não somam 100%; 33% é proporção que cita segurança em uma das duas posições, não um peso causal na decisão de voto."
            )
            + ref("nexus", 88)
            + table(
                ["Tema / duas menções", "Eleitores de Flávio", "Eleitores de Lula"],
                [
                    [name, str(values[0]) + "%", str(values[1]) + "%"]
                    for name, values in problems["by_vote"].items()
                ],
            )
            + "<p>Segurança tem presença semelhante nos dois eleitorados (34% e 32%), assim como saúde (26% e 31%). Corrupção, impostos e crescimento aparecem mais entre eleitores de Flávio; educação aparece mais entre eleitores de Lula. Isso descreve prioridades declaradas e sua associação com voto, sem demonstrar que um tema produziu a escolha.</p>"
            + ref("nexus", 90)
            + callout(
                "O diagnóstico desta rodada",
                "O núcleo de cada finalista declara alta retenção; a terceira via transfere votos de modo desigual e conserva parte sem candidato. O contraste econômico separa avaliação presente e expectativa futura. Segurança e saúde atravessam os campos. A renda revela clivagens importantes, mas ponderação pelo voto do 1º turno continua sem comprovação documental.",
            ),
        )
    )
    chapters.append(
        section(
            8,
            "metodo",
            "Como ler.<br><em>E o que ainda falta saber.</em>",
            "A consulta ao registro e as perguntas do relatório permitem identificar o que foi declarado. Não abrem todos os pesos internos.",
            methodology(d, "nexus")
            + callout(
                "A margem da diferença é outra conta",
                f'O instituto informa ±2 pp por percentual no total. Sob amostragem aleatória simples, a margem de 95% da diferença F−L seria aproximadamente ±{fmt(d["difference_margin_aas"],2)} pp para o placar 48% × 45%. É uma referência calculada, não intervalo com desenho validado; o efeito de desenho e os pesos completos não foram publicados.',
            )
            + "<p>A Nexus informa que a ordem temática do PDF difere da ordem da entrevista, cuja intenção de voto abre o instrumento para reduzir indução. Portanto, uma pergunta aparecer antes do voto no PDF não prova que veio antes no questionário. O instrumento registrado abriu no navegador com 12 páginas; não foi obtida exportação nesta conferência. As formulações e filtros analisados aqui são os publicados no relatório final.</p>"
            + ref("nexus", 4)
            + details(
                "Mapa das perguntas e limites de leitura",
                table(
                    ["Tema", "Página(s)", "Base / cuidado"],
                    [
                        [
                            "Interesse e escalas de polarização",
                            "6–14",
                            "Interesse não é comparecimento; clusters são derivados",
                        ],
                        [
                            "Presença declarada",
                            "15–18",
                            "Certa + provável não é taxa calibrada",
                        ],
                        [
                            "Espontânea, estimulada e válidos",
                            "20–23",
                            "Formatos e denominadores diferentes",
                        ],
                        [
                            "Transferências 2022 e 2026",
                            "24–32",
                            "Voto lembrado, bases dos grupos ausentes",
                        ],
                        [
                            "Firmeza, segunda opção, piso/teto",
                            "33–46",
                            "Filtros específicos; não adicionar pools sobrepostos",
                        ],
                        [
                            "Vitória, polarização e motivação",
                            "48–59",
                            "Percepção não é probabilidade; motivação por eleitorado",
                        ],
                        [
                            "Potencial e rejeição",
                            "61–70",
                            "Poderia votar não é voto medido",
                        ],
                        [
                            "Governo e aprovação",
                            "72–86",
                            "Escalas distintas, correlação com voto",
                        ],
                        ["Problemas do país", "88–90", "Duas menções espontâneas"],
                        [
                            "Economia presente, passada e futura",
                            "92–97",
                            "Horizontes distintos; não identificar causalidade",
                        ],
                    ],
                ),
            )
            + raw_tables(d, "nexus"),
        )
    )
    chapters.append(
        section(
            9,
            "fontes",
            "A evidência<br><em>fica aberta.</em>",
            "Confira o PDF, o registro, as tabelas e cada conta que sustenta a leitura.",
            sources(d, "nexus"),
        )
    )
    return frame(
        d,
        "nexus",
        "Duas lealdades.<br><em>Um país inquieto.</em>",
        "A 17ª rodada abre as transferências do 1º turno, a firmeza do voto, a presença declarada e a distância entre economia atual e expectativa futura. Flávio aparece numericamente à frente; a renda e os recortes mostram as nuances.",
        chapters,
        [
            (
                "As bases ficam; os demais divergem",
                "Retenção declarada de 98% dos dois finalistas. Cury, Caiado, Zema e Renan não transferem do mesmo modo.",
            ),
            (
                "O futuro não repete o presente",
                "54% esperam melhora da economia nacional; só 17% a avaliam bem hoje. Expectativa não equivale a apoio ao governo.",
            ),
            (
                "A ponderação precisa de evidência",
                "Renda e força de trabalho são declaradas no registro. Calibração pelo voto do 1º turno não está documentada nas fontes consultadas.",
            ),
        ],
    )
