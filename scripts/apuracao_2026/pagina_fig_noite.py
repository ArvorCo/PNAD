"""Figuras dos capítulos 1, 2, 3 e 14: placar, a noite, a falha do TSE e o coletor.

Tempo em minutos desde 00:00 de 04/10 (hora de Brasília); depois da meia-noite
soma 1.440. As três paradas do arquivo nacional saem de
`linha_do_tempo.travamentos.nacional` (as que moveram mais de mil seções) e a
lacuna geral de `linha_do_tempo.pausa_geral`, nunca de horário digitado.
"""

from __future__ import annotations

import math

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    COR_CAND,
    FLAVIO,
    GRADE,
    HALO,
    INK,
    LULA,
    MUTED,
    NOME_CAND,
    OUTROS,
    OUTROS_TXT,
    SOMBRA,
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
    minutos,
    nome_bonito,
    pct,
    pp,
    r,
    registra,
    rot_hora,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)

GOLD = "#7d5b00"
HACHURA = (
    '<defs><pattern id="hach-pausa" width="7" height="7" patternUnits="userSpaceOnUse" '
    'patternTransform="rotate(45)"><rect width="7" height="7" fill="#efe6cf"/>'
    '<rect width="2.4" height="7" fill="#c9b27a"/></pattern></defs>'
)


def paradas(L: dict) -> list[dict]:
    """As paradas do arquivo nacional que seguraram mais de mil seções."""
    return [p for p in L["travamentos"]["nacional"] if p["secoes_no_salto"] > 1000]


def versoes(L: dict) -> list[dict]:
    return [v for v in tabela_linhas(L["nacional"]["versoes"]) if (v["st"] or 0) > 0]


CORTE_NOITE = 22 * 60
"""Fim do eixo das figuras da noite: depois das 22h o arquivo só andou de 99,76% a 100%."""


def corta_noite(vs: list[dict]) -> tuple[list[dict], str]:
    """Versões até as 22h e a nota sobre o que ficou depois, para pôr no desenho."""
    vis = [v for v in vs if minutos(v["gerado_brt"]) <= CORTE_NOITE]
    tarde = vs[len(vis) :]
    if not tarde:
        return vis, ""
    ult = tarde[-1]["gerado_brt"]
    dia = " do dia 5" if ult[8:10] == "05" else ""
    nota = (
        f"Eixo cortado às 22h: depois, {len(tarde)} versões levaram as seções de "
        f"{num(vis[-1]['pst'], 2)}% a {num(tarde[-1]['pst'], 2)}% "
        f"(+{inteiro(sum(v['d_vv'] or 0 for v in tarde))} válidos), a última às {ult[11:16]}{dia}."
    )
    return vis, nota


def sombras(L: dict, X, topo: float, base: float, rotulo: bool = True) -> str:
    """Faixas das paradas nacionais e hachura da lacuna geral."""
    out = []
    for k, p in enumerate(paradas(L)):
        a, b = minutos(p["de_brt"]), minutos(p["ate_brt"])
        out.append(r(X(a), topo, X(b) - X(a), base - topo, SOMBRA))
        if rotulo:
            out.append(
                t(
                    (X(a) + X(b)) / 2,
                    topo + 18,
                    f"{num(p['minutos'], 0)} min",
                    13,
                    INK,
                    "middle",
                    "700",
                )
            )
            out.append(
                t((X(a) + X(b)) / 2, topo + 34, f"{k + 1}ª", 13, MUTED, "middle")
            )
    for lac in L["pausa_geral"]["lacunas"]:
        a, b = minutos(lac["de_brt"]), minutos(lac["ate_brt"])
        out.append(r(X(a), base - 26, X(b) - X(a), 26, "url(#hach-pausa)"))
    return "".join(out)


def eixo_x_horas(X, ini: float, fim: float, y: float, passo: int = 60) -> str:
    out = []
    m = math.ceil(ini / passo) * passo
    while m <= fim:
        out.append(ln(X(m), y, X(m), y + 6, MUTED))
        out.append(t(X(m), y + 22, rot_hora(m), 13, MUTED, "middle", mono=True))
        m += passo
    return "".join(out)


def eixo_y(Y, valores: list[float], esq: float, dir_: float, fmt) -> str:
    out = []
    for v in valores:
        out.append(ln(esq, Y(v), dir_, Y(v), GRADE))
        out.append(t(esq - 8, Y(v) + 5, fmt(v), 13, MUTED, "end", mono=True))
    return "".join(out)


