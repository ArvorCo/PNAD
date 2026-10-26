"""Textos da resposta em três números e dos cenários de cruzamento ("De onde veio o voto").

Todo número sai de ``transferencia.json`` (blocos ``resposta``, ``cruzamento`` e
``pesquisas``); nenhum é digitado aqui. Ordem do capítulo: a conta das urnas, a
resposta em três números, os cenários e o que sobrevive a todos, a regressão e os
limites.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import caixa, cartao, inteiro, nota, num, p, tabela
from apuracao_2026.pagina_fig_base import FLAVIO, LULA

from .pagina_fig_transferencia import rotulo_fita


def mi(v: float, casas: int = 2) -> str:
    x = v / 1e6
    return f"{num(x, casas)} {'milhão' if abs(round(x, casas)) < 2 else 'milhões'}"


def pc(v: float, casas: int = 1) -> str:
    return f"{num(v, casas)}%"


def _data(x: dict) -> str:
    """Data de divulgação pela chave da fonte (``nexus_24`` vira 24/10), como no resto do capítulo."""
    return f"{x['fonte'].split('_')[-1]}/10"


def _sinal_pc(v: float, casas: int = 1) -> str:
    s = num(abs(v), casas)
    return ("+" if v > 0 else "−" if v < 0 else "") + s + "%"


def tres_numeros(T: dict) -> str:
    """(b) A resposta direta: quem voltou, a terceira via e o cruzamento entre as bases."""
    r = T["resposta"]
    cz = T["cruzamento"]
    cp = cz["comparacao"]
    pad = cz["cenarios"][cz["padrao"]]
    tc = pad["metricas"]["terceira"]
    fx = cz["faixa_publicada"]
    hi = max(fx["lula_para_flavio_pct"][1], fx["flavio_para_lula_pct"][1])
    nex = [x for x in cz["linhas_publicadas"] if x["instituto"] != "Quaest"]
    lo_nex = min(min(x["lula_para_flavio_pct"], x["flavio_para_lula_pct"]) for x in nex)
    cards = (
        '<div class="finding-grid tr-tres">'
        + cartao(
            mi(r["voltaram_milhoes"] * 1e6, 1),
            f"não votaram no 1º turno e votaram no 2º. De cada 100, {num(r['voltaram_lula_pct'], 0)} foram para Lula "
            f"(de {num(r['voltaram_lula_ic'][0], 0)} a {num(r['voltaram_lula_ic'][1], 0)} no intervalo de 95%)",
            LULA,
        )
        + cartao(
            f"{num(tc['flavio_pct'], 0)} de 100",
            f"eleitores da terceira via foram para Flávio e {num(tc['lula_pct'], 0)} para Lula no cenário padrão "
            f"(Flávio fica entre {num(cp['muda_pouco']['terceira_flavio_pct'][0], 1)} e "
            f"{num(cp['muda_pouco']['terceira_flavio_pct'][1], 1)} nos quatro cenários)",
            FLAVIO,
        )
        + cartao(
            f"0 a {num(hi, 0)} de 100",
            "eleitores de um finalista no 1º turno votaram no outro no 2º, conforme a pesquisa: zero na Quaest, de "
            f"{num(lo_nex, 1)} a {num(hi, 1)} na Nexus. O padrão usa zero",
        )
        + "</div>"
    )
    texto = p(
        "Os três números são estimativa, não medição. A urna diz quanto cada candidato teve em cada turno, não quem "
        "votou em quem. O primeiro sai da regressão entre municípios, mais abaixo; o segundo, do ajuste às duas urnas a "
        "partir das linhas publicadas pelos institutos; o terceiro é o que as pesquisas mediram e é a peça em que elas "
        "mais discordam, por isso o capítulo mostra quatro cenários para ele. Quem voltou a votar explica "
        f"{num(r['explica_pp'], 2)} ponto (de {num(r['explica_pp_ic'][0], 2)} a {num(r['explica_pp_ic'][1], 2)}) dos "
        f"{num(abs(r['swing_h2h_pp']), 2)} pontos que Flávio perdeu na parte entre os dois; o resto se decidiu entre "
        "eleitores que já tinham votado no 1º turno.",
        "inferencia",
    )
    return cards + texto


def cenarios_intro(T: dict) -> str:
    """(c) O que é o cruzamento, o que as pesquisas publicaram e por que o padrão é zero."""
    cz = T["cruzamento"]
    pc_ = cz["padrao_compativel"]
    nex = [x for x in cz["linhas_publicadas"] if x["instituto"] != "Quaest"]
    qua = [x for x in cz["linhas_publicadas"] if x["instituto"] == "Quaest"]
    lf = "; ".join(
        f"{pc(x['lula_para_flavio_pct'])} ({_data(x)}, p. {x['pagina']})" for x in nex
    )
    fl = "; ".join(f"{pc(x['flavio_para_lula_pct'])}" for x in nex)
    q = qua[0] if qua else None
    q_txt = (
        f"A Quaest publicou zero nas duas direções ({_data(q)}, p. {q['pagina']}). "
        if q and q["lula_para_flavio_pct"] == 0 and q["flavio_para_lula_pct"] == 0
        else ""
    )
    pes = cz["cenarios"]["pesquisas"]
    um = p(
        "A peça que mais divide as leituras é o cruzamento entre as bases: quantos eleitores de Lula no 1º turno votaram "
        "em Flávio no 2º, e quantos de Flávio votaram em Lula. A urna não mostra isso, e as pesquisas não concordam. "
        f"{q_txt}A Nexus publicou, de Lula para Flávio, {lf}; de Flávio para Lula, {fl}, nas mesmas páginas. O Datafolha "
        "não publica a linha das bases. Nenhum dos três publica quantos entrevistados há em cada grupo, então não dá para "
        "calcular o intervalo de cada linha. Em vez de escolher uma, o capítulo mostra quatro cenários: sem cruzamento, "
        "1% de cada base, 2% de cada base e a média do que as pesquisas mais recentes mediram "
        f"({pc(pes['lula_para_flavio_pct'], 2)} de Lula para Flávio e {pc(pes['flavio_para_lula_pct'], 2)} de Flávio "
        "para Lula, indecisos repartidos).",
        "hipotese",
    )
    dois = p(
        f"O padrão é o cenário sem cruzamento. Ele passa nos dois testes: fecha as duas urnas em todas as "
        f"{pc_['ufs_ajustadas'] - 1} UFs e no exterior (o maior desvio é de {num(pc_['margens_desvio_max_votos'], 3)} "
        "voto) e é o que a Quaest publicou; fica abaixo das linhas da Nexus. Em todos os cenários o ajuste bate as mesmas "
        "duas urnas; muda só a divisão interna.",
        "verificado" if pc_["margens"] and pc_["linhas_publicadas"] else "hipotese",
    )
    return um + dois


def frase_grafico() -> str:
    """A frase acima do gráfico, em português corrente."""
    return (
        '<p class="tr-acima">O gráfico liga cada escolha do 1º turno, à esquerda, à escolha do 2º turno, à direita. '
        "Cada faixa é um caminho, e a largura é o número de eleitores que o fizeram. Os botões trocam o cenário de "
        "cruzamento: as duas pontas não mudam, porque são as urnas; muda só como as faixas se repartem no meio.</p>"
    )


def como_ler(T: dict) -> str:
    cz = T["cruzamento"]
    fig = cz["cenarios"][cz["padrao"]]["figura"]
    v = float(fig["votos"]["cury"]["lula"])
    pcl = float(fig["pct_origem"]["cury"]["lula"])
    exemplo = f"→ Lula {rotulo_fita(v, pcl)}"
    return caixa(
        "io",
        "Como ler.",
        "<p>Cada faixa liga uma escolha do 1º turno, à esquerda, a uma escolha do 2º, à direita, e a largura é o número "
        "de eleitores, na mesma escala para todas. O rótulo diz para onde a faixa vai, quantos milhões fizeram aquele "
        f"caminho e que parte da origem isso é: “{escape(exemplo)}”, saindo de Augusto Cury, quer dizer que "
        f"{num(pcl, 0)} de cada 100 eleitores de Cury no 1º turno votaram em Lula no 2º. Faixa sólida parte de linha "
        "publicada por instituto, pontilhada vem da regressão sobre as urnas e hachurada é estimativa da casa; em todas, "
        "a largura final sai do ajuste às duas urnas, e nenhuma identifica o voto de um eleitor.</p>",
    )


def sem_js(T: dict) -> str:
    cz = T["cruzamento"]
    nome = cz["cenarios"][cz["padrao"]]["nome"].lower()
    return (
        f'<noscript><p class="tr-semjs">Sem JavaScript, a figura e a tabela acima mostram o cenário padrão ({escape(nome)}). '
        "Os quatro cenários estão lado a lado na tabela seguinte.</p></noscript>"
    )


def tabela_cenarios(T: dict) -> str:
    cz = T["cruzamento"]
    linhas = []
    for k in cz["ordem"]:
        c = cz["cenarios"][k]
        m = c["metricas"]
        t3 = m["terceira"]
        nome = escape(c["nome"]) + (" (padrão)" if k == cz["padrao"] else "")
        linhas.append(
            [
                nome,
                f"{pc(c['lula_para_flavio_pct'], 2)} · {num(m['lula_para_flavio'] / 1e6, 2)} mi",
                f"{pc(c['flavio_para_lula_pct'], 2)} · {num(m['flavio_para_lula'] / 1e6, 2)} mi",
                inteiro(round(m["cruzamento_liquido_para_lula"], -3)),
                f"{num(t3['flavio_pct'], 1)} · {num(t3['lula_pct'], 1)} · {num(t3['bn_pct'], 1)}",
                f"{num(m['fidelidade_lula'], 1)} / {num(m['fidelidade_flavio'], 1)}",
                f"{num(m['ganho_fora_base_lula'] / 1e6, 2)} / {num(m['ganho_fora_base_flavio'] / 1e6, 2)}",
                num(m["razao_consolidacao_flavio_lula"], 2),
                num(m["voltaram_lula_pct"], 1),
            ]
        )
    livre = T["ipf"]["sensibilidades"].get("cruzamento_livre")
    if livre:
        m = livre["metricas"]
        t3 = m["terceira"]
        linhas.append(
            [
                "Diagnóstico: o ajuste escolhe o cruzamento",
                f"{pc(m['lula_para_flavio_pct'], 2)} · {num(m['lula_para_flavio'] / 1e6, 2)} mi",
                f"{pc(m['flavio_para_lula_pct'], 2)} · {num(m['flavio_para_lula'] / 1e6, 2)} mi",
                inteiro(round(m["cruzamento_liquido_para_lula"], -3)),
                f"{num(t3['flavio_pct'], 1)} · {num(t3['lula_pct'], 1)} · {num(t3['bn_pct'], 1)}",
                f"{num(m['fidelidade_lula'], 1)} / {num(m['fidelidade_flavio'], 1)}",
                f"{num(m['ganho_fora_base_lula'] / 1e6, 2)} / {num(m['ganho_fora_base_flavio'] / 1e6, 2)}",
                num(m["razao_consolidacao_flavio_lula"], 2),
                num(m["voltaram_lula_pct"], 1),
            ]
        )
    return tabela(
        [
            "Cenário",
            "De Lula para Flávio (% da base · eleitores)",
            "De Flávio para Lula",
            "Saldo para Lula (eleitores)",
            "Terceira via, de cada 100: Flávio · Lula · branco e nulo",
            "Fidelidade Lula / Flávio (%)",
            "Ganho fora da base, Lula / Flávio (mi)",
            "Razão Flávio : Lula fora da base",
            "Quem voltou, % para Lula",
        ],
        linhas,
        "Os quatro cenários batem as mesmas duas urnas, UF a UF. A última linha é diagnóstico: as duas células partem das "
        "pesquisas e o ajuste as move livremente (era o número central da versão anterior deste capítulo); o ajuste "
        "empurra o cruzamento para muito além do que as pesquisas mediram. Fonte: transferencia.json (cruzamento).",
    )


def muda_nao_muda(T: dict) -> str:
    cz = T["cruzamento"]
    cp = cz["comparacao"]
    nm, mp, md = cp["nao_muda"], cp["muda_pouco"], cp["muda"]
    o = T["margens"]["nacional"]["origens"]
    return (
        p(
            "O que não muda entre os cenários: as duas urnas, que são as pontas do gráfico; os "
            f"{mi(nm['voltaram'][0])} que voltaram a votar e a divisão deles ({pc(nm['voltaram_lula_pct'][0])} para Lula), "
            "porque vêm da regressão e entram iguais em todos; e a soma do que cada candidato tirou de fora das duas "
            "bases. Lula recebeu da terceira via, do branco e nulo do 1º turno e do saldo da troca com a base de Flávio "
            f"de {mi(nm['lula_de_terceira_bn_e_cruzamento'][0])} a {mi(nm['lula_de_terceira_bn_e_cruzamento'][1])} em "
            f"todos; Flávio, de {mi(nm['flavio_de_terceira_bn_e_cruzamento'][0])} a "
            f"{mi(nm['flavio_de_terceira_bn_e_cruzamento'][1])}. Cruzamento e terceira via são vasos comunicantes: cada "
            "voto que a base de Flávio desse a Lula, em saldo, é um voto de terceira via ou de branco e nulo que iria "
            "para Flávio em vez de Lula.",
            "inferencia",
        )
        + p(
            "O que muda pouco: a terceira via. Ela dá a Flávio de "
            f"{num(mp['terceira_flavio_pct'][0], 1)} a {num(mp['terceira_flavio_pct'][1], 1)} de cada 100 eleitores nos "
            "quatro cenários. Com a mesma porcentagem nas duas direções, o que cruza de Lula para Flávio quase empata com o "
            f"que cruza de Flávio para Lula, porque as bases têm tamanho parecido ({mi(o['lula'], 1)} e "
            f"{mi(o['flavio'], 1)}): o saldo para Lula vai de {inteiro(round(mp['cruzamento_liquido_para_lula'][0], -3))} "
            f"a {inteiro(round(mp['cruzamento_liquido_para_lula'][1], -3))} eleitores.",
            "inferencia",
        )
        + p(
            f"O que muda: a fidelidade de cada base (Lula de {pc(md['fidelidade_lula'][0])} a "
            f"{pc(md['fidelidade_lula'][1])}, Flávio de {pc(md['fidelidade_flavio'][0])} a {pc(md['fidelidade_flavio'][1])}), "
            f"o ganho fora da própria base (Lula de {mi(md['ganho_fora_base_lula'][0])} a {mi(md['ganho_fora_base_lula'][1])}, "
            f"Flávio de {mi(md['ganho_fora_base_flavio'][0])} a {mi(md['ganho_fora_base_flavio'][1])}) e a razão de "
            f"consolidação, de {num(md['razao_consolidacao'][0], 2)} a {num(md['razao_consolidacao'][1], 2)} para 1. O "
            "cruzamento bruto entra no ganho fora da base dos dois ao mesmo tempo; a razão sobe com ele sem que nenhum dos "
            "dois leve vantagem.",
            "inferencia",
        )
    )


def tabela_cruzamento_publicado(T: dict) -> str:
    cz = T["cruzamento"]
    liq = {
        (x["instituto"], x["campo"], x["pagina"]): x
        for x in cz["publicado_liquido"]["linhas"]
    }
    linhas = []
    for x in cz["linhas_publicadas"]:
        pl, pf = x["publicado_lula"], x["publicado_flavio"]
        q = liq[(x["instituto"], x["campo"], x["pagina"])]
        linhas.append(
            [
                escape(f"{x['instituto']}, {x['campo']}"),
                str(x["pagina"]),
                escape(x["registro"]),
                f"{num(pl['F'], 1)} · {num(pl['L'], 1)} · {num(pl['BN'], 1)} · {num(pl['NS'], 1)}",
                f"{num(pf['L'], 1)} · {num(pf['F'], 1)} · {num(pf['BN'], 1)} · {num(pf['NS'], 1)}",
                _sinal_pc(q["liquido_para_lula_pct_base_flavio"], 2),
                "sim" if x["na_media"] else "não",
            ]
        )
    return tabela(
        [
            "Pesquisa",
            "Página",
            "Registro",
            "Base de Lula: Flávio · Lula · branco e nulo · indeciso",
            "Base de Flávio: Lula · Flávio · branco e nulo · indeciso",
            "Saldo para Lula (% da base de Flávio)",
            "Na média do cenário",
        ],
        linhas,
        "Linhas de base publicadas: voto lembrado no 1º turno cruzado com a intenção de 2º turno, na mesma entrevista, "
        "percentuais publicados. O cenário das pesquisas usa a onda mais recente de cada instituto, com os indecisos "
        "repartidos na proporção da linha. Fonte: PDFs com SHA-256 em transferencia.json (priors.fontes).",
    )


def terceira_contrario(T: dict) -> str:
    pt = T["pesquisas"]["terceira_via_2t"]
    cz = T["cruzamento"]
    cp = cz["comparacao"]
    inv = T["ipf"]["invariantes"]
    eq = [e for e in pt.get("equilibrio", []) if e]
    ondas = pt["linhas"]
    n_inst = len({x["instituto"] for x in ondas})
    liq = cz["publicado_liquido"]["faixa_pct_base_flavio"]
    sint = T["pesquisas"].get("sintese_pre_1t")
    sint_txt = (
        f" A síntese da casa de 04/10, antes do 1º turno, dizia que {pc(100 * sint['fracao_flavio'], 0)} da queda da "
        "terceira via reapareceria em Flávio."
        if sint
        else ""
    )
    eq_txt = ""
    if len(eq) == 2:
        eq_txt = (
            f" Mantido o resto do ajuste, para a terceira via chegar ao menor número publicado ({pc(eq[0]['alvo_pct'])}), "
            f"a base de Flávio teria de ter cedido a Lula, em saldo, {pc(eq[0]['flavio_para_lula_pct'])} dos seus eleitores "
            f"({mi(eq[0]['flavio_para_lula'])}); para o maior ({pc(eq[1]['alvo_pct'])}), "
            f"{pc(eq[1]['flavio_para_lula_pct'])} ({mi(eq[1]['flavio_para_lula'])}). As linhas de base das mesmas pesquisas "
            f"implicam saldo de {_sinal_pc(liq[0])} a {_sinal_pc(liq[1])}. Os outros dois caminhos que levariam ao número "
            "das pesquisas também não aparecem nelas: a base de Flávio perder para branco, nulo ou abstenção bem mais do "
            "que as linhas mostram, ou o branco e nulo do 1º turno não ter dado quase nada a ele. As urnas não separam "
            "esses três caminhos."
        )
    return nota(
        "contrario",
        f"As pesquisas mediram a terceira via indo mais para Flávio: de {pc(pt['flavio_do_estoque'][0])} a "
        f"{pc(pt['flavio_do_estoque'][1])} do eleitorado dela, em {len(ondas)} ondas de {n_inst} institutos (de "
        f"{pc(pt['flavio_entre_finalistas'][0])} a {pc(pt['flavio_entre_finalistas'][1])} entre os que escolheram um "
        f"finalista).{sint_txt} Nos quatro cenários a matriz dá de {pc(cp['muda_pouco']['terceira_flavio_pct'][0])} a "
        f"{pc(cp['muda_pouco']['terceira_flavio_pct'][1])}, e em nenhuma troca de prior passa de "
        f"{pc(inv['terceira_flavio_pct'][1])}.{eq_txt}",
        "A terceira via não foi para Flávio como as pesquisas mediram.",
    )


CSS = (
    "<style>.tr-acima{font-size:18px;max-width:900px}"
    "#transferencia .tr-frase{font-size:16px;margin:4px 0 12px;max-width:1000px}"
    "#transferencia .tr-cem td .tr-n{display:block;font-size:12px;color:var(--muted);font-weight:400}"
    "#transferencia .tr-cem tr.tr-tot th,#transferencia .tr-cem tr.tr-tot td{border-top:2px solid var(--ink)}"
    ".tr-semjs{font-style:italic}</style>"
)
