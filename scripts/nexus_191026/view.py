"""Dossiê editorial da Nexus de 19/10, nomeado pelo fim do campo."""

import json
from html import escape as esc

from dossies_2t_2026 import view as v
from ga_tag import injetar

from . import context
from .extract import SLUG

PDF = f"fontes/{SLUG}.pdf"


def ref(*pages):
    return (
        '<p class="refs">Fonte: '
        + " · ".join(f'<a href="{PDF}#page={p}">p. {p}</a>' for p in pages)
        + "</p>"
    )


def explorer(data):
    options = '<option value="voto">Intenção de voto</option>' + "".join(
        f'<option value="{k}">{esc(t["title"])}</option>'
        for k, t in data["tables"].items()
        if k != "voto"
    )
    payload = json.dumps(
        {"house": "nexus", "tables": data["tables"], "pdf": PDF, "profile_page": 125},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return (
        '<div class="explorer" id="explorador"><div class="explorer-head"><h3>11 perguntas, oito dimensões</h3>'
        "<p>Voto, polarização, presença, aprovação e escala de trabalho. Cada percentual tem seu próprio universo.</p></div>"
        '<div class="explorer-controls" hidden><label>Pergunta<select id="d-question">'
        + options
        + '</select></label><label>Recorte<select id="d-dimension"></select></label></div>'
        '<div id="d-explorer-chart" aria-live="polite">'
        + chart(data, "voto", ["total", "homens", "mulheres"])
        + '</div><script type="application/json" id="d-explorer-data">'
        + payload
        + "</script></div>"
    )


def chart(data, key, names):
    t = data["tables"][key]
    return v.stacks(
        t["title"],
        {n: list(t["segments"][n]["responses"].values()) for n in names},
        list(t["segments"]["total"]["responses"]),
    ) + ref(*t["pages"])


def render(data):
    chapters = []
    chapters.append(
        v.section(
            1,
            "renda",
            "A renda mudou. A régua precisa acompanhar.",
            "O perfil desta rodada é 21/16/40/23. Reutilizar o perfil anterior alteraria a conta.",
            v.income_section(data, "nexus")
            + ref(43, 125)
            + v.callout(
                "Uma sensibilidade condicional",
                "A ficha não identifica se o perfil da p. 125 é anterior ou posterior à ponderação. A conta adota o perfil publicado e aplica a mudança de composição ao placar divulgado, preservando o resíduo de recomposição. Não há massa de renda ausente quantificada para ajustar separadamente.",
            ),
        )
    )
    chapters.append(
        v.section(
            2,
            "transferencias",
            "Bases retidas. Terceira via dividida.",
            "Entre quem lembra ter votado em cada finalista, a retenção supera 97%.",
            v.stacks(
                "Voto lembrado no primeiro turno e intenção atual",
                data["transfer"],
                ["Flávio", "Lula", "Branco/nulo/nenhum", "NS/NR"],
            )
            + ref(27)
            + "<p>Entre os eleitores declarados de outras candidaturas, 50,5% apontam Flávio e 32,4% Lula; 15,0% preferem branco/nulo e 2,0% não respondem. Entre quem diz ter faltado ao primeiro turno, o placar é 44,1% a 49,3%. As bases desses grupos não estão publicadas.</p>"
            + v.note(
                "São respostas retrospectivas na mesma entrevista, sem acompanhamento individual entre urnas. Esses percentuais não identificam quantos ausentes comparecerão agora, nem autorizam multiplicar uma taxa observada de comparecimento por candidato."
            )
            + v.stats(
                [
                    ("90,9%", "dizem não pretender mudar o voto"),
                    ("8,4%", "admitem mudar"),
                    ("0,7%", "não sabem ou não respondem"),
                ]
            )
            + ref(35)
            + "<p>A segunda opção da p. 40 se refere apenas aos 8,4% que admitem mudar. A simulação da p. 41 explora perdas e entradas hipotéticas em cenários separados; não fornece limites estatísticos nem probabilidades de vitória.</p>"
            + ref(40, 41)
            + context.motivation(data, ref),
        )
    )
    chapters.append(
        v.section(
            3,
            "presenca",
            "92,9% declaram presença certa ou provável.",
            "A resposta de intenção não substitui o comparecimento observado pelo TSE.",
            chart(data, "presenca", ["total", "até 1 SM", ">5 SM"])
            + "<p>85,9% já decidiram comparecer e 7,0% provavelmente irão votar. Outros 5,5% dizem que provavelmente não irão ou já decidiram não ir; 1,6% não respondem. O total declarado não é uma previsão calibrada.</p>"
            + v.note(
                "Esta rodada entra nas centrais pelo voto e pela renda. Ela não troca automaticamente a âncora de comparecimento, as propensões históricas ou o ajuste relativo já declarado no simulador."
            ),
        )
    )
    chapters.append(
        v.section(
            4,
            "escala",
            "A proposta de jornada tem apoio de 66,2%.",
            "A pergunta especifica cinco dias de trabalho, dois de descanso e nenhuma redução salarial.",
            chart(data, "escala", ["total", "até 1 SM", "1–2 SM", "2–5 SM", ">5 SM"])
            + "<p>26,4% desaprovam e 7,4% não respondem. A formulação faz parte do resultado: apoio a essa proposta não equivale a apoio a qualquer desenho de alteração da jornada.</p>"
            + "<p>Na hipótese de um candidato se posicionar contra o fim da escala, 17,7% dos que aprovam a mudança dizem que certamente deixariam de votar nele e 14,8% talvez deixassem. Entre os que desaprovam a mudança, a hipótese de um candidato apoiá-la produz respostas de 2,8% e 4,5%. São bases e posições diferentes.</p>"
            + ref(74, 80)
            + v.note(
                "Reação declarada a um cenário hipotético não é efeito causal medido sobre intenção de voto. Não subtraímos essas parcelas das candidaturas."
            ),
        )
    )
    chapters.append(context.section(data, ref))
    chapters.append(
        v.section(
            6,
            "segmentos",
            "O placar muda conforme o recorte.",
            "29 linhas por pergunta, incluindo o total. Sem bases dos grupos ou margem específica estimada.",
            explorer(data)
            + v.note(
                "Escolaridade, renda, região e religião se sobrepõem. Diferenças descritivas entre grupos não isolam causas; a margem de erro de ±2 pp divulgada para o total não se transfere a cada segmento."
            ),
        )
    )
    raw = []
    for t in data["tables"].values():
        options = list(t["segments"]["total"]["responses"])
        raw.append(
            v.details(
                t["title"],
                v.table(
                    ["Grupo", *options, "Página"],
                    [
                        [
                            esc(n),
                            *[
                                v.fmt(value) + "%"
                                for value in row["responses"].values()
                            ],
                            str(row["page"]),
                        ]
                        for n, row in t["segments"].items()
                    ],
                )
                + v.note(t["universe"])
                + ref(*t["pages"]),
            )
        )
    chapters.append(
        v.section(
            7,
            "perguntas",
            "Os números completos do explorador.",
            "Tabelas legíveis também sem JavaScript; cada célula preserva a precisão publicada.",
            "".join(raw),
        )
    )
    chapters.append(
        v.section(
            8,
            "metodo",
            "Nova precisão, mesma obrigação de transparência.",
            "18ª rodada: 2.002 entrevistas CATI, campo de 16 a 18 de outubro, divulgação em 19 de outubro.",
            "<p>Registro informado: <b>BR-04499/2026</b>. A ficha declara cotas de sexo, idade, escolaridade, tipo de telefonia e DDD, cobertura das 27 UFs, referência PNADC anual 2025, primeira visita, e TSE de junho de 2026. Informa margem de ±2 pontos percentuais e confiança de 95% para a amostra total.</p>"
            + "<p>A Nexus passa a mostrar uma casa decimal e reapresenta a série histórica nessa precisão. Isso não amplia por si só a precisão amostral. Preservamos a versão anterior do dossiê e suas fontes, sem trocar silenciosamente os valores publicados em 13/10 pelos valores retrospectivos desta edição.</p>"
            + "<p>A ficha desta íntegra não declara calibração pelo resultado do primeiro turno. Isso não demonstra ausência de ajustes internos. O código do registro foi lido no relatório; não atribuímos a esta rodada a transcrição do PesqEle da rodada anterior.</p>"
            + ref(4)
            + v.note(
                "O endereço desta página usa 18/10, data final do campo. A data de divulgação e a identificação da onda nos dados são mantidas separadas."
            ),
        )
    )
    catalogue = [
        ("Método e desenho", "Cotas, referências e arredondamento", 4),
        ("Política e eleições", "Interesse, polarização e presença declarada", 6),
        ("Voto no segundo turno", "Espontânea, estimulada, válidos e séries", 20),
        (
            "Voto lembrado e transferências",
            "2022, primeiro turno, perfis e Bolsa Família",
            26,
        ),
        (
            "Firmeza e decisão",
            "Possibilidade de mudança, segunda opção e momento da escolha",
            35,
        ),
        ("Expectativa e motivação", "Quem vencerá, razões da escolha e campanha", 50),
        (
            "Participação política",
            "Somente quem declarou uma candidatura, 92,4% da amostra",
            65,
        ),
        ("Escala 6x1", "Aprovação e reações hipotéticas por posição", 74),
        (
            "Potencial e rejeição",
            "Escalas de disponibilidade e combinação das candidaturas",
            87,
        ),
        ("Governo", "Avaliação, aprovação e segmentos", 98),
        ("Problemas do Brasil", "Duas menções, séries e voto atual", 114),
        (
            "Economia",
            "Situação atual, comparação com governo anterior e próximos seis meses",
            118,
        ),
        ("Perfil e precisão", "Composição, margens informadas e limites de uso", 125),
    ]
    chapters.append(
        v.section(
            9,
            "integra",
            "As 128 páginas, organizadas por tema.",
            "O explorador cobre onze perguntas. Os demais capítulos estão na íntegra, com acesso direto abaixo.",
            v.table(
                ["Tema", "Conteúdo", "Abrir PDF"],
                [
                    [esc(a), esc(b), f'<a href="{PDF}#page={p}">p. {p}</a>']
                    for a, b, p in catalogue
                ],
            )
            + v.note(
                "Expectativa de vitória, rejeição e intenção de voto são perguntas diferentes. Problemas admitem duas menções e não somam 100%; economia atual, comparação retrospectiva e futuro usam horizontes diferentes."
            ),
        )
    )
    controls = [
        [k, dim, v.fmt(row["residuo_max_pp"], 3) + " pp"]
        for k, dims in data["controls"].items()
        for dim, row in dims.items()
    ]
    chapters.append(
        v.section(
            10,
            "fontes",
            "Fonte preservada. Contas reproduzíveis.",
            "Download oficial conferido em 19/10/2026; nenhuma pesquisa antiga foi substituída.",
            '<div class="downloads">'
            + f'<a href="{PDF}">Baixar íntegra · 128 páginas</a><a href="{esc(data["source"]["url"])}">PDF no site da Nexus</a>'
            + f'<a href="assets/{SLUG}_data.json">Dados e controles JSON</a><a href="reponderacao_pnad.html">Centrais Arvor atualizadas</a><a href="nexus_btg_13102026.html">Rodada anterior</a></div>'
            + v.details(
                "Recomposição das onze perguntas pelas oito dimensões",
                v.table(["Pergunta", "Dimensão", "Maior resíduo absoluto"], controls),
            )
            + v.note(
                "Os perfis arredondados são normalizados pela própria soma. Todos os resíduos ficaram abaixo de 0,47 pp. Recomposição é controle aritmético da transcrição; não valida recrutamento, precisão ou representatividade."
            )
            + v.note("SHA-256: <code>" + data["source"]["sha256"] + "</code>")
            + '<p>Também incorporada à reponderação: <a href="fontes/poderdata_19102026.pdf">PoderData de 19/10, íntegra de 33 páginas</a>, campo 16–18/10, 3.000 entrevistas, BR-02586/2026. Publicado 49/46/4/2, que soma 101 por arredondamento. A ficha declara ponderação pelo resultado do primeiro turno. Renda 46/33/21, cruzamento atual na p. 9, perfil com etapa de ponderação não identificada. Válidos publicados 52/48 preservados separadamente.</p>',
        )
    )
    summary = "BTG/Nexus de 19/10: 46,5% a 45,9% no total. Renda atual, retenção das bases, presença declarada e escala 6x1, com 11 perguntas por segmento e íntegra de 128 páginas."
    url = f"https://brasil.arvor.co/{SLUG}.html"
    nav = "".join(
        f'<a href="#{anchor}">{title}</a>'
        for anchor, title in [
            ("renda", "Renda"),
            ("transferencias", "Transferências"),
            ("presenca", "Presença"),
            ("escala", "Escala 6x1"),
            ("agenda", "Agenda"),
            ("segmentos", "Segmentos"),
            ("metodo", "Método"),
            ("integra", "Íntegra"),
            ("fontes", "Fontes"),
        ]
    )
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BTG/Nexus · 19/10/2026 · Bases firmes, placar apertado | Arvor</title>
<meta name="description" content="{esc(summary)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="BTG/Nexus: bases firmes, placar apertado"><meta property="og:description" content="{esc(summary)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="https://brasil.arvor.co/img/og/{SLUG}.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/{SLUG}.png">
<link rel="stylesheet" href="assets/dossies_2t_2026.css"><script src="assets/dossies_2t_2026.js" defer></script></head>
<body class="nexus nexus-decimal"><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html"><img src="img/arvor_logo.png" alt="Arvor Intelligence">Arvor / Brasil</a><span>Dossiê de pesquisa · 2º turno</span><a href="nexus_btg_13102026.html">Rodada de 13/10 ↗</a></header>
<main id="conteudo"><section class="hero"><div class="hero-copy"><p class="eyebrow">BTG/Nexus · divulgada em 19/10/2026 · campo 16–18/10</p><h1>Bases firmes.<br><em>Placar apertado.</em></h1><p class="deck">{summary}</p><div class="hero-meta"><span>2.002 entrevistas</span><span>CATI / telefone</span><span>±2 pp informados / total</span></div></div><aside class="hero-result"><p>Publicado / Flávio × Lula</p><b>46,5 × 45,9</b><span>sobre o total de entrevistados</span><div><strong>50,3% × 49,7%</strong><span>votos válidos publicados</span></div><p class="hero-foot">Branco/nulo: 4,7% · Indecisos: 2,9%<br>Diferença F−L: +0,6 pp no total</p></aside></section>
<nav class="chapter-nav" aria-label="Capítulos">{nav}</nav>{''.join(chapters)}</main>
<footer><a href="index.html">Arvor / Biblioteca</a><p>Percentuais publicados e contas derivadas separados. Sensibilidade não é previsão nem probabilidade de vitória.</p><a href="reponderacao_pnad.html">Duas centrais Arvor</a></footer></body></html>"""
    return injetar(html.replace("<section ", "\n<section ")) + "\n"
