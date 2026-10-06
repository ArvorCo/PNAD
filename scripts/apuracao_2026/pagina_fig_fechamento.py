"""Figuras do fechamento das seções (capítulo 12): quando a votação termina.

Lê `fechamento.json` (gerado por `scripts/apuracao-2026-fechamento.py`):

- `fechamento_regioes`: curvas acumuladas do encerramento (2026) e do recebimento
  no TSE (2022 e 2026) para o Brasil e cada região, mais a parcela de seções que
  encerraram às 18h ou depois por tamanho e por tipo de local;
- `fechamento_persistencia`: dispersão município a município da hora mediana de
  recebimento em 2022 e 2026, com os persistentes em destaque, e o mapa dos
  municípios com p90 de recebimento às 19h ou depois;
- as figuras de voto (`fechamento_voto_lula` e `fechamento_voto_zona`) ficam em
  `pagina_fig_fechamento_b`, que reaproveita os auxiliares daqui.

Nenhum número vem digitado; cobertura parcial aparece na legenda.
"""

from __future__ import annotations

import math

import voto_util_mapa as VM

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LIMA,
    MUTED,
    Tips,
    area,
    chip,
    dado,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    pct,
    r,
    registra,
    svg_abre,
    t,
)
from .pagina_fig_secoes import regiao_da_uf

TEAL = "#0f7f5f"
OURO = "#7d5b00"
OURO_CLARO = "#c9a227"
FUNDO = "#efe9da"
VAZIO = "nenhuma seção nesta condição"
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
SERIES = [
    ("encerramento_2026", "Encerramento da urna, 2026", TEAL, ""),
    ("recebimento_2026", "Chegada ao TSE, 2026", INK, ""),
    ("recebimento_2022", "Chegada ao TSE, 2022", OURO, ' stroke-dasharray="7 4"'),
]


def fech(d) -> dict:
    return dado(d, "fechamento")


def hora(m: float | None) -> str:
    """Minutos depois das 17h de Brasília viram 'HH:MM'."""
    if m is None or (isinstance(m, float) and math.isnan(m)):
        return "s/d"
    total = 17 * 60 + round(m)
    dia, resto = divmod(total, 1440)
    h, mi = divmod(resto, 60)
    return f"{h:02d}:{mi:02d}" + (" (+1 dia)" if dia else "")


def duracao(m: float | None) -> str:
    if m is None:
        return "s/d"
    v = round(m)
    if abs(v) < 60:
        return f"{v} min"
    h, rr = divmod(v, 60)
    return f"{h}h{rr:02d}"


def nota_cobertura(F: dict) -> str:
    c = F["cobertura"]
    if c.get("parcial"):
        return (
            f"Cobertura parcial: {len(c['ufs_completas'])} UFs completas em 2026 "
            f"({inteiro(c['secoes_2026_completas'])} seções); comparações entre anos só nelas."
        )
    return f"Cobertura completa: {inteiro(c['secoes_2026'])} seções de 2026."


def linhas_resumo(rr: dict | None) -> list[tuple[str, str]]:
    if not rr:
        return [("Seções", "sem dado")]
    return [
        ("Seções", inteiro(rr["secoes"])),
        ("Mediana", hora(rr["mediana"])),
        ("p90 · p99", f"{hora(rr['p90'])} · {hora(rr['p99'])}"),
        ("Depois de 17:30", pct(rr["depois_1730_pct"], 1)),
        ("Depois de 18:00", pct(rr["depois_1800_pct"], 1)),
        ("Depois de 19:00", pct(rr["depois_1900_pct"], 1)),
    ]


# ------------------------------------------------------------------ 1 regiões

PW, PH = 340, 236
XMAX = 360


