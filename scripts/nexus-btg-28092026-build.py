#!/usr/bin/env python3
"""Build an auditable round-16 dossier, with static evidence and interactive scenarios."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from ga_tag import injetar

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())
R = D["reweight"]
LV = D["turnout"]
T = D["transfer"]
NAMES = ["Lula", "Flávio", "Cury", "Caiado", "Renan", "Zema", "Outros"]
spec = importlib.util.spec_from_file_location(
    "fig", ROOT / "scripts/nexus-btg-140926-figures.py"
)
fig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig)


def n(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


def ref(*pages):
    return (
        ' <span class="refs">'
        + " · ".join(
            f'<a href="fontes/nexus_btg_28092026.pdf#page={p}">p. {p}</a>'
            for p in pages
        )
        + "</span>"
    )


def tab(headers, rows):
    return (
        '<div class="table-scroll" tabindex="0"><table><thead><tr>'
        + "".join(f'<th scope="col">{h}</th>' for h in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows
        )
        + "</tbody></table></div>"
    )


def figure(svg, caption):
    return f'<figure><div class="chart-scroll" tabindex="0">{svg}</div><figcaption>{caption}</figcaption></figure>'


def adj(b, key="pessoas16_efetivo"):
    return R["turnos"][b]["cenarios"][key]["ajustado"]


def valid(d):
    ds = {k: v for k, v in d.items() if k not in ("branco_nulo", "indecisos")}
    return {k: 100 * v / sum(ds.values()) for k, v in ds.items()}


sections = []


def section(slug, title, lead, body):
    sections.append(
        f'<section id="{slug}"><div class="section-head"><span class="kicker">{len(sections)+1:02} / AUDITORIA</span><h2>{title}</h2><p class="lead">{lead}</p></div>{body}</section>'
    )


section(
    "renda",
    "A renda muda pouco.<br><em>Isso também é resultado.</em>",
    f'O segundo turno publicado é Lula 46% × Flávio 44%. A troca isolada pela renda da PNAD produz {n(adj("2t")["lula"])}% × {n(adj("2t")["flavio"])}%. A diferença cai de 2 para {n(R["turnos"]["2t"]["gap_ajustado"])} pontos; o sinal não muda.'
    + ref(4, 86, 142),
    figure(
        fig.income(D),
        "Perfil publicado comparado à PNADC anual 2025, visita 1, pessoas 16+, renda domiciliar efetiva (VD5001), peso V1032. Histograma em reais de abril/2026, cortes convertidos pelo motor comum do agregador.",
    )
    + "<p>A faixa até um salário tem 19% na Nexus e 13,44% na régua da PNAD. A seguinte faz o movimento inverso: 18% contra 21,75%. Somadas, as duas faixas são 37% contra 35,19%. Exibir apenas o excesso na primeira faixa exageraria a divergência de todo o bloco de baixa renda.</p>"
    + "<p><strong>Não encontramos evidência de uma distorção grave de renda nesta rodada.</strong> O teste principal desloca a diferença em menos de meio ponto. Isso não certifica os pesos: o registro declara ponderação por renda e força de trabalho, mas não publica alvos de renda, algoritmo, limites dos pesos, bases brutas ou tamanho efetivo.</p>"
    + "<p>A PNAD usada como referência já é a anual 2025, primeira visita. Renda familiar declarada ao telefone não coincide necessariamente com renda domiciliar da PNAD; pessoas de 16 anos ou mais não equivalem a eleitores com título. Conferimos visualmente a PF15, p. 13 do questionário atual: renda familiar do mês passado, incluindo todas as fontes, com cortes de R$ 1.621, R$ 3.242, R$ 4.863 e R$ 8.105. A régua é de 2026. A exportação do instrumento permaneceu indisponível.</p>"
    + "<p>O cartão também prevê “sem rendimento”, “não sabe” e “recusa”, enquanto o perfil publicado fecha em quatro faixas. Falta explicar se essas respostas foram agrupadas, imputadas, excluídas ou ausentes na coleta. Não sabemos seu tamanho nem o efeito sobre a ponderação.</p>"
    + tab(
        ["Régua", "Lula 1º", "Flávio 1º", "Lula 2º", "Flávio 2º", "Dif. L−F 2º"],
        [["Publicado", "42,00", "37,00", "46,00", "44,00", "+2,00"]]
        + [
            [
                label,
                n(adj("1t", key)["lula"]),
                n(adj("1t", key)["flavio"]),
                n(adj("2t", key)["lula"]),
                n(adj("2t", key)["flavio"]),
                n(adj("2t", key)["lula"] - adj("2t", key)["flavio"]),
            ]
            for key, label in [
                ("pessoas16_efetivo", "Pessoas 16+, efetivo"),
                ("pessoas16_habitual", "Pessoas 16+, habitual"),
                ("domicilios_efetivo", "Domicílios: outro universo"),
            ]
        ],
    )
    + "<aside><b>Sensibilidade, não voto corrigido.</b> Domicílios não são eleitores. A linha alternativa explicita o efeito da escolha do universo e não entra como previsão nem como justificativa para escolher o resultado mais conveniente.</aside>",
)

proof = []
for dim, cs in D["controls"].items():
    for b, label in [("1t", "1º"), ("2t", "2º")]:
        v = cs[b]["recomposed"]
        proof.append(
            [dim, label, n(v["lula"]), n(v["flavio"]), n(cs[b]["max_residual"])]
        )
section(
    "prova",
    "Antes de ajustar,<br>recompor.",
    "As 145 páginas foram extraídas por programa. Cinco partições recompõem os dois turnos; os resíduos ficam documentados. Tabelas arredondadas não são microdados exatos.",
    tab(
        [
            "Partição",
            "Turno",
            "Lula recomposto",
            "Flávio recomposto",
            "Maior resíduo (pp)",
        ],
        proof,
    )
    + '<div class="formula">ajustado = publicado + Σ (peso PNAD − peso Nexus) × voto da faixa</div>'
    + "<p>A âncora preserva o placar divulgado e acrescenta só a diferença causada pela margem de renda. Não se renormalizam apenas Lula e Flávio no primeiro turno: Cury, Caiado, Renan, Zema e Outros permanecem no denominador dos válidos. O rótulo Outros é voto em candidatura, não branco/nulo.</p>"
    + "<p>A amostra etária publicada soma 101% e o segundo turno soma 99%, ambos compatíveis com o aviso de arredondamento. No modelo conjunto, margens e linhas são compatibilizadas por ajuste proporcional. No agregador, permanece o delta ancorado. São procedimentos diferentes, identificados na tabela de resultados.</p>"
    + ref(4, 36, 37, 85, 86, 142),
)

rows = []
for b, label in [("1t", "1º turno"), ("2t", "2º turno")]:
    pub = valid(D["poll"]["publicado"][b])
    a = valid(adj(b))
    c = LV["central"][b]
    rows += [
        [
            label + " · publicado / válidos",
            n(pub["lula"]),
            n(pub["flavio"]),
            "Sem filtro de presença",
        ],
        [
            label + " · só renda / válidos",
            n(a["lula"]),
            n(a["flavio"]),
            "Delta ancorado PNAD",
        ],
        [
            label + " · conjunto, antes da presença",
            n(c["before_valid"][0]),
            n(c["before_valid"][1]),
            "Renda, idade e região",
        ],
        [
            label + " · cenário de eleitor provável",
            n(c["valid"][0]),
            n(c["valid"][1]),
            f'Comparecimento {n(c["target_turnout"])}%',
        ],
    ]
section(
    "validos",
    "Eleitor provável:<br><em>o efeito líquido é pequeno.</em>",
    f'No cenário de referência, Lula fica com {n(LV["central"]["1t"]["valid"][0],1)}% e Flávio com {n(LV["central"]["1t"]["valid"][1],1)}% dos válidos no primeiro turno. No segundo, {n(LV["central"]["2t"]["valid"][0],1)}% × {n(LV["central"]["2t"]["valid"][1],1)}%. São estimativas condicionais, sem validação que permita chamá-las de mais corretas.',
    tab(
        ["Universo / procedimento", "Lula válidos %", "Flávio válidos %", "Condição"],
        rows,
    )
    + "<p>O comparecimento ajustado quase não altera o cenário conjunto: renda mais alta desloca parte do peso para Flávio; os perfis etário e regional compensam parte desse movimento. O cálculo não foi calibrado para produzir empate, virada ou vitória de candidato algum.</p>"
    + "<aside><b>Uma casa decimal para leitura; duas para reprodução.</b> Os dados de entrada são percentuais inteiros. A precisão exibida na conta não significa precisão eleitoral. Não há microdados, pesos individuais ou desenho completo para um intervalo válido do modelo.</aside>"
    + tab(
        ["Candidatura 1º turno", "Válidos no cenário %"],
        [
            [name, n(v, 1)]
            for name, v in zip(NAMES, LV["central"]["1t"]["valid"], strict=True)
        ],
    )
    + "<p>Branco/nulo é resposta de voto; abstenção é ausência. Primeiro se estima quem comparece; depois se retiram branco/nulo e indecisos do denominador. Os indecisos não são redistribuídos: a conta descreve escolhas declaradas, não prevê como eles votarão.</p>"
    + ref(13, 20, 22, 62),
)

section(
    "modelo",
    "96% prometem ir.<br>O modelo precisa de uma âncora.",
    "89% dizem que já decidiram comparecer e 7% que provavelmente irão. Não há base para converter a soma em presença real de 96%. A calibração usa resultados oficiais anteriores como cenário, mantendo a incerteza sobre 2026.",
    "<ol><li><b>Reconstruir margens compatíveis.</b> Ajustar voto × renda, voto × idade e voto × região aos totais divulgados. A tabela conjunta central maximiza entropia sob essas margens: as dimensões são independentes dado o voto na semente. Ela é sintética, não uma base recuperada.</li>"
    + "<li><b>Trocar a renda.</b> Aplicar a margem PNAD e preservar as margens de idade e região publicadas pela Nexus, referenciadas ao TSE. Cada célula recebe um único peso; não somamos três resultados nacionais.</li>"
    + "<li><b>Transformar declaração em propensão.</b> Atribuir probabilidades de cenário às cinco respostas, na ordem “decidiu ir”, “provavelmente vai”, “provavelmente não”, “decidiu não” e “NS/NR”. O conjunto central usa 95%, 65%, 20%, 5% e 50%. Esses números não foram estimados pela Nexus.</li>"
    + "<li><b>Usar região observada.</b> No cenário central, a componente regional vem das taxas oficiais de 2022, separadas por turno e sem exterior. Renda e idade usam as declarações da Nexus. O intercepto logístico é calibrado ao comparecimento de 2022 reaplicado à composição regional do eleitorado de 2026.</li>"
    + "<li><b>Testar hipóteses.</b> Variar comparecimento nacional de 75% a 85%, probabilidades das respostas, região histórica versus declarada e associação oculta entre dimensões. O segundo turno reaproveita a pergunta de presença do primeiro: extrapolação explícita.</li></ol>"
    + '<div class="formula">q(célula) = logística[α + efeito(renda) + efeito(idade) + efeito(região)]<br>Σ peso(célula) × q(célula) = comparecimento-alvo<br>válidos(candidato) = votos esperados do candidato / votos esperados em todos os candidatos</div>'
    + "<p>Os efeitos são logits centrados das propensões por grupo. Não são coeficientes estimados de regressão individual. A hipótese restante é forte: dentro da célula, comparecimento não depende do candidato. Sem voto × intenção de comparecer, ela não é testável.</p>"
    + "<p>Renda não existe no cadastro do TSE. Portanto, nenhuma taxa por renda aqui é uma “abstenção oficial”. As idades são os grupos amplos publicados pela Nexus; 60+ mistura voto obrigatório e facultativo. Não inventamos uma separação de 70+.</p>"
    + ref(13, 15, 16, 142),
)

segrows = ""
for dim, title in [
    ("renda", "Renda familiar"),
    ("idade", "Idade"),
    ("regiao", "Região"),
]:
    s = LV["central"]["1t"]["segments"][dim]
    segrows += (
        "<h3>"
        + title
        + "</h3>"
        + tab(
            [
                "Grupo",
                "Peso inicial %",
                "Abstenção no grupo %",
                "Peso entre presentes %",
                "Fatia dos ausentes %",
            ],
            [
                [
                    label,
                    n(s["population_share"][i]),
                    n(100 - s["turnout"][i]),
                    n(s["voter_share"][i]),
                    n(s["absentee_share"][i]),
                ]
                for i, label in enumerate(D["tables"][dim]["labels"])
            ],
        )
    )
section(
    "abstencao",
    "Quem falta dentro do grupo<br>e quem compõe a ausência.",
    "Taxa de abstenção e composição dos ausentes respondem a perguntas diferentes. A tabela mostra as duas. Todos os valores de 2026 são resultados do cenário, não observações.",
    segrows
    + "<p>Exemplo: a faixa de 2 a 5 salários representa cerca de 39% da população-alvo; pode formar a maior parcela dos ausentes mesmo sem ter a maior taxa de abstenção. As dimensões se sobrepõem: nunca some as linhas de renda às de idade ou região.</p>"
    + "<h3>Âncora regional efetivamente observada em 2022</h3>"
    + tab(
        ["Região", "Abstenção 1º turno %", "Abstenção 2º turno %"],
        [
            [
                label,
                n(100 * (1 - LV["historical"]["turns"]["1t"]["rates"][i])),
                n(100 * (1 - LV["historical"]["turns"]["2t"]["rates"][i])),
            ]
            for i, label in enumerate(D["tables"]["regiao"]["labels"])
        ],
    )
    + "<p>Fonte: resultados simplificados do TSE, 27 UFs. Denominador: comparecimento + abstenção das seções apuradas. As taxas regionais observadas não são idênticas às taxas finais do modelo acima: idade e renda também variam dentro da região. Os totais, URLs por UF e procedimento estão no JSON.</p>",
)

bounds = LV["income_frechet_lula_runoff"]
section(
    "sensibilidade",
    "A faixa pequena depende<br><em>de uma hipótese grande.</em>",
    f'Nos 54 cenários testados por turno, Lula fica entre {n(LV["envelope"]["2t"][0][0],1)}% e {n(LV["envelope"]["2t"][0][1],1)}% dos válidos no segundo. Isso não é intervalo de confiança nem prova de liderança.',
    "<p>Esses cenários variam as hipóteses demográficas, mas todos mantêm a independência entre voto e comparecimento dentro da célula. Quando essa restrição é retirada no exercício apenas por renda, as mesmas margens admitem resultados muito mais diferentes.</p>"
    + f"<aside><b>Teste de identificação: {n(bounds[0],1)}% a {n(bounds[1],1)}% para Lula.</b> São extremos matemáticos obtidos por programação linear fracionária, mantendo voto e comparecimento de cada faixa de renda fixos. Não são cenários prováveis nem uma previsão. Demonstram que as margens isoladas não identificam quem realmente comparece dentro de cada eleitorado.</aside>"
    + "<p>Escolha as premissas abaixo para consultar cenários já calculados. A linha histórica usa o comparecimento regional observado em 2022; “declarado” usa a pergunta da Nexus. Nenhum controle altera o resultado desejado de candidato.</p>"
    + '<div class="scenario-controls"><label>Turno<select id="lv-turn"><option value="1t">Primeiro turno</option><option value="2t">Segundo turno</option></select></label><label>Comparecimento<select id="lv-target"><option value="hist">Âncora histórica</option><option value=".75">75%</option><option value=".85">85%</option></select></label><label>Respostas<select id="lv-score"><option value="central">Central</option><option value="suave">Suave</option><option value="estrito">Estrito</option></select></label><label>Região<select id="lv-region"><option value="2022">Histórico de 2022</option><option value="declarado">Declaração Nexus</option></select></label><label>Associação oculta<select id="lv-association"><option value="0">Máxima entropia</option><option value="-1">Alternativa negativa</option><option value="1">Alternativa positiva</option></select></label></div>'
    + '<div id="lv-result" class="scenario-result" aria-live="polite">'
    + f'Cenário central, 1º turno: Lula {n(LV["central"]["1t"]["valid"][0],1)}%; Flávio {n(LV["central"]["1t"]["valid"][1],1)}% dos válidos.'
    + "</div>"
    + "<h3>O ponto frágil de 60+: teste adicional</h3>"
    + "<p>O modelo central usa presença declarada por idade, sem calibração etária ao comparecimento real. Para expor essa limitação, fixamos a presença de 60+ em 60%, 70% ou 80% e recalibramos os demais grupos para manter o mesmo comparecimento nacional. São hipóteses de estresse, não taxas observadas em 2022; este teste é separado dos 54 cenários do simulador.</p>"
    + tab(
        [
            "Presença de 60+",
            "Lula 1º válidos %",
            "Flávio 1º válidos %",
            "Lula 2º válidos %",
            "Flávio 2º válidos %",
        ],
        [
            [
                n(a["older_turnout"] * 100, 0) + "%",
                n(a["valid"][0]),
                n(a["valid"][1]),
                n(b["valid"][0]),
                n(b["valid"][1]),
            ]
            for a, b in zip(LV["age_stress"]["1t"], LV["age_stress"]["2t"], strict=True)
        ],
    )
    + "<p>A incerteza etária amplia a variação do placar. Mesmo esses testes preservam a hipótese de comparecimento independente do candidato dentro da célula. Não resolvem a falta do cruzamento direto entre voto e presença.</p>"
    + "<details><summary>Quais probabilidades e associações foram testadas?</summary>"
    + tab(
        ["Resposta", "Suave %", "Central %", "Estrito %"],
        [
            [
                label,
                *[
                    n(LV["scores"][key][i] * 100, 0)
                    for key in ["suave", "central", "estrito"]
                ],
            ]
            for i, label in enumerate(
                [
                    "Decidiu ir",
                    "Provavelmente vai",
                    "Provavelmente não",
                    "Decidiu não",
                    "NS/NR",
                ]
            )
        ],
    )
    + "<p>Nas sementes alternativas, multiplicamos a tabela por exp[κ(idade×renda + idade×região + renda×região)], com índices entre −1 e 1 e κ igual a −1 ou +1. Depois, o IPF restaura exatamente as mesmas margens voto × dimensão. A ordem de região é uma perturbação numérica declarada, não uma escala geográfica. A hipótese de associação oculta é ilustrativa, não um limite de todas as tabelas possíveis.</p></details>",
)

h = LV["past_voting"]
section(
    "passado",
    "O hábito de votar<br>não substitui o filtro de presença.",
    "A Nexus mede a intenção atual dentro de três grupos de comparecimento declarado em 2018/2022. É informação direta e útil; faltam as bases para misturá-la num eleitorado provável nacional.",
    tab(
        [
            "Histórico declarado",
            "Lula 1º válidos",
            "Flávio 1º válidos",
            "Lula 2º válidos",
            "Flávio 2º válidos",
        ],
        [
            [
                label,
                *[n(v) for v in h["1t_valid"][i][:2]],
                *[n(v) for v in h["2t_valid"][i][:2]],
            ]
            for i, label in enumerate(h["labels"])
        ],
    )
    + ref(23, 64)
    + "<p>No primeiro turno, quem diz ter faltado às duas eleições anteriores dá Lula 38% e Flávio 27% sobre todas as respostas. No segundo, esse mesmo grupo marca 38% e 39%. A tese “quem falta é sempre mais lulista” não sobrevive à troca da cédula nesta rodada.</p>"
    + "<p>Não foram publicados o tamanho ponderado desses três grupos nem seu cruzamento com a intenção de presença em 2026. Também falta conferir o tratamento dos jovens que não tinham idade eleitoral em 2018 ou 2022. Não se imputa peso zero ou abstenção a quem ainda não era elegível.</p>",
)

sankey = (
    fig.sankey(D)
    .replace(
        "Sólida: 5 medidas. Contorno pontilhado: 2 bases fixadas. Hachura: 2 estimadas.",
        "Sólida: 5 origens publicadas*. Hachura: 4 origens estimadas, inclusive as bases.",
    )
    .replace(
        "cinco origens medidas, duas bases consolidadas por hipótese e duas origens estimadas",
        "cinco origens publicadas e quatro origens estimadas",
    )
)
section(
    "transferencia",
    "Cinco origens medidas.<br><em>Quatro ainda dependem do modelo.</em>",
    "A página 84 publica o segundo turno de Cury, Caiado, Renan, Zema e Samara. As linhas medidas ficam fixas. Fidelidade de Lula e Flávio, branco/nulo e indecisos não têm matriz publicada.",
    figure(
        sankey,
        "*O bloco Outros=1% é aproximado por Samara=1%, a candidatura com percentual não nulo na p. 20. Candidatos impressos em 0% podem ter frações ocultas. Linhas medidas normalizadas para 100%; origens reescaladas para os 99 pontos do segundo turno. Retenção de 98% e cruzamento direto zero são hipóteses. Não é trajetória individual.",
    )
    + tab(
        ["Origem medida", "Lula %", "Flávio %", "B/N %", "NS/NR %"],
        [
            [NAMES[i] if i != 6 else "Samara", *vals]
            for i, vals in sorted(
                (int(k), v) for k, v in T["conditional_printed"].items()
            )
        ],
    )
    + ref(84)
    + "<p>As cinco origens geram aproximadamente "
    + n(T["pool_points"][0])
    + " pontos para Lula, "
    + n(T["pool_points"][1])
    + " para Flávio e "
    + n(T["pool_points"][2])
    + " para branco/nulo. A divisão de Caiado é 32% para cada finalista e 35% de branco/nulo: omitir esse empate distorceria o achado.</p>"
    + "<p>Nos percentuais publicados, a consolidação líquida é Lula +4 e Flávio +7, razão 1,75:1; na onda anterior, +6 e +8, razão 1,33:1. Essa conta de margens não mede fidelidade individual. Compatibilizando o total 100 do primeiro com 99 do segundo, a razão atual fica em "
    + n(T["net_common_scale"]["ratio"])
    + ":1.</p>"
    + "<p>A retenção foi testada em 97%, 98% e 100%, com prior alternativa para não escolha. Todos fecham as margens e preservam as cinco linhas publicadas. As fitas por origem não publicada mudam; o ganho líquido das margens permanece. Uma retenção de 95% com cruzamento direto zero é incompatível com estas margens e estas cinco linhas: o modelo não força uma solução impossível.</p>"
    + "<aside><b>Base pequena, conclusão limitada.</b> Samara e Zema têm 1% no total, equivalente a cerca de 20 entrevistas apenas se os pesos fossem iguais. Não é a base bruta conhecida. Sem n bruto, pesos e erro do recorte, os 36% de Samara para Flávio não sustentam uma tese de migração ideológica.</aside>",
)

section(
    "problemas",
    "O que o material permite cobrar.",
    "Os problemas mais fortes são de transparência e identificação. Eles impedem reproduzir a ponderação e validar um modelo de comparecimento; não demonstram fraude ou erro direcional.",
    tab(
        ["Achado", "Consequência", "Documento que resolve"],
        [
            [
                "Renda entra na ponderação, alvo não publicado",
                "O perfil 19/18/40/23 não revela a meta ou o ajuste aplicado",
                "Alvos, bases brutas/ponderadas e código de calibração",
            ],
            [
                "Sem distribuição de pesos, n efetivo e efeito de desenho",
                "Não se verifica a precisão final",
                "Pesos anonimizados, aparo, deff e cálculo de variância",
            ],
            [
                "Sem balanço de chamadas e recusas",
                "O sorteio de números não basta para auditar não resposta",
                "Funil de discagem e disposição final dos contatos",
            ],
            [
                "Cadastro de telefones no plano; RDD na descrição territorial",
                "Formulações exigem conciliação do procedimento operacional",
                "Regras de geração, múltiplas linhas, fixo/celular e seleção da pessoa",
            ],
            [
                "Idades de controle e publicação diferentes",
                "Registro usa 25–34, 35–44, 45–59; relatório usa 25–40, 41–59",
                "Cruzamento e bases nas faixas registradas",
            ],
            [
                "Sem voto × intenção de presença",
                "Likely voters exige hipótese ecológica",
                "Cruzamento por candidato e presença, com bases e pesos",
            ],
            [
                "Sem bases no histórico de comparecimento",
                "Não se identificam os pesos dos grupos nem elegibilidade anterior",
                "Bases e códigos para não elegíveis e NS/NR",
            ],
            [
                "Sem fidelidade publicada dos finalistas",
                "Transferência completa depende de prior",
                "Todas as linhas de voto 1º × 2º turno",
            ],
            [
                "Sem rendimento, não sabe e recusa não aparecem no perfil",
                "A PF15 prevê esses códigos; seu tratamento não é reproduzível",
                "Frequências brutas e ponderadas e regra de recodificação da renda",
            ],
            [
                "Questionário integral não exportado nesta auditoria",
                "Cartão de renda conferido na tela; ordem e rodízio não auditados integralmente",
                "PDF local verificável do questionário BR-07557/2026",
            ],
        ],
    )
    + "<p>O plano declara auditoria de cerca de 20% dos questionários. Isso é um procedimento informado, não uma execução comprovada. A primeira página do instrumento orienta encerrar perfis com cotas já completas, compatível com a seleção final por cotas. A seleção inicial aleatória de telefone não permite, sozinha, afirmar probabilidades finais conhecidas de todos os eleitores.</p>"
    + "<p>O PDF informa que a ordem do relatório difere do questionário e que a intenção de voto abre o instrumento. A organização por temas não prova indução. Também não se exige anexo de setores censitários de uma amostra por telefone: a unidade descrita é o número telefônico.</p>"
    + ref(4)
    + '<p><a href="fontes/nexus_btg_28092026/registro-metodologia.txt">Leia o excerto transcrito do registro atual.</a> Nenhuma descrição de registro antigo foi transportada como prova da execução desta onda.</p>',
)

section(
    "incerteza",
    "Dois pontos de diferença<br>não identificam liderança.",
    f'A margem de 95% da diferença Lula menos Flávio é de aproximadamente {n(D["precision"]["gap_moe"])} pontos sob amostragem aleatória simples. O intervalo ilustrativo vai de {n(2-D["precision"]["gap_moe"])} a +{n(2+D["precision"]["gap_moe"])} pontos.',
    '<div class="formula">EP(L−F) = √[(pL + pF − (pL − pF)²) / n]</div>'
    + f'<p>Com n=2.000, a margem máxima individual sob AAS é {n(D["precision"]["aas_max_moe"])} pontos. O “±2” declarado pode refletir arredondamento; a falta do cálculo impede saber. A referência AAS não incorpora seleção final por cotas, não resposta ou pesos. Não é o intervalo oficial e não se transfere ao modelo de eleitor provável.</p>'
    + "<p>Na série publicada, Lula passa de 40 para 42 no primeiro turno e Flávio permanece em 37. No segundo, Lula fica em 46 e Flávio passa de 45 para 44. Mudanças desse tamanho entre amostras não provam deslocamento eleitoral sem o erro da diferença entre ondas.</p>"
    + ref(21, 63)
    + "<h3>Cenários alternativos de segundo turno</h3>"
    + tab(
        ["Adversário de Lula", "Lula %", "Adversário %", "B/N %", "NS/NR %"],
        [
            ["Flávio", 46, 44, 8, 1],
            ["Caiado", 46, 42, 10, 2],
            ["Zema", 48, 39, 12, 2],
            ["Renan", 48, 37, 13, 2],
            ["Cury", 46, 41, 11, 2],
        ],
    )
    + ref(62)
    + "<p>Lula varia entre 46% e 48%; o adversário entre 37% e 44%. É comparação medida de cédulas hipotéticas na mesma amostra, não experimento causal de retirada de candidatura. Ela restringe interpretações, mas não revela por si a passagem de cada pessoa entre candidatos.</p>",
)

section(
    "fontes",
    "A conta e suas fontes.",
    "Relatório oficial, excerto do registro, extração integral, premissas e código permitem refazer cada resultado.",
    '<ul><li><a href="fontes/nexus_btg_28092026.pdf">BTG/Nexus, rodada 16, 145 páginas</a> · <a href="'
    + D["source"]["url"]
    + '">arquivo no domínio do instituto</a>. Campo 25–27/09; divulgação 28/09/2026; BR-07557/2026.</li>'
    + '<li><a href="fontes/nexus_btg_28092026/registro-metodologia.txt">Plano e controle da onda atual, transcritos do PesqEle</a>. O arquivo do questionário não foi exportado.</li>'
    + '<li><a href="assets/nexus_btg_28092026_data.json">Dados, cenários, margens e URLs do TSE por UF (JSON)</a> · <a href="assets/nexus_btg_28092026_cenarios.csv">54 cenários por turno (CSV)</a>.</li>'
    + '<li><a href="reponderacao_pnad.html#pesquisa-nexus_2026-09-27">Mesma régua de renda no agregador</a>. PNADC anual 2025, visita 1, V1032, pessoas 16+, VD5001; cenário habitual VD5007 e domicílios publicados à parte.</li>'
    + '<li><a href="https://dadosabertos.tse.jus.br/dataset/comparecimento-e-abstencao-2022">TSE: comparecimento e abstenção 2022</a>. Esta análise usa os resultados simplificados por UF arquivados no projeto, com URLs no JSON, excluindo exterior.</li>'
    + '<li><a href="https://www.pewresearch.org/methods/2016/01/07/measuring-the-likelihood-to-vote/">Pew Research Center: mensuração de eleitor provável</a>. Referência metodológica sobre validação; coeficientes dos EUA não foram transportados para o Brasil.</li></ul>'
    + '<p class="hash">SHA-256 do PDF: '
    + D["source"]["sha256"]
    + "</p>"
    + "<pre>python3 scripts/nexus-btg-28092026-audit.py\npython3 scripts/nexus-btg-28092026-build.py\npython3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-28\npython3 scripts/reponderacao-build.py</pre>"
    + '<p>Os arquivos de código estão no <a href="https://github.com/ArvorCo/PNAD">repositório Arvor/PNAD</a>. A versão local desta auditoria pode preceder sua publicação. Consulta documental: 28/09/2026.</p>',
)

html = (
    """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTG/Nexus 28/09: renda, transferência e eleitor provável | Arvor</title>
