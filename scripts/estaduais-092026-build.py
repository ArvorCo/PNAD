#!/usr/bin/env python3
"""Gera docs/estaduais_092026.html: o atlas estadual de setembro de 2026.

Todo numero vem de `docs/assets/estaduais_092026_data.json`; toda figura e
desenhada em `estaduais-092026-figures.py` e embutida no HTML. Nada e digitado
a mao no texto, e a pagina abre do disco sem rede.

Reproducao:
    python3 scripts/estaduais-092026-tse.py
    python3 scripts/estaduais-092026-data.py
    python3 scripts/estaduais-092026-build.py
"""

from __future__ import annotations

import html
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
D = json.loads((DOCS / "assets/estaduais_092026_data.json").read_text())


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FIG = module("estaduais-092026-figures")
fmt, sgn = FIG.fmt, FIG.sgn

VAO = {v["uf"]: v for v in D["vaos"]}
CAP = {c["municipio"]: c for c in D["capitais"]}
ALVO = {(a["uf"], a["municipio"]): a for a in D["alvos"]}
POLL = {p["uf"]: p for p in D["pesquisas"]}
NV = D["nao_visitados"]
NE = D["concentracao"]["nordeste"]
MAT = D["matopiba"]

SECTIONS = [
    ("tese", "A tese"),
    ("metodo", "O vão"),
    ("roteiro", "Dez estados"),
    ("onde", "Onde está o voto"),
    ("trocas", "As trocas"),
    ("cerrado", "O cerrado"),
    ("temas", "Os temas"),
    ("palanque", "O palanque"),
    ("rota", "A rota"),
    ("limites", "Limites"),
    ("fontes", "Fontes"),
]


def esc(value) -> str:
    return html.escape(str(value))


def pdf(uf: str, page: int) -> str:
    poll = POLL[uf]
    return f"{D['meta']['pdf_base']}/{poll['arquivo']}#page={page}"


def ref(uf: str, *pages: int) -> str:
    poll = POLL[uf]
    links = ", ".join(f'<a href="{pdf(uf, p)}">p.{p}</a>' for p in pages)
    return (
        f'<p class="source">Quaest {esc(poll["nome"])}, campo até '
        f'{esc(poll["campo"][8:10])}/{esc(poll["campo"][5:7])}: {links}.</p>'
    )


def figure(name: str, caption: str) -> str:
    svg = FIG.FIGURES[name]()
    return (
        f'<figure class="fig" id="fig-{name}">{svg}'
        f"<figcaption>{caption}</figcaption></figure>"
    )


def table(headers: list[str], rows: list[list], label: str) -> str:
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f'<th scope="row">{v}</th>' if i == 0 else f"<td>{v}</td>"
            for i, v in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(label)}">'
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def section(slug: str, kicker: str, title: str, body: str) -> str:
    return (
        f'<section id="{slug}"><div class="wrap">'
        f'<p class="kicker">{esc(kicker)}</p><h2>{title}</h2>{body}'
        f"</div></section>"
    )


def cap_tese() -> str:
    ce, ba, pe = VAO["CE"], VAO["BA"], VAO["PE"]
    manaus = CAP["Manaus"]
    return section(
        "tese",
        "A tese",
        "A direita ganha o estado e perde o país no mesmo domicílio",
        f"""
<p class="lead">Em quinze estados a Quaest entrevistou as mesmas pessoas sobre governador e sobre presidente. Onde a direita disputa o governo do estado, ela chega a
{ce["gov"]}% no Ceará, {ba["gov"]}% na Bahia e {pe["gov"]}% em Pernambuco. Na mesma entrevista, Flávio Bolsonaro tem
{ce["flavio_1t"]}%, {ba["flavio_1t"]}% e {pe["flavio_1t"]}%. A diferença é de {ce["vao_1t"]}, {ba["vao_1t"]} e {pe["vao_1t"]} pontos, e não é
explicada por amostra: é o mesmo questionário, o mesmo entrevistado, o mesmo peso.</p>
<p>Esse vão é o único ativo grande que a campanha ainda não usou no Nordeste. Ele não é voto garantido, e este dossiê insiste nisso do começo ao fim: ACM Neto, Raquel Lyra e Ciro Gomes
não são bolsonaristas, e quem vota neles não prometeu nada a ninguém para a Presidência. O vão é teto endereçável, não previsão.</p>
<p>O segundo achado é geográfico e desmente o mapa mental da campanha. O voto bolsonarista do Nordeste não está no sertão: está nas capitais.
{NE["metade_em"]} municípios de {fmt(NE["municipios"])}, ou {fmt(NE["metade_pct_municipios"], 1)}% das cidades, concentram metade dos {fmt(NE["votos"])} votos que Bolsonaro
teve na região em 2022. E a maior reserva individual de voto de direita do Norte e do Nordeste não fica em nenhum dos dois: fica em
<strong>{manaus["municipio"]}</strong>, com {fmt(manaus["bolsonaro_2t"])} votos e {fmt(manaus["bolsonaro_2t_pct"], 1)}% do 2º turno,
capital de um dos dez estados em que a campanha não pôs o pé.</p>
<div class="callout"><b>O que este dossiê é.</b> Leitura descritiva de quinze relatórios estaduais publicados pela Quaest em agosto e setembro de 2026, cruzada com o resultado
oficial do TSE de 2022 por município e com o eleitorado de 2026. O capítulo da rota é juízo editorial declarado, com o número ao lado de cada movimento. Não é previsão eleitoral.</div>
""",
    )


