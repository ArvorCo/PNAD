"""Extrai métricas em processos separados e reconcilia contagens com o BU."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .coleta import DESTINO, ORIGEM, ROOT
from .complementos import carregar as carregar_complementos
from .parser import VERSAO, analisar

METRICAS = ROOT / "data/outputs/logs_urnas_2026.sqlite"
CHAVES = ("uf", "mun", "zona", "secao")


def reconciliar(r: dict, bu: dict) -> dict:
    c = r["contagens"]
    tipos = r["tipos_habilitacao_computados"]
    esperado = {
        "computados": bu.get("comparecimento"),
        "biometrica": bu.get("hab_biometria"),
        "biografica": bu.get("hab_ano_nascimento"),
        "sem_biometria": bu.get("comp_sem_biometria"),
    }
    observado = {"computados": c.get("computados", 0), **tipos}
    diferencas = {
        k: observado.get(k, 0) - v if v is not None else None
        for k, v in esperado.items()
    }
    r["bu"] = {
        k: bu.get(k)
        for k in (
            "comparecimento",
            "hab_biometria",
            "hab_ano_nascimento",
            "comp_sem_biometria",
            "modelo_urna",
            "tipo_urna",
            "tipo_arquivo",
            "n_cargas",
            "fase",
            "pleito",
        )
    }
    r["diferencas_bu"] = diferencas
    r["contagem_confere"] = (
        diferencas["computados"] == 0 and r["ciclos"] == esperado["computados"]
    )
    r["biometria_confere"] = (
        all(diferencas[k] == 0 for k in tipos if k in esperado)
        and all(
            diferencas[k] == 0 for k in ("biometrica", "biografica", "sem_biometria")
        )
        and tipos.get("desconhecida", 0) == 0
    )
    if any(esperado[k] is None for k in ("biometrica", "biografica", "sem_biometria")):
        r["biometria_confere"] = None  # BU sem campos: não há discrepância mensurável.
    requisitos = {
        "contagem_nao_reconciliada": r["contagem_confere"],
        "sequencia_temporal_inconsistente": r["tempos_validos"],
        "zeresima_anterior_nao_localizada": r["zeresima_antes"],
        "encerramento_posterior_nao_localizado": r["encerramento_depois"],
        "linhas_malformadas": not c.get("linhas_invalidas", 0),
        "fase_ou_pleito_incompativel": bu.get("fase") == 2 and bu.get("pleito") == 3220,
        "menos_de_30_ciclos": r["tempo_voto"]["n"] >= 30,
    }
    r["motivos_tempo"] = [k for k, ok in requisitos.items() if not ok]
    r["elegivel_tempo"] = not r["motivos_tempo"]
    return r


def processar(tarefa: tuple) -> tuple:
    key, raw, sha, bu = tarefa
    try:
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError("Hash do original não confere")
        r = reconciliar(analisar(raw, bu), bu)
        return (
            *key,
            sha,
            VERSAO,
            "ok",
            json.dumps(r, ensure_ascii=False, separators=(",", ":")),
        )
    except (ValueError, KeyError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        return (
            *key,
            sha,
            VERSAO,
            "erro",
            json.dumps({"erro": type(exc).__name__ + ": " + str(exc)[:180]}),
        )


def executar(
    raw_path: Path = DESTINO,
    output: Path = METRICAS,
    workers: int = 4,
    acompanhar: bool = False,
):
    src = sqlite3.connect(f"file:{ORIGEM}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    campos = "uf,mun,zona,secao,numero_interno_urna,comparecimento,hab_biometria,hab_ano_nascimento,comp_sem_biometria,modelo_urna,tipo_urna,tipo_arquivo,n_cargas,fase,pleito"
    bu = {
        tuple(r[k] for k in CHAVES): dict(r)
        for r in src.execute(f"SELECT {campos} FROM bu")
    }
    src.close()
    for chave, r in carregar_complementos().items():
        if chave in bu:
            assert all(
                bu[chave][k] == v for k, v in r["bu"].items() if v is not None
            ), "BU suplementar diverge do banco histórico"
        else:
            bu[chave] = r["bu"]
    con = sqlite3.connect(output)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS metricas (
      uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, sha256 TEXT, versao TEXT,
      status TEXT, resumo TEXT, PRIMARY KEY(uf,mun,zona,secao)
    ) WITHOUT ROWID""")
    raw = sqlite3.connect(f"file:{raw_path}?mode=ro", uri=True)
    inicio, total = time.monotonic(), 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        while True:
            feitos = {
                tuple(r)
                for r in con.execute(
                    "SELECT uf,mun,zona,secao,sha256 FROM metricas WHERE versao=?",
                    (VERSAO,),
                )
            }
            ids = raw.execute(
                "SELECT uf,mun,zona,secao,sha256 FROM arquivos WHERE status='ok'"
            ).fetchall()
            ids = [r for r in ids if tuple(r) not in feitos and tuple(r[:4]) in bu]
            for ini in range(0, len(ids), 200):
                tarefas = []
                for r in ids[ini : ini + 200]:
                    key = tuple(r[:4])
                    blob = raw.execute(
                        "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                        key,
                    ).fetchone()[0]
                    tarefas.append((key, blob, r[4], bu[key]))
                with con:
                    con.executemany(
                        "INSERT OR REPLACE INTO metricas VALUES (?,?,?,?,?,?,?,?)",
                        pool.map(processar, tarefas, chunksize=5),
                    )
                total += len(tarefas)
                print(
                    json.dumps(
                        {
                            "extraidos": total,
                            "segundos": round(time.monotonic() - inicio),
                        }
                    ),
                    flush=True,
                )
            if not acompanhar:
                break
            time.sleep(20)
    con.close()
    raw.close()
