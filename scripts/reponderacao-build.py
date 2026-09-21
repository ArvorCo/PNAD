#!/usr/bin/env python3
"""Gera a página de reponderação; --skip-home preserva a capa e seus assets."""

from __future__ import annotations

import argparse
import csv
import importlib
import json
from html import escape as esc

from reponderacao_vista.charts import (
    gap_svg,
    instituto_svg,
    renda_svg,
    serie_svg,
    slope_svg,
)
from reponderacao_vista.context import (
    AGG,
    ASSETS,
    BENCH,
    CEN,
    CENARIOS,
    HOME_SVG,
    INDEX,
    INSTITUTOS,
    MESES,
    METODO,
    PAGE,
    PAGINAS,
    PAR,
    PESQUISAS,
    RECENTES,
    SHEET,
    TABLE_CSV,
    TIP_SCRIPT,
    TIP_SHEET,
    TURNOS,
    D,
    ajustado,
    coverage_html,
    curto,
    frase,
    gap,
    groups_view,
    longo,
    periodo,
    plural,
    rotulo,
    sinal,
)
from reponderacao_vista.markers import (
    TIPS,
    _tip_id,
)
from reponderacao_vista.style import (
    CSS,
    SCRIPT,
    TIP_CSS,
    TIP_JS,
)
from svgkit import br, inject


def figura(
    ident: str, kicker: str, titulo: str, svg: str, nota: str, dica: bool = True
) -> str:
    aviso = (
        '<p class="dica">Passe o ponteiro sobre uma onda para abrir a ficha</p>'
        if dica
        else ""
    )
    return (
        f'<figure class="chart-shell reveal"><p class="kicker">{esc(kicker)}</p>'
        f"<h3>{esc(titulo)}</h3>{aviso}"
        f'<div class="fig wide" id="{ident}" tabindex="0" role="region"'
        f' aria-label="{esc(titulo, quote=True)}">{svg}</div>'
        f'<figcaption class="note">{nota}</figcaption></figure>'
    )


def tabela(cabeca: list[str], linhas: list[list[str]], cls: str = "") -> str:
    corpo = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas
    )
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela: {esc(cabeca[0])}">'
        f'<table class="{cls}"><thead><tr>'
        + "".join(f'<th scope="col">{esc(c)}</th>' for c in cabeca)
        + f"</tr></thead><tbody>{corpo}</tbody></table></div>"
    )


def capitulo(num: int, ident: str, titulo: str, chamada: str, corpo: str) -> str:
    return (
        f'<section id="{ident}" class="chapter"><div class="wrap">'
        f'<header class="chapter-head reveal"><span class="number">{num:02}</span>'
        f'<div><h2>{titulo}</h2><p class="lead">{chamada}</p></div></header>'
        f"{corpo}</div></section>"
    )


def selo(kind: str, texto: str) -> str:
    return f'<span class="stamp {kind}">{esc(texto)}</span>'


def placar(turno: str) -> str:
    ultimo = AGG["ultimo"][turno]
    if not ultimo["institutos"]:
        return ""
    simples, kernel = ultimo["media_simples"], ultimo["kernel"]
    blocos = []
    for nome, dados in (("Média simples", simples), ("Média Arvor", kernel)):
        for tipo, marca in (("publicado", "fato"), ("ajustado", "inferencia")):
            v = dados[tipo]
            blocos.append(
                f"<div>{selo(marca, 'publicado' if tipo == 'publicado' else 'reponderado')}"
                f"<span>{esc(nome)}</span>"
                f'<b><em class="lula">{br(v["lula"], 1)}</em> × '
                f'<em class="flavio">{br(v["flavio"], 1)}</em></b>'
                f"<small>diferença {sinal(gap(v), 1)} ponto"
                f"{'s' if abs(round(gap(v), 1)) != 1 else ''}</small></div>"
            )
    lista = ", ".join(ultimo["institutos"])
    return (
        f'<div class="ledger reveal">{"".join(blocos)}</div>'
        f'<p class="note">Média simples: última onda de cada instituto, peso igual. '
        f"Média Arvor: {esc(AGG['metodo']['kernel'])}. "
        f"Institutos na conta: {esc(lista)}. Cenário: {esc(CENARIOS[CEN])}.</p>"
    )


def chip_prova(pesquisa: dict) -> str:
    partes = []
    for turno, t in pesquisa["turnos"].items():
        ok = t["residuo_max"] <= 1.0
        partes.append(
            f'<span class="proof {"ok" if ok else "warn"}">prova de leitura '
            f"{TURNOS[turno]}: resíduo {br(t['residuo_max'], 2)} ponto"
            f"{'s' if round(t['residuo_max'], 2) != 1 else ''}</span>"
        )
    return "".join(partes)


