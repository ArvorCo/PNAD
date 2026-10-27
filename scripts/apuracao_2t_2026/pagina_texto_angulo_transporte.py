"""Textos do ângulo do transporte e da ordem de chegada (2º turno de 2026).

``bloco_hipotese(d)`` entra no H3 do capítulo de hipóteses e ``bloco_ordem(d)``
no capítulo cedo e tarde. ``d`` é ``angulo_transporte.json`` (gerado por
``scripts/apuracao-2t-2026-angulo-transporte.py``); sem ele, as duas funções
devolvem "". Todo número sai do JSON.
"""

from __future__ import annotations

from typing import TypeGuard

from apuracao_2026.pagina_comum import (
    FLAVIO,
    caixa,
    inteiro,
    nota,
    num,
    p,
    sinal,
    tabela,
)
from apuracao_2026.pagina_fig_base import (
    GRADE,
    INK,
    MUTED,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    svg_abre,
    t,
    ticks,
)

T1 = "#8a7a3a"
ROTULO = "pede explicação, não prova irregularidade"


def _ok(d: dict | None) -> TypeGuard[dict]:
    return bool(d) and "transporte" in d and "ordem" in d


def _ic(x: dict) -> str:
    ic = x.get("ic95") or [None, None]
    return f"{sinal(x.get('did_pp'), 2)} pp (IC95 de {sinal(ic[0], 2)} a {sinal(ic[1], 2)})"


def _fora_do_zero(T: dict, regra: str) -> list[tuple[int, dict]]:
    """Quintis em que o IC95 da diferença em diferenças da regra não contém o zero."""
    out = []
    for q in T["quintis"]:
        b = (q.get("did") or {}).get(regra) or {}
        lo, hi = (b.get("ic95") or [None, None])[:2]
        if b.get("did_pp") is None or lo is None or hi is None:
            continue
        if lo > 0 or hi < 0:
            out.append((q["quintil"], b))
    return out


def _lista_q(xs: list[tuple[int, dict]]) -> str:
    return "; ".join(f"quintil {q}, {_ic(b)}" for q, b in xs)


# ------------------------------------------------------------------ H3


def _tabela_quintis(T: dict) -> str:
    linhas = [
        [
            f"Q{q['quintil']} ({num(q['lula1_min'], 0)}% a {num(q['lula1_max'], 0)}%)",
            sinal(q["delta_abst_1t_pp"], 2),
            sinal(q["delta_abst_2022_pp"], 2),
            f"{num(q['fim_dia_2t_pct'], 2)}%",
            f"{num(q['fim_dia_1t_pct'], 2)}%",
            sinal(q["swing_f_pp"], 2),
            sinal(q["did"]["salto"].get("did_pp"), 2),
        ]
        for q in T["quintis"]
    ]
    return tabela(
        [
            "quintil de Lula no 1º turno",
            "abstenção 2T−1T (pp)",
            "abstenção 2T−2022, município (pp)",
            "votos 15h–17h, 2T",
            "votos 15h–17h, 1T (amostra)",
            "Flávio 2T−1T (pp)",
            "seções com salto contra vizinhas (pp)",
        ],
        linhas,
        "Marca de transporte por quintil de eleitorado, seções do Brasil sem exterior",
    )


def _bahia(B: dict) -> str:
    s, ba, br = B["Salvador"], B["Bahia"], B["Brasil"]
    corpo = (
        p(
            f"Salvador, onde o Procon-BA contou 544 ônibus parados às 17h09: abstenção de "
            f"{num(s['abst_1t'], 2)}% no 1º turno, {num(s['abst_2t'], 2)}% no 2º e {num(s['abst_2022_mun'], 2)}% "
            f"no 2º turno de 2022. A queda de {sinal(s['delta_abst_1t_pp'], 2)} pp devolve a cidade ao nível de 2022 "
            f"({sinal(s['delta_abst_2022_pp'], 2)} pp). Flávio foi de {num(s['fatia_f_1t'], 2)}% para "
            f"{num(s['fatia_f_2t'], 2)}% entre os dois finalistas ({sinal(s['swing_f_pp'], 2)} pp, contra "
            f"{sinal(br['swing_f_pp'], 2)} no país); Bolsonaro teve {num(s['bolsonaro_2022_h2h'], 2)}% em 2022. "
            f"As duas últimas horas da votação regular levaram {num(s['fim_dia_2t_pct'], 2)}% dos votos de Salvador, "
            f"menos que no país ({num(br['fim_dia_2t_pct'], 2)}%). Seções com salto de comparecimento contra as "
            f"vizinhas: {_ic(s['did_salto'])}.",
            "verificado",
        )
        + p(
            f"Bahia inteira: abstenção {num(ba['abst_1t'], 2)}% → {num(ba['abst_2t'], 2)}% (2022: "
            f"{num(ba['abst_2022_mun'], 2)}%), Flávio {sinal(ba['swing_f_pp'], 2)} pp na parte entre os dois "
            f"finalistas, 2º turno menos 1º, somadas as seções (o país, na mesma régua: {sinal(br['swing_f_pp'], 2)}), "
            f"votos 15h–17h {num(ba['fim_dia_2t_pct'], 2)}%.",
            "verificado",
        )
        + p(
            "O ônibus parado não deixou abstenção alta nem voto concentrado no fim do dia. Pela parcela das 15h às "
            "17h, menor que a do país, o comparecimento a mais veio antes das 15h; essa parte é inferência, porque o "
            "comparecimento extra não foi medido hora a hora.",
            "inferencia",
        )
    )
    return caixa("io", "Bahia e Salvador", corpo)


