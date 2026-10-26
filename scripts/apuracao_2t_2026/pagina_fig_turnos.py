"""Figuras do capítulo "1º turno × 2º turno" (2º turno de 2026).

Fontes: ``comparacao_1t.json`` (UFs, municípios, listas de ganho e perda de votos)
e ``comparacao_2022.json`` (mesmos municípios no 2º turno de 2022). A ponte TSE para
IBGE dos mapas municipais vem de ``presidente.json``.
"""

from __future__ import annotations

import math

from apuracao_2026.pagina_comum import inteiro, num
from apuracao_2026.pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    GRADE,
    INK,
    LULA,
    MUTED,
    REGIOES,
    Tips,
    area,
    botoes,
    chip,
    escala,
    ficha,
    figura_html,
    hit,
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

from .pagina_fig_turnos_util import (
    barras_uf,
    faixa,
    ibge_por_tse,
    linhas_de,
    mapa_mun,
    nome_uf,
)

UFS_MAPA = ["SP", "MG", "BA", "PE", "PA", "AM"]
SW_CORES = ["#8f2618", "#c85a46", "#e5a596", "#f3ddd5", "#bfd0ea", "#2f63ad"]
SW_CORTES = [-6, -4, -2, 0, 2]
SW_ROT = [
    "Flávio −6 pp ou mais",
    "−6 a −4 pp",
    "−4 a −2 pp",
    "−2 a 0 pp",
    "0 a +2 pp",
    "Flávio +2 pp ou mais",
]
AZUL_CLARO = "#7fa3d6"


def fig_barras_uf(C1: dict, C22: dict | None) -> str:
    r22 = {u["uf"]: u for u in (C22 or {}).get("ufs", []) if u["uf"] != "ZZ"}
    itens = []
    for u in C1["ufs"]:
        uf = u["uf"]
        v22 = r22.get(uf, {}).get("flavio_menos_bolsonaro_pp")
        itens.append(
            {
                "uf": uf,
                "rot": nome_uf(uf),
                "s1": u["swing_h2h_flavio_pp"],
                "s22": v22,
                "sub": f"{inteiro(u['n_municipios'])} municípios",
                "ficha": [
                    ("Flávio, 1º turno (entre os dois)", pct(u["t1_h2h_flavio"])),
                    ("Flávio, 2º turno", pct(u["t2_h2h_flavio"])),
                    ("Mudança contra o 1º turno", pp(u["swing_h2h_flavio_pp"])),
                    ("Flávio menos Bolsonaro 2022", pp(v22)),
                    (
                        "Votos de Flávio, 1º para 2º turno",
                        f"{inteiro(u['t1_flavio'])} → {inteiro(u['t2_flavio'])}",
                    ),
                    (
                        "Votos de Lula, 1º para 2º turno",
                        f"{inteiro(u['t1_lula'])} → {inteiro(u['t2_lula'])}",
                    ),
                ],
            }
        )
    itens.sort(key=lambda it: it["s1"])
    tips = Tips()
    series = [("s1", "Contra o 1º turno de 2026", FLAVIO)]
    if r22:
        series.append(("s22", "Contra Bolsonaro no 2º turno de 2022", AZUL_CLARO))
    svg = barras_uf(
        itens,
        series,
        tips,
        "Mudança da parte de Flávio por UF",
        "Barras divergentes de um zero central: à esquerda, Flávio perdeu parte; à direita, ganhou.",
    )
    neg = sum(it["s1"] < 0 for it in itens)
    pos22 = sum((it["s22"] or 0) > 0 for it in itens)
    legenda = (
        f"Contra o 1º turno, a parte de Flávio entre os dois caiu em {neg} de {len(itens)} UFs. Contra Bolsonaro em 2022, "
        f"Flávio ficou acima em {pos22} UFs. Pontos dos válidos. Fontes: comparacao_1t.json e comparacao_2022.json (ufs)."
    )
    return figura_html("tu_barras_uf", svg, legenda, tips, modo="scroll", minw=760)


