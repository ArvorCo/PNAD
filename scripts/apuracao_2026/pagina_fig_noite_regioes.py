"""Figuras da noite por região (capítulo 2) e dos estados lentos (capítulo 3).

Dados: `noite_regioes.json` (soma dos 28 arquivos de UF, minuto a minuto, e
lotes de 5 minutos) e `lentidao_ufs.json` (marcos de 2022 e 2026 por UF). Tempo
em minutos desde 00:00 de 04/10 (Brasília); depois da meia-noite soma 1.440. A
hachura marca a lacuna em que nenhum arquivo de UF de presidente foi gerado,
lida do próprio JSON (`lacuna_da_soma`), nunca de horário digitado.
"""

from __future__ import annotations

import math

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    MUTED,
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
    legenda_html,
    ln,
    minutos,
    nome_bonito,
    pp,
    r,
    registra,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)
from .pagina_fig_noite import HACHURA, eixo_x_horas, eixo_y

REG = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Exterior"]
INI_NOITE = 17 * 60 + 15
FIM_NOITE = 24 * 60
# Texto de região sobre o papel: Norte e Nordeste um tom mais escuros que a barra
# (#0f7f5f e #b0562a ficam em 4,4:1 com letra de 13 px).
COR_REGIAO_TXT = dict(COR_REGIAO, Norte="#0b6650", Nordeste="#9a4520")
LINHA_LULA = "#7a1c12"  # parcela de Lula no lote: vinho, distinto da barra do Nordeste
MAIS_RAPIDO = "#0f7f5f"
MAIS_LENTO = "#7d5b00"
UF_2022 = "#8a8d86"


def _hachura(X, lac: dict, topo: float, base: float, rotulo: str = "") -> str:
    a, b = minutos(lac["de_brt"]), minutos(lac["ate_brt"])
    out = r(X(a), topo, X(b) - X(a), base - topo, "url(#hach-pausa)")
    if rotulo:
        out += t((X(a) + X(b)) / 2, topo + 16, rotulo, 13, INK, "middle", "700")
    return out


def _eixo(v: float, sufixo: str) -> str:
    return ("−" if v < 0 else "") + num(abs(v), 0) + sufixo


def _mi(v: float) -> str:
    return f"{num(v / 1e6, 2)} mi"


