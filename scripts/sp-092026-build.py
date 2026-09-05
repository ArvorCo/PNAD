#!/usr/bin/env python3
"""Gera o atlas de São Paulo: dados públicos, pesquisas auditadas e a camada estratégica.

Toda figura é SVG gerado aqui, com os dados embutidos na página: nada depende
de JavaScript para desenhar. O JavaScript só troca camadas do mapa e filtra a
tabela municipal.
"""

import json
import math
from html import escape as esc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
ASSETS = OUT / "assets"
D = json.loads((ASSETS / "sp_092026_data.json").read_text())
P = json.loads((ASSETS / "sp_092026_pesquisas.json").read_text())
N = json.loads((ASSETS / "sp_092026_pnad.json").read_text())
K = json.loads((ASSETS / "sp_092026_camada2.json").read_text())
C = D["municipios"]
CITY = {r["id"]: r for r in C}
A = N["anual_2025_visita1"]
Q = N["trimestral_2026_t1"]
R = K["reponderacao"]
FLOWS = K["fluxos"]
VAO = K["vao"]
E = K["estrategia"]
CARR = K["carregadores"]
CORR = K["corredores"]
INK, GREEN, GOLD, RED, MUTED, PAPER = (
    "#192e2b",
    "#28705f",
    "#d8a631",
    "#b84648",
    "#56615a",
    "#f4f0e7",
)
BLUE = "#3a6ea5"
ROTA_CORES = {
    "capital": "#192e2b",
    "leste": "#b84648",
    "oeste_metro": "#7d5b00",
    "porto": "#3a6ea5",
    "tecnologia": "#28705f",
    "aeroespacial": "#6b4c9a",
    "sorocaba": "#9a5222",
    "cana": "#6f6f1f",
    "agro_oeste": "#4f7d3c",
}


def fmt(v, n=0):
    return f"{v:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(v, n=1):
    v = round(v, n)
    if v == 0:
        v = 0.0
    return ("+" if v > 0 else "") + fmt(v, n)


def link(url, label):
    return f'<a href="{esc(url, quote=True)}">{esc(label)}</a>'


def table(head, rows, ident="", cls=""):
    idattr = f' id="{ident}"' if ident else ""
    return (
        f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tabela: {esc(head[0])}"><table{idattr} class="{cls}"><thead><tr>'
        + "".join(f'<th scope="col">{x}</th>' for x in head)
        + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows)
        + "</tbody></table></div>"
    )


def bars(values, maxval=100, digits=1):
    return (
        '<div class="bars">'
        + "".join(
            f'<div class="bar"><span>{esc(k)}</span><b>{fmt(v, digits)}%</b><div><i style="width:{min(100, v / maxval * 100):.3f}%"></i></div></div>'
            for k, v in values
        )
        + "</div>"
    )


def source(key, pages):
    return f'<p class="note">Fonte: {link(P["urls"][key], key.title())}, {pages}. Percentuais publicados; arredondamentos preservados.</p>'


def chapter(num, ident, title, lead, body, dark=False, wide=False):
    return f'<section id="{ident}" class="chapter {"dark" if dark else ""}"><div class="wrap{" wide" if wide else ""}"><header class="chapter-head"><span class="number">{num:02}</span><div><h2>{title}</h2><p class="lead">{lead}</p></div></header>{body}</div></section>'


def stamp(kind, text):
    return f'<span class="stamp {kind}">{esc(text)}</span>'


# ------------------------------------------------------------------ geografia
GEO = json.loads((ASSETS / "sp_092026_municipios.geojson").read_text())
COS23 = math.cos(math.radians(23))


def geo_paths():
    polygons = []
    coords = []
    for feature in GEO["features"]:
        shape = feature["geometry"]
        rings = (
            shape["coordinates"]
            if shape["type"] == "Polygon"
            else [ring for poly in shape["coordinates"] for ring in poly]
        )
        coords.extend((x * COS23, -y) for ring in rings for x, y, *_ in ring)
        polygons.append((feature["properties"]["codarea"], rings))
    xs, ys = zip(*coords, strict=True)
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    scale = min(960 / (xmax - xmin), 620 / (ymax - ymin))

    def project(x, y):
        return 20 + (x * COS23 - xmin) * scale, 20 + (-y - ymin) * scale

    out = {}
    cent = {}
    for ident, rings in polygons:
        path = " ".join(
            "M"
            + "L".join(
                f"{px:.2f},{py:.2f}" for px, py in (project(x, y) for x, y, *_ in ring)
            )
            + "Z"
            for ring in rings
        )
        pts = [project(x, y) for x, y, *_ in rings[0]]
        cent[ident] = (
            sum(p[0] for p in pts) / len(pts),
            sum(p[1] for p in pts) / len(pts),
        )
        out[ident] = path
    return out, cent


PATHS, CENTROIDS = geo_paths()


def svgmap():
    colors = {
        "Jair → Jair": GREEN,
        "Jair → PT": GOLD,
        "PT → PT": RED,
        "Jair → Empate": "#859394",
    }
    paths = [
        f'<path data-id="{ident}" d="{d}" fill="{colors[CITY[ident]["virada"]]}" fill-rule="evenodd"><title>{esc(CITY[ident]["nome"])}: {esc(CITY[ident]["virada"])}; Bolsonaro 2022: {fmt(CITY[ident]["jair_2022_2_pct"], 2)}%</title></path>'
        for ident, d in PATHS.items()
    ]
    return (
        '<svg id="municipal-map" viewBox="0 0 1000 660" role="img" aria-labelledby="map-title"><title id="map-title">645 municípios de São Paulo: resultados presidenciais de 2018 e 2022</title>'
        + "".join(paths)
        + "</svg>"
    )


def route_map():
    body = [
        f'<path d="{d}" fill="#e6e7ce" stroke="#fffdf8" stroke-width="0.5"/>'
        for d in PATHS.values()
    ]
    for c in CORR:
        color = ROTA_CORES[c["slug"]]
        ids = [r["id"] for r in c["cidades"]]
        body.append(
            f'<path d="{PATHS_UNION(ids)}" fill="{color}" fill-opacity="0.22" stroke="none"/>'
        )
        top = ids[: min(6, len(ids))]
        for rank, i in enumerate(top):
            x, y = CENTROIDS[i]
            rr = 10 if rank == 0 else 5.5
            body.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" fill="{color}" stroke="#fffdf8" stroke-width="1.6"><title>{esc(CITY[i]["nome"])}: {esc(c["nome"])}</title></circle>'
            )
    return (
        '<svg id="route-map" viewBox="0 0 1000 660" role="img" aria-label="Nove corredores de campanha sobre a malha municipal de São Paulo"><title>Nove corredores de campanha</title>'
        + "".join(body)
        + "</svg>"
    )


def PATHS_UNION(ids):
    return " ".join(PATHS[i] for i in ids)


# ------------------------------------------------------------------ figuras SVG
def hatch_defs():
    defs = []
    for name, color in (
        ("dir", GOLD),
        ("esq", RED),
        ("neu", "#8a8f86"),
        ("out", "#7f9aa8"),
    ):
        defs.append(
            f'<pattern id="h-{name}" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" fill="{color}" fill-opacity="0.16"/><line x1="0" y1="0" x2="0" y2="7" stroke="{color}" stroke-width="2.4" stroke-opacity="0.75"/></pattern>'
        )
    return "<defs>" + "".join(defs) + "</defs>"


def sankey_svg(flow, ident):
    W, H = 1000, 460
    top, bottom = 40, 430
    scale = (bottom - top - 8 * (len(flow["destino"]) - 1)) / 100
    left_x, right_x, node_w = 200, 780, 26
    src = list(flow["origem"])
    dst = list(flow["destino"])
    src_total = sum(flow["origem"].values())
    dst_total = sum(flow["destino"].values())
    row_scale = dst_total / src_total
    right_class = {"Flávio": "dir", "Lula": "esq", "Não escolha": "neu"}
    color_of = {
        "Flávio": GOLD,
        "Lula": RED,
        "Tarcísio": GREEN,
        "Haddad": RED,
        "Não escolha": "#8a8f86",
    }
    parts = [hatch_defs()]
    y = top
    src_pos = {}
    for s in src:
        h = flow["origem"][s] * row_scale * scale
        src_pos[s] = [y, y + h, y]
        parts.append(
            f'<rect x="{left_x}" y="{y:.1f}" width="{node_w}" height="{max(h, 1):.1f}" fill="{color_of.get(s, GREEN)}"/>'
        )
        parts.append(
            f'<text x="{left_x - 12}" y="{y + h / 2 + 5:.1f}" text-anchor="end" class="sk-label">{esc(s)} <tspan class="sk-val">{fmt(flow["origem"][s], 1 if isinstance(flow["origem"][s], float) else 0)}</tspan></text>'
        )
        y += h + 8
    y = top
    dst_pos = {}
    for d in dst:
        h = flow["destino"][d] * scale
        dst_pos[d] = [y, y + h, y]
        parts.append(
            f'<rect x="{right_x}" y="{y:.1f}" width="{node_w}" height="{max(h, 1):.1f}" fill="{color_of.get(d, "#7f9aa8")}"/>'
        )
        parts.append(
            f'<text x="{right_x + node_w + 12}" y="{y + h / 2 + 5:.1f}" class="sk-label">{esc(d)} <tspan class="sk-val">{fmt(flow["destino"][d], 1 if isinstance(flow["destino"][d], float) else 0)}</tspan></text>'
        )
        y += h + 8
    ribbons = []
    labels = []
    for s in src:
        for d in dst:
            v = flow["matriz"][s][d]
            if v < 0.15:
                continue
            h = v * scale
            y1 = src_pos[s][2]
            y2 = dst_pos[d][2]
            src_pos[s][2] += h
            dst_pos[d][2] += h
            x1, x2 = left_x + node_w, right_x
            xm = (x1 + x2) / 2
            cls = right_class.get(d, "out")
            ribbons.append(
                f'<path d="M{x1},{y1:.1f} C{xm},{y1:.1f} {xm},{y2:.1f} {x2},{y2:.1f} L{x2},{y2 + h:.1f} C{xm},{y2 + h:.1f} {xm},{y1 + h:.1f} {x1},{y1 + h:.1f} Z" fill="url(#h-{cls})" stroke="{color_of.get(d, "#7f9aa8")}" stroke-opacity="0.5" stroke-width="0.6"><title>{esc(s)} para {esc(d)}: {fmt(v, 1)} pontos (estimado por IPF)</title></path>'
            )
            if v >= 1.4 and s != d:
                j = dst.index(d)
                if j < 2:
                    t = {0: 0.5, 1: 0.27, 2: 0.74}[src.index(s)]
                else:
                    t = 0.3 + 0.55 * (j - 2) / max(len(dst) - 3, 1)
                    t = min(0.8, t + 0.08 * src.index(s))
                lx = x1 + (x2 - x1) * t
                ease = 3 * t * t - 2 * t * t * t
                ly = y1 + (y2 - y1) * ease + h / 2 + 4
                labels.append(
                    f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" class="sk-flow">{esc(s)} para {esc(d)}: {fmt(v, 1)}</text>'
                )
    parts.extend(ribbons)
    parts.extend(labels)
    parts.append(
        f'<text x="{left_x}" y="{top - 16}" text-anchor="start" class="sk-head">Governo · 2º turno</text>'
    )
    parts.append(
        f'<text x="{right_x + node_w}" y="{top - 16}" text-anchor="end" class="sk-head">{"Presidência · 2º turno" if flow["tipo"] == "2T para 2T" else "Presidência · 1º turno"}</text>'
    )
    return (
        f'<svg id="{ident}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(flow["nome"])}"><title>{esc(flow["nome"])}</title>'
        + "".join(parts)
        + "</svg>"
    )


def lollipop_svg(rows, ident, title):
    W = 1000
    rowh = 26
    H = 60 + rowh * len(rows) + 72
    x0, x1 = 300, 900
    sx = lambda v: x0 + (x1 - x0) * v / 100  # noqa: E731
    parts = [f'<text x="{x0}" y="26" class="sk-head">{esc(title)}</text>']
    for tick in (0, 25, 50, 75, 100):
        parts.append(
            f'<line x1="{sx(tick):.1f}" y1="44" x2="{sx(tick):.1f}" y2="{H - 66}" stroke="#c9c9bc" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{sx(tick):.1f}" y="{H - 50}" text-anchor="middle" class="axis-t">{tick}%</text>'
        )
    y = 60
    for r in rows:
        t, f = r["tarcisio"], r["flavio"]
        parts.append(
            f'<text x="{x0 - 14}" y="{y + 5}" text-anchor="end" class="sk-label">{esc(r["segmento"])}</text>'
        )
        parts.append(
            f'<line x1="{sx(min(t, f)):.1f}" y1="{y}" x2="{sx(max(t, f)):.1f}" y2="{y}" stroke="{INK}" stroke-width="3" stroke-opacity="0.35"/>'
        )
        parts.append(
            f'<circle cx="{sx(f):.1f}" cy="{y}" r="7" fill="{GOLD}" stroke="{INK}" stroke-width="1"><title>Flávio, 2º turno presidencial: {fmt(f, 1)}%</title></circle>'
        )
        parts.append(
            f'<circle cx="{sx(t):.1f}" cy="{y}" r="7" fill="{GREEN}" stroke="{INK}" stroke-width="1"><title>Tarcísio, 2º turno estadual: {fmt(t, 1)}%</title></circle>'
        )
        parts.append(
            f'<text x="{x1 + 16}" y="{y + 5}" class="sk-val2">{sgn(r["vao_tarcisio_flavio"])}</text>'
        )
        y += rowh
    parts.append(
        f'<circle cx="{x0}" cy="{H - 18}" r="6" fill="{GREEN}"/><text x="{x0 + 12}" y="{H - 14}" class="axis-t">Tarcísio · governo 2º turno</text>'
    )
    parts.append(
        f'<circle cx="{x0 + 250}" cy="{H - 18}" r="6" fill="{GOLD}"/><text x="{x0 + 262}" y="{H - 14}" class="axis-t">Flávio · Presidência 2º turno</text>'
    )
    parts.append(
        f'<text x="{x1 + 16}" y="{H - 14}" class="axis-t">vão = Tarcísio menos Flávio</text>'
    )
    return (
        f'<svg id="{ident}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        + "".join(parts)
        + "</svg>"
    )


