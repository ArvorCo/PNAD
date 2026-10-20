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
COR_RISCO = {"baixo": "#e3e0d4", "medio": "#e0b25a", "alto": "#a8321f"}
ROTULO_RISCO = {"baixo": "risco baixo", "medio": "risco médio", "alto": "risco alto"}
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
            for k in ("baixo", "medio", "alto")
        ],
        H + 22,
    )
    corpo = f'<g>{"".join(partes)}</g><g>{_contorno(W, H)}</g>{leg}'
    svg = _svg(
        "Risco climático previsto para 25 de outubro, por célula de 0,5°",
        "Mapa do Brasil com uma célula por quadrado de 0,5 grau, colorida pelo nível "
        "de risco da regra declarada. Risco alto concentra-se em São Paulo, Paraná e "
        "Mato Grosso do Sul.",
        "maprk",
        corpo,
        H + 34,
    )
    return svg, {k: len(v) for k, v in grupos.items()}
