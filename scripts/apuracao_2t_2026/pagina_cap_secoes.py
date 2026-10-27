"""Capítulo 8 do dossiê do 2º turno: seção por seção (encerramento, biometria, comparecimento).

Interface: ``render(d, cap) -> str`` (``analysis/apuracao_2t_2026/CONTRATO_DOSSIE.md``).
Lê ``secoes.json``, ``secoes_voto.json`` e ``secoes_ranking.json`` (da amostra ou do
banco completo, conforme o campo ``fonte``), ``presidente.json`` para os pesos por
UF, ``linha_do_tempo.json`` para a pausa do arquivo nacional e
``noticias_noite.json`` (pasta acima de ``dados/``) para a cronologia.
"""

from __future__ import annotations

import json

from apuracao_2026.pagina_comum import Capitulo, Dados, caixa, limites

from . import pagina_fig_biometria as FBIO
from . import pagina_fig_secoes as F
from . import pagina_fig_secoes_b as FB
from . import pagina_texto_biometria as TBIO
from . import pagina_texto_secoes as T
from .dataset import DICIONARIO, MANIFESTO, ler_manifesto
from .pagina_comum import MEMOS, ROOT, cabeca, inteiro

ARQUIVOS = ("secoes.json", "secoes_voto.json", "secoes_ranking.json")


# Entrada para o mapa do Brasil do Politize-se: todos os locais de votação, cada um com
# as seções lado a lado e o link para a seção no Politize-se.
BOTAO_MAPA = (
    '<p class="mapa-brasil"><a href="politizese_mapa.html" style="display:inline-flex;'
    "align-items:center;min-height:48px;padding:10px 18px;border-radius:8px;"
    'background:#151812;color:#fff;font-weight:700;text-decoration:none">'
    "Explorar todos os locais de votação no mapa do Brasil</a></p>"
)


def bloco_dataset(m: dict | None = None) -> str:
    """Download do dataset por seção; sem ``manifesto.json`` o bloco não aparece."""
    m = m or ler_manifesto()
    if not m:
        return ""
    csv_rel = m["arquivo"]
    pasta = MANIFESTO.parent.relative_to(ROOT / "docs")
    mb = f"{m['bytes'] / 1_000_000:.1f}".replace(".", ",")
    partes = ""
    if m.get("partes_por_uf"):
        partes = (
            f" Há também uma parte por estado em <code>{pasta}/uf/</code>, "
            "com as mesmas colunas."
        )
    return (
        '<p class="dataset"><a href="'
        + csv_rel.removeprefix("docs/")
        + '" download style="display:inline-flex;align-items:center;min-height:48px;'
        "padding:10px 18px;border-radius:8px;border:2px solid #151812;color:#151812;"
        'font-weight:700;text-decoration:none">Baixe os dados por seção '
        "(CSV, dicionário e hash)</a><br>"
        f"CSV comprimido com {mb} MB e {inteiro(m['n_linhas'])} linhas, uma por seção "
        "do Brasil e do exterior com boletim em ao menos um turno: votos, horários, "
        "urna, sinais e nível de atenção dos logs nos dois turnos. "
        f'<a href="{DICIONARIO.relative_to(ROOT / "docs")}">Dicionário das colunas</a>, '
        f'<a href="{pasta}/manifesto.json">manifesto com SHA-256</a>.{partes} '
        "Sinal pede explicação, não prova irregularidade.</p>"
    )


def noticias(d: Dados) -> dict | None:
    """``noticias_noite.json`` mora em ``analysis/apuracao_2t_2026``, fora de ``dados/``."""
    n = d.get("noticias_noite.json")
    if n is not None:
        return n
    arq = MEMOS / "noticias_noite.json"
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))
    return None


def habilitacao(B: dict | None) -> str:
    """Subseção "Como o eleitor foi habilitado" (vazia sem ``biometria.json``)."""
    if not B:
        return ""
    h = "<h3>Como o eleitor foi habilitado</h3>"
    h += caixa("io", "Como ler", f" {B['rotulo']}")
    h += TBIO.abertura(B) + FBIO.fig_categorias(B)
    h += TBIO.ufs(B) + FBIO.fig_ufs(B) + FBIO.fig_mapa_uf(B)
    h += TBIO.municipios(B) + FBIO.fig_mapa_mun(B) + FBIO.tabela_municipios(B)
    h += TBIO.histograma(B) + FBIO.fig_histograma(B)
    h += TBIO.modelos(B) + FBIO.fig_modelos(B)
    h += TBIO.voto(B)
    return h


def render(d: Dados, cap: Capitulo) -> str:
    S = d.get("secoes.json")
    V = d.get("secoes_voto.json")
    R = d.get("secoes_ranking.json")
    if S is None or V is None or R is None:
        raise KeyError("secoes.json, secoes_voto.json ou secoes_ranking.json")
    P = d.get("presidente.json")
    L = d.get("linha_do_tempo.json")
    FB.escreve_csv(R)
    h = cabeca(cap, T.titulo(S), T.lead(S))
    h += T.fonte(S) + T.cartoes(S)
    h += "<h3>As urnas não ficaram abertas até as 19h</h3>"
    h += T.encerramento(S) + F.fig_encerramento(S, P)
    h += "<h3>O atraso foi na transmissão</h3>"
    h += T.recebimento(S) + F.fig_emissao_recebimento(S, L)
    h += T.noticias(noticias(d)) + T.leitura_horario(S)
    h += "<h3>Comparecimento: alta geral, pequena</h3>"
    h += T.comparecimento(S) + F.fig_comparecimento(S, P)
    h += habilitacao(d.get("biometria.json"))
    h += "<h3>Biometria: cadastro, leitor e a hipótese do “pianista”</h3>"
    h += T.biometria(S, R, V)
    h += "<h3>O voto nas seções com sinal</h3>"
    h += T.voto(V) + FB.fig_did(V)
    h += T.tabela_2x2x2_texto(V) + FB.tabela_2x2x2(V) + T.tabela_e_extras(S, V)
    h += "<h3>As mais atípicas</h3>"
    h += T.ranking(R) + FB.fig_mapa(R) + BOTAO_MAPA + bloco_dataset()
    h += FB.tabela_ranking(R)
    h += T.fiscal_e_log()
    h += limites(T.limites_itens(S))
    return h