def degraus(pts: list[tuple[float, float]], X, Y) -> str:
    d, prev = [], None
    for x, y in pts:
        if prev is None:
            d.append(f"M{X(x):.1f},{Y(y):.1f}")
        else:
            d.append(f"H{X(x):.1f}V{Y(y):.1f}")
        prev = y
    return "".join(d)


def _terceiros(v: dict) -> float:
    return v["cury"] + v["renan"] + v["caiado"] + v["outros"]


# ------------------------------------------------------------------ 01 placar


@registra("placar_candidatos")
def placar_candidatos(d, **_op) -> str:
    P = dado(d, "presidente")
    n = P["nacional"]
    cands = sorted(n["candidaturas"], key=lambda c: -c["votos"])
    top, resto = cands[:6], cands[6:]
    lider = top[0]
    tips = Tips()
    itens = []
    for i, c in enumerate(top):
        chave = (
            c["chave"]
            if c["chave"] != "outros"
            else "zema" if c["nome"] == "ZEMA" else "outros"
        )
        nome = NOME_CAND.get(chave) if chave != "outros" else nome_bonito(c["nome"])
        cor = COR_CAND.get(chave, "#8fb8aa")
        dif_v = lider["votos"] - c["votos"]
        k = tips.add(
            ficha(
                f"{nome} ({c['partido']})",
                f"nº {c['numero']}",
                [
                    ("Votos", inteiro(c["votos"])),
                    ("Válidos", pct(c["pct_validos"])),
                    (
                        "Diferença para o 1º",
                        (
                            "lidera"
                            if i == 0
                            else f"{inteiro(dif_v)} votos · {pp(c['pct_validos'] - lider['pct_validos'])}"
                        ),
                    ),
                    (
                        "Parcela do comparecimento",
                        pct(100 * c["votos"] / n["comparecimento"]),
                    ),
                ],
            )
        )
        itens.append((f"{nome} ({c['partido']})", cor, c, k))
    soma_resto = sum(c["votos"] for c in resto)
    rodape_svg = (
        f"Outros {len(resto)} candidatos somam {inteiro(soma_resto)} votos "
        f"({pct(100 * soma_resto / n['validos'])})."
    )
    titulo = "Presidente, 1º turno de 2026: os seis mais votados"
    desc = (
        f"{NOME_CAND['flavio']} {pct(n['pct']['flavio'])} e Lula {pct(n['pct']['lula'])} dos válidos; "
        "ninguém chegou a 50%."
    )
    larga = _placar_largo(itens, titulo, desc, rodape_svg)
    estreita = _placar_estreito(itens, titulo, desc, len(resto), soma_resto, n)
    legenda_ = (
        f"Votos e parcela dos válidos ({inteiro(n['validos'])} válidos, 100% das seções). "
        f"Diferença entre os dois primeiros: {inteiro(n['diferenca_votos'])} votos ({num(n['diferenca_pp'], 2)} ponto). "
        "Fonte: arquivo nacional final do TSE (presidente.json)."
    )
    return figura_html(
        "placar_candidatos",
        larga_estreita(larga, estreita),
        legenda_,
        tips,
        modo="full",
    )


def _placar_largo(itens: list, titulo: str, desc: str, rodape_svg: str) -> str:
    esq, topo, passo = 270, 46, 50
    h = topo + passo * len(itens) + 56
    X = escala(0, 52, esq, W - 220)
    out = [svg_abre(W, h, titulo, desc)]
    for v in ticks(0, 50, 5):
        out.append(ln(X(v), topo - 8, X(v), h - 46, GRADE))
        out.append(t(X(v), h - 24, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True))
    out.append(ln(X(50), topo - 14, X(50), h - 46, INK, 1.5, ' stroke-dasharray="6 4"'))
    out.append(
        t(
            X(50) + 8,
            topo - 18,
            "50% dos válidos: vitória no 1º turno",
            13,
            INK,
            weight="600",
        )
    )
    for i, (nome, cor, c, k) in enumerate(itens):
        y = topo + i * passo
        larg = X(c["pct_validos"]) - esq
        corpo = (
            area(0, y, W, passo)
            + r(esq, y + 9, larg, passo - 18, cor)
            + t(esq - 12, y + passo / 2 + 5, nome, 15, INK, "end", "600")
            + t(
                esq + larg + 10,
                y + passo / 2 + 5,
                f"{pct(c['pct_validos'])} · {inteiro(c['votos'])}",
                14,
                INK,
                mono=True,
                extra=HALO,
            )
        )
        out.append(hit(corpo, k, foco=True))
    out.append(t(esq, h - 4, rodape_svg, 13, MUTED))
    out.append("</svg>")
    return "".join(out)


