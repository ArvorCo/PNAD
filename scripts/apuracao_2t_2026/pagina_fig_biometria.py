"""Figuras do bloco "Como o eleitor foi habilitado" (capítulo seções, 2º turno).

Tudo sai de ``biometria.json`` (``scripts/apuracao-2t-2026-biometria.py``):
categorias por turno, UFs, mapa por UF, os 30 municípios de maior parcela por
ano de nascimento, histograma por seção e modelo de urna. O exterior entra no
gráfico das categorias pela contagem do log da urna, marcada como tal.
"""

from __future__ import annotations

import re
from html import escape

from apuracao_2026.pagina_comum import CINZA, INK, MUTED, inteiro, tabela
from apuracao_2026.pagina_fig_base import (
    Tips,
    area,
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
)
from apuracao_2026.pagina_mapas import mapa_uf, pontos_brasil

from .pagina_fig_turnos_util import faixa, nome_uf

COR_BIO = "#2f5d8f"
COR_ANO = "#7d5b00"
COR_SEM = "#0c7a72"
COR_EXT = "#6b4a92"
COR_1T = CINZA
FONTE = "Fonte: biometria.json (BUs de todas as seções dos dois turnos)."
N_ROTULOS = 8
PATH_UF = re.compile(r'<path [^>]*data-uf="([A-Z]{2})"><title>[^<]*</title></path>')
CIRCULO = re.compile(r"<circle [^>]*><title>([^<]*)</title></circle>")


def _com_fichas(svg: str, padrao: re.Pattern, chaves: dict[str, str]) -> str:
    """Põe cada elemento do ``padrao`` cujo grupo 1 está em ``chaves`` num ``hit`` com a ficha."""

    def troca(m: re.Match) -> str:
        k = chaves.get(m.group(1))
        return hit(m.group(0), k, foco=True) if k else m.group(0)

    return padrao.sub(troca, svg)


def _ficha_uf(u: dict) -> str:
    return ficha(
        nome_uf(u["uf"]),
        "habilitados por ano de nascimento",
        [
            ("2º turno", pct(u["ano_nascimento_pct_2t"])),
            ("1º turno", pct(u["ano_nascimento_pct_1t"])),
            ("diferença", pp(u["ano_nascimento_delta_pp"])),
            ("sem cadastro, 2º turno", pct(u["sem_cadastro_pct_2t"])),
        ],
    )


def _segmentos(B: dict, turno: str) -> list[tuple[str, str, int, str]]:
    tt = B["totais"][turno]
    ex = (B.get("exterior_log") or {}).get(turno) or {}
    return [
        ("biometria reconhecida", COR_BIO, tt["biometria"], "BU"),
        ("ano de nascimento", COR_ANO, tt["ano_nascimento"], "BU"),
        ("sem biometria cadastrada", COR_SEM, tt["sem_cadastro"], "BU"),
        (
            "exterior, sem conferência biométrica",
            COR_EXT,
            ex.get("sem_biometria", 0),
            "log",
        ),
    ]


def fig_categorias(B: dict) -> str:
    w, esq, dir_ = 900, 110, 30
    topo, alt = 50, 46
    x = escala(0, 100, esq, w - dir_)
    out = [
        svg_abre(
            w,
            topo + 2 * (alt + 40) + 10,
            "Como o eleitor foi habilitado, 1º e 2º turno",
            "Barras empilhadas de 0 a 100% do comparecimento: biometria, ano de nascimento, "
            "sem cadastro e exterior (contagem do log).",
        ),
        t(esq, 24, "parcela do comparecimento total", 13, MUTED),
    ]
    tips = Tips()
    for i, turno in enumerate(("1t", "2t")):
        segs = _segmentos(B, turno)
        tot = sum(s[2] for s in segs) or 1
        y = topo + i * (alt + 40)
        out.append(
            t(
                esq - 10,
                y + alt / 2 + 5,
                f"{turno[0]}º turno",
                15,
                INK,
                "end",
                weight="700",
            )
        )
        x0 = esq
        for nome, cor, v, fonte in segs:
            p = 100 * v / tot
            wd = x(p) - esq
            k = tips.add(
                ficha(
                    nome,
                    f"{turno[0]}º turno, fonte {fonte}",
                    [("eleitores", inteiro(v)), ("parcela do comparecimento", pct(p))],
                )
            )
            out.append(hit(r(x0, y, wd, alt, cor) + area(x0, y, wd, alt), k))
            if p >= 4:
                out.append(
                    t(
                        x0 + wd / 2,
                        y + alt / 2 + 5,
                        pct(p, 1),
                        13,
                        "#fff",
                        "middle",
                        weight="700",
                    )
                )
            x0 += wd
        out.append(
            t(
                esq,
                y + alt + 22,
                "  ".join(
                    f"{n.split(',')[0]} {pct(100 * v / tot)}" for n, _, v, _ in segs[1:]
                ),
                13,
                INK,
            )
        )
    out.append("</svg>")
    leg = legenda_html(
        [(f"{n} (fonte {f})", c) for n, c, _, f in _segmentos(B, "2t")], "Categoria"
    )
    t2 = B["totais"]["2t"]
    tot2 = sum(s[2] for s in _segmentos(B, "2t")) or 1
    legenda = (
        f"As três categorias do BU fecham o comparecimento com categoria "
        f"({inteiro(t2['comparecimento_com_categoria'])} no 2º turno). O exterior vem do log "
        f"das urnas, não do BU, que não publica as categorias. A barra divide o comparecimento total, com o "
        f"exterior (biometria {pct(100 * t2['biometria'] / tot2)} no 2º turno); o texto usa o Brasil sem o "
        f"exterior ({pct(t2['biometria_pct'])}). {FONTE}"
    )
    return figura_html(
        "bio_categorias", "".join(out), legenda, tips, modo="scroll", minw=760, apos=leg
    )


