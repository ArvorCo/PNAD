"""Capítulo 9 do dossiê do 2º turno: exterior. Interface ``render(d, cap) -> str``."""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, limites

from . import pagina_fig_exterior as F
from . import pagina_texto_exterior as T
from .pagina_comum import cabeca


def render(d: Dados, cap: Capitulo) -> str:
    E = d.get("exterior.json")
    if E is None:
        raise KeyError("exterior.json")
    h = cabeca(cap, T.titulo(E), T.lead(E))
    h += T.cartoes(E) + T.abre(E) + F.fig_mapa(E)
    h += T.continentes(E) + F.fig_continentes(E) + F.tabela_cidades(E)
    h += T.hora(E) + F.tabela_hora_local(E)
    h += limites(T.limites_itens())
    return h
