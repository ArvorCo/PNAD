"""Capítulos da íntegra: transferências, presença e leitura temática completa."""

from html import escape as esc

from dossies_2t_2026.view import callout, details, fmt, note, section, table

from ..charts import frame, pairs
from .references import aggregation, turnout_reference

COLORS = ["#386ba6", "#a74247", "#b09a5b", "#818b78", "#9a9c96", "#53695f"]


def ref(*pages):
    return (
        '<span class="refs">Fonte: relatório Quaest · '
        + " · ".join(
            f'<a href="fontes/quaest_14102026.pdf#page={p}">p. {p}</a>' for p in pages
        )
        + "</span>"
    )


def distribution(title, options, rows, pages):
    body = ""
    for name, values in rows.items():
        total = sum(v for v in values if v is not None) or 100
        body += (
            '<div class="q-explorer-row"><b>'
            + esc(name)
            + '</b><div class="q-response-strip" aria-hidden="true">'
        )
        body += "".join(
            f'<i style="width:{100*(v or 0)/total}%;background:{COLORS[i%len(COLORS)]}"></i>'
            for i, v in enumerate(values)
        )
        body += '</div><div class="q-response-values">'
        body += "".join(
            f'<span><i style="background:{COLORS[i%len(COLORS)]}"></i>{esc(option)}: <strong>{fmt(value,0)}%</strong></span>'
            for i, (option, value) in enumerate(zip(options, values, strict=True))
            if value is not None
        )
        body += "</div></div>"
    return frame(
        title,
        body,
        "Percentuais publicados dentro de cada grupo. Barras acomodam somas arredondadas; números preservados.",
    ) + ref(*pages)


def transfers(data):
    topic = next(t for t in data["temas"] if t["id"] == "transferencia")
    tr = data["transferencia"]
    u = data["urna"]["pct_eleitorado"]
    table_rows = [
        [
            r["conversao_relativa_pct"],
            fmt(r["flavio_total"], 2),
            fmt(r["lula_total"], 2),
            f'{fmt(r["flavio_validos"],2)} × {fmt(r["lula_validos"],2)}',
        ]
        for r in tr["cenario_conversao"]
    ]
    return section(
        1,
        "transferencia",
        "Quem não escolheu um candidato.<br><em>Um grupo que mistura três coisas.</em>",
        "A íntegra permite ler a transferência. Não permite separar o voto dos abstencionistas.",
        distribution(
            "Intenção atual, segundo o voto lembrado do 1º turno",
            topic["opcoes"],
            topic["linhas"],
            [19],
        )
        + callout(
            "43% para Lula, 38% para Flávio — dentro de qual grupo?",
            "Dentro dos 22% que declaram <b>branco, nulo ou não comparecimento</b> no primeiro turno. A diferença favorece Lula em cinco pontos nesse grupo misto. Não significa que 43% de todos os abstencionistas votarão nele, nem que a Quaest tenha distribuído abstenções por um algoritmo.",
        )
        + f'<p>Tomando os números arredondados literalmente, 22% × 43% = <b>{fmt(tr["contribuicoes_total_pp"]["lula"],2)} pontos do total</b> em intenção de Lula; 22% × 38% = <b>{fmt(tr["contribuicoes_total_pp"]["flavio"],2)}</b> em Flávio. O saldo deste grupo é {fmt(tr["vantagem_lula_total_pp"],2)} ponto a favor de Lula no total. Os 81% que declaram um dos dois nomes não têm comparecimento futuro observado.</p>'
        + "<h3>A matriz que o relatório não entrega</h3>"
        + "<p>A página 19 mostra antigos eleitores de três candidatos, “outros” e o grupo misto. Faltam as linhas de quem lembra voto em Lula ou Flávio, além do NS/NR sobre o passado. Não é possível conferir retenção, trocas entre finalistas e fechamento do novo placar com essa matriz parcial. As bases de cada linha também não são publicadas.</p>"
        + aggregation()
        + "<h3>Uma checagem que contraria a acusação fácil</h3>"
        + pairs(
            "Memória do voto × urna: mesmo denominador, o eleitorado",
            {
                "Flávio": (35, u["flavio"]),
                "Lula": (34, u["lula"]),
                "Branco/nulo/ausência": (22, u["sem_voto_valido"]),
            },
            labels=("Memória", "Urna"),
            digits=2,
            source="Memória: p. 129. Urna: TSE de 04/10, 27 UFs, sem exterior, sobre todos os aptos. Há ainda 3% NS/NR no voto lembrado; bases individuais não publicadas.",
        )
        + f'<p>A urna teve {fmt(u["sem_voto_valido"],2)}% sem voto válido — {fmt(u["abstencao"],2)}% de ausentes e {fmt(u["brancos"]+u["nulos"],2)}% de brancos/nulos sobre os aptos. A memória registra 22% no grupo misto, mais 3% NS/NR. Flávio e Lula lembrados também ficam próximos da urna nessa régua. <b>Não há aqui evidência de uma enorme falta de abstencionistas na memória agregada.</b> Isso tampouco demonstra calibração pelo voto anterior ou representatividade dos subgrupos.</p>'
        + ref(129)
        + note(
            'Referência oficial: <a href="assets/quaest_14102026_integra/auditoria.json">contagens, arquivo, snapshot e SHA-256</a>. Não comparar os 35% e 34% de memória aos 47% e 45% dos válidos: os denominadores são diferentes.'
        )
        + details(
            "Quanto muda se esse grupo gerar menos votos válidos?",
            "<p>Teste de sensibilidade: reduzir proporcionalmente apenas os votos válidos declarados pelo grupo misto, mantendo o restante do topline. O cenário de 100% reproduz a intenção publicada. Zero significa que nenhuma de suas escolhas F/L vira voto válido; pode haver ausência ou voto inválido, sem distingui-los. Não é previsão nem correção.</p>"
            + table(
                [
                    "Fração mantida da conversão declarada (%)",
                    "F / total",
                    "L / total",
                    "F × L / válidos",
                ],
                table_rows,
            )
            + note(
                "São produtos de percentuais arredondados, sem IC próprio. Não identificar os 22% inteiros como abstencionistas, nem aplicar automaticamente esse cenário às centrais."
            ),
        ),
    )


