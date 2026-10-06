"""Figuras do capítulo 4 (regiões, 2022 contra 2026) e do capítulo 5 (exterior).

Swing é diferença de parcela dos válidos em pontos percentuais: Flávio em 2026
menos Bolsonaro em 2022 e Lula em 2026 menos Lula em 2022, no turno escolhido.
"""

from __future__ import annotations

import math

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    GRADE,
    HALO,
    INK,
    LIMA,
    LULA,
    MUTED,
    OUTROS,
    REGIOES,
    Tips,
    W,
    area,
    botoes,
    chip,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    legenda,
    ln,
    nome_bonito,
    pct,
    pp,
    r,
    registra,
    rotulos_com_fio,
    sobre,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)

AZUL_CLARO = "#a7c0e5"
VERMELHO_CLARO = "#e5a596"
SOBE, DESCE = "#0f7f5f", "#b02f21"


def _sinal_cor(v: float, claro: bool = False) -> str:
    if claro:
        return AZUL_CLARO if v >= 0 else VERMELHO_CLARO
    return FLAVIO if v >= 0 else LULA


def _ufs_por_regiao(P: dict) -> list[tuple[str, list[dict]]]:
    out = []
    for reg in REGIOES:
        ufs = [u for u in P["ufs"] if u["regiao"] == reg]
        out.append((reg, ufs))
    return out


# ------------------------------------------------------------------ swing por UF


@registra("regioes_2022_2026")
def regioes_2022_2026(d, **_op) -> str:
    P = dado(d, "presidente")
    linhas_ = []
    for reg, ufs in _ufs_por_regiao(P):
        linhas_.append(("regiao", reg, P["regioes"][reg]))
        for u in sorted(
            ufs, key=lambda u: -u["comparacao"]["flavio_vs_bolsonaro_1t"]["pp"]
        ):
            linhas_.append(("uf", u["uf"], u))
    vals = [
        abs(x["comparacao"][k]["pp"])
        for _, _, x in linhas_
        for k in (
            "flavio_vs_bolsonaro_1t",
            "lula_vs_lula_1t",
            "flavio_vs_bolsonaro_2t",
            "lula_vs_lula_2t",
        )
    ]
    vmax = math.ceil(max(vals) / 2) * 2
    tips = Tips()
    chaves = [tips.add(_ficha_swing(tipo, rot, x)) for tipo, rot, x in linhas_]
    titulo = "Swing por UF: Flávio contra Bolsonaro e Lula contra Lula de 2022"
    desc = "Barras divergentes por UF, agrupadas por região, em pontos percentuais dos válidos."
    larga = _swing_svg(linhas_, chaves, vmax, titulo, desc, estreita=False)
    estreita = _swing_svg(linhas_, chaves, vmax, titulo, desc, estreita=True)
    ctl = botoes(
        [("1t", "Contra o 1º turno de 2022"), ("2t", "Contra o 2º turno de 2022")],
        "1t",
        "Comparar",
    )
    n = P["nacional"]["comparacao"]
    legenda_ = (
        f"No país, Flávio fez {pp(n['flavio_vs_bolsonaro_1t']['pp'])} sobre Bolsonaro no 1º turno de 2022 e Lula "
        f"{pp(n['lula_vs_lula_1t']['pp'])}; a margem andou {pp(n['virada_margem_vs_1t_pp'])} para Flávio. "
        "Contra o 2º turno de 2022 os dois ficam abaixo, porque o 1º turno de 2026 ainda tem terceira via. "
        "Eixo em pontos percentuais dos válidos. Fonte: presidente.json."
    )
    return figura_html(
        "regioes_2022_2026",
        larga_estreita(larga, estreita),
        legenda_,
        tips,
        controles=ctl,
        modo="full",
    )