def _painel_curvas(g: dict, grade: list[int], px: float, py: float, tips: Tips) -> str:
    x0, x1 = px + 46, px + PW - 8
    y0, y1 = py + 44, py + PH - 34
    X = escala(0, XMAX, x0, x1)
    Y = escala(0, 100, y1, y0)
    n = (g.get("encerramento_2026") or {}).get("secoes")
    out = [
        t(px, py + 18, g["chave"], 15, INK, weight="700"),
        t(
            px + PW - 8,
            py + 18,
            f"{inteiro(n)} seções" if n else "",
            13,
            MUTED,
            "end",
            mono=True,
        ),
        r(x0, y0, x1 - x0, y1 - y0, FUNDO),
    ]
    for v in (0, 50, 100):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(t(x0 - 6, Y(v) + 4, f"{v}%", 13, MUTED, "end", mono=True))
    for m in (30, 60, 120):
        out.append(ln(X(m), y0, X(m), y1, "#cbc5b5", 0.8, ' stroke-dasharray="2 3"'))
    for m in range(0, XMAX + 1, 60):
        # o "17h" do canto alinha à esquerda para não encostar no "0%"
        anc = "start" if m == 0 else "middle"
        out.append(t(X(m), y1 + 18, f"{17 + m // 60}h", 13, MUTED, anc, mono=True))
    for chave, _nome, cor, tra in SERIES:
        rr = g.get(chave) or {}
        cur = rr.get("acumulada")
        if not cur:
            continue
        pts = [(X(m), Y(v)) for m, v in zip(grade, cur, strict=False) if m <= XMAX]
        out.append(
            f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" '
            f'stroke="{cor}" stroke-width="2.4" stroke-linejoin="round"{tra} pointer-events="none"/>'
        )
    linhas: list[tuple[str, str]] = []
    for chave, nome, _cor, _tra in SERIES:
        rr = g.get(chave)
        if rr:
            linhas.append(
                (
                    nome,
                    f"mediana {hora(rr['mediana'])}; 18h+ {pct(rr['depois_1800_pct'], 1)}",
                )
            )
    dec = g.get("decomposicao_2026") or {}
    k = tips.add(
        ficha(
            g["chave"],
            "parcela acumulada das seções até cada hora, Brasília",
            [
                *linhas,
                ("Fila (17h ao fim), mediana", duracao(dec.get("fila_mediana_min"))),
                (
                    "Fim da votação até o TSE, mediana",
                    duracao(dec.get("transmissao_mediana_min")),
                ),
            ],
            "19h ou depois: "
            + "; ".join(
                f"{nome.split(',')[0].lower()} {('2026' if '2026' in c else '2022')} "
                f"{pct((g.get(c) or {}).get('depois_1900_pct'), 1)}"
                for c, nome, _cor, _tra in SERIES
            ),
        )
    )
    out.append(hit(area(x0, y0, x1 - x0, y1 - y0), k, foco=True))
    return "".join(out)


def _painel_barras(
    titulo: str,
    sub: str,
    linhas_: list[dict],
    chave_rot: str,
    px: float,
    py: float,
    largura: float,
    tips: Tips,
) -> str:
    out = [
        t(px, py + 18, titulo, 15, INK, weight="700"),
        t(px, py + 38, sub, 13, MUTED),
    ]
    if not linhas_:
        return "".join(out) + t(px + largura / 2, py + 120, VAZIO, 14, MUTED, "middle")
    rot_w = 250
    bx0, bx1 = px + rot_w, px + largura - 70
    vmax = max(
        ((x.get("encerramento_2026") or {}).get("depois_1800_pct") or 0)
        for x in linhas_
    )
    vmax = max(vmax, 1.0)
    X = escala(0, vmax, bx0, bx1)
    y = py + 56
    for x in linhas_:
        e = x.get("encerramento_2026") or {}
        v = e.get("depois_1800_pct")
        k = tips.add(
            ficha(
                str(x[chave_rot]),
                "encerramento da urna, 2026, hora de Brasília",
                [
                    (
                        "Seções 2026 · 2022",
                        f"{inteiro(x.get('secoes_2026'))} · {inteiro(x.get('secoes_2022'))}",
                    ),
                    ("Encerradas às 18h ou depois", pct(v, 1)),
                    ("Às 19h ou depois", pct(e.get("depois_1900_pct"), 1)),
                    ("Encerramento mediano", hora(e.get("mediana"))),
                    ("Parte das seções tardias", pct(x.get("pct_das_tardias_2026"), 1)),
                    (
                        "Chegada ao TSE, mediana 2026 · 2022",
                        f"{hora((x.get('recebimento_2026') or {}).get('mediana'))} · "
                        f"{hora((x.get('recebimento_2022') or {}).get('mediana'))}",
                    ),
                ],
            )
        )
        out.append(t(bx0 - 10, y + 16, str(x[chave_rot]), 14, INK, "end"))
        barra = r(bx0, y + 4, (X(v) - bx0) if v else 0, 18, TEAL)
        out.append(hit(barra + area(px, y, largura, 26), k))
        out.append(
            t(
                (X(v) if v else bx0) + 6,
                y + 18,
                pct(v, 1),
                13,
                INK,
                mono=True,
                extra=' pointer-events="none"',
            )
        )
        y += 30
    return "".join(out)


