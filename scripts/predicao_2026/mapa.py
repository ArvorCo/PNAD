"""Mapa interativo por UF da seção #territorio.

O HTML sai completo e legível sem JavaScript: contorno oficial do IBGE já
colorido pela diferença Flávio menos Lula, rótulos, legenda contínua, cartão do
exterior e links para as fichas estaduais. `docs/assets/predicao_2026_mapa.js`
só acrescenta controles, ficha lateral e o cenário do leitor por cima disso.
"""

from __future__ import annotations

import json
import math
from html import escape as esc

from .base import module
from .tse import ROOT

WIDTH, HEIGHT = 560.0, 540.0
NEUTRAL = "#ece8da"
LULA, FLAVIO, OUTROS = "#b02f21", "#1457aa", "#0f7f5f"
STROKE = "#fffdf8"
INK = "#192e2b"

UF_NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins", "ZZ": "Exterior",
}  # fmt: skip

METRICS = (
    ("Placar", "margem", "Flávio menos Lula"),
    ("Placar", "lula", "Lula %"),
    ("Placar", "flavio", "Flávio %"),
    ("Placar", "outros", "Demais %"),
    ("Urna", "comparecimento", "Comparecimento"),
    ("Urna", "abstencao", "Abstenção"),
    ("Urna", "eleitorado", "Eleitorado 2026"),
    ("Mudança desde 2022", "swing_flavio", "Flávio x Bolsonaro 2022"),
    ("Mudança desde 2022", "swing_lula", "Lula x Lula 2022"),
    ("Base do modelo", "ondas", "Pesquisas usadas"),
    ("Base do modelo", "prior", "Peso da prior"),
)

CAVEAT = (
    "A cor mostra a estimativa pontual do modelo. Ela não indica liderança "
    "estatisticamente identificada."
)


def _fmt(x: float, places: int = 1) -> str:
    s = f"{x:,.{places}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def _signed(x: float, places: int = 1) -> str:
    return ("+" if x > 0 else "") + _fmt(x, places).replace("-", "−")