def fig_ufs(B: dict) -> str:
    ufs = sorted(B["por_uf"], key=lambda u: -(u["ano_nascimento_pct_2t"] or 0))
    w, esq, dir_ = 760, 150, 80
    topo, passo = 44, 24
    h = topo + passo * len(ufs) + 16
    vmax = max(max(u["ano_nascimento_pct_2t"], u["ano_nascimento_pct_1t"]) for u in ufs)
    x = escala(0, vmax * 1.05, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Habilitados por ano de nascimento por UF, 2º turno com marca do 1º",
            "Barras horizontais por UF, ordenadas; traço preto marca o 1º turno.",
        ),
        t(esq, 22, "% do comparecimento; traço: 1º turno", 13, MUTED),
    ]
    tips = Tips()
    for i, u in enumerate(ufs):
        y = topo + i * passo
        v2, v1 = u["ano_nascimento_pct_2t"], u["ano_nascimento_pct_1t"]
        k = tips.add(_ficha_uf(u))
        partes = [
            t(esq - 8, y + 15, nome_uf(u["uf"]), 13, INK, "end"),
            r(esq, y + 3, x(v2) - esq, 16, COR_ANO),
            ln(x(v1), y, x(v1), y + 22, INK, 2),
            t(max(x(v2), x(v1)) + 6, y + 15, pct(v2), 12.5, INK, mono=True),
            area(0, y, w, passo),
        ]
        out.append(hit("".join(partes), k))
    out.append("</svg>")
    return figura_html(
        "bio_ufs",
        "".join(out),
        f"Ordem pelo 2º turno. {FONTE}",
        tips,
        modo="scroll",
        minw=640,
    )


CORTES = [5.0, 6.0, 7.0, 8.0]
CORES = ["#efe6cf", "#dcc48a", "#b8913a", "#8a6410", "#5a3f05"]
ROTULOS = ["abaixo de 5%", "5% a 6%", "6% a 7%", "7% a 8%", "8% ou mais"]


def fig_mapa_uf(B: dict) -> str:
    vals = {u["uf"]: u for u in B["por_uf"]}
    svg = mapa_uf(
        vals,
        lambda uf, u: (
            "#d8d4c8" if not u else CORES[faixa(u["ano_nascimento_pct_2t"], CORTES)]
        ),
        lambda uf, u: uf,
        lambda uf, u: (
            f"{nome_uf(uf)}: {pct(u['ano_nascimento_pct_2t'])} por ano de nascimento "
            f"({pp(u['ano_nascimento_delta_pp'])} contra o 1º turno)"
            if u
            else uf
        ),
        "Habilitados por ano de nascimento por UF, 2º turno",
        "Mapa do Brasil por UF, cor pela parcela do comparecimento habilitada por ano de nascimento.",
        escuro=lambda uf, u: bool(u) and faixa(u["ano_nascimento_pct_2t"], CORTES) >= 3,
    )
    tips = Tips()
    svg = _com_fichas(
        svg, PATH_UF, {uf: tips.add(_ficha_uf(u)) for uf, u in vals.items()}
    )
    leg = legenda_html(
        list(zip(ROTULOS, CORES, strict=True)), "Ano de nascimento, % do comparecimento"
    )
    return figura_html(
        "bio_mapa_uf",
        svg,
        f"Exterior fora: sem categoria no BU. {FONTE}",
        tips,
        modo="fit",
        apos=leg,
    )


