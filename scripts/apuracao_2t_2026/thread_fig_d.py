"""Figuras dos cards 25 e 26 da thread do 2º turno. SVG 1000 × 600, dados dos JSONs.

``fig_perdas`` adapta ao quadrado da thread a figura ``tu_perdas_uf`` do dossiê: as
27 UFs em duas colunas, cada uma com a parcela dos seus municípios em que Flávio
(barra grossa) e Lula (barra fina) tiveram menos votos absolutos no 2º turno, com a
contagem ao lado e o losango nas UFs com 2º turno de governador.

``fig_pendencia`` põe lado a lado os dois achados sem documento público (série da
memória de resultado repetida e urna realocada) e, embaixo, a fatia de Flávio
contra as vizinhas do município com intervalo de 95%: crua no 2º turno e descontado
o 1º turno.
"""

from __future__ import annotations

import math

from apuracao_2026.thread_base import (
    CINZA,
    DISPLAY,
    FLAVIO,
    GOLD,
    GRID,
    INK,
    LULA,
    MONO,
    MUTED,
    PAPER,
    PAPER2,
    circ,
    etiqueta,
    legenda,
    ln,
    num,
    r,
    sinal,
    svg,
    t,
)

from .thread_valores_c import pendencia, resumos

VERDE = "#0c7a72"
H = 660


def _losango(x: float, y: float, s: float = 6) -> str:
    return f'<path d="M{x:.1f} {y - s:.1f}l{s} {s} {-s} {s} {-s} {-s}z" fill="{GOLD}"/>'


def _x(v: float, v0: float, v1: float, x0: float, x1: float) -> float:
    return x0 + (x1 - x0) * (v - v0) / (v1 - v0)


# ------------------------------------------------------------------ 25 perdas


def fig_perdas() -> str:
    rf, rl, _, _ = resumos()
    lula = {u["uf"]: u for u in rl["por_uf"]}
    itens = sorted(rf["por_uf"], key=lambda u: (-u["n"] / u["n_uf"], -u["n"], u["uf"]))
    por_coluna = math.ceil(len(itens) / 2)
    out = [
        t(
            20,
            28,
            "Parcela dos municípios de cada UF em que o finalista teve menos votos "
            "no 2º turno do que no 1º",
            15,
            MUTED,
            600,
        ),
        legenda([("Flávio", FLAVIO), ("Lula", LULA)], 20, 58, 14),
        _losango(186, 53),
        t(198, 58, "UF com 2º turno de governador", 14, INK, 500),
        ln(500, 76, 500, 606, GRID, 1),
    ]
    larg, y0, rh = 230, 100, 38
    for i, u in enumerate(itens):
        col, k = divmod(i, por_coluna)
        x = 20 + col * 495
        y = y0 + k * rh
        nl = lula[u["uf"]]["n"]
        if u["governador_2t"]:
            out.append(_losango(x + 6, y - 6))
        out.append(t(x + 18, y, u["uf"], 16, INK, 700))
        out.append(r(x + 56, y - 13, larg, 13, PAPER2, 2))
        if u["n"]:
            out.append(r(x + 56, y - 13, larg * u["n"] / u["n_uf"], 13, FLAVIO, 2))
        if nl:
            out.append(r(x + 56, y + 3, larg * nl / u["n_uf"], 5, LULA, 1))
        rot = f"{num(u['n'])} de {num(u['n_uf'])}"
        out.append(t(x + 296, y, rot, 14, INK if u["n"] else MUTED, 700, "start", MONO))
        if nl:
            out.append(
                t(
                    x + 306 + 8.4 * len(rot),
                    y,
                    f"Lula {num(nl)}",
                    13,
                    LULA,
                    600,
                    "start",
                    MONO,
                )
            )
    out.append(
        t(
            20,
            646,
            "Barra cheia: todos os municípios da UF. Votos absolutos, não fatia dos "
            "válidos; menos votos não identifica eleitor nem motivo.",
            14,
            INK,
            600,
        )
    )
    return svg("".join(out), "Municípios com menos votos no 2º turno, por UF", h=H)


# ------------------------------------------------------------------ 26 pendência


def _quadro(x: float, cor: str, titulo: str, grande: str, linhas: list[str]) -> str:
    out = [r(x, 16, 470, 256, PAPER2, 10), r(x, 16, 470, 8, cor, 2)]
    out.append(t(x + 24, 60, titulo, 18, INK, 700))
    out.append(t(x + 24, 140, grande, 74, INK, 800, "start", DISPLAY))
    for i, linha in enumerate(linhas):
        out.append(t(x + 24, 182 + i * 28, linha, 16 if i == 0 else 15, INK, 600))
    return "".join(out)