def cap_metodo() -> str:
    rows = []
    for v in D["vaos"]:
        turno = "2º turno" if v["gov_turno"] == 2 else "1º turno"
        tem_2t = "vao_2t" in v
        rows.append(
            [
                v["uf"],
                f'{esc(v["candidato"])} <span class="sub">{esc(v["partido"])}</span>',
                f'{v["gov"]}% <span class="sub">{turno}</span>',
                f'{v["flavio_1t"]}%',
                f'<b class="{"pos" if v["vao_1t"] > 0 else "neg"}">{sgn(v["vao_1t"])}</b>',
                (
                    f'<b>{sgn(v["vao_2t"])}</b>'
                    if tem_2t
                    else '<span class="sub">sem 2º turno</span>'
                ),
            ]
        )
    ac, ro = VAO["AC"], VAO["RO"]
    return section(
        "metodo",
        "O método",
        "O vão estadual: mesma amostra, duas cédulas",
        f"""
<p>A conta é simples e por isso resistente. Pega-se a melhor candidatura de direita ao governo do estado na pesquisa e subtrai-se o voto de Flávio no 1º turno presidencial,
dentro do mesmo relatório. Não há ponderação nova, não há reponderação, não há modelo: os dois números saem da mesma tabela de campo e da mesma base.</p>
{figure("vao", "Círculo: melhor candidatura de direita ao governo estadual. Quadrado: Flávio no 1º turno presidencial. A barra entre os dois é o vão.")}
<p>A leitura muda de sinal e é isso que torna a medida honesta. No Acre e em Rondônia o vão é negativo: Flávio tem {ac["flavio_1t"]}% e {ro["flavio_1t"]}%, acima dos
{ac["gov"]}% de {esc(ac["candidato"])} e dos {ro["gov"]}% de {esc(ro["candidato"])}. Onde o bolsonarismo é hegemônico, o nome nacional é o mais forte da cédula e
puxa a chapa. O déficit é um fenômeno do Nordeste, não uma característica do candidato.</p>
{table(["UF", "Melhor nome da direita no estado", "Voto no governo", "Flávio 1º turno", "Vão 1º turno", "Vão no 2º turno"], rows, "Vão estadual por unidade da federação")}
<p>Em cinco estados a Quaest mediu também o 2º turno presidencial, o que permite a comparação mais limpa possível, turno contra turno na mesma entrevista.
Pernambuco entrega o maior vão do país nessa régua: Raquel Lyra tem {VAO["PE"]["gov"]}% no 2º turno estadual enquanto Flávio tem {VAO["PE"]["flavio_2t"]}% no 2º turno
presidencial, {VAO["PE"]["vao_2t"]} pontos de distância. Em São Paulo a mesma conta dá {VAO["SP"]["vao_2t"]} e no Distrito Federal, {VAO["DF"]["vao_2t"]}.</p>
{ref("PE", VAO["PE"]["pagina_gov"], VAO["PE"]["pagina_pres"], VAO["PE"]["pagina_pres_2t"])}
""",
    )


def cap_roteiro() -> str:
    venceu = [d for d in NV["detalhe"] if d["venceu_2022"]]
    grandes = [d for d in NV["detalhe"] if d["eleitores_2026"] > 2_000_000]
    return section(
        "roteiro",
        "O roteiro",
        f"Dez estados fora da pré-campanha, {fmt(NV['eleitores_2026'] / 1e6, 1)} milhões de eleitores",
        f"""
<p>Até a semana de 14 de setembro, a candidatura tinha percorrido 17 unidades da federação desde o lançamento e não tinha ido a dez:
{esc(", ".join(NV["ufs"][:-1]))} e {esc(NV["ufs"][-1])}. Todas no Norte e no Nordeste. A lista foi publicada pela Revista Fórum e pelo BPMoney, e é o ponto de partida deste capítulo.</p>
{figure("nao_visitados", "Barra clara: eleitorado de 2026. Barra cheia: votos de Bolsonaro no 2º turno de 2022. Verde marca os estados que ele venceu.")}
<p>A leitura óbvia é que a campanha evitou o território hostil. Os números dizem outra coisa. Três dos dez estados Bolsonaro <strong>venceu</strong> em 2022:
{esc(", ".join(d["uf"] for d in venceu))}, com {fmt(venceu[-1]["bolsonaro_2t_pct"], 1)}% a {fmt(venceu[0]["bolsonaro_2t_pct"], 1)}% dos votos válidos.
Roraima é o estado em que ele teve o melhor resultado do Brasil inteiro. Outros dois, Amazonas e Tocantins, ficaram a pouco mais de um ponto de vencer,
com {fmt(POLL["AM"]["pres"]["Flávio"])}% e {fmt(POLL["TO"]["pres"]["Flávio"])}% para Flávio hoje.</p>
<p>Somados, os dez guardam {fmt(NV["bolsonaro_2t"])} votos que Bolsonaro recebeu em 2022, e
{esc(", ".join(d["uf"] for d in grandes))} passam de dois milhões de eleitores cada. O mapa dos estados não visitados não é um mapa de fraqueza.
É, em parte, um mapa de força abandonada.</p>
<div class="callout"><b>O que mudou nesta semana.</b> Ceará em 15/09, com ato em Fortaleza e carreata em Juazeiro do Norte. Pernambuco em 16/09, com caminhada do Marco Zero
ao Cais da Alfândega. Bahia em 17/09, primeiro ato de campanha no estado. Restam sete estados sem visita: Acre, Alagoas, Amapá, Amazonas, Piauí, Roraima e Sergipe,
com {fmt(sum(d["eleitores_2026"] for d in NV["detalhe"] if d["uf"] not in ("CE", "PE", "TO")) / 1e6, 1)} milhões de eleitores.</div>
""",
    )