def _placar_estreito(
    itens: list, titulo: str, desc: str, n_resto: int, soma_resto: int, n: dict
) -> str:
    """Versão de celular: nome e número numa linha, barra embaixo, eixo de 0 a 52%."""
    w, esq, topo, passo = 360, 4, 54, 58
    h = topo + passo * len(itens) + 64
    X = escala(0, 52, esq, w - 8)
    out = [svg_abre(w, h, titulo, desc)]
    for v in ticks(0, 50, 5):
        out.append(ln(X(v), topo - 6, X(v), h - 60, GRADE))
        anc = "start" if v == 0 else "middle"
        out.append(t(X(v), h - 42, f"{num(v, 0)}%", 13, MUTED, anc, mono=True))
    out.append(ln(X(50), topo - 12, X(50), h - 60, INK, 1.5, ' stroke-dasharray="6 4"'))
    out.append(t(X(50), topo - 18, "50%: vitória no 1º turno", 13, INK, "end", "600"))
    for i, (nome, cor, c, k) in enumerate(itens):
        y = topo + i * passo
        larg = X(c["pct_validos"]) - esq
        corpo = (
            area(0, y, w, passo)
            + t(esq, y + 16, nome, 15, INK, weight="600", extra=HALO)
            + t(w - 4, y + 16, pct(c["pct_validos"]), 15, INK, "end", "700", True, HALO)
            + r(esq, y + 24, larg, 14, cor)
            + t(esq, y + 53, f"{inteiro(c['votos'])} votos", 13, MUTED, mono=True)
        )
        out.append(hit(corpo, k))
    out.append(t(esq, h - 20, f"Outros {n_resto} candidatos somam", 13, MUTED))
    out.append(
        t(
            esq,
            h - 4,
            f"{inteiro(soma_resto)} votos ({pct(100 * soma_resto / n['validos'])}).",
            13,
            MUTED,
        )
    )
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ 02 acumulado


@registra("acumulado_noite")
def acumulado_noite(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    todas = versoes(L)
    vs, nota_corte = corta_noite(todas)
    ini, fim = 17 * 60, CORTE_NOITE
    esq, topo, base, dir_ = 70, 64, 420, W - 170
    h = base + 62
    X = escala(ini, fim, esq, dir_)
    vmax = max(v["flavio"] for v in todas) / 1e6
    Y = escala(0, math.ceil(vmax / 10) * 10, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "Votos acumulados por candidato ao longo da noite",
            "Cada degrau é uma versão nova do arquivo nacional; as faixas marcam as três paradas.",
        ),
        HACHURA,
        t(
            esq,
            22,
            "Faixa bege: arquivo nacional parado. Hachura: nenhum arquivo de resultado gerado pelo TSE.",
            13,
            MUTED,
        ),
    ]
    out.append(
        eixo_y(
            Y,
            ticks(0, math.ceil(vmax / 10) * 10, 6),
            esq,
            dir_,
            lambda v: f"{num(v, 0)} mi",
        )
    )
    out.append(sombras(L, X, topo, base))
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, ini, fim, base))
    series = [
        ("Flávio", FLAVIO, lambda v: v["flavio"]),
        ("Lula", LULA, lambda v: v["lula"]),
        ("Terceiros", OUTROS, _terceiros),
    ]
    finais = []
    for nome, cor, f in series:
        pts = [(minutos(v["gerado_brt"]), f(v) / 1e6) for v in vs]
        pts.append((fim, pts[-1][1]))
        out.append(
            f'<path d="{degraus(pts, X, Y)}" fill="none" stroke="{cor}" stroke-width="2.6"/>'
        )
        final = f(todas[-1]) / 1e6
        finais.append([Y(final), nome, cor, final])
    finais.sort()
    for i in range(1, len(finais)):
        finais[i][0] = max(finais[i][0], finais[i - 1][0] + 20)
    for y, nome, cor, val in finais:
        cor_t = cor if cor != OUTROS else OUTROS_TXT
        out.append(
            t(dir_ + 10, y + 5, f"{nome} {num(val, 2)} mi", 14, cor_t, weight="700")
        )
    tips = Tips()
    linhas = []
    for i, v in enumerate(vs):
        a = minutos(v["gerado_brt"])
        b = minutos(vs[i + 1]["gerado_brt"]) if i + 1 < len(vs) else fim
        linhas.append(
            [
                f"Versão de {v['gerado_brt'][11:19]}",
                f"lida às {v['capturado_brt'][11:19]}",
                f"{inteiro(v['st'])} ({num(v['pst'], 2)}%)",
                f"{inteiro(v['flavio'])} ({num(v['pct_flavio'], 2)}%)",
                f"{inteiro(v['lula'])} ({num(v['pct_lula'], 2)}%)",
                f"+{inteiro(v['d_vv'] or 0)}",
            ]
        )
        cruz = ln(
            X(a), topo, X(a), base, INK, 1, ' class="hit-cross" stroke-dasharray="3 3"'
        )
        out.append(
            hit(area(X(a), topo, max(X(b) - X(a), 1), base - topo) + cruz, f"r{i}")
        )
    tips.tabela(
        ["Versão", "Leitura", "Seções", "Flávio", "Lula", "Válidos no lote"],
        linhas,
        sub=1,
    )
    out.append(t(W - 4, h - 4, nota_corte, 13, MUTED, "end"))
    out.append("</svg>")
    par = paradas(L)
    lac = L["pausa_geral"]["lacunas"][0]
    legenda_ = (
        "Votos acumulados no arquivo nacional de presidente, versão a versão, pela hora em que o TSE gerou cada uma. "
        f"O arquivo parou {len(par)} vezes por mais de 8 minutos com seções represadas ("
        + ", ".join(f"{p['de_brt'][11:16]} a {p['ate_brt'][11:16]}" for p in par)
        + f"); de {lac['de_brt'][11:16]} a {lac['ate_brt'][11:16]} nenhum arquivo de resultado foi gerado. "
        "Fonte: linha_do_tempo.json."
    )
    return figura_html(
        "acumulado_noite", "".join(out), legenda_, tips, minw=900, dim=False
    )