def bloco_hipotese(d: dict | None, V: dict | None = None) -> str:
    """Bloco do H3 (transporte e comparecimento diferencial).

    ``V`` é ``secoes_voto.json``, opcional: com ele o texto cita também a régua de
    salto do capítulo Seção por seção, que marca seções diferentes.
    """
    if not _ok(d):
        return ""
    T = d["transporte"]
    q = T["quintis"]
    q1, q5 = q[0], q[-1]
    dq = T["q5_menos_q1"]
    br = T["brasil"]
    c = T["correlacao_secao"]
    txt = p(
        f"<strong>A abstenção não caiu mais nos redutos de Lula.</strong> Em cinco grupos de mesmo eleitorado, "
        f"pela fatia de Lula no 1º turno da própria seção, a variação 2T−1T vai de {sinal(q1['delta_abst_1t_pp'], 2)} pp "
        f"no quintil mais fraco de Lula a {sinal(q5['delta_abst_1t_pp'], 2)} pp no mais forte (diferença de "
        f"{sinal(dq['delta_abst_1t_pp'], 2)} pp); a maior queda está no quarto quintil ({sinal(q[3]['delta_abst_1t_pp'], 2)}). "
        f"Base: {inteiro(d['base']['secoes'])} seções pareadas.",
        "verificado",
    )
    txt += p(
        f"<strong>A última parte do dia encolheu mais onde Lula é forte.</strong> As duas últimas horas da votação "
        f"regular (15h a 17h de Brasília, pelo relógio do log) levaram {num(q1['fim_dia_2t_pct'], 2)}% dos votos no "
        f"quintil 1 e {num(q5['fim_dia_2t_pct'], 2)}% no quintil 5. A diferença já existia no 1º turno "
        f"({num(q1['fim_dia_1t_pct'], 2)}% e {num(q5['fim_dia_1t_pct'], 2)}%, amostra de uma seção em cinco), e entre "
        f"os turnos a parcela caiu {num(-q5['delta_fim_dia_pp'], 2)} pp no quintil 5 contra "
        f"{num(-q1['delta_fim_dia_pp'], 2)} no quintil 1. Mobilização de última hora deixaria o contrário. "
        "O 1º turno tinha mais cargos na urna e votação mais lenta; por isso a régua é a comparação entre "
        "quintis, não o nível de um turno contra o outro.",
        "verificado",
    )
    sal = br["did"]["salto"]
    fim = br["did"]["fim"]
    txt += p(
        f"<strong>Onde o comparecimento saltou, o voto andou, no agregado, como nas vizinhas.</strong> Nas "
        f"{inteiro(sal['n_secoes_marcadas'])} seções com comparecimento ao menos 5 pp acima da mediana do próprio "
        f"município, a fatia de Flávio variou {sinal(sal['swing_marcadas_pp'], 2)} pp contra "
        f"{sinal(sal['swing_vizinhas_pp'], 2)} nas vizinhas: diferença em diferenças de {_ic(sal)}. Nas "
        f"{inteiro(fim['n_secoes_marcadas'])} seções com o fim do dia 10 pp acima da mediana do município: {_ic(fim)}. "
        f"No quintil mais forte de Lula, {_ic(q5['did']['salto'])}. Dentro de cada município, a correlação entre a "
        f"variação do comparecimento e a da fatia de Flávio é {sinal(c['corr_dentro_municipio'], 3)}."
        + _outra_regua(V),
        "verificado",
    )
    txt += _tabela_quintis(T)
    txt += _contrario_quintis(T)
    txt += _bahia(d["bahia"])
    txt += nota(
        "contrario",
        f"Contra o 2º turno de 2022 o desenho inverte: a abstenção do quintil mais forte de Lula ficou "
        f"{num(-q5['delta_abst_2022_pp'], 2)} pp abaixo da do município em 2022, contra "
        f"{num(-q1['delta_abst_2022_pp'], 2)} no quintil mais fraco. Os redutos de Lula estão mais presentes que em "
        "2022. A comparação de 2022 é por município (as seções não se pareiam) e não mede a mudança entre os "
        "turnos de 2026, que é a que acompanha o deslocamento.",
        "O que um leitor hostil vai calcular.",
    )
    q5s, q5f = q5["did"]["salto"], q5["did"].get("fim") or {}
    por_q = ""
    if _fora_do_zero(T, "salto") or _fora_do_zero(T, "fim"):
        por_q = (
            " Por quintil aparece pequena, de décimos de ponto, e fora do desenho esperado: no quintil mais forte "
            f"de Lula, as seções que saltaram votaram como as vizinhas, {_ic(q5s)}"
            + (
                f", e as de fim do dia pesado andaram para Flávio, {_ic(q5f)}: sinal contrário ao da hipótese."
                if q5f.get("did_pp") is not None and q5f["did_pp"] > 0
                else "."
            )
        )
    txt += nota(
        "juizo",
        "A marca de transporte de última hora (abstenção caindo mais e voto concentrado no fim do dia onde Lula é "
        f"forte, com voto deslocado nas seções que saltaram) não aparece no agregado.{por_q} Mobilização ao longo do "
        f"dia, antes das 15h, não se separa nestes dados. Atipicidade {ROTULO}.",
    )
    return txt