def _sinal_mi(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + _mi(abs(v))


# ------------------------------------------------------------------ 02 lotes


@registra("noite_regioes_lotes")
def noite_regioes_lotes(d, **_op) -> str:
    N = dado(d, "noite_regioes")
    # eixo até as 22h: depois disso os lotes somam pouco e só alongam o desenho
    fim = 22 * 60
    lts = [x for x in N["lotes_5min"] if INI_NOITE <= minutos(x["de_brt"]) < fim]
    tarde = [x for x in N["lotes_5min"] if minutos(x["de_brt"]) >= fim and x["vv"]]
    lac = N["lacuna_da_soma"]
    ne = N["nordeste"]
    minimo = ne["lote_minimo_validos"]
    esq, topo, base, dir_ = 80, 56, 430, W - 80
    h = base + 64
    X = escala(INI_NOITE, fim, esq, dir_)
    larg = X(INI_NOITE + 5) - X(INI_NOITE) - 1.6
    vmax = math.ceil(max(x["vv"] for x in lts) / 2e6) * 2
    smax = math.ceil(max(x["st"] for x in lts) / 10000) * 10000
    Yv = escala(0, vmax, base, topo)
    Ys = escala(0, smax, base, topo)
    Yp = escala(0, 100, base, topo)
    out = [
        svg_abre(
            W,
            h,
            "O que entrou na apuração a cada 5 minutos, por região",
            "Barras empilhadas: válidos (ou seções) de cada região no lote; linha: parcela de "
            "Lula dentro do lote, no eixo da direita.",
        ),
        HACHURA,
        _hachura(X, lac, topo, base, "pausa"),
    ]
    gv = [
        eixo_y(Yv, ticks(0, vmax, 5), esq, dir_, lambda v: f"{num(v, 0)} mi"),
    ]
    gs = [
        eixo_y(Ys, ticks(0, smax, 5), esq, dir_, lambda v: f"{num(v / 1000, 0)} mil"),
    ]
    for x in lts:
        x0 = X(minutos(x["de_brt"])) + 0.8
        yv, ys = base, base
        for reg in REG:
            parte = x["regioes"][reg]
            av = base - Yv(max(parte["vv"], 0) / 1e6)
            yv -= av
            gv.append(r(x0, yv, larg, av, COR_REGIAO[reg]))
            a_s = base - Ys(max(parte["st"], 0))
            ys -= a_s
            gs.append(r(x0, ys, larg, a_s, COR_REGIAO[reg]))
    out.append(f'<g data-alt-show="validos">{"".join(gv)}</g>')
    out.append(f'<g data-alt-show="secoes" display="none">{"".join(gs)}</g>')
    out.append(ln(esq, Yp(50), dir_, Yp(50), INK, 1, ' stroke-dasharray="5 4"'))
    trechos: list[list[tuple[float, float]]] = [[]]
    for x in lts:
        if x["vv"] >= minimo and x["pct_lula"] is not None:
            trechos[-1].append((X(minutos(x["de_brt"]) + 2.5), Yp(x["pct_lula"])))
        elif trechos[-1]:
            trechos.append([])
    pts = [pt for tr in trechos for pt in tr]
    for tr in trechos:
        trilha = " ".join(f"{a:.1f},{b:.1f}" for a, b in tr)
        out.append(
            f'<polyline points="{trilha}" fill="none" stroke="#ffffff" stroke-width="5"/>'
            f'<polyline points="{trilha}" fill="none" stroke="{LINHA_LULA}" stroke-width="2.4"/>'
        )
    out.extend(
        f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.6" fill="{LINHA_LULA}"/>'
        for a, b in pts
    )
    for v in (0, 25, 50, 75, 100):
        out.append(t(dir_ + 8, Yp(v) + 5, f"{v}%", 13, LINHA_LULA, mono=True))
    out.append(t(dir_ + 8, topo - 16, "Lula", 13, LINHA_LULA, weight="700"))
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, INI_NOITE, fim, base))
    if tarde:
        out.append(
            t(
                W - 4,
                h - 4,
                f"Eixo cortado às 22h: depois, {len(tarde)} lotes com válidos somaram "
                f"{inteiro(sum(x['vv'] for x in tarde))}, o último às {tarde[-1]['de_brt'][11:16]}.",
                13,
                MUTED,
                "end",
            )
        )
    desde = ne["maior_regiao_do_lote_desde"]
    if desde:
        xm = X(minutos(desde["de_brt"]))
        out.append(ln(xm, topo, xm, base, INK, 1.2, ' stroke-dasharray="2 3"'))
        txt = f"{desde['de_brt'][11:16]}: o Nordeste passa a ser a maior região de todo lote"
        cabe = xm + 8 + 0.53 * 13 * len(txt) + 12 <= dir_
        out.append(
            '<g pointer-events="none">'
            + chip(
                xm + 8 if cabe else xm - 8,
                topo - 14,
                txt,
                13,
                "start" if cabe else "end",
            )
            + "</g>"
        )
    tips = Tips()
    linhas = []
    for i, x in enumerate(lts):
        a = minutos(x["de_brt"])
        cel = []
        for reg in REG:
            p_ = x["regioes"][reg]
            if p_["vv"] > 0:
                cel.append(
                    f"{num(p_['parcela_vv_pct'], 1)}% dos válidos · Lula {num(p_['pct_lula'], 1)}%"
                )
            elif p_["st"] > 0:
                cel.append(f"{inteiro(p_['st'])} seções, sem válidos novos")
            else:
                cel.append("nada")
        linhas.append(
            [
                f"{x['de_brt'][11:16]} a {x['ate_brt'][11:16]}",
                f"{inteiro(x['st'])} seções",
                inteiro(x["vv"]),
                f"{num(x['pct_lula'], 1)}%" if x["pct_lula"] is not None else "s/d",
                f"{num(x['pct_flavio'], 1)}%" if x["pct_flavio"] is not None else "s/d",
                *cel,
            ]
        )
        out.append(hit(area(X(a), topo, X(a + 5) - X(a), base - topo), f"r{i}"))
    tips.tabela(
        ["Lote", "Seções", "Válidos", "Lula no lote", "Flávio no lote", *REG],
        linhas,
        sub=1,
        nota="soma dos 28 arquivos de UF pela hora de geração do TSE",
    )
    out.append("</svg>")
    ctl = botoes(
        [("validos", "Válidos por lote"), ("secoes", "Seções por lote")],
        "validos",
        "Mostrar",
    )
    leg = legenda_html(
        [(reg, COR_REGIAO[reg]) for reg in REG]
        + [("Lula no lote (eixo da direita)", LINHA_LULA)],
        "Região",
    )
    falta = ne["maior_do_que_faltava"]
    legenda_ = (
        "Cada barra soma o que os 28 arquivos de UF de presidente acrescentaram em 5 minutos, pela hora "
        f"em que o TSE gerou cada versão; a linha é a parcela de Lula nos válidos do lote (lotes com pelo "
        f"menos {num(minimo / 1000, 0)} mil válidos). A partir das {falta['hora_brt'][11:16]} o Nordeste já era a maior "
        f"parte do que faltava apurar ({num(falta['parcela_nordeste_pct'], 1)}%). Hachura: nenhum arquivo de UF "
        f"gerado de {lac['de_brt'][11:16]} a {lac['ate_brt'][11:16]}. Fonte: noite_regioes.json."
    )
    return figura_html(
        "noite_regioes_lotes",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=900,
        dim=False,
        apos=leg,
    )