def diverging_svg(rows, ident, title, lo=-5, hi=25):
    W = 1000
    rowh = 46
    H = 70 + rowh * len(rows) + 30
    x0, x1 = 330, 940
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)  # noqa: E731
    parts = [f'<text x="{x0}" y="26" class="sk-head">{esc(title)}</text>']
    for tick in range(lo, hi + 1, 5):
        parts.append(
            f'<line x1="{sx(tick):.1f}" y1="46" x2="{sx(tick):.1f}" y2="{H - 30}" stroke="{"#192e2b" if tick == 0 else "#c9c9bc"}" stroke-width="{2 if tick == 0 else 1}"/>'
        )
        parts.append(
            f'<text x="{sx(tick):.1f}" y="{H - 12}" text-anchor="middle" class="axis-t">{sgn(tick, 0)}</text>'
        )
    y = 62
    for r in rows:
        parts.append(
            f'<text x="{x0 - 14}" y="{y + 9}" text-anchor="end" class="sk-label">{esc(r["rotulo"])}</text>'
        )
        for k, (val, color, lab) in enumerate(
            (("publicado", GREEN, "publicado"), ("sensibilidade", GOLD, "reponderado"))
        ):
            v = r[val]
            yy = y + k * 15
            left, right = (sx(0), sx(v)) if v >= 0 else (sx(v), sx(0))
            parts.append(
                f'<rect x="{left:.1f}" y="{yy}" width="{max(right - left, 1):.1f}" height="12" fill="{color}"><title>{esc(r["rotulo"])}, {lab}: {sgn(v)} pontos</title></rect>'
            )
            parts.append(
                f'<text x="{(right if v >= 0 else left) + (6 if v >= 0 else -6):.1f}" y="{yy + 10}" text-anchor="{"start" if v >= 0 else "end"}" class="axis-t">{sgn(v)}</text>'
            )
        y += rowh
    parts.append(
        f'<rect x="{x0}" y="{H - 52}" width="14" height="10" fill="{GREEN}"/><text x="{x0 + 20}" y="{H - 43}" class="axis-t">diferença publicada (direita menos esquerda)</text>'
    )
    parts.append(
        f'<rect x="{x0 + 330}" y="{H - 52}" width="14" height="10" fill="{GOLD}"/><text x="{x0 + 350}" y="{H - 43}" class="axis-t">diferença com a renda da PNAD 2025</text>'
    )
    return (
        f'<svg id="{ident}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        + "".join(parts)
        + "</svg>"
    )


def grouped_svg(groups, series, ident, title, maxv=70):
    """groups: [(label, {serie: value})]; series: [(name, color)]."""
    W = 1000
    n = len(groups)
    gw = (W - 120) / n
    bw = min(34, (gw - 24) / len(series))
    H = 330
    base = 270
    parts = [f'<text x="60" y="26" class="sk-head">{esc(title)}</text>']
    for tick in range(0, maxv + 1, 10):
        yy = base - (base - 50) * tick / maxv
        parts.append(
            f'<line x1="60" y1="{yy:.1f}" x2="{W - 40}" y2="{yy:.1f}" stroke="#c9c9bc" stroke-width="1"/><text x="52" y="{yy + 4:.1f}" text-anchor="end" class="axis-t">{tick}</text>'
        )
    for gi, (label, values) in enumerate(groups):
        gx = 60 + gi * gw + 12
        for si, (name, color) in enumerate(series):
            v = values.get(name)
            if v is None:
                continue
            h = (base - 50) * v / maxv
            x = gx + si * (bw + 4)
            parts.append(
                f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{max(h, 1):.1f}" fill="{color}"><title>{esc(label)}, {esc(name)}: {fmt(v, 1)}%</title></rect>'
            )
            parts.append(
                f'<text x="{x + bw / 2:.1f}" y="{base - h - 5:.1f}" text-anchor="middle" class="axis-t">{fmt(v, 0 if float(v).is_integer() else 1)}</text>'
            )
        parts.append(
            f'<text x="{gx + (len(series) * (bw + 4)) / 2:.1f}" y="{base + 20}" text-anchor="middle" class="sk-label">{esc(label)}</text>'
        )
    lx = 60
    for name, color in series:
        parts.append(
            f'<rect x="{lx}" y="{H - 24}" width="14" height="10" fill="{color}"/><text x="{lx + 20}" y="{H - 15}" class="axis-t">{esc(name)}</text>'
        )
        lx += 24 + 8 * len(name) + 30
    return (
        f'<svg id="{ident}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        + "".join(parts)
        + "</svg>"
    )


def scatter_svg(regs, ident):
    W, H = 1000, 520
    x0, x1, y0, y1 = 90, 960, 460, 50
    xs = [r["renda_media_municipal_ponderada_pop"] for r in regs]
    ys = [100 * r["jair_2022_2"] / r["2022_PRESIDENTE_2_total"] for r in regs]
    xmin, xmax = min(xs) * 0.95, max(xs) * 1.05
    ymin, ymax = 40, 75
    sx = lambda v: x0 + (x1 - x0) * (v - xmin) / (xmax - xmin)  # noqa: E731
    sy = lambda v: y0 - (y0 - y1) * (v - ymin) / (ymax - ymin)  # noqa: E731
    parts = []
    for t in (40, 50, 60, 70):
        parts.append(
            f'<line x1="{x0}" y1="{sy(t):.1f}" x2="{x1}" y2="{sy(t):.1f}" stroke="{"#192e2b" if t == 50 else "#c9c9bc"}" stroke-width="{1.5 if t == 50 else 1}"/><text x="{x0 - 8}" y="{sy(t) + 4:.1f}" text-anchor="end" class="axis-t">{t}%</text>'
        )
    for t in range(1000, 4001, 250):
        if xmin <= t <= xmax:
            parts.append(
                f'<line x1="{sx(t):.1f}" y1="{y0}" x2="{sx(t):.1f}" y2="{y1}" stroke="#c9c9bc" stroke-width="1"/><text x="{sx(t):.1f}" y="{y0 + 18}" text-anchor="middle" class="axis-t">R$ {fmt(t)}</text>'
            )
    emax = max(r["eleitorado"] for r in regs)
    order = sorted(range(len(regs)), key=lambda i: xs[i])
    for rank, i in enumerate(order):
        r, x, y = regs[i], xs[i], ys[i]
        rad = 10 + 46 * math.sqrt(r["eleitorado"] / emax)
        label_y = sy(y) - rad - 6 if rank % 2 == 0 else sy(y) + rad + 15
        parts.append(
            f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{rad:.1f}" fill="{GREEN}" fill-opacity="0.55" stroke="{INK}" stroke-width="1"><title>{esc(r["nome"])}: renda R$ {fmt(x)}, Bolsonaro {fmt(y, 1)}% no 2º turno de 2022, {fmt(r["eleitorado"])} eleitores</title></circle>'
        )
        parts.append(
            f'<text x="{sx(x):.1f}" y="{label_y:.1f}" text-anchor="middle" class="axis-t halo">{esc(r["nome"])}</text>'
        )
    parts.append(
        f'<text x="{(x0 + x1) / 2}" y="{H - 8}" text-anchor="middle" class="axis-t">Renda domiciliar per capita média do Censo 2022, ponderada pela população</text>'
    )
    parts.append(
        f'<text x="18" y="{(y0 + y1) / 2}" text-anchor="middle" transform="rotate(-90 18 {(y0 + y1) / 2})" class="axis-t">Bolsonaro no 2º turno de 2022</text>'
    )
    return (
        f'<svg id="{ident}" viewBox="0 0 {W} {H}" role="img" aria-label="Renda e voto nas onze regiões intermediárias"><title>Renda e voto nas onze regiões</title>'
        + "".join(parts)
        + "</svg>"
    )


def idx_cell(v):
    cls = "idx-up" if v >= 100 else "idx-dn"
    return f'<td class="num {cls}">{fmt(v)}</td>'


NEWS = [
    (
        "Metrópole de São Paulo",
        "Mobilidade e previsibilidade",
        "A cobertura da paralisação da CPTM em 4 de agosto registra efeitos sobre deslocamentos. O episódio documenta uma interrupção concreta; não mede, sozinho, a qualidade de todo o sistema.",
        "04/08/2026",
        "UOL",
        "https://noticias.uol.com.br/cotidiano/ultimas-noticias/2026/08/04/operacao-greve-cptm.ghtm",
    ),
    (
        "Campinas",
        "Continuidade do abastecimento",
        "A Ares-PCJ publicou interrupção programada da Sanasa para 18 de agosto. Manutenção anunciada não deve ser descrita como colapso hídrico: a questão observável é a informação ao usuário e a continuidade do serviço.",
        "Agosto/2026",
        "Ares-PCJ",
        "https://www.arespcj.com.br/conteudo/sanasa-campinas-interrupcao-programada1098",
    ),
    (
        "Baixada Santista",
        "Logística e execução de obras",
        "O termo de transferência de julho marca uma etapa contratual do túnel Santos e Guarujá. Projeto executivo, início de obras e entrega são marcos diferentes. O financiamento envolve esferas distintas de governo.",
        "07/07/2026",
        "Concessionária TSG",
        "https://tsgp.com.br/2026/07/07/tsg-concessionaria-assina-tti-e-avanca-com-o-tunel-santos-guaruja/",
    ),
    (
        "São José dos Campos",
        "Indústria e qualificação",
        "Notícia de agosto reúne vagas e bancos de talentos da Embraer. A existência de anúncios evidencia demanda de recrutamento; banco de talentos não equivale a contratação realizada.",
        "26/08/2026",
        "Notícias SJC",
        "https://noticiassjc.com.br/embraer-abre-dezenas-de-vagas-de-emprego-e-bancos-de-talentos-em-sao-jose/",
    ),
    (
        "Sorocaba",
        "Emprego industrial",
        "A abertura de 100 vagas na Toyota foi noticiada em agosto, com seleção sem exigência de experiência. É um fato localizado, distinto do saldo líquido de emprego de toda a região.",
        "25/08/2026",
        "Canal Estado SP",
        "https://www.canalestadosp.com.br/noticia/toyota-tem-100-vagas-abertas-em-sorocaba-e-selecao-nao-exige-experiencia-a3809c8b",
    ),
    (
        "Ribeirão Preto",
        "Calor e saúde pública",
        "O Jornal da USP discute os efeitos de variações climáticas e eventos extremos na saúde em Ribeirão Preto. A evidência liga exposição ambiental e capacidade dos serviços; não estabelece efeito eleitoral.",
        "12/08/2026",
        "Jornal da USP",
        "https://jornal.usp.br/campus-ribeirao-preto/variacoes-climaticas-e-eventos-extremos-aumentam-riscos-a-saude-publica-em-ribeirao-preto/",
    ),
    (
        "Araraquara e São Carlos",
        "Produção e mercado de trabalho",
        "O balanço econômico do segundo trimestre reúne superávit comercial e aumento do número de empresas, junto de saldo negativo de empregos no período. Exportação, abertura de empresas e emprego não são indicadores intercambiáveis.",
        "18/08/2026",
        "Jornal de Araraquara",
        "https://jornaldeararaquara.com.br/araraquara-encerra-2o-trimestre-com-superavit-de-us-17058-milhoes-e-saldo-positivo-de-945-empresas/",
    ),
    (
        "São José do Rio Preto e Araçatuba",
        "Estiagem, umidade e incêndios",
        "A cobertura de 28 de agosto registra alerta de calor e baixa umidade para o interior. Alerta meteorológico é previsão e orientação preventiva, não balanço de danos já ocorridos.",
        "28/08/2026",
        "Folha",
        "https://www1.folha.uol.com.br/cotidiano/2026/08/defesa-civil-alerta-para-umidade-critica-e-calor-extremo-no-interior-de-sp.shtml",
    ),
    (
        "Bauru e entorno",
        "Capacidade hospitalar",
        "A prefeitura de Duartina informou contratação de médicos para o Hospital Santa Luzia. Trata-se de anúncio do prestador público; efeitos sobre espera e desfechos exigem indicadores posteriores.",
        "10/08/2026",
        "Prefeitura de Duartina",
        "https://www.duartina.sp.gov.br/noticia/print-noticia/2603/hospital-santa-luzia-contrata-novos-medicos-para-mudancas-que-prometem-elevar-a-qualidade-do-atendimento/",
    ),
    (
        "Marília e Presidente Prudente",
        "Exposição ambiental e serviços de saúde",
        "O alerta de baixa umidade alcança o oeste paulista. Em Prudente, a cobertura do Agosto Laranja registra ação de conscientização sobre esclerose múltipla e serviços de reabilitação. São pautas diferentes, sem hierarquia regional inferida.",
        "31/08/2026",
        "Diário de Prudente",
        "https://www.diariodeprudente.com/centro-de-reabilitacao-encerra-agosto-laranja-com-acao-de-conscientizacao-sobre-esclerose-multipla1/",
    ),
    (
        "Vale do Ribeira",
        "Agricultura e educação técnica",
        "O IFSP Registro anunciou renovação de parceria com CoopercentralVR e Abavar. A cooperação aproxima ensino, pesquisa e organizações agrícolas. A existência da parceria não mede sua cobertura ou impacto econômico.",
        "27/08/2026",
        "IFSP Registro",
        "https://rgt.ifsp.edu.br/portal/sobre-o-campus/outras-noticias/223-snct/snct-2026/2850-ifsp-registro-renova-parceria-com-coopercentralvr-e-abavar",
    ),
]