def likely_voter(data):
    rows = data["eleitor_provavel"]["sensibilidades_por_interesse"]
    return section(
        2,
        "comparecimento",
        "Escolher um nome<br><em>não revela quem vai comparecer.</em>",
        "Não localizamos regra pública de eleitor provável nesta íntegra ou na transcrição do registro consultada.",
        '<div class="q-verdict-grid"><article><span>O que está publicado</span><h3>Eleitores de 16 anos ou mais</h3><p>Universo declarado na p. 2. A p. 3 descreve cotas e pós-estratificação por “MrP ou rake”.</p></article><article><span>O que falta para um likely voter</span><h3>Regra, limiar e validação</h3><p>Não há escore de comparecimento, taxa prevista, corte de inclusão, tamanho da amostra filtrada ou teste retrospectivo divulgado.</p></article></div>'
        + ref(2, 3)
        + callout(
            "9% não é uma previsão de abstenção",
            "O número junta branco, nulo e “não vai votar”. Não separa os que vão comparecer e invalidar o voto dos que pretendem faltar. Mesmo quem escolhe um candidato pode se abster. Portanto, nem 9% de ausência nem 91% de presença são estimativas publicadas de comparecimento.",
        )
        + "<p>A abstenção efetiva do primeiro turno foi 20,84% no Brasil, sem exterior. Isso torna indefensável transportar as respostas de intenção diretamente para volumes de votos sem uma hipótese de presença. Mas não demonstra que uma futura abstenção menor seja matematicamente impossível. A crítica verificável é a <b>ausência de uma ponte publicada entre intenção e voto efetivo</b>.</p>"
        + turnout_reference()
        + distribution(
            "Interesse declarado: a medida que existe no relatório",
            ["Muito", "Pouco", "Nada", "NS/NR"],
            {"Total": [51, 31, 17, 1]},
            [117],
        )
        + pairs(
            "Dentro de cada nível de interesse: escolhas publicadas",
            {
                "Muito interessado": (50, 47),
                "Pouco interessado": (45, 41),
                "Nada interessado": (39, 37),
            },
            source="Quaest, p. 29. Percentuais no próprio grupo; NS/NR de interesse não tem voto publicado. Interesse não é presença observada.",
        )
        + ref(29)
        + table(
            [
                "Grupo retido",
                "F × L / total do grupo",
                "Soma F+L",
                "F × L / apenas os dois",
            ],
            [
                [
                    r["grupo"],
                    f'{r["flavio"]} × {r["lula"]}',
                    f'{r["soma"]}%',
                    f'{fmt(r["flavio_validos"],2)} × {fmt(100-r["flavio_validos"],2)}',
                ]
                for r in rows
            ],
        )
        + "<p>Se alguém retivesse apenas os “muito interessados”, obteria 50 × 47 no grupo, ou <b>51,55% × 48,45%</b> entre os dois nomes. A mudança frente aos 51,11% × 48,89% do total é pequena nessa conta. Isso exclui todos os demais grupos por uma regra nossa, sem validação; <b>não é um filtro divulgado ou recomendado</b>. Os indecisos e não votantes não se transformam automaticamente em ausência.</p>"
        + note(
            "A p. 31 mede firmeza da escolha, não firmeza de comparecimento. Não se infere que não existam tratamentos internos não divulgados. Faltam o questionário integral arquivado, microdados e documentação operacional. As centrais Arvor mantêm suas hipóteses de presença explícitas e independentes desta investigação."
        ),
    )


