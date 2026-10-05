"""Figuras do capítulo 12 no nível da seção eleitoral (boletins de urna), parte 1.

Lê `secoes.json` (contrato em `analysis/apuracao_2026/CONTRATO_SECOES.md`):
`secoes_90` (histograma e mapa dos locais com seção de 90% ou mais),
`secoes_excesso` (a seção contra a própria zona), `secoes_tamanho_tipo`
(tamanho, tipo de local e modelo de urna) e `clusters_secoes` (mistura
gaussiana de quatro grupos em projeção PCA). Nenhum número vem digitado: tudo
sai do JSON, e cobertura parcial aparece na legenda.
"""

from __future__ import annotations

import math
from functools import cache
from html import escape

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro, num, tabela
from .pagina_fig_base import (
    COR_REGIAO,
    FLAVIO,
    GRADE,
    INK,
    LIMA,
    LULA,
    MUTED,
    REGIOES,
    SOMBRA,
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
    ticks,
)
from .pagina_fig_mapas import MH, MW, paths_uf

OURO = "#7d5b00"
CLUSTER_COR = ["#1457aa", "#b02f21", "#0f7f5f", "#7d5b00"]
NOME = {"lula": "Lula", "flavio": "Flávio"}
COR = {"lula": LULA, "flavio": FLAVIO}
UF_REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte",
    "TO": "Norte", "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste", "PR": "Sul",
    "RS": "Sul", "SC": "Sul", "ZZ": "Exterior",
}  # fmt: skip
LIMITE_PONTOS = 6000
CELULA_GRAUS = 0.25


# ------------------------------------------------------------------ comuns


def secoes(d) -> dict:
    return dado(d, "secoes")


def nota_cobertura(S: dict) -> str:
    """Frase de cobertura para a legenda: parcial declara as UFs completas."""
    c = S["cobertura"]
    base = f"{inteiro(c['secoes_validas'])} seções válidas"
    if c.get("parcial"):
        n = len(c.get("ufs_completas") or [])
        return f"Cobertura parcial: {n} UFs completas, {base}."
    return f"Cobertura completa: {base}."


def regiao_da_uf(uf: str | None) -> str:
    return UF_REGIAO.get(uf or "", "Exterior")


def rotulo_cluster(S: dict, k: int) -> str:
    for c in S["clusters"]["componentes"]:
        if c["id"] == k:
            return f"Grupo {k + 1}: {c['rotulo']}"
    return f"Grupo {k + 1}"


def local_ref(s: dict) -> str:
    """'Cajari (MA), zona 20, seção 45, U.E. Fulano' a partir de um SecaoRef."""
    return (
        f"{nome_bonito(s['municipio'])} ({s['uf']}), zona {s['zona']}, seção {s['secao']}, "
        f"{nome_bonito(s.get('local') or 'local sem nome')}"
    )


@cache
def _caixas_uf() -> list[tuple[str, tuple[float, float, float, float], list]]:
    out = []
    for uf, aneis in VM._features().items():
        lons = [p[0] for a in aneis for p in a]
        lats = [p[1] for a in aneis for p in a]
        out.append((uf, (min(lons), min(lats), max(lons), max(lats)), aneis))
    return out


