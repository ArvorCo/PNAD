"""Figuras do fechamento das seções (capítulo 12): quando a votação termina.

Lê `fechamento.json` (gerado por `scripts/apuracao-2026-fechamento.py`):

- `fechamento_regioes`: curvas acumuladas do encerramento (2026) e do recebimento
  no TSE (2022 e 2026) para o Brasil e cada região, mais a parcela de seções que
  encerraram às 18h ou depois por tamanho e por tipo de local;
- `fechamento_persistencia`: dispersão município a município da hora mediana de
  recebimento em 2022 e 2026, com os persistentes em destaque, e o mapa dos
  municípios com p90 de recebimento às 19h ou depois;
- `fechamento_voto_lula`: a % de Lula e de Flávio por faixa de encerramento em
  três réguas (bruta, dentro da zona, dentro da zona com tamanho e tipo), a
  inclinação por hora de atraso e o Spearman por UF;
- `fechamento_voto_zona`: seção tardia contra as demais da mesma zona em voto,
  comparecimento, fila e identificação, com intervalo de 95%.

Nenhum número vem digitado; cobertura parcial aparece na legenda.
"""

from __future__ import annotations

import math
from html import escape

import voto_util_mapa as VM

from .pagina_comum import inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    GRADE,
    INK,
    LIMA,
    LULA,
    MUTED,
    PAPER,
    Tips,
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
    nome_bonito,
    pct,
    pp,
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
        out.append(t(X(m), y1 + 18, f"{17 + m // 60}h", 13, MUTED, "middle", mono=True))
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


