#!/usr/bin/env python3
"""Build the complete Datafolha dossier from extracted, validated evidence."""

import importlib.util
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
SLUG = "datafolha_14092026"
CEN = "pessoas16_efetivo"
spec = importlib.util.spec_from_file_location(
    "figs", ROOT / "scripts/datafolha-14092026-figures.py"
)
figs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figs)
D = json.loads((ASSETS / f"{SLUG}_data.json").read_text())
T = json.loads((ASSETS / f"{SLUG}_cruzamentos.json").read_text())["tabelas"]
R = D["reweight"]
F = D["transfer"]
TERR = D["territory"]
fmt = figs.fmt


def ref(page, kind=""):
    return (
        f'<a class="refs" href="fontes/{SLUG}{kind}.pdf#page={page}">PDF p. {page}</a>'
    )


def table(headers, rows):
    head = "".join(f'<th scope="col">{h}</th>' for h in headers)
    body = ""
    for row in rows:
        body += '<tr><th scope="row">' + str(row[0]) + "</th>"
        body += "".join(f"<td>{v}</td>" for v in row[1:]) + "</tr>"
    return (
        '<div class="table-scroll" tabindex="0"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + body
        + "</tbody></table></div>"
    )


def figure(fn, caption):
    return (
        '<figure><div class="chart-scroll" tabindex="0">'
        + fn(D)
        + "</div><figcaption>"
        + caption
        + "</figcaption></figure>"
    )


def start(slug, number, title, lead):
    return f'<section id="{slug}"><div class="section-head"><p class="kicker">{number} / AUDITORIA</p><h2>{title}</h2><p class="lead">{lead}</p></div>'


def flat(key):
    rows = {}
    for block in T[key]["blocks"].values():
        for label, cols in block["rows"].items():
            rows.setdefault(label, {}).update(cols)
    return rows