# ------------------------------------------------------------------ capítulos
def ch_tese():
    totalpop = sum(r["populacao"] for r in C)
    flips = [r for r in C if r["virada"] == "Jair → PT"]
    flipv = {
        k: sum(r[k] for r in flips)
        for k in ("jair_2018_2", "jair_2022_2", "pt_2018_2", "pt_2022_2", "populacao")
    }
    groups = [
        (
            "547",
            "Bolsonaro nas duas eleições",
            "Maioria dos municípios, sem equivalência com maioria da área urbana ou da população.",
            "observed",
        ),
        (
            "83",
            "Bolsonaro → Lula",
            f"{fmt(flipv['populacao'] / totalpop * 100, 1)}% da população do Censo 2022. Nenhuma virada ocorreu na direção inversa.",
            "observed",
        ),
        (
            "14",
            "PT nas duas eleições",
            "Haddad venceu em 2018 e Lula em 2022.",
            "observed",
        ),
        (
            "1",
            "Empate em Guará",
            "5.529 votos para cada candidato em 2022. Empate é uma categoria própria.",
            "limit",
        ),
    ]
    body = (
        '<div class="metrics four">'
        + "".join(
            f'<article>{stamp(k, "TSE observado" if k == "observed" else "Exceção")}<strong>{n}</strong><h3>{t}</h3><p>{s}</p></article>'
            for n, t, s, k in groups
        )
        + "</div>"
    )
    rows = []
    for yr, turn in [(2018, 1), (2018, 2), (2022, 1), (2022, 2)]:
        total = sum(D["totais_nominais"][f"{yr}_PRESIDENTE_{turn}"].values())
        b = sum(r[f"jair_{yr}_{turn}"] for r in C)
        pt_votes = sum(r[f"pt_{yr}_{turn}"] for r in C)
        rows.append(
            [
                f"{yr} · {turn}º",
                fmt(b),
                fmt(b / total * 100, 2) + "%",
                "Haddad" if yr == 2018 else "Lula",
                fmt(pt_votes),
                fmt(pt_votes / total * 100, 2) + "%",
            ]
        )
    body += table(
        ["Eleição", "Bolsonaro: votos", "% válidos", "PT", "Votos", "% válidos"], rows
    )
    body += '<div class="thesis-band"><span>O mecanismo</span><b>Bolsonaro perdeu 1,09 milhão de votos no estado entre os dois segundos turnos.</b><b>O PT ganhou 3,05 milhões.</b><p>Nos 83 municípios de virada, Bolsonaro perdeu 662.840 votos e Lula recebeu 1.868.006 a mais que Haddad. O ganho petista responde por 73,8% da mudança aritmética da margem e a queda de Bolsonaro por 26,2%. Na capital, Bolsonaro passou de 3.694.834 para 3.191.484 votos; o PT, de 2.424.125 para 3.677.921. Essas parcelas não identificam novos eleitores, migração individual, abstenção ou conversão.</p></div><p class="note">Fonte: TSE, votação nominal por município e zona, 2018 e 2022; IBGE, Censo 2022. Valores recalculados a partir dos arquivos públicos.</p>'
    return chapter(
        1,
        "historia",
        "A maioria permaneceu. <em>A vantagem encolheu.</em>",
        "Bolsonaro passou de 67,97% para 55,24% dos votos válidos paulistas no segundo turno: queda de 12,73 pontos percentuais. São Paulo continua sendo o maior colégio da direita, e é o lugar onde ela mais perdeu volume.",
        body,
    )


def ch_economia():
    totalpib = sum(r["pib_2023"] for r in C)
    body = '<div class="ledger">'
    body += f"<div><span>PIB municipal somado, 2023</span><b>R$ {fmt(totalpib / 1e12, 2)} tri</b><small>preços correntes; não é renda das famílias</small></div>"
    body += f'<div><span>Renda domiciliar per capita</span><b>R$ {fmt(A["renda_pc_media_todos_abril_2026"]["media"])}</b><small>PNAD anual 2025, preços de abril de 2026 · IC 95%: R$ {fmt(A["renda_pc_media_todos_abril_2026"]["low"])} a {fmt(A["renda_pc_media_todos_abril_2026"]["high"])}</small></div>'
    body += f'<div><span>Desocupação 16+</span><b>{fmt(Q["desocupacao_forca_trabalho_pct"]["pct"], 2)}%</b><small>PNAD 1º tri 2026 · IC 95%: {fmt(Q["desocupacao_forca_trabalho_pct"]["low"], 2)} a {fmt(Q["desocupacao_forca_trabalho_pct"]["high"], 2)}</small></div>'
    body += f'<div><span>Renda média do trabalho</span><b>R$ {fmt(Q["renda_media_trabalho_ocupados_abril_2026"]["media"])}</b><small>ocupados 16+, abril de 2026</small></div></div>'
    body += (
        '<div class="split"><article><h3>Renda domiciliar de pessoas com 16 anos ou mais</h3>'
        + bars([(k, v["pct"]) for k, v in A["renda_domiciliar_16_mais"].items()])
        + '<p class="note">Renda conhecida, ponderada por pessoas; salário mínimo-alvo de R$ 1.621. É a régua usada no capítulo 9 para pesar as pesquisas.</p></article><article><h3>Renda per capita nos domínios disponíveis</h3>'
        + table(
            ["Domínio PNAD", "Média em R$", "IC 95%"],
            [
                [
                    k,
                    fmt(v["renda_pc_media_abril_2026"]["media"]),
                    fmt(v["renda_pc_media_abril_2026"]["low"])
                    + " a "
                    + fmt(v["renda_pc_media_abril_2026"]["high"]),
                ]
                for k, v in A["territorios"].items()
            ],
        )
        + '<p class="plain">A capital tem renda per capita 62,6% maior que o restante da região metropolitana e 42,4% maior que o interior. O interior fora da RM reúne 53,2% da população estimada.</p></article></div>'
    )
    body += (
        '<p>A PNAD atualiza o estado e os domínios identificáveis na base. Ela não autoriza estimar renda em cada um dos 645 municípios: para isso usamos o Censo 2022. Escolaridade, no recorte 16+, é 25,62% até fundamental completo, 43,76% médio incompleto ou completo e 30,63% superior incompleto ou completo. Superior aqui não significa diploma concluído.</p><p class="note">Fonte: IBGE, PIB dos Municípios 2023 e PNADC anual 2025 visita 1 / trimestral 2026 T1. Pesos V1032/V1028 e 200 réplicas. '
        + link("assets/sp_092026_pnad.json", "Estimativas, intervalos e método")
        + ".</p>"
    )
    return chapter(
        2,
        "economia",
        "Uma potência econômica <em>com rendas muito diferentes.</em>",
        "Datas e universos estão separados: Censo 2022, PIB 2023, renda anual 2025 e trabalho no primeiro trimestre de 2026.",
        body,
        True,
    )


def ch_mapa():
    opts = [
        ("virada", "Vencedores 2018 × 2022"),
        ("tar1_menos_bol1_pp", "Tarcísio menos Bolsonaro, 1º turno 2022 (pp)"),
        ("garcia1", "Rodrigo Garcia 2022 · 1º turno (%)"),
        ("jair_2018_2_pct", "Bolsonaro 2018 · 2º turno (%)"),
        ("jair_2022_2_pct", "Bolsonaro 2022 · 2º turno (%)"),
        ("tarcisio_2022_2_pct", "Tarcísio 2022 · 2º turno (%)"),
        ("mudanca_jair_pp", "Variação Bolsonaro 2018 → 2022 (pp)"),
        ("i_tarcisio", "Índice Tarcísio (100 = rende como Bolsonaro)"),
        ("i_derrite", "Índice Derrite"),
        ("i_salles", "Índice Salles"),
        ("i_prado", "Índice André do Prado"),
        ("i_carla", "Índice Carla Zambelli"),
        ("i_eduardo", "Índice Eduardo Bolsonaro"),
        ("i_pontes", "Índice Marcos Pontes"),
        ("eleitorado", "Eleitorado TSE 2026"),
        ("renda", "Renda per capita · Censo 2022 (R$)"),
        ("pib_pc_2023", "PIB per capita 2023 (R$)"),
    ]
    opts += [
        (f"{p}_{y}_1", f"{n} {y} · votos nominais")
        for p, n, years in [
            ("eduardo", "Eduardo Bolsonaro", [2018, 2022]),
            ("carla", "Carla Zambelli", [2018, 2022]),
            ("gil", "Gil Diniz", [2018, 2022]),
            ("mario", "Mário Frias", [2022]),
        ]
        for y in years
    ]
    body = (
        '<div class="controls"><label>Camada<select id="map-layer">'
        + "".join(f'<option value="{k}">{v}</option>' for k, v in opts)
        + '</select></label><label>Consultar município<select id="map-city"><option value="">Selecione um município</option>'
        + "".join(
            f'<option value="{r["id"]}">{esc(r["nome"])}</option>'
            for r in sorted(C, key=lambda r: r["nome"])
        )
        + "</select></label></div>"
    )
    body += (
        '<div class="map-layout"><div>'
        + svgmap()
        + '<p id="map-legend" class="legend"><span>Verde: Bolsonaro nas duas · Ocre: Bolsonaro → Lula · Vermelho: PT nas duas · Cinza: empate</span></p></div><aside id="map-readout" aria-live="polite"><span class="eyebrow">Atlas municipal</span><h3>645 histórias locais</h3><p>Toque no mapa ou escolha um município para consultar votos, eleitorado, renda e os índices dos carregadores.</p><p>A camada Tarcísio menos Bolsonaro mostra onde o governador rendeu acima do topo da chapa em 2022, que é o mapa do voto de Tarcísio que Flávio ainda precisa buscar. A camada Rodrigo Garcia mostra onde ficou o eleitor tucano de 2022.</p></aside></div><noscript><p>O mapa inicial funciona sem JavaScript. Para as demais camadas, consulte a tabela municipal e o CSV.</p></noscript><p class="note">Fonte: TSE e IBGE. Eleitorado: arquivo gerado em 01/07/2026, competência junho. Votos legislativos são nominais recebidos, separados dos votos de legenda e da situação jurídica atual. Índices definidos no capítulo 15.</p>'
    )
    return chapter(
        3,
        "mapa",
        "O território, <em>em vinte e quatro camadas.</em>",
        "A consulta combina resultado, mudança histórica, contexto econômico e o rendimento relativo de cada nome da direita. Cada cargo conserva seu próprio denominador.",
        body,
    )


def ch_regioes():
    regs = sorted(D["regioes"], key=lambda r: -r["eleitorado"])
    creg = {r["regiao"]: r for r in CARR["regioes"]}
    body = (
        '<div class="chart-shell">'
        + scatter_svg(regs, "region-scatter")
        + '<p class="note">Círculo proporcional ao eleitorado de 2026. A linha de 50% separa maioria e minoria de Bolsonaro no 2º turno de 2022. A região de São Paulo, com 40% do eleitorado, é a única abaixo da linha.</p></div>'
    )
    body += table(
        [
            "Região intermediária IBGE",
            "Mun.",
            "Eleitorado 2026",
            "Bolsonaro 2018 · 2º",
            "Bolsonaro 2022 · 2º",
            "Tarcísio 2022 · 2º",
            "Tarcísio menos Bolsonaro · 1º",
            "PIB 2023 · R$ bi",
        ],
        [
            [
                r["nome"],
                r["municipios"],
                fmt(r["eleitorado"]),
                fmt(100 * r["jair_2018_2"] / r["2018_PRESIDENTE_2_total"], 2) + "%",
                fmt(100 * r["jair_2022_2"] / r["2022_PRESIDENTE_2_total"], 2) + "%",
                fmt(100 * r["tarcisio_2022_2"] / r["2022_GOVERNADOR_2_total"], 2) + "%",
                sgn(creg[r["nome"]]["tar1_menos_bol1_pp"], 2) + " pp",
                fmt(r["pib_2023"] / 1e9, 1),
            ]
            for r in regs
        ],
    )
    body += (
        "<p>A região intermediária de São Paulo reúne "
        + fmt(regs[0]["eleitorado"] / D["eleitorado"]["total"] * 100, 1)
        + '% do eleitorado estadual e é a única em que Bolsonaro ficou abaixo de 50% em 2022. Nas dez restantes, ele venceu com folga, e em todas Tarcísio rendeu no 1º turno abaixo do que Bolsonaro rendeu: a coluna de diferença é negativa em toda a tabela porque o governador teve 42,32% contra 47,71% do presidente na mesma cédula, com Rodrigo Garcia levando 18,4%. A leitura relativa, no capítulo 15, corrige essa escala.</p><p class="note">Regiões geográficas intermediárias do IBGE; percentuais agregados por soma de votos, nunca média simples dos percentuais municipais.</p>'
    )
    return chapter(
        4,
        "regioes",
        "Onze regiões. <em>Nenhuma é homogênea.</em>",
        "A divisão do IBGE permite fechar os 645 municípios sem sobreposição. Renda e voto andam juntos na metrópole e se separam no interior rico, que é de direita com renda abaixo da capital.",
        body,
    )


def ch_cidades():
    biggest = sorted(C, key=lambda r: -r["eleitorado"])[:20]
    cm = {m["id"]: m for m in CARR["municipios"]}
    body = table(
        [
            "Município",
            "Eleitorado",
            "Vencedores 2018 → 2022",
            "Bolsonaro 2022 · 2º",
            "Tarcísio 2022 · 2º",
            "Tarcísio menos Bolsonaro · 1º",
            "Garcia 2022 · 1º",
        ],
        [
            [
                r["nome"],
                fmt(r["eleitorado"]),
                r["virada"],
                fmt(r["jair_2022_2_pct"], 2) + "%",
                fmt(r["tarcisio_2022_2_pct"], 2) + "%",
                sgn(cm[r["id"]]["tar1_menos_bol1_pp"], 2) + " pp",
                fmt(cm[r["id"]]["garcia1"], 1) + "%",
            ]
            for r in biggest
        ],
    )
    body += (
        "<p>As vinte maiores cidades somam "
        + fmt(100 * sum(r["eleitorado"] for r in biggest) / D["eleitorado"]["total"], 1)
        + '% do eleitorado. Em todas elas Tarcísio rendeu abaixo de Bolsonaro no 1º turno de 2022, e a distância é maior justamente nas cidades em que Rodrigo Garcia foi mais votado: o eleitor tucano de 2022 votou Bolsonaro para presidente e Garcia para governador, e no 2º turno foi para Tarcísio. Esse eleitor existe, tem endereço e é o objeto do capítulo 11.</p><p class="note">Seleção objetiva: os vinte maiores eleitorados no arquivo do TSE de julho de 2026. Ambos os percentuais de voto do 2º turno são de 2022.</p>'
    )
    return chapter(
        5,
        "cidades",
        "As vinte maiores cidades <em>por eleitorado.</em>",
        "Uma forma transparente de examinar a concentração demográfica. Metade do estado cabe em vinte urnas.",
        body,
    )


