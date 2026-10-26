"""Figuras dos cards 1 a 9 da thread do 2º turno. SVG 1000 × 600, dados dos JSONs."""

from __future__ import annotations

from apuracao_2026.thread_base import (
    CINZA,
    FLAVIO,
    GOLD,
    GRID,
    INK,
    LULA,
    MONO,
    MUTED,
    PAPER,
    PAPER2,
    WHITE,
    caminho,
    circ,
    etiqueta,
    hachura,
    legenda,
    ln,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
)

from .thread_base import dado, hhmm_min, min_hhmm
from .thread_valores import noticia, serie_nacional

ROXO = "#6b4a92"
VERDE = "#0c7a72"


def _x(v, v0, v1, x0, x1):
    return x0 + (x1 - x0) * (v - v0) / (v1 - v0)


def _eixo_relogio(x0, x1, m0, m1, y, passo=30, size=15):
    """Marcas de hora para minutos do dia entre m0 e m1."""
    out = []
    m = (m0 // passo + (1 if m0 % passo else 0)) * passo
    while m <= m1:
        x = _x(m, m0, m1, x0, x1)
        out.append(ln(x, y, x, y + 6, MUTED, 1))
        out.append(t(x, y + 24, min_hhmm(m), size, MUTED, 500, "middle", MONO))
        m += passo
    return "".join(out)


# ------------------------------------------------------------------ 1 tese


def fig_tese() -> str:
    pv = dado("pesquisas_vs_urna")
    pr = dado("projecao_noite")
    urna = pr["observado_final"]["p_f_entre_os_dois"]
    p1 = pr["primeiro_ponto_com_projecao"]
    pontos = [x for x in pr["pontos"] if x["p_f_projetado"] is not None]
    c = pv["centrais"]
    transp = dado("projecao_pre_urna")["metodos"]["transportado_25_10"]
    v0, v1, x0, x1 = 45.0, 54.0, 260, 975

    def X(v):
        return _x(v, v0, v1, x0, x1)

    out = []
    for g in range(46, 55, 2):
        out.append(ln(X(g), 30, X(g), 500, GRID, 1, "3 5"))
        out.append(t(X(g), 525, f"{g}%", 15, MUTED, 500, "middle", MONO))
    out.append(ln(X(50), 22, X(50), 505, INK, 1.5, "6 4"))
    out.append(etiqueta(X(50), 18, "empate", 14, MUTED, PAPER, "middle", 500))
    out.append(t(x0, 560, "Parte de Flávio nos votos válidos", 16, MUTED, 600))
    linhas = [
        ("Projeção da casa", "na noite, 40 pontos"),
        ("20 pesquisas", "última onda de cada casa"),
        ("Centrais da casa", "véspera da eleição"),
        ("1º turno repetido", "sem pesquisa nenhuma"),
    ]
    ys = [95, 215, 330, 440]
    for (rot, sub), y in zip(linhas, ys, strict=True):
        out.append(t(x0 - 18, y, rot, 19, INK, 700, "end"))
        out.append(t(x0 - 18, y + 22, sub, 14, MUTED, 500, "end"))
    # projeção: faixa do primeiro ponto e trajetória
    y = ys[0] - 6
    out.append(
        r(
            X(p1["faixa90"][0]),
            y - 14,
            X(p1["faixa90"][1]) - X(p1["faixa90"][0]),
            28,
            "#c9d8ee",
            3,
        )
    )
    for p in pontos:
        out.append(circ(X(p["p_f_projetado"]), y, 4.5, FLAVIO, ' fill-opacity="1"'))
    out.append(
        etiqueta(
            X(p1["p_f_projetado"]) - 6,
            y - 24,
            f"{p1['hhmm']}: {pct(p1['p_f_projetado'])}",
            14,
            FLAVIO,
            PAPER,
            "end",
            700,
        )
    )
    # pesquisas
    y = ys[1] - 6
    vals = sorted(p["validos_do_total"]["flavio"] for p in pv["pesquisas"])
    for i, val in enumerate(vals):
        out.append(circ(X(val), y + (i % 3 - 1) * 12, 7, LULA if val < 50 else CINZA))
    out.append(
        etiqueta(
            X(max(vals)) + 12,
            y + 5,
            f"{len(vals) - sum(v < 50 for v in vals)} de {len(vals)} com Flávio à frente",
            14,
            INK,
            PAPER,
            "start",
            600,
        )
    )
    # centrais
    y = ys[2] - 6
    for rot, val, cor, dy, anc in (
        ("Projeção", c["projecao_arvor"]["validos"]["flavio"], GOLD, 36, "end"),
        ("Média", c["media_arvor"]["validos"]["flavio"], GOLD, -22, "start"),
    ):
        xx = X(val)
        out.append(
            f'<path d="M{xx:.1f},{y - 13} L{xx + 13:.1f},{y} L{xx:.1f},{y + 13} L{xx - 13:.1f},{y} Z" fill="{cor}"/>'
        )
        out.append(
            t(
                xx + (16 if anc == "start" else -16),
                y + dy,
                f"{rot} {pct(val)}",
                14,
                INK,
                600,
                anc,
            )
        )
    # transporte
    y = ys[3] - 6
    xx = X(transp["nacional_flavio_previsto"])
    out.append(circ(xx, y, 9, CINZA))
    out.append(
        t(
            xx + 16,
            y + 5,
            pct(transp["nacional_flavio_previsto"]),
            15,
            INK,
            600,
            "start",
            MONO,
        )
    )
    # urna
    xu = X(urna)
    out.append(r(xu - 2, 40, 4, 460, INK))
    out.append(etiqueta(xu, 492, f"urna {pct(urna)}", 16, WHITE, INK, "middle", 700))
    return svg(
        "".join(out),
        "Projeção da noite, pesquisas, centrais e repetição do 1º turno contra a urna",
    )


# ------------------------------------------------------------------ 2 placar


def fig_placar() -> str:
    p = dado("presidente")
    n = p["nacional"]
    out = []
    x0, x1 = 180, 980
    larg = x1 - x0
    # placar nacional
    xl = x0 + larg * n["pct_lula"] / 100
    out.append(r(x0, 20, xl - x0, 70, LULA, 4))
    out.append(r(xl, 20, x1 - xl, 70, FLAVIO, 4))
    out.append(t(x0 + 16, 66, f"Lula {pct(n['pct_lula'])}", 26, WHITE, 800))
    out.append(t(x1 - 16, 66, f"Flávio {pct(n['pct_flavio'])}", 26, WHITE, 800, "end"))
    out.append(t(x0 - 14, 52, "Brasil", 20, INK, 700, "end"))
    out.append(
        t(x0 - 14, 74, f"{num(n['secoes'])} seções", 13, MUTED, 500, "end", MONO)
    )
    out.append(ln(x0 + larg / 2, 12, x0 + larg / 2, 560, INK, 1.2, "5 4"))
    out.append(t(x0 + larg / 2, 586, "50%", 14, MUTED, 600, "middle", MONO))
    regs = {x["regiao"]: x for x in p["regioes"]}
    ordem = ["Nordeste", "Norte", "Sudeste", "Centro-Oeste", "Sul", "Exterior"]
    for i, nome in enumerate(ordem):
        g = regs[nome] if nome != "Exterior" else p["exterior"]
        y = 130 + i * 72
        xl = x0 + larg * g["pct_lula"] / 100
        destaque = nome == "Norte"
        h = 46
        out.append(r(x0, y, xl - x0, h, LULA, 3))
        out.append(r(xl, y, x1 - xl, h, FLAVIO, 3))
        out.append(
            t(x0 + 12, y + 30, pct(g["pct_lula"]), 18, WHITE, 700, "start", MONO)
        )
        out.append(
            t(x1 - 12, y + 30, pct(g["pct_flavio"]), 18, WHITE, 700, "end", MONO)
        )
        out.append(t(x0 - 14, y + 22, nome, 19, INK, 700 if destaque else 600, "end"))
        m = g["margem_lula_votos"]
        quem = "Lula" if m > 0 else "Flávio"
        out.append(
            t(x0 - 14, y + 42, f"{quem} +{num(abs(m))}", 13, MUTED, 500, "end", MONO)
        )
        if destaque:
            out.append(
                r(
                    x0 - 4,
                    y - 4,
                    larg + 8,
                    h + 8,
                    "none",
                    5,
                    f' stroke="{GOLD}" stroke-width="3"',
                )
            )
    return svg("".join(out), "Placar nacional e por região, com o Norte empatado")


# ------------------------------------------------------------------ 3 noite


def fig_noite() -> str:
    lt = dado("linha_do_tempo")
    sil = lt["pausas"]["silencio_geral"]
    serie = [x for x in serie_nacional() if x["min"] >= 0 and x["pct_flavio"]]
    m0, m1 = 0, max(330, 30 * (int(serie[-1]["min"]) // 30 + 1))
    x0, x1 = 70, 960
    y0, y1 = 40, 380
    v0, v1 = 40.0, 58.0

    def X(m):
        return _x(m, m0, m1, x0, x1)

    def Y(v):
        return _x(v, v0, v1, y1, y0)

    out = [hachura("pp-noite", CINZA, PAPER2)]
    a = hhmm_min(sil["ultimo_gerado_antes_brt"]) - 17 * 60
    b = hhmm_min(sil["primeiro_gerado_depois_brt"]) - 17 * 60
    out.append(r(X(a), y0, X(b) - X(a), y1 - y0, "url(#pp-noite)"))
    out.append(
        etiqueta(
            (X(a) + X(b)) / 2,
            y0 + 40,
            f"{num(sil['minutos'], 1)} min",
            22,
            INK,
            PAPER,
            "middle",
            800,
        )
    )
    out.append(
        etiqueta(
            (X(a) + X(b)) / 2,
            y0 + 70,
            "sem nenhum arquivo",
            15,
            INK,
            PAPER,
            "middle",
            600,
        )
    )
    for g in range(42, 58, 4):
        out.append(ln(x0, Y(g), x1, Y(g), GRID, 1, "3 5"))
        out.append(t(x0 - 10, Y(g) + 5, f"{g}%", 14, MUTED, 500, "end", MONO))
    out.append(ln(x0, Y(50), x1, Y(50), INK, 1.4, "6 4"))
    pts = [(X(x["min"]), Y(x["pct_flavio"])) for x in serie]
    out.append(caminho(pts, FLAVIO, 3.2))
    final = serie[-1]
    out.append(circ(pts[-1][0], pts[-1][1], 6, FLAVIO))
    out.append(
        etiqueta(
            pts[-1][0] - 14,
            pts[-1][1] + 30,
            f"final {pct(final['pct_flavio'])}",
            15,
            FLAVIO,
            PAPER,
            "end",
            700,
        )
    )
    acima = [x for x in serie if x["min"] > b and x["pct_flavio"] > 50]
    if acima:
        top = max(acima, key=lambda x: x["pct_flavio"])
        out.append(
            etiqueta(
                X(top["min"]),
                Y(top["pct_flavio"]) - 16,
                f"máximo {pct(top['pct_flavio'])}",
                14,
                INK,
                PAPER,
                "middle",
                600,
            )
        )
    out.append(
        t(
            x0,
            28,
            "Parte de Flávio nos válidos, cada versão do arquivo nacional",
            16,
            MUTED,
            600,
        )
    )
    # marcas do noticiário
    for padrao, rot in (
        (r"^Zanin, na Reclamação", "decisão do STF"),
        (r"TSE avisou as seções", "TSE avisa as seções"),
    ):
        it = noticia(padrao)
        hh = it["quando"][11:16]
        if "às " in it["resumo"] and "TSE avisou" in it["resumo"]:
            hh = it["resumo"].split("às ")[1][:5].replace("h", ":")
        m = hhmm_min(hh) - 17 * 60
        out.append(ln(X(m), y0, X(m), y1, GOLD, 1.6, "4 4"))
        out.append(
            etiqueta(
                X(m) + 6,
                y1 - 12 - (28 if "avisa" in rot else 0),
                f"{hh} {rot}",
                13,
                GOLD,
                PAPER,
                "start",
                700,
            )
        )
    # seções por versão
    yb0, yb1 = 430, 540
    lmax = max(x["lote_st"] for x in serie)
    for x in serie:
        h = (yb1 - yb0) * x["lote_st"] / lmax
        cor = LULA if (x["lote_pct_flavio"] or 50) < 50 else FLAVIO
        out.append(r(X(x["min"]) - 1.2, yb1 - h, 2.4, h, cor))
    out.append(
        t(
            x0,
            yb0 - 8,
            "Seções acrescentadas por versão (cor: quem levou mais votos no lote)",
            14,
            MUTED,
            600,
        )
    )
    out.append(ln(x0, yb1, x1, yb1, MUTED, 1))
    out.append(_eixo_relogio(x0, x1, 17 * 60 + m0, 17 * 60 + m1, yb1, 30, 14))
    return svg("".join(out), "A noite no arquivo nacional, com a parada de geração")


# ------------------------------------------------------------------ 4 prorrogação


def fig_prorrogacao() -> str:
    s = dado("secoes")
    he = s["reduzidos_thread"]["encerramento"]
    m0, m1 = he["inicio_min_do_dia"], he["fim_min_do_dia"]
    x0, x1 = 60, 980

    def X(m):
        return _x(m, m0, m1, x0, x1)

    out = []
    eventos = [
        (r"^Zanin, na Reclamação", "decisão do STF"),
        (r"suspendeu a totalização às 17h06 com", "TSE suspende a totalização"),
        (r"TSE avisou as seções", "TSE avisa as seções"),
        (r"Zanin reajustou a decisão", "decisão vale só para seção aberta"),
        (r"TRE-SP: mais de", "aviso oficial chega ao TRE-SP"),
    ]
    for i, (padrao, rot) in enumerate(eventos):
        it = noticia(padrao)
        hh = it["quando"][11:16]
        resumo = it["resumo"]
        for chave in ("avisou as seções às ", "às 18h", "totalização às "):
            if chave in resumo and rot != "decisão do STF":
                trecho = (
                    resumo.split(chave)[1]
                    if chave != "às 18h"
                    else "18h" + resumo.split("às 18h")[1]
                )
                hh = trecho[:5].replace("h", ":")
                break
        m = hhmm_min(hh)
        y = 40 + i * 44
        out.append(ln(X(m), y + 6, X(m), 330, GOLD, 1.4, "3 4"))
        out.append(circ(X(m), y, 6, GOLD))
        out.append(t(X(m) + 12, y + 5, f"{hh} {rot} ({it['veiculo']})", 15, INK, 600))
    # histograma do último voto
    yb0, yb1 = 300, 520
    passo = he["passo_min"]
    caixas = {int(k): c for k, c in he["caixas"].items()}
    cmax = max(caixas.values())
    largura = (x1 - x0) / ((m1 - m0) / passo)
    for k, c in caixas.items():
        h = max(2.0, (yb1 - yb0) * (c / cmax) ** 0.5)
        mm = m0 + k * passo
        cor = LULA if mm >= 19 * 60 else INK
        out.append(r(x0 + k * largura + 1, yb1 - h, largura - 2, h, cor, 1))
    pb = s["prorrogacao"]["brasil"]
    xm = X(hhmm_min(pb["encerramento_p50"]))
    out.append(
        etiqueta(
            xm + 60,
            yb0 - 4,
            f"último voto: mediana {pb['encerramento_p50']}, 99º percentil {pb['encerramento_p99']}",
            15,
            INK,
            PAPER,
            "start",
            700,
        )
    )
    x19 = X(19 * 60)
    out.append(r(x19 - 1.5, 30, 3, yb1 - 30, LULA))
    out.append(
        etiqueta(
            x19 - 8,
            yb0 + 80,
            f"depois de {min_hhmm(19 * 60)}: {pct(pb['pct_apos_1900'])} das seções",
            15,
            LULA,
            PAPER,
            "end",
            700,
        )
    )
    out.append(ln(x0, yb1, x1, yb1, MUTED, 1))
    out.append(_eixo_relogio(x0, x1, m0, m1, yb1, 30, 14))
    out.append(
        t(
            x0,
            588,
            f"Último voto de cada seção do país ({num(he['n'])} seções; altura em raiz quadrada)",
            14,
            MUTED,
            600,
        )
    )
    return svg("".join(out), "A decisão do STF e a hora do último voto nas seções")


# ------------------------------------------------------------------ 5 transmissão


def fig_transmissao() -> str:
    s = dado("secoes")
    por_uf = sorted(
        (u for u in s["prorrogacao"]["por_uf"] if u.get("recebimento_p50")),
        key=lambda u: hhmm_min(u["recebimento_p50"]),
    )
    m0, m1 = 16 * 60 + 45, 21 * 60
    x0, x1 = 60, 960

    def X(m):
        return _x(m, m0, m1, x0, x1)

    out = []
    y0 = 40
    passo = (530 - y0) / len(por_uf)
    out.append(r(X(17 * 60), y0 - 14, X(19 * 60) - X(17 * 60), 530 - y0 + 6, PAPER2))
    out.append(
        t(
            (X(17 * 60) + X(19 * 60)) / 2,
            y0 - 20,
            "prorrogação: urnas já fechadas, BU à espera",
            15,
            INK,
            700,
            "middle",
        )
    )
    for i, u in enumerate(por_uf):
        y = y0 + i * passo + passo / 2
        e = hhmm_min(u["emissao_p50"])
        p10 = hhmm_min(u["recebimento_p10"])
        p50 = hhmm_min(u["recebimento_p50"])
        out.append(t(x0 - 10, y + 5, u["uf"], 13, INK, 600, "end", MONO))
        out.append(ln(X(e), y, X(p50), y, CINZA, 1.4, "2 3"))
        out.append(r(X(p10), y - 4, X(p50) - X(p10), 8, FLAVIO, 2))
        out.append(circ(X(e), y, 4.5, INK))
        out.append(circ(X(p50), y, 5, FLAVIO))
    out.append(ln(X(19 * 60), y0 - 10, X(19 * 60), 536, LULA, 2))
    out.append(ln(x0, 536, x1, 536, MUTED, 1))
    out.append(_eixo_relogio(x0, x1, m0, m1, 536, 30, 13))
    out.append(
        legenda(
            [
                ("BU emitido (mediana)", INK),
                ("recebido pelo TSE: 10º percentil à mediana", FLAVIO),
            ],
            x0,
            594,
            14,
        )
    )
    return svg("".join(out), "Emissão do BU e recebimento pelo TSE, por UF")


# ------------------------------------------------------------------ 6 projeção


def fig_projecao() -> str:
    pr = dado("projecao_noite")
    pts = [x for x in pr["pontos"] if x["p_f_projetado"] is not None]
    final = pr["observado_final"]["p_f_entre_os_dois"]
    m0, m1 = pts[0]["min"] - 5, pts[-1]["min"] + 5
    x0, x1 = 70, 975
    v0, v1 = 45.0, 51.5
    y0, y1 = 40, 520

    def X(m):
        return _x(m, m0, m1, x0, x1)

    def Y(v):
        return _x(v, v0, v1, y1, y0)

    out = []
    for g in (46, 47, 48, 49, 50, 51):
        out.append(ln(x0, Y(g), x1, Y(g), GRID, 1, "3 5"))
        out.append(t(x0 - 10, Y(g) + 5, f"{g}%", 14, MUTED, 500, "end", MONO))
    out.append(r(x0, Y(51.5), x1 - x0, Y(50) - Y(51.5), "#e3ebf6"))
    out.append(
        t(x1 - 8, Y(51.5) + 22, "acima de 50%: Flávio à frente", 14, FLAVIO, 600, "end")
    )
    sup = [(X(x["min"]), Y(x["faixa90"][1])) for x in pts]
    inf = [(X(x["min"]), Y(x["faixa90"][0])) for x in pts]
    d = (
        "M"
        + " L".join(f"{a:.1f},{b:.1f}" for a, b in sup)
        + " L"
        + " L".join(f"{a:.1f},{b:.1f}" for a, b in reversed(inf))
        + " Z"
    )
    out.append(f'<path d="{d}" fill="#9fb8dc" fill-opacity="0.55"/>')
    out.append(
        caminho(
            [(X(x["min"]), Y(x["p_f_observado"])) for x in pts],
            CINZA,
            2.4,
            ' stroke-dasharray="5 4"',
        )
    )
    out.append(
        caminho([(X(x["min"]), Y(x["p_f_projetado"])) for x in pts], FLAVIO, 3.4)
    )
    out.append(ln(x0, Y(final), x1, Y(final), INK, 1.6))
    out.append(
        etiqueta(
            x0 + 8,
            Y(final) + 24,
            f"resultado final {pct(final)}",
            15,
            INK,
            PAPER,
            "start",
            700,
        )
    )
    out.append(ln(x0, Y(50), x1, Y(50), INK, 1.2, "6 4"))
    p1 = pts[0]
    out.append(
        etiqueta(
            X(p1["min"]) + 10,
            Y(p1["p_f_projetado"]) + 28,
            f"{p1['hhmm']}: projeção {pct(p1['p_f_projetado'])}",
            14,
            FLAVIO,
            PAPER,
            "start",
            700,
        )
    )
    top = max(pts, key=lambda x: x["p_f_observado"])
    out.append(
        etiqueta(
            X(top["min"]) + 10,
            Y(top["p_f_observado"]) - 10,
            f"contagem {pct(top['p_f_observado'])}",
            14,
            INK,
            PAPER,
            "start",
            600,
        )
    )
    out.append(ln(x0, y1, x1, y1, MUTED, 1))
    out.append(_eixo_relogio(x0, x1, 17 * 60 + m0, 17 * 60 + m1, y1, 30, 14))
    out.append(
        legenda(
            [
                ("projeção da casa", FLAVIO),
                ("faixa de 90%", "#9fb8dc"),
                ("já contado", CINZA),
            ],
            x0,
            590,
            14,
        )
    )
    return svg(
        "".join(out),
        "Projeção da casa a cada cinco minutos contra a contagem e o final",
    )


# ------------------------------------------------------------------ 7 cedo e tarde


def fig_cedo_tarde() -> str:
    d = dado("cedo_tarde")["decis_2t"]
    x0, x1 = 90, 960
    out = []
    passo = (x1 - x0) / len(d)

    def Y(v):
        return _x(v, 42, 62, 300, 30)

    for g in (44, 48, 52, 56, 60):
        out.append(ln(x0, Y(g), x1, Y(g), GRID, 1, "3 5"))
        out.append(t(x0 - 10, Y(g) + 5, f"{g}%", 14, MUTED, 500, "end", MONO))
    p2 = [(x0 + passo * (i + 0.5), Y(x["h2h_flavio"])) for i, x in enumerate(d)]
    p1 = [(x0 + passo * (i + 0.5), Y(x["t1_h2h_flavio"])) for i, x in enumerate(d)]
    out.append(caminho(p1, CINZA, 3, ' stroke-dasharray="6 4"'))
    out.append(caminho(p2, FLAVIO, 3.4))
    for (a, b), (c, e) in zip(p1, p2, strict=True):
        out.append(circ(a, b, 5, CINZA))
        out.append(circ(c, e, 5.5, FLAVIO))
    out.append(
        t(
            x0,
            22,
            "Parte de Flávio entre os dois, municípios em dez grupos pela hora em que fecharam",
            15,
            MUTED,
            600,
        )
    )
    out.append(
        legenda(
            [("2º turno", FLAVIO), ("1º turno, mesmos municípios", CINZA)], x0, 336, 14
        )
    )
    # barras do swing
    yb = 380

    def H(v):
        return abs(v) * 44

    out.append(ln(x0, yb, x1, yb, INK, 1.2))
    for i, x in enumerate(d):
        xx = x0 + passo * i
        h = H(x["swing_h2h_flavio_pp"])
        out.append(r(xx + 10, yb, passo - 20, h, LULA, 2))
        out.append(
            t(
                xx + passo / 2,
                yb + h + 20,
                sinal(x["swing_h2h_flavio_pp"]),
                15,
                INK,
                700,
                "middle",
                MONO,
            )
        )
        out.append(
            t(xx + passo / 2, 560, f"{x['decil']}º", 14, MUTED, 600, "middle", MONO)
        )
    out.append(t(x0 - 10, yb + 22, "mudança", 13, MUTED, 600, "end"))
    out.append(t(x0 - 10, yb + 38, "contra o 1º", 13, MUTED, 600, "end"))
    out.append(
        t(x0, 592, "Grupo, do que fechou cedo ao que fechou tarde", 13, MUTED, 500)
    )
    return svg(
        "".join(out), "Cedo e tarde: nível muda, mudança contra o 1º turno quase igual"
    )


# ------------------------------------------------------------------ 8 1T × 2T


def fig_turnos() -> str:
    ufs = sorted(dado("comparacao_1t")["ufs"], key=lambda u: u["swing_h2h_flavio_pp"])
    x0, x1 = 50, 990
    passo = (x1 - x0) / len(ufs)
    yb = 70
    out = [
        t(
            x0,
            30,
            "Mudança da parte de Flávio entre os dois, 1º para 2º turno, por UF (pontos)",
            16,
            MUTED,
            600,
        )
    ]
    out.append(ln(x0, yb, x1, yb, INK, 1.4))
    for g in (1, 2, 3, 4):
        y = yb + g * 110
        out.append(ln(x0, y, x1, y, GRID, 1, "3 5"))
        out.append(t(x0 - 8, y + 5, f"−{g}", 13, MUTED, 500, "end", MONO))
    for i, u in enumerate(ufs):
        v = u["swing_h2h_flavio_pp"]
        h = abs(v) * 110
        xx = x0 + i * passo
        out.append(r(xx + 4, yb, passo - 8, h, LULA, 2))
        out.append(
            t(xx + passo / 2, yb + h + 18, num(abs(v), 1), 12, INK, 700, "middle", MONO)
        )
        out.append(t(xx + passo / 2, yb - 10, u["uf"], 13, INK, 600, "middle", MONO))
    out.append(
        etiqueta(
            x1 - 6,
            560,
            f"{len(ufs)} de {len(ufs)} UFs: Flávio caiu em todas",
            18,
            WHITE,
            INK,
            "end",
            700,
        )
    )
    return svg("".join(out), "Queda da parte de Flávio em todas as UFs")


# ------------------------------------------------------------------ 9 abstenção


def fig_abstencao() -> str:
    a = dado("abstencao")
    ufs = sorted(a["ufs"], key=lambda u: u["arquivo_uf"]["delta_1t_pp"])
    x0, x1 = 50, 990
    passo = (x1 - x0) / len(ufs)
    y0 = 330
    esc = 30
    out = [
        t(
            x0,
            26,
            "Abstenção no 2º turno menos abstenção no 1º turno, por UF (pontos)",
            16,
            MUTED,
            600,
        )
    ]
    for g in (-3, -2, -1, 1, 2, 4, 6, 8):
        y = y0 - g * esc
        out.append(ln(x0, y, x1, y, GRID, 1, "3 5"))
        out.append(
            t(
                x0 - 8,
                y + 5,
                f"{'+' if g > 0 else '−'}{abs(g)}",
                12,
                MUTED,
                500,
                "end",
                MONO,
            )
        )
    out.append(ln(x0, y0, x1, y0, INK, 1.4))
    for i, u in enumerate(ufs):
        v = u["arquivo_uf"]["delta_1t_pp"]
        h = abs(v) * esc
        xx = x0 + i * passo
        cor = ROXO if v > 0 else VERDE
        if v > 0:
            out.append(r(xx + 4, y0 - h, passo - 8, h, cor, 2))
            out.append(
                t(xx + passo / 2, y0 - h - 8, num(v, 1), 12, INK, 700, "middle", MONO)
            )
            out.append(
                t(xx + passo / 2, y0 + 20, u["uf"], 13, INK, 600, "middle", MONO)
            )
        else:
            out.append(r(xx + 4, y0, passo - 8, h, cor, 2))
            out.append(t(xx + passo / 2, y0 - 8, u["uf"], 13, INK, 600, "middle", MONO))
    cont = dado("pesquisas_vs_urna")["hipoteses"]["contabilidade_entre_turnos"]
    out.append(
        etiqueta(
            x0 + 10,
            540,
            f"correlação com o quanto Flávio ficou abaixo do 1º turno: {sinal(cont['correlacao_variacao_abstencao_com_residuo'], 2)}",
            16,
            INK,
            PAPER,
            "start",
            700,
        )
    )
    out.append(legenda([("caiu", VERDE), ("subiu", ROXO)], x0 + 10, 580, 14))
    return svg("".join(out), "Variação da abstenção entre os turnos por UF")


__all__ = [
    "fig_abstencao",
    "fig_cedo_tarde",
    "fig_noite",
    "fig_placar",
    "fig_projecao",
    "fig_prorrogacao",
    "fig_tese",
    "fig_transmissao",
    "fig_turnos",
]
