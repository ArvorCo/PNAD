"""Capítulo 10 do dossiê do 2º turno: seis governadores. Interface ``render(d, cap) -> str``."""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, limites

from . import pagina_fig_governadores as F
from . import pagina_texto_governadores as T
from .pagina_comum import cabeca


def render(d: Dados, cap: Capitulo) -> str:
    G = d.get("governadores.json")
    if G is None:
        raise KeyError("governadores.json")
    h = cabeca(cap, T.titulo(G), T.lead(G))
    h += T.cartoes(G) + T.abre(G) + F.fig_placar(G)
    h += "<h3>A noite: viradas na contagem</h3>" + T.noite(G) + F.fig_noite(G)
    h += "<h3>O vão contra o presidencial</h3>" + T.vao(G) + F.fig_vao(G)
    h += "<h3>Contra o 1º turno</h3>" + T.comparacao(G) + F.tabela_1t(G)
    h += limites([x for x in T.limites_itens(G) if x])
    return h