# ------------------------------------------------------------------ 02 diferença


def _por_minuto(N: dict) -> tuple[list[dict], dict[str, dict[str, dict]]]:
    nac = tabela_linhas(N["nacional_por_minuto"])
    reg: dict[str, dict[str, dict]] = {}
    for x in tabela_linhas(N["minutos"]):
        reg.setdefault(x["hora_brt"], {})[x["regiao"]] = x
    return nac, reg


@registra("noite_regioes_diferenca")
def noite_regioes_diferenca(d, **_op) -> str:
    N = dado(d, "noite_regioes")
    nac, reg = _por_minuto(N)
    lac = N["lacuna_da_soma"]
    ini = minutos(N["lideranca"]["primeiro_minuto_com_votos"])
    linhas = [x for x in nac if ini <= minutos(x["hora_brt"]) <= FIM_NOITE and x["vv"]]
    esq, topo, base, dir_ = 80, 50, 440, W - 210
    h = base + 52
    X = escala(ini, FIM_NOITE, esq, dir_)
    series_v = {
        "Brasil": [(minutos(x["hora_brt"]), x["dif_votos"] / 1e6) for x in linhas]
    }
    series_p = {"Brasil": [(minutos(x["hora_brt"]), x["dif_pp"]) for x in linhas]}
    for rg in REG:
        series_v[rg], series_p[rg] = [], []
        for x in linhas:
            m, rr = minutos(x["hora_brt"]), reg[x["hora_brt"]][rg]
            dif = rr["flavio"] - rr["lula"]
            series_v[rg].append((m, dif / 1e6))
            series_p[rg].append((m, 100 * dif / x["vv"]))
    padr = [
        (minutos(x["hora_brt"]), x["dif_pp_peso_final"])
        for x in linhas
        if x["dif_pp_peso_final"] is not None
    ]
    out = [
        svg_abre(
            W,
            h,
            "Diferença Flávio menos Lula ao longo da noite e a parte de cada região",
            "Linha preta: diferença no país; linhas coloridas: quanto cada região soma a ela; "
            "abaixo de zero, a região puxa para Lula.",
        ),
        HACHURA,
        _hachura(X, lac, topo, base, "pausa"),
    ]
    cf = N["contribuicao_final"]
    vv_fim = sum(x["validos"] for x in N["totais"].values())
    fim_v = {r_: cf["regioes"][r_]["votos"] for r_ in REG}
    fim_v["Brasil"] = cf["diferenca_votos"]
    fim_p = {r_: 100 * fim_v[r_] / vv_fim for r_ in fim_v}
    for modo, series, fmt, extra in (
        ("votos", series_v, lambda v: _eixo(v, " mi"), []),
        ("pontos", series_p, lambda v: _eixo(v, " pp"), padr),
    ):
        vals = [v for s in series.values() for _, v in s] + [v for _, v in extra]
        passo = 2 if modo == "votos" else 5
        lo = math.floor(min(vals) / passo) * passo
        hi = math.ceil(max(vals) / passo) * passo
        Y = escala(lo, hi, base, topo)
        g = [
            eixo_y(Y, ticks(lo, hi, 6), esq, dir_, fmt),
            ln(esq, Y(0), dir_, Y(0), INK, 1.4),
        ]
        if extra:
            trilha = " ".join(f"{X(m):.1f},{Y(v):.1f}" for m, v in extra)
            g.append(
                f'<polyline points="{trilha}" fill="none" stroke="{INK}" stroke-width="2" '
                'stroke-dasharray="6 4"/>'
            )
        finais = []
        for nome, s in series.items():
            cor = INK if nome == "Brasil" else COR_REGIAO[nome]
            esp = 3.4 if nome == "Brasil" else 2.2
            tracejo = ' stroke-dasharray="3 3"' if nome == "Exterior" else ""
            trilha = " ".join(f"{X(m):.1f},{Y(v):.1f}" for m, v in s)
            g.append(
                f'<polyline points="{trilha}" fill="none" stroke="{cor}" stroke-width="{esp}"{tracejo}/>'
            )
            rot = (
                f"{nome} {_sinal_mi(fim_v[nome])}"
                if modo == "votos"
                else f"{nome} {pp(fim_p[nome], 2)}"
            )
            finais.append(
                [Y(s[-1][1]), rot, INK if nome == "Brasil" else COR_REGIAO_TXT[nome]]
            )
        if extra:
            finais.append([Y(extra[-1][1]) + 1, "peso final (tracejada)", INK])
        finais.sort()
        for i in range(1, len(finais)):
            finais[i][0] = max(finais[i][0], finais[i - 1][0] + 19)
        g.extend(
            t(dir_ + 10, y + 5, rot, 13, cor, weight="700") for y, rot, cor in finais
        )
        mostra = "" if modo == "votos" else ' display="none"'
        out.append(f'<g data-alt-show="{modo}"{mostra}>{"".join(g)}</g>')
    out.append(ln(esq, base, dir_, base, INK, 1.2))
    out.append(eixo_x_horas(X, ini, FIM_NOITE, base))
    tips = Tips()
    rows = []
    for i, x in enumerate(linhas):
        m = minutos(x["hora_brt"])
        cel = []
        for rg in REG:
            rr = reg[x["hora_brt"]][rg]
            dif = rr["flavio"] - rr["lula"]
            cel.append(f"{_sinal_mi(dif)} · {pp(100 * dif / x['vv'], 2)}")
        rows.append(
            [
                x["hora_brt"][11:16],
                f"{num(x['pst'], 1)}% das seções",
                f"{_sinal_mi(x['dif_votos'])} · {pp(x['dif_pp'], 2)}",
                (
                    pp(x["dif_pp_peso_final"], 2)
                    if x["dif_pp_peso_final"] is not None
                    else "s/d"
                ),
                *cel,
            ]
        )
        cruz = ln(
            X(m), topo, X(m), base, INK, 1, ' class="hit-cross" stroke-dasharray="3 3"'
        )
        out.append(
            hit(area(X(m) - 0.5, topo, X(m + 1) - X(m), base - topo) + cruz, f"r{i}")
        )
    tips.tabela(
        ["Minuto", "Seções", "Diferença no país", "Com o peso final", *REG],
        rows,
        sub=1,
        nota="Flávio menos Lula; em pontos, sobre os válidos já apurados no país",
    )
    out.append("</svg>")
    ctl = botoes(
        [("votos", "Milhões de votos"), ("pontos", "Pontos dos válidos apurados")],
        "votos",
        "Escala",
    )
    dec = N["decomposicao"]
    c = N["contribuicao_final"]["regioes"]
    legenda_ = (
        "Flávio menos Lula na soma dos arquivos de UF, minuto a minuto, e a parte de cada região. "
        f"No fim, o Nordeste tira {_mi(-c['Nordeste']['votos'])} de Flávio; Sudeste ({_sinal_mi(c['Sudeste']['votos'])}), "
        f"Sul ({_sinal_mi(c['Sul']['votos'])}), Centro-Oeste ({_sinal_mi(c['Centro-Oeste']['votos'])}) e Norte "
        f"({_sinal_mi(c['Norte']['votos'])}) somam a favor dele. Em pontos, a tracejada repõe cada região no peso final "
        f"dos válidos: no pico das {dec['pico_brt'][11:16]} a vantagem medida era {pp(dec['pico_pp'], 2)} e, com o peso "
        f"final, {pp(dec['pico_peso_final_pp'], 2)}. Fonte: noite_regioes.json."
    )
    return figura_html(
        "noite_regioes_diferenca",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=900,
        dim=False,
    )


