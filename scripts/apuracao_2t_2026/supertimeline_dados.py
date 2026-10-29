"""Três relógios eleitorais, com intervalos explícitos e bases independentes."""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta

from .encerramento_dados import BANCO, CAMPOS, CORTES, SAIDA, deslocamento
from .encerramento_logs import P, elegibilidade, fontes

BASE = datetime(2026, 10, 25)
VERSAO = 1


def instante(texto, off=0):
    d = datetime.fromisoformat(texto)
    if d.tzinfo is not None:
        raise ValueError("Carimbo com fuso inesperado")
    return int((d + timedelta(hours=off) - BASE).total_seconds())


def rotulo(s):
    return (BASE + timedelta(seconds=s)).strftime("%d/%m %H:%M:%S")


def horas_logs(legado, refazer=False):
    path = SAIDA / "logs-dia.json"
    arquivos = fontes()
    if path.exists() and not refazer:
        d = json.loads(path.read_text())
        if (
            d.get("arquivos") == arquivos
            and d.get("versao") == VERSAO
            and d["extrato_sha256"] == legado["extrato_sha256"]
        ):
            return d
    horas, digest = Counter(), hashlib.sha256()
    n = cobertas = total = 0
    primeiro, ultimo = 86400, 0
    with sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con:
        con.execute("ATTACH DATABASE ? AS logs", (f"file:{P.metricas}?mode=ro",))
        query = """SELECT s.uf,s.mun,s.zona,s.secao,s.log_sha256,
            b.comparecimento,m.sha256,m.status,m.resumo FROM secao s
            JOIN bu b USING(uf,mun,zona,secao)
            LEFT JOIN logs.metricas m USING(uf,mun,zona,secao)
            WHERE upper(s.uf)!='ZZ' AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY s.uf,s.mun,s.zona,s.secao"""
        for uf, mun, z, s, esperado, comp, sha, status, txt in con.execute(query):
            r = json.loads(txt) if txt else {}
            digest.update(
                json.dumps(
                    [uf, mun, z, s, esperado, comp, sha, status, r], sort_keys=True
                ).encode()
            )
            n += 1
            off = deslocamento(uf, mun)
            if elegibilidade(status, r, sha, esperado, comp, off):
                continue
            hs = {int(h) + off: v for h, v in r["computados_por_hora"].items()}
            if sum(hs.values()) != comp or any(h < 0 or h > 23 for h in hs):
                raise ValueError(
                    f"Histograma horário não recompõe seção: {uf}/{mun}/{z}/{s}"
                )
            horas.update(hs)
            cobertas += 1
            total += comp
            primeiro = min(primeiro, r["primeiro_computo_s"] + off * 3600)
            ultimo = max(ultimo, r["ultimo_computo_s"] + off * 3600)
            if n % 50000 == 0:
                print(f"Dia: {n} seções conferidas", flush=True)
    if fontes() != arquivos:
        raise ValueError("Fontes alteradas durante a leitura")
    if (digest.hexdigest(), cobertas, total, n) != (
        legado["extrato_sha256"],
        legado["cobertas"],
        legado["computados"],
        legado["secoes"],
    ):
        raise ValueError(
            "Extrato horário diverge da base de logs já publicada; regenerar ambas"
        )
    d = {
        "versao": VERSAO,
        "arquivos": arquivos,
        "extrato_sha256": digest.hexdigest(),
        "horas": [horas[h] for h in range(24)],
        "computados": total,
        "cobertas": cobertas,
        "primeiro_s": primeiro,
        "ultimo_s": ultimo,
        "regra": "Hora civil em Brasília: [HH:00:00, HH:59:59], sem interpolação. Mesmos logs elegíveis do gráfico publicado.",
    }
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    return d


