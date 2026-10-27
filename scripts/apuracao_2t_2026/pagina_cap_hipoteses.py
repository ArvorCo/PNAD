"""Capítulo do dossiê do 2º turno: o que poderia ter acontecido, e o que os dados dizem de cada hipótese.

Interface: ``render(d, cap) -> str`` (``analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md``).
Lê ``hipoteses.json``, gerado por ``python3 scripts/apuracao-2t-2026-hipoteses.py``
a partir dos JSONs do acervo, e ``logs.json`` para a cadência do dia. Memorando
interno de origem: ``analysis/apuracao_2t_2026/HIPOTESES_PRORROGACAO.md``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados

from . import pagina_texto_angulo_boca_urna as TBU
from . import pagina_texto_angulo_transporte as TA
from . import pagina_texto_hipoteses as T
from . import pagina_texto_hipoteses_b as TB
from .pagina_comum import cabeca, checar
from .pagina_fig_hipoteses import fig_cadencia, fig_matriz, fig_tarde

ARQ = "hipoteses.json"
CHAVES = [
    "cronologia",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hipoteses",
    "discriminador",
    "estados",
]


def render(d: Dados, cap: Capitulo) -> str:
    H = d.get(ARQ)
    if H is None:
        raise KeyError(ARQ)
    checar(d, ARQ, CHAVES)
    L = d.get("logs.json")
    h = cabeca(
        cap,
        "O que poderia ter acontecido,<br><em>e o que os dados dizem de cada hipótese.</em>",
        T.lead(H),
    )
    h += T.como_ler(H) + T.cartoes(H)
    h += T.documentado(H) + fig_tarde(H)
    h += f"<details><summary>Os marcos da tarde, com fonte</summary>{T.tabela_marcos(H)}</details>"
    h += T.fato_e_hipotese()
    h += T.h1(H)
    if L is not None:
        h += fig_cadencia(L)
    h += (
        T.h2(H)
        + T.h3(H)
        + TA.bloco_hipotese(d.get("angulo_transporte.json"), d.get("secoes_voto.json"))
        + T.tabela_tercos(H)
        + T.h4(H)
        + TBU.bloco(d)
        + T.h5(H)
        + T.tabela_modelos(H)
        + T.h6(H)
    )
    h += TB.precedentes(H, d.get("presidente.json"))
    h += T.discriminador(H) + T.tabela_testes(H) + fig_matriz(H)
    h += T.quadro(H) + T.fecho(H)
    return h
