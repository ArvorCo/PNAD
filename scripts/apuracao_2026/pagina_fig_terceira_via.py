"""Figuras do capítulo 13: onde está o voto da terceira via e o nulo de 2022.

Dados em `analysis/apuracao_2026/dados/terceira_via.json`
(`scripts/apuracao-2026-terceira-via.py`). Três figuras aqui:

- `terceira_via_mapa`: bolha por município no centroide (área pelos votos de
  terceira via, cor pela classe de margem de Flávio), filtro por região;
- `terceira_via_classes`: barras empilhadas por UF, estoque por classe de margem;
- `nulo_2022_municipios`: aumento do branco e nulo entre os turnos de 2022 contra
  a terceira via de 2022, ponto por município, com as duas retas ponderadas.

As outras duas (`terceira_via_prioridade`, `terceira_via_teto_uf`) estão em
`pagina_fig_terceira_via_b.py`.
"""

from __future__ import annotations

import math
from functools import cache

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    COR_REGIAO,
    GRADE,
    INK,
    LIMA,
    MUTED,
    REGIOES,
    Tips,
    W,
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
    rotulos_com_fio,
    svg_abre,
    t,
    tabela_linhas,
    ticks,
)
from .pagina_fig_mapas import MH, MW, paths_uf
from .pagina_mapas import _aneis, _geo_municipal

CLASSES = ("venceu_folga", "venceu_apertado", "perdeu_apertado", "perdeu_folga")
COR_CLASSE = {
    "venceu_folga": "#123f7e",
    "venceu_apertado": "#5d8bcb",
    "perdeu_apertado": "#d9775f",
    "perdeu_folga": "#8f2618",
}
ROT_CLASSE = {
    "venceu_folga": "Flávio venceu por 10 pontos ou mais",
    "venceu_apertado": "Flávio venceu por menos de 10",
    "perdeu_apertado": "Flávio perdeu por menos de 10",
    "perdeu_folga": "Flávio perdeu por 10 pontos ou mais",
}
COR_GOV = "#b8600b"
COR_SEM_GOV = "#6f7c76"
UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]


def municipios(d) -> list[dict]:
    return tabela_linhas(dado(d, "terceira_via")["municipios"])


def _centroide(aneis: list[list[list[float]]]) -> tuple[float, float] | None:
    """Centroide do anel de maior área (fórmula da área com sinal)."""
    melhor, area_max = None, 0.0
    for anel in aneis:
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(anel, anel[1:] + anel[:1], strict=True):
            cr = x0 * y1 - x1 * y0
            a += cr
            cx += (x0 + x1) * cr
            cy += (y0 + y1) * cr
        if abs(a) > area_max and a != 0:
            area_max = abs(a)
            melhor = (cx / (3 * a), cy / (3 * a))
    return melhor


@cache
def centroides() -> dict[str, tuple[float, float]]:
    """Centroide (lon, lat) de cada município pelo código IBGE, das malhas por UF."""
    saida = {}
    for uf in UFS:
        geo = _geo_municipal(uf)
        if geo is None:
            raise KeyError(f"apuracao/public/geo/mun/{uf}.geojson")
        for f in geo["features"]:
            c = _centroide(_aneis(f["geometry"]))
            if c is not None:
                saida[str(f["properties"]["codarea"])] = c
    return saida


def votos_curto(x: float) -> str:
    """Votos em prosa curta para rótulo: 1,2 mi, 739 mil, 950."""
    a = abs(x)
    s = "−" if x < 0 else ""
    if a >= 1_000_000:
        return f"{s}{num(a / 1e6, 2)} mi"
    if a >= 10_000:
        return f"{s}{num(a / 1000, 0)} mil"
    return f"{s}{inteiro(a)}"


def sinal_votos(x: float) -> str:
    return ("+" if x > 0 else "") + votos_curto(x)


def direita_local(m: dict) -> str:
    if m["vao_votos"] > 0 and m["local_lider"]:
        return f"{nome_bonito(m['local_lider'])} {sinal_votos(m['vao_votos'])}"
    return "nenhum"


# ------------------------------------------------------------------ mapa