def ch_nomes():
    names = [
        ("Eduardo Bolsonaro", "eduardo", "Federal", [2018, 2022]),
        ("Carla Zambelli", "carla", "Federal", [2018, 2022]),
        ("Mário Frias", "mario", "Federal", [2022]),
        ("Gil Diniz", "gil", "Estadual", [2018, 2022]),
    ]
    rows = []
    for name, key, cargo, years in names:
        vals = {y: sum(r.get(f"{key}_{y}_1", 0) for r in C) for y in years}
        rows.append(
            [
                name,
                cargo,
                (
                    fmt(vals[2018])
                    if 2018 in vals
                    else "Sem candidatura neste levantamento"
                ),
                fmt(vals[2022]),
                (
                    fmt((vals[2022] / vals[2018] - 1) * 100, 1) + "%"
                    if 2018 in vals
                    else "Não comparável"
                ),
            ]
        )
    body = table(
        ["Nome", "Deputado", "2018 · votos", "2022 · votos", "Variação nominal"], rows
    )
    est = CARR["estado"]
    body += '<div class="ledger">'
    body += f'<div><span>Marcos Pontes · Senado 2022</span><b>{fmt(est["pontes"], 1)}%</b><small>10.714.913 votos nominais; Bolsonaro fez 47,71% no 1º turno</small></div>'
    body += f'<div><span>Tarcísio · governador 1º turno</span><b>{fmt(est["tarcisio"], 1)}%</b><small>9.881.995 votos; Rodrigo Garcia ficou com {fmt(est["garcia"], 1)}%</small></div>'
    body += f'<div><span>Ricardo Salles · federal</span><b>{fmt(est["salles"], 2)}%</b><small>640.918 votos nominais</small></div>'
    body += f'<div><span>Guilherme Derrite · federal</span><b>{fmt(est["derrite"], 2)}%</b><small>239.772 votos; hoje candidato ao Senado</small></div></div>'
    body += '<p>Eduardo caiu de 1,84 milhão para 741,7 mil votos; Carla passou de 76,3 mil para 946,2 mil. Essas mudanças simultâneas não demonstram que eleitores de um migraram para a outra. Pontes é o único nome da direita paulista que superou Bolsonaro na mesma cédula: 49,68% contra 47,71%, com Márcio França dividindo o campo adversário.</p><h3>Governo: porcentagens próximas, contagens diferentes</h3><p>No segundo turno de 2022, Tarcísio recebeu <b>13.480.643 votos, 55,27%</b>; Bolsonaro, <b>14.216.587, 55,24%</b>. São 735.944 votos de diferença e apenas 0,03 ponto na participação. O total de votos válidos para governo é menor: percentuais quase iguais não provam que sejam os mesmos eleitores. A Atlas mediu isso quatro anos depois: 98,0% dos eleitores de Bolsonaro em 2022 votam Tarcísio no 2º turno de 2026, e 4,8% dos eleitores de Lula também (p. 14).</p><p class="note">TSE, QT_VOTOS_NOMINAIS. O registro de votos recebidos é histórico; não é afirmação sobre mandato, elegibilidade ou validade jurídica atual.</p>'
    return chapter(
        6,
        "nomes",
        "O voto de cada nome <em>tem sua própria escala.</em>",
        "Comparar deputados, senador, governador e presidente exige separar cargo, ano, tamanho do eleitorado e denominador. O capítulo 15 faz essa comparação com uma régua única.",
        body,
        True,
    )


def ch_pesquisas():
    rows = []
    for p in P["pesquisas"]:

        def score(k, poll=p):
            return (
                " × ".join(fmt(v, 1) for v in poll[k])
                if k in poll
                else "Não disponível"
            )

        rows.append(
            [
                link(P["urls"][p["id"]], p["nome"]),
                p["campo"],
                score("governo"),
                score("governo2"),
                score("presidente"),
                score("presidente2"),
            ]
        )
    body = table(
        [
            "Instituto",
            "Campo · 2026",
            "Gov. 1º · T × H",
            "Gov. 2º · T × H",
            "Pres. 1º · F × L",
            "Pres. 2º · F × L",
        ],
        rows,
    )
    groups = []
    for p in P["pesquisas"]:
        if "governo2" in p:
            groups.append(
                (
                    p["nome"] + " · gov. 2º",
                    {"Tarcísio": p["governo2"][0], "Haddad": p["governo2"][1]},
                )
            )
    for p in P["pesquisas"]:
        if "presidente2" in p:
            groups.append(
                (
                    p["nome"] + " · pres. 2º",
                    {"Flávio": p["presidente2"][0], "Lula": p["presidente2"][1]},
                )
            )
    body += (
        '<div class="chart-shell">'
        + grouped_svg(
            groups,
            [
                ("Tarcísio", GREEN),
                ("Haddad", RED),
                ("Flávio", GOLD),
                ("Lula", "#7a2e30"),
            ],
            "poll-chart",
            "Segundos turnos publicados, em % dos votos totais",
        )
        + '<p class="note">T = Tarcísio; H = Haddad; F = Flávio; L = Lula. Votos totais em %, com não escolha fora dos pares. Real Time inclui Marçal no 1º turno e é a única com Lula à frente no 2º turno presidencial em SP; o PDF segue pendente. A Quaest não publica 2º turno presidencial no relatório estadual.</p></div>'
    )
    body += '<div class="callout"><h3>Tarcísio rende acima de Flávio em todas as pesquisas que medem os dois.</h3><p>Datafolha: 54 × 35 no governo e 47 × 42 na Presidência, uma distância de 19 contra 5. Atlas: 53,2 × 42,6 e 46,8 × 43,3, 10,6 contra 3,5. Real Time: 52 × 35 no 1º turno estadual e 44 × 49 no 2º presidencial. A diferença entre o governador e o candidato a presidente, no mesmo estado e na mesma amostra, é o objeto dos capítulos 10 e 11.</p></div>'
    body += table(
        ["Instituto", "Amostra", "Margem declarada", "Método", "Registro", "Documento"],
        [
            [
                p["nome"],
                fmt(p["n"]),
                "±" + fmt(p["me"], 1) + " pp",
                p["metodo"],
                p["registro"],
                p["status"] + "; p. " + p["paginas"],
            ]
            for p in P["pesquisas"]
        ],
    )
    body += "<p>O corte desta revisão é 5 de setembro de 2026. Veritá de julho foi localizada em notícia, mas o denominador do placar 59,6 × 40,4 para governo requer confirmação; por isso não integra a tabela comparável. Não substituímos resultados de SP por pesquisa nacional.</p>"
    body += (
        '<p class="note">Complementos: '
        + link(
            "https://www.poder360.com.br/poder-eleicoes-2026/datafolha-flavio-tem-47-contra-42-de-lula-no-2o-turno-em-sp/",
            "Datafolha presidencial em SP, Poder360, 22/08",
        )
        + " · "
        + link(P["urls"]["datafolha_pres"], "Folha, 22/08")
        + " · "
        + link(P["urls"]["rt_pres"], "Real Time presidencial, Metrópoles")
        + " · "
        + link(P["urls"]["verita"], "Veritá, notícia de julho")
        + ".</p>"
    )
    return chapter(
        7,
        "pesquisas",
        "Cinco institutos, <em>um padrão e uma exceção.</em>",
        "Tarcísio aparece à frente de Haddad em todas as pesquisas reunidas, e Flávio à frente de Lula em três de quatro. A exceção é a Real Time. As diferenças de campo, método, lista e não escolha impedem tratar a sequência como uma única série.",
        body,
    )


def ch_comparabilidade():
    body = (
        '<div class="split"><article><h3>Não escolha no 1º turno para governo</h3>'
        + bars([(p["nome"], p["nao_escolha_gov"]) for p in P["pesquisas"]])
        + '</article><article><h3>O contraste muda ao excluir a não escolha</h3><p>Na Quaest, Tarcísio tem 40% dos votos totais; excluídos 27% de não escolha, são aproximadamente <b>54,8% dos votos atribuídos a candidatos</b>. Na Atlas, 51,1% com 5,5% de não escolha equivalem a <b>54,1%</b>.</p><p>Haddad, pelo mesmo cálculo, passa de 27% a 37,0% na Quaest e de 39,9% a 42,2% na Atlas. A aproximação de um candidato não faz as pesquisas concordarem em tudo.</p><p class="note">Sensibilidade de denominador: valor / (100 − não escolha). Não é previsão de votos válidos na eleição nem reponderação da amostra.</p></article></div>'
    )
    body += (
        "<h3>Margem de um candidato não é margem da diferença</h3><p>A Atlas declara ±1 pp na página 5, enquanto seu catálogo informa ±2 pp. A discrepância precisa ser esclarecida. Sob amostragem aleatória simples, 1.810 entrevistas produziriam margem máxima de cerca de 2,30 pp. A diferença Flávio 46,8 × Lula 43,3, de 3,5 pontos, tem sob a mesma hipótese um intervalo de 95% de aproximadamente −0,9 a +7,9: contém o zero. O Datafolha, 47 × 42 com 1.610 entrevistas, dá de +0,1 a +9,9: não contém, por muito pouco. <b>Só o Datafolha autoriza a palavra lidera para Flávio em SP, e por uma margem de um décimo.</b></p>"
        + source("atlas", "p. 5")
        + '<p class="note">'
        + link("https://www.atlasintel.org/polls/exclusive-polls", "Catálogo Atlas")
        + ". Intervalo da diferença: 1,96 × raiz((p1+p2 − (p1−p2)²)/n), aproximação de amostragem aleatória simples. O desenho digital e a ponderação exigem explicação própria do instituto.</p>"
    )
    return chapter(
        8,
        "comparabilidade",
        "Antes de discutir tendência, <em>confira o denominador.</em>",
        "A não escolha para governo varia de 5,5% a 27%. Parte da distância entre percentuais resulta dessa diferença de resposta, e a margem da diferença é o teste que a manchete costuma pular.",
        body,
        True,
    )


