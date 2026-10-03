"""Mapa do Brasil pintado pelo campo dos dois eleitos prováveis de cada UF."""

from __future__ import annotations

from html import escape as esc

from predicao_2026.base import module

from .comum import COR, ORDEM, ROTULO, SEM_PESQUISA, campo_de, pct

WIDTH, HEIGHT = 560.0, 540.0
STROKE = "#fffdf8"


def eleitos(estado: dict) -> list[dict]:
    """Os dois eleitos prováveis, com campo e probabilidade, na ordem do JSON."""
    nomes = estado.get("eleitos_provaveis") or []
    por_nome = {c.get("nome"): c for c in estado.get("probabilidades", [])}
    return [por_nome[n] for n in nomes if n in por_nome]


def tonalidade(estado: dict) -> tuple[str, tuple[str, ...]]:
    """Devolve (modo, campos): vazio, cheio ou listrado."""
    if estado.get("cobertura") == "sem_pesquisa":
        return "vazio", ()
    campos = tuple(campo_de(c.get("campo")) for c in eleitos(estado))
    if len(campos) < 2:
        return "vazio", ()
    if campos[0] == campos[1]:
        return "cheio", (campos[0],)
    return "listrado", tuple(sorted(campos, key=ORDEM.index))


def pattern_id(campos: tuple[str, ...]) -> str:
    return "sn-pat-" + "-".join(campos)


def patterns(combos: set[tuple[str, ...]]) -> str:
    out = []
    for campos in sorted(combos):
        a, b = COR[campos[0]], COR[campos[1]]
        out.append(
            f'<pattern id="{pattern_id(campos)}" patternUnits="userSpaceOnUse" '
            'width="10" height="10" patternTransform="rotate(45)">'
            f'<rect width="5" height="10" fill="{a}"/>'
            f'<rect x="5" width="5" height="10" fill="{b}"/></pattern>'
        )
    return "<defs>" + "".join(out) + "</defs>"


def descricao_uf(uf: str, estado: dict) -> str:
    nome = estado.get("nome", uf)
    cob = estado.get("cobertura")
    if cob == "sem_pesquisa":
        return f"{nome} ({uf}): sem pesquisa no período, nenhum nome indicado."
    partes = [
        f"{c.get('nome')} ({ROTULO[campo_de(c.get('campo'))].lower()}), "
        f"{pct(c.get('p_eleito'))}"
        for c in eleitos(estado)
    ]
    sufixo = ", cobertura antiga" if cob == "antiga" else ""
    return f"{nome} ({uf}): " + "; ".join(partes) + sufixo


def svg(estados: dict[str, dict]) -> str:
    geo = module("voto_util_mapa").paths(WIDTH, HEIGHT)
    combos: set[tuple[str, ...]] = set()
    shapes, labels = [], []
    for uf, g in sorted(geo.items()):
        e = estados.get(uf)
        if e is None:
            continue
        modo, campos = tonalidade(e)
        if modo == "cheio":
            fill = COR[campos[0]]
        elif modo == "listrado":
            combos.add(campos)
            fill = f"url(#{pattern_id(campos)})"
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
        f"{patterns(combos)}"
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
        '<div class="sn-map-legenda"><p class="eyebrow">Cor = campo dos dois eleitos prováveis</p>'
        f'<ul class="sn-sws">{cheios}'
        '<li><span class="sn-sw sn-sw-lista" aria-hidden="true"></span>'
        "Listras: os dois eleitos são de campos diferentes</li>"
        '<li><span class="sn-sw sn-sw-antiga" aria-hidden="true"></span>'
        "Cor esmaecida: só pesquisa antiga</li>"
        f'<li><span class="sn-sw sn-sw-cheio" style="background:{SEM_PESQUISA}" aria-hidden="true"></span>'
        "Cinza: sem pesquisa, sem nomes</li></ul></div>"
    )