# Interpolação em OKLab: mesma conta de `predicao_2026_mapa.js`.
def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gamma(c: float) -> float:
    c = min(1.0, max(0.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _to_lab(hex_color: str) -> tuple[float, float, float]:
    r, g, b = (_lin(int(hex_color[i : i + 2], 16) / 255) for i in (1, 3, 5))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _from_lab(lab: tuple[float, float, float]) -> str:
    L, a, b = lab
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    return "#" + "".join(f"{round(255 * _gamma(c)):02x}" for c in rgb)


def mix(c0: str, c1: str, t: float) -> str:
    a, b = _to_lab(c0), _to_lab(c1)
    return _from_lab(
        (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)
    )


def diverging(value: float, domain: float) -> str:
    t = max(-1.0, min(1.0, value / domain))
    return mix(NEUTRAL, FLAVIO if t > 0 else LULA, abs(t))


def nice_domain(values) -> float:
    top = max(abs(v) for v in values)
    step = 5 if top <= 20 else 10
    return max(step, step * math.ceil(top / step))


def rows_by_uf(data: dict) -> dict[str, dict]:
    out = {}
    for r in data["central"]["ufs"]:
        valid = r["lula"] + r["flavio"] + r["outros"]
        out[r["uf"]] = {
            **r,
            "validos": valid,
            "pct": {k: 100 * r[k] / valid for k in ("lula", "flavio", "outros")},
            "margem": 100 * (r["flavio"] - r["lula"]) / valid,
        }
    return out


def past_votes() -> dict[str, dict]:
    """Voto de 2022 no 1º turno por UF, em percentual dos válidos (TSE)."""
    raw = json.loads(
        (ROOT / "analysis/voto_util/tse_2022_uf.json").read_text(encoding="utf-8")
    )
    rows = [(u["uf"], u["t1"]) for u in raw["ufs"]]
    ext = ROOT / "analysis/predicao_2026/tse_2022_exterior.json"
    if ext.exists():
        rows.append(("ZZ", json.loads(ext.read_text(encoding="utf-8"))["t1"]))
    return {
        uf: {
            "lula": round(100 * t["lula"] / t["validos"], 4),
            "bolsonaro": round(100 * t["bolsonaro"] / t["validos"], 4),
            "comparecimento": round(100 * t["comparecimento"] / t["aptos"], 4),
        }
        for uf, t in rows
    }


def legend_html(domain: float) -> str:
    stops = ", ".join(
        f"{diverging(domain * (i / 8 - 1), domain)} {i * 100 / 16:.2f}%"
        for i in range(17)
    )
    ticks = []
    for i in range(5):
        v = -domain + i * domain / 2
        side = "Lula " if v < 0 else "Flávio " if v > 0 else ""
        text = f"{side}+{_fmt(abs(v), 0)}" if v else "0"
        edge = (
            ' class="mx-tick-start"'
            if i == 0
            else ' class="mx-tick-end"' if i == 4 else ""
        )
        ticks.append(f'<span{edge} style="left:{i * 25}%">{text}</span>')
    return (
        '<div class="mx-legend" id="mx-legend">'
        '<p class="mx-legend-title" id="mx-legend-title">Diferença Flávio menos Lula, em pontos percentuais dos votos válidos</p>'
        f'<div class="mx-ramp" id="mx-ramp" style="background:linear-gradient(90deg, {stops})"></div>'
        f'<div class="mx-ticks" id="mx-ticks">{"".join(ticks)}</div>'
        f'<p class="mx-legend-note">{CAVEAT}</p></div>'
    )


def svg(rows: dict[str, dict], domain: float) -> str:
    geo = module("voto_util_mapa").paths(WIDTH, HEIGHT)
    shapes, labels = [], []
    for uf, g in sorted(geo.items()):
        r = rows[uf]
        nome = UF_NOMES[uf]
        tip = (
            f"{nome} ({uf}): Flávio menos Lula {_signed(r['margem'])} pp. "
            f"Lula {_fmt(r['pct']['lula'])}%, Flávio {_fmt(r['pct']['flavio'])}%, "
            f"demais {_fmt(r['pct']['outros'])}% dos válidos"
        )
        ax, ay = g["anchor"]
        shapes.append(
            f'<a class="mx-uf" href="#estado-{uf}" data-uf="{uf}" data-cx="{ax:.1f}" data-cy="{ay:.1f}" '
            f'aria-label="{esc(tip)}"><path id="mx-path-{uf}" data-uf="{uf}" d="{g["d"]}" '
            f'fill="{diverging(r["margem"], domain)}"><title>{esc(tip)}</title></path></a>'
        )
        lx, ly = g["label"]
        if g["fora"]:
            labels.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx - 3:.1f}" y2="{ly - 4:.1f}" class="mx-guide"/>'
                f'<rect x="{lx - 4:.1f}" y="{ly - 12:.1f}" width="25" height="16" rx="3" class="mx-chip mx-chip-out"/>'
                f'<text x="{lx + 8.5:.1f}" y="{ly - 3.6:.1f}" class="mx-label">{uf}</text>'
            )
        else:
            labels.append(
                f'<rect x="{lx - 12.5:.1f}" y="{ly - 8:.1f}" width="25" height="16" rx="3" class="mx-chip"/>'
                f'<text x="{lx:.1f}" y="{ly + 0.4:.1f}" class="mx-label">{uf}</text>'
            )
    return (
        f'<svg class="mx-svg" id="mx-svg" viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" role="group" '
        'aria-labelledby="mx-title" aria-describedby="mx-desc" xmlns="http://www.w3.org/2000/svg">'
        f'<g class="mx-shapes" stroke="{STROKE}" stroke-width="1" stroke-linejoin="round">{"".join(shapes)}</g>'
        '<g class="mx-overlay" aria-hidden="true"><use id="mx-sel" class="mx-sel" href="#mx-path-SP" visibility="hidden"/>'
        '<use id="mx-hover" class="mx-hover" href="#mx-path-SP" visibility="hidden"/></g>'
        f'<g class="mx-labels" aria-hidden="true">{"".join(labels)}</g></svg>'
    )


