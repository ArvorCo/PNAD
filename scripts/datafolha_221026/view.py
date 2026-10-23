"""Leitura editorial da íntegra, com cálculo aberto e fontes por afirmação."""

from html import escape

from dossies_2t_2026.view import (
    callout,
    details,
    explorer,
    fmt,
    income_section,
    note,
    raw_tables,
    section,
    stacks,
    stats,
    table,
)
from dossies_2t_2026.view import (
    ref as source_ref,
)
from ga_tag import injetar

PDF = "datafolha_22102026.pdf"


def ref(*pages):
    return source_ref("datafolha", *pages, pdf=PDF)


def rounding_section(d):
    r = d["rounding"]
    example = r["hypothetical_example"]
    return section(
        2,
        "arredondamento",
        "47 × 46 no total.<br><em>50 × 50 nos válidos?</em>",
        "É possível. Dividir números já arredondados não reproduz necessariamente a divisão feita antes do arredondamento.",
        table(
            ["Operação", "Flávio", "Lula", "O que representa"],
            [
                ["Total publicado", "47%", "46%", "Inteiros divulgados"],
                [
                    "Normalizar os inteiros: candidato ÷ 93",
                    "50,54%",
                    "49,46%",
                    "Conta do leitor com precisão já perdida",
                ],
                [
                    "Arredondar essa conta",
                    "51%",
                    "49%",
                    "Resultado da conta com os inteiros",
                ],
                [
                    "Válidos oficiais",
                    "50%",
                    "50%",
                    "Resultado publicado no relatório e no painel G1",
                ],
            ],
        )
        + "<p>Se 47 e 46 fossem os percentuais exatos, o arredondamento usual dos válidos seria 51 e 49. Mas o anexo declara que os percentuais já estão arredondados. Normalizar primeiro e arredondar depois pode produzir 50 e 50.</p>"
        + callout(
            "Uma demonstração, não os números secretos do instituto",
            f"Imagine valores de 46,80% e 46,49%, com 5,20% de branco/nulo e 1,51% de indecisos. Eles somam 100% e aparecem como 47/46/5/2. Entre os candidatos, dão {fmt(example['validos'][0],3)}% e {fmt(example['validos'][1],3)}%. Ambos arredondam para 50%. Esse exemplo é construído para demonstrar compatibilidade; não recupera os dados internos.",
        )
        + '<div class="rounding-lab"><h3>Experimente antes de arredondar</h3><p>Valores hipotéticos em porcentagem do total. Os controles ficam dentro das faixas que aparecem como 47 e 46.</p><div class="lab-inputs"><label>Flávio <output id="round-f-label">46,80%</output><input id="round-f" type="range" min="46.50" max="47.49" step="0.01" value="46.80"></label><label>Lula <output id="round-l-label">46,49%</output><input id="round-l" type="range" min="45.50" max="46.49" step="0.01" value="46.49"></label></div><div id="round-result" aria-live="polite"><b>50,166% × 49,834%</b><p>Nos válidos, ambos arredondam para 50%.</p></div><p class="note">O restante fica em branco/nulo e indecisos. O exercício verifica somente a relação entre os dois candidatos e os seus inteiros publicados.</p></div>'
        + "<p><b>O que falta:</b> percentuais com casas decimais, numeradores ponderados e regra de arredondamento. Sem isso, a conta exata não é reproduzível. O par 47/46, sozinho, admite valores de Flávio entre pouco mais de 50% e pouco menos de 51,08% dos válidos, sob arredondamento usual. Portanto, admite tanto 50/50 quanto 51/49. Não demonstra que os números foram alterados para fabricar empate.</p>"
        + "<p><b>Empate arredondado e empate técnico são coisas diferentes.</b> O primeiro trata das casas decimais exibidas. O segundo trata da incerteza da estimativa: nem um 51/49 arredondado bastaria para demonstrar liderança estatística nesta amostra.</p>"
        + ref(5, 9, 27, 28)
        + details(
            "Duas bases nos votos válidos",
            "<p>A apresentação, p. 9, escreve <b>2.347 entrevistas</b>. O anexo, p. 28, escreve <b>base ponderada 2.351</b>. A natureza ponderada só está explícita no anexo. As duas bases não são intercambiáveis, e nenhuma permite recuperar as contagens ponderadas de cada candidato. Não transformamos essa diferença em quatro entrevistas desaparecidas.</p>"
            + ref(9, 22, 28),
        ),
    )


