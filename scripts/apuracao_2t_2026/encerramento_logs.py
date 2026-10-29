"""Cômputos nos cortes exatos: métricas reconciliadas e releitura da cauda."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from itertools import islice

from apuracao_logs.coleta import ler_compacto
from apuracao_logs.compacto import ler_para_analise
from apuracao_logs.parser import segundos, textos_zip
from apuracao_logs.pleito import PLEITOS

from .encerramento_dados import BANCO, CORTES, ROOT, deslocamento, faixa

P = PLEITOS[3221]
EVENTO = re.compile(
    r"^([^\t\r\n]+)\t[^\t\r\n]+\t([^\t\r\n]+)\t[^\t\r\n]+"
    r"\tO voto do eleitor foi computado\t[^\r\n]*$",
    re.MULTILINE,
)


def contar_textos(arquivos, urnas, off):
    """Mesmos dias/urnas do leitor; uma linha duplicada entra uma vez."""
    vistos, horarios = set(), Counter()
    for _, texto in arquivos:
        for m in EVENTO.finditer(texto):
            data, urna = m[1], m[2]
            if data[:10] not in P.dias or urna not in urnas or m[0] in vistos:
                continue
            vistos.add(m[0])
            horarios[segundos(data, P.dias) + off * 3600] += 1
    return horarios


def elegibilidade(status, r, sha, esperado, comp, off):
    if status != "ok":
        return "sem_log_utilizavel"
    if not esperado:
        return "sem_hash_no_catalogo"
    if sha != esperado:
        return "hash_divergente"
    if r.get("bu", {}).get("pleito") != 3221 or r.get("bu", {}).get("fase") != 2:
        return "pleito_fase"
    if not r.get("tempos_validos") or not r.get("computados_por_hora_confiavel"):
        return "relogio"
    if (
        not r.get("contagem_confere")
        or r.get("contagens", {}).get("computados") != comp
    ):
        return "contagem"
    primeiro, ultimo = r.get("primeiro_computo_s"), r.get("ultimo_computo_s")
    if primeiro is None or ultimo is None:
        return "sem_computos"
    if not 0 <= primeiro + off * 3600 <= ultimo + off * 3600 < 86400:
        return "fora_dia"
    return None


def horarios_reconferidos(tarefa):
    """Relê o original e reconcilia cada segundo com as métricas arquivadas."""
    key, sha, r, off = tarefa
    with sqlite3.connect(f"file:{P.raw}?mode=ro", uri=True) as con:
        pacote = ler_compacto(con, key)
        if pacote:
            if pacote["sha256_zip"] != sha:
                raise ValueError(f"Hash do original divergente: {key}")
            arquivos, _ = ler_para_analise(pacote)
        else:
            raw = con.execute(
                "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                key,
            ).fetchone()[0]
            if hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError(f"Hash do ZIP divergente: {key}")
            arquivos = textos_zip(raw)
    hs = contar_textos(arquivos, set(r["urnas_log"]), off)
    por_hora = Counter()
    for s, n in hs.items():
        por_hora[str((s - off * 3600) // 3600)] += n
    if (
        sum(hs.values()) != r["contagens"]["computados"]
        or dict(por_hora) != r["computados_por_hora"]
        or min(hs) != r["primeiro_computo_s"] + off * 3600
        or max(hs) != r["ultimo_computo_s"] + off * 3600
    ):
        raise ValueError(f"Releitura não recompõe as métricas: {key}")
    return hs


def reler(tarefa):
    hs = horarios_reconferidos(tarefa)
    bins = [0] * (len(CORTES) + 1)
    for s, n in hs.items():
        bins[faixa(s)] += n
    return bins


def gerar_logs():
    arquivos_inicio = fontes()
    contagens = [0] * (len(CORTES) + 1)
    totais = Counter()
    exclusoes, ufs = Counter(), {}
    digest = hashlib.sha256()
    with sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con:
        con.execute("ATTACH DATABASE ? AS logs", (f"file:{P.metricas}?mode=ro",))
        cur = con.execute("""SELECT s.uf,s.mun,s.zona,s.secao,s.log_sha256,
            b.comparecimento,m.sha256,m.status,m.resumo FROM secao s
            JOIN bu b USING(uf,mun,zona,secao)
            LEFT JOIN logs.metricas m USING(uf,mun,zona,secao)
            WHERE upper(s.uf)!='ZZ' AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY s.uf,s.mun,s.zona,s.secao""")
        with ThreadPoolExecutor(max_workers=4) as pool:
            while batch := list(islice(cur, 1000)):
                tarefas = []
                for uf, mun, z, s, esperado, comp, sha, status, txt in batch:
                    r = json.loads(txt) if txt else {}
                    off = deslocamento(uf, mun)
                    motivo = elegibilidade(status, r, sha, esperado, comp, off)
                    digest.update(
                        json.dumps(
                            [uf, mun, z, s, esperado, comp, sha, status, r],
                            sort_keys=True,
                        ).encode()
                    )
                    totais["secoes"] += 1
                    totais["comparecimento_total"] += comp
                    u = ufs.setdefault(uf.upper(), Counter())
                    u["secoes"] += 1
                    if motivo:
                        exclusoes[motivo] += 1
                        totais["comparecimento_excluido"] += comp
                        continue
                    totais["cobertas"] += 1
                    totais["computados"] += comp
                    u["cobertas"] += 1
                    u["computados"] += comp
                    if r["ultimo_computo_s"] + off * 3600 <= CORTES[0]:
                        contagens[0] += comp
                        totais["inteiras_ate_17"] += 1
                    else:
                        tarefas.append(((uf, mun, z, s), sha, r, off))
                for bins in pool.map(reler, tarefas):
                    totais["logs_relidos"] += 1
                    contagens = [a + b for a, b in zip(contagens, bins, strict=True)]
                if totais["secoes"] % 25000 == 0:
                    print(
                        f"Logs: {totais['secoes']} seções conferidas; {totais['logs_relidos']} relidas",
                        flush=True,
                    )
    assert sum(contagens) == totais["computados"]
    assert totais["secoes"] == totais["cobertas"] + sum(exclusoes.values())
    assert (
        totais["comparecimento_total"]
        == totais["computados"] + totais["comparecimento_excluido"]
    )
    if arquivos_inicio != fontes():
        raise ValueError("Fontes alteradas durante a leitura dos logs")
    return {
        "evento": "O voto do eleitor foi computado",
        "regra": "Cômputos de todas as seções com logs utilizáveis no intervalo exato (início, fim]. Não identifica candidato, chegada à fila ou recebimento pelo TSE.",
        "criterios": "Mesmo hash do log associado ao BU, fase 2 e pleito 3221, relógio confiável, contagem reconciliada com comparecimento e ciclos, carimbos no dia em Brasília.",
        "fonte_metricas": str(P.metricas.relative_to(ROOT)),
        "fonte_logs": str(P.raw.relative_to(ROOT)),
        "extrato_sha256": digest.hexdigest(),
        "arquivos": arquivos_inicio,
        **dict(totais),
        "cobertura_secoes_pct": 100 * totais["cobertas"] / totais["secoes"],
        "cobertura_comparecimento_pct": 100
        * totais["computados"]
        / totais["comparecimento_total"],
        "exclusoes": dict(exclusoes),
        "ufs": {uf: dict(c) for uf, c in ufs.items()},
        "intervalos": contagens,
    }


def fontes():
    return {
        str(p.relative_to(ROOT)): {
            "bytes": p.stat().st_size,
            "mtime_ns": p.stat().st_mtime_ns,
        }
        for p in (BANCO, P.metricas, P.raw)
    }


def carregar_logs(saida, refazer=False):
    path = saida / "logs.json"
    if path.exists() and not refazer:
        d = json.loads(path.read_text())
        if d.get("arquivos") == fontes():
            return d
    d = gerar_logs()
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return d


def integrar(d, logs):
    if (
        logs["secoes"] != d["total"]["secoes"]
        or logs["comparecimento_total"] != d["total"]["comparecimento"]
    ):
        raise ValueError("Universo dos logs não corresponde ao gráfico de encerramento")
    d["logs"] = logs
    acumulado = 0
    for r, n in zip(d["linhas"], logs["intervalos"], strict=True):
        acumulado += n
        r["logs_computados_intervalo"] = n
        r["logs_computados_acumulados"] = acumulado
        r["logs_computados_acumulados_pct"] = 100 * acumulado / logs["computados"]
        r["logs_computados_intervalo_pct"] = 100 * n / logs["computados"]
    return d
