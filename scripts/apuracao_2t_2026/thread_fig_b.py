"""Figuras dos cards 10 a 18 da thread do 2º turno. SVG 1000 × 600, dados dos JSONs."""

from __future__ import annotations

from itertools import pairwise

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
    circ,
    etiqueta,
    legenda,
    ln,
    num,
    pct,
    r,
    sinal,
    svg,
    t,
)

from . import secoes_linhas
from .pagina_cap_boletins import NAO_FOI_AO_AR, boletins
from .thread_base import dado, tabela

ROXO = "#6b4a92"
VERDE = "#0c7a72"


def _x(v, v0, v1, x0, x1):
    return x0 + (x1 - x0) * (v - v0) / (v1 - v0)


def _barra(out, y, rot, valor, n, x0, x1, vmax, cor):
    def X(v):
        return _x(v, 0, vmax, x0, x1)

    out.append(t(x0 - 14, y + 6, rot, 16, INK, 600, "end"))
    out.append(r(x0, y - 12, X(valor) - x0, 24, cor, 3))
    out.append(
        t(
            X(valor) + 10,
            y + 6,
            f"{pct(valor)} ({num(n)} seções)",
            15,
            INK,
            700,
            "start",
            MONO,
        )
    )


# ------------------------------------------------------------------ 10 comparecimento