@registra("terceira_via_mapa")
def terceira_via_mapa(d, **_op) -> str:
    mun = municipios(d)
    cen = centroides()
    proj, _ = VM._proj(MW, MH, 10.0)
    emax = max(m["estoque"] for m in mun)
    k = 26 / math.sqrt(emax)
    out = [
        svg_abre(
            MW,
            MH,
            "Votos de terceira via por município, pela margem de Flávio",
            "Bolha no centroide de cada município; área proporcional aos votos de Cury, Renan, Caiado, Zema e "
            "demais; cor pela margem de Flávio sobre Lula no 1º turno.",
            ' data-near="1"',
        )
    ]
    for _uf, g in sorted(paths_uf().items()):
        out.append(
            f'<path d="{g["d"]}" fill="#ebe5d6" stroke="#b9b29f" stroke-width="0.8"/>'
        )
    linhas, xy, grupos = [], [], []
    lotes: dict[tuple[float, int, str], list[str]] = {}
    for m in sorted(mun, key=lambda m: -m["estoque"]):
        c = cen.get(str(m["ibge"]))
        if c is None:
            continue
        x, y = proj(*c)
        raio = max(0.8, round(k * math.sqrt(m["estoque"]) * 2) / 2)
        gi = REGIOES.index(m["regiao"])
        lotes.setdefault((raio, gi, m["classe"]), []).append(f"M{x:.0f} {y:.0f}h0")
        linhas.append(
            [
                f"{nome_bonito(m['nome'])} ({m['uf']})",
                f"{votos_curto(m['estoque'])} ({num(m['estoque_pct'], 1)}%)",
                *(
                    votos_curto(m[g])
                    for g in ("renan", "zema", "cury", "caiado", "outros")
                ),
                pp(m["margem_pp"], 1),
                sinal_votos(m["saldo"]),
                direita_local(m),
                f"{m['posicao']}º",
            ]
        )
        xy.append([round(x), round(y), raio])
        grupos.append(str(gi))
    for (raio, gi, classe), segs in sorted(lotes.items(), key=lambda kv: -kv[0][0]):
        out.append(
            f'<path data-g="{gi}" d="{"".join(segs)}" stroke="{COR_CLASSE[classe]}" '
            f'stroke-width="{2 * raio}" stroke-linecap="round" stroke-opacity="0.72" fill="none"/>'
        )
    # rótulo fora da bolha, com fio, e o contorno da bolha rotulada por cima
    pontos = []
    for m in sorted(mun, key=lambda m: -m["estoque"])[:8]:
        c = cen.get(str(m["ibge"]))
        if c is None:
            continue
        x, y = proj(*c)
        raio = max(0.8, round(k * math.sqrt(m["estoque"]) * 2) / 2)
        pontos.append((x, y, raio, nome_bonito(m["nome"]), COR_CLASSE[m["classe"]]))
    ref_y = MH - 70
    out.append(rotulos_com_fio(pontos, (4, 4, MW - 4, ref_y - 50)))
    out.append(t(14, ref_y - 30, "Votos de terceira via", 13.5, INK, weight="700"))
    cx = 24
    for v in (10_000, 100_000, 500_000):
        rr = k * math.sqrt(v)
        out.append(
            f'<circle cx="{cx + rr:.1f}" cy="{ref_y + 30 - rr:.1f}" r="{rr:.1f}" fill="none" '
            f'stroke="{MUTED}" stroke-width="1"/>'
        )
        out.append(t(cx + rr, ref_y + 46, votos_curto(v), 13, MUTED, "middle"))
        cx += 2 * rr + 34
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Município",
            "Terceira via",
            "Renan",
            "Zema",
            "Cury",
            "Caiado",
            "Demais",
            "Margem de Flávio",
            "Saldo (Nexus)",
            "Acima de Flávio",
            "Posição no índice",
        ],
        linhas,
        xy=xy,
        grupos=grupos,
        nota="matriz nacional aplicada ao município: hipótese, não medição local",
    )
    TV = dado(d, "terceira_via")
    nac = TV["agregados"]["brasil"]
    ctl = botoes(
        [("", "Brasil")] + [(str(i), reg) for i, reg in enumerate(REGIOES)],
        "",
        "Região",
        "filtro",
    )
    leg = legenda_html(
        [(ROT_CLASSE[c], COR_CLASSE[c]) for c in CLASSES],
        "Margem de Flávio sobre Lula no 1º turno",
    )
    legenda_ = (
        f"Cada bolha é um município, no centroide da malha do IBGE; a área segue os votos de terceira via "
        f"({inteiro(nac['estoque'])} no Brasil). {pct(nac['onde_flavio_venceu_parcela'], 1)} desse voto está onde Flávio "
        "venceu. O filtro apaga as outras regiões; a ficha traz a composição por candidatura, o que a matriz Nexus "
        "manda para cada lado e o nome da direita local que teve mais votos que Flávio ali. Fonte: terceira_via.json."
    )
    return figura_html(
        "terceira_via_mapa",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        modo="fit",
        dim=False,
        apos=leg,
    )