def cortes(ultimo_s):
    # Preservar os cortes exatos publicados; madrugada cresce quando houver dados.
    fim = max(86400, ((ultimo_s + 3599) // 3600) * 3600)
    return (
        [h * 3600 - 1 for h in range(8, 18)]
        + CORTES
        + list(range(20 * 3600, fim + 1, 3600))
    )


def agregado(c, ufs, total, acumulado):
    n = c["secoes"]
    return {
        **dict(c),
        "parcela_secoes_pct": 100 * n / total,
        "encerradas_acumuladas": acumulado,
        "encerradas_pct": 100 * acumulado / total,
        "restantes": total - acumulado,
        "restantes_pct": 100 * (total - acumulado) / total,
        "comparecimento_pct": (
            100 * c["comparecimento"] / c["aptos"] if c["aptos"] else None
        ),
        "flavio_pct": 100 * c["flavio"] / c["validos"] if c["validos"] else None,
        "lula_pct": 100 * c["lula"] / c["validos"] if c["validos"] else None,
        "ufs": [
            {"uf": uf, "secoes": v, "pct": 100 * v / n}
            for uf, v in sorted(ufs.items(), key=lambda x: (-x[1], x[0]))
        ],
    }


def gravar_csv(d):
    comuns = [
        "inicio_exclusivo",
        "fim_inclusivo",
        "logs_intervalo",
        "logs_acumulado",
        "logs_acumulado_pct",
    ]
    campos = [
        *CAMPOS,
        "parcela_secoes_pct",
        "encerradas_acumuladas",
        "encerradas_pct",
        "restantes",
        "restantes_pct",
        "comparecimento_pct",
        "flavio_pct",
        "lula_pct",
        "principais_ufs",
        "cronologia_divergente",
    ]
    with (SAIDA / "supertimeline.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=comuns
            + [f"{k}_{c}" for k in ("fecho", "recebido") for c in campos],
            lineterminator="\n",
        )
        w.writeheader()
        for r in d["linhas"]:
            row = {
                "inicio_exclusivo": (
                    rotulo(r["inicio_exclusivo_s"])
                    if r["inicio_exclusivo_s"] is not None
                    else ""
                ),
                "fim_inclusivo": r["data_hora"],
                **{f"logs_{c}": v for c, v in r["logs"].items()},
            }
            for k in ("fecho", "recebido"):
                for c in campos:
                    row[f"{k}_{c}"] = (
                        "; ".join(f"{u['uf']}:{u['secoes']}" for u in r[k]["ufs"])
                        if c == "principais_ufs"
                        else r[k][c]
                    )
            w.writerow(row)


def gerar(refazer=False):
    legado = json.loads((SAIDA / "dados.json").read_text())
    logs = horas_logs(legado["logs"], refazer)
    dados, digest = [], hashlib.sha256()
    digest_legado = hashlib.sha256()
    with sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        query = """WITH votos AS (
            SELECT uf,mun,zona,secao,
            sum(CASE WHEN tipo=1 AND numero=22 THEN votos ELSE 0 END) flavio,
            sum(CASE WHEN tipo=1 AND numero=13 THEN votos ELSE 0 END) lula,
            sum(CASE WHEN tipo=2 THEN votos ELSE 0 END) brancos,
            sum(CASE WHEN tipo=3 THEN votos ELSE 0 END) nulos
            FROM voto_secao WHERE cargo=1 GROUP BY uf,mun,zona,secao)
            SELECT upper(b.uf) uf,b.mun,b.zona,b.secao,b.abertura,b.encerramento,b.emissao,
            b.id_confere,b.pleito,c.aptos,c.comparecimento,
            v.flavio,v.lula,v.brancos,v.nulos,s.dr_hr,s.n_hashes,s.hash,s.aux_json,s.bu_sha256
            FROM bu b JOIN secao s USING(uf,mun,zona,secao)
            JOIN bu_cargo c USING(uf,mun,zona,secao)
            LEFT JOIN votos v USING(uf,mun,zona,secao)
            WHERE upper(b.uf)!='ZZ' AND c.cargo=1 AND c.eleicao=6258
            AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY b.uf,b.mun,b.zona,b.secao"""
        for row in con.execute(query):
            r = dict(row)
            if r["id_confere"] != 1 or r["pleito"] != 3221 or r["n_hashes"] != 1:
                raise ValueError("Identidade ou pacote ambíguo na timeline")
            hs = [
                h for h in json.loads(r["aux_json"])["hashes"] if h["hash"] == r["hash"]
            ]
            if len(hs) != 1:
                raise ValueError("Pacote selecionado não identificado no aux")
            h = hs[0]
            oficial = datetime.strptime(h["dr"] + " " + h["hr"], "%d/%m/%Y %H:%M:%S")
            if oficial != datetime.fromisoformat(r["dr_hr"]):
                raise ValueError("Recebimento diverge do aux.json")
            digest.update(
                (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode()
            )
            campos_legado = [
                "uf",
                "mun",
                "zona",
                "secao",
                "abertura",
                "encerramento",
                "id_confere",
                "pleito",
                "aptos",
                "comparecimento",
                "flavio",
                "lula",
                "brancos",
                "nulos",
                "bu_sha256",
            ]
            original = {k: r[k] for k in campos_legado}
            digest_legado.update(
                (
                    json.dumps(original, sort_keys=True, ensure_ascii=False) + "\n"
                ).encode()
            )
            off = deslocamento(r["uf"], r["mun"])
            r["fecho"] = instante(r["encerramento"], off)
            r["recebido"] = instante(r["dr_hr"])
            em = instante(r["emissao"], off)
            r["cronologia_divergente"] = not r["fecho"] <= em <= r["recebido"]
            if r["fecho"] < 0 or r["recebido"] < 0:
                raise ValueError("Evento anterior ao dia do pleito")
            r["secoes"] = 1
            r["validos"] = r["flavio"] + r["lula"]
            dados.append(r)
    assert (
        digest_legado.hexdigest() == legado["extrato_ordenado_sha256"]
    ), "BUs divergem da versão anterior"
    for k in CAMPOS:
        assert sum(r[k] for r in dados) == legado["total"][k], k
    total = len(dados)
    assert total == legado["total"]["secoes"]
    cs = cortes(max(max(r["fecho"], r["recebido"]) for r in dados))
    trilhas = {}
    for chave in ("fecho", "recebido"):
        bins = [Counter(dict.fromkeys(CAMPOS, 0)) for _ in cs]
        ufs = [Counter() for _ in cs]
        eventos = Counter()
        divergentes = Counter()
        for r in dados:
            i = bisect.bisect_left(cs, r[chave])
            bins[i].update({k: r[k] for k in CAMPOS})
            ufs[i][r["uf"]] += 1
            eventos[r[chave]] += 1
            divergentes[i] += r["cronologia_divergente"]
        acumulado, linhas = 0, []
        for i, b in enumerate(bins):
            acumulado += b["secoes"]
            a = agregado(b, ufs[i], total, acumulado)
            a["cronologia_divergente"] = divergentes[i]
            linhas.append(a)
        trilhas[chave] = {
            "linhas": linhas,
            "primeiro_s": min(eventos),
            "ultimo_s": max(eventos),
            "segundos": [[s, v] for s, v in sorted(eventos.items())],
        }
    # Os segundos exatos de 17h vêm da releitura original; as horas vêm das métricas.
    antes17 = sum(logs["horas"][:17])
    no17 = legado["logs"]["intervalos"][0] - antes17
    if not 0 <= no17 <= logs["horas"][17]:
        raise ValueError("Ponte de 17h não recompõe os dois agregados")
    votos = [sum(logs["horas"][:8]), *logs["horas"][8:17], no17]
    votos.extend(legado["logs"]["intervalos"][1:-1])
    # O último cômputo está antes das 20h neste extrato; não imputar outra base.
    if logs["ultimo_s"] >= 20 * 3600:
        raise ValueError("Nova cauda após 20h: reler logs para os cortes adicionais")
    votos.extend([legado["logs"]["intervalos"][-1]] + [0] * (len(cs) - len(votos) - 1))
    assert len(votos) == len(cs) and sum(votos) == logs["computados"]
    acumulado, linhas = 0, []
    for i, (s, v) in enumerate(zip(cs, votos, strict=True)):
        acumulado += v
        linhas.append(
            {
                "fim_inclusivo_s": s,
                "inicio_exclusivo_s": cs[i - 1] if i else None,
                "data_hora": rotulo(s),
                "logs": {
                    "intervalo": v,
                    "acumulado": acumulado,
                    "acumulado_pct": 100 * acumulado / logs["computados"],
                },
                **{k: t["linhas"][i] for k, t in trilhas.items()},
            }
        )
    for original, nova in zip(legado["linhas"][:-1], linhas[10:30], strict=True):
        for campo in CAMPOS:
            assert original[campo] == nova["fecho"][campo], (campo, nova["data_hora"])
    d = {
        "versao": VERSAO,
        "dia": legado["dia"],
        "fuso": legado["fuso"],
        "extrato_bu_recebimento_sha256": digest.hexdigest(),
        "extrato_bu_legado_sha256": digest_legado.hexdigest(),
        "total": legado["total"],
        "logs_cobertura": legado["logs"],
        "logs_dia": logs,
        "linhas": linhas,
        "apos19_subtotal": legado["linhas"][-1],
        "trilhas": {
            k: {c: v for c, v in t.items() if c != "linhas"} for k, t in trilhas.items()
        },
        "recebimento": {
            "campo": "aux.json dr/hr do único hash selecionado",
            "regra": "Recebimento registrado do pacote, não início do envio nem instante de totalização. Conta uma seção uma vez.",
            "cronologia_divergente": sum(r["cronologia_divergente"] for r in dados),
            "limite": "Carimbos de recebimento mantidos mesmo nas 16 seções com divergência na ordem encerramento/emissão/recebimento; esses casos não servem para estimar a duração do trajeto.",
        },
    }
    (SAIDA / "supertimeline.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    )
    gravar_csv(d)
    print(
        json.dumps(
            {
                "computados": logs["computados"],
                "horas": logs["horas"],
                "primeiro_log": rotulo(logs["primeiro_s"]),
                "ultimo_log": rotulo(logs["ultimo_s"]),
                "ultimo_recebimento": rotulo(trilhas["recebido"]["ultimo_s"]),
                "linhas": len(linhas),
                "no_segundo_17h": no17,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return d
