#!/usr/bin/env python3
"""Build the September 21 dossier from auditable source tables and calculations."""

import importlib.util
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
SLUG = "datafolha_21092026"
CEN = "pessoas16_efetivo"
D = json.loads((ASSETS / f"{SLUG}_data.json").read_text())
T = json.loads((ASSETS / f"{SLUG}_cruzamentos.json").read_text())["tabelas"]
R, G, F = D["reweight"], D["geography"], D["transfer"]
spec = importlib.util.spec_from_file_location(
    "figs", ROOT / "scripts/datafolha-21092026-figures.py"
)
figs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figs)
fmt = figs.fmt
spec_gov = importlib.util.spec_from_file_location(
    "governor_view", ROOT / "scripts/datafolha-21092026-governadores-view.py"
)
governor_view = importlib.util.module_from_spec(spec_gov)
spec_gov.loader.exec_module(governor_view)


def ref(page, kind=""):
    return f'<a class="refs" href="fontes/{SLUG}{kind}.pdf#page={page}">PDF{(" estadual" if kind == "_estaduais" else "")} p. {page}</a>'


def table(headers, rows):
    return (
        '<div class="table-scroll" tabindex="0"><table><thead><tr>'
        + "".join(f'<th scope="col">{v}</th>' for v in headers)
        + "</tr></thead><tbody>"
        + "".join(
            '<tr><th scope="row">'
            + str(r[0])
            + "</th>"
            + "".join(f"<td>{v}</td>" for v in r[1:])
            + "</tr>"
            for r in rows
        )
        + "</tbody></table></div>"
    )


def section(ident, num, title, lead):
    return f'<section id="{ident}"><div class="section-head"><p class="kicker">{num} / AUDITORIA</p><h2>{title}</h2><p class="lead">{lead}</p></div>'


def figure(svg, caption):
    return f'<figure><div class="chart-scroll" tabindex="0">{svg}</div><figcaption>{caption}</figcaption></figure>'


def pair(values):
    return f'<span class="lula">{fmt(values["lula"])}</span> × <span class="flavio">{fmt(values["flavio"])}</span>'


def main():
    adjusted = R["turnos"]["2t"]["cenarios"][CEN]["ajustado"]
    h = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Datafolha: renda, Sudeste e os limites dos microdados | Arvor · 21/09/2026</title>