def _contrario_quintis(T: dict) -> str:
    """Achado contrário: quintis com diferença em diferenças fora do zero, nas duas regras."""
    sal, fim = _fora_do_zero(T, "salto"), _fora_do_zero(T, "fim")
    if not sal and not fim:
        return ""
    partes = []
    if sal:
        partes.append(
            "Nas seções em que o comparecimento saltou, a diferença em diferenças fica fora do zero em "
            f"{len(sal)} dos {len(T['quintis'])} quintis: {_lista_q(sal)}."
        )
    if fim:
        partes.append(
            "Nas seções com o fim do dia pesado, fica fora do zero em "
            f"{len(fim)}: {_lista_q(fim)}."
        )
    partes.append(
        "Negativo é Flávio perdendo mais que nas vizinhas do município; positivo, menos. O agregado esconde "
        "esses sinais porque eles têm direções diferentes entre os quintis."
    )
    return nota("contrario", " ".join(partes), "O que a tabela por quintil mostra.")


def _outra_regua(V: dict | None) -> str:
    """Frase com a régua de salto do capítulo Seção por seção (contra a própria seção), quando existe."""
    s = next(
        (x for x in (V or {}).get("sinais", []) if x.get("sinal") == "delta"),
        None,
    )
    if not s or s.get("did_fatia_flavio_pp") is None:
        return ""
    return (
        " O capítulo Seção por seção usa outra régua de salto: a seção com comparecimento 5 pp ou mais acima do "
        f"dela mesma no 1º turno, sem comparar com o município ({inteiro(s['n_did'])} seções), com diferença em "
        f"diferenças de {sinal(s['did_fatia_flavio_pp'], 2)} pp (erro-padrão aproximado "
        f"{num(s.get('ep_did_fatia_flavio_pp'), 2)}). As duas réguas marcam seções diferentes."
    )


# ------------------------------------------------------------------ cedo e tarde