def fig_pendencia() -> str:
    P = pendencia()
    s, tot, et = P["serie"], P["tot"], P["et"]
    n_br = sum(x["secoes"] for x in P["brasil"])
    n_ext = sum(x["secoes"] for x in P["exterior"])
    n_re = et["certificado_do_1t_em_outra_secao_no_2t"]
    nao = P["log_nao_confere"]
    out = [
        _quadro(
            20,
            GOLD,
            "Série repetida da memória de resultado",
            num(n_br),
            [
                f"seções no Brasil, em {num(len(P['brasil']))} grupos fechados numa zona",
                f"mais {num(n_ext)} no exterior, num só valor",
                f"{num(s['repetidos'])} séries repetidas, {num(s['secoes_em_repeticao'])} "
                "seções ao todo",
            ],
        ),
        _quadro(
            510,
            VERDE,
            "Urna do 1º turno em outra seção no 2º",
            num(n_re),
            [
                "seções com a urna realocada de outra seção",
                f"{num(tot['mesmo_municipio'])} no mesmo município, "
                f"{num(tot['mesma_zona'])} na mesma zona, {num(tot['ufs'])} UFs",
                (
                    "log fecha com o BU em todas"
                    if nao == 0
                    else f"log não fecha com o BU em {num(nao)}"
                ),
            ],
        ),
    ]
    linhas = [
        (
            "Série repetida",
            n_br,
            P["voto_mr"]["contra_vizinhas_2t"],
            P["voto_mr"]["dif_em_dif_contra_1t"],
        ),
        (
            "Urna realocada",
            n_re,
            P["realocado"]["fatia_flavio_2t_menos_vizinhas_do_municipio"],
            P["realocado"]["dif_em_dif_contra_1t"],
        ),
    ]
    limites = [v for _, _, a, b in linhas for v in (*a["ic95_pp"], *b["ic95_pp"])]
    v0, v1 = math.floor(min(limites)), math.ceil(max(limites))
    x0, x1 = 300, 960

    def X(v: float) -> float:
        return _x(v, v0, v1, x0, x1)

    out.append(
        t(
            40,
            318,
            "Fatia de Flávio nos votos dos finalistas, contra as vizinhas do município "
            "(pontos)",
            15,
            MUTED,
            600,
        )
    )
    for g in range(v0, v1 + 1):
        out.append(ln(X(g), 336, X(g), 482, GRID, 1, "3 5"))
        out.append(t(X(g), 504, sinal(g, 0), 14, MUTED, 500, "middle", MONO))
    out.append(ln(X(0), 336, X(0), 482, INK, 1.4))
    for i, (nome, n, cru, did) in enumerate(linhas):
        y = 380 + i * 72
        out.append(t(x0 - 16, y + 5, nome, 17, INK, 700, "end"))
        out.append(t(x0 - 16, y + 25, f"{num(n)} seções", 13, MUTED, 500, "end", MONO))
        lo, hi = cru["ic95_pp"]
        out.append(ln(X(lo), y, X(hi), y, CINZA, 1.6))
        out.append(
            circ(
                X(cru["media_pp"]), y, 7, PAPER, f' stroke="{CINZA}" stroke-width="2.5"'
            )
        )
        out.append(
            etiqueta(
                X(cru["media_pp"]),
                y - 14,
                sinal(cru["media_pp"]),
                14,
                CINZA,
                PAPER,
                "middle",
                700,
            )
        )
        lo, hi = did["ic95_pp"]
        out.append(ln(X(lo), y, X(hi), y, INK, 2.6))
        out.append(circ(X(did["media_pp"]), y, 7, INK))
        out.append(
            etiqueta(
                X(did["media_pp"]),
                y + 28,
                sinal(did["media_pp"]),
                14,
                INK,
                PAPER,
                "middle",
                700,
            )
        )
    out.append(t(X(v0) + 4, 530, "← mais Lula", 14, LULA, 700))
    out.append(t(X(v1) - 4, 530, "mais Flávio →", 14, FLAVIO, 700, "end"))
    out.append(
        legenda(
            [
                ("no 2º turno, IC95", CINZA),
                ("mudança do 1º para o 2º turno, IC95", INK),
            ],
            40,
            564,
            14,
        )
    )
    rdv = P["rdv"]
    div = rdv["divergencias"]
    out.append(
        t(
            40,
            604,
            f"Registro digital do voto: {num(rdv['conferem'])} seções conferem com o BU, "
            + ("nenhuma divergência." if div == 0 else f"{num(div)} divergências."),
            16,
            INK,
            700,
        )
    )
    out.append(
        t(
            40,
            638,
            "Atipicidade pede explicação, não prova irregularidade.",
            15,
            INK,
            600,
        )
    )
    return svg(
        "".join(out), "Pendência documental: série repetida e urna realocada", h=H
    )


__all__ = ["fig_pendencia", "fig_perdas"]
