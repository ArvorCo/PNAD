"""Figuras do dossiê da apuração: primitivas SVG e catálogo `FIGURAS`.

As primitivas (`barras_h`, `divergentes`, `hemiciclo`...) vivem em
`pagina_figuras_prim` e continuam exportadas daqui. O catálogo
(`analysis/apuracao_2026/CATALOGO_FIGURAS.md`) é o dicionário `FIGURAS`, nome para
`fn(dados, **op) -> str`, preenchido pelos módulos `pagina_fig_*`; o texto o chama
por `pagina_comum.figura_catalogo(nome, dados)`.
"""

from __future__ import annotations

from . import (
    pagina_fig_congresso,
    pagina_fig_estrategia,
    pagina_fig_mapas,
    pagina_fig_noite,
    pagina_fig_pesquisas,
    pagina_fig_regioes,
)
from .pagina_fig_base import FIGURAS
from .pagina_figuras_prim import (
    ESCURAS,
    FONTE,
    MONO,
    abre,
    barras_h,
    barras_tempo,
    cascata,
    cor_texto_sobre,
    dispersao,
    divergentes,
    empilhadas,
    grafico_linhas,
    hemiciclo,
    legenda_linha,
    linha,
    pontos_setas,
    rect,
    txt,
)

# Os módulos do catálogo registram as figuras em FIGURAS ao serem importados.
MODULOS_CATALOGO = (
    pagina_fig_congresso,
    pagina_fig_estrategia,
    pagina_fig_mapas,
    pagina_fig_noite,
    pagina_fig_pesquisas,
    pagina_fig_regioes,
)

__all__ = [
    "ESCURAS",
    "FIGURAS",
    "FONTE",
    "MODULOS_CATALOGO",
    "MONO",
    "abre",
    "barras_h",
    "barras_tempo",
    "cascata",
    "cor_texto_sobre",
    "dispersao",
    "divergentes",
    "empilhadas",
    "grafico_linhas",
    "hemiciclo",
    "legenda_linha",
    "linha",
    "pontos_setas",
    "rect",
    "txt",
]