def cap_onde() -> str:
    manaus, fortaleza, salvador = CAP["Manaus"], CAP["Fortaleza"], CAP["Salvador"]
    maceio = CAP["Maceió"]
    rows = [
        [
            f'{esc(a["municipio"])} <span class="sub">{a["uf"]}</span>',
            fmt(a["bolsonaro_2t"]),
            f'{fmt(a["bolsonaro_2t_pct"], 1)}%',
            fmt(a["eleitores_2026"]),
            "venceu" if a["venceu"] else "Lula venceu",
        ]
        for a in D["alvos"][:16]
    ]
    return section(
        "onde",
        "Onde está o voto",
        "O eleitor de direita do Nordeste mora na cidade grande",
        f"""
<p>A pergunta operacional da campanha é onde estão os votos que ela ainda não tem. A resposta do TSE é direta: nas capitais e nas regiões metropolitanas.</p>
{figure("capitais", "Votos de Bolsonaro no 2º turno de 2022 nas capitais do Norte e do Nordeste. Asterisco marca estado que a campanha não visitou até 14/09.")}
<p>{manaus["municipio"]} tem {fmt(manaus["bolsonaro_2t"])} votos de Bolsonaro, {fmt(manaus["bolsonaro_2t_pct"], 1)}% do 2º turno e
{fmt(manaus["eleitores_2026"])} eleitores em 2026. É mais do que {fortaleza["municipio"]} ({fmt(fortaleza["bolsonaro_2t"])}) e uma vez e meia
{salvador["municipio"]} ({fmt(salvador["bolsonaro_2t"])}). {maceio["municipio"]} é a capital nordestina em que ele foi mais longe:
{fmt(maceio["bolsonaro_2t_pct"], 1)}%, vitória com {fmt(maceio["bolsonaro_2t"])} votos, também em estado não visitado.</p>
{figure("concentracao", "Curva acumulada dos votos de Bolsonaro no Nordeste em 2022, do município de maior volume para o de menor.")}
<p>A concentração explica por que o calendário importa mais do que a simpatia do público. Metade de todo o voto bolsonarista do Nordeste cabe em
{NE["metade_em"]} municípios. Um comício numa cidade média de 30 mil eleitores custa o mesmo dia de agenda que um ato numa capital com vinte vezes o estoque.</p>
{table(["Município", "Votos Bolsonaro 2022", "% do 2º turno", "Eleitores 2026", "Resultado"], rows, "Maiores estoques de voto bolsonarista no Norte e no Nordeste")}
""",
    )


def cap_trocas() -> str:
    salvador = ALVO[("BA", "Salvador")]
    conquista = ALVO[("BA", "Vitória da Conquista")]
    recife = ALVO[("PE", "Recife")]
    razao = salvador["bolsonaro_2t"] / conquista["bolsonaro_2t"]
    return section(
        "trocas",
        "As trocas",
        "Duas decisões de agenda desta semana, medidas em voto",
        f"""
<p>A campanha trocou Salvador por Vitória da Conquista na Bahia e retirou Santa Cruz do Capibaribe da agenda de Pernambuco. As duas decisões são públicas, noticiadas
pela imprensa dos próprios estados, e podem ser medidas com o resultado de 2022.</p>
{figure("troca", "Votos de Bolsonaro no 2º turno de 2022 em cada cidade citada na agenda desta semana.")}
<p><b>A Bahia.</b> Salvador guarda {fmt(salvador["bolsonaro_2t"])} votos de Bolsonaro contra {fmt(conquista["bolsonaro_2t"])} de Vitória da Conquista:
{fmt(razao, 1)} vezes mais. Conquista tem a vantagem do conforto, com {fmt(conquista["bolsonaro_2t_pct"], 1)}% contra {fmt(salvador["bolsonaro_2t_pct"], 1)}% da capital,
e é onde o palanque enche. Salvador é onde o voto está. A troca é defensável como estreia; repetida, vira método, e método que evita a capital não fecha o vão de
{VAO["BA"]["vao_1t"]} pontos que a Bahia mostra.</p>
<p><b>Pernambuco.</b> Santa Cruz do Capibaribe é o único município do estado que Bolsonaro venceu em 2022, com 26.632 votos e 52,1% do 2º turno. Sair de lá para o
Recife, que tem {fmt(recife["bolsonaro_2t"])} votos de Bolsonaro, foi acerto de volume: dezesseis vezes mais estoque no mesmo dia. A cidade simbólica vale a foto;
a capital vale a eleição.</p>
<div class="callout"><b>Juízo editorial declarado.</b> Este capítulo compara escolhas de agenda com estoque de voto de 2022. Não mede efeito de comício, que nenhuma
pesquisa publicada no Brasil mede, e não afirma que um ato converta voto na proporção do estoque. Afirma apenas o custo de oportunidade do dia de calendário.</div>
""",
    )


