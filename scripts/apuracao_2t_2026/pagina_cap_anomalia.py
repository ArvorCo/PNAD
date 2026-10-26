"""Capítulo "Grupos" do dossiê do 2º turno: mistura gaussiana sobre as seções nos dois turnos.

Interface: ``render(d, cap) -> str`` (``analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md``).
Lê ``anomalia_ml.json`` (``analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md``, seção 6);
ausente, levanta ``KeyError`` e o esqueleto mostra "capítulo em preparação". O arquivo
pesado ``anomalia_secoes.json.gz`` só alimenta o mapa de pontos: sem ele, a figura
mostra o aviso padrão e o resto renderiza. Ordem fixa da seção 8 do contrato.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import Capitulo, Dados, limites

from . import pagina_fig_anomalia as F
from . import pagina_fig_anomalia_b as FB
from . import pagina_fig_anomalia_base as B
from . import pagina_texto_anomalia as T
from .pagina_comum import cabeca

BOTAO_POLITIZE = (
    '<p class="mapa-brasil"><a href="politizese.html" style="display:inline-flex;'
    "align-items:center;min-height:48px;padding:10px 18px;border-radius:8px;"
    'background:#151812;color:#fff;font-weight:700;text-decoration:none">'
    "Ver o grupo de qualquer seção no Politize-se</a></p>"
)


def render(d: Dados, cap: Capitulo) -> str:
    A = d.get(B.ARQUIVO)
    if A is None:
        raise KeyError(B.ARQUIVO)
    h = cabeca(cap, T.titulo(A), T.lead(A))
    h += T.como_ler(A) + T.cartoes(A) + T.abertura(A)
    h += "<h3>O espaço: nove frações do eleitorado, dois turnos</h3>"
    h += T.espaco(A)
    h += "<h3>Quantos grupos</h3>"
    h += T.escolha_k(A) + F.fig_bic(A) + F.tabela_bic(A)
    h += "<h3>Convergência, e o k-means como contraste</h3>"
    h += T.convergencia(A) + F.fig_kmeans(A)
    h += f"<h3>Os {B.extenso(B.k_de(A))} grupos</h3>"
    h += T.grupos(A) + F.fig_grupos(A) + F.fig_regiao(A) + FB.fig_pca(A)
    h += "<h3>O grupo atípico</h3>"
    h += T.atipico(A) + FB.fig_voto(A) + FB.tabela_seis_sinais(A)
    h += FB.tabela_sinais(A) + FB.tabela_modelo(A)
    h += FB.fig_mapa(A) + BOTAO_POLITIZE + FB.tabela_amostras(A)
    h += T.contrario(A)
    h += limites(T.limites_itens(A))
    return h
