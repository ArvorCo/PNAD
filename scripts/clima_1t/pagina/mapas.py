"""Mapas em SVG: células de 0,25° por faixa de chuva e células de 0,5° por risco previsto.

Cada célula vira um quadrado projetado com a mesma projeção do mapa do voto útil; as
células de uma classe viram um único caminho, para o HTML não passar de algumas centenas
de KB. Contorno de UF por cima, sem rótulo, para orientar a leitura.
"""

from __future__ import annotations

import math

import voto_util_mapa as geo
from clima_1t import variaveis

from .util import Dados, esc, inteiro

W, H = 640.0, 600.0
PAD = 6.0
COR_FAIXA = {
    "seca": "#e3e0d4",
    "fraca": "#bcd8d3",
    "moderada": "#5fa9a1",
    "forte": "#0c6b64",
    "muito_forte": "#0a2f2c",
}
COR_RISCO = {
    "baixo": "#e3e0d4",
    "medio": "#e0b25a",
    "alto": "#a8321f",
    "sem_dado": "#8f9692",
}
ROTULO_RISCO = {
    "baixo": "baixo",
    "medio": "médio",
    "alto": "alto",
    "sem_dado": "sem dado",
}
CONTORNO = "#192e2b"


def _caminho(f, celulas: list[tuple[float, float]], passo: float) -> str:
    """Quadrados do mesmo nível; células vizinhas na mesma linha viram um retângulo."""
    por_linha: dict[float, list[float]] = {}
    for lat, lon in celulas:
        por_linha.setdefault(lat, []).append(lon)
    partes = []
    for lat in sorted(por_linha):
        lons = sorted(por_linha[lat])
        i = 0
        while i < len(lons):
            j = i
            while j + 1 < len(lons) and round(lons[j + 1] - lons[j], 4) == passo:
                j += 1
            x0, y0 = f(lons[i], lat + passo)
            x1, y1 = f(lons[j] + passo, lat)
            w, h = x1 - x0 + 0.4, y1 - y0 + 0.4
            partes.append(f"M{x0:.1f} {y0:.1f}h{w:.1f}v{h:.1f}h-{w:.1f}z")
            i = j + 1
    return "".join(partes)


def _contorno(width: float, height: float) -> str:
    partes = [
        f'<path d="{g["d"]}" fill="none" stroke="{CONTORNO}" stroke-width="0.7" '
        f'stroke-linejoin="round" opacity="0.75"/>'
        for g in geo.paths(width, height, PAD).values()
    ]
    return "".join(partes)


def _legenda(itens: list[tuple[str, str, str]], y: float) -> str:
    out, x = [], 12.0
    for rot, cor, extra in itens:
        out.append(
            f'<rect x="{x:.0f}" y="{y - 11:.0f}" width="14" height="14" fill="{cor}" '
            f'stroke="{CONTORNO}" stroke-width="0.6"/>'
            f'<text x="{x + 20:.0f}" y="{y:.0f}" class="tm">{esc(rot)}{esc(extra)}</text>'
        )
        x += 20 + 7.4 * (len(rot) + len(extra)) + 22
    return "".join(out)


def _svg(titulo: str, desc: str, ident: str, corpo: str, altura: float) -> str:
    return (
        f'<svg viewBox="0 0 {W:.0f} {altura:.0f}" role="img" '
        f'aria-labelledby="{ident}t {ident}d" xmlns="http://www.w3.org/2000/svg">'
        f'<title id="{ident}t">{esc(titulo)}</title><desc id="{ident}d">{esc(desc)}</desc>'
        f"{corpo}</svg>"
    )


def celulas_por_faixa(dados: Dados) -> dict[str, list[tuple[float, float]]]:
    """Células de 0,25° com resposta, agrupadas pela faixa de chuva nas horas de votação."""
    df = variaveis.clima_por_celula(dados.celulas)
    grupos: dict[str, list[tuple[float, float]]] = {k: [] for k in COR_FAIXA}
    for cel, faixa in df["faixa_chuva_votacao"].items():
        if faixa is None or (isinstance(faixa, float) and math.isnan(faixa)):
            continue
        lat, lon = (float(p) for p in str(cel).split(","))
        grupos[str(faixa)].append((lat, lon))
    return grupos


def mapa_faixas(dados: Dados) -> str:
    """Mapa das células de 0,25° pela chuva das 7h às 18h de Brasília de 04/10."""
    f, _ = geo._proj(W, H, PAD)
    grupos = celulas_por_faixa(dados)
    rotulos = dados.d["faixas"]["chuva"]
    partes = []
    for faixa, cor in COR_FAIXA.items():
        celulas = grupos[faixa]
        caminho = _caminho(f, celulas, 0.25)
        if caminho:
            partes.append(
                f'<path d="{caminho}" fill="{cor}" data-faixa="{faixa}">'
                f"<title>{esc(rotulos[faixa])}: {inteiro(len(celulas))} células</title></path>"
            )
    leg = _legenda(
        [
            (rotulos[k].split(" (")[0], COR_FAIXA[k], f" {inteiro(len(grupos[k]))}")
            for k in COR_FAIXA
        ],
        H + 22,
    )
    corpo = f'<g>{"".join(partes)}</g><g>{_contorno(W, H)}</g>{leg}'
    return _svg(
        "Chuva nas horas de votação de 4 de outubro, por célula de 0,25°",
        "Mapa do Brasil com uma célula por quadrado de 0,25 grau, colorida pela faixa "
        "de chuva acumulada das 7h às 18h de Brasília. Chuva forte aparece no "
        "Sudeste, no Sul e no Mato Grosso do Sul.",
        "mapfx",
        corpo,
        H + 34,
    )


