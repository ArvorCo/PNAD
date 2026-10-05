"""Figuras do capítulo 7: o voto dos aliados ao Senado contra o voto de Flávio.

Dados em `analysis/apuracao_2026/dados/senado_x_flavio.json`
(`scripts/apuracao-2026-senado-x-flavio.py`). Três figuras:

- `senado_pl_x_flavio_uf`: soma do PL e do bloco aliado contra Flávio, por UF;
- `senado_vao_candidatos`: a melhor candidatura do bloco em cada UF contra Flávio,
  nas duas réguas (base de votos e eleitores alcançados);
- `senado_carregadores_mapa`: índice dos carregadores por município nas quatro
  maiores UFs com eleito de direita do bloco, um botão por candidatura.
"""

from __future__ import annotations

import math
from html import escape

from .pagina_comum import NOME_UF, inteiro, num, tabela
from .pagina_fig_base import (
    FLAVIO,
    GRADE,
    INK,
    MUTED,
    PAPER,
    Tips,
    W,
    area,
    botoes,
    campo_nome,
    cor_campo,
    dado,
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
    registra,
    svg_abre,
    t,
    ticks,
)
from .pagina_fig_mapas import caminho
from .pagina_mapas import _aneis, _geo_municipal

COR_PL = FLAVIO
COR_BLOCO = "#8fb0dc"
CORES_INDICE = [
    "#8c510a",
    "#c2873a",
    "#e6cf96",
    "#d9d2c0",
    "#93cfc4",
    "#3e9a8f",
    "#01665e",
]
ROT_INDICE = [
    "abaixo de 70",
    "70 a 85",
    "85 a 95",
    "95 a 105",
    "105 a 115",
    "115 a 130",
    "130 ou mais",
]
SEM_INDICE = "#9d9a92"
N_LISTA_FIG = 10


def _limites(
    vals: list[float], passo: int = 10, folga: float = 8
) -> tuple[float, float]:
    """Domínio redondo com folga para o rótulo do valor na ponta da barra."""
    mn, mx = min(*vals, 0), max(*vals, 0)
    lo = math.floor((mn - folga) / passo) * passo if mn < 0 else 0
    hi = math.ceil((mx + folga) / passo) * passo if mx > 0 else 0
    return lo, hi


def _rot_pp(v: float) -> str:
    return pp(v, 1)[:-3]


def _eixo(X, lo: float, hi: float, topo: float, base: float, n: int = 8) -> str:
    out = []
    for v in ticks(lo, hi, n):
        out.append(ln(X(v), topo - 6, X(v), base, GRADE))
        out.append(
            t(
                X(v),
                base + 20,
                f"{'+' if v > 0 else '−' if v < 0 else ''}{num(abs(v), 0)}",
                13,
                MUTED,
                "middle",
                mono=True,
            )
        )
    out.append(ln(X(0), topo - 6, X(0), base, INK, 1.4))
    return "".join(out)


# ------------------------------------------------------------------ blocos por UF


def _ficha_bloco(nome: str, b: dict) -> list[tuple[str, str]]:
    if not b["n_candidatos"]:
        return [(nome, "sem candidatura")]
    nomes = ", ".join(
        nome_bonito(c["nome"]) + (" (eleito)" if c.get("eleito") else "")
        for c in b.get("candidatos", [])
    )
    linhas = [
        (
            nome,
            f"{b['n_candidatos']} nome(s): {pct(b['pct'])} da base, {pp(b['div_pp'])}",
        ),
        (
            f"{nome}, votos por voto de Flávio",
            f"{num(b['votos_por_voto_flavio'], 2)} ({inteiro(b['votos'])} votos)",
        ),
    ]
    if nomes:
        linhas.append((f"{nome}, nomes", nomes))
    return linhas


