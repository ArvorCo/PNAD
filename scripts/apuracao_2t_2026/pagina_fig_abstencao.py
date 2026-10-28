"""Figuras do capítulo "A abstenção mais baixa" (2º turno de 2026).

Fontes: ``abstencao.json`` (UFs, regiões, capitais e interior, histogramas) e
``comparacao_1t.json`` (abstenção por município nos dois turnos, para os mapas
municipais e os quintis). A ponte TSE para IBGE vem de ``presidente.json``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, num
from apuracao_2026.pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    MUTED,
    PAPER,
    Tips,
    area,
    botoes,
    escala,
    ficha,
    figura_html,
    hit,
    legenda,
    legenda_html,
    ln,
    nome_bonito,
    pct,
    pp,
    r,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_mapas import mapa_uf

from .pagina_fig_turnos_util import faixa, ibge_por_tse, linhas_de, mapa_mun, nome_uf

COR_2T = "#0b6650"
COR_1T = "#7d5b00"
COR_22 = "#535b54"
ALTA = "#6b4a92"
NIVEL_CORES = ["#f1ecdc", "#c9dfd3", "#86b8a3", "#3f8a73", "#17594a", "#0a3229"]
NIVEL_CORTES = [12, 15, 18, 21, 25]
NIVEL_ROT = [
    "abaixo de 12%",
    "12 a 15%",
    "15 a 18%",
    "18 a 21%",
    "21 a 25%",
    "25% ou mais",
]
DELTA_CORES = [
    "#0d3f35",
    "#2f7a66",
    "#9cc7b6",
    "#ece7da",
    "#d9b8e3",
    "#9a6bb5",
    "#5a2f78",
]
DELTA_CORTES = [-3, -2, -0.5, 0.5, 2, 5]
DELTA_ROT = [
    "caiu 3 pp ou mais",
    "caiu 2 a 3 pp",
    "caiu 0,5 a 2 pp",
    "quase igual",
    "subiu 0,5 a 2 pp",
    "subiu 2 a 5 pp",
    "subiu 5 pp ou mais",
]
UFS_MAPA = ["BA", "PE", "CE", "SP"]


def _universo(A: dict) -> str:
    """Rótulo do universo municipal: o país inteiro quando a versão lida está completa."""
    if (A.get("meta") or {}).get("pst_nacional") == 100.0:
        return f"todos os {(A.get('brasil') or {}).get('n_municipios', 0):,} municípios, completos".replace(
            ",", "."
        )
    return "municípios completos"


def _uf_valores(u: dict) -> tuple[float, float]:
    """Abstenção do arquivo da UF quando existe (2º e 1º turno); senão, municípios completos."""
    a = u.get("arquivo_uf") or {}
    return a.get("pa_2t", u["pa_2t"]), a.get("pa_1t", u["pa_1t_mesmos"])


def fig_ranking(A: dict) -> str:
    ufs = sorted(A["ufs"], key=lambda u: _uf_valores(u)[0])
    tips = Tips()
    passo = 24
    rot_w, x0, x1, topo = 150, 160, 900, 56
    h = topo + passo * len(ufs) + 46
    vmax = max(max(_uf_valores(u)) for u in ufs) * 1.08
    vmax = max(vmax, max(u["pa_2022_2t_mesmos"] for u in ufs) * 1.05)
    fx = escala(0, vmax, x0, x1)
    out = [
        svg_abre(
            1000,
            h,
            "Abstenção por UF no 2º turno, com o 1º turno e 2022",
            "Barra: abstenção no 2º turno. Ponto dourado: 1º turno de 2026. Quadrado cinza: 2º turno de 2022 nos mesmos municípios.",
        )
    ]
    out.append(
        legenda(
            [
                ("2º turno 2026", COR_2T),
                ("1º turno 2026", COR_1T),
                ("2º turno 2022", COR_22),
            ],
            x0,
            26,
            13.5,
        )
    )
    for v in ticks(0, vmax, 6):
        out.append(ln(fx(v), topo - 8, fx(v), h - 34, GRADE, 1))
        out.append(t(fx(v), h - 16, f"{num(v, 0)}%", 12, MUTED, "middle", mono=True))
    for i, u in enumerate(ufs):
        y = topo + i * passo
        a2, a1 = _uf_valores(u)
        subiu = a2 > a1
        cor_rot = ALTA if subiu else INK
        partes = [
            t(
                rot_w - 6,
                y + 5,
                f"{nome_uf(u['uf'])}{' ↑' if subiu else ''}",
                13,
                cor_rot,
                "end",
                "700" if subiu else None,
            ),
            r(x0, y - 7, fx(a2) - x0, 14, ALTA if subiu else COR_2T),
            t(
                fx(max(a2, a1, u["pa_2022_2t_mesmos"])) + 10,
                y + 5,
                f"{num(a2, 2)}%  ({pp(a2 - a1)})",
                12,
                INK,
                mono=True,
            ),
            f'<rect x="{fx(u["pa_2022_2t_mesmos"]) - 4:.1f}" y="{y - 4:.1f}" width="8" height="8" fill="{PAPER}" stroke="{COR_22}" stroke-width="1.6"/>',
            f'<circle cx="{fx(a1):.1f}" cy="{y:.1f}" r="4.6" fill="{COR_1T}" stroke="{PAPER}" stroke-width="1"/>',
            area(0, y - passo / 2, 1000, passo),
        ]
        k = tips.add(
            ficha(
                nome_uf(u["uf"]),
                f"{inteiro(u['n_municipios'])} municípios, {inteiro(u['aptos'])} eleitores",
                [
                    ("2º turno 2026", pct(a2)),
                    ("1º turno 2026", pct(a1)),
                    ("Mudança contra o 1º turno", pp(a2 - a1)),
                    ("2º turno 2022, mesmos municípios", pct(u["pa_2022_2t_mesmos"])),
                    ("Mudança contra 2022", pp(u["delta_2022_pp"])),
                ],
            )
        )
        out.append(hit("".join(partes), k))
    out.append("</svg>")
    subiram = [u["uf"] for u in ufs if _uf_valores(u)[0] > _uf_valores(u)[1]]
    legenda_txt = (
        f"Barras em roxo e seta: as {len(subiram)} UFs em que a abstenção subiu contra o 1º turno ({', '.join(subiram)}). "
        f"Abstenção do arquivo de presidente da UF; 2022 nos {_universo(A)}. Fonte: abstencao.json (ufs)."
    )
    return figura_html(
        "ab_ranking", "".join(out), legenda_txt, tips, modo="scroll", minw=760
    )


def fig_mapa_delta(A: dict) -> str:
    vals = {u["uf"]: u for u in A["ufs"]}

    def delta(u):
        a2, a1 = _uf_valores(u)
        return a2 - a1

    def cor(uf, u):
        return "#d8d4c8" if not u else DELTA_CORES[faixa(delta(u), DELTA_CORTES)]

    svg = mapa_uf(
        vals,
        cor,
        lambda uf, u: uf,
        lambda uf, u: (
            f"{nome_uf(uf)}: abstenção {pct(_uf_valores(u)[0])} ({pp(delta(u))} contra o 1º turno)"
            if u
            else uf
        ),
        "Mudança da abstenção por UF, 1º para 2º turno",
        "Mapa do Brasil por UF: verde, a abstenção caiu; roxo, subiu.",
        escuro=lambda uf, u: bool(u) and faixa(delta(u), DELTA_CORTES) in (0, 1, 5, 6),
    )
    leg = legenda_html(
        list(zip(DELTA_ROT, DELTA_CORES, strict=True)), "Mudança da abstenção, pontos"
    )
    subiram = sorted(uf for uf, u in vals.items() if delta(u) > 0)
    legenda_txt = (
        f"Verde: a abstenção caiu; roxo: subiu ({', '.join(subiram)}). Todo o Norte sobe; Maranhão e Piauí, no Nordeste, "
        "também. Fonte: abstencao.json (ufs, arquivo da UF)."
        if {"MA", "PI"} <= set(subiram)
        else f"Verde: a abstenção caiu; roxo: subiu ({', '.join(subiram)}). Fonte: abstencao.json (ufs, arquivo da UF)."
    )
    return figura_html("ab_mapa_delta", svg, legenda_txt, Tips(), modo="fit", apos=leg)


def fig_mapas_mun(d, C1: dict) -> str:
    ponte = ibge_por_tse(d)
    if not ponte:
        return ""
    ms = [m for m in linhas_de(C1["municipios"]) if m.get("completo")]
    blocos, abas = [], []
    for k, uf in enumerate(UFS_MAPA):
        cor, tip = {}, {}
        for m in ms:
            if m["uf"] != uf or m["cd_tse"] not in ponte:
                continue
            ib = ponte[m["cd_tse"]]
            v = m["t2_pct_abstencao"]
            cor[ib] = NIVEL_CORES[faixa(v, NIVEL_CORTES)]
            tip[ib] = (
                f"{nome_bonito(m['nome'])}: {num(v, 1)}% ({pp(m['delta_abstencao_pp'], 1)} contra o 1º turno)"
            )
        svg = mapa_mun(
            uf,
            cor,
            tip,
            f"{nome_uf(uf)}: abstenção no 2º turno",
            f"Municípios de {nome_uf(uf)} pela abstenção no 2º turno.",
            560,
            520,
        )
        if svg is None:
            continue
        blocos.append(
            f'<div data-alt-show="{uf}"{"" if k == 0 else " hidden"}>{svg}</div>'
        )
        abas.append((uf, nome_uf(uf)))
    if not blocos:
        return ""
    leg = legenda_html(
        list(zip(NIVEL_ROT, NIVEL_CORES, strict=True)), "Abstenção no 2º turno"
    )
    legenda_txt = (
        "Cada município pela abstenção sobre o eleitorado no 2º turno. Abas trocam o estado. "
        "Fontes: comparacao_1t.json (municípios), presidente.json (código IBGE) e malha do IBGE."
    )
    return figura_html(
        "ab_mapas_mun",
        "".join(blocos),
        legenda_txt,
        Tips(),
        controles=botoes(abas, abas[0][0], "Estado", "tab"),
        modo="fit",
        apos=leg,
    )


def _hist(
    caixas: list[dict],
    ident: str,
    mostra: bool,
    rot_x: str,
    marca: float | None,
    tips: Tips,
) -> str:
    x0, x1, y0, y1 = 80, 980, 50, 380
    lo, hi = caixas[0]["de"], caixas[-1]["ate"]
    fx = escala(lo, hi, x0, x1)
    vmax = max(c["n"] for c in caixas) or 1
    fy = escala(0, vmax * 1.1, y1, y0)
    g = [f'<g data-alt-show="{ident}"{"" if mostra else " display=none"}>']
    for v in ticks(0, vmax * 1.1, 4):
        g.append(ln(x0, fy(v), x1, fy(v), GRADE, 1))
        g.append(t(x0 - 8, fy(v) + 4, inteiro(v), 12, MUTED, "end", mono=True))
    for c in caixas:
        xa, xb = fx(c["de"]), fx(c["ate"])
        cor = ALTA if c["de"] >= 0 and ident == "delta" else COR_2T
        k = tips.add(
            ficha(
                f"De {num(c['de'], 1)} a {num(c['ate'], 1)}",
                rot_x,
                [("Municípios", inteiro(c["n"])), ("Eleitores", inteiro(c["aptos"]))],
            )
        )
        g.append(
            hit(
                r(xa + 0.5, fy(c["n"]), max(xb - xa - 1, 0.5), y1 - fy(c["n"]), cor)
                + area(xa, y0, xb - xa, y1 - y0),
                k,
            )
        )
    g.append(ln(x0, y1, x1, y1, INK, 1.2))
    for v in ticks(lo, hi, 10):
        g.append(
            t(
                fx(v),
                y1 + 20,
                num(v, 0).replace("-", "−"),
                12,
                MUTED,
                "middle",
                mono=True,
            )
        )
    g.append(t((x0 + x1) / 2, y1 + 44, rot_x, 13, INK, "middle"))
    if marca is not None and lo < marca < hi:
        g.append(ln(fx(marca), y0, fx(marca), y1, INK, 1.6, ' stroke-dasharray="4 3"'))
        g.append(
            t(
                fx(marca) + 6,
                y0 + 12,
                f"Brasil: {num(marca, 2)}",
                12.5,
                INK,
                weight="700",
            )
        )
    g.append(t(x0, 30, "municípios em cada faixa", 13, INK, weight="700"))
    g.append("</g>")
    return "".join(g)


def fig_histograma(A: dict) -> str:
    tips = Tips()
    corpo = _hist(
        A["histograma_pa_2t"]["caixas"],
        "nivel",
        True,
        "abstenção no 2º turno, % do eleitorado",
        A["brasil"]["pa_2t"],
        tips,
    )
    corpo += _hist(
        A["histograma_delta_1t"]["caixas"],
        "delta",
        False,
        "mudança contra o 1º turno, pontos",
        A["brasil"]["delta_1t_pp"],
        tips,
    )
    svg = (
        svg_abre(
            1000,
            440,
            "Distribuição da abstenção municipal no 2º turno",
            "Histograma dos municípios pela abstenção e pela mudança contra o 1º turno.",
        )
        + corpo
        + "</svg>"
    )
    abas = botoes(
        [("nivel", "Abstenção no 2º turno"), ("delta", "Mudança contra o 1º turno")],
        "nivel",
        "Mostrar",
        "tab",
    )
    legenda_txt = (
        f"A abstenção caiu em {inteiro(A['n_municipios_caiu_vs_1t'])} municípios e subiu em {inteiro(A['n_municipios_subiu_vs_1t'])}. "
        "Na aba da mudança, as barras roxas são os municípios em que ela subiu; a cauda longa à direita vem do Norte. Fonte: abstencao.json."
    )
    return figura_html(
        "ab_histograma", svg, legenda_txt, tips, controles=abas, modo="scroll", minw=760
    )


def fig_recortes(A: dict) -> str:
    """Barras agrupadas: 2022, 1º turno e 2º turno para capitais, interior e regiões."""
    ci = A["capitais_x_interior"]
    grupos = [("Capitais", ci["capitais"]), ("Interior", ci["interior"])]
    grupos += [(x["regiao"], x) for x in A["regioes"]]
    tips = Tips()
    w, h = 1000, 430
    x0, x1, y0, y1 = 70, 980, 60, 360
    vmax = (
        max(
            max(g["pa_2t"], g["pa_1t_mesmos"], g["pa_2022_2t_mesmos"])
            for _, g in grupos
        )
        * 1.12
    )
    fy = escala(0, vmax, y1, y0)
    passo = (x1 - x0) / len(grupos)
    bw = passo * 0.24
    out = [
        svg_abre(
            w,
            h,
            "Abstenção em capitais, interior e regiões",
            "Três barras por recorte: 2º turno de 2022, 1º turno e 2º turno de 2026.",
        )
    ]
    out.append(
        legenda(
            [
                ("2º turno 2022", COR_22),
                ("1º turno 2026", COR_1T),
                ("2º turno 2026", COR_2T),
            ],
            x0,
            26,
            13.5,
        )
    )
    for v in ticks(0, vmax, 5):
        out.append(ln(x0, fy(v), x1, fy(v), GRADE, 1))
        out.append(t(x0 - 8, fy(v) + 4, f"{num(v, 0)}%", 12, MUTED, "end", mono=True))
    for i, (nome, g) in enumerate(grupos):
        cx = x0 + passo * (i + 0.5)
        partes = []
        for j, (ch, cor) in enumerate(
            (("pa_2022_2t_mesmos", COR_22), ("pa_1t_mesmos", COR_1T), ("pa_2t", COR_2T))
        ):
            x = cx + (j - 1.5) * bw
            partes.append(r(x, fy(g[ch]), bw - 3, y1 - fy(g[ch]), cor))
            partes.append(
                t(
                    x + bw / 2 - 1.5,
                    fy(g[ch]) - 5,
                    num(g[ch], 1),
                    11,
                    INK,
                    "middle",
                    mono=True,
                )
            )
        partes.append(t(cx, y1 + 22, nome, 13, INK, "middle", "700"))
        partes.append(
            t(
                cx,
                y1 + 40,
                pp(g["delta_1t_pp"]),
                12,
                ALTA if g["delta_1t_pp"] > 0 else COR_2T,
                "middle",
                "700",
                mono=True,
            )
        )
        partes.append(area(cx - passo / 2, y0, passo, h - y0))
        k = tips.add(
            ficha(
                nome,
                f"{inteiro(g['n_municipios'])} municípios",
                [
                    ("2º turno 2026", pct(g["pa_2t"])),
                    ("1º turno 2026", pct(g["pa_1t_mesmos"])),
                    ("2º turno 2022", pct(g["pa_2022_2t_mesmos"])),
                    ("Contra o 1º turno", pp(g["delta_1t_pp"])),
                    ("Contra 2022", pp(g["delta_2022_pp"])),
                ],
            )
        )
        out.append(hit("".join(partes), k))
    out.append(
        t(x0, h - 10, "embaixo de cada recorte: mudança contra o 1º turno", 12, MUTED)
    )
    out.append("</svg>")
    legenda_txt = f"Mesmos municípios nos três momentos ({_universo(A)}, sem exterior). Fonte: abstencao.json (capitais_x_interior, regioes)."
    return figura_html(
        "ab_recortes", "".join(out), legenda_txt, tips, modo="scroll", minw=760
    )


def quintis(
    ms: list[dict], chave_ordem: str, chave_valor: str, n: int = 5
) -> list[dict]:
    """Quintis de municípios por ``chave_ordem``; média de ``chave_valor`` ponderada pelo eleitorado."""
    ms = sorted(ms, key=lambda m: m[chave_ordem])
    out = []
    for q in range(n):
        g = ms[q * len(ms) // n : (q + 1) * len(ms) // n]
        te = sum(m["aptos"] for m in g) or 1
        out.append(
            {
                "q": q + 1,
                "de": g[0][chave_ordem],
                "ate": g[-1][chave_ordem],
                "n": len(g),
                "aptos": te,
                "valor": sum(m[chave_valor] * m["aptos"] for m in g) / te,
            }
        )
    return out


def _n0(v: float) -> str:
    return num(v, 0).replace("-", "−")


def _painel_quintis(
    qs: list[dict],
    x0: float,
    titulo: str,
    rot_q: str,
    cor: str,
    tips: Tips,
    espelho: bool = False,
) -> str:
    w, y0, y1 = 440, 70, 300
    vmin = min(min(q["valor"] for q in qs) * 1.25, -0.5)
    vmax = max([0, *[q["valor"] * 1.25 for q in qs]])
    if espelho:
        vmax = max(abs(vmin), abs(vmax))
        vmin = -vmax
    fy = escala(vmin, vmax, y1, y0)
    passo = w / len(qs)
    out = [
        t(x0, 30, titulo, 13.5, INK, weight="700"),
        ln(x0, fy(0), x0 + w, fy(0), INK, 1.2),
    ]
    for v in ticks(vmin, vmax, 4):
        out.append(ln(x0, fy(v), x0 + w, fy(v), GRADE, 1))
        out.append(
            t(
                x0 - 6,
                fy(v) + 4,
                num(v, 0).replace("-", "−"),
                11.5,
                MUTED,
                "end",
                mono=True,
            )
        )
    for i, q in enumerate(qs):
        cx = x0 + passo * (i + 0.5)
        partes = []
        series = [(q["valor"], cor, -0.17)] if espelho else [(q["valor"], cor, 0)]
        if espelho:
            series.append((-q["valor"], "#b02f21", 0.17))
        for valor, color, dx in series:
            bw = passo * (0.26 if espelho else 0.6)
            partes += [
                r(
                    cx + passo * dx - bw / 2,
                    min(fy(0), fy(valor)),
                    bw,
                    abs(fy(valor) - fy(0)),
                    color,
                ),
                t(
                    cx + passo * dx,
                    fy(valor) + (-6 if valor >= 0 else 16),
                    pp(valor, 1).replace(" pp", ""),
                    11.5,
                    color,
                    "middle",
                    mono=True,
                ),
            ]
        partes += [
            t(cx, y1 + 22, f"{q['q']}º", 12.5, INK, "middle", "700"),
            t(
                cx,
                y1 + 38,
                f"{_n0(q['de'])} a {_n0(q['ate'])}",
                10.5,
                MUTED,
                "middle",
                mono=True,
            ),
            area(cx - passo / 2, y0, passo, y1 - y0 + 40),
        ]
        k = tips.add(
            ficha(
                f"{q['q']}º quinto",
                f"{rot_q}: de {num(q['de'], 1)} a {num(q['ate'], 1)}",
                [
                    ("Municípios", inteiro(q["n"])),
                    ("Eleitores", inteiro(q["aptos"])),
                    (
                        "Média ponderada" if not espelho else "Flávio, média ponderada",
                        pp(q["valor"]),
                    ),
                    *([("Lula, média ponderada", pp(-q["valor"]))] if espelho else []),
                ],
            )
        )
        out.append(hit("".join(partes), k))
    out.append(t(x0, y1 + 58, rot_q, 11.5, MUTED))
    return "".join(out)


def fig_quintis(C1: dict) -> tuple[str, list[dict], list[dict]]:
    ms = [
        m
        for m in linhas_de(C1["municipios"])
        if m.get("completo") and m.get("delta_abstencao_pp") is not None
    ]
    q_lula = quintis(ms, "t1_pct_lula", "delta_abstencao_pp")
    q_abs = quintis(ms, "delta_abstencao_pp", "swing_h2h_flavio_pp")
    tips = Tips()
    svg = (
        svg_abre(
            1000,
            380,
            "Abstenção e mudanças de Lula e Flávio entre turnos",
            "Esquerda: mudança média da abstenção em cinco grupos de municípios pela votação de Lula no 1º turno. "
            "Direita: mudanças dos dois candidatos em cinco grupos pela mudança da abstenção.",
        )
        + _painel_quintis(
            q_lula,
            60,
            "Mudança da abstenção, pontos",
            "quintos pela votação de Lula no 1º turno, %",
            COR_2T,
            tips,
        )
        + _painel_quintis(
            q_abs,
            540,
            "Mudança: Flávio (azul) e Lula (vermelho), pp",
            "quintos pela mudança da abstenção, pontos",
            FLAVIO,
            tips,
            espelho=True,
        )
        + "</svg>"
    )
    legenda_txt = (
        "Cinco grupos de mesmo número de municípios; médias ponderadas pelo eleitorado. Se a queda da abstenção fosse "
        "mobilização concentrada nos redutos de Lula, a barra da esquerda cresceria para a direita; se ela explicasse a queda "
        "de Flávio, a barra azul da direita cresceria para a esquerda. As barras vermelhas espelham Lula: mesmo denominador "
        "entre os dois finalistas, sinal oposto. Fonte: comparacao_1t.json (municípios)."
    )
    return (
        figura_html("ab_quintis", svg, legenda_txt, tips, modo="scroll", minw=760),
        q_lula,
        q_abs,
    )
