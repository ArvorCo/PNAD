"""Capítulo "De onde veio o voto: 1º turno → 2º turno" (dossiê do 2º turno de 2026).

Abre pelo saldo que as duas urnas impõem (Lula +10,4 milhões, Flávio +3,7), mede
quem faltou no 1º turno e votou no 2º por regressão ecológica entre municípios e
seções, monta a matriz de hipótese por IPF com as linhas publicadas pelos
institutos como prior e separa o que sobrevive à troca da prior do que depende
dela. Fonte única: ``transferencia.json`` (``scripts/apuracao-2t-2026-transferencia.py``).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, cartao, checar, num
from apuracao_2026.pagina_fig_base import FLAVIO, LULA

from . import pagina_fig_transferencia as S
from . import pagina_fig_transferencia_b as F
from . import pagina_texto_transferencia as X
from .pagina_comum import cabeca

ARQ = "transferencia.json"


def render(d: Dados, cap: Capitulo) -> str:
    T = d.get(ARQ)
    checar(
        d,
        ARQ,
        [
            "contabilidade",
            "regressao.principal",
            "regressao.dispersao",
            "regressao.por_uf",
            "ipf.central.matriz",
            "ipf.sensibilidades",
            "ipf.invariantes",
            "resposta",
        ],
    )
    if not isinstance(T, dict):
        raise KeyError(ARQ)
    c = T["contabilidade"]
    r = T["resposta"]
    h = cabeca(
        cap,
        "De onde veio o voto:<br><em>1º turno → 2º turno.</em>",
        f"Lula ganhou {num(c['ganho_lula'] / 1e6, 1)} milhões de votos entre os turnos; Flávio, "
        f"{num(c['ganho_flavio'] / 1e6, 1)}. A urna liberou {num(c['disponiveis'] / 1e6, 1)} milhões: a terceira via que saiu "
        "da cédula, a queda de branco e nulo e o aumento do comparecimento. Lula ficou com "
        f"{num(c['parte_lula_pct'], 1)}% desse saldo e Flávio com {num(c['parte_flavio_pct'], 1)}%. As duas urnas são as "
        "margens; as pesquisas, a prior; a regressão, o elo de quem voltou a votar.",
    )
    h += X.CSS
    h += (
        '<div class="finding-grid">'
        + cartao(
            f"+{num(c['ganho_lula'] / 1e6, 2)} mi",
            "votos novos de Lula entre os turnos",
            LULA,
        )
        + cartao(
            f"+{num(c['ganho_flavio'] / 1e6, 2)} mi", "votos novos de Flávio", FLAVIO
        )
        + cartao(
            f"{num(r['liquido_por_100_lula'], 0)} de 100",
            "eleitores a mais na urna foram para Lula (entre municípios; intervalo de "
            f"{num(r['liquido_por_100_lula_ic'][0], 0)} a {num(r['liquido_por_100_lula_ic'][1], 0)})",
        )
        + cartao(
            f"{num(r['explica_pp'], 2)} pp",
            f"dos {num(abs(r['swing_h2h_pp']), 2)} pp que Flávio perdeu entre os dois saem de quem voltou a votar",
        )
        + "</div>"
    )
    h += X.resposta(T)
    h += "<h3>A conta que as duas urnas fecham</h3>"
    c1 = d.get("comparacao_1t.json") or {}
    sw_mun = (c1.get("brasil") or {}).get("swing_h2h_flavio_pp")
    h += X.conta(T, sw_mun) + X.tabela_margens(T)
    h += "<h3>Quem faltou no 1º turno e votou no 2º</h3>"
    h += X.regressao_principal(T)
    h += F.fig_dispersao(T)
    h += X.robustez_texto(T) + X.tabela_robustez(T)
    h += X.secoes_contrario(T)
    h += F.fig_barras_uf(T)
    h += X.por_uf_texto(T) + X.ecologica(T)
    h += "<h3>Quantos voltaram</h3>" + X.rotatividade(T)
    h += "<h3>A matriz de hipótese</h3>" + X.metodo_matriz(T)
    h += S.fig_sankey(T)
    h += S.fig_sankey_mudou(T)
    h += (
        '<details class="ct-det"><summary>A matriz em números e as linhas publicadas usadas como prior</summary>'
        + S.tabela_matriz(T)
        + X.tabela_linhas_candidato(T)
        + "</details>"
    )
    h += "<h3>O que sobrevive à troca da prior</h3>"
    h += (
        X.tabela_sensibilidades(T)
        + X.sobrevive(T)
        + X.tabela_decomposicao(T)
        + X.sem_informacao(T)
    )
    h += "<h3>A terceira via contra as pesquisas</h3>"
    h += (
        X.terceira_contrario(T)
        + X.tabela_pesquisas(T)
        + X.terceira_regressao(T)
        + X.reserva(T)
    )
    h += X.juizo(T)
    h += X.limites_cap(T)
    return h