@registra("senado_pl_x_flavio_uf")
def senado_pl_x_flavio_uf(d, **_op) -> str:
    S = dado(d, "senado_x_flavio")
    n = S["nacional"]
    ufs = sorted(S["ufs"], key=lambda u: -(u["aliados"]["div_pp"] or 0))
    linhas = [("BR", n), *((u["uf"], u) for u in ufs)]
    vals = [
        x[k]["div_pp"]
        for _, x in linhas
        for k in ("pl", "aliados")
        if x[k]["div_pp"] is not None
    ]
    lo, hi = _limites(vals)
    esq, topo, passo, sep = 200, 74, 34, 16
    base = topo + passo * len(linhas) + sep
    h = base + 78
    X = escala(lo, hi, esq, W - 190)
    x0 = X(0)
    out = [
        svg_abre(
            W,
            h,
            "Senado contra Flávio: soma do PL e do bloco aliado, por UF",
            "Duas barras por UF, em pontos: parcela da soma na base de votos do Senado menos a parcela de "
            "Flávio nos válidos de presidente; barra cheia, PL; barra clara com contorno, direita e "
            "centro-direita fora dos alinhados a Lula.",
        ),
        t(x0 + 8, 30, "Senado acima de Flávio →", 13, MUTED),
        t(x0 - 8, 30, "← Senado abaixo de Flávio", 13, MUTED, "end"),
        t(W - 176, 56, "nomes: PL · bloco", 13, MUTED),
        _eixo(X, lo, hi, topo, base),
    ]
    tips = Tips()
    y = topo
    for i, (uf, x) in enumerate(linhas):
        if i == 1:
            out.append(ln(16, y + 2, W - 16, y + 2, MUTED, 0.8))
            y += sep
        fl = x["flavio"]
        rot = "Brasil, 27 UFs" if uf == "BR" else NOME_UF[uf]
        corpo = [
            t(esq - 12, y + 22, rot, 14, INK, "end", "700" if uf == "BR" else None)
        ]
        for j, (chave, cor, contorno) in enumerate(
            (("pl", COR_PL, ""), ("aliados", COR_BLOCO, f' stroke="{COR_PL}"'))
        ):
            b = x[chave]
            yy = y + 5 + j * 13
            v = b["div_pp"]
            if v is None:
                corpo.append(t(x0 + 6, yy + 10, "sem nome do PL", 13, MUTED))
                continue
            xa, xb = sorted((x0, X(v)))
            corpo.append(r(xa, yy, xb - xa, 11, cor, contorno + ' stroke-width="1"'))
            corpo.append(
                t(
                    X(v) + (6 if v >= 0 else -6),
                    yy + 10,
                    _rot_pp(v),
                    13,
                    INK,
                    "start" if v >= 0 else "end",
                    mono=True,
                )
            )
        corpo.append(
            t(
                W - 176,
                y + 22,
                f"{x['pl']['n_candidatos']} · {x['aliados']['n_candidatos']}",
                13,
                INK,
                mono=True,
            )
        )
        k = tips.add(
            ficha(
                rot,
                "mesma urna, cargos diferentes",
                [
                    (
                        "Flávio, % dos válidos",
                        f"{pct(fl['pct'])} · {inteiro(fl['votos'])} votos",
                    ),
                    *_ficha_bloco("PL", x["pl"]),
                    *_ficha_bloco("Bloco aliado", x["aliados"]),
                ],
                "Cada eleitor dá dois votos para o Senado: um nome sozinho não passa de metade da base.",
            )
        )
        out.append(hit(area(0, y, W, passo) + "".join(corpo), k))
        y += passo
    out.append(
        legenda([("PL", COR_PL)], esq, base + 52, 13)
        + r(esq + 90, base + 41, 13, 13, COR_BLOCO, f' stroke="{COR_PL}"')
        + t(esq + 108, base + 52, "bloco aliado: direita e centro-direita", 13)
    )
    out.append("</svg>")
    pl, al = n["pl"], n["aliados"]
    legenda_ = (
        f"Parcela da soma na base de votos do Senado menos a parcela de Flávio nos válidos de presidente, na mesma UF. "
        f"No país (eleitor residente), PL {pct(pl['pct'])} e bloco aliado {pct(al['pct'])} contra Flávio {pct(n['flavio']['pct'])}. "
        "Cada eleitor dá dois votos: com um só nome, a soma do partido não passa de metade da base, por isso a coluna "
        "à direita mostra quantos nomes cada um lançou. Bloco aliado: direita e centro-direita, sem as candidaturas "
        "aliadas de Lula listadas no texto. Fonte: senado_x_flavio.json."
    )
    return figura_html("senado_pl_x_flavio_uf", "".join(out), legenda_, tips, minw=820)


