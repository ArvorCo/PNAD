#!/usr/bin/env python3
"""Gera as três páginas de reponderação; --skip-home preserva a capa e seus assets."""

from __future__ import annotations

import argparse
import csv
import importlib
import json
from copy import deepcopy
from html import escape as esc

from ga_tag import injetar
from reponderacao_vista.charts import (
    gap_svg,
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
    curto,
    frase,
    gap,
    groups_view,
    longo,
    periodo,
    rotulo,
    sinal,
)
from reponderacao_vista.markers import (
    TIPS,
    _tip_id,
)
from reponderacao_vista.style import (
    CSS,
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
    for nome, dados in (
        ("Média simples · sem janela", simples),
        ("Média móvel · 7 dias", kernel),
    ):
        for tipo, marca in (("publicado", "fato"), ("ajustado", "inferencia")):
            v = dados[tipo]
            blocos.append(
                f"<div>{selo(marca, 'publicado' if tipo == 'publicado' else 'reponderado')}"
                f"<span>{esc(nome)}</span>"
                f'<b><em class="flavio">{br(v["flavio"], 1)}</em> × '
                f'<em class="lula">{br(v["lula"], 1)}</em></b>'
                f"<small>diferença {sinal(gap(v), 1)} ponto"
                f"{'s' if abs(round(gap(v), 1)) != 1 else ''}</small></div>"
            )
    lista = ", ".join(ultimo["institutos"])
    janela = ", ".join(ultimo["cobertura_movel"]["institutos"]) or "nenhum"
    return (
        f'<div class="ledger reveal">{"".join(blocos)}</div>'
        f'<p class="note">Média simples: última onda de cada instituto, peso igual. '
        f"Média Arvor: {esc(AGG['metodo']['kernel'])}. "
        f"Institutos na média simples: {esc(lista)}. Na janela de 7 dias: {esc(janela)}. Cenário: {esc(CENARIOS[CEN])}.</p>"
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


def paginas_fonte(fonte: dict, turno: str | None = None) -> str:
    itens = fonte.get("paginas") or {}
    if turno:
        other = "1t" if turno == "2t" else "2t"
        itens = {
            key: value for key, value in itens.items() if not key.startswith(other)
        }
    if not itens:
        return fonte.get("localizador", "páginas não declaradas")
    return ", ".join(
        f"{'p. ' if str(valor)[:1].isdigit() else ''}{valor} "
        f"({PAGINAS.get(chave, chave.replace('_', ' '))})"
        for chave, valor in itens.items()
    )


def cartao(pesquisa: dict, turno: str | None = None) -> str:
    if turno:
        pesquisa = deepcopy(pesquisa)
        pesquisa["turnos"] = {turno: pesquisa["turnos"][turno]}
        other = "1t" if turno == "2t" else "2t"
        pesquisa["fonte"]["paginas"] = {
            k: v
            for k, v in pesquisa["fonte"].get("paginas", {}).items()
            if not k.startswith(other)
        }
        if turno == "2t":
            source = pesquisa["fonte"]
            complements = [
                item
                for item in source.get("complementos", [])
                if "1º turno" not in item["rotulo"] and "(1t)" not in item["rotulo"]
            ]
            if "1º turno" in source.get("rotulo", ""):
                second = next(
                    (
                        item
                        for item in complements
                        if "2º turno" in item["rotulo"] or "(2t)" in item["rotulo"]
                    ),
                    None,
                )
                if second:
                    source.update(url=second["url"], rotulo=second["rotulo"])
                    complements.remove(second)
            source["complementos"] = complements
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
        "O perfil assumido tem"
        if renda.get("perfil_tipo") == "hipotese_onda_anterior"
        else (
            "O registro prevê"
            if renda.get("perfil_tipo") == "cota_registrada"
            else (
                "A calibração tem como alvo"
                if renda.get("perfil_tipo") == "alvo_de_calibracao"
                else "A amostra declara"
            )
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
                    br(valores["flavio"], 1),
                    br(valores["lula"], 1),
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
        f'<article class="poll reveal" id="pesquisa-{esc(pesquisa["id"], quote=True)}" '
        f'data-research-house="{esc(pesquisa["instituto"], quote=True)}" data-research-release="{pesquisa["divulgacao"]}" '
        f'data-research-turns="{",".join(pesquisa["turnos"])}">'
        f'<header class="poll-head"><div><h3>{esc(pesquisa["instituto"])}, '
        f"campo de {esc(periodo(pesquisa['campo']))}</h3>"
        f'<p class="note">{esc(pesquisa["registro_tse"])} · contratante {esc(pesquisa["contratante"])} · '
        f"n = {br(pesquisa['n'], 0)} · {esc(pesquisa['metodo'])} · divulgação em "
        f"{esc(longo(pesquisa['divulgacao']))}{link_dossie}{link_pdf}</p>{aviso_fonte}"
        f"{groups_view.selection_note(pesquisa) if turno != '2t' else ''}"
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
        + '<p class="note">Os cenários e as demais opções abaixo usam o total de entrevistados.'
        + (
            " A comparação do 1º turno com a urna, em votos válidos, está nos detalhes da ficha."
            if t1
            else ""
        )
        + "</p>"
        + tabela(
            ["Turno", "Cenário da PNAD", "Flávio", "Lula", "Flávio − Lula", "Uso"],
            cenarios,
            cls="scenarios",
        )
        + extras
        + importlib.import_module("reponderacao_vista.urna_view").poll_table(
            pesquisa, tabela, CENARIOS
        )
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
            "Cada onda entra pela data de divulgação. A média usa apenas os sete dias até a data observada. A linha fina e tracejada é a média "
            "das pesquisas como foram publicadas. A linha cheia é a mesma média depois de "
            "trocar uma margem, a de renda, pela distribuição da PNAD Contínua anual de 2025. "
            "A troca é nossa, e por isso a linha cheia é inferência declarada. "
            "Roxo: indecisos; verde: branco/nulo/não vai votar. As duas linhas usam "
            "as ondas que separam essas respostas, com cobertura informada abaixo.",
        )
        + importlib.import_module("reponderacao-janela-view").summary(D, "2t", tabela)
        + placar("2t")
        + importlib.import_module("reponderacao-nao-escolha-view").summary(
            D, "2t", tabela, br
        )
        + '<p class="plain reveal">Publicado, a média Arvor marca Flávio '
        + br(kernel["publicado"]["flavio"], 1)
        + " e Lula "
        + br(kernel["publicado"]["lula"], 1)
        + ". Sob a régua oficial de renda, marca Flávio "
        + br(kernel["ajustado"]["flavio"], 1)
        + " e Lula "
        + br(kernel["ajustado"]["lula"], 1)
        + ". A diferença sai de "
        + sinal(gap(kernel["publicado"]), 1)
        + " para "
        + sinal(gap(kernel["ajustado"]), 1)
        + " ponto na diferença Flávio − Lula.</p>"
    )
    parciais = [
        p
        for p in PESQUISAS
        if "2t" in p["turnos"]
        and p["fonte"].get("tipo") in ("materia", "painel_contratante")
    ]
    if parciais:
        corpo += (
            '<p class="note">A série inclui fonte parcial: '
            + "; ".join(
                f'<a href="#pesquisa-{esc(p["id"])}">{esc(p["instituto"])} ({longo(p["divulgacao"])})</a>'
                for p in parciais
            )
            + ". Os votos por renda vêm da divulgação, sem o PDF, e a reponderação usa o perfil declarado na divulgação ou, quando ele falta, a hipótese registrada na ficha, condicionada à confirmação do perfil ponderado final.</p>"
        )
    return capitulo(
        1,
        "segundo-turno",
        "O 2º turno sob a régua oficial",
        "Candidatos, indecisos e branco/nulo/não vai votar, com médias publicadas e reponderadas.",
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
    historico = (
        groups_view.scenario_summary(D, tabela)
        + figura(
            "primeiro-turno-chart",
            "Série do 1º turno",
            "Lula, Flávio, demais candidaturas, indecisos e branco/nulo/não vai votar.",
            serie_svg("s1t", "1t"),
            "Lula e Flávio usam os cenários sem Marçal com cruzamento de renda. "
            "Os grupos usam apenas ondas que permitem separar as candidaturas por renda, "
            "com cobertura e datas informadas abaixo. Cinza: centro-direita; preto: esquerda + nanicos. "
            "Roxo: indecisos; verde: branco/nulo/não vai votar. "
            "Média móvel de 7 dias pela divulgação, sempre para trás. Tracejado é publicado; contínuo é reponderado. "
            "Pontilhado conecta lacunas apenas visualmente, sem entrar na média. "
            "No celular, deslize o gráfico para ver as datas recentes e os grupos.",
        )
        + importlib.import_module("reponderacao-janela-view").summary(D, "1t", tabela)
        + groups_view.group_summary(D, tabela, br)
        + importlib.import_module("reponderacao-nao-escolha-view").summary(
            D, "1t", tabela, br
        )
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
        "O 1º turno contra a urna",
        "O resultado oficial, o erro das últimas ondas e o efeito da renda, sob o mesmo denominador.",
        importlib.import_module("reponderacao_vista.urna_view").section(tabela)
        + '<details class="urna-details"><summary>Explorar o histórico do 1º turno sobre o total de entrevistados</summary>'
        + '<p class="note">Arquivo histórico em percentuais sobre o total; estes números não são comparados diretamente com os votos válidos da urna. As séries mostram as preferências nas datas das pesquisas. <a href="apuracao_1o_turno_2026.html#pesquisas">Comparação final e metodologia do erro</a>.</p>'
        + historico
        + "</details>",
    )


def ch_manchete() -> str:
    polls = [p for p in PESQUISAS if "2t" in p["turnos"]]
    viradas = sum(
        1
        for p in polls
        if p["turnos"]["2t"]["gap_publicado"] != 0
        and p["turnos"]["2t"]["gap_publicado"] * p["turnos"]["2t"]["gap_ajustado"] <= 0
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


def ch_institutos(turno: str | None = None) -> str:
    return capitulo(
        4,
        "institutos",
        "Instituto por instituto",
        "Publicado e PNAD, com ficha e fonte de cada onda.",
        importlib.import_module("reponderacao_vista.institutos").body(
            (turno,) if turno else ("2t", "1t")
        ),
    )


def ch_pesquisas(turno: str | None = None) -> str:
    return capitulo(
        5,
        "pesquisas",
        "Pesquisa por pesquisa",
        "Cada onda com a ficha do documento, a composição de renda, o efeito da troca e a "
        "prova de que a leitura do relatório está certa.",
        '<div class="research-controls" hidden><label>Turno<select id="research-turn">'
        + (
            f'<option value="{turno}">{TURNOS[turno]}</option>'
            if turno
            else '<option value="all">Todos os turnos</option><option value="2t">2º turno</option><option value="1t">1º turno</option>'
        )
        + "</select></label>"
        '<label>Ondas<select id="research-waves"><option value="latest">Última de cada casa por turno</option><option value="all">Todas as ondas do arquivo</option></select></label></div>'
        '<p id="research-state" class="note" aria-live="polite">Arquivo completo, da onda mais recente à mais antiga.</p>'
        + "".join(
            cartao(p, turno) for p in RECENTES if not turno or turno in p["turnos"]
        ),
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
        f"<p>{esc(frase(AGG['metodo']['kernel']))}. {esc(frase(AGG['metodo']['linha']))}</p>"
        f"<p>{esc(AGG['metodo']['historico'])}</p>"
        f"<p>{esc(frase(AGG['metodo']['media_simples']))} As duas médias aparecem lado a lado "
        "porque respondem a perguntas diferentes: a simples mostra a fotografia mais "
        "recente de cada casa, a móvel mostra apenas a semana observada.</p></article>"
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


def ch_fontes(turno: str | None = None) -> str:
    linhas = [
        [
            esc(p["instituto"]),
            esc(periodo(p["campo"])),
            esc(p["registro_tse"]),
            br(p["n"], 0),
            f"<code>{esc(p['fonte'].get('arquivo') or p['fonte'].get('pdf') or 'sem arquivo arquivado')}</code>",
            esc(paginas_fonte(p["fonte"], turno)),
        ]
        for p in RECENTES
        if not turno or turno in p["turnos"]
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


def bloco_tips(chaves: list[str] | None = None) -> str:
    """Fichas dos alvos embutidas na própria página, sem depender de rede."""
    dados = TIPS if chaves is None else {k: TIPS[k] for k in chaves if k in TIPS}
    if not dados:
        return ""
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    seguro = texto.replace("</", "<\\/")
    return f'<script type="application/json" class="tips">{seguro}</script>'


def build_html() -> str:
    return importlib.import_module("reponderacao-paginas").current_html(globals())


def placar_home() -> str:
    """Placar compacto da capa, com a mesma convenção de fato e inferência."""
    simulation = json.loads((ASSETS / "reponderacao_simulador.json").read_text())
    central, projection = simulation["central"], simulation["central_projection"]
    celulas = [
        (
            f"{br(central['flavio'], 1)} × {br(central['lula'], 1)}",
            "Central Média Arvor · Flávio × Lula / válidos",
        ),
        (
            f"{br(projection['flavio'], 1)} × {br(projection['lula'], 1)}",
            "Central Projeção Arvor · Flávio × Lula / válidos",
        ),
        (br(central["abstencao"], 1) + "%", "Abstenção / eleitorado"),
        (
            "+" + br(simulation["defaults"]["presenca_relativa"], 1) + "%",
            "Ajuste relativo de Flávio · hipótese do 1º turno",
        ),
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
    SHEET.write_text(CSS, encoding="utf-8")
    TIP_SHEET.write_text(TIP_CSS, encoding="utf-8")
    TIP_SCRIPT.write_text(TIP_JS, encoding="utf-8")
    html = build_html()
    if "—" in html:
        raise SystemExit("travessão encontrado no HTML gerado")
    PAGE.write_text(
        injetar(html).replace("<section ", "\n<section ") + "\n", encoding="utf-8"
    )
    importlib.import_module("reponderacao-paginas").write_companions(globals())
    write_csv()
    groups_view.write_group_csv(ASSETS / "reponderacao_grupos_1t.csv", D)
    importlib.import_module("reponderacao-janela-view").write_csv(
        ASSETS / "reponderacao_medias_7d.csv", D
    )
    importlib.import_module("reponderacao-nao-escolha-view").write_csv(
        ASSETS / "reponderacao_nao_escolha.csv", D
    )

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
