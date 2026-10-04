"""Mapa do Brasil pintado pelo campo da candidatura favorita de cada UF.

Listras brancas marcam o estado onde o 2º turno é mais provável que a decisão
no 1º; cor esmaecida marca cobertura antiga.
"""

from __future__ import annotations

from html import escape as esc

from predicao_2026.base import module
from senado_2026.pagina.comum import COR, ORDEM, ROTULO, SEM_PESQUISA, campo_de, pct

WIDTH, HEIGHT = 560.0, 540.0
STROKE = "#fffdf8"
LISTRA = "#fffdf8"


def favorito(estado: dict) -> dict | None:
    nome = estado.get("favorito")
    for c in estado.get("probabilidades", []):
        if c.get("nome") == nome:
            return c
    return None


def tonalidade(estado: dict) -> tuple[str, str | None]:
    """(modo, campo): vazio, cheio ou listrado (2º turno mais provável)."""
    if estado.get("cobertura") == "sem_pesquisa" or not favorito(estado):
        return "vazio", None
    campo = campo_de(favorito(estado).get("campo"))
    if (estado.get("p_segundo_turno") or 0) >= 0.5:
        return "listrado", campo
    return "cheio", campo


def pattern_id(campo: str) -> str:
    return f"gv-pat-{campo}"


def patterns(campos: set[str]) -> str:
    out = []
    for campo in sorted(campos):
        out.append(
            f'<pattern id="{pattern_id(campo)}" patternUnits="userSpaceOnUse" '
            'width="8" height="8" patternTransform="rotate(45)">'
            f'<rect width="8" height="8" fill="{COR[campo]}"/>'
            f'<rect width="3" height="8" fill="{LISTRA}" fill-opacity=".55"/></pattern>'
        )
    return "<defs>" + "".join(out) + "</defs>"


def descricao_uf(uf: str, estado: dict) -> str:
    nome = estado.get("nome", uf)
    fav = favorito(estado)
    if not fav:
        return f"{nome} ({uf}): sem pesquisa no período, nenhum nome indicado."
    p2 = estado.get("p_segundo_turno") or 0
    sufixo = ", cobertura antiga" if estado.get("cobertura") == "antiga" else ""
    return (
        f"{nome} ({uf}): {fav.get('nome')} ({ROTULO[campo_de(fav.get('campo'))].lower()}), "
        f"{pct(fav.get('p_eleito'))} de chance; 2º turno em {pct(p2)} das simulações{sufixo}"
    )


def svg(estados: dict[str, dict]) -> str:
    geo = module("voto_util_mapa").paths(WIDTH, HEIGHT)
    listrados: set[str] = set()
    shapes, labels = [], []
    for uf, g in sorted(geo.items()):
        e = estados.get(uf)
        if e is None:
            continue
        modo, campo = tonalidade(e)
        if modo == "cheio":
            fill = COR[campo]
        elif modo == "listrado":
            listrados.add(campo)
            fill = f"url(#{pattern_id(campo)})"
        else:
            fill = SEM_PESQUISA
        opac = ' fill-opacity=".5"' if e.get("cobertura") == "antiga" else ""
        tip = descricao_uf(uf, e)
        ax, ay = g["anchor"]
        shapes.append(
            f'<a class="sn-uf" href="#estado-{uf}" data-uf="{uf}" '
            f'aria-label="{esc(tip)}"><path d="{g["d"]}" fill="{fill}"{opac}>'
            f"<title>{esc(tip)}</title></path></a>"
        )
        lx, ly = g["label"]
        if g["fora"]:
            labels.append(
                f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx - 3:.1f}" y2="{ly - 4:.1f}" class="sn-guide"/>'
                f'<rect x="{lx - 4:.1f}" y="{ly - 12:.1f}" width="25" height="16" rx="3" class="sn-chip"/>'
                f'<text x="{lx + 8.5:.1f}" y="{ly - 3.6:.1f}" class="sn-label">{uf}</text>'
            )
        else:
            labels.append(
                f'<rect x="{lx - 12.5:.1f}" y="{ly - 8:.1f}" width="25" height="16" rx="3" class="sn-chip"/>'
                f'<text x="{lx:.1f}" y="{ly + 0.4:.1f}" class="sn-label">{uf}</text>'
            )
    return (
        f'<svg class="sn-map" id="sn-map" viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" '
        'role="group" aria-labelledby="sn-map-title" xmlns="http://www.w3.org/2000/svg">'
        f"{patterns(listrados)}"
        f'<g stroke="{STROKE}" stroke-width="1" stroke-linejoin="round">{"".join(shapes)}</g>'
        f'<g aria-hidden="true">{"".join(labels)}</g></svg>'
    )


def legenda() -> str:
    cheios = "".join(
        f'<li><span class="sn-sw sn-sw-cheio" style="background:{COR[c]}" aria-hidden="true"></span>'
        f"{ROTULO[c]}</li>"
        for c in ORDEM[:5]
    )
    return (
        '<div class="sn-map-legenda"><p class="eyebrow">Cor = campo da candidatura favorita</p>'
        f'<ul class="sn-sws">{cheios}'
        '<li><span class="sn-sw gv-sw-listra" aria-hidden="true"></span>'
        "Listras: 2º turno mais provável que a decisão no 1º</li>"
        '<li><span class="sn-sw sn-sw-antiga" aria-hidden="true"></span>'
        "Cor esmaecida: só pesquisa antiga</li>"
        f'<li><span class="sn-sw sn-sw-cheio" style="background:{SEM_PESQUISA}" aria-hidden="true"></span>'
        "Cinza: sem pesquisa, sem nomes</li></ul></div>"
    )
