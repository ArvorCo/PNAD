"""Ciclos de habilitação por seção, relidos dos logs originais, para o ângulo do pianista.

As métricas publicadas (``logs_urnas_{2t_,}2026.sqlite``, coluna ``resumo``) guardam a
contagem por tipo de habilitação e os cômputos por hora, mas não a hora de cada
habilitação por tipo. Este módulo relê o original com o MESMO leitor (versão 12,
``apuracao_logs.parser``), captura a lista de ciclos que o leitor já monta e devolve
agregados por seção: nenhuma sequência individual sai daqui.

Correspondência com o BU (conferida nas métricas: ``diferencas_bu`` = 0 por tipo):
``biografica`` do log = habilitado por ano de nascimento no BU (biometria cadastrada,
não reconhecida); ``sem_biometria`` do log = eleitor sem biometria cadastrada. As duas
juntas são as habilitações "sem biometria reconhecida", a parcela da regra
``salto_bio`` de ``secoes_sinais``.

Hora de Brasília: hora local do log + deslocamento do município (8 menos a hora modal
do primeiro cômputo das suas seções), a mesma regra de ``logs_cadencia``.
"""

from __future__ import annotations

import math
import sqlite3
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import pairwise
from typing import Any

from apuracao_logs import parser
from apuracao_logs.coleta import ler_compacto
from apuracao_logs.compacto import ler_para_analise
from apuracao_logs.pleito import PLEITOS, Pleito
from apuracao_logs.processamento import carregar_bus

NBIO = ("biografica", "sem_biometria")
ULTIMA_HORA = 16  # 16:00 em diante, hora de Brasília (votação até 17:00)
CONTINGENCIA = (3, 4, 6)

_CAPTURA: list = []
_ORIGINAL = parser.resumir


def _resumir_capturando(ciclos, invalidar, distribuicao):
    _CAPTURA.append(ciclos)
    return _ORIGINAL(ciclos, invalidar, distribuicao)


def _ciclos(pleito: Pleito, raw: sqlite3.Connection, chave: tuple, bu: dict):
    """Resumo do leitor e a lista de ciclos da seção (ou ``None`` sem original)."""
    linha = raw.execute(
        "SELECT zip, sha256 FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=? "
        "AND status='ok'",
        chave,
    ).fetchone()
    if linha is None:
        return None, None
    blob, _sha = linha
    parser.resumir = _resumir_capturando
    _CAPTURA.clear()
    try:
        if blob is None:
            pacote = ler_compacto(raw, chave)
            if pacote is None:
                return None, None
            arquivos, omitidas = ler_para_analise(pacote)
            r = parser.analisar_textos(arquivos, bu, pleito.dia, omitidas)
        else:
            r = parser.analisar(blob, bu, pleito.dia)
    finally:
        parser.resumir = _ORIGINAL
    return r, (_CAPTURA[-1] if _CAPTURA else [])


def _mediana(v: list[float]) -> float | None:
    return float(statistics.median(v)) if v else None


def p_rajada(n: int, n_nbio: int, k: int) -> float | None:
    """Chance aproximada de uma sequência de ≥ k habilitações sem biometria seguidas
    se a ordem dos eleitores fosse aleatória: 1 − exp(−n(1−p)p^k), p = parcela."""
    if n < 2 or k < 1 or n_nbio < 1:
        return None
    pp = n_nbio / n
    if pp >= 1:
        return 1.0
    return float(1 - math.exp(-n * (1 - pp) * pp**k))


