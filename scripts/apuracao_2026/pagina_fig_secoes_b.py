"""Figuras do capítulo 12 no nível da seção eleitoral, parte 2.

`clusters_regiao` (grupo × região), `modelo_urna_uf` (modelos por UF),
`modelo_urna_zona` (diferença entre modelos dentro da zona e do prédio, com
intervalo, contra a diferença bruta) e `secoes_outras`
(recebimento, horários, arquivo, tipo de urna, cargas e contagens raras).
Lista vazia vira a frase "nenhuma seção nesta condição" dentro do painel.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    PAPER,
    REGIOES,
    Tips,
    area,
    botoes,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    pct,
    pp,
    r,
    registra,
    sobre,
    svg_abre,
    t,
)
from .pagina_fig_secoes import (
    OURO,
    nota_cobertura,
    regiao_da_uf,
    rotulo_cluster,
    secoes,
)

VAZIO = "nenhuma seção nesta condição"


def _rampa(n: int) -> list[str]:
    """n tons de um só matiz, do claro (mais velho) ao escuro (mais novo)."""
    claro, escuro = (0xF1, 0xE4, 0xC4), (0x3A, 0x29, 0x00)
    if n <= 1:
        return ["#7d5b00"]
    out = []
    for i in range(n):
        f = i / (n - 1)
        c = [round(a + (b - a) * f) for a, b in zip(claro, escuro, strict=True)]
        out.append("#{:02x}{:02x}{:02x}".format(*c))
    return out


# ------------------------------------------------------------------ 5 clusters_regiao


@registra("clusters_regiao")
def clusters_regiao(d, **_op) -> str:
    S = secoes(d)
    C = S["clusters"]
    linhas = C["cluster_regiao"]
    ids = sorted({x["cluster"] for x in linhas})
    regs = [*REGIOES, "Exterior"]
    w = 1100
    h = 40 + 52 * len(ids) + 20
    x0, x1 = 330, 1080
    out = [
        svg_abre(
            w,
            h,
            "Composição regional de cada grupo de seções",
            "Uma barra por grupo da mistura gaussiana, dividida pela região das seções que o compõem.",
        ),
        t(20, 26, "Grupo", 13, MUTED, weight="600"),
        t(x0, 26, "Parte das seções do grupo, por região", 13, MUTED, weight="600"),
    ]
    tips = Tips()
    y = 40
    for k in ids:
        out.append(t(20, y + 27, rotulo_cluster(S, k), 14, INK, weight="600"))
        cx = float(x0)
        partes = sorted(
            (x for x in linhas if x["cluster"] == k),
            key=lambda x: regs.index(x["regiao"]) if x["regiao"] in regs else 9,
        )
        for x in partes:
            larg = (x1 - x0) * (x["pct_do_cluster"] or 0) / 100
            cor = COR_REGIAO.get(x["regiao"], MUTED)
            chave = tips.add(
                ficha(
                    f"{rotulo_cluster(S, k)}: {x['regiao']}",
                    "",
                    [
                        ("Seções", inteiro(x["secoes"])),
                        ("Parte do grupo", pct(x["pct_do_cluster"], 1)),
                        ("Parte das seções da região", pct(x["pct_da_regiao"], 1)),
                    ],
                )
            )
            out.append(
                hit(
                    r(cx, y + 6, larg, 34, cor, f' stroke="{PAPER}" stroke-width="1"'),
                    chave,
                )
            )
            if larg > 96:
                out.append(
                    t(
                        cx + 6,
                        y + 28,
                        f"{x['regiao']} {num(x['pct_do_cluster'], 0)}%",
                        13,
                        sobre(cor),
                        weight="600",
                        extra=' pointer-events="none"',
                    )
                )
            cx += larg
        y += 52
    out.append("</svg>")
    presentes = [rg for rg in regs if any(x["regiao"] == rg for x in linhas)]
    leg = legenda_html([(rg, COR_REGIAO[rg]) for rg in presentes], "Região")
    interp = (C.get("interpretacao") or [""])[0]
    legenda = f"{escape(interp)} Cada barra soma 100% das seções do grupo. {nota_cobertura(S)} Fonte: secoes.json."
    return figura_html(
        "clusters_regiao", "".join(out), legenda, tips, minw=820, apos=leg
    )


# ------------------------------------------------------------------ 6 modelo_urna_uf


@registra("modelo_urna_uf")
def modelo_urna_uf(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    modelos = U["modelos"]
    cores = dict(zip(modelos, _rampa(len(modelos)), strict=True))
    por: dict[str, list[dict]] = {}
    for x in U["por_uf"]:
        por.setdefault(x["uf"], []).append(x)
    regs = [*REGIOES, "Exterior"]
    ufs = sorted(por, key=lambda u: (regs.index(regiao_da_uf(u)), u))
    linhas_y: list[tuple[str, str]] = []
    reg_ant = None
    for u in ufs:
        rg = regiao_da_uf(u)
        if rg != reg_ant:
            linhas_y.append(("reg", rg))
            reg_ant = rg
        linhas_y.append(("uf", u))
    w = 1100
    h = 30 + 26 * len(linhas_y) + 10
    x0, x1 = 90, 1080
    out = [
        svg_abre(
            w,
            h,
            "Modelos de urna por UF",
            "Uma barra por UF, dividida pela parte das seções em cada modelo de urna, do mais velho (claro) ao mais novo (escuro).",
        )
    ]
    for v in (0, 25, 50, 75, 100):
        xv = x0 + (x1 - x0) * v / 100
        out.append(t(xv, 20, f"{v}%", 13, MUTED, "middle", mono=True))
    tips = Tips()
    y = 30
    for tipo, val in linhas_y:
        if tipo == "reg":
            out.append(t(20, y + 18, val, 13, MUTED, weight="700"))
            out.append(ln(20, y + 2, x1, y + 2, GRADE, 0.8))
            y += 26
            continue
        out.append(t(60, y + 18, val, 14, INK, "end", "600"))
        cx = float(x0)
        partes = sorted(
            por[val],
            key=lambda x: modelos.index(x["modelo"]) if x["modelo"] in modelos else 99,
        )
        for x in partes:
            larg = (x1 - x0) * (x["pct_da_uf"] or 0) / 100
            cor = cores.get(x["modelo"], MUTED)
            k = tips.add(
                ficha(
                    f"{NOME_UF.get(val, val)}: {x['modelo']}",
                    "",
                    [
                        ("Seções", inteiro(x["secoes"])),
                        ("Parte das seções da UF", pct(x["pct_da_uf"], 1)),
                    ],
                )
            )
            out.append(
                hit(
                    r(
                        cx,
                        y + 2,
                        larg,
                        20,
                        cor,
                        f' stroke="{PAPER}" stroke-width="0.8"',
                    ),
                    k,
                )
            )
            if larg > 84:
                out.append(
                    t(
                        cx + 5,
                        y + 17,
                        f"{x['modelo']} {num(x['pct_da_uf'], 0)}%",
                        13,
                        sobre(cor),
                        extra=' pointer-events="none"',
                    )
                )
            cx += larg
        y += 26
    out.append("</svg>")
    leg = legenda_html(
        [(m, cores[m]) for m in modelos], "Modelo de urna, do mais velho ao mais novo"
    )
    fontes = "; ".join(
        f"{escape(f['modelo_fonte'])}: {inteiro(f['secoes'])} seções"
        for f in U.get("fonte_modelo", [])
    )
    legenda = f"UFs agrupadas por região. Origem do modelo: {fontes}. {nota_cobertura(S)} Fonte: secoes.json."
    return figura_html(
        "modelo_urna_uf", "".join(out), legenda, tips, minw=820, apos=leg
    )


# ------------------------------------------------------------------ 7 modelo_urna_zona

METRICAS = [
    ("flavio_pp", "Flávio", "% dos válidos", FLAVIO),
    ("lula_pp", "Lula", "% dos válidos", LULA),
    ("abstencao_pp", "Abstenção", "% dos aptos", INK),
    ("brancos_pp", "Brancos", "% do comparecimento", MUTED),
    ("nulos_pp", "Nulos", "% do comparecimento", MUTED),
]


def _limite(U: dict, chave: str) -> float:
    vals = [0.5]
    for est in ("dentro_zona", "dentro_local", "zona_2022"):
        for par in (U.get(est) or {}).get("pares", []):
            m = par.get(chave) or {}
            for v in [m.get("estimativa"), m.get("bruto"), *(m.get("ic95") or [])]:
                if v is not None:
                    vals.append(abs(v))
    return max(vals) * 1.1


def _painel_estimador(U: dict, est: str, tips: Tips, topo: float) -> str:
    pares = (U.get(est) or {}).get("pares", [])
    nome_est = {
        "dentro_zona": "dentro da zona",
        "dentro_local": "dentro do mesmo local",
        "zona_2022": "dentro da zona, 1º turno de 2022",
    }.get(est, est)
    out = []
    if not pares:
        out.append(t(560, topo + 40, VAZIO, 14, MUTED, "middle"))
        return "".join(out)
    lx, larg, gap = 180, 168, 14
    for j, (chave, nome, base, cor) in enumerate(METRICAS):
        if est == "zona_2022" and chave == "flavio_pp":
            nome = "Bolsonaro"
        px = lx + j * (larg + gap)
        lim = _limite(U, chave)
        X = escala(-lim, lim, px + 6, px + larg - 6)
        yb = topo + 40 * len(pares) + 6
        out.append(r(px, topo - 4, larg, yb - topo + 8, "#efe9da"))
        out.append(ln(X(0), topo - 4, X(0), yb + 4, INK, 1.5))
        for v, anc in ((-lim / 1.1, "start"), (lim / 1.1, "end")):
            vv = float(f"{v:.2g}")
            out.append(ln(X(vv), yb + 4, X(vv), yb + 9, MUTED))
            xt = px + 2 if anc == "start" else px + larg - 2
            out.append(
                t(xt, yb + 24, pp(vv, 1).replace(" pp", ""), 13, MUTED, anc, mono=True)
            )
        out.append(t(X(0), yb + 24, "0", 13, MUTED, "middle", mono=True))
        if j == 0:
            out.append(t(lx - 10, yb + 24, "pp", 13, MUTED, "end", mono=True))
        for i, par in enumerate(pares):
            m = par.get(chave) or {}
            y = topo + 18 + 40 * i
            e, ic, b = (
                m.get("estimativa"),
                m.get("ic95") or [None, None],
                m.get("bruto"),
            )
            g = []
            if ic[0] is not None and ic[1] is not None:
                g.append(ln(X(ic[0]), y, X(ic[1]), y, cor, 3))
            if b is not None:
                g.append(
                    f'<rect x="{X(b) - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{PAPER}" '
                    f'stroke="{cor}" stroke-width="2" transform="rotate(45 {X(b):.1f} {y:.1f})"/>'
                )
            if e is not None:
                g.append(
                    f'<circle cx="{X(e):.1f}" cy="{y:.1f}" r="5.5" fill="{cor}" stroke="{PAPER}" stroke-width="1"/>'
                )
            k = tips.add(
                ficha(
                    f"{par['b']} menos {par['a']}: {nome}",
                    nome_est,
                    [
                        ("Estimativa", pp(e, 2)),
                        ("Intervalo de 95%", f"{pp(ic[0], 2)} a {pp(ic[1], 2)}"),
                        ("Diferença bruta", pp(b, 2)),
                        ("Unidades com os dois", inteiro(par.get("unidades"))),
                        (
                            f"Seções {par['a']} · {par['b']}",
                            f"{inteiro(par.get('secoes_a'))} · {inteiro(par.get('secoes_b'))}",
                        ),
                        (
                            f"Votantes {par['a']} · {par['b']}",
                            f"{inteiro(par.get('votantes_a'))} · {inteiro(par.get('votantes_b'))}",
                        ),
                    ],
                    f"base: {base}",
                )
            )
            out.append(hit("".join(g) + area(px, y - 18, larg, 36), k))
        out.append(
            t(
                px + larg / 2,
                topo - 32,
                nome,
                14,
                cor if cor != MUTED else INK,
                "middle",
                "700",
            )
        )
        out.append(t(px + larg / 2, topo - 14, base, 13, MUTED, "middle"))
    for i, par in enumerate(pares):
        y = topo + 18 + 40 * i
        out.append(t(lx - 14, y + 5, f"{par['b']} − {par['a']}", 14, INK, "end", "600"))
    return "".join(out)


@registra("modelo_urna_zona")
def modelo_urna_zona(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    todos22 = ((U.get("ano_2022") or {}).get("dentro_zona") or {}).get("pares", [])
    n26 = max(
        len((U.get("dentro_zona") or {}).get("pares", [])),
        len((U.get("dentro_local") or {}).get("pares", [])),
        1,
    )
    # 2022 tem muitos pares; mostra os de mais zonas, no máximo o número de linhas de 2026 (ou 6)
    p22 = sorted(todos22, key=lambda x: -(x.get("unidades") or 0))[: max(n26, 6)]
    U22 = (
        {
            "zona_2022": {
                "pares": [
                    {**x, "flavio_pp": x.get("bolsonaro_pp", x.get("flavio_pp"))}
                    for x in p22
                ]
            }
        }
        if p22
        else None
    )
    U = {**U, **(U22 or {})}
    n = max(
        len(p22),
        len((U.get("dentro_zona") or {}).get("pares", [])),
        len((U.get("dentro_local") or {}).get("pares", [])),
        1,
    )
    w = 1100
    topo = 70
    h = topo + 40 * n + 50
    tips = Tips()
    out = [
        svg_abre(
            w,
            h,
            "Diferença entre modelos de urna dentro da mesma zona",
            "Para cada par de modelos, a diferença do mais novo menos o mais velho em Flávio, Lula, abstenção, brancos e nulos: "
            "ponto cheio com intervalo de 95% controlando pela zona, losango vazado sem controle.",
        ),
        f'<g data-alt-show="dentro_zona">{_painel_estimador(U, "dentro_zona", tips, topo)}</g>',
        f'<g data-alt-show="dentro_local" display="none">{_painel_estimador(U, "dentro_local", tips, topo)}</g>',
        (
            f'<g data-alt-show="zona_2022" display="none">{_painel_estimador(U, "zona_2022", tips, topo)}</g>'
            if U22
            else ""
        ),
        "</svg>",
    ]
    ctl = botoes(
        [("dentro_zona", "Dentro da zona"), ("dentro_local", "Dentro do mesmo prédio")]
        + ([("zona_2022", "2022, dentro da zona")] if U22 else []),
        "dentro_zona",
        "Comparação",
    )
    dz = U.get("dentro_zona") or {}
    leg = legenda_html(
        [
            ("estimativa com controle (ponto) e intervalo de 95% (traço)", INK),
            ("diferença bruta, sem controle (losango vazado)", PAPER),
        ]
    )
    legenda = (
        f"{escape((U.get('interpretacao') or [''])[0])} Diferença = modelo mais novo menos o mais velho, em pontos. "
        f"Intervalo por bootstrap de {inteiro(dz.get('bootstrap'))} reamostras de zonas (ou de locais), com ao menos "
        f"{dz.get('minimo_secoes_por_modelo', 's/d')} seções de cada modelo na zona. A distância entre o losango e o ponto é "
        f"o que a geografia inflava."
        + (
            f" Em 2022, Bolsonaro no lugar de Flávio, com os {len(p22)} pares de mais zonas entre {len(todos22)}."
            if todos22
            else ""
        )
        + f" {nota_cobertura(S)} Fonte: secoes.json."
    )
    return figura_html(
        "modelo_urna_zona",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=900,
        apos=leg,
    )


# ------------------------------------------------------------------ 8 secoes_outras

PW, PH = 340, 250


def _vazio(px: float, py: float) -> str:
    return r(px, py + 40, PW, PH - 70, "#efe9da") + t(
        px + PW / 2, py + 40 + (PH - 70) / 2 + 5, VAZIO, 14, MUTED, "middle"
    )


def _hora_rot(h) -> str:
    """'2026-10-04 17' vira '17h'; '2026-10-05 00' vira '00h (05/10)'; inteiro 17 vira '17h'."""
    h = str(h)
    if len(h) <= 2:
        return f"{int(h):02d}h"
    hh = h[-2:]
    return f"{hh}h" + (" (05/10)" if h[:10].endswith("-05") else "")


def _painel_recebimento(OD: dict, px: float, py: float, tips: Tips) -> str:
    rec = OD["recebimento"]["por_hora"]
    out = [
        t(px, py + 18, "Seções recebidas por hora", 14, INK, weight="700"),
        t(px, py + 36, "barras: seções; pontos: Lula, % dos válidos", 13, MUTED),
    ]
    if not rec:
        return "".join(out) + _vazio(px, py)
    vmax = max(x["secoes"] for x in rec) or 1
    y0, y1 = py + 60, py + PH - 30
    bw = PW / len(rec)
    Y = escala(0, vmax, y1, y0)
    Yp = escala(0, 100, y1, y0)
    pts = []
    for i, x in enumerate(rec):
        bx = px + i * bw
        k = tips.add(
            ficha(
                f"Recebidas às {_hora_rot(x['hora'])}",
                "hora de Brasília",
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Válidos", inteiro(x.get("validos"))),
                    ("Lula", pct(x.get("lula_pct"), 1)),
                    ("Flávio", pct(x.get("flavio_pct"), 1)),
                ],
            )
        )
        out.append(
            hit(
                r(bx + 1, Y(x["secoes"]), bw - 2, y1 - Y(x["secoes"]), "#b9c6bd")
                + area(bx, y0, bw, y1 - y0),
                k,
            )
        )
        if x.get("lula_pct") is not None:
            pts.append((bx + bw / 2, Yp(x["lula_pct"])))
        if len(rec) <= 12 or i % 2 == 0:
            out.append(
                t(
                    bx + bw / 2,
                    y1 + 18,
                    _hora_rot(x["hora"])[:3],
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
    if pts:
        out.append(
            f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{LULA}" '
            'stroke-width="1.8" pointer-events="none"/>'
        )
        out.append(
            "".join(
                f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3" fill="{LULA}" pointer-events="none"/>'
                for a, b in pts
            )
        )
    out.append(ln(px, y1, px + PW, y1, INK))
    return "".join(out)


def _painel_encerramento(OD: dict, px: float, py: float, tips: Tips) -> str:
    H = OD["horarios"]
    hist = H.get("histograma_encerramento") or []
    out = [
        t(px, py + 18, "Hora de encerramento da urna", 14, INK, weight="700"),
        t(px, py + 36, "hora de Brasília", 13, MUTED),
    ]
    if not hist:
        return "".join(out) + _vazio(px, py)
    vmax = max(x["secoes"] for x in hist) or 1
    y0, y1 = py + 60, py + PH - 30
    bw = PW / len(hist)
    Y = escala(0, vmax, y1, y0)
    enc = H.get("encerramento") or {}
    for i, x in enumerate(hist):
        bx = px + i * bw
        k = tips.add(
            ficha(
                f"Encerradas às {_hora_rot(x['hora'])}",
                "hora de Brasília",
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Depois das 18h, no total", inteiro(enc.get("depois_1800"))),
                    ("Depois das 19h", inteiro(enc.get("depois_1900"))),
                    ("Depois das 20h", inteiro(enc.get("depois_2000"))),
                ],
            )
        )
        out.append(
            hit(
                r(bx + 1, Y(x["secoes"]), bw - 2, y1 - Y(x["secoes"]), "#7fb19e")
                + area(bx, y0, bw, y1 - y0),
                k,
            )
        )
        if len(hist) <= 14 or i % 2 == 0:
            out.append(
                t(
                    bx + bw / 2,
                    y1 + 18,
                    _hora_rot(x["hora"])[:3],
                    13,
                    MUTED,
                    "middle",
                    mono=True,
                )
            )
    out.append(ln(px, y1, px + PW, y1, INK))
    return "".join(out)


def _painel_tipo(
    lista: list[dict], chave: str, titulo: str, px: float, py: float, tips: Tips
) -> str:
    out = [
        t(px, py + 18, titulo, 14, INK, weight="700"),
        t(px, py + 36, "seções (escala de raiz) e diferença para a zona", 13, MUTED),
    ]
    if not lista:
        return "".join(out) + _vazio(px, py)
    vmax = max(x.get("secoes") or 0 for x in lista) or 1
    y = py + 52
    passo = min(44, (PH - 60) / len(lista))
    for x in lista:
        rot = x.get("descricao") or f"{chave} {x.get(chave)}"
        larg = (PW - 150) * ((x.get("secoes") or 0) / vmax) ** 0.5
        k = tips.add(
            ficha(
                f"{titulo}: {rot}",
                f"{chave} = {x.get(chave)}",
                [
                    ("Seções", inteiro(x.get("secoes"))),
                    ("Votantes", inteiro(x.get("votantes"))),
                    (
                        "Flávio · Lula",
                        f"{pct(x.get('flavio_pct'), 1)} · {pct(x.get('lula_pct'), 1)}",
                    ),
                    (
                        "Flávio contra o resto da zona",
                        pp(x.get("dif_zona_flavio_pp"), 2),
                    ),
                    ("Lula contra o resto da zona", pp(x.get("dif_zona_lula_pp"), 2)),
                ],
                "média ponderada de seção menos resto da zona",
            )
        )
        out.append(t(px, y + 13, str(rot)[:30], 13, INK))
        g = r(px, y + 17, larg, 9, "#535b54")
        out.append(hit(g + area(px, y - 2, PW, passo), k))
        out.append(
            t(px + larg + 6, y + 26, inteiro(x.get("secoes")), 13, INK, mono=True)
        )
        out.append(
            t(
                px + PW,
                y + 13,
                f"L {pp(x.get('dif_zona_lula_pp'), 1)} · F {pp(x.get('dif_zona_flavio_pp'), 1)}",
                13,
                MUTED,
                "end",
                mono=True,
            )
        )
        y += passo
    return "".join(out)


def _painel_raros(OD: dict, px: float, py: float, tips: Tips) -> str:
    cp = OD["comparecimento"]
    zv = OD["zero_votos"]
    rc = OD["recebimento"]
    itens = [
        ("Comparecimento acima de 100%", cp.get("acima_100")),
        ("Comparecimento de 100%", cp.get("igual_100")),
        ("Abstenção zero", cp.get("abstencao_zero")),
        (
            f"Lula com zero votos ({zv.get('minimo_votantes')}+ votantes)",
            (zv.get("lula") or {}).get("secoes"),
        ),
        (
            f"Flávio com zero votos ({zv.get('minimo_votantes')}+ votantes)",
            (zv.get("flavio") or {}).get("secoes"),
        ),
        ("Recebidas depois de 00h", (rc.get("depois_0000") or {}).get("secoes")),
        ("Recebidas depois de 01h", (rc.get("depois_0100") or {}).get("secoes")),
    ]
    out = [
        t(px, py + 18, "Condições raras", 14, INK, weight="700"),
        t(px, py + 36, "número de seções", 13, MUTED),
    ]
    y = py + 58
    for rot, v in itens:
        k = tips.add(ficha(rot, "seções", [("Seções", inteiro(v))]))
        cor = OURO if v else MUTED
        out.append(hit(t(px, y + 4, rot, 13, INK) + area(px, y - 13, PW, 24), k))
        out.append(
            t(
                px + PW,
                y + 4,
                inteiro(v) if v else "0",
                14,
                cor,
                "end",
                "700",
                mono=True,
            )
        )
        out.append(ln(px, y + 10, px + PW, y + 10, GRADE, 0.8))
        y += 26
    return "".join(out)


@registra("secoes_outras")
def secoes_outras(d, **_op) -> str:
    S = secoes(d)
    OD = S["outras"]
    tips = Tips()
    w, h = 1100, 2 * PH + 40
    col = [20, 380, 740]
    lin = [10, PH + 30]
    out = [
        svg_abre(
            w,
            h,
            "O que mais a seção mostra: recebimento, horários, arquivos, urnas e condições raras",
            "Seis painéis: seções recebidas por hora com a parte de Lula, hora de encerramento, tipo de arquivo, tipo de urna, "
            "número de cargas e contagem de condições raras.",
        ),
        _painel_recebimento(OD, col[0], lin[0], tips),
        _painel_encerramento(OD, col[1], lin[0], tips),
        _painel_raros(OD, col[2], lin[0], tips),
        _painel_tipo(
            OD.get("tipo_arquivo") or [],
            "tipo_arquivo",
            "Tipo de arquivo",
            col[0],
            lin[1],
            tips,
        ),
        _painel_tipo(
            OD.get("tipo_urna") or [], "tipo_urna", "Tipo de urna", col[1], lin[1], tips
        ),
        _painel_tipo(
            OD.get("cargas") or [], "n_cargas", "Cargas da urna", col[2], lin[1], tips
        ),
        "</svg>",
    ]
    legenda = (
        "Cada painel responde a uma pergunta da seção. Nos três de baixo, L e F são a diferença média ponderada entre as "
        "seções do grupo e o resto da mesma zona, para Lula e Flávio, em pontos. Hora de Brasília. "
        f"{nota_cobertura(S)} Fonte: secoes.json."
    )
    return figura_html("secoes_outras", "".join(out), legenda, tips, minw=900)


__all__ = ["VAZIO"]