@registra("fechamento_regioes")
def fechamento_regioes(d, **_op) -> str:
    F = fech(d)
    D = F["distribuicao"]
    grade = D["grade_min"]
    grupos = [D["brasil"], *D["regioes"]]
    tips = Tips()
    ncol = 3
    nlin = math.ceil(len(grupos) / ncol)
    topo_barras = 10 + nlin * (PH + 14) + 10
    tam = F["tamanho"]["linhas"]
    tip = F["tipo_local"]["linhas"]
    h = topo_barras + 60 + 30 * max(len(tam), len(tip)) + 16
    out = [
        svg_abre(
            1100,
            h,
            "Quando a votação termina: encerramento da urna e chegada ao TSE, 2022 e 2026",
            "Seis painéis com a parcela acumulada das seções por hora de Brasília: encerramento da urna em 2026 e "
            "chegada do boletim ao TSE em 2026 e 2022, para o Brasil e cada região; abaixo, a parcela de seções que "
            "encerraram às 18h ou depois por tamanho do eleitorado e por tipo de local.",
        )
    ]
    for i, g in enumerate(grupos):
        px = 20 + (i % ncol) * 360
        py = 10 + (i // ncol) * (PH + 14)
        out.append(_painel_curvas(g, grade, px, py, tips))
    out.append(
        _painel_barras(
            "Encerradas às 18h ou depois, por eleitorado apto",
            "parcela das seções de cada faixa, 2026",
            tam,
            "faixa",
            20,
            topo_barras,
            520,
            tips,
        )
    )
    out.append(
        _painel_barras(
            "Por tipo de local (inferido pelo nome)",
            "parcela das seções de cada tipo, 2026",
            tip,
            "tipo",
            570,
            topo_barras,
            520,
            tips,
        )
    )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("encerramento da urna, 2026", TEAL),
            ("chegada do boletim ao TSE, 2026", INK),
            (
                "chegada do boletim ao TSE, 2022",
                f"repeating-linear-gradient(90deg,{OURO} 0 6px,transparent 6px 9px)",
            ),
        ],
        "Curvas: parcela acumulada das seções até cada hora de Brasília",
    )
    br = D["brasil"]
    e = br.get("encerramento_2026") or {}
    legenda = (
        f"Metade das urnas encerrou até as {hora(e.get('mediana'))} de Brasília e "
        f"{pct(e.get('depois_1800_pct'), 1)} às 18h ou depois. A chegada ao TSE soma a fila e o "
        "transporte da mídia; é a única régua que existe nos dois anos. Linhas pontilhadas verticais: "
        "17:30, 18:00 e 19:00. Tipo de local é inferência por palavra-chave. "
        f"{nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_regioes", "".join(out), legenda, tips, minw=900, apos=leg
    )


# ------------------------------------------------------------------ 2 persistência

SX0, SX1, SY0, SY1 = 80, 500, 40, 470
SMAX = 360
MAPA_X, MAPA_W = 560, 520


MAPA_TAMBEM_2022 = "#2f2f2f"
"""Cinza-carvão: no mapa, p90 tardio também em 2022. Não é verde para não se
confundir com o Norte da dispersão ao lado."""


def _cor_mapa(p22: float | None) -> str:
    return MAPA_TAMBEM_2022 if (p22 or 0) >= 120 else "#d9775f"