<meta name="description" content="Auditoria BTG/Nexus de 28/09/2026: renda altera pouco o placar; cinco transferências publicadas; cenários de abstenção e votos válidos com limites explícitos.">
<link rel="canonical" href="https://brasil.arvor.co/nexus_btg_28092026.html">
<meta property="og:title" content="BTG/Nexus: a renda muda pouco. A abstenção exige hipóteses."><meta property="og:type" content="article"><meta property="og:locale" content="pt_BR"><meta property="og:url" content="https://brasil.arvor.co/nexus_btg_28092026.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/nexus_btg_28092026.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/nexus_btg_28092026.png">
<link rel="stylesheet" href="assets/nexus_btg_140926.css"><link rel="stylesheet" href="assets/nexus_btg_28092026.css"><script defer src="assets/nexus_btg_28092026.js"></script></head><body>
<a class="skip" href="#conteudo">Pular para a análise</a><header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / BRASIL</a><span>AUDITORIA INDEPENDENTE · 28 SET 2026</span></div><p class="kicker">BTG / NEXUS · 16ª RODADA · BR-07557/2026</p><h1>A renda muda pouco.<br><em>A ausência exige hipóteses.</em></h1><p class="deck">A pesquisa mantém Lula numericamente à frente. A régua da PNAD encurta a diferença; o modelo de comparecimento não produz uma virada. O que os dados medem e o que ainda não permitem saber.</p><div class="hero-grid"><div><b>46 × 44</b><span>segundo turno publicado<br>Lula × Flávio, total da amostra</span></div><div><b>45,76 × 44,20</b><span>sensibilidade por renda PNAD<br>mesmo universo, sem filtro de presença</span></div><div><b>5 + 4</b><span>origens publicadas + estimadas<br>no diagrama de transferência</span></div></div><p class="meta">2.000 entrevistas · telefone / CATI · campo 25–27/09 · sem liderança estatisticamente identificada no segundo turno</p></div></header>
<nav aria-label="Capítulos"><div class="wrap"><a href="#renda">Renda</a><a href="#validos">Votos válidos</a><a href="#modelo">Modelo</a><a href="#abstencao">Abstenção</a><a href="#sensibilidade">Simulador</a><a href="#transferencia">Transferência</a><a href="#problemas">Problemas</a><a href="#fontes">Fontes</a></div></nav><main id="conteudo" class="wrap">"""
    + "\n".join(sections)
    + """</main><footer class="wrap"><a href="index.html">Biblioteca Arvor</a> · <a href="reponderacao_pnad.html">Agregador PNAD</a> · <a href="nexus_btg_140926.html">Dossiê de 14/09</a></footer><script id="scenario-data" type="application/json">"""
    + json.dumps(LV["scenarios"], ensure_ascii=False).replace("<", "\\u003c")
    + "</script></body></html>"
)
# 3 associations x 3 target levels x 3 scores x 2 regional models = 54 per ballot.
assert "—" not in html
(ROOT / "docs/nexus_btg_28092026.html").write_text(injetar(html) + "\n")

with (ROOT / "docs/assets/nexus_btg_28092026_cenarios.csv").open("w") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(
        [
            "turno",
            "associacao",
            "respostas",
            "regiao",
            "comparecimento_alvo",
            "lula_validos",
            "flavio_validos",
            "outros_validos",
        ]
    )
    for s in LV["scenarios"]:
        w.writerow(
            [
                s["ballot"],
                s["association"],
                s["score"],
                s["region_mode"],
                s["target"],
                *s["valid"][:2],
                sum(s["valid"][2:]),
            ]
        )
print("Built docs/nexus_btg_28092026.html")