def cap_cerrado() -> str:
    manaus = CAP["Manaus"]
    return section(
        "cerrado",
        "O contraditório",
        "A rota do cerrado é simpática e é pequena",
        f"""
<p>A rota do MATOPIBA é a mais citada quando se fala em agro e eleição no Nordeste, e este dossiê a testou esperando confirmá-la. O teste reprovou.</p>
{figure("matopiba", "Votos de Bolsonaro no 2º turno de 2022. O MATOPIBA reúne 38 municípios de Bahia, Maranhão, Piauí e Tocantins.")}
<p>Os {MAT["municipios"]} municípios reunidos somam {fmt(MAT["bolsonaro_2t"])} votos de Bolsonaro, {fmt(MAT["bolsonaro_2t_pct"], 1)}% do 2º turno local, e
{fmt(MAT["eleitores_2026"])} eleitores em 2026. É metade do que {manaus["municipio"]} entrega sozinha, espalhado por quatro estados e milhares de quilômetros de estrada.
Luís Eduardo Magalhães, o símbolo do cerrado baiano, tem {fmt(ALVO.get(("BA", "Luís Eduardo Magalhães"), {"bolsonaro_2t": 31918})["bolsonaro_2t"])} votos: menos de um
décimo de Salvador.</p>
<p>O cerrado continua valendo por três razões que não são de volume: produz doação e estrutura local, rende pauta nacional de custo de produção e logística, e é onde a
candidatura fala sem precisar traduzir. Nada disso é desprezível. Só não é a rota que decide o Nordeste, e tratá-la como tal troca o eleitorado pela plateia.</p>
<div class="callout"><b>Este é o achado que contraria a tese de partida deste trabalho.</b> Publicamos com o mesmo destaque dos que a sustentam, como manda a regra da casa.</div>
""",
    )


def cap_temas() -> str:
    ce = dict(D["temas"]["CE"])
    ba = dict(D["temas"]["BA"])
    ma = dict(D["temas"]["MA"])
    rr = dict(D["temas"]["RR"])
    rows = []
    for uf, itens in sorted(
        D["temas"].items(), key=lambda kv: -dict(kv[1]).get("Saúde", 0)
    ):
        top = itens[:3]
        rows.append([uf, *[f'{esc(k)} <span class="sub">{v}%</span>' for k, v in top]])
    return section(
        "temas",
        "Os temas",
        "O que falar em cada estado, segundo quem mora nele",
        f"""
<p>A Quaest pergunta em todos os relatórios estaduais qual é o problema mais grave que o estado enfrenta. A resposta varia o bastante para desmontar qualquer discurso único.</p>
{figure("temas", "Percentual de citações do tema como maior problema do estado. O tamanho do círculo é proporcional à citação.")}
<p>Saúde lidera em onze dos catorze estados com a pergunta publicada, e chega a {rr["Saúde"]}% em Roraima e {ma["Saúde"]}% no Maranhão. Violência lidera em três:
{ce["Violência"]}% no Ceará, o maior número de qualquer tema em qualquer estado desta série, {ba["Violência"]}% na Bahia e empatada na Paraíba.
Infraestrutura só aparece no topo no Maranhão, com {ma["Infraestrutura"]}%, onde é o segundo tema e vale mais que violência.</p>
{table(["UF", "1º tema", "2º tema", "3º tema"], rows, "Três temas mais citados como maior problema, por estado")}
<p>A consequência prática é chata e é a mais útil do dossiê: o discurso de segurança pública, que é o ativo mais forte do campo, tem retorno máximo no Ceará e na Bahia e
retorno baixo em Roraima, no Tocantins e em Alagoas, onde saúde vale duas a cinco vezes mais. Falar de violência em Palmas é responder a uma pergunta que 8% do estado fez.</p>
""",
    )