# ------------------------------------------------------------------ 02 lotes


@registra("lotes_noite")
def lotes_noite(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    vs, nota_corte = corta_noite(versoes(L))
    ini, fim = 17 * 60, CORTE_NOITE
    esq, topo, base, dir_ = 80, 50, 400, W - 80
    h = base + 62
    X = escala(ini, fim, esq, dir_)
    vmax = max((v["d_vv"] or 0) for v in vs) / 1e6
    smax = max((v["d_st"] or 0) for v in vs)
    Yv = escala(0, math.ceil(vmax / 5) * 5, base, topo)
    Ys = escala(0, math.ceil(smax / 20000) * 20000, base, topo)
    Yp = escala(0, 100, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "O que cada versão do arquivo nacional acrescentou",
            "Barras: votos válidos (ou seções) somados por versão; linha dourada: seções apuradas em porcentagem.",
        ),
        HACHURA,
        sombras(L, X, topo, base, rotulo=False),
    ]
    gv = [
        eixo_y(
            Yv,
            ticks(0, math.ceil(vmax / 5) * 5, 5),
            esq,
            dir_,
            lambda v: f"{num(v, 0)} mi",
        )
    ]
    gs = [
        eixo_y(
            Ys,
            ticks(0, math.ceil(smax / 20000) * 20000, 5),
            esq,
            dir_,
            lambda v: f"{num(v / 1000, 0)} mil",
        )
    ]
    for v in vs:
        x = X(minutos(v["gerado_brt"]))
        y = base
        for parte, cor in (
            (v["d_flavio"] or 0, FLAVIO),
            (v["d_lula"] or 0, LULA),
            ((v["d_vv"] or 0) - (v["d_flavio"] or 0) - (v["d_lula"] or 0), OUTROS),
        ):
            alt = base - Yv(max(parte, 0) / 1e6)
            y -= alt
            gv.append(r(x - 1.4, y, 2.8, alt, cor))
        gs.append(r(x - 1.4, Ys(v["d_st"] or 0), 2.8, base - Ys(v["d_st"] or 0), INK))
    out.append(f'<g data-alt-show="validos">{"".join(gv)}</g>')
    out.append(f'<g data-alt-show="secoes" display="none">{"".join(gs)}</g>')
    pts = " ".join(f"{X(minutos(v['gerado_brt'])):.1f},{Yp(v['pst']):.1f}" for v in vs)
    out.append(
        f'<polyline points="{pts}" fill="none" stroke="{GOLD}" stroke-width="2.2"/>'
    )
    for v in (0, 50, 100):
        out.append(t(dir_ + 8, Yp(v) + 5, f"{v}%", 13, GOLD, mono=True))
    out.append(t(dir_ + 8, topo - 18, "seções", 13, GOLD, weight="600"))
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, ini, fim, base))
    maior = max(vs, key=lambda v: v["d_vv"] or 0)
    xm = X(minutos(maior["gerado_brt"]))
    out.append(
        '<g data-alt-show="validos" pointer-events="none">'
        + chip(
            xm + 10,
            Yv((maior["d_vv"] or 0) / 1e6) + 14,
            f"{maior['gerado_brt'][11:16]}: +{num((maior['d_vv'] or 0) / 1e6, 1)} mi de válidos numa versão",
            13,
        )
        + "</g>"
    )
    out.append(
        legenda([("Flávio", FLAVIO), ("Lula", LULA), ("Terceiros", OUTROS)], esq, 22)
    )
    tips = Tips()
    linhas = []
    for i, v in enumerate(vs):
        a = minutos(v["gerado_brt"])
        b = minutos(vs[i + 1]["gerado_brt"]) if i + 1 < len(vs) else fim
        dv = v["d_vv"] or 0
        linhas.append(
            [
                f"Versão de {v['gerado_brt'][11:19]}",
                f"{num(v['minutos_desde_anterior'] or 0, 1)} min depois da anterior",
                inteiro(v["d_st"] or 0),
                inteiro(dv),
                f"{num(v['lote_pct_flavio'], 1)}%" if dv else "s/d",
                f"{num(v['lote_pct_lula'], 1)}%" if dv else "s/d",
                f"{num(v['pst'], 2)}%",
            ]
        )
        out.append(
            hit(area(X(a) - 1.5, topo, max(X(b) - X(a), 3), base - topo), f"r{i}")
        )
    tips.tabela(
        [
            "Versão",
            "Intervalo",
            "Seções no lote",
            "Válidos no lote",
            "Flávio no lote",
            "Lula no lote",
            "Seções apuradas",
        ],
        linhas,
        sub=1,
    )
    out.append(t(W - 4, h - 4, nota_corte, 13, MUTED, "end"))
    out.append("</svg>")
    ctl = botoes(
        [("validos", "Válidos por versão"), ("secoes", "Seções por versão")],
        "validos",
        "Mostrar",
    )
    legenda_ = (
        f"Cada barra é uma versão nova do arquivo nacional. A maior, às {maior['gerado_brt'][11:16]}, trouxe "
        f"{inteiro(maior['d_vv'])} válidos e {inteiro(maior['d_st'])} seções de uma vez, depois da parada mais longa. "
        "Fonte: linha_do_tempo.json."
    )
    return figura_html(
        "lotes_noite", "".join(out), legenda_, tips, controles=ctl, minw=900, dim=False
    )


