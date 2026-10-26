"""Capítulo do dossiê do 2º turno: o que os logs das 499 mil urnas dizem.

Interface: ``render(d, cap) -> str`` (``analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md``).
Lê ``logs.json``, gerado por ``python3 scripts/apuracao-2t-2026-logs.py`` a partir
das métricas dos logs dos dois turnos, dos diagnósticos públicos por zona e do BU
por seção. Sete blocos, cada um com figura e abrindo pelo número mais forte.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, inteiro, limites

from . import pagina_fig_logs as F
from . import pagina_fig_logs_b as FB
from . import pagina_fig_logs_c as FC
from . import pagina_texto_logs as T
from . import pagina_texto_logs_clima as TC
from . import pagina_texto_logs_rdv as TR
from .pagina_comum import cabeca

ARQUIVOS = ("logs.json",)

BOTOES = (
    '<p class="mapa-brasil"><a href="politizese_mapa.html" style="display:inline-flex;'
    "align-items:center;min-height:48px;padding:10px 18px;border-radius:8px;"
    'background:#151812;color:#fff;font-weight:700;text-decoration:none">'
    "Abrir o mapa do Brasil com todos os locais de votação</a> "
    '<a href="logs_urnas_2026.html" style="display:inline-flex;align-items:center;'
    "min-height:48px;padding:10px 18px;border-radius:8px;border:1px solid #151812;"
    'color:#151812;font-weight:700;text-decoration:none">As 25 regras dos logs</a></p>'
)


def render(d: Dados, cap: Capitulo) -> str:
    L = d.get("logs.json")
    if L is None:
        raise KeyError("logs.json")
    h = cabeca(cap, T.titulo(L), T.lead(L))
    h += T.fonte(L) + T.cartoes(L)
    h += f"<h3>Cobertura: {inteiro(L['cobertura']['contagem_confere'])} logs fecham com o BU</h3>"
    h += T.cobertura(L) + F.fig_excecoes(L) + T.tabela_seis(L)
    h += "<h3>A regra 2: a urna religada não é erro técnico</h3>"
    h += T.regra2(L) + F.fig_regra2(L)
    h += "<h3>O que persiste do 1º para o 2º turno</h3>"
    h += T.persistencia(L) + F.fig_matriz(L) + F.fig_persistencia(L)
    h += "<h3>A cadência do dia: a votação acabou às 17h</h3>"
    h += T.cadencia(L) + FB.fig_cadencia(L) + FB.fig_cadencia_regioes(L)
    h += T.tabela_sinais(L) + T.tabela_depois19(L)
    h += "<h3>Reinícios e bateria durante a votação</h3>"
    h += T.reinicios(L) + FB.fig_reinicio_hora(L)
    h += T.bateria(L) + FB.fig_bateria_chuva(L) + TC.clima_observado(L) + FB.fig_voto(L)
    h += "<h3>Metadados: série da memória de resultado, carga e zerésima</h3>"
    h += T.metadados(L) + FB.fig_serie_mr(L) + T.tabela_cargas(L)
    R = L.get("rdv")
    if R:
        h += "<h3>O registro digital do voto</h3>"
        h += TR.rdv(R) + FC.fig_rdv_nulos(R) + TR.tabela_limites(R)
    h += "<h3>O escore integrado: BU e log juntos</h3>"
    h += T.integrado(L) + FB.fig_integrado_mapa(L) + BOTOES + T.tabela_integrado(L)
    h += T.leitura(L)
    h += limites(T.limites_itens(L) + (TR.limites_itens() if R else []))
    return h
