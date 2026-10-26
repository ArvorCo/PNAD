"""Capítulo "De onde veio o voto: 1º turno → 2º turno" (dossiê do 2º turno de 2026).

Vai do mais simples ao mais técnico: (a) a conta que as duas urnas fecham, que é
fato; (b) a resposta direta em três números (quem voltou a votar e para onde, para
onde foi a terceira via, quanto cruzou entre as bases); (c) os quatro cenários de
cruzamento, o Sankey com os números na fita e o que sobrevive a todos; (d) a
regressão ecológica de quem voltou a votar, na escala do município e da seção; (e)
os limites. Fonte única: ``transferencia.json`` (``scripts/apuracao-2t-2026-transferencia.py``).
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, cartao, checar, num
from apuracao_2026.pagina_fig_base import FLAVIO, LULA

from . import pagina_fig_transferencia as S
from . import pagina_fig_transferencia_b as F
from . import pagina_texto_transferencia as X
from . import pagina_texto_transferencia_b as Y
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
            "cruzamento.cenarios",
            "cruzamento.comparacao",
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
        f"Entre os dois turnos, Lula ganhou {num(c['ganho_lula'] / 1e6, 1)} milhões de votos e Flávio, "
        f"{num(c['ganho_flavio'] / 1e6, 1)} milhões. Este capítulo mostra de onde eles vieram: da terceira via, que saiu da "
        "cédula, de quem votou branco ou nulo e de quem não tinha ido votar no 1º turno. As urnas dão os totais; a divisão "
        "entre as origens é estimativa, não medição.",
    )
    h += X.CSS + Y.CSS
    # (a) A contabilidade das duas urnas: fato.
    h += "<h3>A conta que as duas urnas fecham</h3>"
    h += (
        '<div class="finding-grid">'
        + cartao(
            f"+{num(c['ganho_lula'] / 1e6, 2)} mi",
            "votos novos de Lula entre os turnos",
            LULA,
        )
        + cartao(
            f"+{num(c['ganho_flavio'] / 1e6, 2)} mi",
            "votos novos de Flávio entre os turnos",
            FLAVIO,
        )
        + cartao(
            f"{num(c['disponiveis'] / 1e6, 2)} mi",
            "liberados pela urna: terceira via, queda de branco e nulo e aumento do comparecimento",
        )
        + "</div>"
    )
    c1 = d.get("comparacao_1t.json") or {}
    sw_mun = (c1.get("brasil") or {}).get("swing_h2h_flavio_pp")
    h += X.conta(T, sw_mun) + X.tabela_margens(T)
    # (b) A resposta direta, em três números.
    h += "<h3>A resposta em três números</h3>" + Y.tres_numeros(T)
    # (c) Os cenários de cruzamento e o que sobrevive a todos.
    h += "<h3>Quatro cenários para o cruzamento entre as bases</h3>"
    h += Y.cenarios_intro(T) + Y.frase_grafico() + S.fig_sankey(T)
    h += Y.como_ler(T) + Y.sem_js(T)
    h += "<h4>Os quatro cenários lado a lado</h4>" + Y.tabela_cenarios(T)
    h += Y.muda_nao_muda(T)
    h += Y.terceira_contrario(T) + X.tabela_pesquisas(T)
    h += X.terceira_regressao(T) + X.reserva(T)
    h += (
        '<details class="ct-det"><summary>O método da matriz, as trocas de prior e as linhas publicadas</summary>'
        + X.metodo_matriz(T)
        + X.tabela_sensibilidades(T)
        + X.sobrevive(T)
        + X.tabela_decomposicao(T)
        + X.sem_informacao(T)
        + Y.tabela_cruzamento_publicado(T)
        + X.tabela_linhas_candidato(T)
        + S.tabela_matriz(T)
        + "</details>"
    )
    # (d) A regressão de quem voltou a votar, na escala do município e da seção.
    h += "<h3>Quem voltou a votar: a regressão sobre as urnas</h3>"
    h += (
        '<div class="finding-grid">'
        + cartao(
            f"{num(r['liquido_por_100_lula'], 0)} de 100",
            "eleitores a mais na urna foram para Lula (entre municípios; intervalo de "
            f"{num(r['liquido_por_100_lula_ic'][0], 0)} a {num(r['liquido_por_100_lula_ic'][1], 0)})",
            LULA,
        )
        + cartao(
            f"{num(r['explica_pp'], 2)} pp",
            f"dos {num(abs(r['swing_h2h_pp']), 2)} pp que Flávio perdeu entre os dois saem de quem voltou a votar",
        )
        + "</div>"
    )
    h += X.regressao_principal(T)
    h += F.fig_dispersao(T)
    h += X.robustez_texto(T) + X.tabela_robustez(T)
    h += X.secoes_contrario(T)
    h += F.fig_barras_uf(T)
    h += X.por_uf_texto(T) + X.ecologica(T)
    h += "<h4>Quantos voltaram</h4>" + X.rotatividade(T)
    # (e) Leitura da casa e limites.
    h += X.juizo(T)
    h += X.limites_cap(T)
    return h