def fig_mapa_mun(B: dict) -> str:
    ms = [
        m for m in B["municipios"]["maior_ano_nascimento"] if m.get("lat") is not None
    ]
    amax = max(m["aptos_2t"] for m in ms) or 1
    pontos = [
        {
            "lat": m["lat"],
            "lon": m["lon"],
            "raio": 4 + 10 * (m["aptos_2t"] / amax) ** 0.5,
            "cor": COR_ANO,
            "titulo": (
                f"{m['nome']} ({m['uf']}): {pct(m['ano_nascimento_pct_2t'])} por ano de "
                f"nascimento no 2º turno, {pct(m['ano_nascimento_pct_1t'])} no 1º"
            ),
            "rotulo": m["nome"] if i < N_ROTULOS else "",
        }
        for i, m in enumerate(ms)
    ]
    svg = pontos_brasil(
        pontos,
        f"Os {len(ms)} municípios com maior parcela por ano de nascimento",
        "Pontos nos municípios com 20 mil eleitores ou mais de maior parcela habilitada por ano de nascimento; raio pelo eleitorado.",
        rotulos=N_ROTULOS,
    )
    svg = svg.replace('viewBox="0 0 640 640"', 'viewBox="0 0 800 640"', 1)
    desenhados = sum(
        1 for m in ms[:N_ROTULOS] if m["nome"] and f">{escape(m['nome'])}</text>" in svg
    )
    tips = Tips()
    chaves = {
        escape(q["titulo"]): tips.add(
            ficha(
                f"{nome_bonito(m['nome'] or m['mun'])} ({m['uf']})",
                "habilitados por ano de nascimento",
                [
                    ("2º turno", pct(m["ano_nascimento_pct_2t"])),
                    ("1º turno", pct(m["ano_nascimento_pct_1t"])),
                    ("diferença", pp(m["ano_nascimento_delta_pp"])),
                    ("sem cadastro, 2º turno", pct(m["sem_cadastro_pct_2t"])),
                    ("aptos, 2º turno", inteiro(m["aptos_2t"])),
                ],
            )
        )
        for q, m in zip(pontos, ms, strict=True)
    }
    svg = _com_fichas(svg, CIRCULO, chaves)
    legenda = (
        f"{len(ms)} municípios entre os {inteiro(B['municipios']['n_municipios'])} com 20 mil "
        f"aptos ou mais; raio pelo eleitorado; rótulo em {desenhados} dos {N_ROTULOS} de maior parcela "
        f"(os outros se sobreporiam). {FONTE}"
    )
    return figura_html("bio_mapa_mun", svg, legenda, tips, modo="fit", dim=False)


def fig_histograma(B: dict) -> str:
    H = B["histograma_ano_nascimento"]
    c1, c2 = H["turnos"]["1t"]["contagem"], H["turnos"]["2t"]["contagem"]
    n1, n2 = sum(c1) or 1, sum(c2) or 1
    p1 = [100 * c / n1 for c in c1]
    p2 = [100 * c / n2 for c in c2]
    w, esq, dir_, y0, y1 = 900, 60, 20, 40, 300
    vmax = max(p1 + p2)
    larg = (w - esq - dir_) / len(p2)
    y = escala(0, vmax * 1.08, y1, y0)
    out = [
        svg_abre(
            w,
            y1 + 50,
            "Parcela habilitada por ano de nascimento em cada seção, 1º e 2º turno",
            "Histograma por seção em caixas de 1 ponto; cinza é o 1º turno, dourado é o 2º.",
        ),
        t(esq, 22, "% das seções em cada caixa de 1 ponto", 13, MUTED),
    ]
    tips = Tips()
    for k in range(len(p2)):
        x0 = esq + k * larg
        rot = f"{k}% a {k + 1}%" if k < len(p2) - 1 else f"{k}% ou mais"
        kk = tips.add(
            ficha(
                rot,
                "parcela por ano de nascimento na seção",
                [
                    ("1º turno", f"{inteiro(c1[k])} seções ({pct(p1[k])})"),
                    ("2º turno", f"{inteiro(c2[k])} seções ({pct(p2[k])})"),
                ],
            )
        )
        partes = [
            r(x0 + 1, y(p1[k]), larg / 2 - 1, y1 - y(p1[k]), COR_1T),
            r(x0 + larg / 2, y(p2[k]), larg / 2 - 1, y1 - y(p2[k]), COR_ANO),
            area(x0, y0, larg, y1 - y0),
        ]
        out.append(hit("".join(partes), kk))
        if k % 5 == 0 or k == len(p2) - 1:
            out.append(
                t(
                    x0 + larg / 2,
                    y1 + 20,
                    f"{k}{'+' if k == len(p2) - 1 else ''}",
                    12.5,
                    MUTED,
                    "middle",
                )
            )
    out.append(ln(esq, y1, w - dir_, y1, MUTED, 1))
    out.append("</svg>")
    leg = legenda_html([("1º turno", COR_1T), ("2º turno", COR_ANO)])
    h2 = H["turnos"]["2t"]
    legenda = (
        f"Mediana {pct(h2['p50'])}, 90º percentil {pct(h2['p90'])}; "
        f"{inteiro(h2['secoes_30_mais'])} seções com 30% ou mais no 2º turno. {FONTE}"
    )
    return figura_html(
        "bio_histograma", "".join(out), legenda, tips, modo="scroll", minw=640, apos=leg
    )


