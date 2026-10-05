"""Mapas do dossiê da apuração: UF, municípios, mundo e pontos sobre o Brasil.

O mapa por UF usa a projeção da casa (`voto_util_mapa`, malha mínima do IBGE).
Os municipais leem `apuracao/public/geo/mun/{UF}.geojson`; o mundo lê
`apuracao/public/geo/mundo.geojson`. Os contornos são decimados no pixel para a
página não carregar quilômetros de vértice que a tela não mostra.
"""

from __future__ import annotations

import json
import math
from functools import cache
from html import escape

import voto_util_mapa as VM

from .pagina_comum import FLAVIO, INK, LULA, MUTED, PAPER, ROOT, num
from .pagina_figuras_prim import abre, legenda_linha, rect, txt

AZUIS = ["#c9d8ef", "#8fb0dd", "#4f7fc2", "#1457aa"]
VERMELHOS = ["#f0c9c0", "#e0907f", "#c85a46", "#b02f21"]
FAIXAS_MARGEM = [5, 15, 30]
DIVERGENTE = [
    "#b02f21",
    "#d9775f",
    "#efc3b5",
    "#e9e4d8",
    "#bccfea",
    "#6f97cf",
    "#1457aa",
]
CORTES_SWING = [-10, -5, -2, 2, 5, 10]


def faixa(v: float, cortes: list[float]) -> int:
    return sum(v >= c for c in cortes)


def cor_vencedor(lider: str | None, margem_pp: float | None) -> str:
    if lider is None or margem_pp is None:
        return "#d8d4c8"
    paleta = AZUIS if lider == "flavio" else VERMELHOS
    return paleta[faixa(abs(margem_pp), FAIXAS_MARGEM)]


def escuro_vencedor(margem_pp: float | None) -> bool:
    return margem_pp is not None and abs(margem_pp) >= FAIXAS_MARGEM[1]


def cor_swing(v: float | None) -> str:
    if v is None:
        return "#d8d4c8"
    return DIVERGENTE[faixa(v, CORTES_SWING)]


def _com_titulo(svg: str, titulo: str) -> str:
    i = svg.index(">") + 1
    return svg[:i] + f"<title>{escape(titulo)}</title>" + svg[i:]


def legenda_svg(
    itens: list[tuple[str, str]], x: float, y: float, passo: float = 20
) -> str:
    out = []
    for k, (nome, cor) in enumerate(itens):
        yy = y + k * passo
        out.append(
            rect(x, yy - 11, 14, 14, cor, f' stroke="{MUTED}" stroke-width="0.4"')
        )
        out.append(txt(x + 20, yy, nome, 12.5, INK))
    return "".join(out)


def mapa_uf(
    valores: dict,
    color_of,
    label_of,
    title_of,
    titulo: str,
    desc: str,
    legenda: list[tuple[str, str]] | None = None,
    escuro=None,
    largura: float = 640,
    altura: float = 640,
) -> str:
    leg = legenda_svg(legenda, 14, altura - 20 * len(legenda) - 4) if legenda else ""
    svg = VM.choropleth(
        valores,
        color_of,
        label_of,
        title_of,
        width=largura,
        height=altura,
        label=desc,
        ink=INK,
        muted=MUTED,
        stroke=PAPER,
        legend=leg,
        escuro=escuro,
    )
    return _com_titulo(svg, titulo).replace('class="fig-svg"', 'class="fig mapa"')


# ------------------------------------------------------------------ geometria


def _aneis(geom: dict) -> list[list[list[float]]]:
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [r for p in geom["coordinates"] for r in p]
    return []


def _caminho(aneis, proj, tol: float = 0.9) -> str:
    partes = []
    for anel in aneis:
        pts, ult = [], None
        for lon, lat in anel:
            x, y = proj(lon, lat)
            if ult is None or abs(x - ult[0]) + abs(y - ult[1]) >= tol:
                pts.append((x, y))
                ult = (x, y)
        if len(pts) >= 3:
            partes.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(partes)