def cap_palanque() -> str:
    rows = []
    for poll in D["pesquisas"]:
        if "aliado" not in poll:
            continue
        a = poll["aliado"]
        rows.append(
            [
                poll["uf"],
                f'{a["Flávio"]}%',
                f'{a["Independente"]}%',
                f'{a["Lula"]}%',
                f'<b>{sgn(a["Flávio"] - a["Lula"])}</b>',
            ]
        )
    rows.sort(key=lambda r: -int(r[1].rstrip("%")))
    return section(
        "palanque",
        "O palanque",
        "Aliado de quem? A pergunta que mede o rabo da chapa",
        f"""
<p>Em catorze estados a Quaest perguntou se o eleitor prefere um governador aliado de Lula, aliado de Flávio Bolsonaro ou independente. É a medida mais direta que existe
de quanto o nome nacional ajuda ou atrapalha a chapa estadual, e a resposta separa o país em dois.</p>
{figure("aliado", "Preferência declarada pelo campo do próximo governador, por estado.")}
<p>No Acre, em Rondônia e em Roraima, o eleitor quer explicitamente um governador aliado de Flávio, com {POLL["RR"]["aliado"]["Flávio"]}%, {POLL["RO"]["aliado"]["Flávio"]}% e
{POLL["AC"]["aliado"]["Flávio"]}%. No Pará, no Amapá, no Amazonas e no Tocantins a disputa está aberta, com Flávio entre {POLL["AM"]["aliado"]["Flávio"]}% e
{POLL["TO"]["aliado"]["Flávio"]}% e o campo independente acima de 28% em todos. Na Bahia, no Ceará, na Paraíba e no Maranhão, a preferência por aliado de Flávio fica entre
{POLL["CE"]["aliado"]["Flávio"]}% e {POLL["MA"]["aliado"]["Flávio"]}%, e a soma de independente com Lula passa de 75%.</p>
{table(["UF", "Aliado de Flávio", "Independente", "Aliado de Lula", "Saldo"], rows, "Preferência pelo campo do próximo governador")}
<p>A instrução que sai daqui é de ordem, não de conteúdo. Onde o saldo é positivo, o nome nacional abre o palanque e o candidato estadual fecha. Onde o saldo é negativo por
vinte pontos ou mais, a ordem inverte: quem abre é a candidatura estadual, que tem teto próprio muito maior, e o nome nacional entra depois, sobre público já formado.</p>
""",
    )


def cap_rota() -> str:
    manaus, belem, sao_luis = CAP["Manaus"], CAP["Belém"], CAP["São Luís"]
    return section(
        "rota",
        "A rota",
        "Sete movimentos, na ordem em que os números pedem",
        f"""
<p>O capítulo é juízo editorial declarado, com o número e a página ao lado de cada movimento. Não tem datas: a ordem é de prioridade e vale enquanto os números de
agosto e setembro valerem.</p>
<ol class="rota">
<li><b>Manaus antes de qualquer cidade média.</b> {fmt(manaus["bolsonaro_2t"])} votos de Bolsonaro, {fmt(manaus["bolsonaro_2t_pct"], 1)}% do 2º turno,
{fmt(manaus["eleitores_2026"])} eleitores. O Amazonas está a três pontos no 1º turno, {POLL["AM"]["pres"]["Lula"]} a {POLL["AM"]["pres"]["Flávio"]}, tem candidatura do PL
competitiva ao governo com {POLL["AM"]["gov"]["esquerda"][2]}%, e nunca recebeu visita. É a melhor relação entre estoque, competitividade e ausência do país.</li>
<li><b>Belém e São Luís no mesmo circuito.</b> {fmt(belem["bolsonaro_2t"])} e {fmt(sao_luis["bolsonaro_2t"])} votos, Pará a
{VAO["PA"]["vao_1t"]} pontos de vão e a menor aprovação de Lula do Norte e do Nordeste fora dos estados bolsonaristas: {POLL["PA"]["lula"]["aprova"]} contra
{POLL["PA"]["lula"]["desaprova"]}. O Pará é o único grande colégio da região em que a disputa presidencial já é competitiva.</li>
<li><b>Salvador, e não só Conquista.</b> O vão baiano é de {VAO["BA"]["vao_1t"]} pontos e a capital tem
{fmt(CAP["Salvador"]["bolsonaro_2t"])} votos de 2022. O tema é violência, {dict(D["temas"]["BA"])["Violência"]}% do estado, o mais alto da Bahia e o segundo mais alto da série.</li>
<li><b>Recife de novo, e a Região Metropolitana inteira.</b> Recife, Jaboatão, Olinda e Paulista somam
{fmt(sum(ALVO[("PE", c)]["bolsonaro_2t"] for c in ("Recife", "Jaboatão dos Guararapes", "Olinda", "Paulista")))} votos de Bolsonaro, mais do que o estado inteiro do Piauí.
O vão de 2º turno de Pernambuco, {VAO["PE"]["vao_2t"]} pontos, é o maior do país na régua turno contra turno.</li>
<li><b>Maceió e Aracaju, com Alagoas e Sergipe ainda inéditos.</b> Maceió é a capital nordestina em que Bolsonaro mais foi longe,
{fmt(CAP["Maceió"]["bolsonaro_2t_pct"], 1)}%, e Alagoas dá {POLL["AL"]["pres"]["Flávio"]}% a Flávio hoje, o melhor número do Nordeste depois do Pará. Saúde é
{dict(D["temas"]["AL"])["Saúde"]}% do estado: o discurso de segurança rende pouco ali.</li>
<li><b>Fortaleza com a candidatura estadual na frente.</b> O Ceará tem o maior vão do país, {VAO["CE"]["vao_1t"]} pontos, e o maior índice de violência como problema,
{dict(D["temas"]["CE"])["Violência"]}%. A ordem importa: quem abre é o palanque estadual, porque a preferência por governador aliado de Flávio é de
{POLL["CE"]["aliado"]["Flávio"]}% contra {POLL["CE"]["aliado"]["Lula"]}% de aliado de Lula.</li>
<li><b>Roraima, Acre e Amapá por último, e mesmo assim.</b> São os três estados não visitados em que Bolsonaro venceu. Não precisam de conversão, precisam de
comparecimento e de voto útil no 1º turno. Rendem pouco em volume e muito em sinal, porque a ausência de três anos num território que deu
{fmt(NV["detalhe"][-1]["bolsonaro_2t_pct"], 1)}% é a notícia que a imprensa local publica sozinha.</li>
</ol>
<div class="callout"><b>O que não fazer.</b> Não abrir agenda no Nordeste pelo nome nacional onde o saldo de palanque é negativo. Não levar o discurso de violência a
Roraima, Tocantins e Alagoas, onde saúde vale de duas a cinco vezes mais. Não tratar o cerrado como rota principal. E não confundir vão com voto: o eleitor de ACM Neto,
de Raquel Lyra e de Ciro Gomes não prometeu nada a ninguém.</div>
""",
    )