def fig_comparecimento() -> str:
    s = dado("secoes")
    linhas = [x for x in tabela(secoes_linhas.bloco(s)) if x["delta_pp"] is not None]
    dc = s["agregados"]["brasil"]["delta_comp"]
    out = [
        t(
            60,
            24,
            f"Comparecimento da seção no 2º turno menos no 1º, todas as {num(len(linhas))} seções comparáveis",
            15,
            MUTED,
            600,
        )
    ]
    v0, v1, x0, x1 = -15, 15, 60, 980
    y0, y1 = 40, 290
    caixas = {}
    for x in linhas:
        k = int((min(max(x["delta_pp"], v0), v1 - 0.01) - v0) // 1)
        caixas[k] = caixas.get(k, 0) + 1
    cmax = max(caixas.values())
    larg = (x1 - x0) / (v1 - v0)
    for k, c in caixas.items():
        h = (y1 - y0) * c / cmax
        v = v0 + k
        cor = LULA if v >= 5 else (CINZA if v < -5 else "#9aa3ae")
        out.append(r(x0 + k * larg + 1, y1 - h, larg - 2, h, cor, 1))
    out.append(ln(x0, y1, x1, y1, MUTED, 1))
    for g in range(-15, 16, 5):
        x = _x(g, v0, v1, x0, x1)
        out.append(
            t(
                x,
                y1 + 22,
                f"{'+' if g > 0 else '−' if g < 0 else ''}{abs(g)}",
                14,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
    xm = _x(dc["media"], v0, v1, x0, x1)
    out.append(ln(xm, y0, xm, y1, INK, 2))
    out.append(
        etiqueta(
            xm + 8,
            y0 + 18,
            f"média +{num(dc['media'], 2)} pp",
            15,
            INK,
            PAPER,
            "start",
            700,
        )
    )
    vmax = 12
    n = dc["n"]
    _barra(
        out,
        370,
        "+5 pp contra a própria seção",
        dc["pct_5_mais"],
        s["agregados"]["brasil"]["sinais"]["delta"],
        330,
        760,
        vmax,
        LULA,
    )
    _barra(
        out,
        440,
        "+5 pp acima do município",
        100 * dc["n_relativo_5_mais"] / n,
        dc["n_relativo_5_mais"],
        330,
        760,
        vmax,
        ROXO,
    )
    _barra(
        out,
        510,
        "−5 pp contra a própria seção",
        dc["pct_menos_5"],
        round(dc["pct_menos_5"] * n / 100),
        330,
        760,
        vmax,
        CINZA,
    )
    out.append(
        t(
            330,
            572,
            "Parcela das seções do país, contagem direta no banco completo",
            14,
            MUTED,
            600,
        )
    )
    return svg("".join(out), "Comparecimento por seção contra o 1º turno")


# ------------------------------------------------------------------ 11 biometria


def fig_biometria() -> str:
    s = dado("secoes")
    ps = s["agregados"]["brasil"]["persistencia"]
    jag = max(dado("secoes_ranking")["secoes"], key=lambda x: x["salto_bio_pp"])
    out = []
    x0, x1 = 60, 560
    for i, (rot, n, ja) in enumerate(
        (
            ("Sem biometria cadastrada", ps["sem_bio_n"], ps["sem_bio_ja_no_1t"]),
            (
                "Liberados pelo ano de nascimento",
                ps["ano_nasc_n"],
                ps["ano_nasc_ja_no_1t"],
            ),
        )
    ):
        y = 80 + i * 170
        out.append(t(x0, y - 18, f"{rot}: {n} seções com sinal", 18, INK, 700))
        xa = _x(ja, 0, n, x0, x1)
        out.append(r(x0, y, xa - x0, 48, CINZA, 3))
        out.append(r(xa, y, x1 - xa, 48, LULA, 3))
        out.append(t(x0 + 12, y + 31, f"{ja} já no 1º turno", 16, WHITE, 700))
        if x1 - xa > 60:
            out.append(t(x1 - 10, y + 31, f"{n - ja} novas", 16, WHITE, 700, "end"))
        else:
            out.append(t(x1 + 10, y + 31, f"{n - ja} novas", 16, INK, 700))
    out.append(
        t(
            x0,
            470,
            "A biometria baixa é do cadastro, não do dia: a maioria já tinha o sinal no 1º turno.",
            15,
            MUTED,
            600,
        )
    )
    # Jaguaribe
    ox, ow = 670, 310
    out.append(r(ox - 20, 30, ow + 40, 520, PAPER2, 8))
    out.append(
        t(
            ox,
            64,
            f"{jag['municipio']} ({jag['uf']}), zona {jag['zona']}, seção {jag['secao']}",
            16,
            INK,
            700,
        )
    )
    out.append(t(ox, 88, "liberados pelo ano de nascimento", 14, MUTED, 600))

    def Y(v):
        return _x(v, 0, 100, 400, 120)

    out.append(ln(ox + 40, Y(0), ox + 40, Y(100), GRID, 1))
    out.append(ln(ox + 280, Y(0), ox + 280, Y(100), GRID, 1))
    a, b = jag["ano_nasc_pct_1t"], jag["ano_nasc_pct_2t"]
    out.append(ln(ox + 40, Y(a), ox + 280, Y(b), LULA, 3))
    out.append(circ(ox + 40, Y(a), 7, CINZA))
    out.append(circ(ox + 280, Y(b), 7, LULA))
    out.append(t(ox + 52, Y(a) + 22, pct(a), 16, INK, 700, "start", MONO))
    out.append(t(ox + 268, Y(b) - 14, pct(b), 16, LULA, 700, "end", MONO))
    out.append(t(ox + 40, 428, "1º turno", 14, MUTED, 600, "middle"))
    out.append(t(ox + 280, 428, "2º turno", 14, MUTED, 600, "middle"))
    f1, l1 = num(jag["flavio_1t"]), num(jag["lula_1t"])
    f2, l2 = num(jag["flavio_2t"]), num(jag["lula_2t"])
    out.append(t(ox, 470, f"Flávio × Lula: {f1} × {l1} no 1º", 15, INK, 600))
    out.append(t(ox, 494, f"e {f2} × {l2} no 2º turno.", 15, INK, 600))
    out.append(
        t(ox, 526, "Hipótese: leitor que falhou. Conferir o log.", 14, GOLD, 700)
    )
    return svg("".join(out), "Biometria: sinal estrutural e o caso de Jaguaribe")


# ------------------------------------------------------------------ 12 voto


def fig_voto() -> str:
    sv = dado("secoes_voto")
    si = {x["sinal"]: x for x in sv["sinais"]}
    rot = [
        ("delta", "comparecimento +5 pp"),
        ("sinal_sem_bio", "sem biometria"),
        ("biometria_baixa", "biometria baixa, qualquer"),
        ("sinal_salto_bio", "salto de biometria"),
        ("delta_relativo", "acima do município"),
        ("tardia", "encerrou tarde"),
    ]
    v0, v1, x0, x1 = -7, 7, 330, 960

    def X(v):
        return _x(v, v0, v1, x0, x1)

    out = [
        t(
            x0,
            26,
            "Fatia de Flávio entre os dois, seções com sinal contra as vizinhas do município (pontos)",
            15,
            MUTED,
            600,
        )
    ]
    for g in range(-6, 7, 2):
        out.append(ln(X(g), 40, X(g), 500, GRID, 1, "3 5"))
        out.append(
            t(
                X(g),
                524,
                f"{'+' if g > 0 else '−' if g < 0 else ''}{abs(g)}",
                14,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
    out.append(ln(X(0), 40, X(0), 500, INK, 1.4))
    for i, (k, nome) in enumerate(rot):
        x = si[k]
        y = 75 + i * 72
        out.append(t(x0 - 16, y + 6, nome, 17, INK, 600, "end"))
        out.append(
            t(x0 - 16, y + 26, f"n {num(x['n_did'])}", 13, MUTED, 500, "end", MONO)
        )
        viz = x["dif_fatia_flavio_vs_vizinhas_pp"]
        did = x["did_fatia_flavio_pp"]
        ep = x["ep_did_fatia_flavio_pp"]
        out.append(ln(X(viz), y, X(did), y, CINZA, 1.2, "3 3"))
        out.append(circ(X(viz), y, 7, PAPER, f' stroke="{CINZA}" stroke-width="2.5"'))
        out.append(ln(X(did - 2 * ep), y, X(did + 2 * ep), y, INK, 2.4))
        out.append(circ(X(did), y, 7, INK))
        forte = abs(did) > 2 * ep
        out.append(
            t(
                X(did) + (14 if did >= 0 else -14),
                y - 12,
                sinal(did),
                14,
                LULA if forte else INK,
                700,
                "start" if did >= 0 else "end",
                MONO,
            )
        )
    out.append(t(X(-6.5), 560, "← mais Lula", 14, LULA, 700))
    out.append(t(X(6.5), 560, "mais Flávio →", 14, FLAVIO, 700, "end"))
    out.append(
        legenda(
            [
                ("diferença crua no 2º turno", CINZA),
                ("descontada a do 1º turno, com 2 erros-padrão", INK),
            ],
            60,
            592,
            14,
        )
    )
    return svg("".join(out), "Diferença em diferenças da fatia de Flávio por sinal")


# ------------------------------------------------------------------ 13 pesquisas


def fig_pesquisas() -> str:
    pv = dado("pesquisas_vs_urna")
    ps = sorted(
        pv["pesquisas"], key=lambda p: p["erro_validos_do_total"]["erro_f_menos_l"]
    )
    v0, v1, x0, x1 = -6, 14, 290, 970

    def X(v):
        return _x(v, v0, v1, x0, x1)

    out = []
    y0 = 38
    passo = (520 - y0) / len(ps)
    for g in range(-4, 15, 2):
        out.append(ln(X(g), y0 - 10, X(g), 528, GRID, 1, "3 5"))
        out.append(
            t(
                X(g),
                550,
                f"{'+' if g > 0 else '−' if g < 0 else ''}{abs(g)}",
                13,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
    out.append(r(X(0) - 2, y0 - 16, 4, 528 - y0 + 16, INK))
    out.append(etiqueta(X(0) - 8, y0 - 18, "urna", 14, WHITE, INK, "end", 700))
    media = pv["resumo"]["publicado_validos_do_total"]["media"]
    out.append(ln(X(media), y0 - 10, X(media), 528, LULA, 2, "6 4"))
    out.append(
        etiqueta(
            X(media) + 6,
            y0 - 18,
            f"distância comum {sinal(media)}",
            14,
            LULA,
            PAPER,
            "start",
            700,
        )
    )
    for i, p in enumerate(ps):
        y = y0 + i * passo + passo / 2
        e = p["erro_validos_do_total"]["erro_f_menos_l"]
        mg = p["margem_95_diferenca_aas_pp"]
        out.append(t(x0 - 12, y + 5, p["instituto"], 13, INK, 600, "end"))
        out.append(ln(X(e - mg), y, X(e + mg), y, CINZA, 2))
        fora = p["erro_fora_da_margem_aas"]
        out.append(
            circ(
                X(e),
                y,
                6.5,
                LULA if fora else PAPER,
                "" if fora else f' stroke="{LULA}" stroke-width="2.5"',
            )
        )
    out.append(
        t(
            x0,
            578,
            "Distância até a urna na diferença Flávio menos Lula (pontos); traço: margem de 95% da diferença",
            13,
            MUTED,
            600,
        )
    )
    out.append(legenda([("fora da margem", LULA)], x0, 598, 13))
    return svg("".join(out), "Distância de cada pesquisa até a urna na diferença")


# ------------------------------------------------------------------ 14 sábado × domingo


def fig_mudanca() -> str:
    pv = dado("pesquisas_vs_urna")
    c = pv["centrais"]
    pub = c["ancora_projecao_published"]["erro_f_menos_l"]
    pnad = c["ancora_projecao_pnad"]["erro_f_menos_l"]
    proj = c["projecao_arvor"]["erro_f_menos_l"]
    media = c["media_arvor"]["erro_f_menos_l"]
    simples = pv["resumo"]["publicado_validos_do_total"]["media"]
    out = [t(40, 26, "Distância até a urna na diferença F−L (pontos)", 15, MUTED, 600)]
    y0, y1 = 520, 60

    def Y(v):
        return _x(v, 0, 10, y0, y1)

    for g in (2, 4, 6, 8, 10):
        out.append(ln(40, Y(g), 500, Y(g), GRID, 1, "3 5"))
        out.append(t(36, Y(g) + 5, str(g), 12, MUTED, 500, "end", MONO))
    barras = [
        ("média das casas", 0, simples, CINZA),
        ("âncora", 0, pub, FLAVIO),
        ("+ PNAD", pub, pnad, GOLD),
        ("+ presença", pnad, proj, GOLD),
        ("Projeção", 0, proj, LULA),
        ("Média", 0, media, LULA),
    ]
    larg = 70
    for i, (rot, a, b, cor) in enumerate(barras):
        x = 50 + i * 76
        out.append(r(x, Y(b), larg, Y(a) - Y(b), cor, 3))
        out.append(
            t(
                x + larg / 2,
                Y(b) - 8,
                sinal(b - a if a else b),
                14,
                INK,
                700,
                "middle",
                MONO,
            )
        )
        out.append(t(x + larg / 2, y0 + 20, rot, 12, INK, 600, "middle"))
    out.append(ln(40, y0, 500, y0, INK, 1.2))
    # reponderação casa a casa
    ef = sorted(
        pv["efeito_reponderacao"]["por_casa"],
        key=lambda x: x["erro_publicado_f_menos_l"],
    )
    x0, x1 = 700, 980

    def X(v):
        return _x(v, 3, 12, x0, x1)

    out.append(t(560, 26, "Reponderação por renda, casa a casa", 15, MUTED, 600))
    for g in (4, 6, 8, 10, 12):
        out.append(ln(X(g), 44, X(g), 520, GRID, 1, "3 5"))
        out.append(t(X(g), 540, f"+{g}", 12, MUTED, 500, "middle", MONO))
    passo = 470 / len(ef)
    for i, x in enumerate(ef):
        y = 60 + i * passo
        a, b = x["erro_publicado_f_menos_l"], x["erro_reponderado_f_menos_l"]
        cor = LULA if x["direcao"] == "afastou" else VERDE
        out.append(
            t(x0 - 10, y + 5, x["instituto"].split("/")[0][:16], 12, INK, 600, "end")
        )
        out.append(ln(X(a), y, X(b), y, cor, 2.6))
        out.append(circ(X(a), y, 4.5, CINZA))
        out.append(circ(X(b), y, 5.5, cor))
    out.append(
        legenda(
            [("afastou da urna", LULA), ("aproximou ou neutra", VERDE)], 560, 590, 13
        )
    )
    return svg("".join(out), "O tamanho da mudança medido por cada régua")


# ------------------------------------------------------------------ 15 hipótese


def fig_hipotese() -> str:
    h = dado("hipotese_autor")
    pv = dado("pesquisas_vs_urna")
    nec = pv["hipoteses"]["presenca_relativa_necessaria"]
    v0, v1, x0, x1 = -20, 6, 60, 960

    def X(v):
        return _x(v, v0, v1, x0, x1)

    out = [
        t(
            x0,
            28,
            "Presença relativa de Flávio contra a de Lula (%): quanto cada conta exige para bater a urna",
            15,
            MUTED,
            600,
        )
    ]
    for g in range(-20, 7, 4):
        out.append(ln(X(g), 50, X(g), 470, GRID, 1, "3 5"))
        out.append(
            t(
                X(g),
                494,
                f"{'+' if g > 0 else '−' if g < 0 else ''}{abs(g)}",
                14,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
    out.append(ln(X(0), 50, X(0), 470, INK, 1.4))
    itens = [
        (
            pv["centrais"]["presenca_relativa_pct"],
            "o que a central da casa supunha",
            FLAVIO,
        ),
        (nec["autor_empate_pct"], "empate, no cenário do autor", CINZA),
        (
            h["reproducao_tweet"]["parametros"]["presenca_relativa"],
            "cenário do autor no tweet",
            GOLD,
        ),
        (h["presenca_necessaria_a"], "necessária no motor, com a urna real", LULA),
        (
            nec["media_simples_publicada_20_casas"],
            "por fora: média simples das casas",
            ROXO,
        ),
        (nec["media_arvor"], "por fora: Média Arvor", ROXO),
    ]
    for i, (v, rot, cor) in enumerate(itens):
        y = 80 + i * 66
        out.append(ln(X(0), y, X(v), y, cor, 3))
        out.append(circ(X(v), y, 9, cor))
        lado = "end" if v > 0 else "start"
        dx = 6 if lado == "end" else -6
        out.append(
            etiqueta(
                X(v) + dx, y - 16, f"{sinal(v, 1)}% {rot}", 15, INK, PAPER, lado, 700
            )
        )
    out.append(
        t(
            x0,
            540,
            "Presença por candidato não é medida: a urna não separa esta conta de um erro comum de medição.",
            15,
            INK,
            600,
        )
    )
    out.append(
        t(
            x0,
            566,
            "Rótulo: juízo editorial do autor, refeito no motor da casa.",
            14,
            GOLD,
            700,
        )
    )
    return svg("".join(out), "Hipótese do autor: presença relativa necessária")


# ------------------------------------------------------------------ 16 paralela e boletins


def fig_paralela() -> str:
    p = dado("paralela")
    bus = sorted(p["bus"], key=lambda b: b["recebido_brt"])
    out = [
        t(
            40,
            26,
            f"Os {len(bus)} BUs da paralela, um quadrado cada, na ordem de chegada",
            15,
            MUTED,
            600,
        )
    ]
    col, lado = 30, 26
    for i, b in enumerate(bus):
        x = 40 + (i % col) * (lado + 4)
        y = 44 + (i // col) * (lado + 4)
        cor = VERDE if b["situacao"] == "igual" else LULA
        out.append(r(x, y, lado, lado, cor, 3))
    yfim = 44 + ((len(bus) - 1) // col + 1) * (lado + 4)
    out.append(
        legenda(
            [("igual ao BU publicado pelo TSE", VERDE), ("divergente", LULA)],
            40,
            yfim + 24,
            14,
        )
    )
    # boletins
    bol = boletins()
    m0, m1 = 17 * 60, 21 * 60 + 40
    x0, x1 = 60, 960

    def X(m):
        return _x(m, m0, m1, x0, x1)

    yb = 470
    out.append(
        t(x0, yb - 64, f"Os {len(bol)} boletins falados da noite", 15, MUTED, 600)
    )
    horas = [int(b["id"][:2]) * 60 + int(b["id"][2:]) for b in bol]
    gaps = [(b - a, a, b) for a, b in pairwise(horas)]
    g, a, b = max(gaps)
    out.append(r(X(a) + 8, yb - 40, X(b) - X(a) - 16, 60, PAPER2, 4))
    out.append(
        t(
            (X(a) + X(b)) / 2,
            yb - 4,
            f"{g} min sem boletim: sem versão nova",
            14,
            INK,
            600,
            "middle",
        )
    )
    for b_, m in zip(bol, horas, strict=True):
        dur = (b_["duracao"] or 0) / 60
        cor = CINZA if b_["id"] in NAO_FOI_AO_AR else FLAVIO
        out.append(r(X(m), yb - 30, max(4.0, X(m + dur) - X(m)), 40, cor, 2))
    out.append(ln(x0, yb + 20, x1, yb + 20, MUTED, 1))
    m = m0
    while m <= m1:
        out.append(
            t(
                X(m),
                yb + 44,
                f"{m // 60:02d}:{m % 60:02d}",
                13,
                MUTED,
                500,
                "middle",
                MONO,
            )
        )
        m += 30
    out.append(
        legenda(
            [
                ("boletim no ar (largura: duração)", FLAVIO),
                ("gerado e não foi ao ar", CINZA),
            ],
            x0,
            580,
            13,
        )
    )
    return svg("".join(out), "Paralela conferida e boletins da noite")


# ------------------------------------------------------------------ 17 limites


def fig_limites() -> str:
    p = dado("presidente")["nacional"]
    s = dado("secoes")
    par = dado("paralela")
    univ = s["n_universo_1t"]
    rdv = dado("rdv")["cobertura"]["total"]
    itens = [
        ("arquivos de resultado do TSE", p["secoes"], p["secoes_total"], FLAVIO),
        ("boletins de urna lidos", s["n_bus_completo"], p["secoes_total"], GOLD),
        ("registro digital do voto conferido", rdv["confere"], rdv["ok"], LULA),
        ("totalização paralela", par["recebidos"]["bus"], univ, VERDE),
    ]
    out = [
        t(
            40,
            30,
            "Que parte das seções cada camada do dossiê enxerga (escala logarítmica)",
            15,
            MUTED,
            600,
        )
    ]
    import math

    x0, x1 = 390, 960
    l0, l1 = math.log10(0.01), math.log10(100)

    def X(v):
        return _x(math.log10(max(v, 0.01)), l0, l1, x0, x1)

    for g in (0.01, 0.1, 1, 10, 100):
        out.append(ln(X(g), 50, X(g), 470, GRID, 1, "3 5"))
        rot = num(g, 2 if g < 0.1 else 1 if g < 1 else 0)
        out.append(t(X(g), 494, f"{rot}%", 13, MUTED, 500, "middle", MONO))
    for i, (rot, n, tot, cor) in enumerate(itens):
        y = 100 + i * 100
        v = 100 * n / tot
        out.append(t(x0 - 14, y + 4, rot, 16, INK, 700, "end"))
        out.append(
            t(x0 - 14, y + 26, f"{num(n)} de {num(tot)}", 13, MUTED, 500, "end", MONO)
        )
        out.append(r(x0, y - 16, X(v) - x0, 34, cor, 3))
        if v > 50:
            out.append(t(X(v) - 10, y + 7, pct(v, 2), 16, WHITE, 700, "end", MONO))
        else:
            out.append(t(X(v) + 10, y + 7, pct(v, 2), 16, INK, 700, "start", MONO))
    out.append(
        t(
            40,
            550,
            "Falta a camada dos logs de todas as urnas e dos metadados das seções.",
            15,
            INK,
            600,
        )
    )
    out.append(
        t(40, 576, "A paralela é soma dos BUs recebidos, não projeção.", 15, INK, 600)
    )
    return svg("".join(out), "Cobertura de cada camada do dossiê")


# ------------------------------------------------------------------ 18 fecho


def fig_fecho(v: dict) -> str:
    tiles = [
        (f"{v['l_pct_n']} × {v['f_pct_n']}", "Lula × Flávio nos válidos", LULA),
        (f"{v['sil_min']} min", "sem nenhum arquivo do TSE", INK),
        (
            f"{v['proj_lider_n']} de {v['proj_n']}",
            "pontos da projeção com Lula à frente",
            FLAVIO,
        ),
        (v["pq_erro"], "distância comum entre pesquisa e urna", LULA),
        (
            f"{v['pa_iguais']} / {v['pa_div']}",
            "BUs iguais / divergentes na paralela",
            VERDE,
        ),
        (
            f"{v['t_ufs_caiu']} de {v['t_ufs']}",
            "UFs em que Flávio caiu contra o 1º turno",
            GOLD,
        ),
    ]
    out = []
    for i, (n, rot, cor) in enumerate(tiles):
        x = 20 + (i % 3) * 330
        y = 30 + (i // 3) * 270
        out.append(r(x, y, 310, 240, PAPER2, 10))
        out.append(r(x, y, 310, 8, cor, 2))
        tam = 50 if len(n) <= 9 else 40 if len(n) <= 12 else 32
        out.append(
            t(x + 155, y + 120, n, tam, cor, 800, "middle", "Fraunces, Georgia, serif")
        )
        out.append(t(x + 155, y + 175, rot, 16, INK, 600, "middle"))
    return svg("".join(out), "Os números da noite")


__all__ = [
    "fig_biometria",
    "fig_comparecimento",
    "fig_fecho",
    "fig_hipotese",
    "fig_limites",
    "fig_mudanca",
    "fig_paralela",
    "fig_pesquisas",
    "fig_voto",
]