def ch_renda():
    perf = R["perfis"]
    groups = [
        (lab, {k: v[i] for k, v in perf.items()})
        for i, lab in enumerate(["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"])
    ]
    body = (
        '<div class="split"><div class="chart-shell">'
        + grouped_svg(
            groups,
            [("PNAD 2025 (16+)", INK), ("Datafolha", GREEN), ("Quaest", GOLD)],
            "income-profile",
            "Perfil de renda familiar: amostra × PNAD, em %",
            50,
        )
        + f'<p class="note">Datafolha p. 24 e 27 ({fmt(R["datafolha"]["sem_renda_classificada"])} entrevistados sem faixa); Quaest p. 9; PNADC anual 2025, pessoas 16+, renda domiciliar em salários mínimos de R$ 1.621.</p></div>'
    )
    pa = R["perfil_atlas_brl5"]
    groups5 = [
        (lab, {k: v[i] for k, v in pa.items()})
        for i, lab in enumerate(
            ["Até 2 mil", "2 a 3 mil", "3 a 5 mil", "5 a 10 mil", "Mais de 10 mil"]
        )
    ]
    body += (
        '<div class="chart-shell">'
        + grouped_svg(
            groups5,
            [("PNAD 2025 (16+)", INK), ("Atlas", BLUE)],
            "income-profile-atlas",
            "Atlas × PNAD, faixas em reais",
            40,
        )
        + '<p class="note">Atlas p. 5. A Atlas usa faixas em reais; a PNAD foi cortada nas mesmas faixas, em preços de abril de 2026.</p></div></div>'
    )
    body += '<div class="grid-3"><article class="card"><span class="metric">37,8%</span><h3>até 2 SM no Datafolha</h3><p>Contra 23,2% na PNAD. A amostra de pontos de fluxo é 14,7 pontos mais pobre que o estado na faixa de baixo e tem 16,0% acima de 5 SM contra 34,6% na PNAD.</p></article><article class="card"><span class="metric gold">19%</span><h3>até 2 SM na Quaest</h3><p>Contra 23,2% na PNAD. A amostra domiciliar da Quaest é ligeiramente mais rica que o estado; a distância é de 4 pontos.</p></article><article class="card"><span class="metric red">25,7%</span><h3>acima de R$ 10 mil na Atlas</h3><p>Contra 19,8% na amostra da Atlas. A Atlas também é mais pobre que a PNAD nas duas faixas de baixo, 13,0 e 12,7 contra 10,1 e 7,9.</p></article></div>'
    rows = []
    for inst, lab in (
        ("datafolha", "Datafolha"),
        ("quaest", "Quaest"),
        ("atlas", "Atlas"),
    ):
        for q, qlab in (
            ("gov1", "governo 1º turno"),
            ("gov2", "governo 2º turno"),
            ("pres1", "Presidência 1º turno"),
            ("pres2", "Presidência 2º turno"),
        ):
            b = R[inst].get(q)
            if not b:
                continue
            rows.append(
                {
                    "rotulo": f"{lab} · {qlab}",
                    "publicado": b["diferenca_publicada"],
                    "sensibilidade": b["diferenca_sensibilidade"],
                }
            )
    body += (
        '<div class="chart-shell">'
        + diverging_svg(
            rows,
            "reweight-chart",
            "Diferença direita menos esquerda: publicada e com a renda da PNAD 2025",
        )
        + "</div>"
    )
    trows = []
    for inst, lab in (
        ("datafolha", "Datafolha"),
        ("quaest", "Quaest"),
        ("atlas", "Atlas"),
    ):
        for q, qlab in (
            ("gov1", "Governo 1º"),
            ("gov2", "Governo 2º"),
            ("pres1", "Presidência 1º"),
            ("pres2", "Presidência 2º"),
        ):
            b = R[inst].get(q)
            if not b:
                continue
            for name, c in b["candidatos"].items():
                trows.append(
                    [
                        f"{lab} · {qlab} · p. {b['pagina']}",
                        name,
                        fmt(c["publicado"], 1),
                        fmt(c["recomposto"], 2),
                        sgn(c["residuo_pp"], 2),
                        fmt(c["sensibilidade"], 2),
                        sgn(c["delta_pp"], 2),
                    ]
                )
    body += table(
        [
            "Pesquisa · pergunta",
            "Nome",
            "Publicado",
            "Recomposto",
            "Resíduo",
            "Com renda PNAD",
            "Efeito",
        ],
        trows,
        cls="compact",
    )
    body += '<div class="callout counter"><span class="stamp limit">O achado que contraria a tese</span><h3>A amostra mais pobre do Datafolha não esconde voto de direita. Na Atlas, a régua da PNAD tira a liderança de Flávio.</h3><p>A hipótese de partida era simples: amostra mais pobre que o estado subestima a direita, e a régua oficial a devolveria. O Datafolha é de fato 14,7 pontos mais pobre na faixa de baixo, mas o efeito é pequeno e vai nos dois sentidos: Tarcísio sobe de 54 para 55,3 e Haddad de 35 para 35,6 no 2º turno, porque entre os mais pobres do Datafolha a não escolha é de 20% contra 6% entre os mais ricos. Na Quaest o efeito é de menos de um ponto. Na Atlas o sinal inverte: Flávio faz 65,7% entre quem ganha até R$ 2 mil e 28,5% acima de R$ 10 mil, o oposto do que Quaest e Datafolha medem para a direita. Com a renda da PNAD, o 46,8 × 43,3 da Atlas vira 45,1 × 44,5, e o 39,9 × 36,0 do 1º turno vira empate em 37,4.</p><p>O que isso prova não é que Flávio perde em SP. Prova que <b>o gradiente de renda do voto de direita tem sinal oposto entre a pesquisa digital e as presenciais</b>, e que essa divergência é maior que qualquer efeito de reponderação. É um problema de método que os três institutos precisam explicar, e é um alerta para a campanha: a base pobre que a Atlas mede para Flávio não aparece nas urnas simuladas do Datafolha e da Quaest.</p></div>'
    body += "<h3>Controles de transcrição</h3>" + table(
        ["Fonte", "Controle", "Maior resíduo"],
        [
            [
                "Datafolha, p. 27 e 33",
                "Sexo, idade, escolaridade e renda; governo 1º e 2º",
                "0,87 pp",
            ],
            [
                "Atlas, p. 10, 14, 18 e 23",
                "Renda em cinco faixas; governo e Presidência",
                "0,25 pp",
            ],
            [
                "Quaest, p. 9, 24 e 79",
                "Renda em três faixas; governo e Presidência",
                "2,32 pp em Flávio, 1º turno: controle reprovado, registrado",
            ],
        ],
    )
    body += (
        '<p class="note">Método: para cada faixa, o voto publicado na faixa é mantido e só o peso da faixa é trocado pelo da PNAD; a sensibilidade é publicado + (reponderado − recomposto), para não herdar arredondamento. A ponderação dos institutos é conjunta e não publicada; isto é sensibilidade de uma margem, nunca voto corrigido. '
        + link("assets/sp_092026_camada2.json", "Base com todas as células")
        + ".</p>"
    )
    return chapter(
        9,
        "renda",
        "A régua da renda <em>muda pouco, e não para o lado esperado.</em>",
        "As três amostras têm perfis de renda diferentes da PNAD. Trocar o peso de cada faixa pelo peso oficial é a única sensibilidade que o relatório do instituto permite. O resultado contraria a hipótese de partida, e é publicado com o mesmo destaque.",
        body,
        True,
    )


def ch_fluxos():
    body = '<div class="flow-notes"><div><b>Nós sólidos</b><p>São as margens publicadas de cada instituto: o 2º turno estadual à esquerda e o presidencial à direita, na mesma amostra.</p></div><div><b>Fitas hachuradas</b><p>São estimativa por IPF. A prior é empírica: a Atlas cruza o voto de 2022 para governador com o voto presidencial de 2026 (p. 23), e essa proporção é o ponto de partida ajustado até fechar as margens de cada instituto.</p></div><div><b>O que sobrevive à troca da prior</b><p>Quanto Flávio recebe a menos que Tarcísio, quanto Lula recebe a mais que Haddad e quanto a não escolha cresce. Esses três números são impostos pelas margens. O corte fita a fita depende da prior e não deve ser tratado como medição.</p></div></div>'
    for i, f in enumerate(FLOWS):
        rb, es = f["robusto"], f["estimado"]
        body += (
            f'<div class="flow-shell"><div class="flow-head"><div>{stamp("observed", "Nós = margem publicada")} {stamp("estimated", "Fitas = IPF estimado")}</div><p class="flow-caption">{esc(f["nome"])}. {esc(f["fonte"])}.</p></div>'
            + sankey_svg(f, f"flow-{i}")
            + '<div class="flow-facts">'
        )
        body += f'<div><span>Imposto pelas margens</span><b>Flávio recebe {fmt(rb["diferenca_tarcisio_menos_direita_pp"], 1)} pontos a menos que Tarcísio</b><small>Lula recebe {sgn(rb["diferenca_esquerda_menos_haddad_pp"], 1)} sobre Haddad; não escolha {sgn(rb["variacao_nao_escolha_pp"], 1)}</small></div>'
        body += f'<div><span>Estimado por IPF</span><b>{fmt(es["tarcisio_para_direita_pct"], 1)}% do eleitor de Tarcísio vota Flávio</b><small>{fmt(es["tarcisio_para_esquerda_pct"], 1)}% vai a Lula ({fmt(es["tarcisio_para_esquerda_pontos"], 1)} pontos) e {fmt(es["tarcisio_para_nao_escolha_pct"], 1)}% anula ou não sabe ({fmt(es["tarcisio_para_nao_escolha_pontos"], 1)} pontos)</small></div>'
        body += f'<div><span>Fidelidade do outro lado</span><b>{fmt(es["haddad_para_esquerda_pct"], 1)}% do eleitor de Haddad vota Lula</b><small>{"1º turno: parte do eleitor de Tarcísio vai a Caiado, Zema, Renan e Cury" if f["tipo"] != "2T para 2T" else "a base petista não vaza"}</small></div></div></div>'
    body += '<div class="grid-3"><article class="card"><span class="metric">14,0%</span><h3>Datafolha: o vazamento vai para Lula</h3><p>Tarcísio 54 vira Flávio 47 e Haddad 35 vira Lula 42. Sete pontos saem de um lado e sete entram no outro, com a não escolha parada em 11 e 10. A pesquisa de pontos de fluxo mede um eleitor de Tarcísio que, sem Tarcísio, prefere Lula a Flávio.</p></article><article class="card"><span class="metric gold">13,2%</span><h3>Atlas: o vazamento vai para o branco</h3><p>Tarcísio 53,2 vira Flávio 46,8, mas Haddad 42,6 vira Lula 43,3, quase nada. A perda de 6,4 pontos aparece na não escolha, que sobe de 4,2 para 9,9. A pesquisa digital mede um eleitor de Tarcísio que, sem Tarcísio, não vota em ninguém.</p></article><article class="card"><span class="metric red">36,7%</span><h3>Quaest: a dispersão do 1º turno</h3><p>Sem 2º turno presidencial no relatório, o destino é o 1º turno: Tarcísio 47 vira Flávio 30. A prior da Atlas manda cerca de um quinto do eleitor de Tarcísio para Caiado, Zema, Renan e Cury, e é aí que o voto útil da direita ainda está por consolidar.</p></article></div>'
    body += '<div class="callout"><h3>O que as três pesquisas dizem juntas</h3><p>Em qualquer método, cerca de um em cada sete eleitores de Tarcísio no 2º turno não vota Flávio no 2º turno. A divergência entre os institutos não é sobre o tamanho do vazamento: é sobre o destino. Presencial, ele vira voto em Lula; digital, vira voto nulo. Para a campanha as duas leituras convergem numa só instrução: <b>o eleitor de Tarcísio que falta é conquistável, porque nem o Datafolha o dá como petista convicto nem a Atlas o dá como abstencionista convicto</b>. Ele está no meio, e o capítulo seguinte mostra onde.</p></div>'
    alt = E["atlas"]["cenarios_2t"]
    body += (
        "<h3>Cenários alternativos na mesma amostra da Atlas</h3>"
        + table(
            ["Adversário de Lula", "Adversário · %", "Lula · %", "Não escolha · %"],
            [
                [k, fmt(v[0], 1), fmt(v[1], 1), fmt(v[2], 1)]
                for k, v in alt.items()
                if k != "pagina"
            ],
        )
        + "<p>Lula quase não se move: 43,3, 41,1, 42,7 e 43,1. O bloco adversário rende 46,8 com Flávio, 45,4 com Caiado, 43,8 com Zema e 33,5 com Renan, e a diferença aparece na não escolha. É a mesma restrição observada nas pesquisas nacionais: a troca de líder custa ao campo, não rende ao incumbente. Flávio é o melhor nome da direita em SP por 1,4 ponto sobre Caiado.</p>"
        + source("atlas", "p. 21 a 24")
    )
    body += (
        '<p class="note">IPF: ajuste proporcional iterativo por mínima entropia cruzada contra a prior, até fechar as margens; origens reescaladas ao total do destino. Leitura agregada de massas de voto, nunca de trajetórias individuais. Matrizes, priors e notas em '
        + link("assets/sp_092026_camada2.json", "sp_092026_camada2.json")
        + ".</p>"
    )
    return chapter(
        10,
        "fluxos",
        "De Tarcísio para Flávio: <em>três institutos, um vazamento, dois destinos.</em>",
        "Nenhum dos três relatórios publica o cruzamento do voto estadual de 2026 com o presidencial de 2026. Os diagramas usam IPF para fechar exatamente as margens observadas sob uma prior medida pela Atlas no voto de 2022. As fitas são estimativa; os totais não.",
        body,
        False,
        True,
    )


def ch_vao():
    seg = VAO["segmentos"]
    groups_order = ["Sexo", "Idade", "Escolaridade", "Renda", "Religião", "Região"]
    rows = [s for g in groups_order for s in seg if s["grupo"] == g]
    body = '<div class="ledger"><div><span>Vão total na Atlas</span><b>6,4 pontos</b><small>Tarcísio 53,2 no 2º turno estadual, Flávio 46,8 no presidencial</small></div><div><span>Vão total no Datafolha</span><b>7,0 pontos</b><small>Tarcísio 54, Flávio 47</small></div><div><span>Desaprovação de Lula em SP</span><b>58%</b><small>Atlas p. 26; Flávio tem 46,8: teto endereçável de 11,2</small></div><div><span>Tarcísio merece reeleição</span><b>52,4%</b><small>Atlas p. 30; 42,4% dizem não</small></div></div>'
    body += (
        '<div class="chart-shell">'
        + lollipop_svg(
            rows,
            "gap-chart",
            "Tarcísio (governo, 2º turno) e Flávio (Presidência, 2º turno) por recorte da Atlas",
        )
        + '<p class="note">Atlas p. 14 e p. 23. Cada linha é um recorte da mesma amostra respondendo às duas perguntas. O número à direita é o vão. A margem de cada célula é maior que a do total e não está publicada por recorte.</p></div>'
    )
    top = sorted(rows, key=lambda r: -r["vao_tarcisio_flavio"])[:6]
    body += '<div class="grid-3">'
    for r in top[:3]:
        body += f'<article class="card"><span class="metric">{sgn(r["vao_tarcisio_flavio"])}</span><h3>{esc(r["segmento"])}</h3><p>Tarcísio {fmt(r["tarcisio"], 1)}, Flávio {fmt(r["flavio"], 1)}. Lula fica {sgn(r["ganho_lula_sobre_haddad"])} sobre Haddad e a não escolha salta {sgn(r["salto_nao_escolha"])}.</p></article>'
    body += "</div>"
    body += "<p>Os maiores vãos estão no <b>ensino superior</b> (10,9), nos <b>25 a 44 anos</b> (11,1 e 10,7), na <b>região metropolitana e Santos</b> (9,9) e entre <b>homens</b> (9,5). Não é o eleitor pobre nem o evangélico que falta a Flávio: é o eleitor de classe média escolarizada da metrópole, que aprova o governador e não transfere o voto. Na renda, o vão cresce com a faixa: 2,3 até R$ 2 mil, 8,0 acima de R$ 10 mil.</p>"
    voto22 = [s for s in seg if s["grupo"].startswith("Voto")]
    body += "<h3>O vão tem endereço: o voto de 2022</h3>" + table(
        [
            "Voto em 2022",
            "Recorte",
            "Tarcísio 2º",
            "Haddad 2º",
            "Flávio 2º",
            "Lula 2º",
            "Não escolha pres.",
            "Vão",
        ],
        [
            [
                s["grupo"].replace("Voto para ", "").replace(" em 2022", ""),
                s["segmento"],
                fmt(s["tarcisio"], 1),
                fmt(s["haddad"], 1),
                fmt(s["flavio"], 1),
                fmt(s["lula"], 1),
                fmt(s["nao_escolha_pres"], 1),
                sgn(s["vao_tarcisio_flavio"]),
            ]
            for s in voto22
        ],
        cls="compact",
    )
    body += '<div class="callout"><h3>Três origens medidas para o voto de Tarcísio que não é voto de Flávio</h3><p><b>O eleitor de Rodrigo Garcia em 2022.</b> Foram 4,3 milhões de votos, 18,4% do 1º turno estadual. Hoje 36,5% deles votam Tarcísio e 25,0% votam Flávio: vão de 11,5. No 1º turno presidencial, 31,9% deles escolhem Augusto Cury e 27,0% Lula; Flávio tem 11,0 (Atlas p. 19). É o maior reservatório de voto de direita não bolsonarista do estado, e ele está indo para um candidato de nicho.</p><p><b>O eleitor de Lula em 2022 que aprova o governador.</b> 4,8% dos eleitores de Lula votam Tarcísio no 2º turno; 0,8% votam Flávio. Pequeno em proporção, grande em volume: sobre 9,7 milhões de votos de Lula em SP, cada ponto vale quase 100 mil eleitores.</p><p><b>Quem anulou ou não votou em 2022.</b> Entre os que votaram branco ou nulo para presidente, Tarcísio tem 56,2% e Flávio 4,3%; 87,2% seguem anulando. Entre os que não votaram, Tarcísio 38,8 e Flávio 30,0.</p></div>'
    ideo = [s for s in seg if s["grupo"] == "Ideologia declarada"]
    body += (
        "<h3>O recorte que decide: antipetista e antibolsonarista ao mesmo tempo</h3>"
        + table(
            [
                "Ideologia declarada (Atlas)",
                "Tarcísio 2º",
                "Haddad 2º",
                "Flávio 2º",
                "Lula 2º",
                "Não escolha pres.",
                "Vão",
            ],
            [
                [
                    s["segmento"],
                    fmt(s["tarcisio"], 1),
                    fmt(s["haddad"], 1),
                    fmt(s["flavio"], 1),
                    fmt(s["lula"], 1),
                    fmt(s["nao_escolha_pres"], 1),
                    sgn(s["vao_tarcisio_flavio"]),
                ]
                for s in ideo
            ],
            cls="compact",
        )
    )
    body += "<p>Quem se declara ao mesmo tempo antipetista e antibolsonarista dá 51,9% a Tarcísio e 8,6% a Flávio, e 54,9% não escolhem ninguém no 2º turno presidencial. É o vão de 43,3 pontos, o maior de todo o relatório, e é o retrato do eleitor que sustenta o governador e recusa a marca. A Atlas não publica o tamanho desse grupo na amostra; a Quaest mede algo próximo: 37% querem um governador independente de Lula e de Flávio, 33% aliado de Flávio e 26% aliado de Lula (p. 33), e o apoio de Flávio a um candidato aumenta a chance de voto para 24% e diminui para 29% (p. 34), saldo de −5.</p>"
    body += (
        '<p class="note">Fonte: Atlas/Estadão p. 14, 19, 23, 26, 30; Quaest p. 33 e 34. Vão = teto endereçável, não previsão: aprovar o governador não é estar disponível para o candidato. '
        + link("assets/sp_092026_camada2.json", "Todos os recortes")
        + ".</p>"
    )
    return chapter(
        11,
        "vao",
        "O vão Tarcísio-Flávio <em>tem rosto, renda e voto anterior.</em>",
        "A Atlas responde a mesma amostra duas perguntas: em quem vota para governador no 2º turno e em quem vota para presidente no 2º turno. A diferença entre as duas respostas, recorte a recorte, é a medida mais direta que existe do voto que a direita paulista tem no estado e ainda não tem no país.",
        body,
    )