@registra("fechamento_persistencia")
def fechamento_persistencia(d, **_op) -> str:
    F = fech(d)
    P = F["persistencia"]
    cols = P["pontos"]["colunas"]
    pts = [dict(zip(cols, x, strict=False)) for x in P["pontos"]["linhas"]]
    dec = P.get("decil") or {}
    cor = P.get("correlacao") or {}
    w, h = 1100, 560
    X = escala(0, SMAX, SX0, SX1)
    Y = escala(0, SMAX, SY1, SY0)
    out = [
        svg_abre(
            w,
            h,
            "Onde a eleição termina tarde nos dois anos",
            "À esquerda, cada ponto é um município: hora mediana de chegada dos boletins ao TSE em 2022 e em 2026; "
            "em dourado, os municípios no décimo mais tardio nos dois anos. À direita, o mapa dos municípios cujo p90 "
            "de chegada foi às 19h ou depois em 2026.",
            ' data-near="1"',
        ),
        r(SX0, SY0, SX1 - SX0, SY1 - SY0, FUNDO),
    ]
    for m in range(0, SMAX + 1, 60):
        out.append(ln(X(m), SY0, X(m), SY1, GRADE, 0.8))
        out.append(ln(SX0, Y(m), SX1, Y(m), GRADE, 0.8))
        out.append(
            t(X(m), SY1 + 20, f"{17 + m // 60}h", 13, MUTED, "middle", mono=True)
        )
        out.append(
            t(SX0 - 8, Y(m) + 4, f"{17 + m // 60}h", 13, MUTED, "end", mono=True)
        )
    out.append(ln(X(0), Y(0), X(SMAX), Y(SMAX), INK, 1.2, ' stroke-dasharray="6 4"'))
    c22, c26 = dec.get("corte_2022_min"), dec.get("corte_2026_min")
    if c22 is not None and c26 is not None:
        out.append(ln(X(c22), SY0, X(c22), SY1, OURO, 1.2, ' stroke-dasharray="3 3"'))
        out.append(ln(SX0, Y(c26), SX1, Y(c26), OURO, 1.2, ' stroke-dasharray="3 3"'))
    out.append(
        t(
            (SX0 + SX1) / 2,
            h - 46,
            "Chegada ao TSE em 2022, mediana do município",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = (SY0 + SY1) / 2
    out.append(
        t(
            24,
            yy,
            "Chegada em 2026, mediana",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 24 {yy:.0f})"',
        )
    )
    emax = max((p["eleitorado"] or 0) for p in pts) if pts else 1
    linhas, xy = [], []
    segs: dict[tuple[str, float], list[str]] = {}
    pers = []
    for p in sorted(pts, key=lambda q: -(q["eleitorado"] or 0)):
        if p["med22"] is None or p["med26"] is None:
            continue
        x = X(min(p["med22"], SMAX))
        y = Y(min(p["med26"], SMAX))
        raio = round((1.4 + 9 * math.sqrt((p["eleitorado"] or 0) / emax)) * 2) / 2
        reg = regiao_da_uf(p["uf"])
        if p["persistente"]:
            pers.append((x, y, raio, p))
        else:
            segs.setdefault((reg, raio), []).append(f"M{x:.0f} {y:.0f}h0")
        linhas.append(_linha_tip(p))
        xy.append([round(x), round(y), raio])
    for (reg, raio), s in sorted(segs.items(), key=lambda kv: -kv[0][1]):
        out.append(
            f'<path d="{"".join(s)}" stroke="{COR_REGIAO.get(reg, MUTED)}" stroke-width="{2 * raio}" '
            'stroke-linecap="round" stroke-opacity="0.45" fill="none"/>'
        )
    for x, y, raio, _p in pers:
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{max(raio, 3.5):.1f}" fill="{OURO_CLARO}" '
            f'stroke="{INK}" stroke-width="1"/>'
        )
    out.append(
        chip(
            SX0 + 8,
            SY0 + 22,
            "décimo mais tardio nos dois anos: canto de cima à direita",
            13,
        )
    )
    out.append(
        chip(SX0 + 8, SY1 - 10, "abaixo da diagonal: chegou mais cedo em 2026", 13)
    )
    # mapa
    proj, _ = VM._proj(MAPA_W, MAPA_W, 10.0)
    geo = VM.paths(MAPA_W, MAPA_W)
    out.append(f'<g transform="translate({MAPA_X},20)">')
    for _uf, g in sorted(geo.items()):
        out.append(
            f'<path d="{g["d"]}" fill="#e7e1d2" stroke="#b9b29f" stroke-width="0.8"/>'
        )
    out.append("</g>")
    tarde = [p for p in pts if (p["p9026"] or 0) >= 120 and p["lat"] is not None]
    for p in sorted(tarde, key=lambda q: q["persistente"]):
        x, y = proj(p["lon"], p["lat"])
        x += MAPA_X
        y += 20
        if p["persistente"]:
            out.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{OURO_CLARO}" stroke="{INK}" stroke-width="1"/>'
            )
            linhas.append(_linha_tip(p))
            xy.append([round(x), round(y), 5])
        else:
            out.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{_cor_mapa(p["p9022"])}" '
                'fill-opacity="0.8" pointer-events="none"/>'
            )
    out.append(
        t(MAPA_X, 16, "p90 de chegada às 19h ou depois em 2026", 14, INK, weight="700")
    )
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Município",
            "Chegada mediana 2022 · 2026",
            "p90 2022 · 2026",
            "Posição no ano (percentil) 2022 · 2026",
            "Eleitorado 2026",
            "Locais rurais (inferido)",
        ],
        linhas,
        xy=xy,
        nota="hora de Brasília; décimo mais tardio = percentil 90 ou mais",
    )
    p19 = P.get("p90_depois_19h") or {}
    # uma legenda por painel: as cores do mapa não se misturam às das regiões
    leg = legenda_html(
        [("décimo mais tardio nos dois anos", OURO_CLARO)]
        + [(rg, COR_REGIAO[rg]) for rg in REGIOES],
        "À esquerda, dispersão: cor pela região, área pelo eleitorado",
    ) + legenda_html(
        [
            ("p90 às 19h ou depois também em 2022", MAPA_TAMBEM_2022),
            ("só em 2026", "#d9775f"),
        ],
        "À direita, mapa: municípios com p90 de chegada às 19h ou depois em 2026",
    )
    legenda = (
        f"{inteiro(P.get('municipios'))} municípios comparados. Correlação de postos entre os anos "
        f"{num(cor.get('spearman'), 2)} (IC 95% de {num((cor.get('spearman_ic95') or [None])[0], 2)} a "
        f"{num((cor.get('spearman_ic95') or [None, None])[1], 2)}), {num(cor.get('spearman_dentro_uf'), 2)} dentro da UF. "
        f"{inteiro(dec.get('persistentes'))} municípios ficaram no décimo mais tardio nos dois anos, contra "
        f"{num(dec.get('esperado_independencia'), 0)} esperados por acaso. No mapa, {inteiro(p19.get('municipios_2026'))} "
        f"municípios com p90 às 19h ou depois em 2026; em 2022 foram {inteiro(p19.get('municipios_2022'))}, porque o "
        f"recebimento inteiro foi mais tarde. Linhas douradas: corte do décimo de cada ano. Pontos além das 23h ficam na "
        f"borda. {nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_persistencia", "".join(out), legenda, tips, minw=900, apos=leg
    )


def _linha_tip(p: dict) -> list[str]:
    return [
        f"{nome_bonito(p['municipio'] or p['mun_tse'])} ({p['uf']})",
        f"{hora(p['med22'])} · {hora(p['med26'])}",
        f"{hora(p['p9022'])} · {hora(p['p9026'])}",
        (
            "décimo mais tardio nos dois"
            if p["persistente"]
            else "fora do décimo nos dois"
        ),
        inteiro(p["eleitorado"]),
        f"{num(p['rural_pct'], 0)}%",
    ]


__all__ = [
    "FUNDO",
    "OURO",
    "REGIOES",
    "VAZIO",
    "duracao",
    "fech",
    "hora",
    "nota_cobertura",
]