# ------------------------------------------------------------------ melhor candidatura


def _quantas(n: int, total: int) -> str:
    if n == 0:
        return "nenhuma candidatura passa"
    if n == 1:
        return f"uma das {total} candidaturas passa"
    return f"{n} das {total} candidaturas passam"


REGUAS = {
    "base": ("vao_pp", "Parcela da base de votos"),
    "votantes": ("vao_votantes_pp", "Eleitores alcançados"),
}


@registra("senado_vao_candidatos")
def senado_vao_candidatos(d, **_op) -> str:
    S = dado(d, "senado_x_flavio")
    ufs = [u for u in S["ufs"] if u["melhor"]]
    esq, topo, passo = 380, 64, 28
    base = topo + passo * len(ufs)
    h = base + 70
    out = [
        svg_abre(
            W,
            h,
            "A melhor candidatura do bloco aliado ao Senado contra Flávio, por UF",
            "Barras em pontos; positivo, a candidatura ao Senado teve parcela maior que Flávio na mesma UF. "
            "Duas réguas: parcela da base de votos e fração dos votantes alcançados.",
        ),
    ]
    tips = Tips()
    for chave, (campo_v, _) in REGUAS.items():
        lista = sorted(ufs, key=lambda u, c=campo_v: -u["melhor"][c])
        lo, hi = _limites([u["melhor"][campo_v] for u in lista])
        X = escala(lo, hi, esq, W - 60)
        x0 = X(0)
        g = [
            t(x0 + 8, 30, "Senado à frente de Flávio →", 13, MUTED),
            t(x0 - 8, 30, "← Flávio à frente", 13, MUTED, "end"),
            _eixo(X, lo, hi, topo, base),
        ]
        for i, u in enumerate(lista):
            m, fl = u["melhor"], u["flavio"]
            y = topo + i * passo
            v = m[campo_v]
            xa, xb = sorted((x0, X(v)))
            rot = f"{u['uf']} · {nome_bonito(m['nome'])} ({m['partido']})"
            corpo = (
                t(
                    esq - 12,
                    y + 19,
                    rot,
                    13.5,
                    INK,
                    "end",
                    "700" if m["eleito"] else None,
                )
                + r(xa, y + 5, xb - xa, passo - 10, cor_campo(m["campo"]))
                + t(
                    X(v) + (6 if v >= 0 else -6),
                    y + 19,
                    _rot_pp(v),
                    13,
                    INK,
                    "start" if v >= 0 else "end",
                    mono=True,
                )
            )
            k = tips.add(
                ficha(
                    f"{NOME_UF[u['uf']]}: {nome_bonito(m['nome'])}",
                    "teto endereçável, não transferência",
                    [
                        (
                            "Candidatura",
                            f"{m['partido']} · {campo_nome(m['campo'])} · "
                            + ("eleita" if m["eleito"] else "não eleita"),
                        ),
                        ("Base de votos do Senado", pct(m["pct"])),
                        ("Votantes alcançados", pct(m["pct_votantes"])),
                        ("Flávio, válidos", pct(fl["pct"])),
                        ("Flávio, votantes", pct(fl["pct_votantes"])),
                        ("Vão na base", pp(m["vao_pp"])),
                        ("Vão em votantes", pp(m["vao_votantes_pp"])),
                        (
                            "Votos",
                            f"{inteiro(m['votos'])} × Flávio {inteiro(fl['votos'])}",
                        ),
                    ],
                )
            )
            g.append(hit(area(0, y, W, passo) + corpo, k))
        mostra = "" if chave == "base" else ' display="none"'
        out.append(f'<g data-alt-show="{chave}"{mostra}>{"".join(g)}</g>')
    out.append(
        legenda(
            [(campo_nome(c), cor_campo(c)) for c in ("direita", "centro-direita")],
            esq,
            base + 52,
            13,
        )
        + t(esq + 330, base + 52, "nome em negrito: eleito em 2026", 13, MUTED)
    )
    out.append("</svg>")
    ctl = botoes([(k, v[1]) for k, v in REGUAS.items()], "base", "Régua")
    nac = S["nacional"]["melhor"]
    legenda_ = (
        "A candidatura mais votada do bloco aliado em cada UF, eleita ou não, menos Flávio na mesma UF. "
        "Parcela da base de votos: um nome sozinho não passa de metade da base, porque o eleitor dá dois votos; "
        f"nessa régua, {_quantas(nac['ufs_acima_na_base'], nac['ufs'])} Flávio. Eleitores alcançados: votos "
        "da candidatura sobre os votantes do Senado contra votos de Flávio sobre os votantes de presidente; nessa "
        f"régua, {nac['ufs_acima_em_votantes']} passam. Cor: campo. Teto endereçável, não transferência. "
        "Fonte: senado_x_flavio.json."
    )
    return figura_html(
        "senado_vao_candidatos", "".join(out), legenda_, tips, controles=ctl, minw=820
    )