def paginas_fonte(fonte: dict) -> str:
    itens = fonte.get("paginas") or {}
    if not itens:
        return fonte.get("localizador", "páginas não declaradas")
    return ", ".join(
        f"p. {valor} ({PAGINAS.get(chave, chave.replace('_', ' '))})"
        for chave, valor in itens.items()
    )


def cartao(pesquisa: dict) -> str:
    renda = pesquisa["renda"]
    alvo = renda["pnad_pct"][CEN]
    desvio = pesquisa["desvio_ate_primeira_faixa"]
    dossie = pesquisa.get("dossie")
    link_dossie = (
        f' · <a href="{esc(dossie, quote=True)}">dossiê completo</a>' if dossie else ""
    )
    url = (pesquisa["fonte"] or {}).get("url")
    rotulo_fonte = pesquisa["fonte"].get("rotulo", "PDF do relatório")
    link_pdf = (
        f' · <a href="{esc(url, quote=True)}">{esc(rotulo_fonte)}</a>' if url else ""
    )
    link_pdf += "".join(
        f' · <a href="{esc(s["url"], quote=True)}">{esc(s["rotulo"])}</a>'
        for s in pesquisa["fonte"].get("complementos", [])
    )
    fonte_nota = pesquisa["fonte"].get("nota", "")
    aviso_fonte = (
        f'<p class="note"><b>{esc(pesquisa["fonte"].get("status", ""))}</b> {esc(fonte_nota)}</p>'
        if fonte_nota
        else ""
    )
    perfil_verbo = (
        "O registro prevê"
        if renda.get("perfil_tipo") == "cota_registrada"
        else (
            "A calibração tem como alvo"
            if renda.get("perfil_tipo") == "alvo_de_calibracao"
            else "A amostra declara"
        )
    )

    cenarios = []
    for turno, t in pesquisa["turnos"].items():
        for nome, rotulo_cenario in CENARIOS.items():
            valores = t["cenarios"][nome]["ajustado"]
            cenarios.append(
                [
                    esc(TURNOS[turno]),
                    esc(rotulo_cenario),
                    br(valores["lula"], 1),
                    br(valores["flavio"], 1),
                    sinal(gap(valores), 1),
                    "principal" if nome == CEN else "robustez",
                ]
            )

    extras = ""
    t1 = pesquisa["turnos"].get("1t")
    if t1:
        outras = [c for c in t1["opcoes"] if c not in PAR]
        if outras:
            linhas = [
                [
                    esc(rotulo(c)),
                    br(t1["publicado"][c], 1),
                    br(ajustado(t1)[c], 1),
                    sinal(ajustado(t1)[c] - t1["publicado"][c], 1),
                ]
                for c in outras
            ]
            extras = "<h4>Demais opções do 1º turno</h4>" + tabela(
                ["Opção", "Publicado", "Reponderado", "Efeito"], linhas
            )

    return (
        f'<article class="poll reveal" id="pesquisa-{esc(pesquisa["id"], quote=True)}">'
        f'<header class="poll-head"><div><h3>{esc(pesquisa["instituto"])}, '
        f"campo de {esc(periodo(pesquisa['campo']))}</h3>"
        f'<p class="note">{esc(pesquisa["registro_tse"])} · contratante {esc(pesquisa["contratante"])} · '
        f"n = {br(pesquisa['n'], 0)} · {esc(pesquisa['metodo'])} · divulgação em "
        f"{esc(longo(pesquisa['divulgacao']))}{link_dossie}{link_pdf}</p>{aviso_fonte}"
        f"{groups_view.selection_note(pesquisa)}"
        f'<p class="note">Fonte: <code>{esc(pesquisa["fonte"].get("arquivo") or pesquisa["fonte"].get("pdf") or "sem arquivo arquivado")}</code>, '
        f"{esc(paginas_fonte(pesquisa['fonte']))}.</p></div>"
        f'<div class="proofs">{chip_prova(pesquisa)}</div></header>'
        f'<div class="split">'
        f'<div class="chart-shell"><p class="kicker">Composição de renda</p>'
        f"<h4>{perfil_verbo} {br(renda['amostra_pct'][0], 1)}% na faixa mais baixa. "
        f"A PNAD mede {br(alvo[0], 1)}%.</h4>"
        '<p class="dica">Passe o ponteiro sobre uma faixa</p>'
        f'<div class="fig" tabindex="0" role="region" aria-label="Composição de renda">'
        f"{renda_svg(pesquisa)}</div>"
        f'<p class="note">Desvio na primeira faixa: {br(desvio, 1)} pontos. '
        f"{esc(renda['nota'])}</p></div>"
        f'<div class="chart-shell"><p class="kicker">Placar sob a régua</p>'
        f"<h4>Só a margem de renda muda.</h4>"
        f'<div class="fig" tabindex="0" role="region" aria-label="Placar sob a régua">'
        f"{slope_svg(pesquisa) if pesquisa['turnos'] else '<p>Sem cenário elegível nesta onda. O primeiro turno com Marçal permanece apenas no arquivo histórico.</p>'}</div>"
        f'<p class="note">Ponto vazado é o publicado pelo instituto. Ponto cheio é a '
        f"reponderação Arvor, que é inferência.</p></div></div>"
        + tabela(
            ["Turno", "Cenário da PNAD", "Lula", "Flávio", "Diferença", "Uso"],
            cenarios,
            cls="scenarios",
        )
        + extras
        + "</article>"
    )