def _figura(od: dict) -> str:
    V = od["vintis"]
    w, h = 1100, 520
    x0, x1, y0, y1 = 80, 1060, 70, 330
    yb0, yb1 = 380, 470
    niveis = [v for a in V for v in (a["fatia_f_2t"], a["fatia_f_1t"])]
    lo, hi = min([*niveis, 50]) - 1, max([*niveis, 50]) + 1
    fy = escala(lo, hi, y1, y0)
    dmin = min(a["dif_pp"] for a in V)
    fd = escala(0, min(dmin * 1.2, -1), yb0, yb1)
    passo = (x1 - x0) / len(V)
    fx = [x0 + passo * (i + 0.5) for i in range(len(V))]
    tips = Tips()
    out = [
        svg_abre(
            w,
            h,
            "Flávio por ordem de recebimento do BU",
            "Fatia de Flávio entre os dois finalistas em 20 grupos de mesmo número de votos, pela ordem em que "
            "o TSE recebeu o BU, no 2º turno e no 1º turno das mesmas seções, e a diferença entre os dois.",
        ),
        t(
            x0,
            y0 - 30,
            "Parte de Flávio entre os dois finalistas, %",
            14,
            INK,
            weight="700",
        ),
    ]
    for v in ticks(lo, hi, 5):
        out.append(ln(x0, fy(v), x1, fy(v), GRADE, 1))
        out.append(t(x0 - 8, fy(v) + 5, num(v, 0), 13, MUTED, "end"))
    out.append(ln(x0, fy(50), x1, fy(50), INK, 1.2, ' stroke-dasharray="4 4"'))
    for serie, cor in (("fatia_f_1t", T1), ("fatia_f_2t", FLAVIO)):
        pts = " ".join(f"{fx[i]:.1f},{fy(a[serie]):.1f}" for i, a in enumerate(V))
        out.append(
            f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="2.5"/>'
        )
        for i, a in enumerate(V):
            out.append(
                f'<circle cx="{fx[i]:.1f}" cy="{fy(a[serie]):.1f}" r="4" fill="{cor}"/>'
            )
    out.append(t(x0, yb0 - 14, "2º turno menos 1º turno, pp", 14, INK, weight="700"))
    out.append(ln(x0, yb0, x1, yb0, INK, 1))
    for i, a in enumerate(V):
        y = fd(a["dif_pp"])
        out.append(
            f'<rect x="{fx[i] - passo * 0.35:.1f}" y="{yb0:.1f}" width="{passo * 0.7:.1f}" height="{y - yb0:.1f}" fill="{MUTED}"/>'
        )
        k = tips.add(
            ficha(
                f"{a['vintil']}º vintil",
                f"BU recebidos de {a['de']} a {a['ate']}",
                [
                    ("Flávio, 2º turno", f"{num(a['fatia_f_2t'], 2)}%"),
                    ("Flávio, 1º turno", f"{num(a['fatia_f_1t'], 2)}%"),
                    ("diferença", f"{sinal(a['dif_pp'], 2)} pp"),
                    ("seções", inteiro(a["secoes"])),
                    ("UFs com mais votos", ", ".join(a["ufs_principais"])),
                ],
            )
        )
        out.append(hit(area(fx[i] - passo / 2, y0, passo, yb1 - y0), k, foco=True))
        if i % 4 == 0 or i == len(V) - 1:
            out.append(t(fx[i], h - 20, a["de"], 12, MUTED, "middle"))
    out.append(
        t(
            x0 + (x1 - x0) / 2,
            h - 2,
            "início do grupo, horário de Brasília do recebimento",
            12,
            MUTED,
            "middle",
        )
    )
    out.append("</svg>")
    leg = legenda_html(
        [("2º turno", FLAVIO), ("1º turno, mesmas seções", T1), ("diferença", MUTED)]
    )
    rs = od.get("resumo") or {}
    varia = (
        f"varia {num(rs['dif_amplitude_pp'], 2)} pp entre os grupos, contra {num(rs['fatia_2t_amplitude_pp'], 2)} pp "
        "no nível"
        if rs.get("dif_amplitude_pp") is not None
        and rs.get("fatia_2t_amplitude_pp") is not None
        else "varia bem menos que o nível"
    )
    return figura_html(
        "angulo_ordem_recebimento",
        "".join(out),
        f"Os grupos que chegaram primeiro eram mais de Flávio nos dois turnos; a diferença entre os turnos {varia}.",
        tips,
        apos=leg,
    )


def _tabela_vintis(od: dict, titulo: str) -> str:
    return tabela(
        [
            "vintil",
            "de",
            "até",
            "Flávio 2T",
            "Flávio 1T",
            "diferença (pp)",
            "UFs com mais votos",
        ],
        [
            [
                str(a["vintil"]),
                a["de"],
                a["ate"],
                f"{num(a['fatia_f_2t'], 2)}%",
                f"{num(a['fatia_f_1t'], 2)}%",
                sinal(a["dif_pp"], 2),
                ", ".join(a["ufs_principais"]),
            ]
            for a in od["vintis"]
        ],
        titulo,
    )