def mapa_risco(dados: Dados) -> tuple[str, dict[str, int]]:
    """Mapa das células de 0,5° da previsão para 25/10, por nível de risco."""
    f, _ = geo._proj(W, H, PAD)
    grupos: dict[str, list[tuple[float, float]]] = {k: [] for k in COR_RISCO}
    for chave, cel in dados.previsao["celulas"].items():
        risco = cel.get("risco")
        if risco in grupos:
            lat, lon = (float(p) for p in chave.split(","))
            grupos[risco].append((lat, lon))
    partes = []
    for risco, cor in COR_RISCO.items():
        caminho = _caminho(f, grupos[risco], 0.5)
        if caminho:
            partes.append(
                f'<path d="{caminho}" fill="{cor}" data-risco="{risco}">'
                f"<title>{esc(ROTULO_RISCO[risco])}: {inteiro(len(grupos[risco]))} células</title></path>"
            )
    leg = _legenda(
        [
            (ROTULO_RISCO[k], COR_RISCO[k], f" {inteiro(len(grupos[k]))}")
            for k in COR_RISCO
        ],
        H + 22,
    )
    corpo = f'<g>{"".join(partes)}</g><g>{_contorno(W, H)}</g>{leg}'
    svg = _svg(
        "Risco climático previsto para 25 de outubro, por célula de 0,5°",
        "Mapa do Brasil com uma célula por quadrado de 0,5 grau, colorida pelo nível "
        "de risco da regra declarada, na data de consulta indicada. Não mede abstenção.",
        "maprk",
        corpo,
        H + 34,
    )
    return svg, {k: len(v) for k, v in grupos.items()}


def mapa_chuva_prevista(
    dados: Dados, periodo: str = "votacao", ident: str = "mapchuva2t"
) -> str:
    """Chuva na janela selecionada, com escala comum entre os períodos."""
    f, _ = geo._proj(W, H, PAD)
    grupos = {k: [] for k in COR_FAIXA}
    for chave, cel in dados.previsao["celulas"].items():
        faixa = variaveis.faixa_chuva(
            cel.get("periodos", {}).get(periodo, cel).get("chuva_mm")
        )
        if faixa in grupos:
            grupos[faixa].append(tuple(float(v) for v in chave.split(",")))
    partes = [
        f'<path d="{_caminho(f, cs, 0.5)}" fill="{COR_FAIXA[k]}"/>'
        for k, cs in grupos.items()
        if cs
    ]
    legenda = _legenda(
        [
            (rot, COR_FAIXA[k], "")
            for k, rot in zip(
                COR_FAIXA, ["<0,1", "0,1–5", ">5–20", ">20–50", ">50 mm"], strict=True
            )
        ],
        H + 22,
    )
    return _svg(
        f"Chuva prevista para 25/10, {periodo}, acumulado em mm",
        "Células de 0,5 grau com locais de votação. Áreas sem célula não têm dado; "
        "não representam ausência de chuva. Janela horária indicada em Brasília.",
        ident + periodo,
        "".join(partes) + _contorno(W, H) + legenda,
        H + 34,
    )


def mapa_abstencao(dados: Dados) -> str:
    """Abstenção observada nas 27 UFs, mesma fonte do cenário de persistência."""
    valores = {u["uf"]: u["abstencao_pct"] for u in dados.territorio["ufs"]}

    def cor(_uf, v):
        return (
            "#bcd8d3"
            if v < 18
            else "#5fa9a1" if v < 20 else "#e0b25a" if v < 22 else "#a8321f"
        )

    from .util import pct

    return geo.choropleth(
        valores,
        cor,
        lambda uf, v: uf if uf in geo.FORA else f"{uf} {pct(v, 1)}",
        lambda uf, v: f"{uf}: {pct(v, 2)} de abstenção observada no 1º turno",
        label="Abstenção observada no primeiro turno de 04/10/2026, por UF",
        escuro=lambda uf, v: v >= 22,
        legend=_legenda(
            [
                (r, c, "")
                for r, c in [
                    ("<18%", "#bcd8d3"),
                    ("18–<20%", "#5fa9a1"),
                    ("20–<22%", "#e0b25a"),
                    ("≥22%", "#a8321f"),
                ]
            ],
            610,
        ),
    )