def ch_segundo_turno() -> str:
    ultimo = AGG["ultimo"]["2t"]
    kernel = ultimo["kernel"]
    corpo = (
        figura(
            "segundo-turno-chart",
            "Série do 2º turno",
            "O que os institutos publicaram e o que a mesma amostra devolve sob a renda do IBGE.",
            serie_svg("s2t", "2t"),
            "Cada onda entra pela data final do campo. A linha fina e tracejada é a média "
            "das pesquisas como foram publicadas. A linha cheia é a mesma média depois de "
            "trocar uma margem, a de renda, pela distribuição da PNAD Contínua anual de 2025. "
            "A troca é nossa, e por isso a linha cheia é inferência declarada.",
        )
        + placar("2t")
        + '<p class="plain reveal">Publicado, a média Arvor marca Lula '
        + br(kernel["publicado"]["lula"], 1)
        + " e Flávio "
        + br(kernel["publicado"]["flavio"], 1)
        + ". Sob a régua oficial de renda, marca Lula "
        + br(kernel["ajustado"]["lula"], 1)
        + " e Flávio "
        + br(kernel["ajustado"]["flavio"], 1)
        + ". A diferença sai de "
        + sinal(gap(kernel["publicado"]), 1)
        + " para "
        + sinal(gap(kernel["ajustado"]), 1)
        + " ponto para Lula.</p>"
    )
    parciais = [
        p
        for p in PESQUISAS
        if "2t" in p["turnos"] and p["fonte"].get("tipo") == "materia"
    ]
    if parciais:
        corpo += (
            '<p class="note">A série inclui fonte parcial: '
            + "; ".join(
                f'<a href="#pesquisa-{esc(p["id"])}">{esc(p["instituto"])} ({longo(p["divulgacao"])})</a>'
                for p in parciais
            )
            + ". Os votos por renda vêm da divulgação e a reponderação usa as cotas registradas, condicionada à confirmação do perfil ponderado final.</p>"
        )
    return capitulo(
        1,
        "segundo-turno",
        "O 2º turno sob a régua oficial",
        "Uma linha por candidato, publicada e reponderada, com todos os pontos de campo à vista.",
        corpo,
    )


def ch_primeiro_turno() -> str:
    polls = [p for p in PESQUISAS if "1t" in p["turnos"]]
    if not polls:
        return capitulo(
            2,
            "primeiro-turno",
            "O 1º turno",
            "Nenhuma onda auditada publicou cruzamento de renda no 1º turno até aqui.",
            '<p class="plain reveal">Assim que uma pesquisa publicar a tabela de renda do '
            "1º turno, ela entra aqui pelo mesmo caminho.</p>",
        )
    ultimas = {}
    for p in polls:
        ultimas[p["instituto"]] = p
    linhas = []
    for p in ultimas.values():
        t = p["turnos"]["1t"]
        for chave in t["opcoes"]:
            if chave in PAR:
                continue
            linhas.append(
                [
                    esc(p["instituto"]),
                    esc(curto(p["campo"]["fim"])),
                    esc(rotulo(chave)),
                    br(t["publicado"][chave], 1),
                    br(ajustado(t)[chave], 1),
                    sinal(ajustado(t)[chave] - t["publicado"][chave], 1),
                ]
            )
    corpo = (
        groups_view.scenario_summary(D, tabela)
        + figura(
            "primeiro-turno-chart",
            "Série do 1º turno",
            "Lula, Flávio e dois grupos de outras candidaturas, publicado contra reponderado.",
            serie_svg("s1t", "1t"),
            "Lula e Flávio usam os cenários sem Marçal com cruzamento de renda. "
            "Os grupos usam apenas ondas que permitem separar as candidaturas por renda, "
            "com cobertura e datas informadas abaixo. Cinza: centro-direita; preto: esquerda + nanicos. "
            "Tracejado é publicado; contínuo é reponderado. "
            "No celular, deslize o gráfico para ver as datas recentes e os grupos.",
        )
        + placar("1t")
        + groups_view.group_summary(D, tabela, br)
        + '<h3 class="reveal">As demais candidaturas sob a mesma troca</h3>'
        + tabela(
            ["Instituto", "Campo", "Opção", "Publicado", "Reponderado", "Efeito"],
            linhas,
        )
        + '<p class="note">Última onda de cada instituto. O efeito é a diferença entre o '
        "reponderado e o publicado, em pontos. Todas as ondas estão no CSV e no JSON. "
        "Quem não declarou renda fica fora da conta e entra pelo topline publicado.</p>"
    )
    return capitulo(
        2,
        "primeiro-turno",
        "O 1º turno",
        "A mesma conta aplicada à primeira volta, com todas as candidaturas medidas.",
        corpo,
    )


