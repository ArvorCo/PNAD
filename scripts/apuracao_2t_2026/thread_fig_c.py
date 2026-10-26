"""Figura do card da transferência 1º → 2º turno: Sankey simplificado em SVG.

Origens agrupadas (Lula, Flávio, terceira via, branco e nulo, abstenção) e destinos
do 2º turno, a partir da matriz central de ``transferencia.json``. Fita sólida: linha
com prior em cruzamento publicado por instituto; fita hachurada: elo estimado
(hipótese declarada ou regressão ecológica). Tudo é estimativa, não medição.
"""

from __future__ import annotations

from apuracao_2026.thread_base import (
    CINZA,
    FLAVIO,
    INK,
    LULA,
    MUTED,
    OUTROS,
    legenda,
    mi_curto,
    r,
    svg,
    t,
)

from .thread_base import dado

ORIGENS = [
    ("lula", "Lula", ("lula",), LULA),
    ("flavio", "Flávio", ("flavio",), FLAVIO),
    ("terceira", "Terceira via", ("cury", "renan", "caiado", "zema", "outros"), OUTROS),
    ("bn", "Branco e nulo", ("brancos", "nulos"), CINZA),
    ("abst", "Abstenção", ("abstencao",), "#8a8f96"),
]
DESTINOS = [
    ("lula", "Lula", ("lula",), LULA),
    ("flavio", "Flávio", ("flavio",), FLAVIO),
    ("bn", "Branco e nulo", ("brancos", "nulos"), CINZA),
    ("abst", "Abstenção", ("abstencao",), "#8a8f96"),
]


def fluxos() -> tuple[dict, dict]:
    """Votos e tipo de cada fita agrupada (origem, destino)."""
    c = dado("transferencia")["ipf"]["central"]
    votos, tipo = {}, {}
    for ko, _, mo, _ in ORIGENS:
        for kd, _, md, _ in DESTINOS:
            v = sum(c["matriz"][o][d] for o in mo for d in md)
            tipos = {c["tipos"][o][d] for o in mo for d in md}
            votos[(ko, kd)] = v
            tipo[(ko, kd)] = "medido" if tipos == {"medido"} else "estimado"
    return votos, tipo


def _padrao(pid: str, cor: str) -> str:
    return (
        f'<defs><pattern id="{pid}" width="9" height="9" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><rect width="9" height="9" fill="{cor}" '
        f'fill-opacity="0.18"/><line x1="0" y1="0" x2="0" y2="9" stroke="{cor}" '
        f'stroke-width="3.2" stroke-opacity="0.75"/></pattern></defs>'
    )


def _rotulo(out: list, x: float, y: float, h: float, nome: str, v: float, anc: str):
    if h < 40:
        out.append(t(x, y + h / 2 + 5, f"{nome} · {mi_curto(v)}", 14, INK, 700, anc))
    else:
        out.append(t(x, y + h / 2 + 2, nome, 16, INK, 700, anc))
        out.append(t(x, y + h / 2 + 20, mi_curto(v), 13, MUTED, 500, anc))


def fig_transferencia() -> str:
    votos, tipo = fluxos()
    tot_o = {k: sum(votos[(k, d[0])] for d in DESTINOS) for k, *_ in ORIGENS}
    tot_d = {k: sum(votos[(o[0], k)] for o in ORIGENS) for k, *_ in DESTINOS}
    total = sum(tot_o.values())
    x0, x1, larg = 210, 760, 22
    topo, alt_util = 30, 500
    gap = 12
    esc_o = (alt_util - gap * (len(ORIGENS) - 1)) / total
    esc_d = (alt_util - gap * (len(DESTINOS) - 1)) / total
    out = [_padrao(f"tr-{k}", cor) for k, _, _, cor in ORIGENS]
    y = topo
    pos_o = {}
    for k, nome, _, cor in ORIGENS:
        h = tot_o[k] * esc_o
        pos_o[k] = [y, y]
        out.append(r(x0 - larg, y, larg, h, cor, 2))
        _rotulo(out, x0 - larg - 10, y, h, nome, tot_o[k], "end")
        y += h + gap
    y = topo
    pos_d = {}
    for k, nome, _, cor in DESTINOS:
        h = tot_d[k] * esc_d
        pos_d[k] = [y, y]
        out.append(r(x1, y, larg, h, cor, 2))
        _rotulo(out, x1 + larg + 10, y, h, nome, tot_d[k], "start")
        y += h + gap
    for ko, _, _, cor in ORIGENS:
        for kd, *_ in DESTINOS:
            v = votos[(ko, kd)]
            ho, hd = v * esc_o, v * esc_d
            if ho < 0.3:
                pos_o[ko][1] += ho
                pos_d[kd][1] += hd
                continue
            ya, yb = pos_o[ko][1], pos_d[kd][1]
            pos_o[ko][1] += ho
            pos_d[kd][1] += hd
            xm = (x0 + x1) / 2
            d = (
                f"M{x0},{ya:.1f} C{xm},{ya:.1f} {xm},{yb:.1f} {x1},{yb:.1f} "
                f"L{x1},{yb + hd:.1f} C{xm},{yb + hd:.1f} {xm},{ya + ho:.1f} {x0},{ya + ho:.1f} Z"
            )
            if tipo[(ko, kd)] == "medido":
                out.append(f'<path d="{d}" fill="{cor}" fill-opacity="0.42"/>')
            else:
                out.append(f'<path d="{d}" fill="url(#tr-{ko})"/>')
    tr = dado("transferencia")["ipf"]["central"]["metricas"]
    out.append(
        t(
            60,
            560,
            f"Da abstenção do 1º turno, {mi_curto(tr['voltaram'])} voltaram a votar "
            f"({mi_curto(tr['voltaram_lula'])} para Lula, {mi_curto(tr['voltaram_flavio'])} para Flávio).",
            15,
            INK,
            700,
        )
    )
    out.append(
        legenda(
            [
                ("prior em cruzamento publicado", "#7d8792"),
                ("elo estimado (hachurado)", "#c3c8ce"),
            ],
            60,
            590,
            14,
        )
    )
    out.append(t(940, 590, "Estimativa, não medição.", 14, INK, 700, "end"))
    return svg("".join(out), "Transferência estimada de votos do 1º para o 2º turno")