# ------------------------------------------------------------------ classes por UF


@registra("terceira_via_classes")
def terceira_via_classes(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    ufs = TV["agregados"]["ufs"]
    ordem = sorted(ufs, key=lambda u: -ufs[u]["onde_flavio_venceu"])
    esq, topo, passo = 190, 64, 28
    base = topo + passo * len(ordem)
    h = base + 60
    vmax = max(ufs[u]["estoque"] for u in ordem)
    tips = Tips()
    modos = {"votos": "Votos", "parcela": "Parcela da UF"}
    out = [
        svg_abre(
            W,
            h,
            "Votos de terceira via por UF, pela margem de Flávio no município",
            "Barras empilhadas por UF: votos de terceira via em municípios onde Flávio venceu com folga, venceu "
            "apertado, perdeu apertado e perdeu com folga. Ordem: votos onde Flávio venceu.",
        )
    ]
    for modo in modos:
        if modo == "votos":
            X = escala(0, vmax * 1.04, esq, W - 150)
            marcas = ticks(0, vmax * 1.04, 6)
        else:
            X = escala(0, 100, esq, W - 150)
            marcas = ticks(0, 100, 5)
        g = []
        for v in marcas:
            g.append(ln(X(v), topo - 8, X(v), base, GRADE))
            rotulo = votos_curto(v) if modo == "votos" else f"{num(v, 0)}%"
            g.append(t(X(v), base + 20, rotulo, 13, MUTED, "middle", mono=True))
        for i, uf in enumerate(ordem):
            u = ufs[uf]
            y = topo + i * passo
            x0 = esq
            corpo = [t(esq - 10, y + 18, NOME_UF[uf], 13.5, INK, "end")]
            for c in CLASSES:
                v = u["por_classe"][c]["estoque"]
                largura = (
                    (X(v) - X(0))
                    if modo == "votos"
                    else (X(u["por_classe"][c]["estoque_parcela"] or 0) - X(0))
                )
                corpo.append(r(x0, y + 5, largura, passo - 10, COR_CLASSE[c]))
                x0 += largura
            direita = (
                votos_curto(u["estoque"])
                if modo == "votos"
                else f"{pct(u['onde_flavio_venceu_parcela'], 0)} onde venceu"
            )
            corpo.append(t(x0 + 8, y + 18, direita, 13, INK, mono=True))
            if modo == "votos":
                linhas_f = [
                    (
                        ROT_CLASSE[c],
                        f"{inteiro(u['por_classe'][c]['estoque'])} ({pct(u['por_classe'][c]['estoque_parcela'], 1)})",
                    )
                    for c in CLASSES
                ]
                k = tips.add(
                    ficha(
                        NOME_UF[uf],
                        f"{inteiro(u['estoque'])} votos de terceira via",
                        [
                            *linhas_f,
                            (
                                "Onde Flávio venceu",
                                pct(u["onde_flavio_venceu_parcela"], 1),
                            ),
                            ("Renan e Zema no estoque", pct(u["renan_zema_pct"], 1)),
                            ("Saldo pela matriz Nexus", sinal_votos(u["saldo"])),
                            (
                                "Com Datafolha para Cury e Caiado",
                                sinal_votos(u["saldo_df"]),
                            ),
                            (
                                "Direita local acima de Flávio",
                                votos_curto(u["vao_positivo"]),
                            ),
                        ],
                        "matriz nacional aplicada à UF: hipótese, não medição local",
                    )
                )
                tips_k = k
            else:
                tips_k = f"p{uf}"
            g.append(hit(area(0, y, W, passo) + "".join(corpo), tips_k))
        mostra = "" if modo == "votos" else ' display="none"'
        out.append(f'<g data-alt-show="{modo}"{mostra}>{"".join(g)}</g>')
    out.append("</svg>")
    for uf in ordem:
        u = ufs[uf]
        tips.html[f"p{uf}"] = ficha(
            NOME_UF[uf],
            "parcela do estoque da UF",
            [
                (ROT_CLASSE[c], pct(u["por_classe"][c]["estoque_parcela"], 1))
                for c in CLASSES
            ],
        )
    ctl = botoes(list(modos.items()), "votos", "Escala")
    leg = legenda_html(
        [(ROT_CLASSE[c], COR_CLASSE[c]) for c in CLASSES],
        "Margem de Flávio no município",
    )
    nac = TV["agregados"]["brasil"]
    legenda_ = (
        "Votos de terceira via de cada UF, separados pela margem de Flávio sobre Lula no município. Ordem: votos onde "
        f"Flávio venceu. No país, {pct(nac['por_classe']['venceu_folga']['estoque_parcela'], 1)} do estoque está onde ele "
        f"venceu com folga e {pct(nac['por_classe']['perdeu_folga']['estoque_parcela'], 1)} onde Lula venceu com folga. "
        "A classe é uma variável, não filtro. Fonte: terceira_via.json."
    )
    return figura_html(
        "terceira_via_classes",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=820,
        apos=leg,
    )


# ------------------------------------------------------------------ nulo de 2022


@registra("nulo_2022_municipios")
def nulo_2022_municipios(d, **_op) -> str:
    TV = dado(d, "terceira_via")
    N = TV["nulo_2022"]
    mun = [
        m
        for m in municipios(d)
        if m["delta_bn22_pp"] is not None and m["tv22_pct"] is not None
    ]
    largura, altura = 1000, 720
    esq, topo, lado_x, lado_y = 80, 30, 640, 600
    xlo, xhi, ylo, yhi = 0.0, 20.0, -6.0, 5.0
    X = escala(xlo, xhi, esq, esq + lado_x)
    Y = escala(ylo, yhi, topo + lado_y, topo)
    emax = max(m["eleitores"] for m in mun)
    out = [
        svg_abre(
            largura,
            altura,
            "Branco e nulo do 1º para o 2º turno de 2022, contra a terceira via de 2022",
            "Cada ponto é um município: na horizontal, a terceira via no 1º turno de 2022 (% dos válidos); na "
            "vertical, a variação de branco e nulo de presidente entre os turnos (pontos dos votantes). Duas retas "
            "ponderadas: UFs com 2º turno de governador em 2022 e as demais.",
            ' data-near="1"',
        )
    ]
    for v in ticks(xlo, xhi, 5):
        out.append(ln(X(v), topo, X(v), topo + lado_y, GRADE))
        out.append(
            t(X(v), topo + lado_y + 22, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True)
        )
    for v in ticks(ylo, yhi, 6):
        out.append(
            ln(
                esq,
                Y(v),
                esq + lado_x,
                Y(v),
                INK if v == 0 else GRADE,
                1.4 if v == 0 else 1,
            )
        )
        rot = f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 0)}"
        out.append(t(esq - 8, Y(v) + 5, rot, 13, MUTED, "end", mono=True))
    out.append(
        t(
            esq + lado_x / 2,
            altura - 40,
            "Terceira via no 1º turno de 2022 (% dos válidos)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = topo + lado_y / 2
    out.append(
        t(
            22,
            yy,
            "Branco e nulo, 2º turno menos 1º (pontos)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 22 {yy:.0f})"',
        )
    )
    linhas, xy, grupos = [], [], []
    lotes: dict[tuple[float, int, bool], list[str]] = {}
    for m in sorted(mun, key=lambda m: -m["eleitores"]):
        gi = REGIOES.index(m["regiao"])
        raio = round((1.4 + 11 * math.sqrt(m["eleitores"] / emax)) * 2) / 2
        x = X(min(max(m["tv22_pct"], xlo), xhi))
        y = Y(min(max(m["delta_bn22_pp"], ylo), yhi))
        lotes.setdefault((raio, gi, bool(m["gov22_2t"])), []).append(
            f"M{x:.0f} {y:.0f}h0"
        )
        linhas.append(
            [
                f"{nome_bonito(m['nome'])} ({m['uf']})",
                f"{num(m['tv22_pct'], 1)}%",
                f"{num(m['bn22_1t_pct'], 2)} → {num(m['bn22_2t_pct'], 2)}%",
                pp(m["delta_bn22_pp"], 2),
                "sim" if m["gov22_2t"] else "não",
                votos_curto(m["estoque"]),
            ]
        )
        xy.append([round(x), round(y), raio])
        grupos.append(str(gi))
    for (raio, gi, gov), segs in sorted(lotes.items(), key=lambda kv: -kv[0][0]):
        cor_alt = COR_GOV if gov else COR_SEM_GOV
        out.append(
            f'<path data-g="{gi}" data-as="gov>{cor_alt}" d="{"".join(segs)}" stroke="{COR_REGIAO[REGIOES[gi]]}" '
            f'stroke-width="{2 * raio}" stroke-linecap="round" stroke-opacity="0.5" fill="none"/>'
        )
    for chave, cor, rotulo in (
        ("com_2t_governador", COR_GOV, "UFs com 2º turno de governador em 2022"),
        ("sem_2t_governador", COR_SEM_GOV, "demais UFs"),
    ):
        g = N[chave]
        reg = g["regressao_terceira_via"]
        if reg["inclinacao"] is None:
            continue
        lo = min(q["tv22_min_pct"] for q in g["quintis_terceira_via"])
        hi = max(q["tv22_max_pct"] for q in g["quintis_terceira_via"])
        hi = min(hi, xhi)
        y0 = reg["intercepto"] + reg["inclinacao"] * lo
        y1 = reg["intercepto"] + reg["inclinacao"] * hi
        out.append(
            f'<line x1="{X(lo):.1f}" y1="{Y(y0):.1f}" x2="{X(hi):.1f}" y2="{Y(y1):.1f}" stroke="#ffffff" '
            f'stroke-width="6" stroke-linecap="round"/>'
        )
        out.append(
            f'<line x1="{X(lo):.1f}" y1="{Y(y0):.1f}" x2="{X(hi):.1f}" y2="{Y(y1):.1f}" stroke="{cor}" '
            f'stroke-width="3" stroke-linecap="round"/>'
        )
        texto = f"{rotulo}: {pp(g['delta_pp'], 2)} no conjunto"
        dy = -14 if chave == "com_2t_governador" else 30
        out.append(
            f'<g pointer-events="none">{chip(X(lo) + 6, Y(y0) + dy, texto, 13)}</g>'
        )
    lx = esq + lado_x + 36
    out.append(t(lx, topo + 10, "Cor", 14, INK, weight="700"))
    for i, reg in enumerate(REGIOES):
        y_ = topo + 38 + i * 24
        out.append(
            f'<circle cx="{lx + 7}" cy="{y_ - 5}" r="7" fill="{COR_REGIAO[reg]}" fill-opacity="0.75"/>'
        )
        out.append(t(lx + 22, y_, reg, 13.5))
    y_ = topo + 38 + 5 * 24 + 18
    out.append(t(lx, y_, "Na outra cor:", 13, MUTED))
    for j, (cor, rotulo) in enumerate(
        ((COR_GOV, "2º turno de governador"), (COR_SEM_GOV, "sem 2º turno estadual"))
    ):
        yy2 = y_ + 26 + j * 24
        out.append(
            f'<circle cx="{lx + 7}" cy="{yy2 - 5}" r="7" fill="{cor}" fill-opacity="0.85"/>'
        )
        out.append(t(lx + 22, yy2, rotulo, 13.5))
    out.append(t(lx, y_ + 90, "Área pelo eleitorado de 2026.", 13, MUTED))
    out.append(t(lx, y_ + 110, "Fora da escala: no limite.", 13, MUTED))
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Município",
            "Terceira via em 2022",
            "Branco e nulo, 1º → 2º turno",
            "Variação",
            "2º turno de governador em 2022",
            "Terceira via em 2026",
        ],
        linhas,
        xy=xy,
        grupos=grupos,
        nota="pontos percentuais dos votantes de presidente",
    )
    ctl = botoes(
        [("reg", "Região"), ("gov", "2º turno estadual em 2022")], "reg", "Cor"
    )
    cg, sg, nac = N["com_2t_governador"], N["sem_2t_governador"], N["nacional"]
    legenda_ = (
        f"Entre os turnos de 2022, branco e nulo de presidente foram de {pct(nac['bn_1t_pct'])} para "
        f"{pct(nac['bn_2t_pct'])} dos votantes. Subiram {pp(cg['delta_pp'], 2)} nas {len(cg['ufs'])} UFs com 2º turno de "
        f"governador e mudaram {pp(sg['delta_pp'], 2)} nas outras {len(sg['ufs'])}. As retas são mínimos quadrados "
        "ponderados pelos votantes do 2º turno. Fonte: detalhe por seção do TSE (2022), terceira_via.json."
    )
    return figura_html(
        "nulo_2022_municipios",
        "".join(out),
        legenda_,
        tips,
        controles=ctl,
        minw=700,
        dim=False,
    )
