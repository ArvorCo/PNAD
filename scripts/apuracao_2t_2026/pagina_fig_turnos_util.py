"""Peças compartilhadas pelos capítulos cedo/tarde, turnos e abstenção (2º turno).

Lista longa adiada (tabela inteira em ``<noscript class="fig-src">`` dentro de um
``<details>``, materializada quando o leitor abre), mapa municipal com cor própria
(o ``mapa_municipal`` do 1º turno só pinta swing) e leitura de tabelas compactas.
"""

from __future__ import annotations

import math
from html import escape
from itertools import pairwise

from apuracao_2026.pagina_comum import NOME_UF, inteiro
from apuracao_2026.pagina_fig_base import (
    INK,
    LINE,
    MUTED,
    PAPER,
    area,
    ficha,
    hit,
    legenda,
    ln,
    nome_bonito,
    pp,
    r,
    svg_abre,
    t,
    ticks,
)
from apuracao_2026.pagina_mapas import _aneis, _geo_municipal

SEM_DADO = "#d8d4c8"
ESTILO = (
    "<style>.ct-lista{border-collapse:collapse;width:100%;font:13.5px/1.45 var(--sans)}"
    ".ct-lista th,.ct-lista td{padding:4px 8px;border-bottom:1px solid var(--line);text-align:left}"
    ".ct-lista td+td,.ct-lista th+th{text-align:right;font-variant-numeric:tabular-nums}"
    ".ct-lista thead th{position:sticky;top:0;background:var(--paper)}"
    ".ct-lista-c{max-height:560px;overflow:auto;border-top:2px solid var(--ink);margin:12px 0}"
    "details.ct-det{margin:18px 0}details.ct-det>summary{cursor:pointer;font:700 15px/1.5 var(--sans)}"
    ".ct-mapas{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}"
    ".ct-mapas svg{display:block;width:100%;height:auto}"
    ".duas>div{min-width:0}"
    "@media (max-width:720px){.ct-mapas{grid-template-columns:1fr}}</style>"
)


def linhas_de(bloco: dict) -> list[dict]:
    """{'colunas': [...], 'linhas': [[...]]} vira lista de dicionários."""
    cols = bloco["colunas"]
    return [dict(zip(cols, r, strict=False)) for r in bloco["linhas"]]


def ibge_por_tse(d) -> dict[str, str]:
    """Código TSE do município para o código IBGE, pela tabela do presidente.json."""
    P = d.get("presidente.json") or {}
    bloco = P.get("municipios")
    if not bloco:
        return {}
    return {m["cd_tse"]: str(m["ibge"]) for m in linhas_de(bloco) if m.get("ibge")}


def municipio(nome: str, uf: str) -> str:
    return f"{nome_bonito(nome)} ({uf})"


def _e(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]


def universo_municipios(C1: dict | None, C22: dict | None = None) -> str:
    """Nota de universo dos municípios, lida de ``comparacao_1t.json`` e ``comparacao_2022.json``.

    Explica as três contagens do dossiê: todos os municípios sem exterior (1º × 2º
    turno), os que favoreceram cada candidato (mudança arredondada a 0,00 pp fica
    de fora das duas) e os que existem nos arquivos de 2022.
    """
    if not C1:
        return ""
    ms = linhas_de(C1["municipios"])
    disp = C1["dispersao_municipal"]
    pf, pl = disp["n_swing_h2h_pro_flavio"], disp["n_swing_h2h_pro_lula"]
    zeros = [m for m in ms if not (m.get("swing_h2h_flavio_pp") or 0)]
    txt = (
        f"Universo: os {inteiro(len(ms))} municípios do Brasil, sem o exterior, com o arquivo de "
        "presidente completo nos dois turnos de 2026. A mudança contra o 1º turno favoreceu Lula em "
        f"{inteiro(pl)} e Flávio em {inteiro(pf)}"
    )
    if len(zeros) == 1:
        txt += (
            f"; em {municipio(zeros[0]['nome'], zeros[0]['uf'])} ficou em 0,00 pp, arredondada a duas "
            "casas, e o município não entra em nenhuma das duas contagens"
        )
    elif zeros:
        txt += (
            f"; em {inteiro(len(zeros))} municípios ({_e([municipio(m['nome'], m['uf']) for m in zeros])}) "
            "ficou em 0,00 pp, arredondada a duas casas, e eles não entram em nenhuma das duas contagens"
        )
    txt += "."
    sem = [m for m in (C22 or {}).get("sem_2022", []) if m.get("uf") != "ZZ"]
    n22 = ((C22 or {}).get("brasil") or {}).get("n_municipios")
    if sem and n22 is not None:
        txt += (
            f" Contra o 2º turno de 2022 são {inteiro(n22)}: "
            f"{_e([municipio(m['nome'], m['uf']) for m in sem])} "
            f"{'não está' if len(sem) == 1 else 'não estão'} nos arquivos de 2022 do TSE."
        )
    return txt