def _ficha_swing(tipo: str, rot: str, x: dict) -> str:
    c = x["comparacao"]
    nome = rot if tipo == "regiao" else f"{NOME_UF[rot]}"
    r22 = x["r2022"] if tipo == "uf" else None
    linhas_tip = []
    for turno, rot_t in (("1t", "1º turno"), ("2t", "2º turno")):
        f_, l_ = c[f"flavio_vs_bolsonaro_{turno}"], c[f"lula_vs_lula_{turno}"]
        linhas_tip.append(
            (
                f"Flávio × Bolsonaro {rot_t}",
                f"{pct(f_['pct_a'], 1)} × {pct(f_['pct_b'], 1)} ({pp(f_['pp'], 1)}, {('+' if f_['votos'] >= 0 else '−')}{inteiro(abs(f_['votos']))})",
            )
        )
        linhas_tip.append(
            (
                f"Lula 2026 × Lula {rot_t}",
                f"{pct(l_['pct_a'], 1)} × {pct(l_['pct_b'], 1)} ({pp(l_['pp'], 1)}, {('+' if l_['votos'] >= 0 else '−')}{inteiro(abs(l_['votos']))})",
            )
        )
    linhas_tip.append(("Virada da margem (1º t.)", pp(c["virada_margem_vs_1t_pp"], 2)))
    if r22:
        linhas_tip.append(
            (
                "Comparecimento 2026 × 2022",
                f"{pct(x['pct_comparecimento'], 1)} × {pct(r22['t1']['pct_comparecimento'], 1)}",
            )
        )
    return ficha(nome, "região" if tipo == "regiao" else rot, linhas_tip)


def _swing_svg(
    linhas_: list,
    chaves: list[str],
    vmax: float,
    titulo: str,
    desc: str,
    estreita: bool,
) -> str:
    """Barras divergentes do swing. A versão estreita usa a sigla e cabe em 360."""
    if estreita:
        w, esq, topo, passo, folga = 360, 34, 96, 36, 40
    else:
        w, esq, topo, passo, folga = W, 210, 70, 36, 46
    # na versão estreita a linha da região ganha uma faixa de título acima das barras
    extra_reg = 20 if estreita else 0
    ys, acc = [], topo
    for tipo, _, _ in linhas_:
        ys.append(acc)
        acc += passo + (extra_reg if tipo == "regiao" else 0)
    h = acc + 44
    X = escala(-vmax, vmax, esq + folga, w - folga - (0 if estreita else 40))
    x0 = X(0)
    out = [svg_abre(w, h, titulo, desc)]
    if estreita:
        out.append(legenda([("Flávio 2026 − Bolsonaro 2022", FLAVIO)], 4, 20, 13))
        out.append(legenda([("Lula 2026 − Lula 2022", LULA)], 4, 42, 13))
    else:
        out.append(
            legenda(
                [
                    ("Flávio 2026 − Bolsonaro 2022", FLAVIO),
                    ("Lula 2026 − Lula 2022", LULA),
                ],
                esq,
                24,
            )
        )
    for v in ticks(-vmax, vmax, 4 if estreita else 8):
        out.append(ln(X(v), topo - 10, X(v), h - 38, GRADE))
        out.append(
            t(
                X(v),
                h - 20,
                f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 0)}",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(t(w - 4, h - 2, "pontos percentuais dos válidos", 13, MUTED, "end"))
    out.append(ln(x0, topo - 10, x0, h - 38, INK, 1.4))
    out.append(t(x0 - 8, topo - 18, "← perdeu", 13, MUTED, "end"))
    out.append(t(x0 + 8, topo - 18, "ganhou →", 13, MUTED))
    for i, (tipo, rot, x) in enumerate(linhas_):
        y = ys[i]
        c = x["comparacao"]
        alto = passo + (extra_reg if tipo == "regiao" else 0)
        if tipo == "regiao":
            out.append(
                r(
                    0 if estreita else 10,
                    y + 1,
                    w if estreita else w - 20,
                    alto - 2,
                    "#ebe4d4",
                )
            )
            if estreita:
                out.append(t(4, y + 17, rot, 14, INK, weight="700"))
                y += extra_reg
        if estreita:
            nome = rot if tipo == "uf" else ""
        else:
            nome = rot if tipo == "regiao" else f"{NOME_UF[rot]}"
        grupos = []
        for turno in ("1t", "2t"):
            g = []
            pares = (
                (f"flavio_vs_bolsonaro_{turno}", FLAVIO),
                (f"lula_vs_lula_{turno}", LULA),
            )
            for j, (chave, cor) in enumerate(pares):
                v = c[chave]["pp"]
                yy = y + 5 + j * 15
                xa, xb = sorted((x0, X(v)))
                g.append(r(xa, yy, xb - xa, 12, cor))
                g.append(
                    t(
                        X(v) + (6 if v >= 0 else -6),
                        yy + 11,
                        pp(v, 1)[:-3],
                        13,
                        INK,
                        "start" if v >= 0 else "end",
                        mono=True,
                        extra=HALO,
                    )
                )
            mostra = "" if turno == "1t" else ' display="none"'
            grupos.append(f'<g data-alt-show="{turno}"{mostra}>{"".join(g)}</g>')
        if nome:
            out.append(
                t(
                    esq - 10,
                    y + 22,
                    nome,
                    14 if tipo == "uf" else 15,
                    INK,
                    "end",
                    "700" if tipo == "regiao" else None,
                )
            )
        largura_area = w if estreita else w - 20
        out.append(
            hit(
                area(0 if estreita else 10, ys[i], largura_area, alto)
                + "".join(grupos),
                chaves[i],
            )
        )
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ dispersão