def _dentro(lon: float, lat: float, anel: list) -> bool:
    dentro = False
    n = len(anel)
    j = n - 1
    for i in range(n):
        xi, yi = anel[i][0], anel[i][1]
        xj, yj = anel[j][0], anel[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (
            (yj - yi) or 1e-12
        ) + xi:
            dentro = not dentro
        j = i
    return dentro


def uf_do_ponto(lat: float, lon: float) -> str:
    """UF pela malha do IBGE; ponto fora de todas vira a UF de caixa mais próxima."""
    perto, melhor = "", math.inf
    for uf, (x0, y0, x1, y1), aneis in _caixas_uf():
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            if sum(_dentro(lon, lat, a) for a in aneis) % 2:
                return uf
            dist = 0.0
        else:
            dist = max(x0 - lon, 0, lon - x1) + max(y0 - lat, 0, lat - y1)
        if dist < melhor:
            perto, melhor = uf, dist
    return perto


# ------------------------------------------------------------------ 1 secoes_90


def _faixa_bin(bins: list[float], i: int) -> str:
    return f"{num(bins[i], 1)} a {num(bins[i + 1], 1)}%"


def _histograma(
    E: dict, serie_l: str, serie_f: str, tips: Tips, x0: float, x1: float
) -> str:
    H = E["histograma"]
    bins = H["bins_pct"]
    lu, fl = H[serie_l], H[serie_f]
    total = sum(lu) or 1
    vmax = max([*lu, *fl, 1])
    base, meia = 300.0, 225.0
    X = escala(0, 100, x0, x1)

    def alt(v: float) -> float:
        return meia * math.sqrt(v / vmax)

    out = [r(X(90), base - meia - 8, X(100) - X(90), 2 * meia + 16, SOMBRA)]
    for v in ticks(0, vmax, 4)[1:]:
        h = alt(v)
        out.append(ln(x0, base - h, x1, base - h, GRADE, 0.8))
        out.append(ln(x0, base + h, x1, base + h, GRADE, 0.8))
        rot = inteiro(v)
        out.append(t(x0 - 6, base - h + 5, rot, 13, MUTED, "end", mono=True))
        out.append(t(x0 - 6, base + h + 5, rot, 13, MUTED, "end", mono=True))
    out.append(ln(x0, base, x1, base, INK, 1.2))
    for v in (0, 25, 50, 75, 90, 100):
        out.append(ln(X(v), base + meia + 6, X(v), base + meia + 12, MUTED))
        out.append(
            t(X(v), base + meia + 28, f"{num(v, 0)}%", 13, MUTED, "middle", mono=True)
        )
    for i in range(len(lu)):
        xa, xb = X(bins[i]), X(bins[i + 1])
        forte = bins[i] >= 90
        op = "1" if forte else "0.5"
        hl, hf = alt(lu[i]), alt(fl[i])
        barras = r(
            xa + 0.5, base - hl, xb - xa - 1, hl, LULA, f' fill-opacity="{op}"'
        ) + r(xa + 0.5, base, xb - xa - 1, hf, FLAVIO, f' fill-opacity="{op}"')
        k = tips.add(
            ficha(
                f"Seções com {_faixa_bin(bins, i)} dos válidos",
                "faixa de 90% ou mais" if forte else "",
                [
                    (
                        "Lula",
                        f"{inteiro(lu[i])} seções ({pct(100 * lu[i] / total, 2)} das seções)",
                    ),
                    (
                        "Flávio",
                        f"{inteiro(fl[i])} seções ({pct(100 * fl[i] / total, 2)} das seções)",
                    ),
                ],
            )
        )
        out.append(hit(barras + area(xa, base - meia - 8, xb - xa, 2 * meia + 16), k))
    n90 = [i for i in range(len(lu)) if bins[i] >= 90]
    sl, sf = sum(lu[i] for i in n90), sum(fl[i] for i in n90)
    out.append(
        f'<g pointer-events="none">{chip(X(90) - 6, base - meia + 12, f"Lula: {inteiro(sl)} seções", 13, "end")}'
        f'{chip(X(90) - 6, base + meia - 4, f"Flávio: {inteiro(sf)} seções", 13, "end")}</g>'
    )
    return "".join(out)


def _pontos_mapa(E: dict) -> tuple[list[dict], bool]:
    M = E["mapa"]
    cols = M["colunas"]
    pontos = [dict(zip(cols, p, strict=False)) for p in M["pontos"]]
    pontos = [
        p for p in pontos if p.get("lat") is not None and p.get("lon") is not None
    ]
    if len(pontos) <= LIMITE_PONTOS:
        return pontos, False
    cel: dict[tuple[int, int], dict] = {}
    for p in pontos:
        chave = (
            math.floor(p["lat"] / CELULA_GRAUS),
            math.floor(p["lon"] / CELULA_GRAUS),
        )
        c = cel.setdefault(
            chave,
            {"lat": 0.0, "lon": 0.0, "lula_90": 0, "flavio_90": 0, "secoes": 0, "n": 0},
        )
        c["lat"] += p["lat"]
        c["lon"] += p["lon"]
        c["n"] += 1
        for k in ("lula_90", "flavio_90", "secoes"):
            c[k] += p.get(k) or 0
    out = []
    for c in cel.values():
        c["lat"] /= c["n"]
        c["lon"] /= c["n"]
        out.append(c)
    return out, True


def _mapa_90(E: dict, tips: Tips, ox: float, oy: float, esc: float) -> tuple[str, int]:
    geo = paths_uf()
    proj, _ = VM._proj(MW, MH, 10.0)
    out = [f'<g transform="translate({ox:.1f} {oy:.1f}) scale({esc:.4f})">']
    for _uf, g in sorted(geo.items()):
        out.append(
            f'<path d="{g["d"]}" fill="#e7e1d2" stroke="#b9b29f" stroke-width="1"/>'
        )
    out.append("</g>")
    pontos, agrupado = _pontos_mapa(E)
    linhas, xy = [], []
    grupos: dict[tuple[str, float], list[str]] = {}
    for p in sorted(pontos, key=lambda p: -(p.get("secoes") or 0)):
        x, y = proj(p["lon"], p["lat"])
        x, y = ox + x * esc, oy + y * esc
        lu, fl = p.get("lula_90") or 0, p.get("flavio_90") or 0
        cor = LULA if lu > fl else FLAVIO if fl > lu else OURO
        raio = round(min(9.0, 1.8 + 1.1 * math.sqrt(p.get("secoes") or 1)) * 2) / 2
        grupos.setdefault((cor, raio), []).append(f"M{x:.0f} {y:.0f}h0")
        uf = p.get("uf") or uf_do_ponto(p["lat"], p["lon"])
        quem = "Lula" if lu > fl else "Flávio" if fl > lu else "empate"
        titulo = (
            f"{NOME_UF.get(uf, uf)}: {p['n']} locais (célula de 0,25 grau)"
            if agrupado
            else f"{NOME_UF.get(uf, uf)}: local de votação"
        )
        linhas.append(
            [
                titulo,
                inteiro(lu),
                inteiro(fl),
                inteiro(p.get("secoes")),
                quem,
                f"{num(p['lat'], 2)}, {num(p['lon'], 2)}",
            ]
        )
        xy.append([round(x), round(y), raio])
    for (cor, raio), segs in sorted(grupos.items(), key=lambda kv: -kv[0][1]):
        out.append(
            f'<path d="{"".join(segs)}" stroke="{cor}" stroke-width="{2 * raio}" '
            'stroke-linecap="round" stroke-opacity="0.7" fill="none"/>'
        )
    tips.tabela(
        [
            "Local",
            "Seções de Lula com 90% ou mais",
            "Seções de Flávio com 90% ou mais",
            "Seções do local",
            "Predomina",
            "Latitude, longitude",
        ],
        linhas,
        xy=xy,
    )
    return "".join(out), len(pontos)


@registra("secoes_90")
def secoes_90(d, **_op) -> str:
    S = secoes(d)
    E = S["extremos"]
    tips = Tips()
    w, h = 1100, 600
    corte = E.get("corte_tamanho", 100)
    out = [
        svg_abre(
            w,
            h,
            "Seções com 90% ou mais para um candidato: distribuição e mapa",
            "À esquerda, quantas seções há em cada faixa de percentual dos válidos, Lula para cima e Flávio para baixo; "
            "à direita, os locais de votação com ao menos uma seção de 90% ou mais.",
            ' data-near="1"',
        ),
        t(70, 30, "Seções por faixa de % dos válidos", 15, INK, weight="700"),
        t(76, 56, "Lula", 14, LULA, weight="700"),
        t(76, 594, "Flávio", 14, FLAVIO, weight="700"),
    ]
    out.append(
        f'<g data-alt-show="todas">{_histograma(E, "lula", "flavio", tips, 70, 520)}</g>'
    )
    out.append(
        f'<g data-alt-show="m100" display="none">'
        f'{_histograma(E, "lula_100mais", "flavio_100mais", tips, 70, 520)}</g>'
    )
    out.append(t(295, 594, "% dos válidos na seção", 13, MUTED, "middle"))
    out.append(t(570, 30, "Locais com seção de 90% ou mais", 15, INK, weight="700"))
    esc = 520 / MW
    mapa, n_pts = _mapa_90(E, tips, 570, 48, esc)
    out.append(mapa)
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    M = E["mapa"]
    agrupado = len(M["pontos"]) > LIMITE_PONTOS
    ctl = botoes(
        [
            ("todas", "Todas as seções"),
            ("m100", f"Só seções com {corte} votantes ou mais"),
        ],
        "todas",
        "Seções",
    )
    leg_mapa = legenda_html(
        [
            ("predominam seções de Lula com 90% ou mais", LULA),
            ("predominam seções de Flávio com 90% ou mais", FLAVIO),
            ("empate entre os dois", OURO),
        ],
        "Mapa: raio pelo número de seções do local",
    )
    legenda = (
        "Altura das barras em escala de raiz quadrada, para a cauda de 90% ou mais aparecer ao lado do centro da distribuição; "
        f"a faixa sombreada marca 90% ou mais. O botão restringe o histograma às seções com {corte} votantes ou mais, "
        f"onde um punhado de eleitores não basta para produzir percentual extremo. O mapa mostra {inteiro(M['n_locais'])} locais "
        f"de votação ({inteiro(M['n_sem_coordenada'])} sem coordenada ficam fora)"
        + (
            f", agrupados em células de 0,25 grau ({inteiro(n_pts)} pontos) porque passam de {inteiro(LIMITE_PONTOS)}"
            if agrupado
            else ""
        )
        + f". {nota_cobertura(S)} Fonte: secoes.json."
    )
    return figura_html(
        "secoes_90",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=860,
        dim=False,
        apos=leg_mapa,
    )


# ------------------------------------------------------------------ 2 secoes_excesso


def _coluna_excesso(
    cand: str, X: dict, x0: float, tips: Tips, total_secoes: int
) -> str:
    cor = COR[cand]
    lab, bar0, bar1 = x0, x0 + 190, x0 + 400
    n = X["secoes"] or 0
    esc = escala(0, max(n, 1), bar0, bar1)
    out = [
        t(
            lab,
            34,
            f"{NOME[cand]}: {inteiro(n)} seções com 90% ou mais",
            16,
            cor,
            weight="700",
        ),
        t(
            lab,
            58,
            f"excesso mediano sobre a zona {pp(X.get('excesso_zona_pp_mediana'), 1)}; "
            f"zona mediana {pct(X.get('zona_pct_mediana'), 1)}",
            13,
            MUTED,
        ),
        t(lab, 92, "Voto do candidato na zona da seção", 13, INK, weight="600"),
    ]
    y = 104
    linhas = [(f["rotulo"], f["secoes"], cor, "faixa") for f in X["faixas_zona"]]
    linhas.append(("", None, "", "gap"))
    linhas.append(("10 pp ou mais acima da zona", X["acima_zona_10pp"], OURO, "acima"))
    linhas.append(("20 pp ou mais acima da zona", X["acima_zona_20pp"], OURO, "acima"))
    for rot, v, c, tipo in linhas:
        if tipo == "gap":
            out.append(t(lab, y + 20, "Distância para a zona", 13, INK, weight="600"))
            y += 30
            continue
        v = v or 0
        parte = 100 * v / n if n else 0
        out.append(t(lab, y + 19, rot, 14, INK))
        k = tips.add(
            ficha(
                f"{NOME[cand]}: {rot}",
                "seções com 90% ou mais",
                [
                    ("Seções", inteiro(v)),
                    (f"Parte das {inteiro(n)} seções", pct(parte, 1)),
                    (
                        "Parte de todas as seções válidas",
                        pct(100 * v / total_secoes, 3),
                    ),
                ],
                (
                    "excesso = % da seção menos % da zona sem a própria seção"
                    if tipo == "acima"
                    else "faixa pelo voto do candidato no resto da zona"
                ),
            )
        )
        barra = r(bar0, y + 4, esc(v) - bar0, 20, c)
        out.append(hit(barra + area(lab, y, bar1 - lab + 110, 28), k))
        out.append(
            t(esc(v) + 6, y + 19, f"{inteiro(v)} ({pct(parte, 1)})", 13, INK, mono=True)
        )
        y += 34
    return "".join(out)


@registra("secoes_excesso")
def secoes_excesso(d, **_op) -> str:
    S = secoes(d)
    X = S["extremos"]["excesso"]
    tips = Tips()
    total = S["cobertura"]["secoes_validas"] or 1
    nf = max(len(X["lula"]["faixas_zona"]), len(X["flavio"]["faixas_zona"]))
    w, h = 1100, 104 + 34 * (nf + 2) + 50
    out = [
        svg_abre(
            w,
            h,
            "Seções de 90% ou mais contra o voto da própria zona",
            "Para Lula e para Flávio, quantas seções de 90% ou mais estão em zonas que já votam acima de 80%, "
            "de 60 a 80%, de 40 a 60% ou abaixo de 40% no mesmo candidato, e quantas ficam 10 ou 20 pontos acima da zona.",
        ),
        _coluna_excesso("lula", X["lula"], 30, tips, total),
        _coluna_excesso("flavio", X["flavio"], 580, tips, total),
        "</svg>",
    ]
    legenda = (
        "90% numa zona que já dá 85% ao candidato é rotina; 90% numa zona de 50% exige explicação documental. As barras "
        "de cima contam as seções pelo voto do candidato no resto da zona; as douradas, as que ficam 10 ou 20 pontos acima "
        f"dele. {escape(X.get('definicao', '').rstrip('.'))}. {nota_cobertura(S)} Fonte: secoes.json."
    )
    return figura_html("secoes_excesso", "".join(out), legenda, tips, minw=860)


# ------------------------------------------------------------------ 3 secoes_tamanho_tipo


def _grupo_barras(
    linhas: list[dict],
    chave_rot: str,
    k_l: str,
    k_f: str,
    tips: Tips,
    titulo_ficha: str,
    medias: tuple[float | None, float | None],
) -> str:
    x0, x1 = 250, 900
    vmax = max(
        [
            *(ln_[k_l] or 0 for ln_ in linhas),
            *(ln_[k_f] or 0 for ln_ in linhas),
            *(m or 0 for m in medias),
            0.1,
        ]
    )
    X = escala(0, vmax * 1.08, x0, x1)
    out = []
    for v in ticks(0, vmax * 1.08, 5):
        out.append(ln(X(v), 40, X(v), 52 + 46 * len(linhas), GRADE, 0.8))
        out.append(t(X(v), 32, f"{num(v, 1)}%", 13, MUTED, "middle", mono=True))
    y = 52
    for L in linhas:
        out.append(t(30, y + 26, str(L[chave_rot]), 14, INK, weight="600"))
        k = tips.add(
            ficha(
                f"{titulo_ficha} {L[chave_rot]}",
                "",
                [
                    ("Seções válidas", inteiro(L["todas"])),
                    ("Lula 90% ou mais", f"{inteiro(L['lula_90'])} ({pct(L[k_l], 2)})"),
                    (
                        "Flávio 90% ou mais",
                        f"{inteiro(L['flavio_90'])} ({pct(L[k_f], 2)})",
                    ),
                ],
                "percentual das seções do próprio grupo",
            )
        )
        barras = r(x0, y + 6, X(L[k_l] or 0) - x0, 16, LULA) + r(
            x0, y + 23, X(L[k_f] or 0) - x0, 16, FLAVIO
        )
        out.append(hit(barras + area(20, y + 2, x1 + 160 - 20, 42), k))
        out.append(t(X(L[k_l] or 0) + 6, y + 19, pct(L[k_l], 1), 13, INK, mono=True))
        out.append(t(X(L[k_f] or 0) + 6, y + 36, pct(L[k_f], 1), 13, INK, mono=True))
        y += 46
    for m, cor, nome in ((medias[0], LULA, "Lula"), (medias[1], FLAVIO, "Flávio")):
        if m is None:
            continue
        out.append(ln(X(m), 44, X(m), y + 2, cor, 1.6, ' stroke-dasharray="5 4"'))
        out.append(
            f'<g pointer-events="none">{chip(X(m) + 4, y + 22 + (18 if cor == FLAVIO else 0), f"{nome} no total: {pct(m, 1)}", 13)}</g>'
        )
    return "".join(out)


@registra("secoes_tamanho_tipo")
def secoes_tamanho_tipo(d, **_op) -> str:
    S = secoes(d)
    E = S["extremos"]
    res = {(x["candidato"], x["limiar"]): x for x in E["resumo"]}
    medias = (
        (res.get(("lula", 90)) or {}).get("pct_das_secoes"),
        (res.get(("flavio", 90)) or {}).get("pct_das_secoes"),
    )
    tips = Tips()
    tam = E["tamanho"]["linhas"]
    tipo = E["tipo_local"]["linhas"]
    mod = E["modelo_urna"]
    n = max(len(tam), len(tipo), len(mod))
    w, h = 1100, 52 + 46 * n + 64
    out = [
        svg_abre(
            w,
            h,
            "Parcela de seções com 90% ou mais por tamanho, tipo de local e modelo de urna",
            "Em cada grupo, a parte das seções em que Lula ou Flávio passou de 90% dos válidos; linhas tracejadas, a média do país.",
        ),
        f'<g data-alt-show="tamanho">{_grupo_barras(tam, "faixa", "lula_90_pct", "flavio_90_pct", tips, "Seções com votantes na faixa", medias)}</g>',
        f'<g data-alt-show="tipo" display="none">{_grupo_barras(tipo, "tipo", "lula_90_pct_do_tipo", "flavio_90_pct_do_tipo", tips, "Local do tipo", medias)}</g>',
        f'<g data-alt-show="modelo" display="none">{_grupo_barras(mod, "modelo", "lula_90_pct_do_modelo", "flavio_90_pct_do_modelo", tips, "Urna", medias)}</g>',
        "</svg>",
    ]
    ctl = botoes(
        [
            ("tamanho", "Por votantes"),
            ("tipo", "Por tipo de local"),
            ("modelo", "Por modelo de urna"),
        ],
        "tamanho",
        "Agrupar",
    )
    legenda = (
        "Parte das seções de cada grupo em que Lula (vermelho) ou Flávio (azul) teve 90% dos válidos ou mais; a linha "
        "tracejada é a parte no total. Seção pequena produz percentual extremo com poucos eleitores. O tipo de local é "
        f"inferido pelo nome ({escape(E['tipo_local'].get('aviso', ''))}). {nota_cobertura(S)} Fonte: secoes.json."
    )
    leg = legenda_html(
        [("Lula com 90% ou mais", LULA), ("Flávio com 90% ou mais", FLAVIO)]
    )
    return figura_html(
        "secoes_tamanho_tipo",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=820,
        apos=leg,
    )


# ------------------------------------------------------------------ 4 clusters_secoes


def _elipse(
    pts: list[tuple[float, float]],
) -> tuple[float, float, float, float, float] | None:
    """Centro, semieixos (2 desvios) e ângulo em graus da nuvem de pontos."""
    if len(pts) < 3:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    disc = math.sqrt(max(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, max(tr / 2 - disc, 0)
    ang = (
        math.degrees(math.atan2(l1 - sxx, sxy))
        if sxy
        else (0.0 if sxx >= syy else 90.0)
    )
    return mx, my, 2 * math.sqrt(l1), 2 * math.sqrt(l2), ang


def _casa_menos_provaveis(C: dict, pontos: list[dict]) -> dict[int, dict]:
    """Índice do ponto top200 para o registro de `menos_provaveis`, quando dá para casar."""
    mp = C.get("menos_provaveis") or []
    top = [i for i, p in enumerate(pontos) if p.get("top200")]
    out: dict[int, dict] = {}
    if mp and "x" in mp[0] and "y" in mp[0]:
        pos = {(round(m["x"], 3), round(m["y"], 3)): m for m in mp}
        for i in top:
            m = pos.get((round(pontos[i]["x"], 3), round(pontos[i]["y"], 3)))
            if m:
                out[i] = m
        return out
    for i, m in zip(top, mp, strict=False):
        p = pontos[i]
        if p.get("uf") == m.get("uf") and p.get("cluster") == m.get("cluster"):
            out[i] = m
    return out


def _painel_clusters(S: dict) -> str:
    C = S["clusters"]
    ma = C["mais_anomalo"]["id"]
    itens = []
    for c in C["componentes"]:
        cv, ce = c["centro_pct_validos"], c["centro_pct_eleitorado"]
        ufs = ", ".join(
            f"{u['uf']} {num(u['pct_do_cluster'], 1)}%" for u in c["ufs_top"][:3]
        )
        reg = c["regioes"][0] if c.get("regioes") else None
        marca = ' <em class="cl-anom">mais atípico</em>' if c["id"] == ma else ""
        itens.append(
            f'<li><span class="sw" style="background:{CLUSTER_COR[c["id"] % 4]}"></span>'
            f"<b>Grupo {c['id'] + 1}: {escape(c['rotulo'])}</b>{marca}"
            f"<span>{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%)</span>"
            f"<span>Centro: Lula {num(cv['lula'], 1)}%, Flávio {num(cv['flavio'], 1)}%, outros {num(cv['outros'], 1)}% dos válidos</span>"
            f"<span>Abstenção média {num(ce['abstencao'], 1)}% dos aptos</span>"
            f"<span>UFs: {escape(ufs)}</span>"
            + (
                f"<span>Região dominante: {escape(reg['regiao'])} ({num(reg['pct_do_cluster'], 1)}%)</span>"
                if reg
                else ""
            )
            + "</li>"
        )
    return f'<div class="cl-painel"><h4>Os quatro grupos</h4><ol>{"".join(itens)}</ol></div>'


def _tabela_anomalo(S: dict) -> str:
    C = S["clusters"]
    am = C["mais_anomalo"]["amostras"]
    linhas = [
        [
            escape(a["uf"]),
            escape(nome_bonito(a["municipio"])),
            str(a["zona"]),
            str(a["secao"]),
            escape(nome_bonito(a.get("local") or "")),
            num(a.get("lula_pct"), 1),
            num(a.get("flavio_pct"), 1),
            inteiro(a.get("aptos")),
            inteiro(a.get("comparecimento")),
            escape(a.get("modelo_urna") or "s/d"),
            escape(a.get("explicacao") or ""),
        ]
        for a in am
    ]
    return tabela(
        [
            "UF",
            "Município",
            "Zona",
            "Seção",
            "Local",
            "Lula %",
            "Flávio %",
            "Aptos",
            "Votantes",
            "Modelo",
            "Explicação (regra declarada)",
        ],
        linhas,
        f"Amostras do grupo mais atípico ({escape(rotulo_cluster(S, C['mais_anomalo']['id']))}): "
        f"{escape(C['mais_anomalo'].get('criterio', '').rstrip('.'))}. Percentuais dos válidos.",
    )


@registra("clusters_secoes")
def clusters_secoes(d, **_op) -> str:
    S = secoes(d)
    C = S["clusters"]
    P = C["pca"]
    cols = P["colunas"]
    pontos = [dict(zip(cols, p, strict=False)) for p in P["pontos"]]
    if not pontos:
        raise ValueError("clusters.pca.pontos vazio")
    w, h = 780, 620
    x0, x1, y0, y1 = 70, 760, 24, 560
    xs = [p["x"] for p in pontos]
    ys = [p["y"] for p in pontos]
    pad_x = (max(xs) - min(xs)) * 0.04 or 1
    pad_y = (max(ys) - min(ys)) * 0.04 or 1
    lox, hix = min(xs) - pad_x, max(xs) + pad_x
    loy, hiy = min(ys) - pad_y, max(ys) + pad_y
    X = escala(lox, hix, x0, x1)
    Y = escala(loy, hiy, y1, y0)
    ve = P.get("variancia_explicada") or [None, None]
    out = [
        svg_abre(
            w,
            h,
            "Quatro grupos de seções na projeção em dois componentes principais",
            "Cada ponto é uma seção da amostra; cor pelo grupo da mistura gaussiana; as 200 seções menos prováveis "
            "têm contorno preto; o grupo mais atípico tem a nuvem marcada em dourado.",
            ' data-near="1"',
        )
    ]
    for v in ticks(lox, hix, 6):
        out.append(ln(X(v), y0, X(v), y1, GRADE, 0.8))
        out.append(t(X(v), y1 + 20, num(v, 1), 13, MUTED, "middle", mono=True))
    for v in ticks(loy, hiy, 6):
        out.append(ln(x0, Y(v), x1, Y(v), GRADE, 0.8))
        out.append(t(x0 - 8, Y(v) + 5, num(v, 1), 13, MUTED, "end", mono=True))
    out.append(
        t(
            (x0 + x1) / 2,
            h - 22,
            f"Componente principal 1 ({num(100 * ve[0], 1) if ve[0] is not None else 's/d'}% da variância)",
            14,
            INK,
            "middle",
            "600",
        )
    )
    yy = (y0 + y1) / 2
    out.append(
        t(
            20,
            yy,
            f"Componente 2 ({num(100 * ve[1], 1) if ve[1] is not None else 's/d'}%)",
            14,
            INK,
            "middle",
            "600",
            extra=f' transform="rotate(-90 20 {yy:.0f})"',
        )
    )
    ma = C["mais_anomalo"]["id"]
    nuvem = [(X(p["x"]), Y(p["y"])) for p in pontos if p["cluster"] == ma]
    el = _elipse(nuvem)
    if el:
        cx, cy, rx, ry, ang = el
        out.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{max(ry, 6):.1f}" '
            f'transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" fill="#f2e3b8" fill-opacity="0.45" '
            f'stroke="{OURO}" stroke-width="2.5" stroke-dasharray="7 5"/>'
        )
    grupos: dict[tuple[int, str], list[str]] = {}
    casados = _casa_menos_provaveis(C, pontos)
    linhas, xy, top = [], [], []
    for i, p in enumerate(pontos):
        x, y = X(p["x"]), Y(p["y"])
        k = int(p["cluster"])
        reg = regiao_da_uf(p.get("uf"))
        if p.get("top200"):
            top.append((x, y, k, reg))
            raio = 4.5
        else:
            grupos.setdefault((k, reg), []).append(f"M{x:.0f} {y:.0f}h0")
            raio = 2
        linha = [f"Grupo {k + 1} · {p.get('uf') or 's/d'}"]
        if p.get("top200"):
            m = casados.get(i)
            linha.append("entre as 200 menos prováveis")
            if m:
                linha += [
                    nome_bonito(m["municipio"]),
                    f"{m['zona']} · {m['secao']}",
                    nome_bonito(m.get("local") or ""),
                    f"{num(m.get('lula_pct'), 1)} · {num(m.get('flavio_pct'), 1)}",
                    m.get("explicacao") or "",
                    num(m.get("loglik"), 1),
                ]
        linhas.append(linha)
        xy.append([round(x), round(y), raio])
    for (k, reg), segs in sorted(grupos.items()):
        out.append(
            f'<path d="{"".join(segs)}" stroke="{CLUSTER_COR[k % 4]}" data-as="regiao>{COR_REGIAO.get(reg, MUTED)}" '
            'stroke-width="4" stroke-linecap="round" stroke-opacity="0.5" fill="none"/>'
        )
    for x, y, k, reg in top:
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{CLUSTER_COR[k % 4]}" '
            f'data-af="regiao>{COR_REGIAO.get(reg, MUTED)}" stroke="{INK}" stroke-width="1.3"/>'
        )
    for i, c in enumerate(P["centros"]):
        cx, cy = X(c["x"]), Y(c["y"])
        k = int(c["cluster"])
        out.append(
            f'<g pointer-events="none">{ln(cx - 8, cy, cx + 8, cy, INK, 3)}{ln(cx, cy - 8, cx, cy + 8, INK, 3)}'
            + (
                chip(cx - 10, cy - 10 - 22 * (i % 2), f"Grupo {k + 1}", 13, "end")
                if cx > x1 - 120
                else chip(cx + 10, cy - 10 - 22 * (i % 2), f"Grupo {k + 1}", 13)
            )
            + "</g>"
        )
    if el:
        out.append(
            f'<g pointer-events="none">{chip(el[0] - el[2] * 0.3, el[1] + max(el[3], 6) + 22, "grupo mais atípico", 13)}</g>'
        )
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        [
            "Seção",
            "Marca",
            "Município",
            "Zona · seção",
            "Local",
            "Lula · Flávio, % dos válidos",
            "Explicação",
            "Log-verossimilhança",
        ],
        linhas,
        xy=xy,
        nota="rótulo de cada grupo no painel ao lado",
    )
    ctl = botoes(
        [("cluster", "Cor pelo grupo"), ("regiao", "Cor pela região")], "cluster", "Cor"
    )
    leg_cl = (
        '<div data-alt-show="cluster">'
        + legenda_html(
            [
                (rotulo_cluster(S, c["id"]), CLUSTER_COR[c["id"] % 4])
                for c in C["componentes"]
            ],
            "Grupo da mistura gaussiana",
        )
        + "</div>"
    )
    regs = [*REGIOES, "Exterior"]
    leg_rg = (
        '<div data-alt-show="regiao" hidden>'
        + legenda_html([(rg, COR_REGIAO[rg]) for rg in regs], "Região da seção")
        + "</div>"
    )
    aj = C["ajuste"]
    legenda = (
        f"Projeção das {inteiro(P.get('n_pontos', len(pontos)))} seções da amostra nos dois primeiros componentes "
        f"principais das {len(C['features'])} variáveis ({escape(C['transformacao'])} sobre {escape(C['base'])}). "
        f"Mistura gaussiana com k = {C['k']}, covariância completa, {aj.get('n_init')} inicializações. Contorno preto: as 200 "
        "seções menos prováveis sob o modelo. O botão troca a cor do grupo pela região, para ver se grupo é geografia. "
        f"{nota_cobertura(S)} Fonte: secoes.json."
    )
    apos = _painel_clusters(S) + leg_cl + leg_rg + _tabela_anomalo(S)
    return figura_html(
        "clusters_secoes",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        minw=640,
        dim=False,
        apos=apos,
    )


__all__ = [
    "CLUSTER_COR",
    "OURO",
    "UF_REGIAO",
    "local_ref",
    "nota_cobertura",
    "regiao_da_uf",
    "rotulo_cluster",
    "secoes",
    "uf_do_ponto",
]