# ------------------------------------------------------------------ mapa dos carregadores


def cor_indice(v: float | None) -> str:
    if v is None:
        return SEM_INDICE
    cortes = (70, 85, 95, 105, 115, 130)
    return CORES_INDICE[sum(v >= c for c in cortes)]


def _projecao(feats: list[dict], w: float, h: float):
    lons = [c[0] for f in feats for a in _aneis(f["geometry"]) for c in a]
    lats = [c[1] for f in feats for a in _aneis(f["geometry"]) for c in a]
    cosl = math.cos(math.radians((min(lats) + max(lats)) / 2))
    sx, sy = (max(lons) - min(lons)) * cosl, max(lats) - min(lats)
    pad, topo, base = 10, 8, 12
    esc = min((w - 2 * pad) / sx, (h - topo - base) / sy)
    ox = pad + ((w - 2 * pad) - sx * esc) / 2
    oy = topo + ((h - topo - base) - sy * esc) / 2
    lon0, lat1 = min(lons), max(lats)

    def proj(lon, lat):
        return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

    return proj


def _curto(nome: str) -> str:
    """Nome de urna curto para a ficha: inteiro até 14 letras, senão o último nome."""
    bonito = nome_bonito(nome)
    return bonito if len(bonito) <= 14 else bonito.split()[-1]


def _lista_html(c: dict, uf: str, k: str, mostra: bool, minimo: int) -> str:
    """Resumo e os municípios dos dois extremos de uma candidatura, em HTML."""
    maiores, menores = c["maiores"][:N_LISTA_FIG], c["menores"][:N_LISTA_FIG]
    linhas = []
    for i in range(max(len(maiores), len(menores))):
        a = maiores[i] if i < len(maiores) else None
        b = menores[i] if i < len(menores) else None
        linhas.append(
            [
                f"{i + 1}º",
                escape(nome_bonito(a["nome"])) if a else "",
                num(a["indice"], 1) if a else "",
                escape(nome_bonito(b["nome"])) if b else "",
                num(b["indice"], 1) if b else "",
            ]
        )
    cab = (
        f"<p><b>{escape(nome_bonito(c['nome']))} ({escape(c['partido'])})</b>: "
        f"{num(c['pct_uf'], 2)}% da base de votos do Senado em {escape(NOME_UF[uf])}; Flávio, "
        f"{num(c['flavio_pct_uf'], 2)}% dos válidos. Índice acima de 100 em {inteiro(c['municipios_acima_de_100'])} "
        f"de {inteiro(c['municipios'])} municípios. Listas: municípios com {inteiro(minimo)} votantes ou mais.</p>"
    )
    tab = tabela(
        ["", "Rende mais que Flávio", "Índice", "Rende menos", "Índice"], linhas
    )
    oculto = "" if mostra else " hidden"
    return f'<div class="car-lista" data-alt-show="{k}"{oculto}>{cab}{tab}</div>'


