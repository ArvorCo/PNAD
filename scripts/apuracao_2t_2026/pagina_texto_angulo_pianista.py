"""Bloco "O log da célula do pianista" para o capítulo de seções do dossiê do 2º turno.

``bloco(d)`` devolve o HTML interno (sem ``<section>``). ``d`` é o conteúdo de
``angulo_pianista.json`` (gerado por ``scripts/apuracao-2t-2026-angulo-pianista.py``)
ou um ``Dados`` do dossiê; sem o JSON, devolve "". Todo número sai do JSON.
"""

from __future__ import annotations

from html import escape
from typing import Any

from apuracao_2026.pagina_comum import caixa, inteiro, nota, num, p, sinal, tabela

from .angulo_pianista_texto import (
    CAB_METRICAS,
    CAB_TOP,
    ic,
    linha_top,
    linhas_metricas,
    n2,
    resposta,
)

ARQUIVO = "angulo_pianista.json"


def _json(d: Any) -> dict | None:
    if d is None:
        return None
    if hasattr(d, "get") and not isinstance(d, dict):
        d = d.get(ARQUIVO)
    if not isinstance(d, dict) or not {"celula", "grupos", "comparacoes"} <= set(d):
        return None
    return d


def bloco(d: Any) -> str:
    J = _json(d)
    if J is None:
        return ""
    c, g = J["celula"], J["grupos"]
    gc = g["celula"]
    v = J.get("voto_ja_medido") or {}
    r = resposta(J)
    C = J["comparacoes"]
    h = "<h3>O log da célula do pianista</h3>"
    h += caixa(
        "io",
        "Como ler. ",
        "O pianista é o mesário que libera eleitor ausente. Se isso acontecesse em série, o log "
        "da urna mostraria liberações sem biometria juntas numa janela de tempo (fim do dia ou "
        "rajada), em ritmo rápido ou regular, com habilitação curta, e diferente do 1º turno "
        "da mesma seção e das vizinhas. Relemos o log de cada seção para procurar esse desenho.",
    )
    h += p(
        f"A célula tem {inteiro(c['secoes'])} seções em {inteiro(c['municipios'])} municípios: "
        "comparecimento pelo menos 5 pp acima do 1º turno e salto da parcela sem biometria "
        f"reconhecida. Relemos os logs das {inteiro(c['com_log_2t'])} nos dois turnos, mais "
        f"{inteiro(g['vizinhas']['secoes'])} vizinhas sem sinal do mesmo município e "
        f"{inteiro(g['salto_sem_delta']['secoes'])} seções com o mesmo salto de biometria e "
        "sem alta de comparecimento.",
        "verificado",
    )
    h += p(escape(r[0]), "verificado")
    h += p(escape(r[1]), "verificado")
    h += p(escape(r[2]), "inferencia")
    h += p(escape(r[3]), "verificado")
    h += p(
        f"No voto, a mesma célula fica {n2(v.get('dif_fatia_flavio_vs_vizinhas_pp'))} pp "
        "na fatia de Flávio contra as vizinhas, diferença que já existia no 1º turno: em "
        f"diferença em diferenças, {sinal(v.get('did_fatia_flavio_pp'), 2)} pp (ep "
        f"{num(v.get('ep_did_fatia_flavio_pp'), 2)}).",
        "verificado",
    )
    h += tabela(
        CAB_METRICAS,
        linhas_metricas(J),
        "Métricas do log por seção, médias da célula e diferenças com IC de 95% "
        f"(bootstrap de municípios, {inteiro(J['bootstrap']['reamostragens'])} reamostragens).",
    )
    h += tabela(
        CAB_TOP,
        [linha_top(t, t["link"]) for t in J["top"]],
        f"As {len(J['top'])} seções da célula de maior força da marca; com a marca completa, "
        f"{inteiro(gc['marca_2t'])} de {inteiro(c['secoes'])}. O número da seção abre a "
        "ficha no Politize-se.",
    )
    h += nota(
        "hipotese",
        "Um mesário que digitasse o ano de nascimento no ritmo normal, depois de tentativas "
        "simuladas de digital, não deixaria marca no log. A ausência da marca enfraquece a "
        "hipótese; não a elimina. Decidem a ata da mesa (liberações por ano de nascimento, "
        "troca de urna, ocorrências, fila às 17h) e o caderno de votação (assinatura de cada "
        "eleitor liberado pelo documento; nome de falecido, de quem estava fora do país ou "
        "justificou).",
        "O que o log não alcança.",
    )
    dh = C["hab_nbio_p50_s"]["did_vizinhas"]
    h += p(
        "Tempo mediano da habilitação sem biometria, 2º menos 1º turno, célula menos "
        f"vizinhas: {ic(dh)} s"
        + (
            "; a liberação pelo documento ficou mais lenta, não mais curta."
            if (dh.get("estimativa") or 0) > 0
            else "."
        )
        + " Sinal pede explicação, não prova irregularidade."
    )
    return h