def quota_section(d):
    q = d["quota"]
    margin = d["difference_aas_margin_pp"]
    registry = (
        '<a href="fontes/datafolha_22102026_registro.txt">registro BR-09709/2026</a>'
    )
    plan = '<a href="fontes/datafolha_22102026_plano_amostral.txt">detalhamento do plano amostral</a>'
    return section(
        3,
        "cotas",
        "As cotas começam<br><em>antes da planilha.</em>",
        "O próprio Datafolha declara ao TSE que gênero e idade orientam a seleção de quem será entrevistado. Isso acontece no campo, antes da ponderação posterior.",
        f"<p>No {plan}, o instituto classifica o desenho como <b>misto</b>: probabilístico em algumas etapas e não probabilístico em outras. Informa que conhece as probabilidades de seleção apenas em parte das etapas e identifica o componente não probabilístico como amostragem estratificada por cotas.</p>"
        + '<ol class="field-steps"><li><b>Dividir o território.</b> Estratos por região e natureza do município.</li><li><b>Sortear os locais.</b> Municípios com probabilidade proporcional ao tamanho; depois bairros e pontos de abordagem.</li><li><b>Selecionar as pessoas por cotas.</b> O registro descreve abordagem aleatória condicionada às cotas de gênero e idade.</li><li><b>Ponderar depois.</b> Ajustes previstos por estrato, gênero e idade; escolaridade pode receber ajuste sob o critério declarado.</li></ol>'
        + f"<p>O {registry} informa que os entrevistadores são treinados e recebem instruções específicas por projeto, com checagem de ao menos 20% dos questionários de cada pesquisador. Portanto, as cotas não surgem apenas quando alguém calcula pesos: integram o protocolo de recrutamento. Esses controles não equivalem a uma probabilidade conhecida de inclusão para cada eleitor.</p>"
        + callout(
            "Onde está o problema metodológico",
            "Preencher uma cota torna a amostra semelhante ao eleitorado nas variáveis controladas. Não garante semelhança dentro de cada grupo. Duas pessoas da mesma idade e gênero podem ter rendas, rotinas e preferências diferentes. Passar pelo ponto, no horário da coleta, estar disponível e aceitar a entrevista continuam podendo afetar quem entra. O tamanho e o sentido desse efeito não são identificados pelas tabelas públicas.",
        )
        + "<p>Pense em duas mulheres da mesma idade: uma trabalha longe durante o horário da entrevista, outra passa pelo ponto selecionado. A cota demográfica pode estar preenchida sem que as duas tenham a mesma chance de entrar. É uma ilustração do mecanismo possível, não uma observação sobre estas entrevistadas.</p>"
        + table(
            ["Variável", "Na seleção em campo", "No processamento declarado"],
            [
                ["Gênero e idade", "Cotas explícitas", "Ponderação prevista"],
                [
                    "Região e natureza do município",
                    "Estratificação territorial",
                    "Ponderação prevista",
                ],
                [
                    "Escolaridade",
                    "Não listada como cota no plano consultado",
                    "Ajuste possível segundo critério do registro",
                ],
                [
                    "Renda",
                    "Não listada como cota no plano consultado",
                    "Referência 49/47/4; fator previsto 1",
                ],
            ],
        )
        + "<p><b>Não há base documental para dizer que o entrevistador recebe uma cota de 49% de pobres.</b> O registro trata 49% até 2 SM, 47% acima e 4% sem resposta como referência de renda; declara fator previsto igual a 1, associado aos resultados de campo. Isso não prova que o perfil final por renda seja bruto: pesos de outras variáveis também podem alterá-lo.</p>"
        + details(
            "Uma diferença entre o plano e a base final que precisa ser explicada",
            table(
                ["Gênero", "Cota registrada", "Base ponderada final", "% do total"],
                [
                    ["Homens", "47%", "1.239", fmt(q["male_weighted_pct"], 2) + "%"],
                    [
                        "Mulheres",
                        "53%",
                        "1.281",
                        fmt(q["female_weighted_pct"], 2) + "%",
                    ],
                ],
            )
            + "<p>A diferença de 2,17 pontos no perfil masculino não se explica apenas pelo arredondamento de 47 para um inteiro. Mas estamos comparando meta registrada com base ponderada final. Sem o perfil bruto, tolerâncias de cota, pesos e relatório de execução, não sabemos se a origem está no campo, nos pesos ou na descrição do plano. É um pedido objetivo de reconciliação, não prova de violação no recrutamento.</p>"
            + ref(27),
        )
        + details(
            "Por que ±2 pontos não resolve o desenho",
            f"<p>O registro informa que a margem de ±2 pp é baseada em amostra aleatória simples. O plano detalhado, porém, declara desenho misto. Sob AAS, usando os inteiros divulgados como aproximação, a margem de 95% da <b>diferença</b> F−L seria ±{fmt(margin,2)} pp, levando o saldo de +1 a aproximadamente [{fmt(1-margin,2)}; +{fmt(1+margin,2)}]. Essa conta didática não incorpora conglomerados, pesos ou seleção por cotas, nem estima o viés de cobertura. Não é um intervalo validado para o desenho efetivo.</p>"
            + "<p>Para auditar a precisão real faltam probabilidades nas etapas aplicáveis, estratos e conglomerados, pesos, tamanho efetivo e hipótese ou modelo usado na etapa não probabilística. Cotas são uma técnica de controle; não são, por si, evidência de fraude.</p>",
        )
        + note(
            f"Fonte: {registry} e {plan}, transcrições de consulta em 22/10/2026. Declarações do instituto no sistema do TSE, não certificação metodológica pelo tribunal."
        ),
    )


