"""Capítulo 12 do dossiê do 2º turno: totalização paralela por QR. Interface ``render(d, cap)``."""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, limites

from . import pagina_fig_paralela as F
from . import pagina_texto_paralela as T
from .pagina_comum import cabeca


def render(d: Dados, cap: Capitulo) -> str:
    P = d.get("paralela.json")
    if P is None:
        raise KeyError("paralela.json")
    Pres = d.get("presidente.json")
    h = cabeca(cap, T.titulo(P), T.lead(P))
    h += T.cartoes(P) + T.abre(P, Pres)
    h += f'<figure class="chart-fit">{F.placar_svg(P)}</figure>'
    h += F.fig_cobertura(P) + T.relogios(P) + F.fig_relogios(P)
    h += T.prova() + F.qr_html()
    h += limites([x for x in T.limites_itens(P) if x])
    return h