def fig_dispersao(C1: dict) -> str:
    """Cada município: parte de Flávio no 1º turno (entre os dois) contra o 2º turno."""
    ms = [
        m
        for m in linhas_de(C1["municipios"])
        if m.get("completo") and m.get("t1_h2h_flavio") is not None
    ]
    w = h = 700
    x0, x1, y0, y1 = 70, 680, 30, 640
    fx = escala(0, 100, x0, x1)
    fy = escala(0, 100, y1, y0)
    out = [
        svg_abre(
            w,
            h,
            "Parte de Flávio por município, 1º turno contra 2º turno",
            "Cada ponto é um município; a reta diagonal marca a mesma parte nos dois turnos. "
            "Ponto abaixo da reta: Flávio perdeu parte entre os turnos.",
        )
    ]
    for v in ticks(0, 100, 5):
        out.append(ln(fx(v), y0, fx(v), y1, GRADE, 1))
        out.append(ln(x0, fy(v), x1, fy(v), GRADE, 1))
        out.append(t(fx(v), y1 + 20, num(v, 0), 12, MUTED, "middle", mono=True))
        out.append(t(x0 - 8, fy(v) + 4, num(v, 0), 12, MUTED, "end", mono=True))
    out.append(ln(fx(0), fy(0), fx(100), fy(100), INK, 1.4, ' stroke-dasharray="6 4"'))
    out.append(t(fx(96), fy(99), "mesma parte", 12, INK, "end"))
    out.append(
        t(
            (x0 + x1) / 2,
            h - 6,
            "Flávio no 1º turno, % entre Flávio e Lula",
            13,
            INK,
            "middle",
        )
    )
    out.append(
        t(
            18,
            (y0 + y1) / 2,
            "Flávio no 2º turno, %",
            13,
            INK,
            "middle",
            extra=f' transform="rotate(-90 18 {(y0 + y1) / 2:.0f})"',
        )
    )
    por_reg: dict[str, list[str]] = {}
    for m in ms:
        por_reg.setdefault(m["regiao"], []).append(
            f"M{fx(m['t1_h2h_flavio']):.1f} {fy(m['t2_h2h_flavio']):.1f}h0"
        )
    for reg in REGIOES:
        if reg in por_reg:
            out.append(
                f'<path d="{"".join(por_reg[reg])}" stroke="{COR_REGIAO[reg]}" stroke-width="4.2" '
                'stroke-linecap="round" stroke-opacity="0.55" fill="none"/>'
            )
    tips = Tips()
    caps = sorted((m for m in ms if m.get("capital")), key=lambda m: -m["aptos"])
    for m in caps:
        cx, cy = fx(m["t1_h2h_flavio"]), fy(m["t2_h2h_flavio"])
        rr = 3 + 9 * math.sqrt(m["aptos"] / caps[0]["aptos"])
        k = tips.add(
            ficha(
                f"{nome_bonito(m['nome'])} ({m['uf']})",
                "capital",
                [
                    ("Flávio, 1º turno (entre os dois)", pct(m["t1_h2h_flavio"])),
                    ("Flávio, 2º turno", pct(m["t2_h2h_flavio"])),
                    ("Mudança", pp(m["swing_h2h_flavio_pp"])),
                    ("Eleitores", inteiro(m["aptos"])),
                ],
            )
        )
        out.append(
            hit(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr:.1f}" fill="none" stroke="{INK}" stroke-width="1.4"/>'
                + area(cx - rr - 2, cy - rr - 2, 2 * rr + 4, 2 * rr + 4),
                k,
            )
        )
    for m in caps[:3]:
        out.append(
            chip(
                fx(m["t1_h2h_flavio"]) + 14,
                fy(m["t2_h2h_flavio"]) + 22,
                nome_bonito(m["nome"]),
                12,
            )
        )
    out.append("</svg>")
    acima = sum(m["t2_h2h_flavio"] > m["t1_h2h_flavio"] for m in ms)
    leg = legenda_html(
        [(rg, COR_REGIAO[rg]) for rg in REGIOES] + [("capital (círculo)", "#ffffff")],
        "Região",
    )
    legenda = (
        f"{inteiro(len(ms))} municípios completos; só {inteiro(acima)} ficam acima da reta. A nuvem desce inteira por "
        "um degrau quase constante: a geografia do voto se manteve e o nível de Flávio caiu. Fonte: comparacao_1t.json (municipios)."
    )
    return figura_html(
        "tu_dispersao", "".join(out), legenda, tips, modo="fit", apos=leg
    )