# ------------------------------------------------------------------ 03 lentidão


PAUSA_CSS = "repeating-linear-gradient(45deg,#c9b27a 0 3px,#efe6cf 3px 7px)"


def _cel(h: str | None, ano: str) -> str:
    """Hora curta para célula de ficha: '02:59 (+1)' vira '05/10 02:59'."""
    if not h:
        return "s/d"
    base, _, resto = h.partition(" (+")
    if not resto:
        return base
    d0 = 4 if ano == "2026" else 2
    return f"{d0 + int(resto.rstrip(')')):02d}/10 {base}"


def _dia(h: str | None, ano: str) -> str:
    """'02:59 (+1)' vira '02:59 de 05/10' em 2026 e '02:59 de 03/10' em 2022."""
    if not h:
        return "s/d"
    base, _, resto = h.partition(" (+")
    if not resto:
        return base
    d0 = 4 if ano == "2026" else 2
    return f"{base} de {d0 + int(resto.rstrip(')')):02d}/10"


def _marcos_linhas(h26: dict, h22: dict) -> list[tuple[str, str]]:
    linhas = [("Seções", "2026 · 2022")]
    for k in ("50", "90", "99", "100"):
        linhas.append(
            (f"{k}%", f"{_cel(h26.get(k), '2026')} · {_cel(h22.get(k), '2022')}")
        )
    return linhas