def ch_manchete() -> str:
    polls = [p for p in PESQUISAS if "2t" in p["turnos"]]
    viradas = sum(
        1
        for p in polls
        if p["turnos"]["2t"]["gap_publicado"] > 0 >= p["turnos"]["2t"]["gap_ajustado"]
    )
    dentro = sum(
        1
        for p in polls
        if abs(p["turnos"]["2t"]["gap_publicado"])
        <= p["turnos"]["2t"]["margem_diferenca_95"]
    )
    corpo = (
        figura(
            "manchete-chart",
            "Manchete contra régua",
            "A diferença publicada, a margem de 95% dessa diferença e a diferença reponderada.",
            gap_svg("gap2t", "2t"),
            "A barra cheia é a diferença que o instituto publicou, com o bigode marcando o "
            "intervalo de 95% da diferença sob amostragem aleatória simples. A barra hachurada "
            "é a mesma diferença depois da troca da margem de renda, e é inferência nossa. "
            "O registro no TSE de cada onda está na tabela de fontes.",
        )
        + '<div class="metrics three reveal">'
        f"<article><strong>{dentro} de {len(polls)}</strong>"
        "<p>ondas em que a diferença publicada cabe dentro da própria margem de 95%. "
        "Nelas a palavra <em>lidera</em> afirma mais do que a amostra sustenta.</p></article>"
        f"<article><strong>{viradas} de {len(polls)}</strong>"
        "<p>ondas em que a vantagem publicada não sobrevive à troca da margem de renda "
        "pela distribuição oficial.</p></article>"
        f"<article><strong>{br(BENCH['totais_milhoes'][CEN], 1)} mi</strong>"
        "<p>pessoas de 16 anos ou mais representadas no histograma da PNAD que serve "
        "de régua.</p></article></div>"
        '<div class="callout reveal"><p>Uma manchete que diz <em>lidera</em> precisa passar '
        "em dois testes independentes. O primeiro é de amostragem: o intervalo de 95% da "
        "diferença não pode conter o zero. O segundo é de composição: o sinal precisa "
        "sobreviver à troca da margem dominante pela régua oficial. Os dois testes são "
        "diferentes, e uma manchete pode falhar em um e passar no outro.</p></div>"
    )
    return capitulo(
        3,
        "manchete",
        "A manchete contra a régua",
        "Diferença publicada, incerteza da diferença e diferença reponderada, na mesma linha.",
        corpo,
    )