<meta name="description" content="Relatório completo: 46 × 44 publicados; sensibilidade PNAD 42,95 × 47,33. Comparação com SP, RJ e MG, limites de reconstrução e 13 tabelas auditadas.">
<link rel="canonical" href="https://brasil.arvor.co/{SLUG}.html"><meta property="og:type" content="article"><meta property="og:title" content="Datafolha: o empate e a régua da renda"><meta property="og:description" content="42,95 × 47,33 na sensibilidade PNAD. Sudeste conferido com as estaduais; reconstrução dos microdados testada."><meta property="og:url" content="https://brasil.arvor.co/{SLUG}.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><link rel="stylesheet" href="assets/{SLUG}.css"><script src="assets/{SLUG}.js" defer></script></head>
<body><a class="skip" href="#renda">Pular para o conteúdo</a><header class="hero"><div class="wrap"><div class="masthead"><a href="index.html">ARVOR / BRASIL</a><span>CADERNO DE PESQUISAS · 21.09.26</span><a href="reponderacao_pnad.html#pesquisa-datafolha_2026-09-17">AGREGADOR PNAD ↗</a></div><p class="kicker">DATAFOLHA / BR-04029/2026 / 50 PÁGINAS CONFERIDAS</p>
<h1>O empate.<br><em>A régua da renda.</em></h1><p class="deck">O placar nacional repete 46 × 44. A troca da referência de renda mantém Flávio numericamente à frente. O relatório completo permite conferir a conta, comparar o Sudeste e testar os limites da engenharia reversa.</p>
<div class="score-grid"><div><span>2º TURNO · PUBLICADO</span><b><i class="lula">46</i> <small>×</small> <i class="flavio">44</i></b><p>Lula / Flávio</p></div><div><span>2º TURNO · SENSIBILIDADE PNAD 2025</span><b><i class="lula">{fmt(adjusted["lula"])}</i> <small>×</small> <i class="flavio">{fmt(adjusted["flavio"])}</i></b><p>Renda domiciliar efetiva · pessoas de 16 anos ou mais</p></div></div>
<p class="boundary">Sensibilidade a uma margem de ponderação. Não é previsão, voto corrigido nem reprodução dos pesos conjuntos do instituto.</p><p class="meta">Campo: 15–17/09 · Divulgação: 17/09 · Relatório completo e dossiê: 21/09/2026<br>2.001 entrevistas no relatório · presencial em pontos de fluxo · Folha e TV Globo</p></div></header>
<nav aria-label="Capítulos"><div class="wrap"><a href="#renda">01 Renda</a><a href="#sudeste">02 Sudeste</a><a href="#governadores">02b Governadores</a><a href="#microdados">03 Microdados</a><a href="#historico">04 Série</a><a href="#transferencia">05 Transferências</a><a href="#documentos">06 Documentos</a><a href="#tabelas">07 Tabelas</a><a href="#fontes">08 Fontes</a></div></nav><main class="wrap">"""
    h += section(
        "renda",
        "01",
        "A conta começa<br>nas bases certas.",
        "Até dois salários mínimos são 51,86% da base com renda publicada. Na PNAD anual 2025, pela referência principal da análise, essa parcela é de 35,19%.",
    )
    h += f"<p>O anexo informa <strong>992, 655 e 266</strong> casos ponderados nas três faixas de renda, tanto no primeiro como no segundo turno. São 1.913 de 2.001; os outros 88 não aparecem nesses cruzamentos. As bases são da intenção de voto, não da pergunta de motivação. {ref(35)} {ref(42)}</p>"
    income = figs.income(D).replace(
        "Renda: perfil de 51,78/36,00/12,23% contra PNAD de 35,19/39,26/25,55%",
        "Renda: perfil de 51,86/34,24/13,90% contra PNAD de 35,19/39,26/25,55%",
    )
    h += figure(
        income,
        "Bases normalizadas entre os casos com renda publicada. PNADC anual 2025, visita 1, peso V1032; renda domiciliar total efetiva, pessoas 16+. Cortes nominais de 2026 convertidos para a referência de preços do benchmark pelo IPCA. Não é renda per capita.",
    )
    rows = T["turno2_flavio"]["blocks"]["bloco2"]["rows"]
    first = T["estimulada_b"]["blocks"]["bloco2"]["rows"]
    h += table(
        [
            "Renda familiar",
            "Base ponderada",
            "Lula 1º",
            "Flávio 1º",
            "Lula 2º",
            "Flávio 2º",
        ],
        [
            [
                name,
                base,
                first["Lula (PT)"][key],
                first["Flavio Bolsonaro (PL)"][key],
                rows["Lula (PT)"][key],
                rows["Flavio Bolsonaro (PL)"][key],
            ]
            for name, base, key in zip(
                ["Até 2 SM / R$ 3.242", "2 a 5 SM / até R$ 8.105", "Mais de 5 SM"],
                [992, 655, 266],
                ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"],
                strict=True,
            )
        ],
    )
    variants = []
    for title, key in [
        ("Publicado", None),
        ("PNAD · pessoas 16+ · efetiva", CEN),
        ("PNAD · pessoas 16+ · habitual", "pessoas16_habitual"),
        ("PNAD · domicílios · efetiva", "domicilios_efetivo"),
    ]:
        vals = [
            R["turnos"][t]["publicado"]
            if key is None
            else R["turnos"][t]["cenarios"][key]["ajustado"]
            for t in ["1t", "2t"]
        ]
        variants.append(
            [
                title,
                pair(vals[0]),
                pair(vals[1]),
                fmt(vals[1]["lula"] - vals[1]["flavio"]) + " pp",
            ]
        )
    h += table(
        [
            "Referência",
            "1º turno · Lula × Flávio",
            "2º turno · Lula × Flávio",
            "Diferença no 2º",
        ],
        variants,
    )
    h += '<div class="formula">Sensibilidade = placar publicado + Σ (peso PNAD − peso publicado) × voto na faixa</div>'
    h += f"<p>A âncora conserva o placar nacional e aplica apenas a diferença entre as duas composições de renda. Se aplicarmos o delta somente aos 95,60% com renda publicada, mantendo a parcela restante intacta, o segundo turno fica em <strong>{pair(D['missing_share_preserved']['2t'])}</strong>. A inversão numérica permanece.</p>"
    h += f'<aside><b>O registro ainda usa PNADC-A 2024.</b>A referência declarada é 49% até 2 SM, 47% acima e 4% sem resposta, com fator de renda previsto igual a 1. O questionário usa os valores nominais de 2026. Atualizar a renda é um teste pertinente, mas a PNAD cobre residentes, não um cadastro de eleitores; não controla comparecimento nem seleção nos pontos de fluxo. <a href="fontes/{SLUG}_registro.txt">Registro</a> · {ref(7, "_questionario")}</aside>'
    h += "<details><summary>Precisão, arredondamento e o limite da fórmula</summary><p>As duas casas decimais servem para reproduzir a conta, não representam precisão eleitoral. Não há pesos individuais, estratos, conglomerados e covariâncias suficientes para um intervalo de confiança da reponderação. O delta ancorado também pode gerar resíduo negativo em candidatura publicada como zero: Edmilson fica em −0,17 ponto no cálculo mecânico do primeiro turno. Isso é limite do uso de margens arredondadas, não intenção de voto negativa; por isso não publicamos esse resíduo como estimativa de apoio.</p></details></section>"
    h += section(
        "sudeste",
        "02",
        "No Sudeste deste relatório,<br>Flávio está à frente.",
        "A página 42 traz Lula 42% e Flávio 46%. No primeiro turno, são 34% e 37%. A hipótese de Lula liderar esta região não se confirma nas células do PDF.",
    )
    h += f'<p>A comparação correta usa o mesmo confronto, votos totais e datas identificadas. As estaduais encontradas têm campo em <strong>8–10/09</strong>, anterior ao novo nacional de 15–17/09. Por isso, o primeiro controle é o Sudeste nacional da semana anterior: <strong>Lula 42% × Flávio 47%</strong>, colhido também em 8–10/09. {ref(42)} <a class="refs" href="fontes/datafolha_14092026.pdf#page=49">Nacional anterior p. 49</a></p>'
    sr = []
    for s in G["states"]:
        sr.append(
            [
                s["uf"],
                s["lula"],
                s["flavio"],
                fmt(100 * s["southeast_weight"]) + "%",
                f"{s['n']:,}".replace(",", "."),
                f"±{s['moe']} pp",
                ref(s["page"], "_estaduais"),
            ]
        )
    sr.append(
        [
            "ES",
            "Não localizado",
            "Não localizado",
            fmt(100 * G["weights"]["ES"]) + "%",
            "Não localizado",
            "Não localizado",
            "Fora do relatório consultado",
        ]
    )
    h += table(
        [
            "Estado",
            "Lula",
            "Flávio",
            "Peso TSE no Sudeste",
            "Entrevistas",
            "Margem declarada",
            "Fonte",
        ],
        sr,
    )
    h += "<p><strong>Onde Flávio fica atrás?</strong> Apenas em Minas Gerais entre as três estaduais localizadas, por um ponto, dentro da margem declarada. SP e RJ mostram vantagem numérica de Flávio. O Espírito Santo permanece uma lacuna documental: o relatório conjunto cobre SP, RJ, MG, PE e DF, e a busca no acervo público do instituto não localizou uma estadual capixaba até 21/09.</p>"
    h += f"<p>SP, RJ e MG representam <strong>{fmt(100 * (1 - G['weights']['ES']))}%</strong> do eleitorado do Sudeste. Ponderados pelo TSE e normalizados apenas entre esses três estados, resultam em <strong>{pair(G['known_conditional'])}</strong>. Não é uma nova pesquisa regional: falta o ES, e somar pesquisas não reconstrói a amostra nacional. A proximidade com o 42 × 47 regional do mesmo campo <strong>não aponta uma contradição clara</strong>.</p>"
    h += "<p>Os pesos vêm do perfil TSE gerado em 01/07/2026, competência junho, disponível no acervo. Não usamos média simples dos estados nem seus tamanhos de amostra como pesos eleitorais. Também não confundimos voto total com voto válido: a normalização dos válidos deve vir depois da agregação dos votos totais.</p>"
    h += f"<details><summary>Quanto o ES ausente permite variar a conta?</summary><p>Fixando os pontos publicados dos outros três estados, Lula no Sudeste poderia ficar entre {fmt(G['bounds']['lula'][0])}% e {fmt(G['bounds']['lula'][1])}%; Flávio, entre {fmt(G['bounds']['flavio'][0])}% e {fmt(G['bounds']['flavio'][1])}%. Os máximos não podem ocorrer juntos. O intervalo aritmético da diferença Lula menos Flávio é de {fmt(G['gap_bounds'][0])} a {fmt(G['gap_bounds'][1])} pontos, permitindo qualquer divisão dos votos capixabas. Não são intervalos de confiança: congelam estimativas arredondadas e ignoram o erro amostral.</p><p>Tentar deduzir o voto capixaba pela diferença entre pesquisas amplifica cada ponto regional por <strong>{fmt(1 / G['weights']['ES'])}</strong>. A igualdade exata entre os pontos dos candidatos exigiria ES em 24,39 × 49,36 para a regional antiga, ou 24,39 × 27,17 para a nova. Esses resíduos algébricos não medem o ES; mudam violentamente com arredondamento, amostras e datas. Não os usamos para atribuir um estado a um candidato.</p></details>"
    h += '<div class="simulation"><h3>Explore o peso do estado ausente</h3><p>Hipótese ilustrativa para o ES, mantendo SP, RJ e MG nos pontos publicados. Não é pesquisa nem previsão.</p><label for="es-lula">Lula no ES <output id="es-lula-out">40%</output></label><input id="es-lula" type="range" min="0" max="100" value="40"><label for="es-flavio">Flávio no ES <output id="es-flavio-out">50%</output></label><input id="es-flavio" type="range" min="0" max="100" value="50"><p id="es-result" aria-live="polite"></p><noscript>Ative JavaScript para explorar. A tabela e os limites acima continuam disponíveis.</noscript></div>'
    h += f"<p>No anexo territorial do novo nacional, o Sudeste tem 840 entrevistas de campo: SP 448, MG 196, RJ 168 e ES 28. Na tabela de voto, a base regional ponderada é 838. Os recortes estaduais de voto dessa amostra nacional não foram publicados; não podemos identificar em qual UF ela diverge das pesquisas estaduais independentes. {ref(3, '_bairros')} {ref(4, '_bairros')}</p></section>"
    h += governor_view.render(table, fmt)
    h += section(
        "microdados",
        "03",
        "Reproduzir as margens<br>não recupera as pessoas.",
        "É possível construir bases sintéticas compatíveis com partes do relatório. Isso não identifica as respostas originais, os pesos individuais nem as correlações que não foram publicadas.",
    )
    h += "<p>O relatório cruza cada resposta com sexo, idade, renda e outras características separadamente. Ele não revela, por exemplo, a distribuição conjunta de <strong>voto × renda × região × sexo</strong>. A mesma proporção nacional de pessoas de baixa renda e a mesma votação no Sudeste podem esconder associações muito diferentes entre renda e voto dentro da região.</p>"
    h += '<div class="finding-grid"><div><b>128</b><span>células possíveis na projeção testada</span></div><div><b>32</b><span>restrições lineares independentes</span></div><div><b>96</b><span>dimensões do núcleo linear antes das restrições de não negatividade</span></div></div>'
    h += "<p>Testamos quatro respostas de segundo turno, quatro categorias de renda (incluindo a renda não publicada), quatro regiões e dois sexos. Primeiro encontramos margens compatíveis com os inteiros do PDF, aceitando até meio ponto de arredondamento e tratando as bases ponderadas como exatas. Depois fixamos essas mesmas margens não arredondadas e procuramos dois extremos por programação linear.</p>"
    h += table(
        [
            "Duas soluções agregadas",
            "Lula + até 2 SM + Sudeste, como % do total nacional",
            "Margens de voto × renda, região e sexo",
        ],
        [
            [
                "Solução A",
                fmt(D["identification_range"][0]) + "%",
                "Idênticas nas duas soluções",
            ],
            [
                "Solução B",
                fmt(D["identification_range"][1]) + "%",
                "Idênticas nas duas soluções",
            ],
        ],
    )
    h += "<p>O grupo oculto pode passar de zero a 17,38% da massa ponderada nacional nessas duas soluções, sem alterar nenhuma das projeções usadas no teste. São certificados de não identificação <strong>desta projeção da página 42</strong>, não bases individuais recuperadas e não um ajuste de todas as perguntas do relatório. Acrescentar outras restrições poderia estreitar esse intervalo.</p>"
    h += "<aside><b>Conclusão da engenharia reversa</b>Vale para verificar consistência, obter limites e testar hipóteses de dependência. Uma base sintética única produzida por IPF ou máxima entropia completaria o que falta com suposições; não acrescentaria observações. Para reponderar conjuntamente TSE + PNAD e estimar incerteza com mais segurança, precisamos da base anonimizada real, pesos finais e informações do desenho amostral.</aside>"
    h += f'<p>O problema de identificar relações não observadas também é central na literatura de <a href="https://ec.europa.eu/eurostat/web/products-statistical-working-papers/-/ks-ra-13-020">statistical matching do Eurostat</a>. Aqui publicamos as células agregadas e as projeções comuns para permitir conferência: <a href="assets/{SLUG}_identificacao.json">dois certificados e restrições em JSON</a>.</p></section>'
    h += section(
        "historico",
        "04",
        "Mesmo placar.<br>Composição diferente.",
        "As últimas duas ondas publicam 46 × 44. Sob a mesma referência PNAD, a diferença numérica também favorece Flávio, mas diminui.",
    )
    hist = []
    for v in D["history"]:
        day = v["field"]["fim"]
        a = v["turnos"]["2t"]
        b = a["cenarios"][CEN]["ajustado"]
        hist.append(
            [
                day[8:10] + "/" + day[5:7],
                pair(a["publicado"]),
                pair(b),
                fmt(b["lula"] - b["flavio"]) + " pp",
            ]
        )
    h += table(
        [
            "Fim do campo · 2026",
            "Publicado · Lula × Flávio",
            "Mesma PNAD · Lula × Flávio",
            "Diferença sob PNAD",
        ],
        hist,
    )
    h += "<p>Na onda anterior, a sensibilidade era 42,41 × 47,89; agora, 42,95 × 47,33. Essa aproximação descritiva de cerca de 1,10 ponto na diferença não é tendência estatisticamente demonstrada. Variam os votos por faixa e suas bases, e faltam covariâncias para testar a mudança.</p></section>"
    h += section(
        "transferencia",
        "05",
        "Duas origens medidas.<br>O restante exige hipóteses.",
        "O texto do próprio Datafolha informa como eleitores de Cury e Caiado responderam ao segundo turno. Essas duas linhas entram como medições publicadas; as outras não.",
    )
    h += table(
        [
            "Eleitorado no 1º turno",
            "Lula no 2º",
            "Flávio no 2º",
            "Não escolha, por complemento",
            "Margem do recorte",
        ],
        [
            ["Cury", "32%", "44%", "24%", "±9 pp"],
            ["Caiado", "27%", "42%", "31%", "±11 pp"],
        ],
    )
    h += f"<p>A página 7 publica os destinos Lula e Flávio; o restante é complemento aritmético, sem separar branco/nulo de indecisos. Os erros dos recortes são muito maiores que o erro nacional. {ref(7)}</p>"
    h += figure(
        figs.sankey(D),
        "Fitas sólidas: duas origens medidas. Fitas hachuradas: oito origens apoiadas em hipóteses, incluindo as duas bases próprias fixadas. A largura representa massa percentual reescalada, não acompanhamento de pessoas.",
    )
    h += '<div class="flow-readout" aria-live="polite">Toque em uma fita ou use Tab para ler sua origem, destino e natureza.</div>'
    old = json.loads((ASSETS / "datafolha_14092026_data.json").read_text())["transfer"]
    h += f"<p>As margens inteiras somam 101 no primeiro turno e 99 no segundo; reescalamos as origens por 99/101. Com as bases próprias fiéis por hipótese, o ganho fora delas é de <strong>{fmt(F['gains'][0])} pontos para Lula e {fmt(F['gains'][1])} para Flávio</strong>: razão {fmt(F['ratio_flavio_lula'])}:1, ante {fmt(old['ratio_flavio_lula'])}:1 na onda anterior. O ganho líquido é imposto pelas margens reescaladas; descrevê-lo como fluxo bruto exige a hipótese de fidelidade. O corte entre as demais candidaturas depende da prior e do IPF.</p>"
    h += "<details><summary>Hipóteses e fechamento do diagrama</summary><p>Base própria fiel, zeros estruturais de cruzamento nas duas bases; maior migração entre candidaturas próximas, pequena migração para o campo oposto e não escolha absorvendo parte das perdas. Cury e Caiado ficam fixos nos percentuais publicados. O ajuste proporcional iterativo fecha o resíduo nas duas margens. O JSON registra a matriz e as linhas de cada natureza; o script expõe a prior. Nada disso permite identificar o percurso de um entrevistado.</p></details>"
    h += table(
        [
            "Segundo turno na mesma amostra",
            "Lula",
            "Adversário",
            "Não escolha",
            "Fonte",
        ],
        [
            [a["name"], a["lula"], a["opponent"], a["nonchoice"], ref(a["page"])]
            for a in D["alternatives"]
        ],
    )
    h += "<p>O contraponto à força de Flávio está no cenário com Cury: ambos os nomes fazem 44% contra Lula em perguntas diferentes, e Lula cai de 46% para 44% diante de Cury. É comparação descritiva na mesma amostra; sem o cruzamento individual entre cenários, não identifica migração nem significância da diferença.</p></section>"
    h += section(
        "documentos",
        "06",
        "O que o documento mostra.<br>E o que ainda falta.",
        "Registro, questionário, perfil ponderado e anexo de campo são fontes distintas. Suas diferenças precisam ser explicitadas antes de virar uma conclusão.",
    )
    h += table(
        [
            "Dimensão do cruzamento de voto",
            "Base ponderada somada",
            "Fora do recorte / diferença",
        ],
        [
            [
                c["dimension"],
                c["base"],
                (
                    "Excesso de 1 por arredondamento"
                    if c["missing"] < 0
                    else c["missing"]
                ),
            ]
            for c in D["coverage"]
        ],
    )
    h += "<p>Renda deixa 88 casos fora das colunas, cor deixa 71, e religião, 441. Sexo, idade, região, natureza do município e ocupação fecham 2.001. Escolaridade e preferência partidária somam 2.002 por arredondamento das bases ponderadas. Não se deve somar indicadores nacionais a partir de partições incompletas.</p>"
    h += f'<p><strong>Conferência da extração:</strong> recompusemos Lula e Flávio por sexo e por região nos dois turnos. As oito diferenças em relação ao placar publicado ficam abaixo de um ponto, compatíveis com o uso de percentuais arredondados. <a href="assets/{SLUG}_data.json">Resultados da conferência</a>.</p>'
    h += f'<p><strong>Voto de 2022:</strong> o questionário coleta comparecimento e voto no segundo turno entre os elegíveis, mas o plano de ponderação consultado não o declara como variável de ajuste e o relatório recebido não traz esse cruzamento. Não podemos concluir que a pesquisa foi ponderada pelo voto de 2022. {ref(3, "_questionario")} <a href="fontes/{SLUG}_registro.txt">Plano registrado</a>.</p>'
    h += f"<p><strong>Território:</strong> o anexo soma 2.001 entrevistas e contém 302 setores distintos, associados a <strong>126 códigos municipais</strong>, contra 125 municípios informados no relatório. Seu rodapé indica 14–16/09, enquanto registro e relatório indicam 15–17/09. São discrepâncias documentais a reconciliar, não evidência de fraude. O registro previa 2.002 entrevistas, uma a mais que o realizado. {ref(2)} {ref(4, '_bairros')}</p>"
    h += "<p>O anexo permite distinguir campo de ponderação: na renda, são 986/658/276 e 81 sem resposta no campo; no cruzamento ponderado, 992/655/266 e 88 fora das colunas. Esses números não revelam o peso de cada pessoa nem separam o efeito conjunto de região, idade, sexo e escolaridade.</p>"
    h += '<p>A <a href="reponderacao_pnad.html#comparar-metodos">tabela comparativa dos institutos</a> foi atualizada para esta onda. Modalidade: presencial em pontos de fluxo; seleção em etapas com cotas finais. Sem taxas de resposta, pesos individuais ou efeito do desenho publicado, não há fundamento para dar à reconstrução sintética a precisão de uma amostra probabilística observada.</p></section>'
    h += section(
        "tabelas",
        "07",
        "As treze tabelas.<br>Todas as células acessíveis.",
        "Extração automática do texto nativo, com três blocos por tabela. Traços preservados no arquivo de origem; páginas vinculadas em cada bloco.",
    )
    labels = {
        "espontanea": "Voto espontâneo",
        "estimulada_b": "1º turno, situação B",
        "validos_b": "Votos válidos, situação B",
        "rejeicao": "Rejeição",
        "turno2_flavio": "2º turno, Flávio",
        "turno2_caiado": "2º turno, Caiado",
        "turno2_zema": "2º turno, Zema",
        "turno2_renan": "2º turno, Renan",
        "turno2_cury": "2º turno, Cury",
        "definicao": "Decisão do voto",
        "motivacao": "Motivação do voto",
        "avaliacao": "Avaliação do governo",
        "aprovacao": "Aprovação do presidente",
    }
    for key, t in T.items():
        h += f"<details><summary>{escape(labels[key])}</summary>"
        for block in t["blocks"].values():
            cols = block["columns"]
            h += f'<p class="table-source">{ref(block["pdf_page"])} · Base ponderada da pergunta</p>'
            h += table(
                ["Resposta", *cols],
                [
                    [escape(n), *[("–" if rr[c] is None else rr[c]) for c in cols]]
                    for n, rr in block["rows"].items()
                ]
                + [["Base ponderada", *[block["base"][c] for c in cols]]],
            )
        h += "</details>"
    h += f'<p><a href="assets/{SLUG}_cruzamentos.json">Baixar o anexo completo extraído em JSON</a></p></section>'
    h += section(
        "fontes",
        "08",
        "Da fonte à conta.",
        "Documentos originais, dados derivados e roteiro de reprodução.",
    )
    h += f'''<ol><li><a href="fontes/{SLUG}.pdf">Relatório nacional completo, 50 páginas</a> · <a href="{D["provenance"]["official_report_url"]}">original no Datafolha</a>. O PDF recebido em Downloads foi movido ao acervo e seu SHA256 confere com o download oficial.</li><li><a href="fontes/{SLUG}_estaduais.pdf">Relatório estadual completo, 132 páginas</a> · <a href="{D["provenance"]["official_states_url"]}">original no Datafolha</a>. Campo 8–10/09; metodologia p. 2; segundo turno SP p. 58, RJ p. 76, MG p. 94.</li><li><a href="fontes/{SLUG}_registro.txt">Registro BR-04029/2026</a> · <a href="fontes/{SLUG}_questionario.pdf">questionário</a> · <a href="fontes/{SLUG}_bairros.pdf">território e perfil de campo</a> · <a href="https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml">PesqEle</a>.</li><li><a href="https://dadosabertos.tse.jus.br/dataset/eleitorado-atual">Perfil oficial do eleitorado, TSE</a>. Cópia usada: geração 01/07/2026, excluído exterior. Totais estaduais e hash preservados no JSON analítico.</li><li><a href="assets/{SLUG}_data.json">Cálculos, conferências, fontes e hashes</a> · <a href="assets/{SLUG}_identificacao.json">certificados da projeção conjunta</a> · <a href="reponderacao_pnad.html#metodo">método e referências PNAD</a>.</li><li><a href="https://ec.europa.eu/eurostat/web/products-statistical-working-papers/-/ks-ra-13-020">Eurostat, Statistical matching: a model based approach for data integration</a>. Referência sobre suposições de identificação; não certificação desta auditoria.</li></ol>
<details><summary>Reproduzir no repositório</summary><pre>python3 scripts/datafolha-21092026-extract.py
python3 scripts/datafolha-21092026-audit.py
python3 scripts/datafolha-21092026-governadores.py
python3 scripts/datafolha-21092026-build.py
python3 scripts/reponderacao-pnad.py calcular --hoje 2026-09-21
python3 scripts/reponderacao-build.py
python3 scripts/social-cards.py --only datafolha_21092026</pre><p class="hash">SHA256 nacional: {D["provenance"]["relatorio.pdf"]["sha256"]}</p></details></section></main><footer class="wrap">Arvor · 21 de setembro de 2026 · Sensibilidade e auditoria documental. <a href="index.html">Biblioteca</a> · <a href="reponderacao_pnad.html">Comparar pesquisas</a></footer>
<script type="application/json" id="southeast-data">{json.dumps({"weight": G["weights"]["ES"], "known": G["known_contribution"]})}</script></body></html>'''
    assert "—" not in h
    (ROOT / "docs" / f"{SLUG}.html").write_text(
        h.replace("<section ", "\n<section ") + "\n"
    )
    print(SLUG, len(h), "characters")


if __name__ == "__main__":
    main()