@registra("dispersao_municipios")
def dispersao_municipios(d, **_op) -> str:
    P = dado(d, "presidente")
    mun = [
        m
        for m in tabela_linhas(P["municipios"])
        if m["pct_bolsonaro_2022_1t"] is not None and m["validos"]
    ]
    largura, altura = 1000, 760
    esq, topo, lado = 80, 30, 660
    X = escala(0, 100, esq, esq + lado)
    Y = escala(0, 100, topo + lado, topo)
    emax = max(m["eleitores"] for m in mun)
    out = [
        svg_abre(
            largura,
            altura,
            "Município a município: Bolsonaro no 1º turno de 2022 contra Flávio em 2026",
            "Cada ponto é um município; acima da diagonal, Flávio fez mais que Bolsonaro. Área pelo eleitorado.",
            ' data-near="1"',
        )
    ]
    for v in ticks(0, 100, 5):
        out.append(ln(X(v), topo, X(v), topo + lado, GRADE))
        out.append(ln(esq, Y(v), esq + lado, Y(v), GRADE))
        out.append(
            t(X(v), topo + lado + 22, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True)
        )
        out.append(t(esq - 8, Y(v) + 5, f"{num(v, 0)}%", 13, MUTED, "end", mono=True))
    out.append(ln(X(0), Y(0), X(100), Y(100), INK, 1.4, ' stroke-dasharray="6 4"'))
    out.append(chip(X(4), Y(84), "acima da diagonal: Flávio maior que Bolsonaro", 13))
    out.append(chip(X(70), Y(38), "abaixo: Flávio menor", 13))
    out.append(
        t(
            esq + lado / 2,
            altura - 14,
            "Bolsonaro, 1º turno de 2022 (% dos válidos)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = topo + lado / 2
    out.append(
        t(
            22,
            yy,
            "Flávio, 2026 (% dos válidos)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 22 {yy:.0f})"',
        )
    )
    linhas, xy, grupos = [], [], []
    caminhos: dict[tuple[int, float], list[str]] = {}
    for m in sorted(mun, key=lambda m: -m["eleitores"]):
        gi = REGIOES.index(m["regiao"]) if m["regiao"] in REGIOES else 5
        raio = round((1.6 + 13 * math.sqrt(m["eleitores"] / emax)) * 2) / 2
        x, y = X(m["pct_bolsonaro_2022_1t"]), Y(m["pct_flavio"])
        caminhos.setdefault((gi, raio), []).append(f"M{x:.0f} {y:.0f}h0")
        linhas.append(
            [
                f"{nome_bonito(m['nome'])} ({m['uf']})",
                num(m["pct_bolsonaro_2022_1t"], 1),
                num(m["pct_flavio"], 1),
                pp(m["swing_flavio_pp"], 1),
                f"{num(m['pct_lula'], 1)} × {num(m['pct_lula_2022_1t'], 1)}",
                inteiro(m["eleitores"]),
            ]
        )
        xy.append([round(x), round(y), raio])
        grupos.append(str(gi))
    for (gi, raio), segs in sorted(caminhos.items(), key=lambda kv: -kv[0][1]):
        reg = REGIOES[gi] if gi < 5 else "Exterior"
        out.append(
            f'<path data-g="{gi}" d="{"".join(segs)}" stroke="{COR_REGIAO[reg]}" stroke-width="{2 * raio}" '
            'stroke-linecap="round" stroke-opacity="0.55" fill="none"/>'
        )
    pontos = []
    for m in sorted(mun, key=lambda m: -m["eleitores"])[:6]:
        raio = round((1.6 + 13 * math.sqrt(m["eleitores"] / emax)) * 2) / 2
        pontos.append(
            (
                X(m["pct_bolsonaro_2022_1t"]),
                Y(m["pct_flavio"]),
                raio,
                nome_bonito(m["nome"]),
                COR_REGIAO.get(m["regiao"], COR_REGIAO["Exterior"]),
            )
        )
    out.append(
        rotulos_com_fio(pontos, (esq + 4, topo + 4, esq + lado - 4, topo + lado - 4))
    )
    lx = esq + lado + 40
    out.append(t(lx, topo + 10, "Região", 14, INK, weight="700"))
    for i, reg in enumerate(REGIOES):
        yy = topo + 40 + i * 26
        out.append(
            f'<circle cx="{lx + 7}" cy="{yy - 5}" r="7" fill="{COR_REGIAO[reg]}" fill-opacity="0.75"/>'
        )
        out.append(t(lx + 22, yy, reg, 14))
    out.append(t(lx, topo + 200, "Área do ponto pelo eleitorado", 13, MUTED))
    out.append(t(lx, topo + 220, "de 2026; o maior é São Paulo.", 13, MUTED))
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Município",
            "Bolsonaro 2022, 1º t.",
            "Flávio 2026",
            "Swing de Flávio",
            "Lula 2026 × 2022",
            "Eleitores",
        ],
        linhas,
        xy=xy,
        grupos=grupos,
        nota="em % dos válidos",
    )
    acima = sum(1 for m in mun if m["pct_flavio"] > m["pct_bolsonaro_2022_1t"])
    ctl = botoes(
        [("", "Todas")] + [(str(i), reg) for i, reg in enumerate(REGIOES)],
        "",
        "Região",
        "filtro",
    )
    legenda_ = (
        f"{inteiro(acima)} de {inteiro(len(mun))} municípios ficaram acima da diagonal: Flávio superou a parcela de Bolsonaro "
        "no 1º turno de 2022. O filtro apaga as outras regiões. Fonte: presidente.json (municípios)."
    )
    return figura_html(
        "dispersao_municipios",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=700,
        dim=False,
    )


