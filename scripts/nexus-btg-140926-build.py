#!/usr/bin/env python3
"""Build the Nexus September dossier from auditable data and static figures."""

from __future__ import annotations

import importlib.util
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "docs/assets/nexus_btg_140926_data.json").read_text())
spec = importlib.util.spec_from_file_location(
    "figures", ROOT / "scripts/nexus-btg-140926-figures.py"
)
fig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig)
R = D["reweight"]


def num(v, digits=2):
    return f"{v:.{digits}f}".replace(".", ",")


def ref(*pages):
    return (
        ' <span class="refs">'
        + " · ".join(
            f'<a href="fontes/nexus_btg_140926.pdf#page={p}">p. {p}</a>' for p in pages
        )
        + "</span>"
    )


def tab(headers, rows):
    return (
        '<div class="table-scroll" tabindex="0"><table><thead><tr>'
        + "".join(f'<th scope="col">{h}</th>' for h in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>"
            + "".join(
                f'<{"th scope=row" if i==0 else "td"}>{v}</{"th" if i==0 else "td"}>'
                for i, v in enumerate(row)
            )
            + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def figure(svg, caption):
    return f'<figure><div class="chart-scroll" tabindex="0">{svg}</div><figcaption>{caption}</figcaption></figure>'


def section(slug, number, title, lead, content):
    return f'<section id="{slug}"><div class="section-head"><span class="kicker">{number} / DOSSIÊ</span><h2>{title}</h2><p class="lead">{lead}</p></div>{content}</section>'


def adj(ballot, scenario="pessoas16_efetivo"):
    return R["turnos"][ballot]["cenarios"][scenario]["ajustado"]


sections = []
sections.append(
    section(
        "renda",
        "01",
        "A renda encurta a diferença.<br><em>O sinal permanece.</em>",
        f'O segundo turno publicado marca Lula 47% e Flávio 46%. Com a distribuição de renda da PNAD, passa a {num(adj("2t")["lula"])}% e {num(adj("2t")["flavio"])}%. A diferença cai de um ponto para {num(adj("2t")["lula"]-adj("2t")["flavio"])}. É sensibilidade a uma margem, sem liderança estatisticamente identificada.'
        + ref(76, 152),
        figure(
            fig.income(D),
            "Régua comum do agregador Arvor: PNADC anual 2025, visita 1, pessoas de 16 anos ou mais; renda domiciliar efetiva, peso V1032. Valores monetários compatibilizados com abril/2026. Perfil da Nexus na p. 152.",
        )
        + "<p>A amostra publicada tem 19% até um salário mínimo; a régua devolve 13,44%. Mas a faixa seguinte está abaixo da PNAD: 18% contra 21,75%. Até dois salários, a diferença agregada é apenas 37% contra 35,19%. O desvio na primeira faixa não pode ser apresentado como desvio de todo o bloco de baixa renda.</p>"
        + "<p><strong>A crítica antiga não serve automaticamente.</strong> A metodologia já declara PNAD anual 2025, primeira visita, e TSE de junho/2026. Declarar a mesma pesquisa de referência não determina renda familiar, universo, tratamento de ausência de renda nem distribuição conjunta dos pesos. Renda nem aparece na lista de cotas de controle. O nosso exercício troca o perfil publicado, sem alegar que o instituto usou PNAD velha."
        + ref(4)
        + "</p>"
        + tab(
            ["Cenário", "Lula 1º", "Flávio 1º", "Lula 2º", "Flávio 2º", "Dif. 2º L−F"],
            [["Publicado", "42,00", "37,00", "47,00", "46,00", "+1,00"]]
            + [
                [
                    name,
                    num(adj("1t", key)["lula"]),
                    num(adj("1t", key)["flavio"]),
                    num(adj("2t", key)["lula"]),
                    num(adj("2t", key)["flavio"]),
                    num(adj("2t", key)["lula"] - adj("2t", key)["flavio"]),
                ]
                for key, name in [
                    ("pessoas16_efetivo", "Pessoas 16+, efetivo (principal)"),
                    ("pessoas16_habitual", "Pessoas 16+, habitual"),
                    ("domicilios_efetivo", "Domicílios, efetivo (outro universo)"),
                ]
            ],
        )
        + "<aside><b>O resultado contrário à hipótese está aqui.</b> A PNAD habitual deixa só 0,06 ponto a favor de Lula. O universo de domicílios amplia a diferença para 2,30 pontos, mas cada casa não é um eleitor. Nenhuma dessas linhas é uma previsão ou uma correção oficial da Nexus.</aside>",
    )
)

proof = []
for i, label in enumerate(["Até 1 SM", "1 a 2 SM", "2 a 5 SM", "Mais de 5 SM"]):
    row = D["poll"]["cruzamentos"]["2t"]["linhas"][i]
    w = R["renda"]["amostra_pct"][i]
    target = R["renda"]["pnad_pct"]["pessoas16_efetivo"][i]
    proof.append(
        [
            label,
            num(w),
            num(target),
            str(row[0]),
            str(row[1]),
            num(w * row[0] / 100),
            num(w * row[1] / 100),
        ]
    )
sections.append(
    section(
        "conta",
        "02",
        "A conta fica aberta.",
        "Antes de trocar os pesos, o cruzamento precisa reproduzir o placar da própria Nexus. Renda, sexo e escolaridade passam por controles independentes.",
        tab(
            [
                "Faixa",
                "Peso Nexus %",
                "Peso PNAD %",
                "Lula %",
                "Flávio %",
                "Contrib. Lula",
                "Contrib. Flávio",
            ],
            proof,
        )
        + '<div class="formula">ajustado = publicado + (média com PNAD − média com Nexus)</div>'
        + "<p>O cruzamento de renda recompõe 47,35% para Lula e 45,72% para Flávio, contra 47% e 46% publicados. A média com a PNAD dá 47,04% e 46,12%. Somamos apenas a diferença entre as duas médias ao placar publicado. Assim, o arredondamento da tabela não é promovido a mudança de voto."
        + ref(76, 152)
        + "</p>"
        + tab(
            ["Controle independente", "Lula 1º", "Flávio 1º", "Lula 2º", "Flávio 2º"],
            [
                [
                    k.title(),
                    num(D["independent_controls"]["1t"][k][0]),
                    num(D["independent_controls"]["1t"][k][1]),
                    num(D["independent_controls"]["2t"][k][0]),
                    num(D["independent_controls"]["2t"][k][1]),
                ]
                for k in ["sexo", "escolaridade"]
            ],
        )
        + "<p>Os resíduos máximos dos candidatos na renda são 0,55 ponto no primeiro turno e 0,35 no segundo. Sexo e escolaridade também recompõem os finalistas com menos de um ponto de resíduo. Os dados são extraídos por programa das tabelas, com rótulo, página e número de colunas conferidos."
        + ref(33, 34, 75, 76, 152)
        + "</p>"
        + f'<p><strong>Arredondamento não é incerteza amostral.</strong> Mantendo placar e pesos fixos, variar cada célula dos dois candidatos em até ±0,5 ponto altera a diferença ajustada em no máximo {num(D["rounding_gap_bound_pp"])} ponto. Esse limite não inclui arredondamento dos perfis ou do placar, erro de amostragem, renda omitida ou efeito do desenho.</p>'
        + f'<p>O histograma usa caixas de R$ 10 e interpola os cortes. O cartão desta rodada não foi obtido; usamos a continuidade dos salários de 2026 conferida em questionários anteriores. O último IPCA local é {D["income_latest_ipca_month"][:4]}-{D["income_latest_ipca_month"][4:]}; o motor mantém o último índice para meses posteriores. O alvo preserva a comparação com o <a href="reponderacao_pnad.html">agregador</a>. Renda familiar declarada e rendimento domiciliar efetivo não são conceitos idênticos.</p>'
        + "<p>As linhas impressas nem sempre somam 100. O agregador preserva as células e ancora cada opção no seu percentual publicado; por isso a linha ajustada completa pode somar ligeiramente diferente de 100. Não normalizamos apenas este dossiê para produzir um número diferente da série comum.</p>",
    )
)

history_rows = []
for p in D["history"]:
    a = p["turnos"]["1t"]
    b = p["turnos"]["2t"]
    av = a["cenarios"]["pessoas16_efetivo"]["ajustado"]
    bv = b["cenarios"]["pessoas16_efetivo"]["ajustado"]
    history_rows.append(
        [
            p["divulgacao"][8:] + "/" + p["divulgacao"][5:7],
            f'{a["publicado"]["lula"]:g} × {a["publicado"]["flavio"]:g}',
            f'{num(av["lula"])} × {num(av["flavio"])}',
            f'{b["publicado"]["lula"]:g} × {b["publicado"]["flavio"]:g}',
            f'{num(bv["lula"])} × {num(bv["flavio"])}',
            num(bv["lula"] - bv["flavio"]),
        ]
    )
sections.append(
    section(
        "historico",
        "03",
        "A recuperação tem dois lados.",
        "De 8 para 14 de setembro, Lula sobe três pontos no primeiro turno e dois no segundo. Flávio sobe dois no primeiro e fica em 46% no segundo. Cury cai de 9% para 6%; Renan, de 4% para 2%. São oscilações entre amostras, sem rastreamento de pessoas."
        + ref(21, 53),
        figure(
            fig.history(D),
            "Série publicada na rodada atual, sem misturar o cenário com Pablo Marçal ao cenário principal. A tabela abaixo usa o cruzamento de renda próprio de cada onda; março e abril ficam sem reponderação por ausência desses insumos no agregador.",
        )
        + tab(
            [
                "Divulgação",
                "1º publicado L×F",
                "1º PNAD L×F",
                "2º publicado L×F",
                "2º PNAD L×F",
                "Dif. PNAD 2º",
            ],
            history_rows,
        )
        + "<p>Na régua comum, o segundo turno de 8/9 era 44,55% × 46,65%; agora é 46,69% × 46,40%. A mudança não desaparece ao fixar o critério de renda. A distribuição publicada 19/18/40/23 permanece igual: nesta comparação, o movimento vem dos votos dentro das faixas e do placar de referência, não da troca desse perfil.</p>"
        + "<p>Não confundimos a série comum com os números de um dossiê antigo: versões anteriores usaram normalização das linhas e alvos próprios. Aqui, todas as ondas passam pelo mesmo motor do agregador, com seus cruzamentos originais. A série publicada retrocede a março; a reponderada começa em maio.</p>",
    )
)

transfer_rows = []
for name, row in D["transfer"]["published_conditional"].items():
    transfer_rows.append([name, *[str(v) + "%" for v in row], str(sum(row)) + "%"])
transfer_detail = []
for i, row in enumerate(D["transfer"]["matrix"]):
    transfer_detail.append(
        [
            D["transfer"]["sources"][i],
            *map(num, row),
            (
                "medido, normalizado"
                if i in D["transfer"]["measured_rows"]
                else (
                    "base consolidada por hipótese"
                    if i in D["transfer"]["consolidated_rows"]
                    else "estimado"
                )
            ),
        ]
    )
sections.append(
    section(
        "transferencia",
        "04",
        "Cinco origens medidas.<br><em>Duas bases consolidadas.</em>",
        "O relatório publica o destino no segundo turno de quem escolheu Cury, Caiado, Renan, Zema e Samara no primeiro. Não publica as linhas de Lula, Flávio, branco/nulo e indecisos. Neste diagrama, Lula e Flávio retêm integralmente suas bases por hipótese. Só as origens branco/nulo e indecisos são estimadas, com as margens como restrição."
        + ref(20, 52, 74),
        figure(
            fig.sankey(D),
            "O diagrama fecha 100 pontos em cada lado. As cinco linhas publicadas entram fixas depois de normalizadas: Cury soma 101% e Renan soma 99%. As fitas sólidas sem contorno identificam as cinco origens medidas. O contorno pontilhado marca as duas bases fixadas por hipótese; a hachura marca as duas origens estimadas por IPF.",
        )
        + '<p class="flow-readout" id="flow-caption" aria-live="polite">Selecione uma fita para ler origem, destino e volume.</p>'
        + tab(
            ["Origem no 1º", "Lula", "Flávio", "B/N", "NS/NR", "Soma impressa"],
            transfer_rows,
        )
        + f'<p>As cinco candidaturas somam 15% no primeiro turno. Seus cruzamentos entregam <strong>{num(D["transfer"]["pool_points"][1])} pontos a Flávio</strong>, {num(D["transfer"]["pool_points"][0])} a Lula e {num(sum(D["transfer"]["pool_points"][2:]))} à não escolha. A razão Flávio/Lula é {num(D["transfer"]["pool_ratio_flavio_lula"])} para 1. Com as bases integralmente retidas, o restante do ganho dos finalistas vem da não escolha inicial neste modelo.</p>'
        + "<p>Cury sozinho fornece cerca de 2,50 pontos a Flávio e 2,02 a Lula. Caiado fornece 2,65 e 1,50. Somar toda a terceira via como reserva exclusiva de Flávio contradiz a própria matriz da Nexus."
        + ref(74)
        + "</p>"
        + "<details><summary>Ver matriz completa e escolhas do modelo</summary>"
        + tab(
            [
                "Origem",
                "Lula (pp)",
                "Flávio (pp)",
                "B/N (pp)",
                "NS/NR (pp)",
                "Natureza",
            ],
            transfer_detail,
        )
        + "<p>As bases de Lula e Flávio têm retenção fixada em 100%, com zero estrutural em todos os outros destinos. É uma hipótese de consolidação, não uma medição da Nexus. As duas linhas ficam fora do IPF. Branco/nulo parte de 15/15/67/3; indecisos, de 20/20/20/40. IPF/RAS ajusta só o resíduo até fechar as margens. Testamos mais duas priors para as origens branco/nulo e indecisos, mantendo as bases fixadas; o JSON guarda todos os resultados. As porcentagens internas estimadas não são medição de fidelidade.</p>"
        + "<p>O 1% de “Outros” é representado por Samara, que também tem 1% na tabela nominal; candidaturas com 0% impresso ficam fora. Arredondamento pode ocultar massas pequenas. A matriz descreve agregados da pesquisa, não trajetórias individuais entre eleições. Sem renda × candidato de origem × destino, não existe Sankey PNAD identificado: não aplicamos o peso de renda às fitas como se essa tabela tivesse sido publicada.</p></details>",
    )
)

bounds = D["useful_vote_bounds"]
sections.append(
    section(
        "voto-util",
        "05",
        "Há espaço para voto útil.<br><em>Não há prova de migração consumada.</em>",
        "Flávio precisa acrescentar nove pontos líquidos entre os dois cenários: 37% para 46%. Lula acrescenta cinco: 42% para 47%. A razão de consolidação líquida é 1,80 para 1, contra 1,83 na rodada anterior. A assimetria já estava no segundo turno."
        + ref(21, 53),
        "<p>Se um eleitor que já escolhe Flávio no segundo turno antecipar essa escolha ao primeiro, o primeiro turno cresce sem alteração mecânica do segundo. O movimento observado de Flávio, +2 no primeiro e zero no segundo, é compatível com isso. Mas amostras repetidas não identificam quem mudou, a origem, nem a causa. Lula também cresceu; a soma de ambos no primeiro foi de 74% para 79%.</p>"
        + tab(
            ["Pergunta/recorte", "Resultado", "O que permite concluir"],
            [
                [
                    "Pode mudar o voto?",
                    "17% entre quem escolheu candidato; 83% decidido" + ref(35),
                    "Não são 17% de todo o eleitorado.",
                ],
                [
                    "Certeza por candidato",
                    "Lula 89%; Flávio 86%; Cury 65%; Caiado 48%; Zema 30%" + ref(38),
                    "Decisão declarada não é garantia de voto.",
                ],
                [
                    "Segunda escolha dos que podem mudar",
                    "Cury 17%; Lula 14%; Caiado 13%; Flávio 12%; Renan 9%; Zema 7%"
                    + ref(41),
                    "A segunda escolha não favorece exclusivamente Flávio.",
                ],
                [
                    "Pisos e tetos publicados",
                    "Lula 38–44%; Flávio 32–39%; Cury 4–9%" + ref(43),
                    "Contas de cenário, sem intervalo probabilístico.",
                ],
                [
                    "Certeza no segundo turno",
                    "Lula 91%; Flávio 90%" + ref(56),
                    "Não confundir com fidelidade de base do primeiro para o segundo.",
                ],
                [
                    "Segunda escolha no segundo turno",
                    "B/N 42%; Lula 22%; Flávio 18%; NS 18%, entre os 11% que podem mudar"
                    + ref(58),
                    "Parte da abertura termina em não escolha.",
                ],
            ],
        )
        + "<p>Aproximadamente 94% escolheram candidato. Logo, 94% × 17% ≈ 15,98% do eleitorado declara voto ainda mutável. Aplicar os 12% que citam Flávio como segunda escolha dá cerca de <strong>1,92 ponto</strong>, uma entrada bruta hipotética. Sua própria base tem 13% que pode mudar, cerca de 4,81 pontos. Não se deve somar a entrada e ignorar a possível saída."
        + ref(38, 41, 46)
        + "</p>"
        + "<h3>Duas perguntas não publicam a interseção</h3><p>Por candidato, sabemos a fração que pode mudar e a que escolhe Flávio no segundo turno. Não sabemos quantos pertencem às duas ao mesmo tempo. Os limites de Fréchet dão o intervalo matematicamente possível, sem supor independência.</p>"
        + tab(
            [
                "Origem",
                "1º turno %",
                "Pode mudar %",
                "Flávio no 2º %",
                "Interseção mínima (pp)",
                "Máxima (pp)",
            ],
            [
                [
                    b["candidate"],
                    b["share"],
                    b["can_change"],
                    b["runoff_flavio"],
                    num(b["lower_pp"]),
                    num(b["upper_pp"]),
                ]
                for b in bounds
            ],
        )
        + f'<aside><b>De {num(sum(b["lower_pp"] for b in bounds))} a {num(sum(b["upper_pp"] for b in bounds))} pontos.</b> É a interseção possível entre abertura a mudança e escolha de Flávio no segundo turno, nas quatro candidaturas. Não é previsão de transferência, intenção de votar útil ou ganho líquido. Usa porcentagens arredondadas como marginais fixas; não inclui incerteza dessas marginais. A conversão pode ser zero.</aside>'
        + "<p>Os limites da Nexus na p. 43, a interseção acima e os nove pontos líquidos de consolidação respondem perguntas diferentes. Somá-los produziria dupla contagem. Para medir voto útil motivado, faltam a pergunta sobre motivo e o cruzamento origem × certeza × segunda opção × segundo turno.</p>",
    )
)

alt = []
for label, p in [
    ("Flávio", 75),
    ("Caiado", 77),
    ("Zema", 79),
    ("Renan", 81),
    ("Cury", 83),
]:
    vals = D["profile_tables"][str(p)][0]["values"]
    alt.append([label, *[str(x) + "%" for x in vals], str(vals[0] - vals[1]) + " pp"])
sections.append(
    section(
        "alternativas",
        "06",
        "Flávio rende mais no agregado.<br><em>Cury tem contrapontos.</em>",
        "A mesma amostra testa cinco adversários de Lula. Flávio chega a 46%, cinco pontos acima de Caiado e quatro acima de Cury. A resposta à troca de candidato também passa por Lula e pela não escolha."
        + ref(52),
        tab(["Adversário", "Lula", "Adversário", "B/N", "NS/NR", "Dif. Lula−adv."], alt)
        + "<p>Trocar Flávio por Caiado reduz o desafiante de 46% para 41%, mantém Lula em 47% e eleva branco/nulo de 6% para 11%. Essa comparação é medida na mesma amostra, mas não é experimento causal de substituição de candidatura. Ela não prova que as mesmas pessoas iriam diretamente ao nulo.</p>"
        + "<p><strong>O contraponto tem o mesmo peso.</strong> Entre jovens de 16 a 24 anos, Cury chega a 50% contra 49% de Flávio nos respectivos duelos. Acima de cinco salários, Cury tem 50% contra 48% de Flávio; Lula cai de 46% para 41%. As pequenas diferenças por subgrupo não identificam superioridade estatística, mas impedem escrever que Flávio domina todos os recortes."
        + ref(75, 76, 83, 84)
        + "</p>"
        + "<p>Entre quem declara voto em Jair Bolsonaro em 2022, Flávio tem 79% no primeiro e 93% no segundo. Entre quem declara Lula em 2022, Lula tem 82% e 89%. São perguntas feitas em setembro de 2026 sobre lembrança de 2022, sujeitas a erro de memória e composição; não são uma pesquisa antiga nem a matriz de retenção das bases atuais."
        + ref(23, 68)
        + "</p>",
    )
)

sections.append(
    section(
        "opiniao",
        "07",
        "Rejeição não é voto.<br><em>Terceira via não é um bloco.</em>",
        "Lula tem 48% de rejeição; Flávio, 50%. O potencial declarado é 50% para Lula e 48% para Flávio. Essas medidas não são teto intransponível, previsão ou substituto da pergunta de intenção de voto."
        + ref(86),
        tab(
            [
                "Nome",
                "Único em quem votaria",
                "Poderia votar",
                "Rejeita",
                "Não conhece",
            ],
            [
                ["Lula", "38%", "12%", "48%", "1%"],
                ["Flávio", "30%", "18%", "50%", "1%"],
                ["Cury", "6%", "36%", "33%", "24%"],
                ["Caiado", "4%", "33%", "39%", "23%"],
                ["Zema", "2%", "29%", "42%", "26%"],
                ["Renan", "2%", "22%", "43%", "32%"],
            ],
        )
        + "<p>O cruzamento de potencial encontra 44% que aceitam Lula e rejeitam Flávio, 43% que aceitam Flávio e rejeitam Lula, 5% que aceitam ambos e 5% que rejeitam ambos. Aceitar os dois não significa dividir o voto, e rejeitar os dois não obriga a votar nulo."
        + ref(91)
        + "</p>"
        + "<p>Na preferência por campo político, 40% escolhem Lula, 36% Flávio ou um indicado da família Bolsonaro e 20% alguém sem apoio de ambos. Dentro desses 20%, Lula e Flávio têm 19% cada no primeiro turno; outros candidatos somam 48%. Preferência abstrata por terceira via não descreve uma cédula sem os finalistas."
        + ref(95)
        + "</p>"
        + "<p>O enquadramento das perguntas também conta: a escala opõe “Anti-Lula” a “Anti-Bolsonaro (e sua família)”. São objetos assimétricos, pessoa e família. A classificação “não polarizados” vem dessas respostas, não de uma escala universal de centro político. O relatório descreve 18% não polarizados, 28% lulistas convictos e 30% bolsonaristas convictos."
        + ref(8, 12)
        + "</p>",
    )
)

sections.append(
    section(
        "governo",
        "08",
        "O governo recupera aprovação.<br><em>A segurança concentra perda.</em>",
        "Aprovação pessoal: 47%. Desaprovação: 49%. Avaliação ótima/boa: 37%; ruim/péssima: 44%. Comparadas à rodada anterior, aprovação sobe dois pontos e avaliação negativa cai dois. Isso não se resume ao primeiro turno."
        + ref(129, 130, 135, 136),
        figure(
            fig.economics(),
            "Respostas sobre a vida do entrevistado e de sua família desde 2023. Melhora e piora agregam muito e pouco. Igual e NS/NR ficam fora das barras, mas permanecem na base de 100%. Fonte: p. 99.",
        )
        + "<p>Segurança reúne 45% de piora e 24% de melhora, saldo de −21 pontos. Renda tem 41% de melhora e 29% de piora, saldo de +12; poder de compra anda no sentido oposto, 36% contra 43%, saldo de −7. Renda nominal e capacidade de compra não devem ser tratados como a mesma experiência."
        + ref(99)
        + "</p>"
        + "<p>Na atribuição ao governo, 36% do total dizem que a segurança piorou por influência federal e 21% que melhorou por essa influência. Na renda, são 26% e 35%. O governo recebe crédito em uma dimensão e responsabilização em outra. É percepção declarada, não identificação causal de efeito de políticas."
        + ref(127)
        + "</p>"
        + "<p>Quando se pedem o primeiro e o segundo principal problema, segurança soma 34% das menções, saúde 28% e corrupção 27%. Só na primeira menção, corrupção marca 20%, acima dos 17% de segurança. O ranking muda conforme a métrica; as respostas são múltiplas e não devem somar 100%."
        + ref(142)
        + "</p>"
        + "<p>96% declaram que decidiram ou provavelmente irão votar. Entre quem escolheu candidato no primeiro turno, 79% dizem saber e acertam seu número de urna; para Lula são 89% e para Flávio, 83%. Certeza e conhecimento são medidas úteis de consistência, mas não validam comparecimento futuro."
        + ref(14, 46, 47)
        + "</p>",
    )
)

sections.append(
    section(
        "incerteza",
        "09",
        "Um ponto não separa os dois.",
        "A margem de uma proporção não é a margem da diferença entre candidatos. Para 2.003 entrevistas, o modelo de amostra aleatória simples já deixa o segundo turno atravessar zero.",
        tab(
            [
                "Cenário",
                "Diferença L−F",
                "Margem 95% da diferença (AAS)",
                "Intervalo 95% (AAS)",
            ],
            [
                ["1º: 42 × 37", "+5,00", "±3,89", "+1,11 a +8,89"],
                ["2º: 47 × 46", "+1,00", "±4,22", "−3,22 a +5,22"],
            ],
        )
        + '<div class="formula">ME(diferença) = 1,96 × 100 × √[(pL + pF − (pL − pF)²) / n]</div>'
        + "<p><strong>Amostragem:</strong> o segundo turno não identifica liderança nem sob esse modelo simples. O primeiro passa nesse cálculo ilustrativo; um efeito de desenho próximo de 1,66 já faria seu intervalo alcançar zero. A coleta por telefone com cotas exige cautela: sem probabilidades de inclusão, pesos e desenho completos, este não é o intervalo oficial da pesquisa.</p>"
        + "<p><strong>Composição:</strong> a troca da renda reduz a diferença do segundo turno para 0,28 ponto e preserva o sinal positivo. Não é um segundo teste de significância. A reponderação não recebe o intervalo original como se os pesos e o benchmark fossem conhecidos sem erro.</p>"
        + "<aside>A frase fiel é: “Lula tem 47%, Flávio tem 46%, e a diferença não separa os dois no cálculo de 95% sob amostragem simples. Ao trocar apenas a renda pela régua comum da PNAD, o placar fica praticamente igual.”</aside>",
    )
)

sections.append(
    section(
        "documento",
        "10",
        "O arquivo também é evidência.",
        "Há avanços reais de transparência: referências de PNAD e TSE explicitadas, margens por perfil, cinco linhas de migração e perguntas de segunda escolha. Há também lacunas e inconsistências que precisam ser conciliadas.",
        tab(
            ["Registro documental", "Constatação", "Limite"],
            [
                [
                    "Criação do PDF",
                    "14/09/2026, 00:55:51 (UTC−3)",
                    "Posterior ao fim do campo de 13/9; não prova data pública.",
                ],
                [
                    "Última modificação",
                    "14/09/2026, 05:12:24 (UTC−3)",
                    "Metadado editável; não mede atraso de divulgação.",
                ],
                [
                    "Ordem das perguntas",
                    "O relatório diz que reorganiza os resultados por tema" + ref(4),
                    "Não se deve inferir a ordem da entrevista pela ordem das páginas.",
                ],
                [
                    "Terceira via",
                    "A p. 95 diz 20%; o título da p. 97 ainda diz 23%" + ref(95, 97),
                    "Discrepância documental; não usamos 23% para contas nacionais.",
                ],
                [
                    "Indecisos no cenário 1",
                    "2% na p. 20; a coluna “Cenário 1” da p. 22 mostra 1%"
                    + ref(20, 22),
                    "Adotamos o placar principal, corroborado pelas pp. 33–34.",
                ],
                [
                    "Cenário 2 repetido",
                    "Páginas 44–45 reaparecem em 49–50",
                    "Duplicação editorial; não são duas ondas independentes.",
                ],
                [
                    "Cury no título da série",
                    "A legenda da p. 66 traz “Eduardo”; título e demais tabelas dizem Augusto"
                    + ref(66, 83),
                    "Erro de nome no documento; nossa identificação segue as tabelas.",
                ],
                [
                    "Bases e pesos",
                    "Perfil percentual publicado; bases não ponderadas e pesos individuais ausentes",
                    "Não inferir tamanho real de subgrupo multiplicando n pela fatia ponderada.",
                ],
            ],
        )
        + "<p>A ficha metodológica declara telefone/CATI, cotas de sexo, idade, escolaridade, tipo de telefonia e DDD, 27 UFs, 2.003 entrevistas entre 11 e 13/9, margem geral de ±2 pontos e registro BR-04076/2026. Não transportamos automaticamente o questionário, o valor contratado ou uma alegação de execução de agosto para esta rodada."
        + ref(4)
        + "</p>"
        + "<p>Para encerrar as lacunas: questionário registrado desta rodada com ordem e randomização; contagens brutas e ponderadas por faixa; regra de renda e tratamento da não resposta; pesos e efeito de desenho; linhas faltantes da matriz; cruzamento conjunto das perguntas de mudança. São pedidos de reprodutibilidade, não evidência de fraude ou direcionamento.</p>",
    )
)

appendix = []
for p, rows in D["profile_tables"].items():
    cols = len(rows[0]["values"])
    if int(p) in [33, 34]:
        names = [
            "Lula",
            "Flávio",
            "Cury",
            "Caiado",
            "Renan",
            "Zema",
            "Outros",
            "B/N",
            "NS",
        ]
    elif 75 <= int(p) <= 84:
        names = ["Lula", "Adversário", "B/N", "NS"]
    elif 110 <= int(p) <= 125:
        names = [
            "Melhorou muito",
            "Melhorou pouco",
            "Igual",
            "Piorou pouco",
            "Piorou muito",
            "NS",
        ]
    elif int(p) in [133, 134]:
        names = ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo", "NS"]
    else:
        names = ["Aprova", "Desaprova", "NS"]
    appendix.append(
        f"<details><summary>Tabela da página {p}: {len(rows)} linhas</summary>"
        + ref(int(p))
        + tab(
            ["Recorte", *names],
            [
                [escape(row["label"]), *[str(v) + "%" for v in row["values"]]]
                for row in rows
            ],
        )
        + "</details>"
    )
sections.append(
    section(
        "anexo",
        "11",
        "O anexo é conferível.",
        "Trinta e duas páginas de tabelas alinhadas foram extraídas por programa, incluindo todos os duelos, condições de vida e governo. Cada linha conserva a página de origem. Os demais gráficos e perguntas estão na íntegra do PDF e na extração integral por página.",
        "".join(appendix),
    )
)

sections.append(
    section(
        "fontes",
        "12",
        "Fontes, limites e reprodução.",
        "Este dossiê atualiza a leitura de julho com a 14ª rodada. Distingue percentual publicado, análise descritiva e sensibilidade; nenhum número ajustado é chamado de resultado real da eleição.",
        '<ul><li><a href="fontes/nexus_btg_140926.pdf">Nexus/BTG, relatório completo de 14/09/2026, 155 páginas</a>. Fonte principal recebida em Downloads, arquivada com hash. Campo, método e registro na p. 4.</li><li><a href="assets/nexus_btg_140926_data.json">Base analítica completa</a>: tabelas, série, controles, matriz e priors alternativas.</li><li><a href="https://github.com/ArvorCo/PNAD">Repositório do projeto</a>: scripts e documentação. Caminhos de reprodução listados abaixo.</li><li><a href="reponderacao_pnad.html">Agregador PNAD</a>: benchmark, fontes de cada onda e placares sob a mesma regra.</li><li><a href="nexus_btg_0726.html">Dossiê de julho</a> e <a href="nexus_btg_240826.html">dossiê de 24/08</a>: antecedentes, sem presumir que falhas antigas se repetem.</li></ul>'
        + f'<p class="hash">SHA-256 do relatório: {D["source"]["sha256"]}</p>'
        + "<pre><code>python3 scripts/nexus-btg-140926-audit.py\npython3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-14\npython3 scripts/reponderacao-build.py\npython3 scripts/nexus-btg-140926-build.py\npython3 scripts/social-cards.py --only nexus_btg_140926 reponderacao_pnad</code></pre>"
        + "<p>A versão de dados conserva toda a extração em <code>data/pesquisas/nexus_btg/rodada14_2026-09-14/</code>. A renda usa o histograma <code>analysis/reponderacao/pnad_2025v1_histograma.json</code>; cada onda tem um manifesto em <code>analysis/reponderacao/pesquisas/</code>. O registro desta rodada foi lido no relatório; o questionário registrado não integra esta auditoria. Imagens de páginas são reproduções documentais da fonte, não ilustrações.</p>",
    )
)

evidence = "".join(
    f"<details><summary>Conferir reprodução da página {page}</summary>"
    f'<a href="fontes/nexus_btg_140926.pdf#page={page}">Abrir página no PDF</a>'
    f'<img loading="lazy" width="1344" height="756" src="img/nexus_btg_140926/p{page}.png" '
    f'alt="Página {page} do relatório Nexus/BTG de 14 de setembro de 2026"></details>'
    for page in [4, 34, 38, 41, 43, 74, 76, 95, 97, 152]
)
sections[-1] = sections[-1].replace("</section>", evidence + "</section>")

nav = [
    ("renda", "Renda"),
    ("conta", "A conta"),
    ("historico", "História"),
    ("transferencia", "Sankey"),
    ("voto-util", "Voto útil"),
    ("alternativas", "Alternativas"),
    ("opiniao", "Rejeição"),
    ("governo", "Governo"),
    ("incerteza", "Incerteza"),
    ("documento", "Documento"),
    ("anexo", "Anexo"),
    ("fontes", "Fontes"),
]
html = (
    """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A renda encurta. O empate fica. BTG/Nexus 14/09/2026 · Arvor</title>
<meta name="description" content="Dossiê da 14ª rodada BTG/Nexus: 47 × 46 vira 46,69 × 46,40 com a PNAD. Série histórica, Sankey com cinco origens medidas, voto útil e anexo auditável.">
<link rel="canonical" href="https://brasil.arvor.co/nexus_btg_140926.html"><link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="article"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="A renda encurta. O empate fica."><meta property="og:description" content="BTG/Nexus 14/09: 47 × 46 vira 46,69 × 46,40 na sensibilidade PNAD. Transferência medida, série e voto útil.">
<meta property="og:url" content="https://brasil.arvor.co/nexus_btg_140926.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/nexus_btg_140926.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/nexus_btg_140926.png">
<link rel="stylesheet" href="assets/nexus_btg_140926.css"><script defer src="assets/nexus_btg_140926.js"></script></head><body>
<a class="skip" href="#conteudo">Pular para o dossiê</a><header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / INTELLIGENCE</a><span>AUDITORIA ELEITORAL · Nº 14</span></div><p class="kicker">BTG/NEXUS · 14 SETEMBRO 2026 · BR-04076/2026</p><h1>A renda encurta.<br><em>O empate fica.</em></h1><p class="deck">A PNAD quase apaga o ponto que separa Lula e Flávio. A Nexus mede a transferência de cinco candidaturas, mas isso não prova voto útil já consumado. Os números, as perguntas e os limites, na mesma página.</p><div class="hero-grid"><div><b>47 × 46</b><span>2º turno publicado · Lula × Flávio</span></div><div><b>46,69 × 46,40</b><span>Sensibilidade PNAD · Lula × Flávio</span></div><div><b>5 + 2 + 2</b><span>origens medidas + bases fixadas + estimadas</span></div></div><p class="meta">Campo 11–13/09 · 2.003 eleitores · telefone/CATI · 155 páginas · análise independente Arvor</p></div></header>
<nav aria-label="Capítulos"><div class="wrap">"""
    + "".join(f'<a href="#{s}">{t}</a>' for s, t in nav)
    + """</div></nav><main class="wrap" id="conteudo">"""
    + "".join(sections)
    + """</main><footer class="wrap"><a href="index.html">Arvor Intelligence</a><p>Leitura de pesquisa, com evidência e limite explícitos. Atualização: 14/09/2026.</p></footer></body></html>"""
)
(ROOT / "docs/nexus_btg_140926.html").write_text(html)
print("Dossiê gerado: 12 capítulos, 4 figuras, 32 páginas de anexo.")