def _painel_instituto(nome: str, turno: str) -> str:
    if nome == "Palver":
        historico = importlib.import_module("reponderacao-palver-view").history_polls()
        return (
            f'<article class="panel reveal" data-instituto="Palver" data-turno="{turno}">'
            f"<h3>Palver <small>{TURNOS[turno]}</small></h3>"
            f'<div class="fig">{instituto_svg(nome, turno, historico)}</div>'
            '<p class="note"><b>3 ondas · 4 versões.</b> A onda 2 original (v1) foi substituída '
            "pela revisada (v2). Todos os pontos estão visíveis; a v1 fica fora das médias. "
            + (
                "Os dois cenários de 07/09 incluem Marçal e também ficam fora da média do 1º turno. "
                if turno == "1t"
                else ""
            )
            + "Vazado é publicado, cheio é reponderado. "
            '<a href="#palver-pesos">Fontes, valores e critérios</a>.</p></article>'
        )
    ondas = sum(1 for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"])
    total = sum(1 for p in PESQUISAS if p["instituto"] == nome)
    if turno == "2t" and ondas < total:
        cobertura = f"{ondas} de {total} ondas cruzam o 2º turno por renda"
    elif turno == "1t" and not any(
        "2t" in p["turnos"] for p in PESQUISAS if p["instituto"] == nome
    ):
        cobertura = f"{plural(ondas, 'onda', 'ondas')}; o instituto não cruza o 2º turno por renda"
    else:
        cobertura = plural(ondas, "onda auditada", "ondas auditadas")
    return (
        f'<article class="panel reveal"><h3>{esc(nome)} <small>{TURNOS[turno]}</small></h3>'
        f'<div class="fig">{instituto_svg(nome, turno)}</div>'
        f'<p class="note">{cobertura}. Vazado é publicado, cheio é reponderado.</p></article>'
    )


def ch_institutos() -> str:
    so_1t = [
        nome
        for nome in INSTITUTOS
        if not any(p["instituto"] == nome and "2t" in p["turnos"] for p in PESQUISAS)
    ]
    paineis = "".join(
        _painel_instituto(nome, turno)
        for nome in INSTITUTOS
        for turno in ("2t", "1t")
        if any(p["instituto"] == nome and turno in p["turnos"] for p in PESQUISAS)
    )
    return capitulo(
        4,
        "institutos",
        "Instituto por instituto",
        "O mesmo desenho repetido em painéis pequenos, para comparar a distância entre a "
        "publicação e a régua dentro de cada casa.",
        f'<div class="grid-3">{paineis}</div>'
        '<p class="note">Cada instituto recebe um painel por turno que cruza por renda: '
        f"quem só publica o 1º turno por faixa de renda ({esc(', '.join(so_1t))}) "
        "aparece só com ele. Painéis com uma só onda mostram os pontos sem linha: com uma "
        "medida não há série. A escala vertical é própria de cada painel.</p>",
    )


def ch_pesquisas() -> str:
    return capitulo(
        5,
        "pesquisas",
        "Pesquisa por pesquisa",
        "Cada onda com a ficha do documento, a composição de renda, o efeito da troca e a "
        "prova de que a leitura do relatório está certa.",
        "".join(cartao(p) for p in RECENTES),
    )


def ch_metodo() -> str:
    limites = "".join(f"<li>{esc(frase(item))}</li>" for item in METODO["limites"])
    return capitulo(
        6,
        "metodo",
        "Como a conta é feita",
        "Uma margem trocada, uma régua só, e a prova de leitura antes de qualquer número derivado.",
        '<div class="split">'
        "<article><h3>A fórmula</h3>"
        f'<p class="formula">{esc(METODO["formula"])}</p>'
        "<p>O recomposto é o placar refeito com as bases de renda do próprio instituto. "
        "Se ele não devolve o placar publicado, a leitura do relatório está errada e nada "
        "derivado dela pode ser publicado. O contrafactual é o mesmo cruzamento com os "
        "pesos da PNAD no lugar dos pesos da amostra.</p>"
        f"<p>{esc(frase(METODO['margem_unica']))}</p></article>"
        "<article><h3>A régua</h3>"
        f"<p>{esc(BENCH['benchmark'])}, variável de rendimento domiciliar, "
        f"peso <code>{esc(BENCH['weight'])}</code>, pessoas de "
        f"{BENCH['min_age']} anos ou mais, "
        f"{br(BENCH['rows_read'], 0)} registros lidos.</p>"
        f"<p>Os cortes do cartão de renda de cada pesquisa são convertidos para reais de "
        f"{MESES[int(BENCH['price_month'][4:]) - 1]}. de {BENCH['price_month'][:4]} pelo IPCA, "
        "usando o salário mínimo do ano impresso no próprio cartão. Sem isso, cartão e cota "
        "ficam em réguas de anos diferentes.</p>"
        f"<p>Cenário principal: {esc(CENARIOS[CEN])}. Os outros dois cenários aparecem em "
        "cada ficha como teste de robustez.</p></article></div>"
        '<div class="split">'
        "<article><h3>As médias</h3>"
        f"<p>{esc(frase(AGG['metodo']['kernel']))} A meia-vida é de "
        f"{br(AGG['metodo']['meia_vida_dias'], 0)} dias sobre a data final do campo, "
        "de modo que uma onda de um mês atrás pesa cerca de um quarto de uma onda "
        "desta semana.</p>"
        f"<p>{esc(frase(AGG['metodo']['media_simples']))} As duas médias aparecem lado a lado "
        "porque respondem a perguntas diferentes: a simples mostra a fotografia mais "
        "recente de cada casa, a ponderada no tempo mostra a tendência.</p></article>"
        "<article><h3>Os limites</h3>"
        f'<ol class="method-list">{limites}</ol></article></div>'
        '<div class="callout reveal"><h3>Como acrescentar uma pesquisa</h3>'
        "<p>Um arquivo JSON por onda em <code>analysis/reponderacao/pesquisas/</code>, com o "
        "perfil de renda da amostra, o cruzamento do voto por faixa e o placar publicado, "
        "cada bloco com a página do relatório ao lado. Depois:</p>"
        "<pre><code>python3 scripts/reponderacao-pnad.py calcular\n"
        "python3 scripts/reponderacao-build.py</code></pre>"
        "<p>O primeiro comando refaz a conta e reescreve "
        "<code>docs/assets/reponderacao_pnad.json</code>. O segundo regenera esta página "
        "inteira, o CSV e o gráfico da capa. Nenhum número desta página é digitado à mão.</p>"
        "</div>",
    )


def ch_fontes() -> str:
    linhas = [
        [
            esc(p["instituto"]),
            esc(periodo(p["campo"])),
            esc(p["registro_tse"]),
            br(p["n"], 0),
            f"<code>{esc(p['fonte'].get('arquivo') or p['fonte'].get('pdf') or 'sem arquivo arquivado')}</code>",
            esc(paginas_fonte(p["fonte"])),
        ]
        for p in RECENTES
    ]
    return capitulo(
        7,
        "fontes",
        "Fontes e dados abertos",
        "Cada número desta página combina uma divulgação identificada pelo registro no TSE e um microdado "
        "público do IBGE.",
        tabela(
            ["Instituto", "Campo", "Registro TSE", "n", "Arquivo", "Localização"],
            linhas,
        )
        + '<div class="downloads reveal">'
        '<a class="download" href="assets/reponderacao_pnad.json"><b>JSON completo</b>'
        "<span>toda a conta, cenário por cenário, onda por onda</span></a>"
        '<a class="download" href="assets/reponderacao_pnad.csv"><b>CSV do agregador</b>'
        "<span>uma linha por pesquisa e turno, publicado e reponderado</span></a>"
        '<a class="download" href="pnad.html"><b>A PNAD por dentro</b>'
        "<span>de onde vem a distribuição de renda usada como régua</span></a></div>"
        f'<p class="note">Régua: {esc(BENCH["benchmark"])}, arquivo '
        f"<code>{esc(BENCH['source'])}</code>. Preços de "
        f"{MESES[int(BENCH['price_month'][4:]) - 1]}. de {BENCH['price_month'][:4]}. "
        f"Conta gerada em {esc(longo(D['gerado_em'][:10]))}, referência de "
        f"{esc(longo(D['referencia']))}.</p>",
    )


def head() -> str:
    ultimo = AGG["ultimo"]["2t"]["kernel"]
    titulo = "Agregador Arvor: a corrida sob a régua oficial de renda"
    descricao = (
        f"Toda pesquisa nacional reponderada pela distribuição de renda da PNAD Contínua "
        f"anual de 2025 do IBGE. Publicada, a média marca Lula {br(ultimo['publicado']['lula'], 1)} "
        f"e Flávio {br(ultimo['publicado']['flavio'], 1)} no 2º turno. Sob a régua oficial, "
        f"Lula {br(ultimo['ajustado']['lula'], 1)} e Flávio {br(ultimo['ajustado']['flavio'], 1)}."
    )
    og = "https://brasil.arvor.co/img/og/reponderacao_pnad.png"
    alt_card = (
        f"Agregador Arvor: {len(PESQUISAS)} ondas de {len(INSTITUTOS)} institutos "
        "reponderadas pela renda da PNAD, com uma margem trocada e o resto como "
        "o instituto ponderou."
    )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<script>document.documentElement.classList.add('js')</script>"
        f"<title>{esc(titulo)} · Arvor</title>"
        f'<meta name="description" content="{esc(descricao, quote=True)}">'
        '<link rel="canonical" href="https://brasil.arvor.co/reponderacao_pnad.html">'
        '<link rel="icon" href="favicon.ico" sizes="any">'
        '<link rel="icon" href="img/favicon.svg" type="image/svg+xml">'
        '<link rel="apple-touch-icon" href="img/favicon-180.png">'
        '<meta name="theme-color" content="#192e2b">'
        '<meta property="og:type" content="article">'
        '<meta property="og:locale" content="pt_BR">'
        '<meta property="og:site_name" content="Arvor Intelligence">'
        f'<meta property="og:title" content="{esc(titulo, quote=True)}">'
        f'<meta property="og:description" content="{esc(descricao, quote=True)}">'
        '<meta property="og:url" content="https://brasil.arvor.co/reponderacao_pnad.html">'
        f'<meta property="og:image" content="{og}">'
        f'<meta property="og:image:alt" content="{esc(alt_card, quote=True)}">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{og}">'
        f'<meta name="twitter:image:alt" content="{esc(alt_card, quote=True)}">'
        f'<meta name="twitter:title" content="{esc(titulo, quote=True)}">'
        f'<meta name="twitter:description" content="{esc(descricao, quote=True)}">'
        '<link rel="stylesheet" href="assets/reponderacao_pnad.css"><link rel="stylesheet" href="assets/reponderacao_tip.css"><link rel="stylesheet" href="assets/reponderacao_metodologias.css">'
        "</head>"
    )


