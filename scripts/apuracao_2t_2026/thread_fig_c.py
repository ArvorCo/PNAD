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


def fig_habilitacao() -> str:
    """Ano de nascimento (% do comparecimento) por modelo de urna, 1º × 2º turno."""
    bi = dado("biometria")
    mods = ["UE2013", "UE2015", "UE2020", "UE2022"]
    pm = {(m["turno"], m["modelo"]): m for m in bi["modelos"]["por_modelo"]}
    t2 = bi["totais"]["2t"]
    out = [
        t(
            60,
            30,
            "Eleitor habilitado pelo ano de nascimento, % do comparecimento, por modelo de urna",
            15,
            MUTED,
            600,
        )
    ]
    x0, y0, y1 = 120, 60, 380
    vmax = 12.0

    def Y(v):
        return y1 - (y1 - y0) * v / vmax

    for g in (3, 6, 9, 12):
        out.append(
            f'<line x1="{x0}" y1="{Y(g):.1f}" x2="960" y2="{Y(g):.1f}" stroke="#d6cfbd" stroke-dasharray="3 5"/>'
        )
        out.append(t(x0 - 10, Y(g) + 5, f"{g}%", 14, MUTED, 500, "end"))
    passo = 210
    for i, m in enumerate(mods):
        xx = x0 + 30 + i * passo
        for j, (turno, cor) in enumerate((("1t", "#8a8f96"), ("2t", FLAVIO))):
            v = pm[(turno, m)]["ano_nascimento_pct"]
            out.append(r(xx + j * 70, Y(v), 62, y1 - Y(v), cor, 2))
            out.append(
                t(
                    xx + j * 70 + 31,
                    Y(v) - 8,
                    f"{v:.2f}".replace(".", ","),
                    14,
                    INK if j == 0 else FLAVIO,
                    700,
                    "middle",
                )
            )
        out.append(t(xx + 66, y1 + 24, m, 15, INK, 700, "middle"))
    out.append(f'<line x1="{x0}" y1="{y1}" x2="960" y2="{y1}" stroke="{MUTED}"/>')
    out.append(legenda([("1º turno", "#8a8f96"), ("2º turno", FLAVIO)], x0, 438, 14))
    # composição do 2º turno
    tot = t2["comparecimento_com_categoria"]
    xb0, xb1, yb = 120, 960, 470
    partes = [
        ("biometria", t2["biometria"], "#0c7a72"),
        ("ano de nascimento", t2["ano_nascimento"], "#7d5b00"),
        ("sem cadastro", t2["sem_cadastro"], LULA),
    ]
    x = xb0
    for _nome, v, cor in partes:
        w = (xb1 - xb0) * v / tot
        out.append(r(x, yb, w, 30, cor))
        x += w
    out.append(
        t(
            xb0,
            yb + 54,
            "2º turno, Brasil: "
            + " · ".join(
                f"{n} {100 * v / tot:.1f}%".replace(".", ",") for n, v, _ in partes
            ),
            14,
            INK,
            600,
        )
    )
    out.append(
        t(
            xb0,
            yb + 80,
            "Leitor antigo falha mais: hipótese a confirmar no log.",
            14,
            INK,
            700,
        )
    )
    return svg("".join(out), "Habilitação por modelo de urna e composição do 2º turno")


CORES_GRUPOS = (
    "#1f5f9e",
    "#4f8fa0",
    "#0c7a72",
    "#7d5b00",
    "#939cae",
    "#6b4a92",
    "#b8560f",
    "#c8412f",
)


