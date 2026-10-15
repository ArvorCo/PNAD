"""Dossiê preliminar: evidência separada de aritmética e hipótese de campo."""

from html import escape as esc

from dossies_2t_2026.view import (
    callout,
    details,
    fmt,
    note,
    section,
    signed,
    stacks,
    table,
)
from ga_tag import injetar

from .audit import SLUG
from .income_view import render as income_section
from .panel_view import panel_section


def link(url, label):
    return f'<a href="{esc(url, quote=True)}">{esc(label)}</a>'


def income_history(h):
    rows = [
        [
            r["faixa"],
            fmt(r["peso_pct"], 0) + "%",
            f'{r["julho"]["flavio"]} × {r["julho"]["lula"]}',
            f'{r["setembro"]["flavio"]} × {r["setembro"]["lula"]}',
            signed(r["mudanca_gap_na_faixa_pp"], 0),
            signed(r["contribuicao_gap_pp"], 2),
        ]
        for r in h["faixas"]
    ]
    pages = "".join(
        '<figure><a href="' + esc(p["arquivo"].removeprefix("docs/"), quote=True) + '">'
        '<img loading="lazy" src="'
        + esc(p["arquivo"].removeprefix("docs/"), quote=True)
        + '" '
        'alt="' + esc(p["rotulo"], quote=True) + '" width="1200" height="675"></a>'
        "<figcaption>"
        + esc(p["rotulo"])
        + f' · página física {p["pagina_fisica"]}.</figcaption></figure>'
        for p in h["fontes"]["paginas"]
    )
    return (
        '<div id="evolucao-renda"><h3>Antes da urna, o avanço se concentrou acima de 2 SM</h3>'
        "<p>Entre as divulgações de 15/07 e 28/09, a diferença publicada F−L passou de −8 para zero. "
        "O perfil de renda publicado era o mesmo nas duas pontas: 31% / 42% / 27%. "
        "Fixando essa margem, a mudança aparece nas preferências dentro das faixas.</p>"
        + table(
            [
                "Faixa",
                "Peso publicado",
                "Julho · F × L",
                "28/09 · F × L",
                "Mudança F−L na faixa",
                "Contribuição / total (pp)",
            ],
            rows,
        )
        + f'<p>A recomposição atribui <b>{signed(h["faixas"][1]["contribuicao_gap_pp"],2)} pp</b> à faixa de dois a cinco salários e <b>{signed(h["faixas"][2]["contribuicao_gap_pp"],2)} pp</b> à faixa acima de cinco. Até dois salários, a contribuição é {signed(h["faixas"][0]["contribuicao_gap_pp"],2)} pp. A soma é {signed(h["mudanca_gap_recomposto_pp"],2)} pp; a mudança da diferença publicada é {signed(h["mudanca_gap_publicado_pp"],0)} pp. Sobram {signed(h["mudanca_residuo_pp"],2)} pp na diferença dos resíduos de recomposição.</p>'
        + note(
            "Conta por faixa: peso × [(F−L) em setembro − (F−L) em julho]. Os cruzamentos e os totais são arredondados; os resíduos são mantidos, sem forçar fechamento. São pontos estimados em amostras diferentes, sem teste de significância das mudanças por segmento. Não identificam migração individual, renda como causa ou efeito de campanha."
        )
        + "<p><b>O contraponto à hipótese do feriadão:</b> parte importante da aproximação já aparecia antes de outubro, nas faixas média e alta. A nova coleta não pode ser responsabilizada por esse movimento anterior. Esta decomposição para em 28/09: não usa o perfil assumido de 03/10 e não imputa nenhum cruzamento de 14/10.</p>"
        + details(
            "Conferir as quatro páginas originais",
            '<div class="q-evidence">'
            + pages
            + "</div>"
            + "<p>Julho: votos na coluna Jul do relatório de 14/08, p. 36, e perfil do relatório de julho, p. 114. Setembro: votos na coluna 28 Set, p. 37, e perfil na p. 204 do relatório de 28/09. Páginas integrais renderizadas dos PDFs intactos; hashes no JSON da auditoria.</p>",
        )
        + "</div>"
    )