def bloco_ordem(d: dict | None) -> str:
    """Bloco do capítulo cedo e tarde: ordem de recebimento e de encerramento do BU."""
    if not _ok(d):
        return ""
    R = d["ordem"]["recebimento"]
    E = d["ordem"]["encerramento"]
    rr, er = R["resumo"], E["resumo"]
    V = R["vintis"]
    pico = max(V, key=lambda a: a["fatia_f_2t"])
    difs = [a["dif_pp"] for a in V]
    ac = R["acumulado"]
    ult_ufs = ", ".join(V[-1]["ufs_principais"])
    prim_ufs = ", ".join(V[0]["ufs_principais"])
    txt = p(
        f"Em {len(V)} grupos "
        f"de mesmo número de votos, pela hora em que o TSE recebeu cada BU, Flávio tem {num(V[0]['fatia_f_2t'], 2)}% no "
        f"primeiro ({V[0]['de']} a {V[0]['ate']}), {num(pico['fatia_f_2t'], 2)}% no {pico['vintil']}º ({pico['de']} a "
        f"{pico['ate']}, com {', '.join(pico['ufs_principais'])} à frente) e {num(V[-1]['fatia_f_2t'], 2)}% no último "
        f"({V[-1]['de']} a {V[-1]['ate']}, {', '.join(V[-1]['ufs_principais'])}). A amplitude é de "
        f"{num(rr['fatia_2t_amplitude_pp'], 2)} pp. Nas mesmas seções, a diferença contra o 1º turno fica entre "
        f"{sinal(min(difs), 2)} e {sinal(max(difs), 2)} pp em todos os grupos (amplitude {num(rr['dif_amplitude_pp'], 2)}): "
        f"quem chegou cedo já era mais de Flávio no 1º turno.",
        "verificado",
    )
    txt += p(
        "<strong>A virada da noite veio sobretudo da ordem de chegada, e pouco de mudança dentro das seções.</strong> "
        f"A diferença contra o 1º turno varia pouco: {num(rr['dif_amplitude_pp'], 2)} pp de amplitude na mudança, "
        f"contra {num(rr['fatia_2t_amplitude_pp'], 2)} pp no nível.",
        "inferencia",
    )
    txt += p(
        f"Somando na ordem de recebimento, a partir de 100 mil votos, Flávio fica à frente de {ac['frente_de']} a "
        f"{ac['frente_ate']}, com máximo de {num(ac['maximo_pct'], 2)}% às {ac['maximo_em']}, e termina em "
        f"{num(ac['final_pct'], 2)}%. A diferença entre os turnos é {num(abs(V[-1]['dif_pp'] - V[0]['dif_pp']), 2)} pp "
        f"{'mais negativa' if V[-1]['dif_pp'] < V[0]['dif_pp'] else 'menos negativa'} no último grupo que no primeiro "
        f"({sinal(V[-1]['dif_pp'], 2)} contra {sinal(V[0]['dif_pp'], 2)}; correlação com a ordem "
        f"{sinal(rr['corr_ordem_dif'], 2)}), e nos últimos grupos pesam {ult_ufs}; a deriva é "
        f"pequena perto dos {num(rr['fatia_2t_amplitude_pp'], 2)} pp que separam os grupos no nível.",
        "verificado",
    )
    txt += _figura(R)
    ev = E["vintis"]
    txt += p(
        f"Pela hora de encerramento do BU, o mesmo desenho: {num(ev[0]['fatia_f_2t'], 2)}% de Flávio nas urnas que "
        f"fecharam primeiro e {num(ev[-1]['fatia_f_2t'], 2)}% nas últimas (amplitude {num(er['fatia_2t_amplitude_pp'], 2)} pp), "
        f"com a diferença contra o 1º turno entre {sinal(min(a['dif_pp'] for a in ev), 2)} e "
        f"{sinal(max(a['dif_pp'] for a in ev), 2)} pp. Nos últimos grupos pesam {', '.join(ev[-1]['ufs_principais'])}, "
        "a mesma geografia do recebimento tardio.",
        "verificado",
    )
    txt += nota(
        "inferencia",
        f"A ordem de recebimento segue a transmissão de cada UF ({prim_ufs} nos primeiros grupos; {ult_ufs} nos "
        "últimos); ela muda o placar parcial e não o resultado. Um atraso seletivo deixaria a "
        "diferença contra o 1º turno variando com a hora de chegada. Ela varia, com tendência "
        f"(correlação {sinal(rr['corr_ordem_dif'], 2)} com a ordem), mas pouco: {num(rr['dif_amplitude_pp'], 2)} pp de "
        f"amplitude contra {num(rr['fatia_2t_amplitude_pp'], 2)} pp no nível. Isso descarta um atraso seletivo grande, "
        f"não um pequeno. Atipicidade {ROTULO}.",
    )
    txt += _tabela_vintis(
        R, "Flávio por ordem de recebimento do BU, 20 grupos de mesmo número de votos"
    )
    return txt
