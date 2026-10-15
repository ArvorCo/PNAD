"""Crítica da agregação: fontes primárias e contraprova aritmética ilustrativa."""

from html import escape as esc

from dossies_2t_2026.view import callout, details, note, table

from ..charts import pairs
from .data import DATA, read


def sources():
    return read(DATA / "referencias.json")


def cite(key, label=None):
    ref = next(r for r in sources()["fontes"] if r["id"] == key)
    return f'<a href="{esc(ref["url"], quote=True)}">{esc(label or ref["rotulo"])}</a>'


def aggregation():
    example = sources()["exemplo_agregacao"]
    rows = {}
    cells = []
    for scenario in example["cenarios"]:
        for group in scenario["grupos"]:
            values = group["pessoas_por_resposta"]
            base = sum(values)
            cells.append([scenario["nome"], group["grupo"], base, *values])
            if group["grupo"] == "Ausentes":
                rows[scenario["nome"] + " · ausentes"] = (
                    100 * values[0] / base,
                    100 * values[1] / base,
                )
    return (
        '<div id="agregacao"><h3>Uma linha só apaga uma distinção essencial</h3>'
        "<p><b>Quem vota branco ou nulo comparece. Quem se abstém não comparece.</b> "
        "A documentação técnica do TSE separa comparecimento, abstenção e tipos de voto. "
        "O International IDEA inclui brancos e inválidos no total de pessoas que votaram; "
        "sua taxa de comparecimento usa os registrados como denominador, enquanto a taxa "
        "de votos inválidos usa o total de votos. Somar essas taxas sem harmonizar a base "
        "mistura denominadores. "
        + cite("tse", "TSE · perguntas 1–3")
        + " · "
        + cite("idea", "International IDEA · pp. 9–10")
        + ".</p>"
        + table(
            ["Resultado observado", "Compareceu?", "Escolheu candidatura válida?"],
            [
                ["Voto branco", "Sim", "Não"],
                ["Voto nulo", "Sim", "Não"],
                ["Abstenção", "Não", "Não houve voto"],
            ],
        )
        + "<p>Agregar branco e nulo pode servir ao estudo de votos inválidos. Agregar os "
        "três pode descrever quem não deu voto válido, com denominador comum. Mas essa "
        "soma não mede ausência, mobilização ou a preferência dos ausentes. Tampouco "
        "revela os motivos de cada comportamento: não se pode chamar todo voto inválido "
        "de protesto.</p>"
        + callout(
            "A referência profissional pede o percentual de quem não vai votar",
            "O guia <b>ESOMAR/WAPOR de agosto de 2026</b>, §6.5(6), exige publicar "
            "indecisos/não respostas e o percentual dos que dizem que não votarão; também "
            "exige documentar redistribuições de respostas para candidaturas. O §7.1(9) "
            "reitera a divulgação dos que não votarão. A linha conjunta de 9% da Quaest "
            "não permite recuperar esse percentual. Esta é uma lacuna concreta da "
            "publicação examinada frente à referência profissional. "
            + cite("esomar_wapor", "Guia · pp. 13 e 16")
            + ".",
        )
        + "<p>O guia não determina três linhas com esses nomes nem é uma decisão sobre "
        "a Quaest. Separar branco e nulo entre si é uma recomendação analítica nossa; "
        "identificar os que dizem que não votarão tem apoio textual direto. Não estamos "
        "afirmando infração legal ou existência de redistribuição oculta.</p>"
        + "<h3>O mesmo 43% permite histórias opostas sobre os ausentes</h3>"
        + "<p>O resultado misto é uma média ponderada das preferências de três grupos. "
        "Sem seus pesos e cruzamentos, essa média não identifica cada componente. "
        "<b>Exemplo fictício:</b> 100 pessoas, sendo 50 ausentes no turno anterior e "
        "50 que votaram branco/nulo. Em ambos os exemplos abaixo, o grupo inteiro "
        "termina com <b>38% Flávio, 43% Lula, 2% indecisos e 17% sem escolha</b>. "
        "Dentro dos ausentes, porém, a liderança se inverte.</p>"
        + pairs(
            "Demonstração fictícia · preferência dentro dos 50 ausentes",
            rows,
            source="Construção aritmética Arvor, não estimativa da Quaest. A divisão 50/50 é inventada para demonstrar a perda de informação; não reproduz a composição da pesquisa nem da urna.",
        )
        + details(
            "Conferir as 100 pessoas de cada exemplo",
            table(
                ["Exemplo", "Passado", "Pessoas", "F", "L", "Ind.", "Sem escolha"],
                cells,
            )
            + note(
                "Células são contagens fictícias. Cada exemplo soma 100 pessoas; "
                "cada linha soma 50. Sem escolha junta as respostas futuras "
                "branco/nulo/não votar apenas para reproduzir a tabela publicada. "
                "Os exemplos não estimam abstenção futura."
            ),
        )
        + "<p><b>A perda demonstrada está na publicação.</b> A formulação da p. 19 "
        "pergunta primeiro se a pessoa foi à eleição e, se sim, em quem votou. "
        "Isso indica que comparecimento e escolha foram perguntados em etapas; não "
        "autoriza afirmar que a Quaest deixou de coletar a distinção. O questionário "
        "integral, seu roteamento e as bases ainda precisam ser conferidos. "
        '<a href="fontes/quaest_14102026.pdf#page=19">Ver a p. 19</a>.</p>'
        + "<h3>O que tornaria a transferência auditável</h3>"
        + "<p>A AAPOR prevê divulgação da formulação e opções das perguntas, regras "
        "do universo e ponderação; suas normas de abril de 2021 também incluem bases "
        "não ponderadas dos subgrupos entre as informações fornecidas mediante "
        "solicitação. Isso sustenta pedir documentação, sem fingir que a ausência "
        "de cada detalhe nesta apresentação prova descumprimento de um pedido. "
        + cite("aapor", "AAPOR · §III.A e §III.B.6")
        + ".</p>"
        + "<ul><li>Publicar separadamente ausência, branco, nulo e NS/NR no voto "
        "lembrado, com a intenção atual de cada grupo e as linhas dos dois finalistas.</li>"
        "<li>Informar bases brutas e ponderadas, denominadores, filtros e incerteza. "
        "Células pequenas exigem cautela; eventual agregação deve ser justificada.</li>"
        "<li>Medir propensão a comparecer separadamente da escolha de candidato e "
        "explicar como uma eventual regra de eleitor provável entra nos resultados.</li></ul>"
        + note(
            "São recomendações Arvor de publicação e análise. A agregação limita o que "
            "se pode concluir sobre os subgrupos; sozinha, não demonstra viés no "
            "46 × 44, favorecimento deliberado ou transferência de abstenção para Lula."
        )
        + "</div>"
    )