def medir(r: dict, ciclos: list, off: int, bu: dict) -> dict[str, Any]:
    """Agregados de uma seção num turno. ``off`` em horas (log local → Brasília)."""
    c = sorted((x for x in ciclos if x.get("fim") is not None), key=lambda x: x["fim"])
    n = len(c)
    nb = [x for x in c if x["tipo"] in NBIO]
    validos = bool(r.get("tempos_validos"))
    cont = r.get("contagens") or {}

    def hb(t: float) -> float:
        return t / 3600 + off

    ult_todos = sum(hb(x["fim"]) >= ULTIMA_HORA for x in c)
    ult_nb = sum(hb(x["fim"]) >= ULTIMA_HORA for x in nb)
    run = best = 0
    pares_nb, pares = [], []
    for a, b in pairwise(c):
        if validos and a["urna"] == b["urna"] and a["sessao"] == b["sessao"]:
            d = b["fim"] - a["fim"]
            if d >= 0:
                pares.append(d)
                if a["tipo"] in NBIO and b["tipo"] in NBIO:
                    pares_nb.append(d)
    for x in c:
        run = run + 1 if x["tipo"] in NBIO else 0
        best = max(best, run)
    hab = [
        x["hab"] - x["ident"]
        for x in c
        if validos and x["ident"] is not None and x["hab"] >= x["ident"]
    ]
    hab_nb = [
        x["hab"] - x["ident"]
        for x in nb
        if validos and x["ident"] is not None and x["hab"] >= x["ident"]
    ]
    hab_b = [
        x["hab"] - x["ident"]
        for x in c
        if validos
        and x["tipo"] == "biometrica"
        and x["ident"] is not None
        and x["hab"] >= x["ident"]
    ]
    voto = [x["fim"] - x["hab"] for x in c if validos and x["fim"] >= x["hab"]]
    tipos = Counter(x["tipo"] for x in c)
    med_int = _mediana(pares)
    med_int_nb = _mediana(pares_nb) if len(pares_nb) >= 4 else None
    cv_nb = None
    if validos and len(pares_nb) >= 4:
        m = statistics.mean(pares_nb)
        cv_nb = float(statistics.pstdev(pares_nb) / m) if m > 0 else None
    ultima_nb = max((hb(x["fim"]) for x in nb), default=None)
    reinicios = int(cont.get("reinicios_sistema_em_votacao", 0)) + int(
        cont.get("reinicios_durante_votacao", 0)
    )
    contingencia = (bu.get("tipo_urna") in CONTINGENCIA) or (
        (bu.get("n_cargas") or 1) > 1
    )
    return {
        "n": n,
        "n_nbio": len(nb),
        "n_ano_nasc": tipos.get("biografica", 0),
        "n_sem_cadastro": tipos.get("sem_biometria", 0),
        "pct_nbio": round(100 * len(nb) / n, 3) if n else None,
        "nbio_ultima_hora": ult_nb,
        "pct_nbio_na_ultima_hora": round(100 * ult_nb / len(nb), 3) if nb else None,
        "pct_todos_na_ultima_hora": round(100 * ult_todos / n, 3) if n else None,
        "hora_ultima_nbio": round(ultima_nb, 4) if ultima_nb is not None else None,
        "maior_sequencia_nbio": best,
        "p_sequencia": p_rajada(n, len(nb), best),
        "intervalo_p50_s": med_int,
        "intervalo_nbio_p50_s": med_int_nb,
        "pares_nbio": len(pares_nb),
        "cv_intervalo_nbio": round(cv_nb, 4) if cv_nb is not None else None,
        "hab_p50_s": _mediana(hab),
        "hab_nbio_p50_s": _mediana(hab_nb),
        "hab_bio_p50_s": _mediana(hab_b),
        "voto_p50_s": _mediana(voto),
        "reinicios_votacao": reinicios,
        "urnas": int(r.get("urnas") or 0),
        "contingencia": bool(contingencia),
        "tempos_validos": validos,
    }


def _trabalho(tarefa: tuple) -> list[tuple]:
    numero, itens = tarefa
    pleito = PLEITOS[numero]
    raw = sqlite3.connect(f"file:{pleito.raw}?mode=ro", uri=True)
    out = []
    try:
        for chave, bu, off in itens:
            try:
                r, ciclos = _ciclos(pleito, raw, chave, bu)
            except (ValueError, KeyError, OSError, RuntimeError, AssertionError) as e:
                out.append((chave, {"erro": type(e).__name__}))
                continue
            if r is None:
                out.append((chave, {"erro": "sem_original"}))
                continue
            out.append((chave, medir(r, ciclos, off, bu)))
    finally:
        raw.close()
    return out


def deslocamentos(pleito: Pleito) -> dict[tuple[str, str], int]:
    """8 − hora local modal do primeiro cômputo, por município (regra de ``logs_cadencia``)."""
    con = sqlite3.connect(f"file:{pleito.metricas}?mode=ro", uri=True)
    horas: dict[tuple[str, str], Counter] = {}
    for uf, mun, s in con.execute(
        "SELECT uf, mun, json_extract(resumo, '$.primeiro_computo_s') FROM metricas "
        "WHERE status='ok' AND uf != 'ZZ'"
    ):
        if s is not None:
            horas.setdefault((uf, mun), Counter())[int(s) // 3600] += 1
    con.close()
    return {k: 8 - c.most_common(1)[0][0] for k, c in horas.items()}


def extrair(
    numero: int, chaves: list[tuple], workers: int = 8, lote: int = 40
) -> dict[tuple, dict]:
    """Métricas por seção de um turno, em processos separados."""
    pleito = PLEITOS[numero]
    bus = carregar_bus(pleito)
    off = deslocamentos(pleito)
    itens = [
        (k, bus[k], off.get((k[0], k[1]), 0))
        for k in chaves
        if k in bus and (k[0], k[1]) in off
    ]
    tarefas = [(numero, itens[i : i + lote]) for i in range(0, len(itens), lote)]
    out: dict[tuple, dict] = {}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for res in pool.map(_trabalho, tarefas):
            out.update(res)
    return out