def main():
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Datafolha: a renda muda o placar | Arvor · 14/09/2026</title>
<meta name="description" content="Dossiê Datafolha BR-01833/2026: reponderação PNAD, série histórica, transferências medidas, questionário e 303 setores auditados.">
<link rel="canonical" href="https://brasil.arvor.co/{SLUG}.html"><meta property="og:type" content="article"><meta property="og:title" content="Datafolha: a renda muda o placar"><meta property="og:description" content="46 × 44 publicados. Sensibilidade de renda: 42,41 × 47,89. O relatório completo, sob auditoria."><meta property="og:url" content="https://brasil.arvor.co/{SLUG}.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><link rel="stylesheet" href="assets/{SLUG}.css"><script src="assets/{SLUG}.js" defer></script></head>
<body><a class="skip" href="#renda">Pular para o conteúdo</a><header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / BRASIL</a><span>CADERNO DE PESQUISAS · Nº 14.09.26</span><a href="reponderacao_pnad.html#pesquisa-datafolha_2026-09-10">AGREGADOR PNAD ↗</a></div>
<p class="kicker">DATAFOLHA / BR-01833/2026 / RELATÓRIO COMPLETO</p><h1>A renda muda<br><em>o placar.</em></h1><p class="deck">O empate publicado sobrevive de uma semana para outra. A sensibilidade à renda também: com a referência principal da PNAD anual 2025, Flávio fica numericamente à frente nos dois turnos.</p>
<div class="score-grid"><div><span>2º TURNO · PUBLICADO</span><b><i class="lula">46</i> <small>×</small> <i class="flavio">44</i></b><p>Lula / Flávio</p></div><div><span>2º TURNO · SENSIBILIDADE PNAD</span><b><i class="lula">42,41</i> <small>×</small> <i class="flavio">47,89</i></b><p>Renda efetiva · pessoas de 16 anos ou mais</p></div></div>
<p class="boundary">Análise de uma margem de ponderação. Não é previsão, resultado corrigido nem reprodução dos pesos conjuntos do instituto.</p><p class="meta">Campo: 8–10 de setembro · Divulgação: 11/09 · Dossiê: 14/09/2026<br>2.002 entrevistas · 125 municípios · Folha de S.Paulo e TV Globo</p></div></header>
<nav aria-label="Capítulos"><div class="wrap"><a href="#renda">01 Renda</a><a href="#historico">02 Histórico</a><a href="#voto-util">03 Voto útil</a><a href="#transferencia">04 Sankey</a><a href="#alternativos">05 Alternativas</a><a href="#territorio">06 Território</a><a href="#questionario">07 Questionário</a><a href="#limites">08 Limites</a><a href="#tabelas">09 Tabelas</a><a href="#fontes">10 Fontes</a></div></nav><main class="wrap">"""
    html += start(
        "renda",
        "01",
        "O que muda quando<br>a renda pesa diferente.",
        "A faixa de até dois salários mínimos representa 51,78% das bases com renda declarada. Na referência principal da PNAD, são 35,19%. Dentro dessa faixa, Lula tem 55% e Flávio, 35% no segundo turno.",
    )
    html += f"<p>O PDF completo resolve a lacuna da divulgação preliminar: as bases ponderadas são <strong>991, 689 e 234</strong>, nas três faixas de renda. As mesmas contagens aparecem nas tabelas dos dois turnos. A soma é 1.914; outras 88 entrevistas ponderadas não estão representadas nesses recortes. A conta usa as bases da intenção de voto. {ref(42)} {ref(49)}</p>"
    html += figure(
        figs.income,
        "Percentuais normalizados entre os 1.914 casos representados no cruzamento de renda. Benchmark: PNADC anual 2025, visita 1, renda domiciliar efetiva, pessoas 16+, peso V1032. A renda é familiar total, não renda per capita.",
    )
    html += table(
        [
            "Faixa familiar mensal",
            "Base ponderada",
            "Lula 1º",
            "Flávio 1º",
            "Lula 2º",
            "Flávio 2º",
        ],
        [
            ["Até 2 SM / R$ 3.242", "991", "47%", "27%", "55%", "35%"],
            ["2 a 5 SM / R$ 3.242–8.105", "689", "31%", "42%", "39%", "52%"],
            ["Mais de 5 SM / acima de R$ 8.105", "234", "27%", "47%", "32%", "60%"],
        ],
    )
    rows = []
    for label, key in [
        ("Publicado", None),
        ("PNAD · pessoas 16+ · efetivo", CEN),
        ("PNAD · pessoas 16+ · habitual", "pessoas16_habitual"),
        ("PNAD · domicílios · efetivo", "domicilios_efetivo"),
    ]:
        values = [
            (
                R["turnos"][t]["publicado"]
                if key is None
                else R["turnos"][t]["cenarios"][key]["ajustado"]
            )
            for t in ["1t", "2t"]
        ]
        rows.append(
            [label] + [fmt(v[c]) + "%" for v in values for c in ["lula", "flavio"]]
        )
    html += table(["Referência", "Lula 1º", "Flávio 1º", "Lula 2º", "Flávio 2º"], rows)
    html += "<p><strong>O segundo turno muda de sinal nas três referências.</strong> No primeiro, a referência por domicílios ainda deixa Lula 0,34 ponto acima de Flávio. Esse contraponto delimita o resultado: a inversão do primeiro turno depende da unidade de ponderação; a do segundo aparece nos três exercícios.</p>"
    html += '<div class="formula">ajustado = publicado + Σ [(peso PNAD − peso do perfil publicado) × voto na faixa]</div>'
    html += "<p>A âncora é sempre o placar nacional publicado. Somamos apenas a variação provocada pela troca dos pesos de renda. Isso preserva o resíduo de arredondamento e evita vender a média de três recortes como reprodução exata da estimativa conjunta do instituto. A referência é a mesma base anual 2025 usada no agregador, expressa em preços de abril de 2026; os cortes nominais do questionário são convertidos por IPCA. Como o IPCA disponível não alcança todo o período de campo, o último índice disponível é usado, conforme a regra comum do agregador.</p>"
    q = D["missing_share_preserved"]["2t"]
    html += f'<aside><b>E as 88 entrevistas fora do cruzamento?</b>O exercício principal aplica o delta da renda declarada à âncora nacional. Num teste mais conservador, aplicando apenas 1.914/2.002 desse delta e mantendo intacta a contribuição dos demais, o segundo turno fica em Lula <strong>{fmt(q["lula"])}%</strong> e Flávio <strong>{fmt(q["flavio"])}%</strong>. O sinal permanece. Não é possível identificar o voto ou a renda dos casos ausentes sem os microdados.</aside>'
    html += "<details><summary>Conferência independente da extração</summary><p>As tabelas foram extraídas do texto nativo do anexo, com validação do número de colunas, rótulos e bases. Sexo e região são partições fechadas de 2.002 casos e recompõem os dois finalistas perto dos totais publicados.</p>"
    html += (
        table(
            ["Tabela / dimensão", "Candidato", "Recomposto", "Publicado", "Base"],
            [
                [
                    ("1º turno" if p["tabela"] == "estimulada_b" else "2º turno")
                    + " / "
                    + p["dimensao"],
                    p["candidato"],
                    fmt(p["recomposto"]) + "%",
                    str(p["publicado"]) + "%",
                    p["base"],
                ]
                for p in D["proofs"]
                if p["dimensao"] != "renda"
            ],
        )
        + "</details></section>"
    )

    html += start(
        "historico",
        "02",
        "O segundo turno<br>continua no mesmo lugar.",
        "Entre 3 e 11 de setembro, Lula segue em 46% e Flávio em 44%. O intervalo entre os candidatos também quase não se altera depois da padronização por renda.",
    )
    html += figure(
        figs.history,
        "Série recalculada com o motor e o benchmark atuais do agregador. Cada onda conserva suas bases e seus votos por renda; aplica-se a mesma regra de correção monetária dos cortes. Pequenas diferenças frente a dossiês antigos podem refletir a versão da referência de preços.",
    )
    histrows = []
    for h in D["history"]:
        t = h["turnos"]["2t"]
        p = t["publicado"]
        a = t["cenarios"][CEN]["ajustado"]
        date = h["divulgacao"]
        histrows.append(
            [
                date[8:] + "/" + date[5:7],
                f'{fmt(p["lula"],0)} × {fmt(p["flavio"],0)}',
                f'{fmt(a["lula"])} × {fmt(a["flavio"])}',
                fmt(a["lula"] - a["flavio"]) + " pp",
            ]
        )
    html += table(
        [
            "Divulgação",
            "Publicado · Lula × Flávio",
            "PNAD · Lula × Flávio",
            "Diferença PNAD · Lula − Flávio",
        ],
        histrows,
    )
    html += f"<h3>O primeiro turno se aproxima; o segundo já incorporava essa disputa</h3><p>Na série sem Marçal apresentada pelo relatório, Lula e Flávio marcam, respectivamente, <strong>40 × 31, 41 × 31, 40 × 33, 39 × 33, 38 × 33 e 39 × 35</strong>, de maio até esta rodada. Na última semana, Flávio cresce dois pontos no primeiro turno; Lula cresce um. No segundo, nenhum se move. A combinação é compatível com consolidação antecipada de votos, mas não identifica a motivação individual nem prova uma migração entre ondas. {ref(5)}</p>"
    html += "<p>Um controle adicional mantém os votos por renda desta rodada e troca apenas o perfil da amostra pelo da rodada anterior. A mudança de composição reduz a diferença Lula menos Flávio em cerca de <strong>0,26 ponto</strong> em cada turno. Portanto, a redução publicada de um ponto no primeiro turno não pode ser atribuída integralmente à alteração desse perfil. Trata-se de decomposição descritiva, sem identificação causal.</p></section>"

    html += start(
        "voto-util",
        "03",
        "Consolidação não é<br>adesão incondicional.",
        "Flávio reúne 35% no primeiro turno e 44% no segundo. O relatório mede tanto a firmeza da escolha quanto a razão declarada para votar, em universos diferentes.",
    )
    html += table(
        [
            "Entre quem declara voto em…",
            "Já decidiu",
            "Vota pelas propostas",
            "Vota para evitar outro",
        ],
        [
            ["Lula", "84%", "71%", "22%"],
            ["Flávio", "81%", "58%", "35%"],
            ["Cury", "43%", "62%", "27%"],
        ],
    )
    html += f"<p>As porcentagens por candidato vêm do texto analítico da página 7. A resposta “evitar outro” é mais frequente entre os declarantes de Flávio do que entre os de Lula, enquanto ambas as bases têm decisão majoritariamente firme. Isso sustenta uma leitura de consolidação com componente de oposição; não autoriza classificar todos esses votos como voto útil nem somar as duas perguntas. {ref(7)}</p>"
    html += f'<p>Na pergunta de definição, 25% ainda podem mudar. A base ponderada é <strong>1.931</strong>, incluindo quem escolheu branco/nulo e excluindo quem não indicou opção. Acrescentando os 71 casos fora dessa pergunta, o mercado aberto aproximado chega a <strong>{fmt(D["market"]["mercado_aberto_pct_aproximado"],1)}%</strong> do total. É uma medida de disponibilidade declarada, sem direção presumida: parte pode terminar em branco, nulo ou abstenção. {ref(54)}</p>'
    html += f"<aside><b>Três denominadores, três perguntas.</b>Intenção de voto: 2.002. Definição do voto: 1.931. Motivação da escolha: 1.821. A última exclui branco/nulo e indecisos. Uma base menor nessa tabela não é uma contagem alternativa da amostra de intenção de voto. {ref(55)}</aside>"
    html += f"<p>A rejeição total a Lula e a Flávio está em 46% para cada um. Como a pergunta admite múltiplas respostas, isso não constitui uma partição do eleitorado e não pode ser adicionado ao voto ou à indecisão. {ref(46)}</p></section>"

    html += start(
        "transferencia",
        "04",
        "Dois fluxos medidos.<br>O restante, explicitamente estimado.",
        "O Datafolha informa como os eleitores de Cury e Caiado respondem ao confronto Lula × Flávio. Essas proporções entram fixas; as bases de Lula e Flávio permanecem integralmente com seus candidatos por hipótese de consolidação.",
    )
    html += table(
        [
            "Origem no 1º turno",
            "Lula no 2º",
            "Flávio no 2º",
            "Não escolha · complemento",
        ],
        [["Cury", "37%", "39%", "24%"], ["Caiado", "33%", "45%", "22%"]],
    )
    html += f"<p>O texto informa margens de erro de ±9 pontos para o recorte Cury e ±11 para Caiado. Os 24% e 22% de não escolha são o complemento das duas intenções publicadas, sem separação entre branco/nulo e indecisos. A pequena diferença de destino entre os eleitores de Cury não identifica preferência estatisticamente distinta. {ref(8)}</p>"
    html += figure(
        figs.sankey,
        "Fitas sólidas: duas origens com percentuais medidos; na não escolha, complemento aritmético. Contorno pontilhado: duas bases consolidadas por hipótese. Fitas hachuradas: seis origens ajustadas por IPF. Não há saída das bases de Lula e Flávio para branco/nulo ou indecisos. Passe o ponteiro, toque ou use Tab para ler um elo.",
    )
    html += '<div class="flow-readout" aria-live="polite">Selecione uma fita para consultar sua origem, destino e natureza.</div>'
    html += f'<p>Os percentuais arredondados do primeiro turno somam <strong>103</strong>; os do segundo, <strong>99</strong>. Para que o fluxo feche, as origens são multiplicadas por 99/103. Assim, as bases desenhadas são 37,49 e 33,64 pontos, e os ganhos fora delas são <strong>{fmt(F["gains"][0])}</strong> para Lula e <strong>{fmt(F["gains"][1])}</strong> para Flávio. A razão é <strong>{fmt(F["ratio_flavio_lula"])}:1</strong>, ante <strong>{fmt(F["previous"]["ratio_flavio_lula"])}:1</strong> na rodada divulgada em 3/09, sob a mesma regra de fechamento. Sem esse ajuste, as subtrações diretas seriam +7 e +9, mas não produziriam um diagrama conservativo.</p>'
    html += "<details><summary>Hipóteses, IPF e sensibilidade à prior</summary><p>Depois de fixar as duas bases e os dois cruzamentos publicados, o ajuste proporcional iterativo fecha as margens residuais. A prior é ideológica e declarada: Renan e Zema majoritariamente para Flávio; Samara e o grupo de candidaturas menores de esquerda majoritariamente para Lula; branco/nulo e indecisos repartidos entre os três destinos. Esses últimos fluxos são estimativas, não medições.</p><p>Três priors são executadas. O JSON contém as matrizes e o mínimo/máximo de cada elo. A razão de consolidação não muda porque deriva das margens e da retenção fixada das bases; a repartição entre origens menores muda. O modelo é agregado e condicionado à hipótese de bases fiéis. Não acompanha eleitores individuais e não deve ser combinado com a reponderação PNAD como se houvesse microdados conjuntos.</p></details></section>"

    html += start(
        "alternativos",
        "05",
        "Flávio é o maior no total.<br>Cury é o contraponto obrigatório.",
        "O confronto alternativo com Cury chega a Lula 45% × Cury 43%. A diferença entre os adversários é de apenas um ponto no total, e Cury ultrapassa Flávio em alguns recortes publicados.",
    )
    altrows = []
    for a in D["alternatives"]:
        p = a["publicado"]
        v = a["reweight"]["cenarios"][CEN]["ajustado"]
        altrows.append(
            [
                a["nome"] + " " + ref(a["pagina"]),
                f'{p["lula"]} × {p["adversario"]}',
                str(p["branco_nulo"] + p["indecisos"]) + "%",
                f'{fmt(v["lula"])} × {fmt(v["adversario"])}',
                fmt(v["lula"] - v["adversario"]) + " pp",
            ]
        )
    html += table(
        [
            "Adversário",
            "Publicado · Lula × adversário",
            "Não escolha",
            "PNAD · Lula × adversário",
            "Diferença PNAD",
        ],
        altrows,
    )
    html += "<p>A comparação de cenários na mesma amostra mantém grande parte do contexto constante, mas não é um experimento causal randomizado. Ela mede substituição declarada. Caiado perde três pontos em relação a Flávio enquanto Lula permanece em 46%; o acréscimo aparece na não escolha. Zema e Renan perdem mais, com Lula também subindo para 48%.</p>"
    cury = D["alternatives"][-1]
    wins = [r for r in cury["recortes"] if r["delta_vs_flavio"] > 0]
    html += table(
        ["Recorte em que Cury supera Flávio", "Flávio", "Cury", "Diferença descritiva"],
        [
            [
                r["recorte"],
                str(r["adversario"] - r["delta_vs_flavio"]) + "%",
                str(r["adversario"]) + "%",
                "+" + str(r["delta_vs_flavio"]) + " pp",
            ]
            for r in wins
        ],
    )
    html += "<p>Na renda de 2 a 5 SM, Cury tem 54% contra 52% de Flávio; no superior, 55% contra 51%. Essas diferenças pontuais não têm teste pareado disponível. No exercício nacional de renda, Cury chega a 47,62%, praticamente o mesmo nível de Flávio, 47,89%, mas Lula tem menos apoio no confronto com Cury. A hipótese de que só Flávio consegue consolidar o voto adversário é mais forte do que os dados permitem afirmar.</p></section>"

    html += start(
        "territorio",
        "06",
        "O anexo fecha.<br>A composição merece ser lida.",
        "O documento territorial contém 303 setores distintos e 125 municípios. As contagens somam exatamente 2.002 entrevistas, de acordo com o tamanho anunciado.",
    )
    html += f'<p>O PDF separou as colunas: locais nas páginas 1–4 e números de entrevistas nas páginas 6–9. A extração alinha as linhas de cada par de páginas e valida a soma nacional e as cinco regiões contra o perfil da página 5. São 25 UFs; Amapá e Roraima não aparecem. Isso descreve a cobertura desta seleção, sem demonstrar por si só viés no resultado. {ref(1,"_bairros")} {ref(5,"_bairros")}</p>'
    html += table(
        [
            "Faixa de renda",
            "Perfil do anexo territorial",
            "Base ponderada do voto",
            "Diferença de contagem",
        ],
        [
            [name, a, b, b - a]
            for name, a, b in zip(
                ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM", "Não representado nas faixas"],
                TERR["perfil_campo"]["renda"],
                [991, 689, 234, 88],
                strict=True,
            )
        ],
    )
    html += "<p>Até 2 SM são 51,30% no perfil do anexo territorial e 49,50% do total das bases ponderadas de voto. Entre os que declararam renda, o segundo valor vira 51,78%, usado na conta. A diferença documenta perfis distintos nos dois arquivos; não permite reconstruir pesos individuais. O registro prevê ajustes e informa fator previsto 1, o que não comprova que cada peso final tenha sido exatamente 1.</p>"
    html += table(
        [
            "Comparação com o anexo atual",
            "Municípios em comum",
            "Entrevistas atuais nesses municípios",
            "Setores em comum",
            "Setores atuais novos",
        ],
        [
            [
                a["onda"],
                a["municipios_repetidos"],
                a["entrevistas_em_municipios_repetidos"],
                a["setores_repetidos"],
                fmt(a["setores_novos_pct"], 1) + "%",
            ]
            for a in TERR["comparacoes"]
        ],
    )
    html += '<p>A referência aqui é julho ou agosto, não a rodada de 3 de setembro, cujo anexo não foi incorporado a esta comparação. O mapa municipal também muda: 71 dos 125 municípios reaparecem em relação a agosto, contendo 1.246 entrevistas atuais. Apenas 19 dos 303 setores coincidem. Rotação territorial é diferente de mudança na composição social; nenhuma delas identifica a intenção de voto dos lugares sem observação eleitoral apropriada.</p><p><a href="assets/datafolha_14092026_territorio.csv">Baixar os 303 setores e suas contagens</a> · <a href="assets/datafolha_14092026_territorio.json">Conferências e comparação territorial</a></p></section>'

    html += start(
        "questionario",
        "07",
        "O que foi perguntado<br>e o que este PDF mostra.",
        "O questionário registrado tem 11 páginas. O relatório recebido tem 57. A comparação revela variáveis coletadas que não aparecem como cruzamentos neste arquivo.",
    )
    html += table(
        ["Bloco registrado", "Página do questionário", "Presença neste relatório"],
        [
            [
                "Intenção espontânea, situações A e B, rejeição e cinco confrontos",
                "1–2",
                "Tabelas completas no anexo",
            ],
            [
                "Definição e motivação do voto",
                "2",
                "Tabelas com universos condicionais diferentes",
            ],
            [
                "Voto em 2022, participação em 2024, comparecimento sem obrigação e interesse político",
                "3",
                "Sem tabulação própria neste PDF",
            ],
            [
                "Escala bolsonarista–petista e escala esquerda–direita",
                "3",
                "Texto usa não alinhados; anexo não publica essas dimensões",
            ],
            [
                "Afirmações sobre STF e perguntas de conhecimento/efeito eleitoral sobre Moraes, Vorcaro e Mendonça",
                "3–4",
                "Sem resultados neste PDF",
            ],
            [
                "Ocupação, partido, religião, escolaridade, renda e cor",
                "5–7",
                "Perfil e parte dos recortes; sem matriz conjunta",
            ],
        ],
    )
    html += f'<p>A ausência acima se refere estritamente ao arquivo recebido. Não afirma que os resultados não tenham sido ou não venham a ser divulgados em outras matérias. O questionário contém perguntas condicionais e escalas distintas; a categoria “não alinhado” de uma escala não substitui a posição esquerda–direita da outra. {ref(3,"_questionario")}</p>'
    html += "<h3>Uma referência de 2024, um cartão em reais de 2026</h3>"
    html += f'<p>O plano amostral cita PNADC-A 2024, Censo 2022 e estimativa populacional de 2025 entre suas referências. Para renda, informa 49% até 2 SM, 47% acima e 4% sem resposta. O cartão apresenta limites nominais de 2026: R$ 3.242 para dois salários e R$ 8.105 para cinco. Essa diferença de referência temporal é uma escolha auditável e justifica testar uma PNAD mais recente. O registro não fornece a tabela conjunta que permitiria isolar quanto de cada ajuste veio de renda, escolaridade ou outras margens. {ref(6,"_questionario")}</p>'
    html += "<p>O registro prevê campo até 11/09; o relatório e o anexo territorial informam execução de 8 a 10/09. O dossiê usa as datas efetivas dos documentos, preservando a previsão no arquivo do registro. O dia 14/09 é a data deste dossiê e de recebimento do PDF, não a data de divulgação da pesquisa.</p></section>"

    html += start(
        "limites",
        "08",
        "Precisão de cálculo<br>não é certeza eleitoral.",
        "O segundo turno publicado tem dois pontos de diferença. Mesmo sob amostragem aleatória simples, a margem de 95% para essa diferença é de aproximadamente 4,16 pontos.",
    )
    html += '<p>A margem da diferença considera a covariância negativa entre respostas mutuamente exclusivas. Não se obtém somando, subtraindo ou aplicando duas vezes a margem de cada candidato. No primeiro turno, a diferença de quatro pontos tem margem aproximada de 3,76 sob a mesma hipótese simples; um efeito de desenho de apenas 1,13 já elimina a separação nesse cálculo. O desenho real, os pesos finais e a covariância necessária aos demais contrastes não estão disponíveis.</p><div class="formula">ME(diferença) ≈ 1,96 × √[(pL + pF − (pL − pF)²) / n]</div><p>Os decimais da reponderação expressam a aritmética de uma sensibilidade. Não acompanham intervalo de confiança eleitoral recalculado. O exercício altera uma margem, mantém as preferências dentro dos grupos e não elimina seleção em pontos de fluxo, erro de resposta, arredondamento ou relações entre dimensões.</p>'
    html += table(
        ["Dimensão do anexo de voto", "Base coberta", "Fora das colunas", "Cobertura"],
        [
            [v["dimensao"], v["base"], v["faltam"], fmt(v["cobertura_pct"], 1) + "%"]
            for v in D["coverage"]
        ],
    )
    html += "<p>Seis das nove dimensões são partições fechadas. Renda, cor e religião deixam casos de fora. Não se devem somar recortes sobrepostos nem tratar a média de católicos e evangélicos como todo o país. O TSE é a referência adequada para sexo, idade e território do eleitorado; PNAD é usada aqui para renda. Nenhuma inferência de voto individual é feita a partir desses cadastros.</p></section>"

    html += start(
        "tabelas",
        "09",
        "Quinze tabelas.<br>Extração conferível.",
        "O anexo foi convertido integralmente em dados estruturados: 45 blocos, com a página do PDF, rótulos, percentuais e bases ponderadas. Abra uma tabela para conferir cada dimensão.",
    )
    names = {
        "espontanea": "Intenção espontânea",
        "estimulada_a": "1º turno · situação A, com Marçal",
        "validos_a": "Votos válidos · situação A",
        "estimulada_b": "1º turno · situação B, sem Marçal",
        "validos_b": "Votos válidos · situação B",
        "rejeicao": "Rejeição múltipla",
        "turno2_flavio": "2º turno · Flávio",
        "turno2_caiado": "2º turno · Caiado",
        "turno2_zema": "2º turno · Zema",
        "turno2_renan": "2º turno · Renan",
        "turno2_cury": "2º turno · Cury",
        "definicao": "Definição do voto",
        "motivacao": "Motivação do voto",
        "avaliacao": "Avaliação do governo",
        "aprovacao": "Aprovação do trabalho presidencial",
    }
    for key, tab in T.items():
        html += f"<details><summary>{names[key]}</summary>"
        for block_index, block in enumerate(tab["blocks"].values(), start=1):
            columns = block["columns"]
            html += f'<p class="table-source">{ref(block["pdf_page"])} · Bloco {block_index}</p>'
            cells = [
                [escape(label)]
                + ["·" if vals[c] is None else str(vals[c]) for c in columns]
                for label, vals in block["rows"].items()
            ]
            cells.append(["Base ponderada"] + [block["base"][c] for c in columns])
            html += table(["Resposta / %", *columns], cells)
        html += "</details>"
    html += '<p>O ponto “·” representa o traço do PDF. Para a conta, ele é tratado como zero, sem atribuir uma fração não publicada. Votos válidos têm universo próprio e não são misturados com percentuais do eleitorado total. <a href="assets/datafolha_14092026_cruzamentos.json">Baixar todas as tabelas em JSON</a>.</p></section>'

    html += start(
        "fontes",
        "10",
        "Documento, conta<br>e trilha de reprodução.",
        "O laudo parte de três PDFs preservados e de uma captura textual do registro público. Os arquivos derivados permitem refazer a leitura sem transcrever percentuais à mão.",
    )
    html += f"""<ol><li><a href="fontes/{SLUG}.pdf">Relatório Datafolha completo, 57 páginas</a>. Pesquisa 814284, campo 8–10/09, divulgação 11/09. Arquivo fornecido em Downloads em 14/09/2026.</li><li><a href="fontes/{SLUG}_questionario.pdf">Questionário registrado, 11 páginas</a> e <a href="fontes/{SLUG}_bairros.pdf">anexo territorial, 10 páginas</a>. Baixados do <a href="https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml">PesqEle</a>, registro BR-01833/2026, em 14/09.</li><li><a href="fontes/{SLUG}_registro.txt">Registro público em texto</a>. Referências amostrais, cronograma e plano de ponderação.</li><li><a href="assets/{SLUG}_data.json">Base analítica</a>, <a href="assets/{SLUG}_cruzamentos.json">cruzamentos extraídos</a>, <a href="assets/{SLUG}_fontes.json">proveniência e hashes</a>.</li><li><a href="reponderacao_pnad.html#metodo">Método e referências da PNAD no agregador</a>. Mesma base, regras de renda, IPCA e definição dos cenários.</li></ol>