def hero() -> str:
    ultimo = AGG["ultimo"]["2t"]["kernel"]
    dif_pub, dif_adj = gap(ultimo["publicado"]), gap(ultimo["ajustado"])
    ondas = len(PESQUISAS)
    return (
        '<section class="hero"><div class="wrap">'
        f'<p class="eyebrow">Agregador Arvor · atualizado em {esc(longo(D["referencia"]))} · '
        "sensibilidade sob régua comum</p>"
        "<h1>A corrida sob<br>a régua <em>oficial.</em></h1>"
        '<div class="hero-bottom">'
        "<p>Todo instituto declara uma distribuição de renda para a amostra. O IBGE mede "
        "outra. Este agregador troca só essa margem, mantém tudo o que o instituto ponderou "
        "e mostra o placar dos dois jeitos, onda por onda.</p>"
        f"<div><strong>{ondas}</strong><span>ondas auditadas<br>com cruzamento de renda</span></div>"
        f"<div><strong>{sinal(dif_pub, 1)}</strong><span>diferença publicada<br>"
        "na média Arvor do 2º turno</span></div>"
        f"<div><strong>{sinal(dif_adj, 1)}</strong><span>diferença reponderada<br>"
        "pela renda da PNAD</span></div></div>"
        f'<p class="note">Régua: {esc(BENCH["benchmark"])}, pessoas de {BENCH["min_age"]} anos '
        f"ou mais, preços de {MESES[int(BENCH['price_month'][4:]) - 1]}. de "
        f"{BENCH['price_month'][:4]}. Diferença positiva favorece Lula. A reponderação é "
        "inferência declarada, não resultado de eleição.</p></div></section>"
    )