# ------------------------------------------------------------------ capitais × interior


@registra("capitais_interior")
def capitais_interior(d, **_op) -> str:
    P = dado(d, "presidente")
    soma: dict[tuple[str, bool], dict] = {}
    for m in tabela_linhas(P["municipios"]):
        if m["regiao"] not in REGIOES or m["validos_2022_1t"] is None:
            continue
        s = soma.setdefault(
            (m["regiao"], bool(m["capital"])),
            dict.fromkeys(("f", "l", "v", "b22", "l22", "v22", "n"), 0),
        )
        s["f"] += m["flavio"]
        s["l"] += m["lula"]
        s["v"] += m["validos"]
        s["b22"] += m["bolsonaro_2022_1t"]
        s["l22"] += m["lula_2022_1t"]
        s["v22"] += m["validos_2022_1t"]
        s["n"] += 1
    esq, topo, passo = 230, 70, 44
    linhas_ = [(reg, cap) for reg in REGIOES for cap in (True, False)]
    h = topo + passo * len(linhas_) + len(REGIOES) * 10 + 48
    margens = []
    for k in linhas_:
        s = soma[k]
        margens += [
            100 * (s["f"] - s["l"]) / s["v"],
            100 * (s["b22"] - s["l22"]) / s["v22"],
        ]
    vmax = math.ceil(max(abs(v) for v in margens) / 10) * 10
    X = escala(-vmax, vmax, esq, W - 90)
    x0 = X(0)
    out = [
        svg_abre(
            W,
            h,
            "Capitais e interior por região: margem de 2022 e de 2026",
            "Margem da direita sobre Lula, em pontos dos válidos; barra clara 2022 (Bolsonaro), escura 2026 (Flávio).",
        ),
        r(esq, 13, 13, 13, AZUL_CLARO),
        r(esq + 15, 13, 13, 13, VERMELHO_CLARO),
        t(esq + 34, 24, "tom claro: 1º turno de 2022 (Bolsonaro − Lula)", 14),
        r(esq + 380, 13, 13, 13, FLAVIO),
        r(esq + 395, 13, 13, 13, LULA),
        t(esq + 414, 24, "tom escuro: 2026 (Flávio − Lula)", 14),
        t(esq, 48, "Azul: direita à frente; vermelho: Lula à frente.", 13, MUTED),
    ]
    for v in ticks(-vmax, vmax, 8):
        out.append(ln(X(v), topo - 6, X(v), h - 42, GRADE))
        out.append(
            t(
                X(v),
                h - 22,
                f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 0)}",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(ln(x0, topo - 6, x0, h - 42, INK, 1.4))
    out.append(
        t(W - 90, h - 3, "margem em pontos percentuais dos válidos", 13, MUTED, "end")
    )
    tips = Tips()
    y = topo
    for i, (reg, cap) in enumerate(linhas_):
        if cap and i:
            y += 10
        s = soma[(reg, cap)]
        m26 = 100 * (s["f"] - s["l"]) / s["v"]
        m22 = 100 * (s["b22"] - s["l22"]) / s["v22"]
        corpo = []
        for j, (v, claro) in enumerate(((m22, True), (m26, False))):
            yy = y + 6 + j * 16
            xa, xb = sorted((x0, X(v)))
            corpo.append(r(xa, yy, xb - xa, 14, _sinal_cor(v, claro)))
            corpo.append(
                t(
                    X(v) + (6 if v >= 0 else -6),
                    yy + 12,
                    pp(v, 1)[:-3],
                    13,
                    INK,
                    "start" if v >= 0 else "end",
                    mono=True,
                )
            )
        rot = f"{reg}, {'capitais' if cap else 'interior'}"
        k = tips.add(
            ficha(
                rot,
                f"{inteiro(s['n'])} municípios",
                [
                    ("Flávio 2026", pct(100 * s["f"] / s["v"], 1)),
                    ("Bolsonaro 2022 (1º t.)", pct(100 * s["b22"] / s["v22"], 1)),
                    (
                        "Lula 2026 × 2022",
                        f"{pct(100 * s['l'] / s['v'], 1)} × {pct(100 * s['l22'] / s['v22'], 1)}",
                    ),
                    ("Margem 2026 × 2022", f"{pp(m26, 1)} × {pp(m22, 1)}"),
                    ("Virada", pp(m26 - m22, 1)),
                    ("Válidos 2026", inteiro(s["v"])),
                ],
            )
        )
        lab = t(esq - 12, y + 25, rot, 14, INK, "end", "700" if cap else None)
        out.append(
            hit(
                area(esq - 220, y, W - 90 - esq + 220, passo - 4)
                + lab
                + "".join(corpo),
                k,
                foco=True,
            )
        )
        y += passo
    out.append("</svg>")
    legenda_ = (
        "Margem da direita sobre Lula em capitais e no interior de cada região, somando os municípios com arquivo "
        "completo e base de 2022. Fonte: presidente.json (municípios)."
    )
    maior = max(margens, key=abs)
    foco = (min(x0, X(maior)) - 40, max(x0, X(maior)) + 40, x0)
    return figura_html(
        "capitais_interior", "".join(out), legenda_, tips, minw=820, foco=foco
    )