def render(d):
    p = d["pesquisa"]
    sample_size = f'{p["n"]:,}'.replace(",", ".")
    a = d["aas"]
    delta = d["decomposicao"]
    reg = link("fontes/quaest_14102026_registro.txt", "conferência do registro TSE")
    source = link(p["fonte"]["url"], "G1: painel Quaest, 14/10")
    asset = f"assets/{SLUG}_data.json"
    prev = d["serie"][-2]
    now = d["serie"][-1]
    projected = delta["proporcao_anterior_aplicada_a_massa_atual"]
    blocks = []
    blocks.append(
        section(
            1,
            "mudanca",
            "Dois pontos para cada lado.<br><em>O mesmo intervalo entre eles.</em>",
            "A primeira onda depois da urna não inaugura a vantagem numérica de Flávio no segundo turno.",
            stacks(
                "O mesmo duelo, antes e depois da eleição",
                {
                    "03/10 · antes da urna": [
                        prev["publicado"][k]
                        for k in ("flavio", "lula", "branco_nulo", "indecisos")
                    ],
                    "14/10 · depois da urna": [
                        now["publicado"][k]
                        for k in ("flavio", "lula", "branco_nulo", "indecisos")
                    ],
                },
                ["Flávio", "Lula", "Branco/nulo/não vai votar", "Indecisos"],
            )
            + table(
                ["Resposta", "03/10", "14/10", "Variação"],
                [
                    [
                        name,
                        f'{prev["publicado"][key]}%',
                        f'{now["publicado"][key]}%',
                        f'{delta["variacoes_total_pp"][key]:+d} pp',
                    ]
                    for key, name in [
                        ("flavio", "Flávio"),
                        ("lula", "Lula"),
                        ("branco_nulo", "Branco/nulo/não vai votar"),
                        ("indecisos", "Indecisos"),
                    ]
                ],
            )
            + callout(
                "A conta que muda a leitura",
                f'Se mantivermos a proporção anterior entre os dois e elevarmos a soma das candidaturas de 86% para 90%, obtemos <b>Flávio {fmt(projected["flavio"],2)}% e Lula {fmt(projected["lula"],2)}%</b>. Arredondando, é o novo 46 × 44. O movimento é compatível com redução proporcional da não escolha, sem deslocamento perceptível da preferência entre os finalistas.',
            )
            + "<p>Isso descreve os totais; não acompanha pessoas. São amostras diferentes. Não sabemos quais entrevistados saíram do branco/nulo, mudaram de candidato ou passaram a responder. O grupo agregado também mistura branco, nulo e quem diz que não vai votar: não pode ser convertido inteiro em abstenção.</p>"
            + note(
                f'Fonte: {source}; onda de 03/10 no acervo conferido. <a href="reponderacao_pnad_1o_turno_2026.html">Arquivo do 1º turno</a>. Os pontos são publicados; a redistribuição proporcional é conta nossa, não fluxo observado.'
            ),
        )
    )
    rows = []
    for w in d["serie"]:
        v = w["publicado"]
        rows.append(
            [
                f'{w["divulgacao"][8:10]}/{w["divulgacao"][5:7]}',
                f'{w["campo"]["inicio"][8:10]}/{w["campo"]["inicio"][5:7]} a {w["campo"]["fim"][8:10]}/{w["campo"]["fim"][5:7]}',
                str(v["flavio"]),
                str(v["lula"]),
                f'{w["gap_total_pp"]:+d}',
                fmt(w["flavio_binario_pct"], 2),
            ]
        )
    blocks.append(
        section(
            2,
            "serie",
            "A mudança de sinal<br><em>aconteceu antes de outubro.</em>",
            "Duelo Lula × Flávio em todas as ondas do acervo, sempre com o mesmo denominador.",
            table(
                [
                    "Divulgação",
                    "Campo",
                    "Flávio / total",
                    "Lula / total",
                    "F−L / total",
                    "Flávio / F+L",
                ],
                rows,
            )
            + "<p>Em julho, a Quaest media Lula 45% e Flávio 37%. Em 14/09 já divulgava Flávio 42% e Lula 40% no cenário de segundo turno; em 03/10, 44% a 42%. A série oscilou, inclusive com empate em 28/09. <b>Não há uma primeira passagem para Flávio à frente depois da eleição.</b> A impressão de virada nasce, em parte, de comparar o primeiro turno de 03/10 (Lula 40 × Flávio 38) com o segundo turno de 14/10 (Flávio 46 × Lula 44). São perguntas diferentes.</p>"
            + f'<p>Na mesma pergunta de segundo turno, a diferença entre os dois, normalizada por F+L, passa de <b>{fmt(prev["gap_binario_pp"],2)} para {fmt(now["gap_binario_pp"],2)} pp</b>. A variação é de {fmt(delta["mudanca_gap_binario_pp"],2)} pp. São renormalizações nossas, não números de eleitor provável divulgados pela Quaest.</p>'
            + income_history(d["evolucao_renda_historica"])
            + details(
                "A comparação possível com a urna de 04/10",
                f'<p>Sem exterior, Flávio teve {fmt(d["urna_1t"]["validos"]["flavio"],4)}% e Lula {fmt(d["urna_1t"]["validos"]["lula"],4)}% dos válidos do primeiro turno. Retendo só os votos dos dois, a fração de Flávio é {fmt(d["urna_1t"]["flavio_entre_finalistas_pct"],2)}%, próxima aos {fmt(now["flavio_binario_pct"],2)}% atuais. Essa proximidade não determina transferências, presença nem resultado de segundo turno. A terceira via fica fora dessa conta; os ausentes não são observados.</p><p><a href="assets/reponderacao_urna_1t.json">Apuração oficial arquivada e proveniência</a>. O universo sem exterior é o comparável ao levantamento domiciliar no Brasil.</p>',
            )
            + note(
                'Cada onda aponta para a ficha e as fontes originais no <a href="'
                + asset
                + '">JSON da auditoria</a>. A defesa do instituto também está registrada: no <a href="https://quaest.com.br/pesquisas-quaest-e-o-resultado-das-urnas-2026/">balanço de 06/10</a>, Felipe Nunes atribui o movimento final ao voto útil. É a interpretação do instituto, não identificação causal nossa.'
            ),
        )
    )
    blocks.append(
        section(
            3,
            "campo",
            "Três dias de feriadão.<br><em>Mais a terça-feira.</em>",
            "A coleta domiciliar ocorreu de 10 a 13 de outubro. A publicação foi em 14/10.",
            '<div class="q-calendar">'
            + "".join(
                f'<div><b>{x["data"][8:10]}/10</b><span>{esc(x["tipo"])}</span><small>Entrevistas no dia: não obtidas</small></div>'
                for x in d["campo"]
            )
            + "</div>"
            + f'<p>O {reg} fixa o campo. O <a href="https://crt01.gov.br/comunicado-crt-01-feriado-de-12-de-outubro/">calendário oficial de 12/10</a> confirma a segunda-feira como feriado nacional. Três dos quatro dias de calendário são sábado, domingo e feriado; <b>isso não significa que 75% das entrevistas ocorreram nesses dias</b>. O volume diário não foi obtido.</p>'
            + '<div class="method-grid"><div><h3>O mecanismo que merece teste</h3><p>Viagens, trabalho e disponibilidade em casa podem alterar quem é encontrado. Mesmo dentro da mesma cota de renda, pessoas disponíveis e indisponíveis podem ter preferências distintas. Cumprir a cota não resolve automaticamente essa seleção.</p></div><div><h3>O contraponto necessário</h3><p>Fim de semana também pode facilitar o contato com quem trabalha fora nos dias úteis. Terça-feira, revisitas e calibração podem reduzir diferenças. Sem paradata, não sabemos a direção nem a magnitude líquida. A data não prova favorecimento de qualquer candidato.</p></div></div>'
            + callout(
                "A pergunta nova: quem faltou dentro da cota?",
                "A auditoria decisiva cruza dia e horário com renda, região, voto lembrado e voto atual; depois compara contatos, ausências, recusas e revisitas. Se o perfil político variar dentro da cota com a disponibilidade, ponderar só as margens demográficas poderá deixar resíduo. É uma hipótese de seleção verificável, ainda sem resultado.",
            )
            + note(
                "O registro prevê horários e georreferenciamento na coleta e checagem de áudio de 30% dos questionários. A primeira página do questionário tem campos de início e fim; isso mostra que a auditoria é possível, não que seus dados já estejam públicos. Não se recomenda identificar ou divulgar entrevistados."
            ),
        )
    )
    blocks.append(income_section(d))
    lo, hi = a["intervalo_gap_95_pp"]
    blocks.append(
        section(
            5,
            "incerteza",
            "Vantagem numérica.<br><em>Liderança não identificada.</em>",
            "Uma diferença de dois pontos precisa da incerteza da diferença entre os candidatos.",
            f'<p>Como referência sob amostragem aleatória simples, n = {sample_size} e os totais de 46% e 44% dão margem de <b>{fmt(a["margem_gap_95_pp"],2)} pp para F−L</b>, com intervalo aproximado de 95% de {fmt(lo,2)} a +{fmt(hi,2)} pp. Ele contém zero. Essa referência não incorpora o desenho por conglomerados, as cotas, os pesos ou o erro de seleção.</p>'
            + f'<p>A diferença publicada mudou {fmt(a["mudanca_gap_total_pp"],0)} pp desde 03/10. Sob duas amostras AAS independentes, a margem da mudança seria {fmt(a["margem_mudanca_independente_aas_95_pp"],2)} pp. Não identifica estabilidade perfeita, tampouco uma nova abertura da distância. Os percentuais também são arredondados.</p>'
            + callout(
                "Uma frase fiel à evidência",
                "“Quaest: Flávio tem 46% e Lula 44%; a diferença não separa os dois com 95% de confiança na referência amostral simples. Ambos cresceram dois pontos e a não escolha caiu quatro desde 03/10.”",
            )
            + note(
                "Fórmula AAS: Var(pF−pL) = [pF+pL−(pF−pL)²]/n. Não somamos mecanicamente duas margens individuais. Sem o desenho e os pesos, não calculamos um IC próprio validado da Quaest. A sensibilidade por renda reduz a diferença numérica, mas não transforma vantagem em liderança estatisticamente identificada."
            ),
        )
    )
    blocks.append(panel_section(d))
    blocks.append(
        section(
            7,
            "fontes",
            "O que está conferido.<br><em>O que continua aberto.</em>",
            "Atualizado em 15/10/2026 com o HTML salvo e cinco perguntas da API do painel. A íntegra e os pesos finais poderão mudar o diagnóstico.",
            "<ul>"
            + "".join(f"<li>{esc(x)}</li>" for x in d["pendencias"])
            + "</ul>"
            + table(
                ["Documento", "Conferência"],
                [
                    [
                        source,
                        "Voto por renda, controles por sexo, idade e escolaridade; arquivo salvo pelo usuário e preservado com SHA-256.",
                    ],
                    [
                        link(p["fonte"]["complementos"][0]["url"], "SBT News, 14/10"),
                        "Conferência independente de 46/44/9/1, n, campo e registro.",
                    ],
                    [
                        reg,
                        "Campos relevantes transcritos; não é HTML original. Mensagem do TSE: relatório não fornecido.",
                    ],
                    [
                        "Questionário TSE, QUEST_NACIONAL_2T_R01_V14",
                        "27 páginas vistas no visualizador; salvamento não concluído. Só a primeira página foi lida; sem auditoria integral.",
                    ],
                    [
                        link(
                            p["fonte"]["complementos"][1]["url"], "G1: painel indicado"
                        ),
                        "HTML salvo: total e 25 recortes completos extraídos dos rótulos SVG. Extração local preservada, inclusive o recorte sem rótulos.",
                    ],
                    [
                        link(
                            d["painel_g1"]["resumo"],
                            "G1: cinco perguntas e fontes da API",
                        ),
                        "Cinco perguntas com 26 recortes cada, extraídas da API pública consumida pelo painel. Todos os 100 valores presentes nos recortes do HTML coincidem. Bases ausentes não foram imputadas.",
                    ],
                    [
                        "Anexo territorial TSE",
                        "Em 15/10, cerca de 01h12 BRT, o TSE informou: Pesquisa não possui arquivo de bairros/municípios. Prazo exibido: 15/10, ainda não encerrado. Não permite inferir irregularidade.",
                    ],
                    [
                        link(asset, "Dados e contas da auditoria"),
                        "Série, denominadores, AAS, recomposição e sensibilidade provisória por renda.",
                    ],
                ],
            )
            + note(
                'Cópias de trabalho ficam no acervo do projeto. <a href="assets/'
                + SLUG
                + '_sources.json">Manifesto de hashes</a>. O catálogo público de mídia da Quaest consultado nesta rodada tinha relatório do DF em 13/10 como arquivo mais recente; a ausência nesse recorte não prova inexistência em toda a internet.'
            )
            + "<p><b>Juízo editorial:</b> a novidade sólida desta publicação é a redução da não escolha com quase a mesma divisão entre finalistas. A fragilidade investigável é a disponibilidade dentro das cotas durante o feriadão. A primeira é mensurável agora; a segunda precisa de evidência antes de virar acusação ou ajuste de votos.</p>",
        )
    )
    title = "Quaest 14/10: a distância permanece | Arvor"
    summary = "Flávio 46%, Lula 44%: série, renda e cinco perguntas do G1 com 130 recortes. Sensibilidade PNAD com cotas atuais; bases e pesos finais pendentes."
    nav = "".join(
        f'<a href="#{x}">{label}</a>'
        for x, label in [
            ("mudanca", "O que mudou"),
            ("serie", "Evolução"),
            ("campo", "Feriadão"),
            ("renda", "Renda"),
            ("incerteza", "Incerteza"),
            ("painel", "Painel G1"),
            ("fontes", "Fontes"),
        ]
    )
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<meta name="description" content="{summary}"><link rel="canonical" href="https://brasil.arvor.co/{SLUG}.html">
<meta property="og:title" content="{title}"><meta property="og:description" content="{summary}"><meta property="og:type" content="article"><meta property="og:url" content="https://brasil.arvor.co/{SLUG}.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/{SLUG}.png">
<link rel="stylesheet" href="assets/dossies_2t_2026.css"><link rel="stylesheet" href="assets/{SLUG}.css"></head>
<body><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html">ARVOR / Intelligence</a><span>Auditoria de pesquisa · 2º turno</span></header>
<main id="conteudo"><section class="hero"><div><p class="eyebrow">Quaest · 14 outubro 2026 · Dossiê preliminar</p><h1>Duas escolhas crescem.<br><em>A distância permanece.</em></h1><p class="deck">O novo placar não traz uma virada depois da urna. Flávio e Lula ganham dois pontos cada; a não escolha perde quatro. Por renda, Flávio avança até 2 SM e Lula acima desse corte. O feriadão abre uma pergunta sobre disponibilidade, ainda sem evidência de efeito.</p><div class="hero-meta"><span>Campo: 10–13/10</span><span>{sample_size} entrevistas</span><span>BR-08729/2026</span><span>Conferido em 15/10</span></div></div><aside class="hero-result"><p class="eyebrow">Publicado / total de entrevistados</p><div class="score">46 <span>×</span> 44</div><p>Flávio Bolsonaro × Lula</p><p>Branco/nulo/não vai votar: 9%<br>Indecisos: 1%</p><p class="q-status">Íntegra pendente no TSE<br>Sensibilidade PNAD com cotas atuais</p></aside></section><nav class="chapter-nav" aria-label="Capítulos">{nav}</nav>{''.join(blocks)}</main><footer><a href="index.html">Arvor / Biblioteca</a><p>Publicados, contas derivadas e hipóteses identificados. A análise não mede probabilidade de vitória.</p><a href="reponderacao_pnad.html">Centrais e simulador</a></footer></body></html>"""
    return injetar(html.replace("<section ", "\n<section ")) + "\n"