def fig_grupos() -> str:
    """Os grupos da mistura gaussiana (tamanho) e o que define o atípico (brancos e nulos)."""
    A = dado("anomalia_ml")
    comps = A["componentes"]
    anom = A["mais_anomalo"]["id"]
    pais = A["pais"]["centro_pct_eleitorado"]
    out = [
        t(
            60,
            30,
            "Oito grupos de seções pelas frações do eleitorado nos dois turnos",
            15,
            MUTED,
            600,
        )
    ]
    x0, y0, passo = 60, 56, 40
    vmax = max(c["secoes"] for c in comps)
    larg = 300
    for i, c in enumerate(comps):
        y = y0 + i * passo
        cor = CORES_GRUPOS[c["id"] % len(CORES_GRUPOS)]
        w = larg * c["secoes"] / vmax
        out.append(r(x0 + 90, y, w, 26, cor, 2))
        out.append(t(x0 + 82, y + 19, f"Grupo {c['id'] + 1}", 14, INK, 700, "end"))
        rot = f"{c['secoes']:,}".replace(
            ",", "."
        ) + f" ({c['pct_secoes']:.1f}%)".replace(".", ",")
        out.append(
            t(
                x0 + 96 + w,
                y + 19,
                rot,
                13,
                INK if c["id"] != anom else "#6b4a92",
                700 if c["id"] == anom else 500,
            )
        )
    ya = y0 + anom * passo
    out.append(
        f'<rect x="{x0 + 86}" y="{ya - 4}" width="{larg + 210}" height="34" fill="none" stroke="#6b4a92" stroke-width="2" stroke-dasharray="6 4" rx="4"/>'
    )
    out.append(
        t(
            x0 + 90,
            y0 + len(comps) * passo + 14,
            "O tracejado marca o grupo mais atípico, pelo critério do 1º turno.",
            13,
            MUTED,
            500,
        )
    )
    # direita: brancos e nulos, grupo atípico contra o país, nos dois turnos
    cx0, cy1, cy0 = 680, 360, 90
    c = comps[anom]["centro_pct_eleitorado"]
    pares = [
        ("1º turno", c["brancos1"] + c["nulos1"], pais["brancos1"] + pais["nulos1"]),
        ("2º turno", c["brancos2"] + c["nulos2"], pais["brancos2"] + pais["nulos2"]),
    ]
    vmax2 = 8.0
    out.append(t(cx0, 66, "Brancos e nulos, % do eleitorado", 15, INK, 700))

    def Y(v):
        return cy1 - (cy1 - cy0) * v / vmax2

    for g in (2, 4, 6, 8):
        out.append(
            f'<line x1="{cx0}" y1="{Y(g):.1f}" x2="{cx0 + 300}" y2="{Y(g):.1f}" stroke="#d6cfbd" stroke-dasharray="3 5"/>'
        )
        out.append(t(cx0 - 8, Y(g) + 5, f"{g}%", 13, MUTED, 500, "end"))
    for i, (nome, vg, vp) in enumerate(pares):
        xx = cx0 + 30 + i * 150
        for j, (v, cor) in enumerate(((vg, "#6b4a92"), (vp, "#8a8f96"))):
            out.append(r(xx + j * 58, Y(v), 50, cy1 - Y(v), cor, 2))
            out.append(
                t(
                    xx + j * 58 + 25,
                    Y(v) - 7,
                    f"{v:.1f}%".replace(".", ","),
                    14,
                    INK,
                    700,
                    "middle",
                )
            )
        out.append(t(xx + 54, cy1 + 22, nome, 14, INK, 700, "middle"))
    out.append(
        f'<line x1="{cx0}" y1="{cy1}" x2="{cx0 + 300}" y2="{cy1}" stroke="{MUTED}"/>'
    )
    out.append(
        legenda([("grupo atípico", "#6b4a92"), ("país", "#8a8f96")], cx0, 412, 14)
    )
    out.append(t(cx0, 460, "Não é geografia nem modelo de urna:", 14, INK, 700))
    cv = A["mais_anomalo"]["contra"]["cramer_v"]
    linhas_cv = (
        f"V de Cramér do grupo com a região {cv['regiao']:.3f};",
        f"com o modelo da urna {cv['modelo']:.3f}; com o tamanho {cv['tamanho']:.3f}.",
    )
    for j, linha in enumerate(linhas_cv):
        out.append(
            t(
                cx0,
                482 + 22 * j,
                linha.replace(".0", ",0").replace(".2", ",2"),
                14,
                INK,
                500,
            )
        )
    out.append(t(cx0, 530, "É, em boa parte, seção pequena.", 14, INK, 700))
    out.append(
        t(
            60,
            560,
            "Atipicidade estatística não é irregularidade; o grupo pede explicação, não prova nada.",
            14,
            MUTED,
            600,
        )
    )
    return svg("".join(out), "Grupos de seções nos dois turnos e o grupo atípico")