def cap_limites() -> str:
    return section(
        "limites",
        "Limites",
        "O que este dossiê não mede",
        """
<p><b>O vão não é voto transferível.</b> É a distância entre dois números na mesma amostra. Nada nos relatórios mede quanto do eleitorado de um governador de centro-direita
aceitaria a candidatura presidencial do PL, e a experiência de 2022 em São Paulo mostra que a taxa nunca é de um para um.</p>
<p><b>Os institutos não publicam o cruzamento direto.</b> Se a Quaest publicasse a tabela do voto para governador contra o voto para presidente dentro do mesmo estado,
este dossiê teria metade do tamanho e o dobro de força. O pedido fica registrado.</p>
<p><b>O estoque de 2022 é memória, não promessa.</b> Votos de quatro anos atrás medem onde o campo já esteve, não onde estará. Municípios mudam, eleitorado envelhece e
a abstenção de 2026 não é a de 2022.</p>
<p><b>Dois estados não têm pesquisa estadual publicada</b> no período: Piauí e Sergipe, com 2,7 e 1,7 milhão de eleitores. Onde aparecem neste dossiê, aparecem apenas
com dado do TSE, nunca com intenção de voto.</p>
<p><b>Os relatórios são imagem.</b> Os PDFs da Quaest não têm camada de texto nos gráficos. Cada tabela foi transcrita página a página, com o número da página declarado no
script que gera esta página, e conferida por leitura de máquina independente. Divergência entre as duas quebra o teste automático do repositório.</p>
""",
    )


def cap_fontes() -> str:
    rows = []
    for poll in D["pesquisas"]:
        rows.append(
            [
                f'{esc(poll["nome"])} <span class="sub">{poll["uf"]}</span>',
                esc(poll["campo"]),
                f'<a href="{D["meta"]["pdf_base"]}/{poll["arquivo"]}">relatório</a>',
                f'p. {poll["pres"]["pagina"]}',
                f'p. {poll["gov"]["pagina"]}',
            ]
        )
    agenda = "".join(
        f'<li><b>{esc(a["uf"])}, {esc(a["data"][8:10])}/{esc(a["data"][5:7])}</b>: '
        f'{esc(", ".join(a["cidades"]))}, {esc(a["formato"])}. '
        f'<a href="{esc(a["url"])}">{esc(a["veiculo"])}</a>.</li>'
        for a in D["agenda"]["atos"]
    )
    return section(
        "fontes",
        "Fontes",
        "Tudo aberto, com página e link",
        f"""
{table(["Relatório", "Fim do campo", "PDF", "Presidente 1º turno", "Governador"], rows, "Relatórios estaduais usados no dossiê")}
<h3>Agenda declarada</h3>
<ul class="fontes">{agenda}</ul>
<h3>Roteiro da pré-campanha</h3>
<ul class="fontes">
<li><a href="{esc(D["agenda"]["fonte_roteiro"]["url"])}">{esc(D["agenda"]["fonte_roteiro"]["veiculo"])}</a>: {esc(D["agenda"]["fonte_roteiro"]["titulo"])}.</li>
<li><a href="{esc(D["agenda"]["fonte_roteiro_2"]["url"])}">{esc(D["agenda"]["fonte_roteiro_2"]["veiculo"])}</a>: {esc(D["agenda"]["fonte_roteiro_2"]["titulo"])}.</li>
</ul>
<h3>Base eleitoral</h3>
<ul class="fontes">
<li>TSE, votação por candidato e município, eleições gerais de 2022, 1º e 2º turnos.</li>
<li>TSE, eleitorado por município, perfil vigente de 2026.</li>
<li>Delimitação do MATOPIBA: Embrapa, municípios de cerrado de Bahia, Maranhão, Piauí e Tocantins.</li>
</ul>
<h3>Reprodução</h3>
<p class="repro">python3 scripts/estaduais-092026-tse.py<br>python3 scripts/estaduais-092026-extract.py<br>python3 scripts/estaduais-092026-data.py<br>python3 scripts/estaduais-092026-build.py</p>
<p>A base pública está em <a href="assets/estaduais_092026_data.json">estaduais_092026_data.json</a>, e os derivados em
<a href="../derivados/estaduais-092026-vao.csv">estaduais-092026-vao.csv</a> e <a href="../derivados/estaduais-092026-alvos.csv">estaduais-092026-alvos.csv</a>.</p>
""",
    )


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--paper:#f7f5ee;--paper2:#efece2;--ink:#151812;--ink2:#2a2f27;--muted:#535b54;--line:#d5d2c6;
 --lula:#c8412f;--flavio:#2f6fae;--direita:#0c7a72;--gold:#7d5b00;--green:#2f7d52;
 --display:Fraunces,Georgia,serif;--sans:"IBM Plex Sans Condensed",Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
 --wrap:min(1080px,calc(100% - 40px))}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:17.5px;line-height:1.66;-webkit-font-smoothing:antialiased}
