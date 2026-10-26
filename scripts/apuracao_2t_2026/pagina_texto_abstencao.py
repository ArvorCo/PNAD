"""Textos, tabelas e hipóteses do capítulo "A abstenção mais baixa" (2º turno de 2026)."""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import caminho, inteiro, num, p, rotulo
from apuracao_2026.pagina_fig_base import pct, pp

from .pagina_fig_turnos_util import linhas_de, lista_adiada, municipio, tabela_compacta


def noticias_abstencao(N: dict | None) -> list[dict]:
    if not N:
        return []
    return [
        x for x in N.get("itens", []) if x.get("tema") == "abstencao" and x.get("url")
    ]


def fontes_imprensa(itens: list[dict]) -> str:
    """Lista das matérias da noite sobre abstenção, com veículo, hora e endereço."""
    if not itens:
        return ""
    lis = []
    for x in itens:
        quando = escape(str(x.get("quando", "")).replace("T", " ")[:16])
        tipo = "relato" if x.get("tipo") != "hipotese" else "hipotese"
        lis.append(
            f"<li>{rotulo(tipo)} <b>{escape(x.get('veiculo', ''))}</b>, {quando}: "
            f'<a href="{escape(x["url"])}">{escape(x.get("titulo", ""))}</a>. {escape(x.get("resumo", ""))}</li>'
        )
    return (
        '<details class="ct-det"><summary>A abstenção nas matérias da noite</summary>'
        f'<ul class="fontes">{"".join(lis)}</ul></details>'
    )


def _por_cd(C1: dict) -> dict[str, dict]:
    return {m["cd_tse"]: m for m in linhas_de(C1["municipios"])}


def tabela_quedas(C1: dict) -> str:
    bloco = C1.get("abstencao_caiu_5pp") or {}
    if not bloco.get("lista"):
        return ""
    cd = _por_cd(C1)
    ms = sorted(linhas_de(bloco["lista"]), key=lambda m: m["delta_abstencao_pp"])
    linhas = []
    for m in ms:
        x = cd.get(m["cd_tse"], {})
        linhas.append(
            [
                municipio(m["nome"], m["uf"]),
                inteiro(m["aptos"]),
                num(x.get("t1_pct_abstencao"), 2),
                num(x.get("t2_pct_abstencao"), 2),
                pp(m["delta_abstencao_pp"]),
                num(x.get("t2_pct_lula"), 1),
            ]
        )
    return tabela_compacta(
        [
            "Município",
            "Eleitores",
            "Abstenção 1º turno, %",
            "Abstenção 2º turno, %",
            "Mudança",
            "Lula 2º turno, %",
        ],
        linhas,
        f"Os {len(ms)} municípios com 5 mil eleitores ou mais em que a abstenção caiu 5 pontos ou mais contra o 1º turno. "
        "Fonte: comparacao_1t.json (abstencao_caiu_5pp).",
    )


def lista_altas(C1: dict) -> str:
    bloco = C1.get("abstencao_subiu_5pp") or {}
    if not bloco.get("lista"):
        return ""
    cd = _por_cd(C1)
    ms = sorted(linhas_de(bloco["lista"]), key=lambda m: -m["delta_abstencao_pp"])
    linhas = [
        [
            municipio(m["nome"], m["uf"]),
            inteiro(m["aptos"]),
            num(cd.get(m["cd_tse"], {}).get("t1_pct_abstencao"), 2),
            num(cd.get(m["cd_tse"], {}).get("t2_pct_abstencao"), 2),
            pp(m["delta_abstencao_pp"]),
        ]
        for m in ms
    ]
    return lista_adiada(
        "ab-lista-altas",
        f"Lista completa: os {len(ms)} municípios com 5 mil eleitores ou mais em que a abstenção subiu 5 pontos ou mais",
        ["Município", "Eleitores", "1º turno, %", "2º turno, %", "Mudança"],
        linhas,
    )


def tabela_capitais(A: dict) -> str:
    caps = sorted(
        A["capitais_x_interior"].get("capitais_lista", []), key=lambda c: c["pa_2t"]
    )
    if not caps:
        return ""
    todas = {
        "AC",
        "AL",
        "AM",
        "AP",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MG",
        "MS",
        "MT",
        "PA",
        "PB",
        "PE",
        "PI",
        "PR",
    }
    todas |= {"RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"}
    fora = sorted(todas - {c["uf"] for c in caps})
    linhas = [
        [
            municipio(c["nome"], c["uf"]),
            inteiro(c["aptos"]),
            num(c["pa_2t"], 2),
            num(c["pa_1t"], 2),
            pp(c["delta_1t_pp"]),
            num(c["pa_2022_2t"], 2),
            num(c["pct_lula"], 1),
        ]
        for c in caps
    ]
    return (
        f'<details class="ct-det"><summary>As {len(caps)} capitais com arquivo completo, da menor à maior abstenção</summary>'
        + tabela_compacta(
            [
                "Capital",
                "Eleitores",
                "2º turno, %",
                "1º turno, %",
                "Mudança",
                "2022, %",
                "Lula 2º turno, %",
            ],
            linhas,
            "Fonte: abstencao.json (capitais_x_interior.capitais_lista); capital com seção por totalizar na rodada fica fora"
            + (f" ({', '.join(fora)})." if fora else "."),
        )
        + "</details>"
    )


