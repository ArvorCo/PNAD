"""Figuras do capítulo 13 (onde colocar fiscal), parte 2: o mapa navegável do Brasil e
os mapas municipais das oito UFs com mais locais sinalizados.

`fiscais_mapa_navegavel`: malha das UFs e um ponto por local (`mapa.pontos`), cor pelo
nível do sinal ou, na outra aba, pelo nível de risco; raio pelo número de seções
sinalizadas; pan, zoom, malha municipal sob demanda, busca e lista de UFs ficam em
`pagina_fig_fiscais_nav` (JavaScript próprio, sem rede). `fiscais_mapa_uf`: uma aba
por UF, malha municipal do IBGE e os pontos, com ficha por local.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from html import escape

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro
from .pagina_fig_base import (
    INK,
    LIMA,
    MUTED,
    PAPER,
    Tips,
    botoes,
    figura_html,
    legenda_html,
    nome_bonito,
    registra,
    svg_abre,
    t,
)
from .pagina_fig_fiscais import (
    COR_NIVEL,
    COR_RISCO,
    NIVEIS,
    ROT_NIVEL,
    ROT_RISCO,
    criterios_txt,
    fiscais,
    nivel_txt,
    risco_nivel,
    risco_txt,
    tem_risco,
)
from .pagina_fig_fiscais_nav import blocos_malha
from .pagina_fig_mapas import MH, MW, caminho, paths_uf
from .pagina_fig_secoes import uf_do_ponto
from .pagina_mapas import _aneis, _geo_municipal


def raio(n: int) -> float:
    return round(min(9.0, 2.2 + 1.3 * math.sqrt(max(n, 1) - 1)) * 2) / 2


def _pontos(F: dict) -> list[dict]:
    """Um dicionário por ponto do mapa, com o local de `por_local` ao lado."""
    M = F["mapa"]
    cols = M["colunas"]
    loc = F["por_local"]
    out = []
    for linha in M["pontos"]:
        p = dict(zip(cols, linha, strict=False))
        if p.get("lat") is None or p.get("lon") is None:
            continue
        i = p.get("local")
        x = loc[i] if isinstance(i, int) and 0 <= i < len(loc) else {}
        if x.get("uf") == "ZZ":
            continue  # exterior: fora do mapa do Brasil, fica na lista de locais
        p["l"] = x
        out.append(p)
    return out


def risco_ponto(p: dict) -> str:
    """Nível de risco do local: a coluna `risco` do mapa (1.1) ou o bloco do local."""
    return p.get("risco") or risco_nivel(p["l"])


def _linha_ficha(p: dict) -> list:
    x = p["l"]
    return [
        nome_bonito(x.get("local") or "local de votação"),
        f"{nome_bonito(x.get('municipio', ''))} ({x.get('uf', '')}), zona {x.get('zona', '')}",
        nome_bonito(x.get("endereco") or ""),
        nome_bonito(x.get("bairro") or ""),
        f"{inteiro(p.get('n_secoes'))} de {inteiro(x.get('secoes_local'))}"
        + (
            f" ({', '.join(str(s) for s in x.get('lista_secoes', [])[:12])})"
            if x.get("lista_secoes")
            else ""
        ),
        criterios_txt(x.get("criterios")),
        nivel_txt(p.get("nivel")),
        inteiro(p.get("pontuacao")),
        risco_txt(x) if isinstance(x.get("risco"), dict) else "",
    ]


CAMPOS_FICHA = [
    "Local",
    "Município",
    "Endereço",
    "Bairro",
    "Seções sinalizadas",
    "Critérios",
    "Nível",
    "Pontuação somada",
    "Risco do território",
]


def _lotes(pts, proj_xy, chave) -> dict:
    lotes: dict = {}
    for p, (x, y) in zip(pts, proj_xy, strict=True):
        lotes.setdefault(chave(p), []).append(f"M{x:.1f} {y:.1f}h0")
    return lotes


@registra("fiscais_mapa_navegavel")
def fiscais_mapa_navegavel(d, **_op) -> str:
    F = fiscais(d)
    pts = sorted(_pontos(F), key=lambda p: (NIVEIS.index(p["nivel"]), -p["n_secoes"]))
    pts.reverse()  # alta por cima
    proj, _ = VM._proj(MW, MH, 10.0)
    xy = [proj(p["lon"], p["lat"]) for p in pts]
    risco = tem_risco(F)
    out = [
        svg_abre(
            MW,
            MH,
            "Locais de votação com seção sinalizada, no mapa do Brasil",
            "Um ponto por local de votação com ao menos uma seção sinalizada; cor pelo nível do sinal, raio pelo "
            "número de seções sinalizadas. Aproxime para ver a malha e os nomes dos municípios.",
            ' data-near="1"',
        ).replace('class="fig"', 'class="fig fz-svg"', 1)
    ]
    for uf, g in sorted(paths_uf().items()):
        out.append(
            f'<path class="fz-uf" d="{g["d"]}" fill="#ebe5d6" stroke="#9f9884" stroke-width="0.9" '
            f'vector-effect="non-scaling-stroke"><title>{NOME_UF.get(uf, uf)}</title></path>'
        )
    out.append('<g class="fz-mun-g" display="none" transform="scale(0.1)"></g>')
    grupos = [risco_ponto(p) for p in pts]
    for aba, chave, cor in (
        ("sinal", lambda p: p["nivel"], COR_NIVEL),
        ("risco", lambda p: risco_ponto(p), COR_RISCO),
    ):
        if aba == "risco" and not risco:
            continue
        oculto = "" if aba == "sinal" else ' display="none"'
        out.append(f'<g data-alt-show="{aba}"{oculto}>')
        lotes = _lotes(
            pts, xy, lambda p, c=chave: (c(p), risco_ponto(p), raio(p["n_secoes"]))
        )
        ordem = (
            sorted(lotes, key=lambda k: (-NIVEIS.index(k[0]), -k[2]))
            if aba == "sinal"
            else sorted(
                lotes,
                key=lambda k: (-(["alto", "medio", "baixo", ""].index(k[0])), -k[2]),
            )
        )
        for k in ordem:
            val, g_risco, rr = k
            out.append(
                f'<path data-g="{g_risco}" d="{"".join(lotes[k])}" stroke="{cor.get(val, "#d8d4c8")}" '
                f'stroke-width="{2 * rr + 1.6:.1f}" stroke-linecap="round" fill="none" '
                'vector-effect="non-scaling-stroke" stroke-opacity="0.9"/>'
            )
        out.append("</g>")
    out.append('<g class="fz-rot"></g>')
    out.append(
        f'<circle class="fz-sel" cx="0" cy="0" r="10" fill="none" stroke="{INK}" stroke-width="2.5" '
        'vector-effect="non-scaling-stroke" display="none" pointer-events="none"/>'
    )
    out.append(
        f'<circle class="near-halo" cx="0" cy="0" r="8" fill="none" stroke="{LIMA}" stroke-width="3" '
        'vector-effect="non-scaling-stroke" display="none"/>'
    )
    out.append("</svg>")
    tips = Tips()
    tips.tabela(
        CAMPOS_FICHA,
        [_linha_ficha(p) for p in pts],
        sub=1,
        nota="clique ou toque para abrir o painel com os links do mapa externo",
        xy=[
            [round(x, 1), round(y, 1), raio(p["n_secoes"])]
            for p, (x, y) in zip(pts, xy, strict=True)
        ],
        grupos=grupos,
    )
    # dados do painel e da busca: coordenada, links e o índice da ficha
    # dados do painel e da busca: coordenada no viewBox e lat/lon para os links;
    # nome, endereço e o resto saem das fichas (`_rows`), sem cópia
    dados = {
        "pontos": [
            [round(x, 1), round(y, 1), p["lat"], p["lon"]]
            for p, (x, y) in zip(pts, xy, strict=True)
        ]
    }
    bloco = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    # lista das UFs com contagem e a caixa (viewBox) para centrar
    por_uf = Counter()
    caixa: dict[str, list[float]] = {}
    for p, (x, y) in zip(pts, xy, strict=True):
        uf = p["l"].get("uf") or uf_do_ponto(p["lat"], p["lon"])
        por_uf[uf] += 1
        c = caixa.setdefault(uf, [x, y, x, y])
        caixa[uf] = [min(c[0], x), min(c[1], y), max(c[2], x), max(c[3], y)]
    lis = "".join(
        f'<li><button type="button" aria-pressed="false" data-caixa="{" ".join(f"{v:.1f}" for v in caixa[uf])}">'
        f"<span>{NOME_UF.get(uf, uf)}</span><b>{inteiro(n)}</b></button></li>"
        for uf, n in sorted(por_uf.items(), key=lambda kv: -kv[1])
    )
    ufs_mun = sorted(u for u in por_uf if u != "ZZ")
    nomes = {}
    TV = d.get("terceira_via") if isinstance(d, dict) else None
    if TV and "municipios" in TV:
        cols = TV["municipios"]["colunas"]
        i_ibge, i_nome = cols.index("ibge"), cols.index("nome")
        nomes = {
            str(m[i_ibge]): nome_bonito(m[i_nome]) for m in TV["municipios"]["linhas"]
        }
    for m in F.get("por_municipio", []):
        if m.get("ibge"):
            nomes.setdefault(str(m["ibge"]), nome_bonito(m["municipio"]))
    for x in F.get("por_local", []):
        if x.get("ibge"):
            nomes.setdefault(str(x["ibge"]), nome_bonito(x["municipio"]))
    controles = (
        '<div class="fz-ctl"><label class="fz-busca" style="display:contents">'
        '<span class="fig-ctl"><span class="rot">Buscar</span></span>'
        '<input type="search" placeholder="Município ou local de votação" aria-label="Buscar município ou local de votação">'
        '</label><button type="button" class="fz-btn" data-fz="buscar">Ir</button></div>'
        '<ul class="fz-res" aria-live="polite"></ul>'
        + botoes(
            [("sinal", "Cor pelo nível do sinal")]
            + ([("risco", "Cor pelo risco do território")] if risco else []),
            "sinal",
            "Pontos",
        )
        + (
            botoes(
                [("", "Todos")]
                + [
                    (k, f"Risco {ROT_RISCO[k].lower()}")
                    for k in ("alto", "medio", "baixo")
                ],
                "",
                "Filtro de risco",
                "filtro",
            )
            if risco
            else ""
        )
    )
    mapa = (
        '<div class="fz-quadro"><div class="fz-mapa">'
        + "".join(out)
        + '<div class="fz-zoom"><button type="button" class="fz-btn" data-fz="mais" aria-label="Aproximar">+</button>'
        '<button type="button" class="fz-btn" data-fz="menos" aria-label="Afastar">−</button>'
        '<button type="button" class="fz-btn" data-fz="brasil" aria-label="Ver o Brasil inteiro">BR</button></div>'
        '<span class="fz-escala" aria-hidden="true"></span></div>'
        f'<ul class="fz-ufs" aria-label="UFs com locais sinalizados">{lis}</ul></div>'
    )
    leg = legenda_html(
        [(f"Sinal {ROT_NIVEL[n].lower()}", COR_NIVEL[n]) for n in NIVEIS]
        + (
            [
                (f"Risco {ROT_RISCO[k].lower()}", COR_RISCO[k])
                for k in ("alto", "medio", "baixo", "")
            ]
            if risco
            else []
        ),
        "Cor do ponto (raio: seções sinalizadas no local)",
    )
    apos = (
        leg
        + '<div class="fz-painel" aria-live="polite"><p>Clique ou toque num ponto para ver o local, o endereço, as seções e os links do mapa.</p></div>'
        + f'<script type="application/json" class="fz-dados">{bloco}</script>'
        + blocos_malha(ufs_mun, nomes)
    )
    M = F["mapa"]
    legenda = (
        f"{inteiro(len(pts))} locais de votação no Brasil com coordenada ({inteiro(M.get('n_sem_coordenada'))} sem "
        "coordenada no cadastro e os do exterior ficam só na lista). Roda do mouse ou pinça para aproximar, arrastar para mover, duplo clique para "
        "centrar; os botões +, − e BR e as setas do teclado fazem o mesmo. A malha municipal do IBGE e os nomes de "
        "município entram ao aproximar, sem rede. Só os links do OpenStreetMap e do Google Maps, no painel, abrem "
        "páginas externas e precisam de internet. Fonte: fiscais.json, mapa e por_local."
    )
    fig = figura_html(
        "fiscais_mapa_navegavel",
        mapa,
        legenda,
        tips,
        controles=controles,
        modo="full",
        dim=False,
        apos=apos,
    )
    return fig.replace(
        ' data-fig="fiscais_mapa_navegavel"',
        ' data-fig="fiscais_mapa_navegavel" data-fz-fig',
        1,
    )


# ------------------------------------------------------------------ mapas por UF

MWU, MHU = 640, 600


def _proj_uf(uf: str):
    geo = _geo_municipal(uf)
    feats = geo["features"]
    lons = [c[0] for f in feats for a in _aneis(f["geometry"]) for c in a]
    lats = [c[1] for f in feats for a in _aneis(f["geometry"]) for c in a]
    cosl = math.cos(math.radians((min(lats) + max(lats)) / 2))
    sx, sy = (max(lons) - min(lons)) * cosl, max(lats) - min(lats)
    pad, topo = 10, 34
    esc = min((MWU - 2 * pad) / sx, (MHU - topo - pad) / sy)
    ox = pad + ((MWU - 2 * pad) - sx * esc) / 2
    oy = topo + ((MHU - topo - pad) - sy * esc) / 2
    lon0, lat1 = min(lons), max(lats)

    def proj(lon, lat):
        return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

    return feats, proj


@registra("fiscais_mapa_uf")
def fiscais_mapa_uf(d, **_op) -> str:
    F = fiscais(d)
    pts = _pontos(F)
    cont = Counter(
        p["l"].get("uf") for p in pts if p["l"].get("uf") not in (None, "ZZ")
    )
    ufs = [u for u, _ in cont.most_common() if _geo_municipal(u) is not None][:8]
    if not ufs:
        raise KeyError("mapa.pontos sem UF com malha municipal")
    tips = Tips()
    out = [
        svg_abre(
            MWU,
            MHU,
            "Locais sinalizados nas oito UFs com mais locais, sobre a malha municipal",
            "Uma aba por UF: malha dos municípios do IBGE e um ponto por local de votação com seção sinalizada; cor "
            "pelo nível, raio pelo número de seções sinalizadas.",
        )
    ]
    linhas = []
    for j, uf in enumerate(ufs):
        feats, proj = _proj_uf(uf)
        oculto = "" if j == 0 else ' display="none"'
        g = [f'<g data-alt-show="{uf}"{oculto}>']
        g.append(
            t(
                10,
                22,
                f"{NOME_UF.get(uf, uf)}: {inteiro(cont[uf])} locais sinalizados",
                15,
                INK,
                weight="700",
            )
        )
        malha = "".join(caminho(_aneis(f["geometry"]), proj, 1.2) for f in feats)
        g.append(
            f'<path d="{malha}" fill="#ebe5d6" stroke="{PAPER}" stroke-width="0.6"/>'
        )
        da_uf = sorted(
            (p for p in pts if p["l"].get("uf") == uf),
            key=lambda p: (-NIVEIS.index(p["nivel"]), p["n_secoes"]),
        )
        for p in da_uf:
            x, y = proj(p["lon"], p["lat"])
            k = f"r{len(linhas)}"
            lf = _linha_ficha(p)
            linhas.append([lf[0], lf[1], lf[4], lf[5], lf[6]])
            g.append(
                f'<circle class="hit fu-{p["nivel"]}" data-k="{k}" cx="{x:.0f}" cy="{y:.0f}" '
                f'r="{raio(p["n_secoes"]):g}"/>'
            )
        g.append("</g>")
        out.append("".join(g))
    out.append("</svg>")
    tips.tabela(
        ["Local", "Município", "Seções sinalizadas", "Critérios", "Nível"],
        linhas,
        sub=1,
        nota="endereço e links no mapa navegável e na lista de locais",
    )
    estilo = (
        "".join(
            f"#fig-fiscais_mapa_uf .fu-{n}{{fill:{COR_NIVEL[n]};fill-opacity:.85;stroke:{PAPER};stroke-width:.8}}"
            for n in NIVEIS
        )
        + "#fig-fiscais_mapa_uf circle.hit.on{stroke:#a4d42b;stroke-width:3px}"
    )
    ctl = botoes([(u, u) for u in ufs], ufs[0], "UF", "tab")
    leg = legenda_html([(ROT_NIVEL[n], COR_NIVEL[n]) for n in NIVEIS], "Nível do local")
    legenda = (
        f"As {len(ufs)} UFs com mais locais sinalizados ({', '.join(escape(NOME_UF.get(u, u)) for u in ufs)}). "
        "Malha municipal do IBGE; ponto na coordenada do cadastro de locais do TSE. Fonte: fiscais.json."
    )
    return figura_html(
        "fiscais_mapa_uf",
        "".join(out),
        legenda,
        tips,
        controles=ctl,
        modo="fit",
        dim=False,
        apos=f"<style>{estilo}</style>" + leg,
    )


__all__ = ["MUTED", "fiscais_mapa_navegavel", "fiscais_mapa_uf"]