def turnout_reference():
    return (
        "<p>Há evidência empírica para não equiparar declaração e presença: Keeter e "
        "Igielnik confrontaram entrevistas com registros de comparecimento nas eleições "
        "legislativas americanas de 2014. Os modelos avaliados superaram a simples "
        "seleção de quem dizia que iria votar. É um estudo de uma eleição nos EUA, "
        "não uma validação para o Brasil nem um ajuste transportável para Lula ou Flávio. "
        + cite("pew", "Pew Research Center · 2016")
        + ".</p><p>Um modelo de eleitor provável pode selecionar entrevistados ou "
        "ponderá-los por probabilidade de presença. Para avaliá-lo aqui, seriam "
        "necessários definição, variáveis, efeito sobre o resultado e validação pertinente. "
        "O guia ESOMAR/WAPOR pede explicitar universo e variáveis de seleção (§6.5, p. 12). "
        + cite("esomar_wapor", "Guia de 2026")
        + ".</p>"
    )


def bibliography():
    items = []
    for ref in sources()["fontes"]:
        name = cite(ref["id"])
        if ref.get("arquivo_publico"):
            name += f'<br><a href="{ref["arquivo_publico"]}">Cópia arquivada</a>'
        items.append(
            "<li><b>"
            + name
            + '</b><p class="note">'
            + esc(ref["localizador"])
            + "</p><p>"
            + esc(ref["uso"])
            + "</p></li>"
        )
    return (
        '<div id="referencias-metodologicas"><h3>Referências da crítica à agregação</h3>'
        + '<ol class="q-reference-list">'
        + "".join(items)
        + "</ol>"
        + note(
            "Consultadas em 15/10/2026. Definições oficiais, normas profissionais e "
            "evidência empírica têm funções distintas; sua aplicação à Quaest é análise "
            "Arvor. Nenhuma instituição citada emitiu aqui um parecer sobre esta pesquisa. "
            '<a href="assets/quaest_14102026_integra/referencias.json">Referências, '
            "limites, hashes e exemplo reproduzível</a>."
        )
        + "</div>"
    )