def tabela_compacta(cabecalho: list[str], linhas: list[list], legenda: str = "") -> str:
    """Tabela leve: sem classe por célula e sem fechamento de célula (HTML válido)."""
    th = "".join(f"<th scope=col>{escape(c)}</th>" for c in cabecalho)
    corpo = "".join(
        "<tr>" + "".join(f"<td>{escape(str(v))}" for v in r) for r in linhas
    )
    cap = f"<caption>{escape(legenda)}</caption>" if legenda else ""
    return (
        f'<div class="ct-lista-c" tabindex="0"><table class="ct-lista">{cap}'
        f"<thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table></div>"
    )


def lista_adiada(
    ident: str, resumo: str, cabecalho: list[str], linhas: list[list]
) -> str:
    """Tabela longa dentro de ``<details>``: sem script aparece inteira; com script,
    o corpo fica cru no ``<noscript>`` e só vira DOM quando o leitor abre."""
    tab = tabela_compacta(cabecalho, linhas)
    if "</noscript" in tab.lower():
        raise ValueError(f"lista {ident}: conteúdo com fechamento de noscript")
    return (
        f'<details class="ct-det" id="{ident}"><summary>{escape(resumo)}</summary>'
        f'<figure class="fig-adiada" data-adiada data-fig="{ident}">'
        '<div class="fig-espera-c" aria-hidden="true"><div class="fig-espera" style="--ar:4/1">'
        "lista carregada ao abrir</div></div>"
        f'<noscript class="fig-src">{tab}</noscript></figure></details>'
    )


def caminho(aneis, proj, tol: float = 1.6) -> str:
    """Contorno decimado no pixel, coordenadas inteiras e passos relativos
    (mesmo desenho de ``apuracao_2026.pagina_fig_mapas.caminho``)."""
    partes = []
    for anel in aneis:
        pts, ult = [], None
        for lon, lat in anel:
            x, y = proj(lon, lat)
            if ult is None or abs(x - ult[0]) + abs(y - ult[1]) >= tol:
                pts.append((round(x), round(y)))
                ult = (x, y)
        limpos = [q for i, q in enumerate(pts) if i == 0 or q != pts[i - 1]]
        if len(limpos) < 3:
            continue
        x0, y0 = limpos[0]
        passos = " ".join(
            f"{xb - xa} {yb - ya}" for (xa, ya), (xb, yb) in pairwise(limpos)
        )
        partes.append(f"M{x0} {y0}l{passos}z")
    return "".join(partes)