def _fim_ficha(u: dict) -> tuple[list[tuple[str, str]], str]:
    """Linhas curtas da ficha de uma UF e a nota com os últimos municípios."""
    linhas = _marcos_linhas(
        u["horas"]["2026_totalizado"], u["horas"]["2022_totalizado"]
    )
    rec = u["horas"]["2026_recebido"]
    linhas.append(
        (
            "Recebido 99%",
            (
                f"{_cel(rec.get('99'), '2026')} em 2026"
                if rec
                else (
                    f"coleta parcial, {num(u['recebido_2026']['cobertura_pct'], 0)}%"
                    if u["recebido_2026"]["cobertura_pct"]
                    else "seções ainda não coletadas"
                )
            ),
        )
    )
    c = u["cauda_min"]
    if c["2026"] is not None and c["2022"] is not None:
        linhas.append(("99% a 100%", f"{num(c['2026'], 0)} · {num(c['2022'], 0)} min"))
    partes = []
    for ano in ("2026", "2022"):
        ult = u[f"ultimos_municipios_{ano}"][:2]
        if ult:
            partes.append(
                f"Últimos em {ano}: "
                + "; ".join(
                    f"{nome_bonito(x['nome'])}, {_dia(x['hora'], ano)}" for x in ult
                )
            )
    return linhas, ". ".join(partes) + ("." if partes else "")


def _x_marco(v: float) -> float:
    return 17 * 60 + v