def questions_section(d):
    tables = d["tables"]

    def chart(key):
        row = tables[key]["segments"]["total"]["responses"]
        return stacks(
            tables[key]["title"], {"Total": list(row.values())}, list(row)
        ) + ref(tables[key]["page"])

    return section(
        5,
        "perguntas",
        "A pergunta muda.<br><em>A base também.</em>",
        "O anexo abre dez perguntas em onze tabelas, cada uma com 31 recortes. Certeza de voto em cada candidato ocupa duas tabelas.",
        stats(
            [
                (
                    fmt(d["denominators"]["certain_all_pct"], 2) + "%",
                    "voto firme reexpresso sobre toda a amostra",
                ),
                ("2.482", "base ponderada da pergunta sobre decisão"),
                ("2.351", "base ponderada de motivação e votos válidos"),
            ]
        )
        + "<p>Os 94% totalmente decididos usam quem declarou candidato ou branco/nulo, não todos os 2.520 entrevistados. Reexpressos sobre o total, são aproximadamente 92,58%. A motivação usa só quem declarou candidato. Certeza declarada não é comparecimento observado.</p>"
        + ref(29, 33)
        + chart("espontanea")
        + "<p>Na espontânea, Flávio tem 46% e Lula 45%; na estimulada, 47% e 46%. A mudança de pergunta reduz os indecisos de 4% para 2%. Isso não mede uma migração entre datas.</p>"
        + ref(26, 27)
        + chart("rejeicao")
        + "<p>A rejeição exclusiva é 46% a Flávio e 45% a Lula; 3% rejeitam ambos. Não confundir rejeição exclusiva, rejeição individual e intenção de voto. Somar inteiros de perguntas diferentes pode não reproduzir o inteiro da outra tabela, por arredondamento.</p>"
        + ref(30, 31, 32)
        + chart("motivacao")
        + chart("avaliacao")
        + chart("aprovacao")
        + chart("expectativa")
        + "<p>A expectativa de vitória é 53% para Flávio e 39% para Lula. Ela mede quem o entrevistado acha que ganhará; não é intenção de voto, previsão calibrada ou probabilidade de vitória.</p>"
        + explorer(d, "datafolha", pdf=PDF)
        + raw_tables(d, "datafolha", pdf=PDF),
    )