def theme_details(topic):
    pages = topic["paginas"]
    text = (
        "<p>"
        + esc(topic["leitura"])
        + "</p><p><b>Limite:</b> "
        + esc(topic["limite"])
        + "</p>"
    )
    text += (
        '<p class="note"><b>Formulação publicada:</b> '
        + esc(topic["formulacao_publicada"])
        + "</p>"
    )
    text += '<p class="note"><b>Universo:</b> ' + esc(topic["universo"]) + ".</p>"
    if topic["valores"]:
        text += table(
            ["Resposta", "Publicado (%)"],
            [[esc(k), fmt(v, 0)] for k, v in topic["valores"].items()],
        )
    if topic.get("linhas"):
        text += table(
            ["Grupo/item", *topic["opcoes"]],
            [
                [esc(k), *[fmt(v, 0) for v in values]]
                for k, values in topic["linhas"].items()
            ],
        )
    for name, values in topic.get("grupos", {}).items():
        text += (
            "<h4>"
            + esc(name)
            + "</h4>"
            + table(
                ["Resposta", "Publicado (%)"],
                [[esc(k), fmt(v, 0)] for k, v in values.items()],
            )
        )
    for dim, cross in topic.get("recortes", {}).items():
        text += (
            "<h4>"
            + esc(dim)
            + "</h4>"
            + table(
                ["Recorte", *cross["opcoes"]],
                [
                    [esc(k), *[fmt(v, 0) for v in values]]
                    for k, values in cross["linhas"].items()
                ],
            )
            + ref(cross["pagina"])
        )
    text += ref(*pages)
    text += f'<p><a href="?pagina={topic["pagina_total"]}#documentos">Ver a página original neste dossiê</a> · <a href="assets/quaest_14102026_integra/{topic["id"]}.json">Dados desta leitura</a></p>'
    return details(
        esc(topic["titulo"]) + " · " + esc(topic["destaque"]),
        text,
        ident="tema-" + topic["id"],
    )


def complete_reading(data):
    topics = {t["id"]: t for t in data["temas"]}
    return section(
        8,
        "integra",
        "Além do placar.<br><em>Todos os 23 temas do relatório.</em>",
        "Cada tema tem uma leitura, seus limites, números transcritos e acesso a todas as páginas correspondentes.",
        distribution(
            "Firmeza atual da escolha: Lula e Flávio",
            topics["firmeza"]["recortes"]["Intenção 2T"]["opcoes"],
            topics["firmeza"]["recortes"]["Intenção 2T"]["linhas"],
            [31, 32],
        )
        + "<p>Firmeza alta não resolve a questão do comparecimento. A série de firmeza muda do primeiro para o segundo turno. O salto da expectativa de vitória de Flávio, de 35% para 53%, também atravessa uma mudança de pergunta e de contexto; não são 18 pontos de votos transferidos.</p>"
        + '<div class="q-chart-grid">'
        + pairs(
            "Intenção × expectativa de vitória",
            {"Flávio": (46, 53), "Lula": (44, 35)},
            labels=("Intenção", "Expectativa"),
            source="Quaest, pp. 18 e 62. Perguntas distintas; expectativa de vitória não é probabilidade estimada.",
        )
        + pairs(
            "Motivo afirmativo × voto contra o outro polo",
            {"Voto lembrado em Lula": (73, 23), "Voto lembrado em Flávio": (53, 42)},
            labels=("Melhor nome", "Contra polo"),
            source="Quaest, pp. 136 e 139. Grupos condicionais ao voto lembrado; demais respostas ficam nas tabelas. Não mede risco de abstenção.",
        )
        + "</div>"
        + distribution(
            "Renda e custo de vida no último ano",
            list(topics["custo_vida"]["valores"]),
            {"Total": list(topics["custo_vida"]["valores"].values())},
            [103],
        )
        + "<p>Os 55% que relatam renda parada ou crescendo menos que o custo de vida são percepção sobre orçamento familiar. Não são uma medida de renda real extraída da PNAD. A direção do país tem 49% de avaliação errada e 40% certa, com 11% NS/NR; a onda anterior dessa série é agosto.</p>"
        + distribution(
            "Propostas: conhecer antes e aprovar depois são medidas diferentes",
            topics["propostas"]["opcoes"],
            topics["propostas"]["linhas"],
            [114, 115],
        )
        + "<p>O gráfico mantém as cinco respostas separadas. Por exemplo, os 88% favoráveis a salário mínimo acima da inflação incluem 29% que não conheciam a proposta antes da apresentação. A autoria de cada item não está identificada nessa página. Os recortes políticos da p. 115 não rotulam todas as células pequenas; não completamos esses valores por adivinhação.</p>"
        + '<div class="q-theme-index">'
        + "".join(
            f'<a href="#tema-{esc(t["id"])}"><b>{esc(t["titulo"])}</b><span>{esc(t["destaque"])}</span></a>'
            for t in data["temas"]
        )
        + "</div>"
        + '<div id="q-temas-completos">'
        + "".join(theme_details(t) for t in data["temas"])
        + "</div>"
        + note(
            "Cobertura: catálogo das 152 páginas e leitura dos 23 temas. As tabelas transcrevem os totais e recortes identificados em cada tema; séries históricas completas e demais cruzamentos permanecem nas páginas originais, sem promessa de transcrição célula a célula. Os 130 recortes do G1 continuam no explorador abaixo."
        ),
    )
