"""Capítulo 13 do dossiê do 2º turno: o dia nas fontes.

Cronologia da prorrogação em ordem de hora, linha do tempo em SVG, blocos por
tema, divergências entre fontes, o que não foi encontrado e a tabela filtrável
dos registros. Tudo lido de `analysis/apuracao_2t_2026/noticias_noite.json`.
"""

from __future__ import annotations

import json
import re

from . import pagina_texto_noticias as T
from .pagina_comum import MEMOS, Capitulo, Dados, cabeca
from .pagina_fig_noticias import fig_linha


def carregar(d: Dados) -> dict | None:
    """O JSON fica em `analysis/apuracao_2t_2026/`, fora de `dados/`; aceita os dois."""
    N = d.get(T.ARQ)
    if N is not None:
        return N
    c = MEMOS / T.ARQ
    if not c.exists():
        return None
    N = json.loads(c.read_text(encoding="utf-8"))
    d.cache[T.ARQ] = N
    return N


def render(d: Dados, cap: Capitulo) -> str:
    N = carregar(d)
    if N is None:
        raise KeyError(T.ARQ)
    ms = {m["chave"]: m for m in T.marcos(N)}
    lead = f"{len(N['itens'])} registros com link, hora e tipo de evidência."
    if "zanin" in ms and "aviso" in ms:
        z = ms["zanin"]
        outras = [
            x
            for x in re.findall(r"\b\d{1,2}h\d{2}\b", z["item"].get("nota", ""))
            if x != T._hm(z["min"])
        ]
        alt = (
            f" (hora mais citada; há registros de {' e '.join(dict.fromkeys(outras))})"
            if outras
            else ""
        )
        lead = (
            f"A decisão saiu às {T._hm(z['min'])}{alt}; o TSE avisou as seções às "
            f"{T._hm(ms['aviso']['min'])}. " + lead
        )
    h = T.CSS + cabeca(
        cap, "O dia nas fontes.<br><em>Hora, veículo e tipo de evidência.</em>", lead
    )
    h += T.abertura(N, d.get("linha_do_tempo.json")) + fig_linha(N)
    h += T.cronologia(N) + T.blocos(N) + T.divergencias(N) + T.nao_encontrado(N)
    h += T.tabela_filtravel(N) + T.JS + T.limites_cap(N)
    return h