def toc() -> str:
    itens = [
        ("atualizacao", "Atualização"),
        ("segundo-turno", "2º turno"),
        ("primeiro-turno", "1º turno"),
        ("palver-pesos", "Palver e pesos"),
        ("manchete", "Manchete"),
        ("institutos", "Institutos"),
        ("comparar-metodos", "Comparar métodos"),
        ("pesquisas", "Pesquisas"),
        ("metodo", "Método"),
        ("fontes", "Fontes"),
    ]
    return (
        '<nav class="toc" aria-label="Seções">'
        + "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in itens)
        + "</nav>"
    )


def bloco_tips(chaves: list[str] | None = None) -> str:
    """Fichas dos alvos embutidas na própria página, sem depender de rede."""
    dados = TIPS if chaves is None else {k: TIPS[k] for k in chaves if k in TIPS}
    if not dados:
        return ""
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    seguro = texto.replace("</", "<\\/")
    return f'<script type="application/json" class="tips">{seguro}</script>'


def build_html() -> str:
    corpo = "".join(
        [
            coverage_html(D, tabela),
            ch_segundo_turno(),
            ch_primeiro_turno(),
            importlib.import_module("reponderacao-palver-view").audit_html(D, tabela),
            ch_manchete(),
            ch_institutos(),
            importlib.import_module("reponderacao-metodos").section_html(),
            ch_pesquisas(),
            ch_metodo(),
            ch_fontes(),
        ]
    )
    return (
        head() + '<body><a class="skip" href="#conteudo">Pular para o conteúdo</a>'
        '<header class="masthead"><a href="index.html">ARVOR <span>Intelligence</span></a>'
        "<span>Agregador de pesquisas</span></header>"
        '<main id="conteudo">'
        + hero()
        + toc()
        + corpo
        + '</main><footer class="wrap footer"><b>ARVOR Intelligence</b>'
        f"<span>Agregador de pesquisas reponderadas · referência de "
        f"{esc(longo(D['referencia']))}</span>"
        '<span><a href="index.html">Biblioteca</a> · <a href="pnad.html">A PNAD por dentro</a>'
        " · uso livre com crédito e link</span></footer>"
        + bloco_tips()
        + f"<script>{SCRIPT}</script>"
        '<script src="assets/reponderacao_tip.js" defer></script><script src="assets/reponderacao_metodologias.js" defer></script></body></html>'
    )