def ch_senado():
    body = table(
        [
            "Nome",
            "Datafolha · média das duas",
            "Quaest · média das duas",
            "Quaest · 1ª escolha",
            "Quaest · 2ª escolha",
            "Atlas · imagem +/−",
            "Atlas · rejeição",
        ],
        [
            [
                name,
                fmt(
                    P["senado_datafolha"].get(
                        "Ricardo Salles" if name == "Salles" else name, 0
                    )
                ),
                *[fmt(v) for v in vals],
                (
                    sgn(
                        E["atlas"]["imagem"]["valores"].get(
                            {"Salles": "Ricardo Salles"}.get(name, name), [0, 0, 0]
                        )[0]
                        - E["atlas"]["imagem"]["valores"].get(
                            {"Salles": "Ricardo Salles"}.get(name, name), [0, 0, 0]
                        )[2],
                        0,
                    )
                    if {"Salles": "Ricardo Salles"}.get(name, name)
                    in E["atlas"]["imagem"]["valores"]
                    else "Não medido"
                ),
                (
                    fmt(
                        E["atlas"]["rejeicao"]["valores"].get(
                            {"Salles": "Ricardo Salles"}.get(name, name), 0
                        ),
                        1,
                    )
                    + "%"
                    if {"Salles": "Ricardo Salles"}.get(name, name)
                    in E["atlas"]["rejeicao"]["valores"]
                    else "Não medido"
                ),
            ]
            for name, vals in P["senado_quaest"].items()
        ],
    )
    body += (
        "<p>Derrite é o único nome da direita com saldo de imagem positivo na Atlas (+7, com 20% que não sabem) e o menos rejeitado dos quinze medidos (30,2%). André do Prado tem 37% que não sabem avaliá-lo e saldo −1. No Datafolha, 79% da resposta espontânea para o Senado ainda está indefinida (p. 6). A eleição de Senado em SP é uma disputa de conhecimento, não de opinião, e as duas vagas premiam quem puxar voto junto com o topo da chapa.</p><p>As médias de duas escolhas somam 100% considerando candidatos e não escolha. Elas não são a proporção de entrevistados que citaram o nome ao menos uma vez. Em 2018, Major Olímpio recebeu 9.039.717 votos e Mara Gabrilli, 6.513.282; em 2022, Marcos Pontes recebeu 10.714.913. O número de vagas mudou entre as duas eleições.</p>"
        + source("datafolha", "p. 12 e 14")
        + source("quaest", "p. 61")
        + source("atlas", "p. 37 e 39")
    )
    return chapter(
        12,
        "senado",
        "Duas vagas, <em>e a direita tem o nome menos rejeitado.</em>",
        "O Senado tem disputa e denominador distintos. Não se pode somar votos de deputados ou popularidade presidencial para deduzir uma dupla vencedora, mas a imagem e a rejeição medidas mostram quem pode carregar a chapa.",
        body,
        True,
    )


def ch_temas():
    body = (
        '<div class="split"><article><h3>Quaest: o problema mais grave</h3>'
        + bars(list(P["temas_quaest"].items()))
        + source("quaest", "p. 105")
        + "</article><article><h3>Atlas: até três problemas</h3>"
        + bars([(k, v) for k, v in E["atlas"]["problemas"]["valores"].items()][:9])
        + source("atlas", "p. 41")
        + "</article></div>"
    )
    body += '<p>Violência e criminalidade lideram nas duas réguas, com distância de 12 pontos sobre o segundo tema na Quaest e de 23,5 na Atlas. Educação aparece em segundo na Atlas (35,9%) e em quarto na Quaest (6%): a diferença é da pergunta, não da opinião. A Atlas permite até três respostas; a Quaest pede o problema mais grave. Os valores não medem a mesma coisa e não devem ser usados para dizer que um tema cresceu de uma pesquisa para outra.</p><h3>Como os temas aparecem nas notícias locais</h3><p class="note">Seleção documental, não amostra representativa da imprensa nem medição de prioridades regionais. A pauta de cada corredor de campanha, no capítulo 16, usa outra seleção, com valor, devedor e destinatário.</p><div class="news-grid">'
    for region, title, copy, date, outlet, url in NEWS:
        body += f'<article><span class="eyebrow">{esc(region)}</span><h3>{esc(title)}</h3><p>{esc(copy)}</p><p class="note">{esc(date)} · {link(url, outlet)}</p></article>'
    body += (
        '</div><p class="note">Financiamento do túnel: '
        + link(
            "https://www.gov.br/portos-e-aeroportos/pt-br/assuntos/noticias/2026/03-1/governo-assina-emprestimo-do-banco-do-brasil-para-conclusao-das-obras-do-tunel-santos-guaruja",
            "Ministério de Portos e Aeroportos",
        )
        + ".</p>"
    )
    return chapter(
        13,
        "temas",
        "Segurança, saúde <em>e o cotidiano de cada região.</em>",
        "As pesquisas medem saliência estadual. As notícias dão exemplos locais, sem permitir deduzir a opinião de todos os moradores.",
        body,
    )


def ch_leitura():
    q = E["quaest"]
    body = '<div class="stance"><span class="stamp limit">Posição declarada</span><p>Deste capítulo em diante o dossiê tem lado, e o diz. As recomendações são dirigidas à campanha de Flávio Bolsonaro em São Paulo e aos nomes da direita paulista que carregam voto, a começar por Tarcísio. A regra da casa continua valendo dentro dele: cada movimento recomendado tem número e página ao lado, o juízo editorial está rotulado como juízo editorial, e o capítulo publica com o mesmo destaque o achado que contraria a própria tese. Esse achado está no capítulo 9 e volta no contraponto abaixo.</p></div>'
    items = [
        (
            "Fechar o vão antes de abrir frente nova",
            "Um em cada sete eleitores de Tarcísio no 2º turno não vota Flávio (Datafolha 14,0%, Atlas 13,2%). É o maior estoque de voto de direita disponível no país numa só unidade da federação: 7 pontos de 34,1 milhões de eleitores são 2,4 milhões de votos. Nenhuma outra frente rende isso.",
        ),
        (
            "Tarcísio abre, Flávio fecha, sempre nessa ordem",
            f"O governador tem 52% de aprovação e 42% de desaprovação (Atlas p. 26), 56% na Quaest (p. 36), imagem +10 e a menor rejeição dos nomes nacionais, 34,5%. Flávio tem imagem −13 e rejeição de 48,3%. Palanque que começa pelo nome nacional expõe a rejeição antes de mostrar a entrega. Na Quaest o endosso de Flávio tem saldo −5 ({q['endosso']['Flávio Bolsonaro'][0]} aumentam, {q['endosso']['Flávio Bolsonaro'][2]} diminuem, p. 34).",
        ),
        (
            "Falar com o eleitor de Rodrigo Garcia como quem pede voto, não como quem cobra fidelidade",
            "Foram 4,3 milhões de votos em 2022. Hoje 36,5% deles estão com Tarcísio e 25,0% com Flávio; no 1º turno, 31,9% escolhem Augusto Cury (Atlas p. 19 e 23). Esse eleitor é de centro-direita, de ensino superior e da metrópole, e quer competência administrativa, não bandeira. A pauta que funciona com ele é a do capítulo 16: trem, porto, tarifa e emprego, com número.",
        ),
        (
            "Trocar identidade por serviço na metrópole",
            "Na cidade de São Paulo Tarcísio faz 48,9 × 48,4 e Flávio 43,7 × 50,3; na RM e Santos, 50,3 × 48,9 e 40,4 × 51,2 (Atlas p. 14 e 23). O vão metropolitano é de 5,2 e 9,9 pontos. A capital e o colar são 47% do eleitorado e é onde a direita mais perdeu volume entre 2018 e 2022. O discurso nacional não converte aqui; a Linha 8 que descarrila e a barreira do PCC removida convertem.",
        ),
        (
            "Consolidar o 1º turno onde a direita se dispersa",
            "Na Quaest, Flávio tem 30 e o resto da direita (Caiado 4, Zema 3, Renan 3, Cury 2) tem 12, com 25 de não escolha (p. 75). Na Atlas o eleitor de Tarcísio de 2022 dá 78,8 a Flávio e 20,2 a Cury, Renan, Zema e Caiado (p. 19). Voto útil no 1º turno é o argumento que o eleitor de Tarcísio já aceitou para governador (99,1% de fidelidade) e ainda não aceitou para presidente.",
        ),
        (
            "Planejar para uma eleição que a Real Time diz que está perdida",
            "A Real Time é a única com Lula à frente em SP, 49 × 44, com 2.000 entrevistas telefônicas. O PDF está pendente e o resultado é preservado. Uma campanha séria não descarta a pesquisa que a contraria; ela testa se a divergência vem do método (telefone, cenário com Marçal) ou do eleitorado, e a resposta decide o tamanho do esforço em SP.",
        ),
    ]
    body += (
        '<div class="strategy-grid">'
        + "".join(
            f"<article><span>{i + 1:02}</span><h3>{esc(t)}</h3><p>{esc(x)}</p></article>"
            for i, (t, x) in enumerate(items)
        )
        + "</div>"
    )
    body += '<div class="counterpoint"><span class="stamp limit">Contraponto obrigatório</span><p>Três fatos pesam contra a tese deste capítulo. Primeiro, a reponderação pela PNAD tira a liderança de Flávio na Atlas (45,1 × 44,5) e empata o 1º turno: a base pobre que a pesquisa digital mede para ele não aparece nas presenciais. Segundo, a única pesquisa que testa o endosso, a Quaest, dá saldo negativo ao apoio de Flávio (−5) e pior ao de Lula (−17): endosso organiza coalizão, não transfere voto, e isso vale para Tarcísio também. Terceiro, entre os que se declaram antipetistas e antibolsonaristas, 54,9% não votam em ninguém no 2º turno presidencial (Atlas p. 23): o vão existe, mas metade dele hoje é abstenção declarada, não voto disponível.</p></div>'
    return chapter(
        14,
        "leitura",
        "O que os dados permitem recomendar <em>em público.</em>",
        "A leitura abaixo é de arquitetura de campanha, ordem de palanque e cobertura territorial. Vale para a candidatura de Flávio Bolsonaro em São Paulo e para os nomes da direita que dividem a cédula com ele.",
        body,
        True,
    )


