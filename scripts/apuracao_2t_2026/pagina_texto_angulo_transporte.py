"""Textos do ângulo do transporte e da ordem de chegada (2º turno de 2026).

``bloco_hipotese(d)`` entra no H3 do capítulo de hipóteses e ``bloco_ordem(d)``
no capítulo cedo e tarde. ``d`` é ``angulo_transporte.json`` (gerado por
``scripts/apuracao-2t-2026-angulo-transporte.py``); sem ele, as duas funções
devolvem "". Todo número sai do JSON.
"""

from __future__ import annotations

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


def _ok(d: dict | None) -> bool:
    return bool(d) and "transporte" in d and "ordem" in d


def _ic(x: dict) -> str:
    ic = x.get("ic95") or [None, None]
    return f"{sinal(x.get('did_pp'), 2)} pp (IC95 de {sinal(ic[0], 2)} a {sinal(ic[1], 2)})"


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
            f"{num(ba['abst_2022_mun'], 2)}%), Flávio {sinal(ba['swing_f_pp'], 2)} pp, votos 15h–17h "
            f"{num(ba['fim_dia_2t_pct'], 2)}%.",
            "verificado",
        )
        + p(
            "O ônibus parado não deixou abstenção alta nem voto concentrado no fim do dia; o comparecimento a mais "
            "veio antes das 15h, como no resto do país.",
            "inferencia",
        )
    )
    return caixa("io", "Bahia e Salvador", corpo)


def bloco_hipotese(d: dict | None) -> str:
    """Bloco do H3 (transporte e comparecimento diferencial)."""
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
        f"<strong>Onde o comparecimento saltou, o voto andou como nas vizinhas.</strong> Nas "
        f"{inteiro(sal['n_secoes_marcadas'])} seções com comparecimento ao menos 5 pp acima da mediana do próprio "
        f"município, a fatia de Flávio variou {sinal(sal['swing_marcadas_pp'], 2)} pp contra "
        f"{sinal(sal['swing_vizinhas_pp'], 2)} nas vizinhas: diferença em diferenças de {_ic(sal)}. Nas "
        f"{inteiro(fim['n_secoes_marcadas'])} seções com o fim do dia 10 pp acima da mediana do município: {_ic(fim)}. "
        f"No quintil mais forte de Lula, {_ic(q5['did']['salto'])}. Dentro de cada município, a correlação entre a "
        f"variação do comparecimento e a da fatia de Flávio é {sinal(c['corr_dentro_municipio'], 3)}.",
        "verificado",
    )
    txt += _tabela_quintis(T)
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
    txt += nota(
        "juizo",
        "A marca de transporte de última hora (abstenção caindo mais e voto concentrado no fim do dia onde Lula é "
        "forte, com voto deslocado nas seções que saltaram) não aparece. Mobilização ao longo do dia, antes das "
        f"15h, não se separa nestes dados. Atipicidade {ROTULO}.",
    )
    return txt


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
    return figura_html(
        "angulo_ordem_recebimento",
        "".join(out),
        "Os grupos que chegaram primeiro eram mais de Flávio nos dois turnos; a diferença entre os turnos "
        "quase não muda com a hora de chegada.",
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
        f"<strong>A virada da noite veio da ordem de chegada, não de mudança dentro das seções.</strong> Em 20 grupos "
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
        f"Somando na ordem de recebimento, a partir de 100 mil votos, Flávio fica à frente de {ac['frente_de']} a "
        f"{ac['frente_ate']}, com máximo de {num(ac['maximo_pct'], 2)}% às {ac['maximo_em']}, e termina em "
        f"{num(ac['final_pct'], 2)}%. A diferença entre os turnos fica cerca de meio ponto mais negativa nos últimos grupos "
        f"(correlação com a ordem {sinal(rr['corr_ordem_dif'], 2)}), onde pesam {ult_ufs}; a deriva é "
        f"pequena perto dos {num(rr['fatia_2t_amplitude_pp'], 2)} pp que separam os grupos.",
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
        "diferença contra o 1º turno variando com a hora de chegada, e ela fica estável. Atipicidade "
        f"{ROTULO}.",
    )
    txt += _tabela_vintis(
        R, "Flávio por ordem de recebimento do BU, 20 grupos de mesmo número de votos"
    )
    return txt
