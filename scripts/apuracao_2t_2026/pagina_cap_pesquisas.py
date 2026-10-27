"""Capítulo 11 do dossiê do 2º turno: pesquisas × urna, e a hipótese do autor.

Tese editorial (`analysis/apuracao_2t_2026/TESE.md`, juízo declarado do autor): as
pesquisas e a régua de renda mediram certo até o último campo, e o afastamento
comum de todas as casas mede o tamanho do que mudou entre sábado e domingo. A
hipótese do autor é o eixo; os candidatos a explicar a mudança saem com o que
sustenta e o que contraria; a medição casa a casa, as centrais e a régua de renda
continuam publicadas; o que contraria a tese fica em "O que ainda falta explicar".
"""

from __future__ import annotations

from . import pagina_texto_pesquisas as T
from . import pagina_texto_pesquisas_b as TB
from .pagina_cap_noticias import carregar
from .pagina_comum import Capitulo, Dados, cabeca, checar, sinal
from .pagina_fig_pesquisas import fig_casas, fig_erro
from .pagina_fig_pesquisas_b import fig_mapa, fig_tres

CHAVES = [
    "pesquisas",
    "ranking",
    "resumo",
    "efeito_reponderacao",
    "centrais",
    "tendencia_publicada",
    "hipoteses",
    "primeiro_turno",
    "painel_1t_2t",
    "referencia_2022",
]


def render(d: Dados, cap: Capitulo) -> str:
    PV = d.get(T.ARQ)
    if PV is None:
        raise KeyError(T.ARQ)
    checar(d, T.ARQ, CHAVES)
    PP = d.get("projecao_pre_urna.json")
    PE = d.get("pesquisas_estaduais.json")
    H = d.get("hipotese_autor.json")
    N = carregar(d)
    f = T.fatos(PV, PP, PE, H)
    h = cabeca(
        cap,
        "O que mudou entre sábado e domingo?<br><em>Pesquisas, urna e a hipótese do autor.</em>",
        f"{sinal(f['erro'], 2)} pontos na diferença Flávio menos Lula entre o último campo das "
        f"{f['n']} casas e a urna, no mesmo sentido em todas. Para o autor do dossiê, é a medida do que "
        "mudou; o capítulo mostra o que sustenta e o que contraria essa leitura.",
    )
    h += T.tese() + T.cartoes(f) + T.abertura(f)
    if H is not None:
        h += T.hipotese(H, f)
    else:
        d.aviso(
            "hipotese_autor.json ausente: capítulo pesquisas sem o bloco da hipótese"
        )
    h += TB.candidatos(f, PV, N, d.get("logs.json"))
    h += T.medicao(f) + fig_casas(PV) + fig_erro(PV)
    h += f"<details><summary>As {f['n']} casas, uma a uma</summary>{T.tabela_casas(PV)}</details>"
    h += T.centrais(f) + T.tabela_centrais(PV)
    h += T.reponderacao(f)
    h += f"<details><summary>A régua de renda, casa a casa</summary>{T.tabela_reponderacao(PV)}</details>"
    h += T.sinal_invertido(f) + fig_tres(PV)
    if PP is not None:
        h += T.geografia(f) + fig_mapa(PP)
    else:
        d.aviso("projecao_pre_urna.json ausente: capítulo pesquisas sem o mapa por UF")
    if PE is not None:
        h += f"<details><summary>Estaduais do 2º turno</summary>{T.tabela_estaduais(PE)}</details>"
    h += TB.falta_explicar(f) + T.limites_cap()
    return h