# ------------------------------------------------------------------ comparecimento


@registra("comparecimento_regioes")
def comparecimento_regioes(d, **_op) -> str:
    P = dado(d, "presidente")
    esq, topo, passo = 210, 70, 26
    linhas_ = []
    for reg, ufs in _ufs_por_regiao(P):
        linhas_.append(
            (
                "regiao",
                reg,
                P["regioes"][reg],
                P["regioes"][reg]["r2026"]["pct_comparecimento"],
            )
        )
        for u in sorted(ufs, key=lambda u: -u["comparacao"]["comparecimento_vs_1t_pp"]):
            linhas_.append(("uf", u["uf"], u, u["pct_comparecimento"]))
    h = topo + passo * len(linhas_) + 40
    todos = []
    for tipo, _, x, v26 in linhas_:
        v22 = (
            x["r2022"]["t1"]["pct_comparecimento"]
            if tipo == "uf"
            else v26 - x["comparacao"]["comparecimento_vs_1t_pp"]
        )
        todos += [v26, v22]
    lo, hi = math.floor(min(todos) / 5) * 5, math.ceil(max(todos) / 5) * 5
    X = escala(lo, hi, esq, W - 150)
    out = [
        svg_abre(
            W,
            h,
            "Comparecimento por UF: 1º turno de 2022 contra 2026",
            "Círculo vazado 2022, cheio 2026; verde onde subiu, vermelho onde caiu.",
        ),
        f'<circle cx="{esq + 6}" cy="20" r="6" fill="#ffffff" stroke="{INK}" stroke-width="2"/>',
        t(esq + 18, 25, "1º turno de 2022", 14),
        f'<circle cx="{esq + 166}" cy="20" r="6" fill="{INK}"/>',
        t(esq + 178, 25, "2026", 14),
        r(esq + 240, 18, 22, 4, SOBE) + t(esq + 268, 25, "subiu", 14),
        r(esq + 330, 18, 22, 4, DESCE) + t(esq + 358, 25, "caiu", 14),
    ]
    for v in ticks(lo, hi, 6):
        out.append(ln(X(v), topo - 6, X(v), h - 34, GRADE))
        out.append(t(X(v), h - 14, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True))
    tips = Tips()
    for i, (tipo, rot, x, v26) in enumerate(linhas_):
        y = topo + i * passo + passo / 2
        delta = x["comparacao"]["comparecimento_vs_1t_pp"]
        v22 = v26 - delta
        cor = SOBE if delta >= 0 else DESCE
        if tipo == "regiao":
            out.append(
                r(
                    esq - 200,
                    y - passo / 2 + 1,
                    W - 140 - esq + 200,
                    passo - 2,
                    "#ebe4d4",
                )
            )
        nome = rot if tipo == "regiao" else NOME_UF[rot]
        corpo = (
            t(
                esq - 12,
                y + 5,
                nome,
                14 if tipo == "uf" else 15,
                INK,
                "end",
                "700" if tipo == "regiao" else None,
            )
            + ln(X(v22), y, X(v26), y, cor, 3.5)
            + f'<circle cx="{X(v22):.1f}" cy="{y:.1f}" r="6" fill="#ffffff" stroke="{INK}" stroke-width="2"/>'
            + f'<circle cx="{X(v26):.1f}" cy="{y:.1f}" r="6" fill="{INK}"/>'
            + t(max(X(v22), X(v26)) + 12, y + 5, pp(delta, 2), 13, INK, mono=True)
        )
        r26 = x["r2026"] if tipo == "regiao" else x
        k = tips.add(
            ficha(
                nome,
                "região" if tipo == "regiao" else rot,
                [
                    ("Comparecimento 2026", pct(v26, 2)),
                    ("1º turno de 2022", pct(v22, 2)),
                    ("Variação", pp(delta, 2)),
                    (
                        "Contra o 2º turno de 2022",
                        pp(x["comparacao"]["comparecimento_vs_2t_pp"], 2),
                    ),
                    ("Eleitores 2026", inteiro(r26["eleitores"])),
                    ("Votantes 2026", inteiro(r26["comparecimento"])),
                ],
            )
        )
        out.append(
            hit(area(esq - 200, y - passo / 2, W - 140 - esq + 200, passo) + corpo, k)
        )
    out.append("</svg>")
    reg = P["regioes"]
    legenda_ = (
        f"Comparecimento sobre o eleitorado apto. Subiu no Norte ({pp(reg['Norte']['comparacao']['comparecimento_vs_1t_pp'])}) "
        f"e no Nordeste ({pp(reg['Nordeste']['comparacao']['comparecimento_vs_1t_pp'])}); caiu no Sul "
        f"({pp(reg['Sul']['comparacao']['comparecimento_vs_1t_pp'])}) e no Sudeste "
        f"({pp(reg['Sudeste']['comparacao']['comparecimento_vs_1t_pp'])}). Fonte: presidente.json."
    )
    return figura_html(
        "comparecimento_regioes",
        "".join(out),
        legenda_,
        tips,
        minw=820,
        foco=(esq - 6, W - 90, esq - 6),
    )