@cache
def _geo_municipal(uf: str):
    arquivo = ROOT / f"apuracao/public/geo/mun/{uf}.geojson"
    if not arquivo.exists():
        return None
    return json.loads(arquivo.read_text(encoding="utf-8"))


def mapa_municipal(
    uf: str,
    valor_por_ibge: dict[str, float],
    titulo_por_ibge: dict[str, str],
    titulo: str,
    desc: str,
    largura: float = 420,
    altura: float = 400,
) -> str | None:
    geo = _geo_municipal(uf)
    if geo is None:
        return None
    feats = geo["features"]
    lons = [c[0] for f in feats for a in _aneis(f["geometry"]) for c in a]
    lats = [c[1] for f in feats for a in _aneis(f["geometry"]) for c in a]
    lat_m = (min(lats) + max(lats)) / 2
    cosl = math.cos(math.radians(lat_m))
    sx = (max(lons) - min(lons)) * cosl
    sy = max(lats) - min(lats)
    pad, topo = 8, 26
    esc = min((largura - 2 * pad) / sx, (altura - topo - pad) / sy)
    ox = pad + ((largura - 2 * pad) - sx * esc) / 2
    oy = topo + ((altura - topo - pad) - sy * esc) / 2
    lon0, lat1 = min(lons), max(lats)

    def proj(lon, lat):
        return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

    out = [abre(largura, altura, titulo, desc, "fig mapa-mun")]
    out.append(txt(pad, 18, titulo, 15, INK, weight="700"))
    for f in feats:
        cod = str(f.get("properties", {}).get("codarea", ""))
        v = valor_por_ibge.get(cod)
        d = _caminho(_aneis(f["geometry"]), proj, 0.8)
        if not d:
            continue
        tip = escape(titulo_por_ibge.get(cod, cod))
        out.append(
            f'<path d="{d}" fill="{cor_swing(v)}" stroke="{PAPER}" stroke-width="0.35">'
            f"<title>{tip}</title></path>"
        )
    out.append("</svg>")
    return "".join(out)


def legenda_swing_html() -> str:
    rot = [
        "Lula +10 ou mais",
        "Lula +5 a +10",
        "Lula +2 a +5",
        "de −2 a +2",
        "Flávio +2 a +5",
        "Flávio +5 a +10",
        "Flávio +10 ou mais",
    ]
    itens = "".join(
        f'<li><span class="sw" style="background:{c}"></span>{r}</li>'
        for c, r in zip(DIVERGENTE, rot, strict=True)
    )
    return f'<ul class="legenda-mapa">{itens}</ul>'


# ------------------------------------------------------------------ Brasil com pontos


def pontos_brasil(
    pontos: list[dict],
    titulo: str,
    desc: str,
    largura: float = 640,
    altura: float = 640,
    rotulos: int = 12,
    legenda: list[tuple[str, str]] | None = None,
) -> str:
    """Contorno das UFs com pontos (lat, lon, raio, cor, titulo, rotulo)."""
    geo = VM.paths(largura, altura)
    proj, _ = VM._proj(largura, altura, 10.0)
    out = [abre(largura, altura, titulo, desc, "fig mapa")]
    for uf, g in sorted(geo.items()):
        out.append(
            f'<path d="{g["d"]}" fill="#e7e1d2" stroke="#b9b29f" stroke-width="0.8">'
            f"<title>{uf}</title></path>"
        )
    ordem = sorted(pontos, key=lambda q: -q.get("raio", 4))
    for q in ordem:
        x, y = proj(q["lon"], q["lat"])
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{q.get("raio", 4):.1f}" fill="{q["cor"]}" '
            f'fill-opacity="0.85" stroke="{PAPER}" stroke-width="0.8">'
            f"<title>{escape(q.get('titulo', ''))}</title></circle>"
        )
    usados: list[tuple[float, float]] = []
    for q in pontos[:rotulos]:
        if not q.get("rotulo"):
            continue
        x, y = proj(q["lon"], q["lat"])
        if any(abs(x - a) < 70 and abs(y - b) < 15 for a, b in usados):
            continue
        usados.append((x, y))
        largura_txt = 6.6 * len(q["rotulo"]) + 8
        out.append(
            rect(
                x + 6,
                y - 20,
                largura_txt,
                16,
                "#ffffff",
                f' stroke="{MUTED}" stroke-width="0.5" rx="3"',
            )
        )
        out.append(txt(x + 10, y - 8, q["rotulo"], 11.5, INK, weight="600"))
    if legenda:
        out.append(legenda_svg(legenda, 14, altura - 20 * len(legenda) - 4))
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------------ mundo