def fig_dispersao() -> str:
    """Dispersão das seções nos dois componentes principais, cor por grupo, elipse do atípico."""
    import math

    A = dado("anomalia_ml")
    P = A["pca"]
    cols = P["colunas"]
    pts = [dict(zip(cols, p, strict=False)) for p in P["pontos"]]
    anom = int(P.get("anomalo", A["mais_anomalo"]["id"]))
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    x0, x1, y0, y1 = 70, 700, 40, 520
    lox, hix = min(xs) - 0.3, max(xs) + 0.3
    loy, hiy = min(ys) - 0.3, max(ys) + 0.3

    def X(v):
        return x0 + (x1 - x0) * (v - lox) / (hix - lox)

    def Y(v):
        return y1 - (y1 - y0) * (v - loy) / (hiy - loy)

    ve = P.get("variancia_explicada") or [None, None]
    out = [
        t(
            60,
            28,
            "Cada ponto é uma seção; a cor é o grupo da mistura gaussiana",
            15,
            MUTED,
            600,
        ),
        f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="#f7f4ec" stroke="#d6cfbd"/>',
    ]
    grupos: dict[int, list[str]] = {}
    tops = []
    for p in pts:
        k = int(p["cluster"])
        if p.get("top"):
            tops.append((X(p["x"]), Y(p["y"]), k))
        else:
            grupos.setdefault(k, []).append(f"M{X(p['x']):.1f} {Y(p['y']):.1f}h0.01")
    # o atípico por cima dos demais
    for k in sorted(grupos, key=lambda k: k == anom):
        cor = CORES_GRUPOS[k % len(CORES_GRUPOS)]
        out.append(
            f'<path d="{"".join(grupos[k])}" stroke="{cor}" stroke-width="{4.2 if k == anom else 3.2}" '
            f'stroke-linecap="round" fill="none" opacity="{0.95 if k == anom else 0.55}"/>'
        )
    for x, y, k in tops:
        cor = CORES_GRUPOS[k % len(CORES_GRUPOS)]
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{cor}" stroke="{INK}" stroke-width="0.9"/>'
        )
    el = next((e for e in P.get("elipses") or [] if int(e["cluster"]) == anom), None)
    if el:
        cx, cy = X(el["cx"]), Y(el["cy"])
        rx = el["rx"] * (x1 - x0) / (hix - lox)
        ry = el["ry"] * (y1 - y0) / (hiy - loy)
        ang = -float(el["ang"])
        out.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" '
            'fill="#6b4a92" fill-opacity="0.05" stroke="#6b4a92" stroke-width="2.4" stroke-dasharray="8 5"/>'
        )
    v1 = f"{100 * ve[0]:.0f}%" if ve[0] is not None else "s/d"
    v2 = f"{100 * ve[1]:.0f}%" if ve[1] is not None else "s/d"
    out.append(
        t(
            (x0 + x1) / 2,
            y1 + 26,
            f"componente principal 1 ({v1} da variância)",
            14,
            INK,
            600,
            "middle",
        )
    )
    out.append(
        t(
            x0 - 8,
            (y0 + y1) / 2,
            f"componente 2 ({v2})",
            14,
            INK,
            600,
            "middle",
            extra=f' transform="rotate(-90 {x0 - 8} {(y0 + y1) / 2:.0f})"',
        )
    )
    # legenda à direita
    lx, ly = 730, 70
    comps = A["componentes"]
    for i, c in enumerate(comps):
        k = int(c["id"])
        cor = CORES_GRUPOS[k % len(CORES_GRUPOS)]
        out.append(r(lx, ly + i * 34 - 11, 13, 13, cor, 2))
        rot = f"Grupo {k + 1}" + (" (atípico)" if k == anom else "")
        out.append(t(lx + 20, ly + i * 34, rot, 14, INK, 700 if k == anom else 500))
        out.append(
            t(
                lx + 20,
                ly + i * 34 + 15,
                f"{c['secoes']:,}".replace(",", ".") + " seções",
                12,
                MUTED,
                500,
            )
        )
    out.append(t(lx, 372, "Ponto com contorno preto:", 13, INK, 700))
    out.append(t(lx, 390, "uma das 300 seções menos", 13, INK, 500))
    out.append(t(lx, 406, "prováveis do país.", 13, INK, 500))
    out.append(t(lx, 436, "Tracejado: o grupo atípico,", 13, INK, 700))
    out.append(t(lx, 454, "dois desvios no plano.", 13, INK, 500))
    out.append(
        t(
            60,
            588,
            "Atipicidade estatística não é irregularidade; o grupo pede explicação, não prova nada.",
            14,
            MUTED,
            600,
        )
    )
    _ = math
    return svg(
        "".join(out), "Seções nos dois componentes principais, por grupo da mistura"
    )


__all__ = [
    "DESTINOS",
    "ORIGENS",
    "fig_cadencia",
    "fig_dispersao",
    "fig_grupos",
    "fig_habilitacao",
    "fig_hipoteses",
    "fig_transferencia",
    "fluxos",
]