def controls() -> str:
    groups: dict[str, list[str]] = {}
    for group, key, label in METRICS:
        pressed = "true" if key == "margem" else "false"
        groups.setdefault(group, []).append(
            f'<button type="button" data-metric="{key}" aria-pressed="{pressed}">{esc(label)}</button>'
        )
    return (
        '<div class="mx-controls" id="mx-controls" role="toolbar" aria-label="Métrica do mapa" hidden>'
        + "".join(
            f'<div class="mx-group" role="group" aria-label="{esc(g)}"><span class="mx-group-label" aria-hidden="true">{esc(g)}</span>'
            f'<div class="mx-seg">{"".join(b)}</div></div>'
            for g, b in groups.items()
        )
        + "</div>"
        '<div class="mx-scenario" id="mx-scenario" hidden><p id="mx-scenario-text" role="status"></p>'
        '<div class="mx-seg" role="group" aria-label="O que o mapa mostra">'
        '<button type="button" data-view="cenario" aria-pressed="true">Cenário do leitor</button>'
        '<button type="button" data-view="diff" aria-pressed="false">Diferença para a central</button></div>'
        '<button type="button" class="mx-back" id="mx-back">Voltar à central</button></div>'
    )


def exterior_card(row: dict | None) -> str:
    if not row:
        return ""
    return (
        '<a class="mx-zz" id="mx-zz" href="#estado-ZZ" data-uf="ZZ">'
        '<span class="mx-zz-head"><b>Exterior</b><span>fora do mapa, somado ao total</span></span>'
        f'<span class="mx-zz-value" id="mx-zz-value">Flávio menos Lula {_signed(row["margem"])} pp</span>'
        f'<span class="mx-zz-score" id="mx-zz-score">Lula {_fmt(row["pct"]["lula"])}% · Flávio {_fmt(row["pct"]["flavio"])}% · '
        f'demais {_fmt(row["pct"]["outros"])}% · {_fmt(row["eleitorado"] / 1e6, 2)} mi de eleitores</span></a>'
    )


def explorer(data: dict) -> str:
    rows = rows_by_uf(data)
    domestic = {uf: r for uf, r in rows.items() if uf != "ZZ"}
    domain = nice_domain(r["margem"] for r in domestic.values())
    lula_n = sum(r["margem"] < 0 for r in domestic.values())
    desc = (
        f"Mapa das 27 unidades da federação colorido pela diferença Flávio menos Lula "
        f"nos votos válidos da previsão central. Pela estimativa pontual, Lula fica à "
        f"frente em {lula_n} UFs e Flávio em {len(domestic) - lula_n}. {CAVEAT} "
        "Os valores de cada estado estão na tabela e nas fichas estaduais desta seção."
    )
    payload = json.dumps(
        {"passado": past_votes(), "nomes": UF_NOMES}, ensure_ascii=False
    ).replace("<", "\\u003c")
    return (
        '<div class="mx" id="mapa-explorador" data-mode="estatico">'
        '<div class="mx-head"><h3 id="mx-title">Diferença Flávio menos Lula nos votos válidos, previsão central</h3>'
        f'<p class="mx-sr" id="mx-desc">{esc(desc)}</p><p class="mx-sr" id="mx-live" aria-live="polite"></p>{controls()}</div>'
        '<div class="mx-body"><figure class="mx-figure"><div class="mx-canvas" id="mx-canvas">'
        f'{svg(rows, domain)}<div class="mx-tip" id="mx-tip" role="tooltip" hidden></div></div>'
        "<figcaption>Malha oficial do IBGE. Área no mapa não é peso na soma nacional. "
        "Cada estado leva à sua ficha estadual nesta página.</figcaption></figure>"
        f'<div class="mx-side">{legend_html(domain)}{exterior_card(rows.get("ZZ"))}'
        '<section class="mx-panel" id="mx-panel" aria-labelledby="mx-panel-title" tabindex="-1">'
        '<h4 id="mx-panel-title">Ficha do estado</h4><p class="mx-panel-empty">Cada estado do mapa abre a ficha estadual '
        "completa, com as pesquisas usadas, o peso da prior e o comparecimento.</p></section></div></div>"
        f'<script type="application/json" id="mapa-2022">{payload}</script></div>'
    )