@registra("senado_carregadores_mapa")
def senado_carregadores_mapa(d, **_op) -> str:
    S = dado(d, "senado_x_flavio")
    M = S["mapa"]
    C = {(c["uf"], c["sqcand"]): c for c in S["carregadores"]["candidatos"]}
    minimo = S["carregadores"]["min_votantes"]
    w, h = 640, 600
    tips = Tips()
    linhas_tip, grupos, abas, listas = [], [], [], []
    primeiro = None
    for uf in M["ufs"]:
        P = M["por_uf"][uf]
        cands = P["candidatos"]
        chaves = [f"{uf}{j}" for j in range(len(cands))]
        primeiro = primeiro or chaves[0]
        geo = _geo_municipal(uf)
        if geo is None:
            raise KeyError(f"apuracao/public/geo/mun/{uf}.geojson")
        proj = _projecao(geo["features"], w, h)
        col = P["colunas"]
        por_ibge = {str(x[0]): dict(zip(col, x, strict=True)) for x in P["linhas"]}
        curtos = [_curto(c["nome"]) + " " for c in cands] if len(cands) > 1 else [""]
        partes = []
        for f in geo["features"]:
            cod = str(f.get("properties", {}).get("codarea", ""))
            dd = caminho(_aneis(f["geometry"]), proj, 2.0)
            if not dd:
                continue
            m = por_ibge.get(cod)
            if m is None:
                partes.append(f'<path d="{dd}" fill="{SEM_INDICE}"/>')
                continue
            inds = [
                m[f"indice_{j}"] if m["completo"] else None for j in range(len(cands))
            ]
            cores = [cor_indice(v) for v in inds]
            i = len(linhas_tip)
            linhas_tip.append(
                [
                    f"{nome_bonito(m['nome'])} ({uf})",
                    " · ".join(
                        f"{nm}{num(v, 1) if v is not None else 's/d'}"
                        for nm, v in zip(curtos, inds, strict=True)
                    ),
                    " · ".join(
                        f"{nm}{num(m[f'pct_cand_{j}'], 1)}"
                        for j, nm in enumerate(curtos)
                    ),
                    num(m["pct_flavio"], 1),
                    inteiro(m["votantes"]),
                ]
            )
            af = ""
            if len(cands) > 1:
                pares = "|".join(f"{k}>{c}" for k, c in zip(chaves, cores, strict=True))
                af = f' data-af="{pares}"'
            partes.append(
                f'<path class="hit" data-k="r{i}" d="{dd}" fill="{cores[0]}"{af}/>'
            )
        mostra = "" if uf == M["ufs"][0] else ' display="none"'
        grupos.append(
            f'<g data-alt-show="{" ".join(chaves)}" stroke="{PAPER}" stroke-width="0.4"{mostra}>'
            f'{"".join(partes)}</g>'
        )
        for k, c in zip(chaves, cands, strict=True):
            abas.append((k, f"{uf} · {nome_bonito(c['nome'])}"))
            listas.append(
                _lista_html(C[(uf, c["sqcand"])], uf, k, k == primeiro, minimo)
            )
    tips.tabela(
        [
            "Município",
            "Índice",
            "% da candidatura no município",
            "Flávio, % dos válidos no município",
            "Votantes",
        ],
        linhas_tip,
        nota="Índice 100: a candidatura rende ali o mesmo que Flávio, cada um contra a própria média estadual",
    )
    svg = (
        svg_abre(
            w,
            h,
            "Índice dos carregadores: senadores eleitos do bloco contra Flávio, por município",
            "Cada município pelo índice da candidatura escolhida: 100 vezes a parcela no município sobre a parcela "
            "no estado, dividido pela mesma razão de Flávio. Verde, a candidatura rende acima de Flávio ali; "
            "marrom, abaixo.",
        )
        + "".join(grupos)
        + "</svg>"
    )
    ctl = botoes(abas, primeiro, "Candidatura", "tab")
    leg = legenda_html(
        [*zip(ROT_INDICE, CORES_INDICE, strict=True), ("sem comparação", SEM_INDICE)],
        "Índice do carregador (100 = rende como Flávio)",
    )
    legenda_ = (
        "Índice = 100 × (parcela da candidatura no município ÷ parcela no estado) ÷ (parcela de Flávio no município ÷ "
        "parcela no estado), cada uma sobre a base do próprio cargo. Acima de 100, a candidatura rende ali mais do "
        "que Flávio rende, relativamente; índice alto pode ser Flávio fraco no município, não só senador forte. "
        f"Quatro maiores eleitorados com eleito de direita do bloco: {', '.join(M['ufs'])}. Cinza: arquivo de "
        "presidente congelado incompleto no município. Fonte: senado_x_flavio.json e malha do IBGE."
    )
    return figura_html(
        "senado_carregadores_mapa",
        svg,
        legenda_,
        tips,
        controles=ctl,
        modo="fit",
        apos=leg + "".join(listas),
    )
