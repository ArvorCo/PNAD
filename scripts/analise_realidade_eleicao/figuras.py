"""Figuras SVG autossuficientes, com escalas comuns e texto acessível."""

import json
import math
from functools import cache
from html import escape

from .desenvolvimento import ROOT

LULA, FLAVIO = "#ae3428", "#1e5c99"


def num(v, casas=0):
    if v is None:
        return "s/d"
    return f"{v:,.{casas}f}".replace(",", "~").replace(".", ",").replace("~", ".")


def proj(lon, lat):
    return (lon + 75) * 12.0, (6 - lat) * 12.0


@cache
def contornos():
    j = json.loads(
        (ROOT / "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson").read_text()
    )
    out = []
    for f in j["features"]:
        geo = f["geometry"]
        polys = (
            geo["coordinates"]
            if geo["type"] == "MultiPolygon"
            else [geo["coordinates"]]
        )
        paths = []
        for poly in polys:
            for ring in poly:
                points = [proj(lon, lat) for lon, lat, *_ in ring]
                paths.append(
                    "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"
                )
        out.append(f'<path d="{"".join(paths)}"/>')
    return '<g class="contorno">' + "".join(out) + "</g>"


def mapa(rows, corte, max_diferenca):
    validos = [
        m for m in rows if m["completo"] and 100 * m["flavio"] < corte * m["validos"]
    ]
    pontos = [
        m for m in validos if m["sede_lon"] is not None and m["sede_lat"] is not None
    ]
    out = [
        f'<svg viewBox="0 0 520 490" role="img" aria-label="Municípios com Flávio abaixo de {corte}% dos votos válidos">',
        contornos(),
    ]
    for m in sorted(pontos, key=lambda r: r["diferenca"], reverse=True):
        x, y = proj(m["sede_lon"], m["sede_lat"])
        raio = 19 * math.sqrt(m["diferenca"] / max_diferenca)
        titulo = f"{m['nome']}/{m['uf']}: Flávio {num(m['pct_flavio'], 2)}%, Lula {num(m['pct_lula'], 2)}%; diferença {num(m['diferenca'])} votos"
        out.append(
            f'<circle class="cidade" cx="{x:.2f}" cy="{y:.2f}" r="{raio:.3f}" data-ibge="{m["ibge"]}"><title>{escape(titulo)}</title></circle>'
        )
    if not pontos:
        out.append(
            '<text x="260" y="220" text-anchor="middle" class="vazio">Nenhum município</text>'
        )
    out.append("</svg>")
    return f'<figure class="map-card" data-corte="{corte}"><div class="map-head"><h3>&lt; {corte}%</h3><p><b>{num(len(validos))}</b> municípios</p></div>{"".join(out)}<figcaption>{num(len(pontos))} sedes localizadas. Corte estrito: percentual menor que {corte}%.</figcaption></figure>'


def barras_faixas(stats, titulo, unidade):
    out = [f'<figure class="faixas"><h3>{escape(titulo)}</h3>']
    for row in stats["faixas"]:
        value = row["pct_lula"]
        out.append(
            f'<div class="faixa"><div class="faixa-label"><b>{num(row["min"], 1)} a {num(row["max"], 1)}{unidade}</b><span>{num(row["n"])} municípios</span></div><div class="placar" role="img" aria-label="Lula {num(value, 1)}%, Flávio {num(100-value, 1)}%"><span class="lula" style="width:{value:.3f}%">{num(value, 1)}%</span><span class="flavio" style="width:{100-value:.3f}%">{num(100-value, 1)}%</span></div></div>'
        )
    return (
        "".join(out)
        + "<figcaption>Faixas por quintis do indicador; empates ficam juntos. Barras somam os votos dos municípios de cada faixa. Vermelho: Lula; azul: Flávio.</figcaption></figure>"
    )


def regua_correlacao(stats):
    labels = [
        ("pearson", "Municípios com peso igual"),
        ("ponderada_validos", "Peso dos votos válidos"),
        ("dentro_grupo", "Dentro da mesma UF"),
    ]
    out = ['<div class="reguas">']
    for key, title in labels:
        value = stats[key]
        left, width = min(50, 50 + value * 50), abs(value) * 50
        out.append(
            f'<div><div class="regua-label"><span>{title}</span><b>{num(value, 2)}</b></div><div class="regua"><i style="left:{left:.2f}%;width:{width:.2f}%"></i><span></span></div></div>'
        )
    return (
        "".join(out)
        + '<p class="small">−1: associação inversa · 0: sem associação linear · +1: direta. Coeficientes com o voto em Lula; com Flávio, o sinal se inverte.</p></div>'
    )