# ------------------------------------------------------------------ exterior


def _barra_100(
    y: float,
    esq: float,
    larg: float,
    partes: list[tuple[float, str, str]],
    alt: float = 26,
) -> str:
    out, x = [], esq
    tot = sum(v for v, _, _ in partes) or 1
    for v, cor, _ in partes:
        w = larg * v / tot
        out.append(r(x, y, w, alt, cor, ' stroke="#f4f0e6" stroke-width="1"'))
        if w > 48:
            out.append(
                t(
                    x + w / 2,
                    y + alt / 2 + 5,
                    f"{num(v, 1)}%",
                    13,
                    sobre(cor),
                    "middle",
                    "600",
                    mono=True,
                )
            )
        x += w
    return "".join(out)


@registra("exterior_continentes")
def exterior_continentes(d, **_op) -> str:
    E = dado(d, "exterior")
    esq, topo, passo, larg = 240, 60, 40, 600
    conts = sorted(E["continentes"], key=lambda c: -c["validos"])
    paises = sorted(E["paises"], key=lambda c: -c["validos"])[:12]
    # cada aba tem a própria altura: o viewBox troca junto com a série
    alturas = {
        "continente": topo + passo * len(conts) + 30,
        "pais": topo + passo * len(paises) + 30,
    }
    h = alturas["continente"]
    vb = "|".join(f"{k}>0 0 {W} {v}" for k, v in alturas.items())
    out = [
        svg_abre(
            W,
            h,
            "Exterior: voto por continente e pelos 12 países com mais válidos",
            "Barras 100% com Flávio, Lula e os demais; à direita, válidos e comparecimento.",
            f' data-alt-vb="{vb}"',
        ),
        legenda([("Flávio", FLAVIO), ("Lula", LULA), ("Demais", OUTROS)], esq, 24),
        t(esq + larg + 20, 24, "válidos · comparecimento", 13, MUTED),
    ]
    tips = Tips()
    for modo, lista, rotulo in (
        ("continente", conts, "continente"),
        ("pais", paises, "pais_nome"),
    ):
        g = []
        for i, c in enumerate(lista):
            y = topo + i * passo
            p = c["pct"]
            demais = 100 - p["flavio"] - p["lula"]
            r22 = c.get("r2022_mesmas_cidades") or {}
            k = tips.add(
                ficha(
                    c[rotulo],
                    (
                        c.get("continente", "")
                        if modo == "pais"
                        else f"{c['cidades']} cidades"
                    ),
                    [
                        (
                            "Flávio · Lula",
                            f"{pct(p['flavio'], 1)} · {pct(p['lula'], 1)}",
                        ),
                        (
                            "Bolsonaro · Lula 2022 (1º t.)",
                            f"{pct(r22.get('pct_bolsonaro_1t'), 1)} · {pct(r22.get('pct_lula_1t'), 1)}",
                        ),
                        (
                            "Swing de Flávio",
                            pp(c.get("swing_flavio_vs_bolsonaro_1t_pp"), 1),
                        ),
                        ("Eleitorado", inteiro(c["eleitores"])),
                        (
                            "Votantes",
                            f"{inteiro(c['comparecimento'])} ({pct(c['pct_comparecimento'], 1)})",
                        ),
                        ("Válidos", inteiro(c["validos"])),
                    ],
                    "2022 nas mesmas cidades",
                )
            )
            corpo = (
                t(esq - 12, y + 19, c[rotulo], 14, INK, "end", "600")
                + _barra_100(
                    y + 1,
                    esq,
                    larg,
                    [
                        (p["flavio"], FLAVIO, "Flávio"),
                        (p["lula"], LULA, "Lula"),
                        (demais, OUTROS, "Demais"),
                    ],
                )
                + t(
                    esq + larg + 20,
                    y + 19,
                    f"{inteiro(c['validos'])} · {pct(c['pct_comparecimento'], 1)}",
                    13,
                    INK,
                    mono=True,
                )
            )
            g.append(hit(area(0, y - 6, W, passo) + corpo, k))
        g.append(
            ln(
                esq + larg / 2,
                topo - 8,
                esq + larg / 2,
                topo + passo * len(lista) - 6,
                INK,
                1,
                ' stroke-dasharray="3 3" pointer-events="none"',
            )
        )
        mostra = "" if modo == "continente" else ' display="none"'
        out.append(f'<g data-alt-show="{modo}"{mostra}>{"".join(g)}</g>')
    out.append("</svg>")
    ctl = botoes(
        [("continente", "Por continente"), ("pais", "Por país (12 maiores)")],
        "continente",
        "Agrupar",
    )
    T = E["total"]
    legenda_ = (
        f"Parcela dos válidos no exterior ({inteiro(T['validos'])} válidos, comparecimento de {pct(T['pct_comparecimento'], 1)}). "
        "A linha tracejada marca 50%. Fonte: exterior.json."
    )
    return figura_html(
        "exterior_continentes", "".join(out), legenda_, tips, controles=ctl, minw=820
    )