def placar_home() -> str:
    """Placar compacto da capa, com a mesma convenção de fato e inferência."""
    kernel = AGG["ultimo"]["2t"]["kernel"]
    pub, adj = kernel["publicado"], kernel["ajustado"]
    celulas = [
        (
            f"{br(pub['lula'], 1)} × {br(pub['flavio'], 1)}",
            "Média Arvor publicada, Lula × Flávio, 2º turno",
        ),
        (
            f"{br(adj['lula'], 1)} × {br(adj['flavio'], 1)}",
            "A mesma média sob a renda medida pela PNAD",
        ),
        (sinal(gap(pub), 1), "Diferença publicada, em pontos"),
        (sinal(gap(adj), 1), "Diferença sob a régua oficial"),
    ]
    return "".join(
        f"<div><b>{esc(valor)}</b><span>{esc(texto)}</span></div>"
        for valor, texto in celulas
    )


def write_csv() -> None:
    cabeca = [
        "id",
        "instituto",
        "contratante",
        "registro_tse",
        "campo_inicio",
        "campo_fim",
        "divulgacao",
        "n",
        "turno",
        "cenario",
        "lula_publicado",
        "lula_reponderado",
        "flavio_publicado",
        "flavio_reponderado",
        "gap_publicado",
        "gap_reponderado",
        "margem_diferenca_95",
        "residuo_max",
        "desvio_ate_primeira_faixa",
        "outras_opcoes_publicado",
        "outras_opcoes_reponderado",
    ]
    linhas = []
    for p in PESQUISAS:
        for turno, t in p["turnos"].items():
            adj = ajustado(t)
            outras = [c for c in t["opcoes"] if c not in PAR]
            linhas.append(
                [
                    p["id"],
                    p["instituto"],
                    p["contratante"],
                    p["registro_tse"],
                    p["campo"]["inicio"],
                    p["campo"]["fim"],
                    p["divulgacao"],
                    p["n"],
                    turno,
                    CEN,
                    round(t["publicado"]["lula"], 3),
                    round(adj["lula"], 3),
                    round(t["publicado"]["flavio"], 3),
                    round(adj["flavio"], 3),
                    round(t["gap_publicado"], 3),
                    round(t["gap_ajustado"], 3),
                    round(t["margem_diferenca_95"], 3),
                    round(t["residuo_max"], 3),
                    round(p["desvio_ate_primeira_faixa"], 3),
                    ";".join(f"{c}={round(t['publicado'][c], 3)}" for c in outras),
                    ";".join(f"{c}={round(adj[c], 3)}" for c in outras),
                ]
            )
    with TABLE_CSV.open("w", encoding="utf-8", newline="") as handle:
        escritor = csv.writer(handle, lineterminator="\n")
        escritor.writerow(cabeca)
        escritor.writerows(linhas)


def build(*, update_home: bool = True) -> None:
    html = build_html()
    if "—" in html:
        raise SystemExit("travessão encontrado no HTML gerado")
    SHEET.write_text(CSS, encoding="utf-8")
    TIP_SHEET.write_text(TIP_CSS, encoding="utf-8")
    TIP_SCRIPT.write_text(TIP_JS, encoding="utf-8")
    PAGE.write_text(html.replace("<section ", "\n<section ") + "\n", encoding="utf-8")
    write_csv()
    groups_view.write_group_csv(ASSETS / "reponderacao_grupos_1t.csv", D)

    if update_home:
        home = serie_svg("home2t", "2t", compacta=True)
        HOME_SVG.write_text(home + "\n", encoding="utf-8")
        chaves_home = [_tip_id(p, "2t") for p in PESQUISAS if "2t" in p["turnos"]]
    if update_home and INDEX.exists():
        for nome, fragmento in (
            ("reponderacao_home", home + bloco_tips(chaves_home)),
            ("reponderacao_home_placar", placar_home()),
        ):
            if inject(INDEX, {nome: fragmento}):
                print(f"Capa atualizada ({nome}):", INDEX)
            else:
                print(
                    f"Aviso: marcadores <!--FIG:{nome}--> ausentes em",
                    INDEX,
                    "· nada foi escrito na capa",
                )
    print("Página gerada:", PAGE)
    print("Folha de estilo:", SHEET)
    print("Camada interativa:", TIP_SHEET, "e", TIP_SCRIPT)
    print("Tabela:", TABLE_CSV)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-home",
        action="store_true",
        help="Não atualiza index.html nem o SVG da capa.",
    )
    args = parser.parse_args()
    build(update_home=not args.skip_home)