# ------------------------------------------------------------------ 02 e 03 divergência


@registra("divergencia_nacional")
def divergencia_nacional(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    D = L["divergencia_soma_ufs"]
    rows = tabela_linhas(D["minutos"])
    tot = D["secoes_total"]
    xs = [minutos(x["hora_brt"]) for x in rows]
    ini, fim = xs[0], xs[-1] + 1
    esq, topo, base, dir_ = 80, 50, 420, W - 230
    h = base + 50
    X = escala(ini, fim, esq, dir_)
    ymax = (
        math.ceil(max(x["andamento_br_st_visivel"] or 0 for x in rows) / tot * 10) * 10
    )
    ymin = math.floor(min(x["nacional_st_visivel"] for x in rows) / tot * 10) * 10
    Y = escala(ymin, ymax, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "Três contagens de seções, minuto a minuto, das 18:40 às 20:10",
            "Arquivo nacional, soma dos 27 arquivos de UF mais exterior e monitoramento nacional do próprio TSE.",
        ),
        HACHURA,
        sombras(L, X, topo, base, rotulo=False),
        eixo_y(Y, ticks(ymin, ymax, 5), esq, dir_, lambda v: f"{num(v, 0)}%"),
        ln(esq, base, dir_, base, INK, 1.2),
        eixo_x_horas(X, ini, fim, base, 10),
    ]
    series = [
        ("Arquivo nacional", INK, "nacional_st_visivel"),
        ("Soma das UFs", OUTROS, "soma_ufs_st_visivel"),
        ("Monitoramento do TSE", GOLD, "andamento_br_st_visivel"),
    ]
    finais = []
    for nome, cor, col in series:
        pts = [(minutos(x["hora_brt"]), 100 * (x[col] or 0) / tot) for x in rows]
        pts.append((fim, pts[-1][1]))
        out.append(
            f'<path d="{degraus(pts, X, Y)}" fill="none" stroke="{cor}" stroke-width="2.6"/>'
        )
        finais.append([Y(pts[-1][1]), nome, cor])
    finais.sort()
    for i in range(1, len(finais)):
        finais[i][0] = max(finais[i][0], finais[i - 1][0] + 20)
    for y, nome, cor in finais:
        out.append(
            t(
                dir_ + 10,
                y + 5,
                nome,
                14,
                OUTROS_TXT if cor == OUTROS else cor,
                weight="700",
            )
        )
    pior = max(rows, key=lambda x: x["diferenca_visivel"])
    xp = X(minutos(pior["hora_brt"]))
    out.append(
        ln(
            xp,
            Y(100 * pior["nacional_st_visivel"] / tot),
            xp,
            Y(100 * pior["soma_ufs_st_visivel"] / tot),
            INK,
            1.5,
            ' stroke-dasharray="2 3"',
        )
    )
    nota_pior = (
        f"{pior['hora_brt']}: UFs {inteiro(pior['diferenca_visivel'])} seções à frente"
    )
    y_pior = Y(100 * pior["soma_ufs_st_visivel"] / tot) - 12
    out.append(f'<g pointer-events="none">{chip(xp + 8, y_pior, nota_pior, 13)}</g>')
    tips = Tips()
    linhas = []
    for i, x in enumerate(rows):
        a = minutos(x["hora_brt"])
        linhas.append(
            [
                x["hora_brt"],
                f"versão nacional de {x['nacional_gerado_brt_visivel']}",
                f"{inteiro(x['nacional_st_visivel'])} ({num(100 * x['nacional_st_visivel'] / tot, 1)}%)",
                f"{inteiro(x['soma_ufs_st_visivel'])} ({num(100 * x['soma_ufs_st_visivel'] / tot, 1)}%)",
                f"{inteiro(x['andamento_br_st_visivel'] or 0)}",
                f"{inteiro(x['diferenca_visivel'])} seções",
            ]
        )
        cruz = ln(
            X(a), topo, X(a), base, INK, 1, ' class="hit-cross" stroke-dasharray="3 3"'
        )
        out.append(hit(area(X(a), topo, X(a + 1) - X(a), base - topo) + cruz, f"r{i}"))
    tips.tabela(
        [
            "Minuto",
            "Nacional",
            "Arquivo nacional",
            "Soma das UFs",
            "Monitoramento",
            "UFs à frente do nacional",
        ],
        linhas,
        sub=1,
        nota="contagem do que o coletor já tinha lido até o minuto",
    )
    out.append("</svg>")
    legenda_ = (
        f"Seções apuradas em três fontes do TSE, lidas pelo coletor. No pior minuto ({pior['hora_brt']}) a soma das UFs "
        f"estava {inteiro(pior['diferenca_visivel'])} seções à frente do arquivo nacional. Faixas: paradas do nacional; "
        "hachura: nenhum arquivo de resultado gerado. Fonte: linha_do_tempo.json (divergencia_soma_ufs)."
    )
    return figura_html(
        "divergencia_nacional", "".join(out), legenda_, tips, minw=900, dim=False
    )