<details><summary>Páginas originais essenciais</summary><p>As reproduções abaixo são auxiliares de leitura; o PDF preservado é a fonte.</p>"""
    for p in [42, 49]:
        html += f'<figure><a href="fontes/{SLUG}.pdf#page={p}"><img src="img/{SLUG}/p{p}.png" loading="lazy" alt="Página {p} original do relatório com tabelas por renda"></a><figcaption>Relatório, página {p}.</figcaption></figure>'
    html += "</details><details><summary>Reproduzir a auditoria no repositório</summary><pre><code>python3 scripts/datafolha-14092026-fontes.py\npython3 scripts/datafolha-14092026-extract.py\npython3 scripts/datafolha-14092026-territorio.py\npython3 scripts/datafolha-14092026-audit.py\npython3 scripts/datafolha-14092026-build.py</code></pre><p>O relatório fornecido pelo usuário é preservado antes da extração. O primeiro comando baixa os dois anexos públicos, sem substituir o relatório. Históricos usam os registros arquivados no projeto e o motor comum de reponderação.</p></details>"
    html += f'<p class="hash">SHA-256 do relatório: {D["provenance"]["report_sha256"]}</p></section></main><footer class="wrap"><a href="index.html">Arvor / Brasil</a><p>Dossiê de 14 de setembro de 2026 · Dados publicados, hipóteses declaradas e reprodução aberta.</p></footer></body></html>'
    (ROOT / f"docs/{SLUG}.html").write_text(html + "\n")
    print(f"Wrote docs/{SLUG}.html ({len(html):,} characters)")


if __name__ == "__main__":
    main()