def ch_carregadores():
    est = CARR["estado"]
    body = '<div class="ledger">'
    body += f'<div><span>Bolsonaro · 1º turno 2022</span><b>{fmt(est["bolsonaro_1t"], 2)}%</b><small>votos nominais para presidente</small></div>'
    body += f'<div><span>Tarcísio · 1º turno 2022</span><b>{fmt(est["tarcisio"], 2)}%</b><small>governador, mesma cédula</small></div>'
    body += f'<div><span>Marcos Pontes · Senado</span><b>{fmt(est["pontes"], 2)}%</b><small>o único acima do topo da chapa</small></div>'
    body += f'<div><span>Derrite · federal</span><b>{fmt(est["derrite"], 2)}%</b><small>Salles {fmt(est["salles"], 2)}, Carla {fmt(est["carla"], 2)}, Eduardo {fmt(est["eduardo"], 2)}, Prado {fmt(est["prado"], 2)}</small></div></div>'
    body += '<div class="plain">O primeiro achado desmonta um lugar-comum. No mesmo dia e na mesma urna, Tarcísio fez 42,32% e Bolsonaro fez 47,71%: o governador que hoje aprova com 52% correu 5,4 pontos atrás do presidente em 2022, porque Rodrigo Garcia levou 18,4% do voto que Bolsonaro já tinha. O valor de Tarcísio para a chapa de 2026 não está no volume de 2022. Está em ter conquistado depois o eleitor que não votou nele: 36,5% dos eleitores de Garcia e 4,8% dos eleitores de Lula.</div>'
    regs = CARR["regioes"]
    rows = []
    for r in regs:
        rows.append(
            f'<tr><th scope="row">{esc(r["regiao"])}</th><td class="num">{fmt(r["eleitores"])}</td><td class="num">{fmt(r["bol1"], 1)}%</td><td class="num">{sgn(r["margem_pt_2t_pp"], 1)} pp</td><td class="num">{fmt(r["garcia"], 1)}%</td>'
            + "".join(
                idx_cell(r["i_" + k])
                for k in (
                    "tarcisio",
                    "pontes",
                    "derrite",
                    "salles",
                    "carla",
                    "eduardo",
                    "prado",
                )
            )
            + "</tr>"
        )
    body += (
        '<div class="table-scroll" tabindex="0"><table class="carrier-table"><caption>Índice por região intermediária, sobre votos nominais do próprio cargo</caption><thead><tr><th>região</th><th>eleitores</th><th>Bolsonaro 1T</th><th>margem PT 2T</th><th>Garcia 1T</th><th>Tarcísio</th><th>Pontes</th><th>Derrite</th><th>Salles</th><th>Carla</th><th>Eduardo</th><th>Prado</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></div>"
    )
    comp = CARR["complementares_tarcisio"]
    body += '<div class="split"><div class="chart-shell"><div class="chart-title"><div><p class="kicker">Onde Tarcísio rendeu acima de Bolsonaro no 1º turno</p><h3>Cidades complementares, com 40 mil eleitores ou mais</h3></div></div>'
    body += table(
        [
            "município",
            "região",
            "eleitores",
            "Bolsonaro 1T",
            "Tarcísio 1T",
            "diferença",
            "Garcia 1T",
        ],
        [
            [
                esc(r["nome"]),
                esc(r["regiao"]),
                fmt(r["eleitorado"]),
                fmt(r["bol1"], 1) + "%",
                fmt(r["tar1"], 1) + "%",
                sgn(r["tar1_menos_bol1_pp"], 1) + " pp",
                fmt(r["garcia1"], 1) + "%",
            ]
            for r in comp[:15]
        ],
        cls="compact",
    )
    body += '<p class="note">São os municípios em que o governador teve, em 2022, mais votos que o presidente na mesma cédula. É a lista curta de lugares onde o eleitor já separou os dois nomes a favor do estadual.</p></div>'
    body += '<div class="chart-shell"><div class="chart-title"><div><p class="kicker">Limite do índice</p><h3>O que ele não mede</h3></div></div><div class="limit-list"><p><b>Mede alcance, não repasse.</b> Governador, senador, deputado e presidente disputam cédulas e incentivos diferentes. O índice mostra onde um nome chegou mais longe que o topo da chapa, e a distância entre chegar longe e entregar voto a outro candidato é justamente o que a campanha tem de construir.</p><p><b>Mede território, não gente.</b> A unidade é o município. A capital, com 9,1 milhões de eleitores, tem bolsões de índice alto e baixo dentro dela, e a leitura por zona eleitoral exige o arquivo de seção, que não está nesta versão.</p><p><b>Mede o passado.</b> O denominador é 2022. Desde então mudaram partido, adversário e economia. Derrite fez 1,05% como deputado e hoje disputa o Senado: o índice dele mostra a geografia da base, não o teto.</p></div></div></div>'
    body += '<div class="grid-3"><article class="card"><span class="metric">107</span><h3>Tarcísio no Porto</h3><p>É o corredor onde o governador mais rende acima de Bolsonaro: Baixada Santista, com 48,4% para Bolsonaro no 1º turno e o túnel como pauta. No interior rico (Tecnologia 104, Aeroespacial 105, Sorocaba 103, Agro 103) ele também rende acima. Na capital e no ABC, 97; no oeste metropolitano, 95.</p></article><article class="card"><span class="metric gold">434</span><h3>Derrite em Sorocaba</h3><p>A base do candidato ao Senado é concentrada no sudoeste: no corredor de Sorocaba ele rende mais de quatro vezes o que Bolsonaro rendeu ali. No Porto, 37; na Tecnologia, 64. É um nome regional que precisa da chapa para virar estadual, e a chapa precisa dele onde ele existe.</p></article><article class="card"><span class="metric red">Pontes</span><h3>O carregador que sobrou</h3><p>Marcos Pontes fez 49,68% para o Senado e superou Bolsonaro em todas as regiões. É o único nome da direita paulista com prova de voto acima do topo da chapa em todo o estado, e não está na cédula de 2026 como candidato. Como cabo eleitoral, é o ativo mais subutilizado da campanha.</p></article></div>'
    body += (
        '<p class="note"><b>Cálculo.</b> '
        + esc(K["meta"]["definicao_indice"])
        + " Base auditável em <code>data/pesquisas/estaduais/sp/2026-09/derivados/carregadores-municipais.csv</code>.</p>"
    )
    return chapter(
        15,
        "carregadores",
        "Quem puxa voto <em>onde o topo da chapa não puxou.</em>",
        "Comparar 42% de um governador com 1% de um deputado não diz nada. A régua abaixo divide o desempenho de cada nome em cada município pela própria participação estadual dele, e compara esse número com o mesmo cálculo feito para Bolsonaro no 1º turno de 2022. Cem significa render exatamente o que Bolsonaro rendeu ali.",
        body,
        True,
        True,
    )


def ch_corredores():
    body = '<div class="stance"><span class="stamp limit">Posição declarada</span><p>Este capítulo tem lado, e o diz. As recomendações são dirigidas à campanha de Flávio Bolsonaro em São Paulo, em associação com Tarcísio. Cada corredor reúne municípios com a mesma base econômica, a mesma imprensa e o mesmo tipo de encontro público possível. Para cada um: o que os jornais paulistas publicaram, com data e link; quem tem base eleitoral medida ali; quem sobe no palanque; o formato que a região comporta; o que não dizer; e o juízo editorial, rotulado como tal. O corredor que contraria a própria tese é o da Capital: 26,8% do eleitorado, Tarcísio 48,9 × Haddad 48,4 e a maior perda de volume da direita entre 2018 e 2022.</p></div>'
    body += (
        '<div class="route-grid"><div class="route-map">'
        + route_map()
        + '</div><div class="route-copy"><p class="kicker">NOVE CORREDORES</p><h3>O estado cabe em nove viagens, e a ordem delas está no capítulo 17.</h3><ol>'
        + "".join(
            f'<li><span class="dot" style="background:{ROTA_CORES[c["slug"]]}"></span><b>{esc(c["nome"].replace("Corredor ", ""))}:</b> {fmt(c["resumo"]["eleitores"])} eleitores, {fmt(c["resumo"]["share_sp"], 1)}% do estado, Bolsonaro {fmt(c["resumo"]["bol1"], 1)}% no 1º turno.</li>'
            for c in CORR
        )
        + '</ol><p class="note">Os pontos são as maiores cidades de cada corredor e as linhas tracejadas indicam a sequência de leitura, não um itinerário logístico. Os corredores cobrem '
        + fmt(100 * sum(c["resumo"]["eleitores"] for c in CORR) / K["eleitorado_sp"], 1)
        + "% do eleitorado.</p></div></div>"
    )
    for c in CORR:
        r = c["resumo"]
        pa = c["pauta"]
        body += f'<article class="corridor" id="corr-{c["slug"]}" style="--corr:{ROTA_CORES[c["slug"]]}"><header class="corridor-head"><div><p class="kicker">{esc(c["sub"])}</p><h3>{esc(c["nome"])}</h3></div><dl class="corridor-kpi"><div><dt>eleitores</dt><dd>{fmt(r["eleitores"])}</dd></div><div><dt>% de SP</dt><dd>{fmt(r["share_sp"], 2)}%</dd></div><div><dt>Bolsonaro 1º turno</dt><dd>{fmt(r["bol1"], 1)}%</dd></div><div><dt>margem do PT no 2º</dt><dd>{sgn(r["margem_pt_2t_pp"], 1)} pp</dd></div><div><dt>Garcia 1º turno</dt><dd>{fmt(r["garcia"], 1)}%</dd></div><div><dt>viradas</dt><dd>{r["viradas"]}</dd></div></dl></header><div class="corridor-body"><div>'
        body += (
            f'<p class="corridor-agenda">{esc(pa["agenda"])}</p><h4>O que a imprensa paulista publicou</h4><ul class="fatos">'
            + "".join(
                f"<li>{esc(t)} <cite>{link(u, v)}, {esc(d)}</cite></li>"
                for t, v, d, u in pa["fatos"]
            )
            + "</ul>"
        )
        body += (
            f'<h4>Quem sobe no palanque</h4><p>{esc(pa["palanque"])}</p><p class="corridor-frase">{esc(pa["frase"])}</p><h4>Formato de encontro que a região comporta</h4><ul class="eventos">'
            + "".join(f"<li>{esc(e)}</li>" for e in pa["eventos"])
            + "</ul>"
        )
        body += (
            f'<p class="corridor-alerta"><b>O que não dizer.</b> {esc(pa["alerta"])}</p><p class="corridor-juizo"><b>Juízo editorial.</b> {esc(pa["juizo"])}</p></div><aside><h4>Índice dos carregadores</h4><div class="idx-cards">'
            + "".join(
                f'<div class="{"up" if r["i_" + k] >= 100 else "dn"}"><b>{fmt(r["i_" + k])}</b><span>{lab}</span></div>'
                for k, lab in (
                    ("tarcisio", "Tarcísio"),
                    ("derrite", "Derrite"),
                    ("salles", "Salles"),
                    ("prado", "Prado"),
                )
            )
            + "</div>"
        )
        if c["ancoras"]:
            body += (
                '<h4>Quem tem base medida no corredor</h4><div class="table-scroll"><table class="mini"><thead><tr><th>eleito em 2022</th><th>partido</th><th>casa</th><th>votos SP</th><th>no corredor</th><th>cidade base</th></tr></thead><tbody>'
                + "".join(
                    f'<tr><th scope="row">{esc(a["nome"])}</th><td>{esc(a["partido"])}</td><td>{a["casa"]}</td><td class="num">{fmt(a["votos_sp"])}</td><td class="num">{fmt(a["concentracao_pct"], 1)}%</td><td>{esc(a["base"])}</td></tr>'
                    for a in c["ancoras"]
                )
                + '</tbody></table></div><p class="micro">Concentração é a fatia da votação nominal de 2022 do parlamentar que veio dos municípios do corredor. Só eleitos de partidos de direita e centro-direita, com ao menos 40% da votação no corredor. Situação de candidatura em 2026 não está verificada aqui.</p>'
            )
        else:
            body += '<p class="micro">Nenhum deputado eleito em 2022 por partido de direita concentra 40% ou mais da votação neste corredor. A base é dos prefeitos e das lideranças estaduais.</p>'
        body += "</aside></div>"
        cities = [x for x in c["cidades"] if x["eleitorado"] >= 40000][:14]
        body += '<div class="table-scroll"><table class="corridor-cities"><caption>Municípios do corredor com pelo menos quarenta mil eleitores</caption><thead><tr><th>município</th><th>eleitores 2026</th><th>Bolsonaro 1T</th><th>margem PT 2T</th><th>desloc. 18→22</th><th>Garcia 1T</th><th>Tarcísio</th><th>Derrite</th><th>Salles</th><th>Prado</th></tr></thead><tbody>'
        for x in cities:
            tag = (
                ' <span class="tag-virou">virou</span>'
                if x["virada"] == "Jair → PT"
                else ""
            )
            body += (
                f'<tr><th scope="row">{esc(x["nome"])}{tag}</th><td class="num">{fmt(x["eleitorado"])}</td><td class="num">{fmt(x["bol1"], 1)}%</td><td class="num">{sgn(x["margem_pt_2t_pp"], 1)} pp</td><td class="num">{sgn(x["desloc_18_22_pp"], 1)} pp</td><td class="num">{fmt(x["garcia1"], 1)}%</td>'
                + "".join(
                    idx_cell(x["i_" + k])
                    for k in ("tarcisio", "derrite", "salles", "prado")
                )
                + "</tr>"
            )
        body += "</tbody></table></div></article>"
    return chapter(
        16,
        "corredores",
        "A economia manda na pauta, <em>e a pauta muda a cada cem quilômetros.</em>",
        "Nove corredores, da capital ao oeste. Para cada um, a pauta vem da imprensa local com link, o palanque vem do índice dos carregadores e o formato vem do que a região comporta.",
        body,
        False,
        True,
    )