@registra("lentidao_ufs_2022_2026")
def lentidao_ufs_2022_2026(d, **_op) -> str:
    T = dado(d, "lentidao_ufs")
    ufs = T["ufs"]
    lentas = set(T["resumo_99"]["classificacao"]["lentas_nos_dois"])
    pz = T["pausa"]["geracao_uf"]
    esq, topo, passo = 210, 40, 25
    h = topo + passo * len(ufs) + 44
    ini, fim = 17 * 60 + 30, 24 * 60
    X = escala(ini, fim, esq, W - 70)
    out = [
        svg_abre(
            W,
            h,
            "Hora em que cada UF chegou a 99% das seções totalizadas, 2022 e 2026",
            "Círculo vazado: 1º turno de 2022; cheio: 2026; UFs na ordem de 2026.",
        ),
        HACHURA,
    ]
    a, b = minutos(f"2026-10-04 {pz['de']}"), minutos(f"2026-10-04 {pz['ate']}")
    out.append(r(X(a), topo - 8, X(b) - X(a), passo * len(ufs) + 8, "url(#hach-pausa)"))
    out.append(
        t((X(a) + X(b)) / 2, topo - 14, "pausa do TSE", 13, INK, "middle", "700")
    )
    for m in range(18 * 60, fim + 1, 60):
        out.append(ln(X(m), topo - 6, X(m), h - 34, GRADE))
        out.append(t(X(m), h - 14, f"{m // 60:02d}h", 13, MUTED, "middle", mono=True))
    tips = Tips()
    grupos: dict[str, list[str]] = {k: [] for k in ("50", "90", "99")}
    for i, u in enumerate(ufs):
        y = topo + i * passo + passo / 2
        fuso = "" if u["fuso_utc"] == -3 else f" UTC−{abs(u['fuso_utc'])}"
        peso = "700" if u["uf"] in lentas else None
        out.append(t(esq - 12, y + 5, f"{u['nome']}{fuso}", 14, INK, "end", peso))
        for k, g in grupos.items():
            v22 = u["marcos"]["2022_totalizado"].get(k)
            v26 = u["marcos"]["2026_totalizado"].get(k)
            if v22 is None or v26 is None:
                continue
            x22, x26 = X(_x_marco(v22)), X(_x_marco(v26))
            cor = MAIS_RAPIDO if v26 <= v22 else MAIS_LENTO
            g.append(
                ln(x22, y, x26, y, cor, 3.5)
                + f'<circle cx="{x22:.1f}" cy="{y:.1f}" r="6" fill="#ffffff" '
                f'stroke="{UF_2022}" stroke-width="2.4"/>'
                + f'<circle cx="{x26:.1f}" cy="{y:.1f}" r="6" fill="{INK}"/>'
            )
        linhas_f, nota_f = _fim_ficha(u)
        kf = tips.add(
            ficha(
                u["nome"],
                f"{u['regiao']} · {inteiro(u['secoes_2026'])} seções",
                linhas_f,
                nota_f,
            )
        )
        out.append(hit(area(esq - 200, y - passo / 2, W - esq + 130, passo), kf))
    for k, g in grupos.items():
        mostra = "" if k == "99" else ' display="none"'
        out.append(
            f'<g data-alt-show="m{k}" pointer-events="none"{mostra}>{"".join(g)}</g>'
        )
    out.append("</svg>")
    ctl = botoes(
        [("m50", "50%"), ("m90", "90%"), ("m99", "99%")],
        "m99",
        "Marco das seções",
    )
    leg = legenda_html(
        [
            ("2022 (círculo vazado)", UF_2022),
            ("2026 (círculo cheio)", INK),
            ("mais cedo em 2026", MAIS_RAPIDO),
            ("mais tarde em 2026", MAIS_LENTO),
            ("pausa do TSE", PAUSA_CSS),
        ],
        "Nome em negrito: UF lenta nos dois anos",
    )
    nac = T["nacional"]
    res = T["resumo_99"]
    n_rap = res["mais_rapidas_em_2026"]
    quantas = "as 27 UFs" if n_rap == 27 else f"{n_rap} de 27 UFs"
    legenda_ = (
        f"Hora de Brasília em que cada UF passou de 50%, 90% ou 99% das seções totalizadas. No país, 99% às "
        f"{nac['horas_2026']['99']} em 2026 e às {nac['horas_2022']['99']} em 2022; {quantas} chegaram aos 99% "
        "mais cedo. Hachura: pausa em que nenhum arquivo de UF foi gerado. Régua de 2022: primeira totalização "
        "parcial de cada seção (TSE, dados abertos). Fonte: lentidao_ufs.json."
    )
    return figura_html(
        "lentidao_ufs_2022_2026",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=860,
        apos=leg,
        foco=_foco_99(ufs, X),
    )


def _foco_99(ufs: list[dict], X) -> tuple[float, float]:
    """Faixa dos marcos de 99% nos dois anos: o que a rolagem mostra ao abrir no celular."""
    xs = [
        X(_x_marco(u["marcos"][ano]["99"]))
        for u in ufs
        for ano in ("2022_totalizado", "2026_totalizado")
        if u["marcos"][ano].get("99") is not None
    ]
    return (min(xs) - 10, max(xs) + 10)


def _paineis(T: dict) -> list[dict]:
    nac = T["nacional"]
    saida = [
        {
            "uf": "BR",
            "nome": "Brasil, sem o exterior",
            "c26": nac["curva_2026"],
            "c22": nac["curva_2022"],
            "h26": nac["horas_2026"],
            "h22": nac["horas_2022"],
            "u": None,
        }
    ]
    saida += [
        {
            "uf": u["uf"],
            "nome": u["nome"],
            "c26": u["curva_2026"],
            "c22": u["curva_2022"],
            "h26": u["horas"]["2026_totalizado"],
            "h22": u["horas"]["2022_totalizado"],
            "u": u,
        }
        for u in T["ufs"]
    ]
    return saida