def hipoteses(d, A: dict, q_lula: list[dict], q_abs: list[dict]) -> str:
    """Bloco das explicações candidatas, cada uma com o que o dado sustenta e o que não sustenta."""
    S = d.get("secoes.json") or {}
    PV = d.get("pesquisas_vs_urna.json") or {}
    pr = caminho(S, "prorrogacao.brasil", {}) or {}
    est = next(
        (
            x
            for x in caminho(S, "estimativa_nacional.indicadores", []) or []
            if x.get("indicador") == "apos_19h"
        ),
        None,
    )
    corr = caminho(
        PV,
        "hipoteses.contabilidade_entre_turnos.correlacao_variacao_abstencao_com_residuo",
    )
    itens = []
    if pr:
        tarde = (
            f" A estimativa nacional da amostra estratificada dá {pct(est['pct'])} das seções com último voto depois das 19h "
            f"(intervalo de 95% de {num(est['ic95'][0], 2)} a {num(est['ic95'][1], 2)})."
            if est
            else ""
        )
        itens.append(
            "<li><b>Prorrogação até 19h.</b> "
            + rotulo("verificado")
            + f" Na amostra de {inteiro(pr.get('n'))} seções com boletim de urna, o último voto tem mediana "
            f"{pr.get('encerramento_p50', 's/d')} e p99 {pr.get('encerramento_p99', 's/d')}; só {pct(pr.get('pct_apos_1900'))} das seções "
            f"lidas votaram depois das 19h.{tarde} A urna fechou quando acabou a fila, perto das 17h. A prorrogação não "
            "explica a queda: quase ninguém usou as duas horas a mais. O capítulo Seção por seção traz a tabela por UF.</li>"
        )
    if q_lula:
        menor, maior = q_lula[0], q_lula[-1]
        itens.append(
            "<li><b>Mobilização das campanhas.</b> "
            + rotulo("hipotese")
            + " A imprensa da noite atribuiu a queda à mobilização de rua, com foco em regiões favoráveis a Lula. "
            + rotulo("contrario")
            + f" O dado municipal não mostra a concentração esperada: nos municípios em que Lula teve mais voto no 1º turno "
            f"(quinto mais forte), a abstenção variou {pp(maior['valor'])}; no quinto mais fraco, {pp(menor['valor'])}. A queda foi "
            f"geral{', e menor nos redutos de Lula' if maior['valor'] > menor['valor'] else ''}. Mobilização dos dois lados ao mesmo tempo é compatível com isso; "
            "o dado não separa quem mobilizou quem.</li>"
        )
    if q_abs:
        itens.append(
            "<li><b>A abstenção explica o erro das pesquisas ou a queda de Flávio?</b> "
            + rotulo("verificado")
            + (
                f" Entre as UFs, a correlação entre a mudança da abstenção e o resíduo de Flávio nas pesquisas é {num(corr, 2)}."
                if corr is not None
                else ""
            )
            + f" Entre os municípios, onde a abstenção mais caiu (primeiro quinto) a parte de Flávio mudou "
            f"{pp(q_abs[0]['valor'])}; onde ela subiu (último quinto), {pp(q_abs[-1]['valor'])}. "
            + rotulo("contrario")
            + f" A diferença, de {num(abs(q_abs[0]['valor'] - q_abs[-1]['valor']), 2)} ponto, vai na direção esperada se os "
            "novos votantes pendessem para Lula; é pequena perto da queda de Flávio, que aparece inteira até onde a abstenção "
            "subiu. A abstenção baixa é fato; não é a explicação principal do resultado.</li>"
        )
    itens.append(
        "<li><b>Transporte gratuito.</b> "
        + rotulo("hipotese")
        + " Transporte no dia da eleição eleva o comparecimento em áreas rurais e periféricas. O acervo não tem a oferta "
        "de transporte por município no 1º e no 2º turno; sem ela, a hipótese não se testa e fica como pergunta.</li>"
    )
    itens.append(
        "<li><b>Boca de urna e pressão no dia.</b> "
        + rotulo("hipotese")
        + " É crime eleitoral no dia da votação (Lei 9.504/1997, art. 39, § 5º). A totalização não registra abordagem de "
        "eleitor; nada neste capítulo mede ou descarta essa conduta. Relato precisa de registro em ata ou de ocorrência.</li>"
    )
    itens.append(
        "<li><b>Clima.</b> "
        + rotulo("hipotese")
        + " No 1º turno, a análise da casa com dados ERA5 achou a chuva associada a quedas de energia nas urnas, não à "
        "ausência do eleitor (efeito sobre a abstenção dentro do município com intervalo que inclui o zero; "
        '<a href="clima_abstencao_1t_2026.html">relatório</a>). O tempo observado em 25/10 ainda não está no acervo; '
        "a previsão da véspera não serve de medida.</li>"
    )
    return (
        "<h3>O que explica a queda: hipóteses e o que o dado diz de cada uma</h3>"
        + p(
            "A abstenção caiu, e isso é fato. A causa não está nos arquivos da totalização, que contam quem votou e não "
            "por que votou. Cada explicação abaixo leva o rótulo do que ela é e o teste que o acervo permite.",
        )
        + f'<ul class="hipoteses">{"".join(itens)}</ul>'
    )