def mapa_mun(
    uf: str,
    cor_por_ibge: dict[str, str],
    tip_por_ibge: dict[str, str],
    titulo: str,
    desc: str,
    largura: float = 420,
    altura: float = 400,
    tol: float = 1.6,
) -> str | None:
    """Coroplético municipal de uma UF com a cor pronta de cada município.

    Mesmo desenho de ``pagina_mapas.mapa_municipal``; município sem valor fica cinza.
    """
    geo = _geo_municipal(uf)
    if geo is None:
        return None
    feats = geo["features"]
    lons = [c[0] for f in feats for a in _aneis(f["geometry"]) for c in a]
    lats = [c[1] for f in feats for a in _aneis(f["geometry"]) for c in a]
    cosl = math.cos(math.radians((min(lats) + max(lats)) / 2))
    sx = (max(lons) - min(lons)) * cosl
    sy = max(lats) - min(lats)
    pad, topo = 8, 28
    esc = min((largura - 2 * pad) / sx, (altura - topo - pad) / sy)
    ox = pad + ((largura - 2 * pad) - sx * esc) / 2
    oy = topo + ((altura - topo - pad) - sy * esc) / 2
    lon0, lat1 = min(lons), max(lats)

    def proj(lon, lat):
        return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

    out = [svg_abre(largura, altura, titulo, desc, ' data-mapa-mun="1"')]
    out.append(t(pad, 19, titulo, 15, INK, weight="700"))
    out.append(f'<g stroke="{PAPER}" stroke-width="0.35">')
    for f in feats:
        cod = str(f.get("properties", {}).get("codarea", ""))
        d = caminho(_aneis(f["geometry"]), proj, tol)
        if not d:
            continue
        cor = cor_por_ibge.get(cod, SEM_DADO)
        tip = escape(tip_por_ibge.get(cod, cod))
        out.append(f'<path d="{d}" fill="{cor}"><title>{tip}</title></path>')
    out.append("</g></svg>")
    return "".join(out)


def faixa(v: float, cortes: list[float]) -> int:
    return sum(v >= c for c in cortes)


def barras_uf(
    itens: list[dict],
    series: list[tuple[str, str, str]],
    tips,
    titulo: str,
    desc: str,
    largura: float = 900,
    rotulo_w: float = 170,
    casas: int = 2,
) -> str:
    """Barras divergentes de um zero central, uma linha por UF e uma barra por série.

    ``itens``: dicionários com 'uf' e as chaves das séries; ``series``: (chave, nome, cor).
    Cada linha leva ficha com todos os valores da UF.
    """
    ns = len(series)
    barra = 12 if ns > 1 else 18
    passo = ns * barra + 10
    topo = 46
    h = topo + passo * len(itens) + 36
    vals = [abs(it[k]) for it in itens for k, _, _ in series if it.get(k) is not None]
    vmax = (max(vals, default=1) or 1) * 1.12
    x0 = rotulo_w + (largura - rotulo_w - 20) / 2
    meia = (largura - rotulo_w - 130) / 2
    out = [svg_abre(largura, h, titulo, desc)]
    out.append(legenda([(n, c) for _, n, c in series], rotulo_w, 22, 13.5))
    for v in ticks(-vmax, vmax, 6):
        x = x0 + meia * v / vmax
        out.append(ln(x, topo - 6, x, h - 30, LINE, 1))
        rot = "0" if round(v) == 0 else f"{v:+.0f}".replace("-", "−")
        out.append(t(x, h - 12, rot, 12, MUTED, "middle", mono=True))
    out.append(ln(x0, topo - 6, x0, h - 30, INK, 1.4))
    for i, it in enumerate(itens):
        y = topo + i * passo
        partes = [t(rotulo_w - 10, y + passo / 2 + 2, it["rot"], 13.5, INK, "end")]
        for j, (k, _, cor) in enumerate(series):
            v = it.get(k)
            if v is None:
                continue
            yy = y + 4 + j * barra
            w = meia * abs(v) / vmax
            x = x0 if v >= 0 else x0 - w
            partes.append(r(x, yy, w, barra - 2, cor))
            tx = x0 + w + 5 if v >= 0 else x0 - w - 5
            partes.append(
                t(
                    tx,
                    yy + barra - 3,
                    pp(v, casas),
                    11.5,
                    INK,
                    "start" if v >= 0 else "end",
                    mono=True,
                )
            )
        partes.append(area(0, y, largura, passo))
        k = tips.add(ficha(it["rot"], it.get("sub", ""), it.get("ficha", [])))
        out.append(hit("".join(partes), k))
    out.append("</svg>")
    return "".join(out)


def nome_uf(uf: str) -> str:
    return NOME_UF.get(uf, uf)


__all__ = [
    "ESTILO",
    "MUTED",
    "SEM_DADO",
    "barras_uf",
    "faixa",
    "ibge_por_tse",
    "linhas_de",
    "lista_adiada",
    "mapa_mun",
    "municipio",
    "nome_uf",
    "tabela_compacta",
]