def fig_hist_2022(C22: dict) -> str:
    """Histograma da mudança de Lula contra 2022: por número de municípios e por eleitorado."""
    ms = linhas_de(C22["municipios"])
    ms = [
        m
        for m in ms
        if m["uf"] != "ZZ"
        and m.get("swing_lula_pp") is not None
        and m.get("r22_validos")
    ]
    lo, hi = -16, 9
    caixas = list(range(lo, hi))
    cont = {b: [0, 0] for b in caixas}
    for m in ms:
        b = min(max(math.floor(m["swing_lula_pp"]), lo), hi - 1)
        cont[b][0] += 1
        cont[b][1] += m["aptos"]
    disp = C22.get("dispersao_swing_lula_pp", {})
    w, h = 1000, 460
    x0, x1, y0, y1 = 80, 980, 50, 390
    fx = escala(lo, hi, x0, x1)
    tips = Tips()
    out = [
        svg_abre(
            w,
            h,
            "Mudança de Lula contra o 2º turno de 2022, por município",
            "Barras: municípios (ou eleitores) em cada faixa de um ponto da mudança da parte de Lula.",
        )
    ]
    for j, (ident, rot) in enumerate((("n", "municípios"), ("te", "eleitores"))):
        vmax = max(c[j] for c in cont.values()) or 1
        fy = escala(0, vmax * 1.08, y1, y0)
        g = [f'<g data-alt-show="{ident}"{"" if j == 0 else " display=none"}>']
        for v in ticks(0, vmax * 1.08, 4):
            g.append(ln(x0, fy(v), x1, fy(v), GRADE, 1))
            g.append(
                t(
                    x0 - 8,
                    fy(v) + 4,
                    inteiro(v) if j == 0 else f"{num(v / 1e6, 0)} mi",
                    12,
                    MUTED,
                    "end",
                    mono=True,
                )
            )
        for b in caixas:
            v = cont[b][j]
            xa, xb = fx(b), fx(b + 1)
            cor = LULA if b >= 0 else FLAVIO
            k = tips.add(
                ficha(
                    f"De {num(b, 0)} a {num(b + 1, 0)} pp",
                    "mudança da parte de Lula contra 2022",
                    [
                        ("Municípios", inteiro(cont[b][0])),
                        ("Eleitores", inteiro(cont[b][1])),
                    ],
                )
            )
            g.append(
                hit(
                    r(xa + 1, fy(v), xb - xa - 2, y1 - fy(v), cor)
                    + area(xa, y0, xb - xa, y1 - y0),
                    k,
                )
            )
        g.append(t(x0, 30, f"{rot} em cada faixa de um ponto", 13, INK, weight="700"))
        g.append("</g>")
        out.append("".join(g))
    out.append(ln(x0, y1, x1, y1, INK, 1.2))
    for v in range(lo, hi + 1, 2):
        out.append(
            t(
                fx(v),
                y1 + 20,
                f"{v:+d}".replace("-", "−") if v else "0",
                12,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(
        t(
            (x0 + x1) / 2,
            h - 18,
            "mudança da parte de Lula nos válidos, 2026 menos 2022, pontos",
            13,
            INK,
            "middle",
        )
    )
    for chave, rot, dy in (
        ("mediana", "mediana dos municípios", 0),
        ("media_ponderada", "média ponderada pelo eleitorado", 30),
    ):
        v = disp.get(chave)
        if v is None:
            continue
        x = fx(v)
        out.append(ln(x, y0, x, y1, INK, 1.6, ' stroke-dasharray="4 3"'))
        out.append(chip(x + 4, y0 + 18 + dy, f"{rot}: {pp(v)}", 12))
    out.append("</svg>")
    abas = botoes([("n", "Municípios"), ("te", "Eleitores")], "n", "Contar por", "tab")
    legenda = (
        f"Lula caiu contra 2022 em {inteiro(C22.get('n_lula_caiu'))} municípios e subiu em {inteiro(C22.get('n_lula_subiu'))}; "
        f"a mediana é {pp(disp.get('mediana'))} e a média ponderada pelo eleitorado é {pp(disp.get('media_ponderada'))}. "
        "Em municípios a maior parte das barras é azul; em eleitores, o peso passa para o vermelho. Fonte: comparacao_2022.json."
    )
    return figura_html(
        "tu_hist_2022",
        "".join(out),
        legenda,
        tips,
        controles=abas,
        modo="scroll",
        minw=760,
    )


def fig_mapas_swing(d, C1: dict) -> str:
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
            v = m["swing_h2h_flavio_pp"]
            cor[ib] = SW_CORES[faixa(v, SW_CORTES)]
            tip[ib] = (
                f"{nome_bonito(m['nome'])}: Flávio {num(m['t1_h2h_flavio'], 1)} → {num(m['t2_h2h_flavio'], 1)} ({pp(v, 1)})"
            )
        svg = mapa_mun(
            uf,
            cor,
            tip,
            f"{nome_uf(uf)}: mudança da parte de Flávio",
            f"Municípios de {nome_uf(uf)} pela mudança da parte de Flávio entre os dois turnos.",
            560,
            520,
        )
        if svg is None:
            continue
        oculto = "" if k == 0 else " hidden"
        blocos.append(f'<div data-alt-show="{uf}"{oculto}>{svg}</div>')
        abas.append((uf, nome_uf(uf)))
    if not blocos:
        return ""
    controles = botoes(abas, abas[0][0], "Estado", "tab")
    leg = legenda_html(
        list(zip(SW_ROT, SW_CORES, strict=True)),
        "Mudança da parte de Flávio entre os dois, pontos",
    )
    legenda = (
        "Cada município pela mudança da parte de Flávio entre Flávio e Lula, do 1º para o 2º turno. Vermelho: andou para "
        "Lula; azul: para Flávio. Abas trocam o estado. Fontes: comparacao_1t.json, presidente.json (código IBGE) e malha do IBGE."
    )
    return figura_html(
        "tu_mapas_swing",
        "".join(blocos),
        legenda,
        Tips(),
        controles=controles,
        modo="fit",
        apos=leg,
    )