LON0, LON1, LAT0, LAT1 = -170.0, 180.0, -56.0, 72.0


@cache
def _mundo():
    arquivo = ROOT / "apuracao/public/geo/mundo.geojson"
    if not arquivo.exists():
        return None
    return json.loads(arquivo.read_text(encoding="utf-8"))


def mapa_mundo(
    cidades: list[dict],
    titulo: str,
    desc: str,
    largura: float = 960,
    altura: float = 470,
    rotulos: int = 10,
) -> str:
    """Bolhas por cidade (área proporcional aos válidos), cor do líder."""
    topo = 6
    esc = min(largura / (LON1 - LON0), (altura - topo - 40) / (LAT1 - LAT0))
    ox = (largura - (LON1 - LON0) * esc) / 2

    def proj(lon, lat):
        return ox + (lon - LON0) * esc, topo + (LAT1 - lat) * esc

    out = [abre(largura, altura, titulo, desc, "fig mapa-mundo")]
    mundo = _mundo()
    if mundo:
        partes = []
        for f in mundo["features"]:
            d = _caminho(_aneis(f["geometry"]), proj, 1.4)
            if d:
                partes.append(d)
        out.append(
            f'<path d="{"".join(partes)}" fill="#e3ddce" stroke="{PAPER}" stroke-width="0.5"/>'
        )
    vmax = max((c.get("validos") or 0 for c in cidades), default=1) or 1
    for c in sorted(cidades, key=lambda c: -(c.get("validos") or 0)):
        if c.get("lat") is None or c.get("lon") is None:
            continue
        x, y = proj(c["lon"], c["lat"])
        r = 2 + 20 * math.sqrt((c.get("validos") or 0) / vmax)
        cor = (
            FLAVIO
            if c.get("lider") == "flavio"
            else LULA if c.get("lider") == "lula" else "#8a8a80"
        )
        pct = c.get("pct", {})
        tip = (
            f"{c.get('nome', '').title()} ({c.get('pais_nome', '')}): "
            f"Flávio {num(pct.get('flavio'), 1)}%, Lula {num(pct.get('lula'), 1)}%, "
            f"{c.get('validos', 0)} válidos"
        )
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{cor}" fill-opacity="0.6" '
            f'stroke="{cor}" stroke-width="0.8"><title>{escape(tip)}</title></circle>'
        )
    usados: list[tuple[float, float]] = []
    for c in sorted(cidades, key=lambda c: -(c.get("validos") or 0))[:rotulos]:
        x, y = proj(c["lon"], c["lat"])
        if any(abs(x - a) < 80 and abs(y - b) < 16 for a, b in usados):
            continue
        usados.append((x, y))
        nome = c.get("nome", "").title()
        out.append(
            rect(
                x + 8,
                y - 22,
                6.6 * len(nome) + 8,
                16,
                "#ffffff",
                f' stroke="{MUTED}" stroke-width="0.5" rx="3"',
            )
        )
        out.append(txt(x + 12, y - 10, nome, 11.5, INK, weight="600"))
    out.append(
        legenda_linha(
            [("Flávio lidera a cidade", FLAVIO), ("Lula lidera a cidade", LULA)],
            16,
            altura - 12,
        )
    )
    out.append("</svg>")
    return "".join(out)