def ch_ordem():
    steps = [
        (
            "Capital e RM",
            "Onde o vão é maior e o volume também: 47% do eleitorado, vão de 5,2 na cidade e 9,9 na RM e Santos (Atlas). Começar pela entrega estadual, não pela identidade. A regra de convergência que decide o alvo está satisfeita: topo da chapa abaixo da média (Bolsonaro 38,0% na capital), carregador estadual acima da média em aprovação e pauta material com número (Linha 8, PCC, tarifa).",
        ),
        (
            "Tecnologia e Porto",
            "Os dois corredores em que Tarcísio mais rende acima de Bolsonaro (104 e 107) e que têm a pauta federal mais concreta: trem intercidades e Viracopos em Campinas, Tecon 10 e fila de navios em Santos. É onde Flávio pode prometer o que só um presidente entrega.",
        ),
        (
            "ABC e Alto Tietê",
            "Fronteira, não bloco: 12,6% do eleitorado, Bolsonaro 42,4%. A pauta é federal (importação e energia) e o formato é portaria de fábrica. Sem comício em Diadema e São Bernardo.",
        ),
        (
            "Interior de direita",
            "Sorocaba, Cana e Couro, Agro do Oeste e Aeroespacial: 23,5% do eleitorado com Bolsonaro entre 53% e 60%. Não é conversão, é comparecimento e voto útil no 1º turno, onde a Quaest ainda mede 12 pontos de direita dispersa. Formatos baratos: comício de praça, cavalgada, motociata.",
        ),
        (
            "Oeste metropolitano",
            "Direita majoritária, cobrança concentrada num serviço estadual visível. A vistoria da Linha 8 com o governador vale mais que qualquer evento de campanha, e precisa vir antes que o adversário a faça.",
        ),
    ]
    body = (
        '<ol class="march">'
        + "".join(
            f"<li><span>{i + 1:02}</span><div><h3>{esc(t)}</h3><p>{esc(x)}</p></div></li>"
            for i, (t, x) in enumerate(steps)
        )
        + "</ol>"
    )
    body += '<div class="callout"><h3>A regra de convergência</h3><p>O alvo prioritário é o corredor em que três condições se encontram: (a) o topo da chapa ficou abaixo da média estadual em 2022, (b) o carregador estadual rende acima ou aprova acima, e (c) existe pauta material com valor, devedor e destinatário publicados na imprensa local. Em São Paulo isso é a metrópole com o trem e a segurança, e é a Baixada com o porto. O interior de direita não precisa de convergência: precisa de calendário.</p><p>Sem datas. A ordem é de prioridade, não de agenda, e vale enquanto os números de agosto valerem. A próxima onda das três pesquisas reabre este capítulo.</p></div>'
    return chapter(
        17,
        "ordem",
        "Sem datas. <em>Com ordem.</em>",
        "Cinco movimentos, na ordem em que os números os pedem. Cada um tem o motivo numérico ao lado e nenhum depende de promessa que a campanha não pode cumprir.",
        body,
        True,
    )


def ch_dados():
    cm = {m["id"]: m for m in CARR["municipios"]}
    body = '<div class="controls"><label>Filtrar tabela por município ou região<input id="municipal-search" type="search" placeholder="Ex.: Guará, Campinas, Santos"></label></div><p id="table-count" aria-live="polite">645 municípios</p>'
    body += table(
        [
            "Município",
            "Região IBGE",
            "Eleitorado",
            "Renda pc Censo · R$",
            "Bolsonaro 2018 · 2º",
            "Bolsonaro 2022 · 2º",
            "Tarcísio 2022 · 2º",
            "Tarcísio menos Bolsonaro · 1º",
            "Garcia 1º",
            "Vencedores",
        ],
        [
            [
                esc(r["nome"]),
                esc(r["regiao"]),
                fmt(r["eleitorado"]),
                fmt(r["renda"], 2),
                fmt(r["jair_2018_2_pct"], 2) + "%",
                fmt(r["jair_2022_2_pct"], 2) + "%",
                fmt(r["tarcisio_2022_2_pct"], 2) + "%",
                sgn(cm[r["id"]]["tar1_menos_bol1_pp"], 2),
                fmt(cm[r["id"]]["garcia1"], 1) + "%",
                r["virada"],
            ]
            for r in sorted(C, key=lambda r: r["nome"])
        ],
        "municipal-table",
    )
    body = (
        "<details><summary>Abrir a tabela completa dos 645 municípios</summary>"
        + body
        + "</details><p>"
        + link("assets/sp_092026_municipios.csv", "Baixar CSV municipal")
        + " · "
        + link("assets/sp_092026_data.json", "Abrir base JSON")
        + " · "
        + link(
            "assets/sp_092026_camada2.json",
            "Camada 2: reponderação, fluxos, vão, carregadores e corredores",
        )
        + " · "
        + link("assets/sp_092026_municipios.geojson", "Malha municipal GeoJSON")
        + "</p>"
    )
    return chapter(
        18,
        "dados",
        "Todos os municípios, <em>com a mesma regra.</em>",
        "O arquivo completo inclui os votos nominais dos parlamentares por ano, os totais por cargo, PIB, eleitorado, os índices dos carregadores e as fontes geográficas.",
        body,
    )


def ch_fontes():
    body = '<ol class="method-list"><li><b>TSE.</b> ZIPs de votação por candidato, município e zona de 2018 e 2022. Presidência no arquivo BR filtrado por SP; demais cargos no arquivo SP, evitando duplicidade. Junção ao IBGE por nome normalizado e exceções explícitas. São 645 municípios.</li><li><b>Empates.</b> Comparação das contagens inteiras. Percentual igual a 50% não é vitória do candidato oposto. Guará permanece em categoria separada.</li><li><b>PNAD.</b> Renda conhecida de pessoas 16+; estatísticas monetárias e domínios identificados. População anual estimada e eleitorado cadastrado não são intercambiáveis. Os intervalos usam 200 réplicas oficiais e aproximação normal.</li><li><b>Pesquisas.</b> Percentuais publicados e arredondamentos preservados. Bases ponderadas não são contagens de campo. Toda tabela cruzada foi transcrita com a página ao lado e provada recompondo o placar publicado; o único controle reprovado (Quaest p. 79, Flávio) está declarado no capítulo 9.</li><li><b>Reponderação.</b> Sensibilidade de uma margem: o voto por faixa é mantido e só o peso da faixa muda para o da PNAD 2025. Publicada como publicado + (reponderado − recomposto). Nunca chamada de voto corrigido.</li><li><b>Fluxos.</b> IPF/RAS sobre margens publicadas, com prior empírica da Atlas (p. 19 e 23) sobre o voto de 2022. Nós são medição; fitas são estimativa. Só o vazamento agregado sobrevive à troca da prior.</li><li><b>Índice dos carregadores.</b> Participação municipal do nome dividida pela participação estadual, dividida pelo mesmo quociente de Bolsonaro no 1º turno de 2022, vezes cem, sobre votos nominais do próprio cargo.</li><li><b>Geografia.</b> Municípios agrupados nas onze regiões intermediárias IBGE e em nove corredores declarados no script. A malha é simplificada para visualização; área não representa população.</li><li><b>Imprensa.</b> Cada fato dos corredores tem veículo, data e link, conferidos no próprio veículo. Resultado nulo de buscador não foi tratado como ausência de cobertura.</li><li><b>Rastreabilidade.</b> Os quatro PDFs têm SHA-256, número de páginas, registros e status de conferência na base de pesquisas. A ausência de um PDF ou cruzamento é indicada onde limita a análise.</li></ol>'
    body += table(
        ["Fonte", "Acesso"],
        [
            [
                "TSE, resultados 2018",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/resultados-2018",
                    "Dados Abertos TSE",
                ),
            ],
            [
                "TSE, resultados 2022",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/resultados-2022",
                    "Dados Abertos TSE",
                ),
            ],
            [
                "TSE, eleitorado",
                link(
                    "https://dadosabertos.tse.jus.br/dataset/eleitorado-atual",
                    "Perfil atual",
                ),
            ],
            [
                "IBGE, renda Censo 2022",
                link("https://sidra.ibge.gov.br/tabela/10295", "SIDRA 10295"),
            ],
            [
                "IBGE, população",
                link("https://sidra.ibge.gov.br/tabela/4714", "SIDRA 4714"),
            ],
            [
                "IBGE, PIB municipal",
                link(
                    "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html",
                    "PIB dos Municípios",
                ),
            ],
            [
                "IBGE, PNADC",
                link(
                    "https://www.ibge.gov.br/estatisticas/sociais/trabalho/9173-pesquisa-nacional-por-amostra-de-domicilios-continua-trimestral.html",
                    "PNAD Contínua",
                ),
            ],
            ["Atlas/Estadão, SP, 03/09/2026", link(P["urls"]["atlas"], "PDF")],
            ["Genial/Quaest, SP, 25/08/2026", link(P["urls"]["quaest"], "PDF")],
            ["Paraná Pesquisas, SP, 19/08/2026", link(P["urls"]["parana"], "PDF")],
            [
                "Datafolha, SP, 21 e 22/08/2026",
                link(P["urls"]["datafolha"], "Folha")
                + " · "
                + link(
                    "https://www.poder360.com.br/poder-eleicoes-2026/datafolha-flavio-tem-47-contra-42-de-lula-no-2o-turno-em-sp/",
                    "Poder360",
                ),
            ],
            [
                "Real Time Big Data, SP, 24/08/2026",
                link(P["urls"]["rt_gov"], "iG")
                + " · "
                + link(P["urls"]["rt_pres"], "Metrópoles"),
            ],
        ],
    )
    body += '<h3>Reprodução</h3><pre><code>python3 scripts/sp-092026-data.py\npython3 scripts/sp-092026-pnad.py\npython3 scripts/sp-092026-polls.py\npython3 scripts/sp-092026-camada2.py\npython3 scripts/sp-092026-build.py</code></pre><p class="note">Requer os arquivos oficiais locais e dependências do projeto. Os números públicos são calculados dessas fontes; documentos privados de terceiros não são dependência de construção nem são distribuídos com esta página.</p>'
    body += (
        "<p>"
        + link("assets/sp_092026_pesquisas.json", "Pesquisas e hashes")
        + " · "
        + link("assets/sp_092026_pnad.json", "PNAD e incerteza")
        + " · "
        + link("assets/sp_092026_camada2.json", "Camada 2")
        + " · "
        + link("index.html", "Voltar ao acervo")
        + "</p>"
    )
    return chapter(
        19,
        "fontes",
        "Uma trilha pública <em>para refazer as contas.</em>",
        "Atlas descritivo até o capítulo 13, leitura estratégica declarada do 14 ao 17. Toda conta derivada tem a fonte, a página e o script ao lado.",
        body,
    )


def build():
    parts = [
        ch_tese(),
        ch_economia(),
        ch_mapa(),
        ch_regioes(),
        ch_cidades(),
        ch_nomes(),
        ch_pesquisas(),
        ch_comparabilidade(),
        ch_renda(),
        ch_fluxos(),
        ch_vao(),
        ch_senado(),
        ch_temas(),
        ch_leitura(),
        ch_carregadores(),
        ch_corredores(),
        ch_ordem(),
        ch_dados(),
        ch_fontes(),
    ]
    nav = [
        ("historia", "História"),
        ("economia", "Economia"),
        ("mapa", "Mapa"),
        ("regioes", "Regiões"),
        ("pesquisas", "Pesquisas"),
        ("renda", "Renda"),
        ("fluxos", "Fluxos"),
        ("vao", "O vão"),
        ("senado", "Senado"),
        ("leitura", "Leitura"),
        ("carregadores", "Carregadores"),
        ("corredores", "Corredores"),
        ("ordem", "Ordem"),
        ("fontes", "Fontes"),
    ]
    html = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>São Paulo 2026: o atlas do voto de Tarcísio que ainda não é de Flávio | Arvor</title><meta name="description" content="Atlas de São Paulo: 645 municípios, TSE 2018 e 2022, PNAD, cinco pesquisas auditadas, reponderação por renda, três diagramas de fluxo de Tarcísio para Flávio, o vão por recorte, o índice dos carregadores e nove corredores de campanha."><meta property="og:title" content="São Paulo 2026: o voto de Tarcísio que ainda não é de Flávio"><meta property="og:description" content="Um em cada sete eleitores de Tarcísio no 2º turno não vota Flávio. Onde ele está, quanto vale e como se busca: reponderação, fluxos, carregadores e nove corredores."><meta property="og:type" content="article"><meta property="og:url" content="https://brasil.arvor.co/sp_092026.html"><meta property="og:image" content="https://brasil.arvor.co/img/og/sp_092026.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://brasil.arvor.co/img/og/sp_092026.png"><link rel="canonical" href="https://brasil.arvor.co/sp_092026.html"><link rel="stylesheet" href="assets/sp_092026.css"><script defer src="assets/sp_092026.js"></script></head><body><a class="skip" href="#conteudo">Pular para o conteúdo</a><header class="masthead"><a href="index.html">ARVOR <span>Intelligence</span></a><span>Atlas estadual 02 / SP</span></header><main id="conteudo"><section class="hero"><div class="wrap"><p class="eyebrow">São Paulo · 5 de setembro de 2026 · dados, auditoria e leitura estratégica</p><h1>O voto de Tarcísio<br>que ainda não é<br><em>de Flávio.</em></h1><div class="hero-bottom"><p>O estado que deu 67,97% a Bolsonaro em 2018 deu 55,24% em 2022 e aprova o governador com 52%. Um em cada sete eleitores de Tarcísio no 2º turno não vota Flávio. Este atlas mede onde ele está, quanto vale e o que a imprensa local diz que ele quer.</p><div><strong>645</strong><span>municípios<br>com dados conferidos</span></div><div><strong>34,1 mi</strong><span>eleitores<br>no cadastro TSE</span></div><div><strong>7,0</strong><span>pontos de vão<br>Tarcísio-Flávio no Datafolha</span></div><div><strong>9</strong><span>corredores<br>com pauta e palanque</span></div></div><p class="note">TSE: segundos turnos de 2018 e 2022; eleitorado de junho de 2026. Pesquisas: Paraná, Datafolha, Real Time, Quaest e Atlas, campo de 16 a 31 de agosto. Posição editorial declarada a partir do capítulo 14.</p></div></section><nav class="toc" aria-label="Capítulos">"""
    html += (
        "".join(link("#" + ident, label) for ident, label in nav)
        + "</nav>"
        + "".join(parts)
        + '</main><footer class="wrap footer"><b>ARVOR Intelligence</b><span>São Paulo · edição de setembro de 2026 · corte em 05/09</span></footer></body></html>'
    )
    assert "—" not in html and "–" not in html
    (OUT / "sp_092026.html").write_text(
        html.replace("<section ", "\n<section ").replace("<article", "\n<article")
        + "\n"
    )
    (ASSETS / "sp_092026_noticias.json").write_text(
        json.dumps(
            [
                dict(
                    zip(
                        ["recorte", "tema", "leitura", "data", "veiculo", "url"],
                        r,
                        strict=True,
                    )
                )
                for r in NEWS
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("Relatório gerado:", OUT / "sp_092026.html")


if __name__ == "__main__":
    build()