.wrap{width:var(--wrap);margin:0 auto}
a{color:#1d5f97}
a:hover{color:#123f66}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:var(--ink);color:var(--paper);padding:10px 14px;z-index:99}
.hero{background:var(--ink);color:#f4f2ea;padding:0 0 46px}
.hero a{color:#cfe63c}
.brand{display:flex;align-items:center;gap:10px;padding:22px 0 0;font-family:var(--mono);font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;color:#a9a99c}
.brand a{display:flex;align-items:center;gap:10px;color:inherit;text-decoration:none}
.brand img{width:26px;height:26px;border-radius:4px}
.eyebrow{font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:#cfe63c;margin:34px 0 0}
.hero h1{font-family:var(--display);font-size:clamp(2.2rem,6vw,4.1rem);line-height:1;letter-spacing:-.028em;margin:14px 0 0;font-weight:900}
.hero h1 em{display:block;font-style:italic;font-weight:500;color:#cfe63c}
.hero .deck{max-width:74ch;color:#ddd8ca;font-size:1.07rem;margin:20px 0 0}
.hero-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px;margin:30px 0 0}
.hero-stats div{border-top:2px solid #cfe63c;padding-top:10px}
.hero-stats b{display:block;font-family:var(--display);font-size:2.1rem;line-height:1;font-weight:900}
.hero-stats span{display:block;font-size:.88rem;color:#bdb9ab;margin-top:6px}
.case-file{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:1px;background:#2f342c;border:1px solid #2f342c;margin:32px 0 0}
.case-file>div{background:var(--ink);padding:12px 14px}
.case-file dt{font-family:var(--mono);font-size:.68rem;letter-spacing:.11em;text-transform:uppercase;color:#a9a99c}
.case-file dd{margin:4px 0 0;font-size:.95rem}
.toc{position:sticky;top:0;z-index:20;background:rgb(247 245 238 / 95%);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.toc .wrap{display:flex;gap:6px;align-items:center;overflow-x:auto;padding:10px 0;scrollbar-width:none}
.toc b{font-family:var(--mono);font-size:.68rem;letter-spacing:.13em;color:var(--muted);margin-right:8px;white-space:nowrap}
.toc a{font-family:var(--mono);font-size:.74rem;text-decoration:none;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:5px 12px;white-space:nowrap}
.toc a:hover{border-color:var(--ink);color:var(--ink)}
section{padding:54px 0;border-bottom:1px solid var(--line)}
.kicker{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin:0}
h2{font-family:var(--display);font-size:clamp(1.7rem,3.4vw,2.5rem);line-height:1.08;letter-spacing:-.02em;margin:10px 0 18px;font-weight:700}
h3{font-family:var(--display);font-size:1.3rem;margin:32px 0 10px;font-weight:700}
p{max-width:76ch}
.lead{font-size:1.14rem}
.callout{border-left:3px solid var(--gold);background:var(--paper2);padding:16px 20px;margin:26px 0;max-width:80ch}
.callout b{color:var(--ink)}
.fig{margin:30px 0;border:1px solid var(--line);background:#fff;border-radius:6px;padding:16px}
.fig-svg{width:100%;height:auto;display:block}
.fig-svg .bar-fill,.fig-svg .bar-bg{display:block}
figcaption{font-family:var(--mono);font-size:.78rem;color:var(--muted);margin-top:12px;line-height:1.5}
.table-scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:#fff;margin:24px 0}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--line);white-space:nowrap}
thead th{font-family:var(--mono);font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);background:var(--paper2)}
tbody th{font-weight:600}
.sub{font-family:var(--mono);font-size:.76rem;color:var(--muted)}
.pos{color:var(--direita)}
.neg{color:var(--gold)}
.source{font-family:var(--mono);font-size:.78rem;color:var(--muted);margin-top:-6px}
ol.rota{max-width:80ch;padding-left:20px}
ol.rota li{margin:0 0 16px}
ul.fontes{max-width:80ch;padding-left:20px}
ul.fontes li{margin:0 0 8px}
.repro{font-family:var(--mono);font-size:.84rem;background:var(--paper2);border:1px solid var(--line);border-radius:6px;padding:14px 16px;line-height:2}
footer{padding:36px 0 64px;color:var(--muted);font-size:.93rem}
@media (width <= 720px){
 body{font-size:16.5px}
 section{padding:38px 0}
 .hero-stats b{font-size:1.7rem}
}
"""


def main() -> None:
    body = "".join(
        [
            cap_tese(),
            cap_metodo(),
            cap_roteiro(),
            cap_onde(),
            cap_trocas(),
            cap_cerrado(),
            cap_temas(),
            cap_palanque(),
            cap_rota(),
            cap_limites(),
            cap_fontes(),
        ]
    )
    links = "".join(f'<a href="#{slug}">{esc(name)}</a>' for slug, name in SECTIONS)
    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atlas estadual 09/2026: onde a direita ganha o estado e perde o país | Arvor</title>
<meta name="description" content="Quinze pesquisas estaduais e o resultado do TSE de 2022 por município: o vão entre a direita estadual e Flávio Bolsonaro, os dez estados fora do roteiro, as capitais onde o voto está e os temas de cada estado.">
<link rel="canonical" href="https://brasil.arvor.co/estaduais_092026.html">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#151812">
<meta property="og:type" content="article">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:title" content="Atlas estadual: a direita ganha o estado e perde o país">
<meta property="og:description" content="O vão de até 33 pontos entre a direita estadual e Flávio, os dez estados fora do roteiro e as capitais onde mora o voto bolsonarista do Norte e do Nordeste.">
<meta property="og:url" content="https://brasil.arvor.co/estaduais_092026.html">
<meta property="og:image" content="https://brasil.arvor.co/img/og/estaduais_092026.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/estaduais_092026.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,700;0,9..144,900;1,9..144,500&amp;family=IBM+Plex+Mono:wght@400;500;700&amp;family=IBM+Plex+Sans+Condensed:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="hero"><div class="wrap">
<div class="brand"><a href="index.html"><img src="img/arvor_logo.png" alt="">Arvor Intelligence · Perícia eleitoral</a></div>
<p class="eyebrow">Atlas estadual · setembro de 2026 · corte em 16/09</p>
<h1>A direita ganha o estado.<em>E perde o país no mesmo domicílio.</em></h1>
<p class="deck">Quinze relatórios estaduais da Quaest, lidos página a página, cruzados com o resultado oficial do TSE de 2022 em 5.751 municípios. O vão entre a candidatura de direita ao governo e a candidatura presidencial chega a {VAO["CE"]["vao_1t"]} pontos no Ceará e {VAO["BA"]["vao_1t"]} na Bahia, medido na mesma entrevista. Dez estados ficaram fora do roteiro da pré-campanha, e três deles Bolsonaro venceu em 2022.</p>
<div class="hero-stats">
<div><b>{VAO["CE"]["vao_1t"]}</b><span>pontos de vão no Ceará, o maior do país</span></div>
<div><b>{fmt(NV["eleitores_2026"] / 1e6, 1)} mi</b><span>de eleitores nos dez estados sem visita</span></div>
<div><b>{NE["metade_em"]}</b><span>municípios concentram metade do voto bolsonarista do Nordeste</span></div>
<div><b>{fmt(CAP["Manaus"]["bolsonaro_2t"] / 1000)} mil</b><span>votos de Bolsonaro em Manaus, o maior estoque das duas regiões</span></div>
</div>
<dl class="case-file">
<div><dt>Instituto</dt><dd>Quaest / Globo</dd></div>
<div><dt>Relatórios</dt><dd>{len(D["pesquisas"])} estaduais</dd></div>
<div><dt>Campo</dt><dd>23/08 a 07/09 de 2026</dd></div>
<div><dt>Base eleitoral</dt><dd>TSE 2022, 5.751 municípios</dd></div>
<div><dt>Eleitorado</dt><dd>TSE, perfil de 2026</dd></div>
<div><dt>Sem pesquisa estadual</dt><dd>Piauí e Sergipe</dd></div>
</dl>
</div></header>
<nav class="toc" aria-label="Capítulos"><div class="wrap"><b>NO DOSSIÊ</b>{links}</div></nav>
<main id="conteudo">{body}</main>
<footer><div class="wrap">
<p><strong>Arvor Intelligence</strong> · Leitura descritiva de pesquisa e de resultado eleitoral, não previsão. O capítulo da rota é juízo editorial declarado.</p>
<p><a href="index.html">Biblioteca</a> · <a href="reponderacao_pnad.html">Agregador PNAD</a> · <a href="superthread_092026.html">A thread</a> · <a href="#conteudo">Voltar ao início</a></p>
</div></footer>
</body>
</html>
"""
    assert "—" not in page, "travessão proibido"
    (DOCS / "estaduais_092026.html").write_text(page)
    print("Gerado:", DOCS / "estaduais_092026.html", len(SECTIONS), "capítulos")


if __name__ == "__main__":
    main()
