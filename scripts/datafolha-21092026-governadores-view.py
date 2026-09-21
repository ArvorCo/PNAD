"""Editorial section for the comparison of state and presidential preferences."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(table, fmt):
    data = json.loads(
        (ROOT / "docs/assets/datafolha_21092026_governadores.json").read_text()
    )
    states = {s["uf"]: s for s in data["states"]}

    def source(uf, page):
        return f'<a class="refs" href="fontes/datafolha_21092026_governador_{uf.lower()}.pdf#page={page}">{uf} · governador p. {page}</a>'

    def pres(page):
        return f'<a class="refs" href="fontes/datafolha_21092026_estaduais.pdf#page={page}">Presidente p. {page}</a>'

    h = """<section id="governadores"><div class="section-head"><p class="kicker">02B / GOVERNADOR × PRESIDENTE</p><h2>Cleitinho, Tarcísio e Lula.<br>A conta do voto dividido.</h2><p class="lead">Cleitinho supera Flávio em 14 pontos em MG; Tarcísio o supera em nove em SP. Lula também supera os candidatos estaduais do PT. A diferença precisa ser explicada pelo cruzamento das respostas, mas não demonstra, por si só, erro da pesquisa.</p></div>
<p>Para testar essa aparente disparidade, usamos exclusivamente <strong>segundo turno contra segundo turno, em votos totais, no campo de 8–10/09</strong>. Em cada estado, os relatórios de governador e presidente informam o mesmo projeto, os mesmos registros, o mesmo número de entrevistas e bases ponderadas idênticas em todas as colunas do segundo turno. Não misturamos essas estaduais com o nacional mais recente de 15–17/09, nem com pesquisas da Quaest.</p>"""
    h += table(
        [
            "Estado e campo",
            "Governador · 2º turno",
            "Presidente · 2º turno",
            "Diferenças entre cargos",
            "Documentos",
        ],
        [
            [
                "MG · 8–10/09",
                "Cleitinho 59 × Patrus 24",
                "Lula 46 × Flávio 45",
                "Cleitinho − Flávio: +14 pp<br>Lula − Patrus: +22 pp",
                source("MG", 40) + " · " + pres(94),
            ],
            [
                "SP · 8–10/09",
                "Tarcísio 56 × Haddad 35",
                "Lula 42 × Flávio 47",
                "Tarcísio − Flávio: +9 pp<br>Lula − Haddad: +7 pp",
                source("SP", 39) + " · " + pres(58),
            ],
        ],
    )
    h += "<p>As diferenças medem a distância entre apoios a nomes e cargos distintos. <strong>Não são uma transferência perdida por Flávio nem votos automaticamente disponíveis para ele.</strong> O eleitor pode escolher Lula e um governador de outro campo; também pode escolher o governador e não escolher nenhum finalista presidencial.</p>"
    h += f"<p>Há um contraponto importante em MG: contra <strong>Kalil</strong>, Cleitinho marca <strong>54%</strong>, e o adversário, 29%. O intervalo entre Cleitinho e Flávio cai de 14 para nove pontos ao mudar o adversário estadual. A força de uma candidatura depende também do confronto oferecido. {source('MG', 39)}</p>"
    h += "<h3>O próprio recorte de preferência partidária exige algum voto dividido.</h3><p>Na coluna de quem declara o <strong>PT como partido de preferência</strong>, os relatórios mostram os números abaixo. Essa coluna não é o eleitorado de Lula, nem a escala de identificação entre bolsonarismo e petismo: são perguntas diferentes.</p>"
    h += table(
        [
            "Mesmo recorte: preferência pelo PT",
            "Base ponderada",
            "Vota em Lula · 2º",
            "Vota no governador · 2º",
            "Interseção mínima pelos pontos publicados",
        ],
        [
            ["MG", 291, "97%", "34% em Cleitinho", "31% do recorte PT"],
            ["SP", 387, "95%", "19% em Tarcísio", "14% do recorte PT"],
        ],
    )
    h += f'<p class="table-source">MG: {source("MG", 40)} · {pres(94)}. SP: {source("SP", 39)} · {pres(58)}. A última coluna é cálculo nosso, não cruzamento medido.</p>'
    h += '<div class="formula">Mínimo com os dois votos = máximo(0, voto em Lula + voto no governador − 100)<br>MG, dentro do recorte PT: 97 + 34 − 100 = 31%<br>SP, dentro do recorte PT: 95 + 19 − 100 = 14%</div>'
    h += "<p><strong>Se as respostas usam os mesmos eleitores e os mesmos pesos finais</strong>, pelo menos 31% do recorte PT em MG precisariam combinar Lula com Cleitinho; em SP, pelo menos 14% precisariam combinar Lula com Tarcísio, tomando os pontos publicados literalmente. Admitindo meio ponto de arredondamento em cada porcentagem, os pisos passam a <strong>30% e 13%</strong> desses recortes. São limites lógicos da tabela ponderada, não estimativas populacionais com confiança de 95%.</p>"
    h += f"<p>Somente essas parcelas do recorte PT corresponderiam a pisos de <strong>{fmt(states['MG']['pt']['state_lower_rounding'])} pontos do total ponderado de MG</strong> e <strong>{fmt(states['SP']['pt']['state_lower_rounding'])} pontos de SP</strong>, já admitindo o arredondamento das porcentagens. Tratamos as bases publicadas como exatas nessa conta; o arredondamento delas introduz pequena incerteza adicional. As bases e os registros coincidem, mas isso não permite verificar se cada pessoa recebeu o mesmo peso nas duas perguntas.</p>"
    h += "<details><summary>Por que somar só os placares gerais esclarece menos?</summary><p>Em MG, Cleitinho 59% + Lula 46% = 105%: no mínimo cinco pontos precisariam pertencer aos dois apoios, ou quatro admitindo o arredondamento. Em SP, Tarcísio 56% + Lula 42% = 98%, portanto os totais sozinhos permitem interseção zero. A coluna de preferência pelo PT impõe uma interseção positiva em ambos os estados. Não somamos o piso geral com o piso partidário, pois são grupos sobrepostos.</p><p>Os máximos também são amplos: dentro do recorte PT, sem tolerância de arredondamento, a interseção pode variar de 31% a 34% em MG e de 14% a 19% em SP. Nada disso revela o voto de pessoas identificáveis ou recupera microdados.</p></details>"
    h += "<h3>O que pedir ao Datafolha para esclarecer a diferença.</h3>"
    h += table(
        ["Documento ou resposta necessária", "O que permite verificar"],
        [
            [
                "Matriz governador × presidente por estado",
                "Medir diretamente Lula + Cleitinho, Lula + Tarcísio e os outros pares, com branco/nulo e indecisos incluídos.",
            ],
            [
                "Mesmas entrevistas e mesmos pesos em cada cenário?",
                "Confirmar o pressuposto dos limites de interseção; informar filtros, recusas e reponderações específicas por pergunta.",
            ],
            [
                "Bases brutas, ponderadas e erros dos cruzamentos",
                "Distinguir poucos casos com muito peso de um comportamento bem representado e calcular a incerteza do voto dividido.",
            ],
            [
                "Conciliação das tabelas publicadas",
                "Reproduzir os totais a partir das células não arredondadas e explicar eventuais diferenças entre os dois relatórios.",
            ],
        ],
    )
    h += "<p>Não localizamos a matriz governador × presidente nos dois relatórios completos de governador nem no relatório presidencial estadual consultado. As margens por partido já tornam o voto dividido uma explicação matematicamente compatível; a matriz revelaria sua dimensão efetiva e o restante das combinações.</p>"
    checks = [p for s in data["states"] for p in s["proofs"]]
    h += f"<aside><b>Disparidade encontrada; inconsistência aritmética não demonstrada.</b>Extraímos as 27 tabelas dos anexos estaduais e fizemos {len(checks)} recomposições por sexo e natureza do município. O maior resíduo foi de {fmt(max(abs(p['residual']) for p in checks))} ponto, dentro do que o arredondamento das células e dos totais pode explicar nesta checagem. Ela não certifica o campo nem testa todas as relações conjuntas. As divergências documentais de municípios e datas do nacional, descritas adiante, continuam sendo questões objetivas separadas.</aside>"
    h += "<p><strong>A conclusão que os dados sustentam:</strong> a vantagem de Cleitinho ou Tarcísio não obriga Flávio a ter votação semelhante, e a votação de Lula não obriga Patrus ou Haddad a acompanhá-lo. O ponto auditável é se o Datafolha consegue mostrar a combinação de votos, seus pesos e sua incerteza que sustentam esses resultados. Seria uma inconsistência verificável se essa matriz, sob os mesmos pesos e universos, não recompusesse as margens além do arredondamento.</p>"
    h += f'<p class="table-source"><a href="assets/datafolha_21092026_governadores.json">27 tabelas, bases, cálculos, conferências e fontes (JSON)</a> · <a href="{states["MG"]["source"]["url"]}">PDF original MG no Datafolha</a> · <a href="{states["SP"]["source"]["url"]}">PDF original SP no Datafolha</a>. Reproduzir: <code>python3 scripts/datafolha-21092026-governadores.py</code>, seguido pelo gerador do dossiê.</p></section>'
    return h