@registra("lentidao_marcos")
def lentidao_marcos(d, **_op) -> str:
    T = dado(d, "lentidao_ufs")
    grade = T["grade_min"]
    pz = T["pausa"]["geracao_uf"]
    paineis = _paineis(T)
    cols, cw, ch = 6, 176, 132
    pad_x, pad_top, pad_bot = 8, 40, 24
    topo0 = 10
    h = topo0 + math.ceil(len(paineis) / cols) * (ch + 18) + 10
    out = [
        svg_abre(
            W,
            h,
            "Seções totalizadas ao longo da noite, por UF: 2026 contra 2022",
            "Pequenos múltiplos, das 17h à 01h; linha cheia 2026, tracejada 2022; UFs na "
            "ordem do 99% de 2026.",
        ),
        HACHURA,
    ]
    tips = Tips()
    a_p = minutos(f"2026-10-04 {pz['de']}") - 17 * 60
    b_p = minutos(f"2026-10-04 {pz['ate']}") - 17 * 60
    for i, p in enumerate(paineis):
        x0 = 30 + (i % cols) * (cw + 3)
        y0 = topo0 + (i // cols) * (ch + 18)
        X = escala(grade[0], grade[-1], x0 + pad_x, x0 + cw - pad_x)
        Y = escala(0, 100, y0 + ch - pad_bot, y0 + pad_top)
        g = [
            r(x0, y0, cw, ch, "#fbf8f1", f' stroke="{GRADE}"'),
            r(X(a_p), Y(100), X(b_p) - X(a_p), Y(0) - Y(100), "url(#hach-pausa)"),
            ln(X(grade[0]), Y(50), X(grade[-1]), Y(50), GRADE),
            ln(X(grade[0]), Y(0), X(grade[-1]), Y(0), INK, 1),
        ]
        g.extend(ln(X(m), Y(0), X(m), Y(0) + 4, MUTED) for m in (60, 180, 300, 420))
        if i == 0:
            # o primeiro painel (país) leva a escala; os demais repetem a mesma
            g.extend(
                t(X(m), Y(0) + 17, rot, 13, MUTED, "middle", mono=True)
                for m, rot in ((60, "18h"), (180, "20h"), (300, "22h"), (420, "0h"))
            )
            g.append(t(X(grade[-1]), Y(50) - 4, "50%", 13, MUTED, "end", mono=True))
        for serie, cor, esp, tr in (
            (p["c22"], UF_2022, 2.2, ' stroke-dasharray="5 3"'),
            (p["c26"], INK, 2.4, ""),
        ):
            trilha = " ".join(
                f"{X(m):.1f},{Y(v):.1f}"
                for m, v in zip(grade, serie, strict=True)
                if v is not None
            )
            g.append(
                f'<polyline points="{trilha}" fill="none" stroke="{cor}" '
                f'stroke-width="{esp}"{tr}/>'
            )
        g.append(t(x0 + 8, y0 + 18, p["uf"], 15, INK, weight="800"))
        h26 = (p["h26"].get("99") or "s/d")[:5]
        h22 = (p["h22"].get("99") or "s/d")[:5]
        g.append(t(x0 + cw - 8, y0 + 18, f"99%: {h26}", 13, INK, "end", mono=True))
        g.append(t(x0 + cw - 8, y0 + 33, f"2022: {h22}", 13, MUTED, "end", mono=True))
        linhas_f, nota_f = _marcos_linhas(p["h26"], p["h22"]), ""
        if p["u"]:
            linhas_f, nota_f = _fim_ficha(p["u"])
        k = tips.add(ficha(p["nome"], p["uf"], linhas_f, nota_f))
        out.append(hit("".join(g) + area(x0, y0, cw, ch), k, foco=True))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("2026, arquivo da UF (linha cheia)", INK),
            ("2022, primeira totalização (tracejada)", UF_2022),
            ("pausa do TSE em 2026", PAUSA_CSS),
        ],
        "Cada painel: 17h a 01h, 0 a 100% das seções (escala no primeiro)",
    )
    legenda_ = (
        "Parcela das seções totalizadas, de 5 em 5 minutos desde as 17h, em 2026 (arquivo da UF, hora de geração) "
        "e em 2022 (primeira totalização parcial de cada seção). O primeiro painel é o país sem o exterior; os "
        "demais seguem a ordem do 99% de 2026. Fonte: lentidao_ufs.json."
    )
    return figura_html(
        "lentidao_marcos", "".join(out), legenda_, tips, minw=980, apos=leg
    )