def render(d):
    turn = d["reweight"]["turn"]
    adjusted = turn["cenarios"]["pessoas16_efetivo"]["ajustado"]
    pnad = d["reweight"]["profile"]["pnad_pct"]["pessoas16_efetivo"]
    bases = [1171, 913, 341]
    rows = [
        [
            label,
            str(n),
            fmt(100 * n / 2425, 2) + "%",
            fmt(w, 2) + "%",
            str(flavio) + "%",
            str(lula) + "%",
        ]
        for label, n, w, flavio, lula in zip(
            ["Até 2 SM", "2–5 SM", ">5 SM"],
            bases,
            pnad,
            [39, 54, 54],
            [54, 39, 40],
            strict=True,
        )
    ]
    chapters = [
        section(
            1,
            "renda",
            "A íntegra chegou.<br><em>A renda continua pesando.</em>",
            "A revisão substitui as bases emprestadas de 15/10 pelas bases atuais. O ajuste de composição quase não muda, mas agora tem documentação da própria onda.",
            income_section(d, "datafolha")
            + table(
                [
                    "Faixa",
                    "Base ponderada",
                    "Entre quem informou renda",
                    "PNAD 2025",
                    "Flávio",
                    "Lula",
                ],
                rows,
            )
            + "<p>As bases somam <b>2.425 de 2.520</b>. A cobertura é 96,23%; os 95 restantes conservam o placar publicado. A conta troca somente a margem de renda: <b>publicado + (2.425/2.520) × (PNAD − recomposto)</b>. O perfil entre declarantes não é o mesmo percentual sobre toda a amostra.</p>"
            + table(
                ["Etapa / % do total ou do grupo indicado", "Flávio", "Lula"],
                [
                    ["Publicado / toda a amostra", "47,00", "46,00"],
                    [
                        "Recomposto / declarantes de renda",
                        fmt(turn["recomposto"]["flavio"], 3),
                        fmt(turn["recomposto"]["lula"], 3),
                    ],
                    [
                        "Soma direta com PNAD / declarantes",
                        fmt(
                            turn["cenarios"]["pessoas16_efetivo"]["contrafactual"][
                                "flavio"
                            ],
                            3,
                        ),
                        fmt(
                            turn["cenarios"]["pessoas16_efetivo"]["contrafactual"][
                                "lula"
                            ],
                            3,
                        ),
                    ],
                    [
                        "Sensibilidade ancorada / toda a amostra",
                        fmt(adjusted["flavio"], 3),
                        fmt(adjusted["lula"], 3),
                    ],
                ],
            )
            + "<p>A soma direta não substitui a estimativa ancorada: ela se refere aos declarantes e inclui resíduos dos inteiros. A régua principal usa PNADC anual 2025, visita 1, renda domiciliar efetiva para pessoas de 16 anos ou mais. A pergunta do Datafolha é de renda familiar declarada; as definições não são idênticas.</p>"
            + callout(
                "O que esta conta não conserta",
                "Trocar a distribuição de renda não identifica o voto das pessoas que ficaram fora dos pontos de fluxo, não reconstrói todos os pesos e não elimina possível seleção dentro das faixas. O resultado é uma sensibilidade explícita, não voto corrigido nem previsão da urna.",
            )
            + ref(22, 24, 27),
        ),
        rounding_section(d),
        quota_section(d),
        section(
            4,
            "presenca",
            "Quem votou antes<br><em>é outro recorte.</em>",
            "Entre quem declara ter votado no primeiro turno, o Datafolha publica 51% × 49% dos válidos. No conjunto, publica 50% × 50%.",
            "<p>A diferença vem de restringir o universo, não de recalcular 47/93. Voto lembrado no primeiro turno não determina quem comparecerá no segundo. Sem base e cruzamento completos desse recorte, não reconstruímos a contribuição dos ausentes nem transportamos o 51/49 para a central.</p>"
            + stacks(
                "Voto atual de quem declarou Cury, Renan, Caiado ou Zema no primeiro turno",
                {"Terceira via agregada": [47, 26, 21, 6]},
                ["Flávio", "Lula", "Branco/nulo", "Indecisos"],
            )
            + "<p>A transferência é declarada e agregada: 47% para Flávio, 26% para Lula, 21% branco/nulo e 6% indecisos. Sem a base ponderada desse grupo, não convertemos os percentuais em pontos nacionais. A apresentação também informa 77% decididos e 23% que podem mudar nesse grupo.</p>"
            + "<p>O relatório traz 48% × 45% entre quem mora perto do local de votação e 43% × 51% entre quem mora longe ou em outra cidade, sempre Flávio × Lula. São associações publicadas; não identificam causalidade da distância nem voto dos futuros ausentes. Faltam os tamanhos dos grupos para recompor o país.</p>"
            + ref(5),
        ),
        questions_section(d),
    ]
    control_rows = [
        [escape(key), escape(dim), fmt(c["max_residual_pp"], 3) + " pp"]
        for key, groups in d["controls"].items()
        for dim, c in groups.items()
    ]
    chapters.append(
        section(
            6,
            "fontes",
            "A conta fica aberta.<br><em>As fontes também.</em>",
            "Divulgação em 22/10; íntegra publicada e conferida em 23/10/2026. Registro e plano amostral consultados em 22/10, com a data da consulta preservada.",
            '<div class="downloads"><a href="fontes/datafolha_22102026.pdf">Íntegra · 36 páginas</a><a href="assets/datafolha_22102026_data.json">Dados e contas</a><a href="fontes/datafolha_22102026_registro.txt">Registro TSE</a><a href="fontes/datafolha_22102026_plano_amostral.txt">Plano amostral TSE</a><a href="reponderacao_pnad.html">Centrais Arvor</a><a href="datafolha_08102026.html">Dossiê de 08/10</a></div>'
            + f'<p>Fonte original: <a href="{escape(d["source"]["url"])}">PDF no domínio oficial do Datafolha</a>. SHA-256: <code>{d["pdf_sha256"]}</code>.</p>'
            + details(
                "Recomposição independente de todas as tabelas",
                table(["Tabela", "Dimensão", "Maior resíduo absoluto"], control_rows)
                + note(
                    "Controles por sexo, idade e região usam bases ponderadas da própria pergunta. Resíduos são diferenças aritméticas decorrentes dos números publicados; não são margens de erro nem validação do recrutamento."
                ),
            )
            + "<p>Preservamos o 50/50 oficial, os totais 47/46/5/2 e o cálculo dos válidos a partir dos inteiros como objetos diferentes. Bases ponderadas não são contagens brutas. Zero impresso pode representar uma parcela positiva arredondada; traços permanecem sem valor. A revisão não altera versões congeladas anteriores.</p>"
            + "<p>Para completar a auditoria: publicar percentuais não arredondados, pesos e limites, perfil bruto e ponderado, execução e tolerâncias das cotas, recusas por ponto/horário e documentação da precisão no desenho misto. Não se localizou declaração de calibração pelo voto do primeiro turno nas fontes consultadas; isso não identifica todos os procedimentos internos.</p>",
        )
    )
    summary = "Íntegra de 36 páginas: renda atual, a conta do 47 × 46 e 50 × 50, cotas na seleção em campo e dez perguntas com suas bases."
    url = "https://brasil.arvor.co/datafolha_22102026.html"
    nav = "".join(
        f'<a href="#{key}">{label}</a>'
        for key, label in [
            ("renda", "Renda"),
            ("arredondamento", "Arredondamento"),
            ("cotas", "Cotas no campo"),
            ("presenca", "Presença"),
            ("perguntas", "Perguntas"),
            ("fontes", "Fontes"),
        ]
    )
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Datafolha 22/10/2026: renda, arredondamento e cotas | Arvor</title>
<meta name="description" content="{summary}"><link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="Datafolha: dois placares, uma pesquisa"><meta property="og:description" content="{summary}"><meta property="og:url" content="{url}"><meta property="og:image" content="https://brasil.arvor.co/img/og/datafolha_22102026.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/datafolha_22102026.png">
<link rel="stylesheet" href="assets/dossies_2t_2026.css"><link rel="stylesheet" href="assets/datafolha_22102026.css"><script src="assets/dossies_2t_2026.js" defer></script><script src="assets/datafolha_22102026.js" defer></script></head>
<body class="datafolha"><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html"><img src="img/arvor_logo.png" alt="Arvor Intelligence">Arvor / Brasil</a><span>Dossiê de pesquisa · 2º turno</span><a href="datafolha_08102026.html">Dossiê anterior ↗</a></header>
<main id="conteudo"><section class="hero"><div class="hero-copy"><p class="eyebrow">Datafolha · 22 de outubro de 2026 · íntegra conferida em 23/10</p><h1>Dois placares.<br><em>Uma pesquisa.</em></h1><p class="deck">{summary} A renda continua sendo a principal sensibilidade: com a régua PNAD, {fmt(adjusted['flavio'],2)}% × {fmt(adjusted['lula'],2)}% no total.</p><div class="hero-meta"><span>Campo 20–22/10</span><span>2.520 entrevistas · 154 municípios</span><span>BR-09709/2026</span></div></div><aside class="hero-result"><p>Publicado / Flávio × Lula</p><b>47 × 46</b><span>sobre o total de entrevistados</span><div><strong>50% × 50%</strong><span>votos válidos oficiais</span></div><p class="hero-foot">Branco/nulo: 5% · Indecisos: 2%<br>Entrevistas presenciais em pontos de fluxo<br>Margem informada: ±2 pp / total</p></aside></section>
<nav class="chapter-nav" aria-label="Capítulos">{nav}</nav><div class="reading"><p class="eyebrow">O diagnóstico em três pontos</p><div><article><span>01</span><h3>Renda atual</h3><p>As bases 1.171/913/341 substituem a hipótese emprestada. Os 95 sem renda ficam fora do ajuste.</p></article><article><span>02</span><h3>Arredondar tem ordem</h3><p>47/93 dá 50,54%. Isso não recupera os decimais anteriores ao arredondamento.</p></article><article><span>03</span><h3>Cotas já no campo</h3><p>O registro descreve a seleção por gênero e idade. A renda não aparece como cota declarada.</p></article></div></div>
{''.join(chapters)}</main><footer><a href="index.html">Arvor / Biblioteca</a><p>Fontes, cálculos e hipóteses separados. Sensibilidade de composição não é previsão eleitoral.</p><a href="reponderacao_pnad.html">Centrais e cenários</a></footer></body></html>"""
    return injetar(html.replace("<section ", "\n<section ")) + "\n"