def fig_modelos(B: dict) -> str:
    lin = [x for x in B["modelos"]["por_modelo"] if x["modelo"].startswith("UE")]
    mods = sorted({x["modelo"] for x in lin})
    val = {(x["turno"], x["modelo"]): x for x in lin}
    w, esq, dir_, topo, passo = 760, 110, 90, 44, 58
    h = topo + passo * len(mods) + 10
    vmax = max(x["ano_nascimento_pct"] for x in lin)
    x = escala(0, vmax * 1.1, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Habilitados por ano de nascimento por modelo de urna",
            "Barras por modelo de urna, 1º turno em cinza e 2º em dourado.",
        ),
        t(esq, 22, "% do comparecimento", 13, MUTED),
    ]
    tips = Tips()
    for i, m in enumerate(mods):
        yb = topo + i * passo
        a1, a2 = val.get(("1t", m)), val.get(("2t", m))
        k = tips.add(
            ficha(
                m,
                "habilitados por ano de nascimento",
                [
                    (
                        "1º turno",
                        (
                            f"{pct(a1['ano_nascimento_pct'])} em {inteiro(a1['secoes'])} seções"
                            if a1
                            else "s/d"
                        ),
                    ),
                    (
                        "2º turno",
                        (
                            f"{pct(a2['ano_nascimento_pct'])} em {inteiro(a2['secoes'])} seções"
                            if a2
                            else "s/d"
                        ),
                    ),
                ],
            )
        )
        partes = [t(esq - 10, yb + 24, m, 15, INK, "end", weight="700")]
        for j, (a, cor) in enumerate(((a1, COR_1T), (a2, COR_ANO))):
            if not a:
                continue
            yy = yb + 4 + j * 22
            partes.append(r(esq, yy, x(a["ano_nascimento_pct"]) - esq, 18, cor))
            partes.append(
                t(
                    x(a["ano_nascimento_pct"]) + 6,
                    yy + 14,
                    pct(a["ano_nascimento_pct"]),
                    13,
                    INK,
                    mono=True,
                )
            )
        partes.append(area(0, yb, w, passo))
        out.append(hit("".join(partes), k))
    out.append("</svg>")
    leg = legenda_html([("1º turno", COR_1T), ("2º turno", COR_ANO)])
    return figura_html(
        "bio_modelos",
        "".join(out),
        f"Modelo da urna pelo log da seção. {FONTE}",
        tips,
        modo="scroll",
        minw=600,
        apos=leg,
    )


def tabela_municipios(B: dict) -> str:
    linhas = [
        [
            f"{nome_bonito(m['nome'] or m['mun'])} ({m['uf']})",
            inteiro(m["aptos_2t"]),
            pct(m["ano_nascimento_pct_2t"]),
            pct(m["ano_nascimento_pct_1t"]),
            pp(m["ano_nascimento_delta_pp"]),
            pct(m["sem_cadastro_pct_2t"]),
        ]
        for m in B["municipios"]["maior_ano_nascimento"]
    ]
    return tabela(
        ["Município", "Aptos", "Ano de nasc. 2T", "1T", "Diferença", "Sem cadastro 2T"],
        linhas,
        f"Os 30 municípios com 20 mil aptos ou mais de maior parcela por ano de nascimento no 2º turno. {FONTE}",
    )