def fig_cadencia() -> str:
    """Votos por hora (hora de Brasília), 1º × 2º turno nas mesmas seções da amostra do log."""
    cad = dado("logs")["cadencia"]["amostra_1t"]
    p1, p2 = cad["brasil_1t"]["pct"], cad["brasil_2t_mesmas"]["pct"]
    horas = sorted(p1, key=int)
    x0, x1, y0, y1 = 80, 980, 50, 470
    passo = (x1 - x0) / len(horas)
    vmax = 18.0

    def Y(v):
        return y1 - (y1 - y0) * v / vmax

    out = [
        t(
            x0,
            30,
            "Votos computados em cada hora, % do dia (hora de Brasília, mesmas seções)",
            15,
            MUTED,
            600,
        )
    ]
    for g in (5, 10, 15):
        out.append(
            f'<line x1="{x0}" y1="{Y(g):.1f}" x2="{x1}" y2="{Y(g):.1f}" stroke="#d6cfbd" stroke-dasharray="3 5"/>'
        )
        out.append(t(x0 - 10, Y(g) + 5, f"{g}%", 14, MUTED, 500, "end"))
    larg = passo * 0.36
    for i, h in enumerate(horas):
        xx = x0 + i * passo + passo * 0.12
        a, b = p1[h], p2[h]
        out.append(r(xx, Y(a), larg, y1 - Y(a), "#8a8f96", 2))
        out.append(r(xx + larg + 4, Y(b), larg, y1 - Y(b), FLAVIO, 2))
        out.append(t(xx + larg, y1 + 24, f"{int(h)}h", 14, INK, 600, "middle"))
        if int(h) >= 17:
            out.append(
                t(
                    xx + larg / 2,
                    Y(a) - 8,
                    f"{a:.1f}".replace(".", ","),
                    13,
                    INK,
                    700,
                    "middle",
                )
            )
            out.append(
                t(
                    xx + larg * 1.5 + 4,
                    Y(b) - 8,
                    f"{b:.2f}".replace(".", ","),
                    13,
                    FLAVIO,
                    700,
                    "middle",
                )
            )
    x17 = x0 + horas.index("17") * passo
    out.append(
        f'<line x1="{x17:.1f}" y1="{y0}" x2="{x17:.1f}" y2="{y1}" stroke="{LULA}" stroke-width="2"/>'
    )
    out.append(t(x17 + 8, y0 + 18, "17h: fim do horário oficial", 14, LULA, 700))
    out.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{MUTED}"/>')
    out.append(legenda([("1º turno", "#8a8f96"), ("2º turno", FLAVIO)], x0, 540, 15))
    out.append(
        t(x0, 575, "Rótulo: pede explicação, não prova irregularidade.", 14, INK, 600)
    )
    return svg("".join(out), "Cadência horária dos votos no log, 1º e 2º turno")


COR_ESTADO = {"descartada": "#0c7a72", "pendente": "#7d5b00", "compativel": FLAVIO}


def fig_hipoteses() -> str:
    """Quadro-resumo das seis hipóteses, com o estado de cada uma em cor."""
    hp = dado("hipoteses")
    est = hp["estados"]
    out = [t(40, 30, "As hipóteses e o que os dados dizem de cada uma", 15, MUTED, 600)]
    y = 60
    for i, h in enumerate(hp["hipoteses"], 1):
        cor = COR_ESTADO[h["estado"]]
        out.append(r(40, y, 920, 70, "#ebe5d6", 6))
        out.append(r(40, y, 10, 70, cor, 3))
        out.append(t(70, y + 30, f"H{i} · {h['curto']}", 20, INK, 700))
        alcance = h["alcance"]
        if len(alcance) > 92:
            alcance = alcance[: alcance.rfind(" ", 0, 90)] + " (…)"
        out.append(t(70, y + 55, alcance, 13, MUTED, 500))
        out.append(r(700, y + 16, 244, 34, cor, 17))
        out.append(t(822, y + 39, est[h["estado"]], 14, "#ffffff", 700, "middle"))
        y += 82
    out.append(
        t(
            40,
            575,
            "Rótulo: atipicidade pede explicação, não prova irregularidade.",
            14,
            INK,
            600,
        )
    )
    return svg("".join(out), "Quadro-resumo das seis hipóteses")


__all__ = [
    "DESTINOS",
    "ORIGENS",
    "fig_cadencia",
    "fig_hipoteses",
    "fig_transferencia",
    "fluxos",
]
