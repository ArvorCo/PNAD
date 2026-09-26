"""Mapa do Brasil por UF em SVG, sem dependencias externas.

Le a malha oficial do IBGE (`servicodados.ibge.gov.br/api/v3/malhas`, qualidade
minima, arquivada em `data/originals/ibge_malhas/br_uf/br_uf_minima.geojson`) e
projeta em equiretangular com correcao de cosseno na latitude media do pais.
Cada UF vira um `<path>` com `<title>` para leitura ao passar o ponteiro, e a
pagina continua legivel sem JavaScript.
"""

from __future__ import annotations

import html
import json
import math
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MALHA = ROOT / "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson"

IBGE_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}  # fmt: skip

# Estados pequenos demais para rotulo dentro do contorno: rotulo deslocado com guia.
FORA = {
    "RN": (1.9, -0.2),
    "PB": (2.3, 0.3),
    "PE": (2.6, 1.1),
    "AL": (2.3, 1.4),
    "SE": (2.0, 1.8),
    "ES": (2.4, 0.4),
    "RJ": (2.2, 1.6),
    "DF": (2.6, -0.6),
}

LON0, LON1, LAT0, LAT1 = -74.2, -34.6, -33.9, 5.4
COS = math.cos(math.radians(-14.0))


@cache
def _features() -> dict[str, list[list[list[float]]]]:
    raw = json.loads(MALHA.read_text(encoding="utf-8"))
    out: dict[str, list[list[list[float]]]] = {}
    for feat in raw["features"]:
        uf = IBGE_UF[feat["properties"]["codarea"]]
        geom = feat["geometry"]
        polys = (
            geom["coordinates"]
            if geom["type"] == "MultiPolygon"
            else [geom["coordinates"]]
        )
        out[uf] = [ring for poly in polys for ring in poly]
    return out


def _proj(width: float, height: float, pad: float):
    # Margem extra a direita para os rotulos deslocados dos estados pequenos.
    width = width - 44
    span_y = LAT1 - LAT0
    span_x = (LON1 - LON0) * COS
    scale = min((width - 2 * pad) / span_x, (height - 2 * pad) / span_y)
    ox = pad + ((width - 2 * pad) - span_x * scale) / 2
    oy = pad + ((height - 2 * pad) - span_y * scale) / 2

    def f(lon: float, lat: float) -> tuple[float, float]:
        return ox + (lon - LON0) * COS * scale, oy + (LAT1 - lat) * scale

    return f, scale


def _centroid(rings: list[list[list[float]]]) -> tuple[float, float]:
    """Centroide do maior anel, pela formula da area com sinal."""
    best = max(rings, key=len)
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(best, best[1:] + best[:1], strict=True):
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    return cx / (6 * a), cy / (6 * a)


LABEL_NUDGE = {
    "GO": (0.2, 0.6),
    "MG": (0.3, 0.2),
    "PA": (0.0, 0.8),
    "MT": (0.0, 0.3),
    "BA": (0.4, 0.2),
}


def paths(width: float, height: float, pad: float = 10.0) -> dict[str, dict]:
    """Devolve, por UF, o atributo `d` do contorno e o ponto do rotulo."""
    f, scale = _proj(width, height, pad)
    out = {}
    for uf, rings in _features().items():
        parts = []
        for ring in rings:
            pts = [f(lon, lat) for lon, lat in ring]
            seg = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            parts.append(f"M{seg}Z")
        lon, lat = _centroid(rings)
        dx, dy = LABEL_NUDGE.get(uf, (0.0, 0.0))
        lx, ly = f(lon + dx, lat - dy)
        entry = {
            "d": "".join(parts),
            "label": (lx, ly),
            "anchor": (lx, ly),
            "fora": False,
        }
        if uf in FORA:
            ox, oy = FORA[uf]
            ax, ay = f(lon, lat)
            entry["label"] = (ax + ox * scale * COS, ay + oy * scale)
            entry["fora"] = True
        out[uf] = entry
    return out


def choropleth(
    values: dict[str, float | None],
    color_of,
    label_of,
    title_of,
    *,
    width: float = 640,
    height: float = 620,
    label: str = "Mapa do Brasil por estado",
    ink: str = "#151812",
    muted: str = "#535b54",
    stroke: str = "#f7f5ee",
    legend: str = "",
    escuro=None,
) -> str:
    """Mapa coroplético. `color_of(uf, v)`, `label_of(uf, v)` e `title_of(uf, v)`."""
    geo = paths(width, height)
    shapes, labels = [], []
    for uf, g in sorted(geo.items()):
        v = values.get(uf)
        fill = color_of(uf, v)
        tip = html.escape(title_of(uf, v))
        shapes.append(
            f'<path d="{g["d"]}" fill="{fill}" stroke="{stroke}" stroke-width="1.1" '
            f'stroke-linejoin="round" data-uf="{uf}"><title>{tip}</title></path>'
        )
        lx, ly = g["label"]
        text = html.escape(label_of(uf, v))
        if g["fora"]:
            ax, ay = g["anchor"]
            largura = 8.2 * len(text) + 8
            labels.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx - 3:.1f}" y2="{ly - 4:.1f}" '
                f'stroke="{muted}" stroke-width="0.8"/>'
                f'<rect x="{lx - 4:.1f}" y="{ly - 13:.1f}" width="{largura:.1f}" height="17" rx="3" '
                f'fill="#ffffff" stroke="{muted}" stroke-width="0.5"/>'
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="12.5" fill="{ink}" '
                f'font-family="IBM Plex Sans Condensed,Arial,sans-serif" font-weight="600">{text}</text>'
            )
        else:
            claro = escuro is not None and escuro(uf, v)
            cor, halo = ("#ffffff", "#0d2238") if claro else (ink, "#ffffff")
            labels.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="12.5" text-anchor="middle" '
                f'dominant-baseline="middle" fill="{cor}" paint-order="stroke" stroke="{halo}" '
                f'stroke-width="3" stroke-linejoin="round" '
                f'font-family="IBM Plex Sans Condensed,Arial,sans-serif" font-weight="700">{text}</text>'
            )
    return (
        f'<svg class="fig-svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="{html.escape(label)}" xmlns="http://www.w3.org/2000/svg">'
        f"<g>{''.join(shapes)}</g><g>{''.join(labels)}</g>{legend}</svg>"
    )