def _cor_mapa(p22: float | None) -> str:
    return "#0d3f35" if (p22 or 0) >= 120 else "#d9775f"


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
    leg = legenda_html(
        [
            ("décimo mais tardio nos dois anos", OURO_CLARO),
            ("mapa: p90 às 19h ou depois também em 2022", "#0d3f35"),
            ("mapa: só em 2026", "#d9775f"),
        ]
        + [(rg, COR_REGIAO[rg]) for rg in REGIOES],
        "Pontos da dispersão pela região; área pelo eleitorado",
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


# ------------------------------------------------------------------ 3 voto de Lula por hora

MODELOS = [
    ("bruta", "bruta", MUTED, "losango"),
    ("zona", "dentro da zona", INK, "ponto"),
    ("zona_controles", "zona, tamanho e tipo", OURO, "quadrado"),
]


def _marca(forma: str, x: float, y: float, cor: str) -> str:
    if forma == "losango":
        return (
            f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{PAPER}" stroke="{cor}" '
            f'stroke-width="2" transform="rotate(45 {x:.1f} {y:.1f})"/>'
        )
    if forma == "quadrado":
        return f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{cor}" stroke="{PAPER}"/>'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{cor}" stroke="{PAPER}"/>'


def _painel_bruta(L: dict, grupo: str, px: float, py: float, tips: Tips) -> str:
    linhas_ = [x for x in L["bruta"] if x["grupo"] == grupo]
    x0, x1 = px + 150, px + 420
    X = escala(0, 100, x0, x1)
    out = []
    for v in (0, 25, 50, 75, 100):
        out.append(ln(X(v), py, X(v), py + 34 * len(linhas_), GRADE, 0.8))
        out.append(
            t(
                X(v),
                py + 34 * len(linhas_) + 18,
                f"{v}%",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    for i, x in enumerate(linhas_):
        y = py + 17 + 34 * i
        out.append(t(px, y + 5, x["faixa"], 14, INK))
        if not x["secoes"]:
            out.append(t(x0, y + 5, VAZIO, 13, MUTED))
            continue
        k = tips.add(
            ficha(
                f"{grupo}: encerramento {x['faixa']}",
                "% dos válidos de presidente, soma das seções",
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Votantes", inteiro(x["votantes"])),
                    ("Lula", pct(x["lula_pct"], 1)),
                    ("Flávio", pct(x["flavio_pct"], 1)),
                ],
            )
        )
        xl, xf = X(x["lula_pct"] or 0), X(x["flavio_pct"] or 0)
        g = ln(min(xl, xf), y, max(xl, xf), y, "#b9b29f", 3)
        g += f'<circle cx="{xl:.1f}" cy="{y:.1f}" r="6" fill="{LULA}"/>'
        g += f'<circle cx="{xf:.1f}" cy="{y:.1f}" r="6" fill="{FLAVIO}"/>'
        out.append(hit(g + area(px, y - 16, 520, 32), k))
        out.append(
            t(
                px + 520,
                y + 5,
                f"{inteiro(x['secoes'])} seções",
                13,
                MUTED,
                "end",
                mono=True,
            )
        )
    return "".join(out)


def _coef(L: dict, bloco: str, mid: str, cand: str, nome: str) -> dict:
    m = next((z for z in L[bloco] if z["id"] == mid), {})
    return ((m.get(cand) or {}).get("coeficientes") or {}).get(nome) or {}


def _coluna_coef(
    L: dict,
    bloco: str,
    cand: str,
    nomes: list[str],
    px: float,
    py: float,
    larg: float,
    tips: Tips,
    passo: float = 52,
) -> str:
    """Coeficientes dentro da zona (com e sem controles) com IC; a bruta vai em texto."""
    controlados = MODELOS[1:]
    vals = [0.0]
    for n in nomes:
        for mid, _rot, _cor, _f in controlados:
            c = _coef(L, bloco, mid, cand, n)
            vals += [
                v
                for v in [c.get("estimativa"), *(c.get("ic95") or [])]
                if v is not None
            ]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or 1
    X = escala(lo - pad, hi + pad, px + 4, px + larg - 4)
    yb = py + passo * len(nomes)
    nome_c = "Lula" if cand == "lula" else "Flávio"
    out = [
        r(px, py - 4, larg, yb - py + 8, FUNDO),
        ln(X(0), py - 4, X(0), yb + 4, INK, 1.4),
        t(
            px + larg / 2,
            py - 14,
            nome_c,
            14,
            LULA if cand == "lula" else FLAVIO,
            "middle",
            "700",
        ),
        t(
            px + 2,
            yb + 20,
            pp(lo - pad, 1).replace(" pp", ""),
            13,
            MUTED,
            "start",
            mono=True,
        ),
        t(
            px + larg - 2,
            yb + 20,
            pp(hi + pad, 1).replace(" pp", ""),
            13,
            MUTED,
            "end",
            mono=True,
        ),
    ]
    for i, n in enumerate(nomes):
        yc = py + passo * i + 16
        for j, (mid, rot, cor, forma) in enumerate(controlados):
            c = _coef(L, bloco, mid, cand, n)
            e, ic = c.get("estimativa"), c.get("ic95") or [None, None]
            if e is None:
                continue
            y = yc + 12 * j
            g = ""
            if ic[0] is not None and ic[1] is not None:
                g += ln(X(ic[0]), y, X(ic[1]), y, cor, 2.4)
            g += _marca(forma, X(e), y, cor)
            k = tips.add(
                ficha(
                    f"{nome_c}: {n.replace('horas_atraso', 'por hora de atraso')}",
                    rot,
                    [
                        ("Estimativa", pp(e, 2)),
                        ("Intervalo de 95%", f"{pp(ic[0], 2)} a {pp(ic[1], 2)}"),
                        ("Erro-padrão (bootstrap)", num(c.get("ep"), 2)),
                        (
                            "Bruta, sem controle",
                            pp(_coef(L, bloco, "bruta", cand, n).get("estimativa"), 2),
                        ),
                    ],
                    "pontos percentuais dos válidos; bootstrap de zonas"
                    + ("" if bloco == "inclinacao" else f"; contra {L['referencia']}"),
                )
            )
            out.append(hit(g + area(px, y - 6, larg, 12), k))
        b = _coef(L, bloco, "bruta", cand, n).get("estimativa")
        esquerda = X(0) > px + larg / 2
        out.append(
            t(
                px + 6 if esquerda else px + larg - 6,
                yc + 34,
                f"bruta {pp(b, 1)}",
                13,
                MUTED,
                "start" if esquerda else "end",
                mono=True,
            )
        )
    return "".join(out)


def _painel_spearman(L: dict, px: float, py: float, larg: float, tips: Tips) -> str:
    lista = L.get("spearman_uf") or []
    out = [
        t(px, py, "4. Spearman seção a seção dentro da UF", 15, INK, weight="700"),
        t(
            px,
            py + 18,
            "hora de encerramento contra % de Lula, sem controle",
            13,
            MUTED,
        ),
    ]
    if not lista:
        return "".join(out) + t(px + larg / 2, py + 80, VAZIO, 14, MUTED, "middle")
    vals = [x["rho_lula"] for x in lista if x["rho_lula"] is not None] + [0.0]
    lo, hi = min(min(vals), -0.05), max(max(vals), 0.05)
    X = escala(lo, hi, px + 44, px + larg - 70)
    y = py + 34
    passo = 17
    out.append(ln(X(0), y - 4, X(0), y + passo * len(lista), INK, 1.2))
    for x in lista:
        v = x["rho_lula"]
        k = tips.add(
            ficha(
                x["uf"],
                x["regiao"],
                [
                    ("Seções", inteiro(x["secoes"])),
                    ("Encerradas às 18h ou depois", inteiro(x["secoes_depois_1800"])),
                    ("Spearman com Lula", num(v, 3)),
                    ("Spearman com Flávio", num(x["rho_flavio"], 3)),
                ],
                "correlação de postos, sem controle de zona",
            )
        )
        out.append(t(px + 30, y + 11, x["uf"], 13, INK, "end", mono=True))
        barra = ""
        if v is not None:
            a, b = sorted((X(0), X(v)))
            barra = r(a, y + 2, b - a, 11, LULA)
        out.append(hit(barra + area(px, y, larg, passo), k))
        out.append(t(px + larg, y + 11, num(v, 2), 13, INK, "end", mono=True))
        y += passo
    return "".join(out)


@registra("fechamento_voto_lula")
def fechamento_voto_lula(d, **_op) -> str:
    F = fech(d)
    L = F["lula_hora"]
    tips = Tips()
    grupos = ["Brasil"] + [
        rg for rg in REGIOES if any(x["grupo"] == rg for x in L["bruta"])
    ]
    n_faixas = len(L["faixas"])
    topo = 70
    alt_a = 34 * n_faixas + 40
    nomes_f = [x["rotulo"] for x in L["faixas"] if x["rotulo"] != L["referencia"]]
    nomes_f = [
        n
        for n in nomes_f
        if any(
            n in (m.get("lula") or {}).get("coeficientes", {}) for m in L["por_faixa"]
        )
    ]
    topo_b = topo + alt_a + 70
    n_uf = len(L.get("spearman_uf") or [])
    h = max(topo_b + 40 * 1 + 120, topo_b + 17 * n_uf + 60) + 20
    out = [
        svg_abre(
            1100,
            h,
            "Encerramento tardio e voto em Lula, em três réguas",
            "Bruta: % dos válidos de Lula e de Flávio por faixa de hora de encerramento. Dentro da zona: diferença "
            "contra as seções que encerraram de 17:00 a 17:30, com e sem controle de tamanho e tipo de local. "
            "Inclinação: pontos por hora de atraso. Spearman por UF.",
        ),
        t(
            20,
            24,
            "1. Bruta: % dos válidos por faixa de encerramento",
            15,
            INK,
            weight="700",
        ),
        t(
            20,
            44,
            "Lula (vermelho) e Flávio (azul), soma das seções da faixa",
            13,
            MUTED,
        ),
    ]
    for gi, g in enumerate(grupos):
        vis = "" if gi == 0 else ' display="none"'
        out.append(
            f'<g data-alt-show="{escape(g)}"{vis}>{_painel_bruta(L, g, 20, topo, tips)}</g>'
        )
    out.append(
        t(580, 24, "2. Dentro da zona, contra 17:00 a 17:30", 15, INK, weight="700")
    )
    out.append(t(580, 44, "pontos dos válidos; traço: intervalo de 95%", 13, MUTED))
    py = topo + 20
    for i, n in enumerate(nomes_f):
        out.append(t(580, py + 52 * i + 27, n, 14, INK))
    out.append(_coluna_coef(L, "por_faixa", "lula", nomes_f, 712, py, 178, tips))
    out.append(_coluna_coef(L, "por_faixa", "flavio", nomes_f, 908, py, 178, tips))
    out.append(
        t(
            20,
            topo_b - 24,
            "3. Inclinação: pontos por hora de atraso",
            15,
            INK,
            weight="700",
        )
    )
    sob = L.get("sobrevive_pct") or {}
    out.append(
        t(
            20,
            topo_b - 4,
            f"sobra {num(sob.get('lula_inclinacao'), 0)}% da bruta para Lula e "
            f"{num(sob.get('flavio_inclinacao'), 0)}% para Flávio",
            13,
            MUTED,
        )
    )
    out.append(t(20, topo_b + 66, "por hora", 14, INK))
    out.append(
        _coluna_coef(
            L, "inclinacao", "lula", ["horas_atraso"], 130, topo_b + 40, 190, tips, 60
        )
    )
    out.append(
        _coluna_coef(
            L, "inclinacao", "flavio", ["horas_atraso"], 340, topo_b + 40, 190, tips, 60
        )
    )
    out.append(_painel_spearman(L, 580, topo_b - 24, 500, tips))
    out.append("</svg>")
    ctl = botoes([(g, g) for g in grupos], "Brasil", "Painel 1, régua bruta")
    leg = legenda_html(
        [(f"{rot}", cor) for _m, rot, cor, _f in MODELOS[1:]],
        "Painéis 2 e 3: ponto = dentro da zona; quadrado = zona, tamanho e tipo; a régua bruta vai escrita",
    )
    legenda = (
        "A correlação bruta é esperada: seção grande, rural e indígena fecha tarde e vota em Lula. O número que "
        f"interessa é o que sobrevive ao controle por zona, tamanho e tipo de local: sobra "
        f"{num(sob.get('lula_inclinacao'), 0)}% da inclinação bruta. Correlação dentro da zona não identifica "
        f"mecanismo. Regressão ponderada pelos votantes, efeito fixo de zona, intervalo por bootstrap de "
        f"{inteiro(F['voto']['bootstrap'])} reamostras de zonas; {inteiro(L['secoes'])} seções em "
        f"{inteiro(L['zonas'])} zonas. {nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_voto_lula",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=900,
        apos=leg,
    )


# ------------------------------------------------------------------ 4 seção tardia contra a zona

ESTIMADORES = [
    "tarde18_zona",
    "tarde18_zona_tamanho",
    "tarde19_zona",
    "recebimento_decil_2026",
    "recebimento_decil_2022",
]
CURTO = {
    "tarde18_zona": "encerrou 18h+, mesma zona",
    "tarde18_zona_tamanho": "18h+, mesma zona e tamanho",
    "tarde19_zona": "encerrou 19h+, mesma zona",
    "recebimento_decil_2026": "chegou no último décimo, 2026",
    "recebimento_decil_2022": "chegou no último décimo, 2022",
}
PAINEIS = [
    [
        ("lula_pp", "Lula", LULA),
        ("flavio_pp", "Flávio", FLAVIO),
        ("comparecimento_pp", "Comparecimento", INK),
    ],
    [
        ("votantes_secao", "Votantes por seção", INK),
        ("votantes_hora", "Votantes por hora", INK),
        ("ano_nascimento_pp", "Hab. por ano de nascimento", OURO),
        ("sem_biometria_pp", "Sem biometria", MUTED),
    ],
]
UNIDADE = {
    "lula_pp": "pontos dos válidos",
    "flavio_pp": "pontos dos válidos",
    "comparecimento_pp": "pontos dos aptos",
    "votantes_secao": "votantes",
    "votantes_hora": "votantes por hora",
    "ano_nascimento_pp": "pontos dos votantes",
    "sem_biometria_pp": "pontos dos votantes",
}


def _painel_metrica(
    ests: dict,
    chave: str,
    nome: str,
    cor: str,
    px: float,
    py: float,
    larg: float,
    tips: Tips,
) -> str:
    vals = [0.0]
    for e in ests.values():
        m = (e or {}).get(chave) or {}
        vals += [
            v
            for v in [m.get("estimativa"), m.get("bruto"), *(m.get("ic95") or [])]
            if v is not None
        ]
    lim = max(abs(v) for v in vals) * 1.12 or 1
    X = escala(-lim, lim, px + 6, px + larg - 6)
    yb = py + 34 * len(ESTIMADORES)
    out = [
        r(px, py - 4, larg, yb - py + 8, FUNDO),
        ln(X(0), py - 4, X(0), yb + 4, INK, 1.4),
        t(
            px + larg / 2,
            py - 30,
            nome,
            14,
            cor if cor != MUTED else INK,
            "middle",
            "700",
        ),
        t(px + larg / 2, py - 13, UNIDADE[chave], 13, MUTED, "middle"),
    ]
    for v, anc in ((-lim / 1.12, "start"), (lim / 1.12, "end")):
        vv = float(f"{v:.2g}")
        out.append(
            t(
                px + 2 if anc == "start" else px + larg - 2,
                yb + 20,
                pp(vv, 1).replace(" pp", ""),
                13,
                MUTED,
                anc,
                mono=True,
            )
        )
    for i, ident in enumerate(ESTIMADORES):
        y = py + 17 + 34 * i
        e = ests.get(ident) or {}
        m = e.get(chave) or {}
        if not m:
            out.append(r(px + larg / 2 - 34, y - 10, 68, 20, PAPER))
            out.append(t(px + larg / 2, y + 5, "sem dado", 13, MUTED, "middle"))
            continue
        est, ic, b = m.get("estimativa"), m.get("ic95") or [None, None], m.get("bruto")
        g = ""
        if ic[0] is not None and ic[1] is not None:
            g += ln(X(ic[0]), y, X(ic[1]), y, cor, 3)
        if b is not None:
            g += _marca("losango", X(b), y, cor)
        if est is not None:
            g += f'<circle cx="{X(est):.1f}" cy="{y:.1f}" r="5.5" fill="{cor}" stroke="{PAPER}"/>'
        k = tips.add(
            ficha(
                f"{nome}: {CURTO[ident]}",
                "seção tardia menos as demais",
                [
                    ("Estimativa", num(est, 2)),
                    ("Intervalo de 95%", f"{num(ic[0], 2)} a {num(ic[1], 2)}"),
                    ("Sem controle", num(b, 2)),
                    ("Unidades comparadas", inteiro(e.get("unidades"))),
                    (
                        "Seções tardias · demais",
                        f"{inteiro(e.get('secoes_b'))} · {inteiro(e.get('secoes_a'))}",
                    ),
                ],
                UNIDADE[chave],
            )
        )
        out.append(hit(g + area(px, y - 16, larg, 32), k))
    return "".join(out)


@registra("fechamento_voto_zona")
def fechamento_voto_zona(d, **_op) -> str:
    F = fech(d)
    ests = {e["id"]: e.get("resultado") for e in F["voto"]["estimadores"]}
    tips = Tips()
    lx, larg, gap = 250, 196, 14
    alt = 34 * len(ESTIMADORES) + 90
    h = 2 * alt + 20
    out = [
        svg_abre(
            1100,
            h,
            "A seção que fecha tarde contra as demais da mesma zona",
            "Para cinco definições de seção tardia, a diferença contra as demais seções da mesma zona em voto, "
            "comparecimento, votantes por seção e por hora e forma de habilitação, com intervalo de 95%.",
        )
    ]
    for li, painel in enumerate(PAINEIS):
        py = 60 + li * alt
        for i, ident in enumerate(ESTIMADORES):
            out.append(t(lx - 12, py + 17 + 34 * i + 5, CURTO[ident], 13, INK, "end"))
        for j, (chave, nome, cor) in enumerate(painel):
            out.append(
                _painel_metrica(
                    ests, chave, nome, cor, lx + j * (larg + gap), py, larg, tips
                )
            )
    out.append("</svg>")
    leg = legenda_html(
        [
            ("estimativa dentro da unidade (ponto) e intervalo de 95% (traço)", INK),
            ("diferença sem controle (losango vazado)", PAPER),
        ]
    )
    z = ests.get("tarde18_zona") or {}
    legenda = (
        "Diferença = seções tardias menos as demais da mesma zona (ou da mesma zona e faixa de eleitorado apto), "
        "pelo estimador do modelo de urna: percentual agregado de cada grupo dentro da unidade, média ponderada "
        f"pelos votantes, intervalo por bootstrap de {inteiro(F['voto']['bootstrap'])} reamostras de unidades. "
        f"{inteiro(z.get('unidades'))} zonas com seções dos dois grupos na primeira linha. Em 2022 não há hora de "
        f"encerramento nem habilitação no arquivo do TSE. {nota_cobertura(F)} Fonte: fechamento.json."
    )
    return figura_html(
        "fechamento_voto_zona", "".join(out), legenda, tips, minw=900, apos=leg
    )


__all__ = ["duracao", "hora", "nota_cobertura"]