# ------------------------------------------------------------------ 03 latência

GRUPOS_LAT = [
    ("presidente_br", "Nacional", INK),
    ("presidente_uf", "UF", FLAVIO),
    ("presidente_mu", "Município", OUTROS),
    ("presidente_zona", "Zona", GOLD),
]


@registra("latencia_hora")
def latencia_hora(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    lat = L["latencia"]["por_hora"]
    horas = sorted({x["hora_brt"] for x in lat})
    por = {(x["hora_brt"], x["grupo"]): x for x in lat}
    esq, topo, base, dir_ = 90, 50, 400, W - 150
    h = base + 56
    col = (dir_ - esq) / len(horas)

    def Xc(i):
        return esq + col * (i + 0.5)

    lo, hi = math.log10(20), math.log10(4000)
    Y = escala(lo, hi, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "Latência entre a geração no TSE e a leitura do coletor, por hora",
            "Mediana e percentil 95 dos segundos entre gerar e ler, em escala logarítmica, por nível do arquivo.",
        )
    ]
    for s, rot in (
        (30, "30 s"),
        (60, "1 min"),
        (120, "2 min"),
        (300, "5 min"),
        (600, "10 min"),
        (1800, "30 min"),
        (3600, "1 h"),
    ):
        out.append(ln(esq, Y(math.log10(s)), dir_, Y(math.log10(s)), GRADE))
        out.append(t(esq - 8, Y(math.log10(s)) + 5, rot, 13, MUTED, "end", mono=True))
    for i, hh in enumerate(horas):
        out.append(t(Xc(i), base + 24, hh[-3:], 13, MUTED, "middle", mono=True))
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    for chave, rot in (("p50_s", "p50"), ("p95_s", "p95")):
        g = []
        finais = []
        for grupo, nome, cor in GRUPOS_LAT:
            pts = [
                (Xc(i), Y(math.log10(max(por[(hh, grupo)][chave], 1))))
                for i, hh in enumerate(horas)
                if (hh, grupo) in por and por[(hh, grupo)].get(chave)
            ]
            if not pts:
                continue
            g.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" '
                f'stroke="{cor}" stroke-width="2.4"/>'
            )
            g.extend(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{cor}"/>'
                for x, y in pts
            )
            finais.append([pts[-1][1], pts[-1][0], nome, cor])
        # cada nome no fim da própria linha; só afasta na vertical os que
        # terminam na mesma hora
        finais.sort()
        for i in range(1, len(finais)):
            for j in range(i):
                if abs(finais[i][1] - finais[j][1]) < 1:
                    finais[i][0] = max(finais[i][0], finais[j][0] + 20)
        g.extend(
            t(
                x + 10,
                y + 5,
                nome,
                14,
                OUTROS_TXT if cor == OUTROS else cor,
                weight="700",
                extra=HALO,
            )
            for y, x, nome, cor in finais
        )
        mostra = "" if rot == "p50" else ' display="none"'
        out.append(f'<g data-alt-show="{rot}"{mostra}>{"".join(g)}</g>')
    tips = Tips()
    for i, hh in enumerate(horas):
        linhas = []
        for grupo, nome, _ in GRUPOS_LAT:
            x = por.get((hh, grupo))
            if x:
                linhas.append(
                    (
                        nome,
                        f"p50 {num(x['p50_s'], 0)} s · p95 {num(x['p95_s'], 0)} s · {inteiro(x['n'])}",
                    )
                )
        todos = por.get((hh, "todos"))
        if todos:
            linhas.append(
                (
                    "Todos os arquivos",
                    f"p50 {num(todos['p50_s'], 0)} s · {inteiro(todos['n'])} versões",
                )
            )
        k = tips.add(
            ficha(
                f"{hh[-3:]} de {hh[8:10]}/10",
                "segundos entre gerar e ler",
                linhas,
                "nível: mediana, percentil 95 e versões lidas",
            )
        )
        cruz = ln(
            Xc(i),
            topo,
            Xc(i),
            base,
            INK,
            1,
            ' class="hit-cross" stroke-dasharray="3 3"',
        )
        out.append(
            hit(area(esq + col * i, topo, col, base - topo) + cruz, k, foco=True)
        )
    out.append("</svg>")
    ctl = botoes([("p50", "Mediana"), ("p95", "Percentil 95")], "p50", "Latência")
    legenda_ = (
        "Tempo entre a hora em que o TSE gerou cada versão e a hora em que o coletor a leu, por hora e nível do arquivo, "
        "em escala logarítmica de 30 segundos a 1 hora (a ficha dá os valores em segundos). "
        "Inclui o intervalo de sondagem; mede o atraso total de quem acompanhava, não só o do tribunal. Fonte: linha_do_tempo.json."
    )
    return figura_html(
        "latencia_hora",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=820,
        dim=False,
    )


# ------------------------------------------------------------------ 14 coletor


@registra("auditoria_coletor")
def auditoria_coletor(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    lidas = {
        x["hora_brt"]: x["n"]
        for x in L["latencia"]["por_hora"]
        if x["grupo"] == "todos"
    }
    regr = {x["hora_brt"]: x for x in L["idg_regressivo"]["por_hora"]}
    horas = sorted(set(lidas) | set(regr))
    esq, dir_ = 100, W - 40
    t1, b1 = 60, 250
    t2, b2 = 350, 500
    h = b2 + 50
    col = (dir_ - esq) / len(horas)
    m1 = max(lidas.values())
    m2 = max(x["eventos"] for x in regr.values())
    Y1 = escala(0, math.ceil(m1 / 50000) * 50000, b1, t1)
    Y2 = escala(0, math.ceil(m2 / 500) * 500, b2, t2)
    out = [
        svg_abre(
            W,
            h,
            "O coletor da casa: versões lidas por hora e versões marcadas como regressivas",
            "Em cima, versões novas lidas por hora; embaixo, eventos marcados como regressivos, por classe.",
        ),
        t(
            esq,
            t1 - 22,
            "Versões novas lidas por hora (todos os cargos e níveis)",
            14,
            INK,
            weight="700",
        ),
        t(
            esq,
            t2 - 46,
            "Versões marcadas como regressivas pelo coletor, por classe",
            14,
            INK,
            weight="700",
        ),
        eixo_y(
            Y1,
            ticks(0, math.ceil(m1 / 50000) * 50000, 3),
            esq,
            dir_,
            lambda v: f"{num(v / 1000, 0)} mil",
        ),
        eixo_y(
            Y2, ticks(0, math.ceil(m2 / 500) * 500, 3), esq, dir_, lambda v: inteiro(v)
        ),
        legenda(
            [
                ("mais nova que todas as anteriores", OUTROS),
                ("cópia antiga de fato", "#b02f21"),
                ("mesma geração", MUTED),
            ],
            esq,
            t2 - 20,
            13,
        ),
    ]
    tips = Tips()
    for i, hh in enumerate(horas):
        x0 = esq + col * i
        bw = col * 0.62
        xb = x0 + (col - bw) / 2
        n = lidas.get(hh, 0)
        out.append(r(xb, Y1(n), bw, b1 - Y1(n), "#4a6560"))
        e = regr.get(hh, {})
        y = b2
        for chave, cor in (
            ("mais_nova_que_todas_as_anteriores", OUTROS),
            ("copia_antiga", "#b02f21"),
            ("mesma_geracao", MUTED),
        ):
            v = e.get(chave, 0)
            alt = b2 - Y2(v)
            y -= alt
            out.append(r(xb, y, bw, alt, cor))
        out.append(t(x0 + col / 2, b2 + 22, hh[-3:], 13, MUTED, "middle", mono=True))
        k = tips.add(
            ficha(
                f"{hh[-3:]} de {hh[8:10]}/10",
                "coletor da casa",
                [
                    ("Versões novas lidas", inteiro(n) if n else "s/d"),
                    ("Marcadas regressivas", inteiro(e.get("eventos", 0))),
                    (
                        "Mais novas que todas",
                        inteiro(e.get("mais_nova_que_todas_as_anteriores", 0)),
                    ),
                    ("Cópias antigas de fato", inteiro(e.get("copia_antiga", 0))),
                    ("Mesma geração", inteiro(e.get("mesma_geracao", 0))),
                ],
            )
        )
        out.append(
            hit(
                area(x0, t1, col, b2 - t1)
                + ln(
                    x0 + col / 2,
                    t1,
                    x0 + col / 2,
                    b2,
                    INK,
                    1,
                    ' class="hit-cross" stroke-dasharray="3 3"',
                ),
                k,
                foco=True,
            )
        )
    out.append(
        ln(esq, b1, dir_, b1, INK, 1.2) + ln(esq, b2, dir_, b2, INK, 1.2) + "</svg>"
    )
    tot = L["idg_regressivo"]["total_por_classe"]
    lac = L["pausa_geral"]["lacunas"][0]["leituras_no_intervalo"]
    legenda_ = (
        f"De {inteiro(sum(tot.values()))} versões que a regra do coletor marcou como regressivas, "
        f"{inteiro(tot.get('mais_nova_que_todas_as_anteriores', 0))} eram mais novas que todas as anteriores e só "
        f"{inteiro(tot.get('copia_antiga', 0))} eram cópias antigas. Na lacuna geral o coletor fez "
        f"{inteiro(sum(lac.values()))} leituras: {inteiro(lac.get('nao_modificado', 0))} sem modificação (304), "
        f"{inteiro(lac.get('ok', 0))} com corpo, {inteiro(lac.get('timeout', 0))} timeouts. Fonte: linha_do_tempo.json."
    )
    return figura_html(
        "auditoria_coletor", "".join(out), legenda_, tips, minw=820, dim=False
    )
