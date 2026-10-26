"""Extrai métricas em processos separados e reconcilia contagens com o BU."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .coleta import ROOT, ler_compacto
from .compacto import ler_para_analise
from .complementos import carregar as carregar_complementos
from .parser import VERSAO, analisar, analisar_textos
from .pleito import PRIMEIRO, Pleito

METRICAS = ROOT / "data/outputs/logs_urnas_2026.sqlite"
CHAVES = ("uf", "mun", "zona", "secao")
CAMPOS_BU = (
    "uf,mun,zona,secao,numero_interno_urna,comparecimento,hab_biometria,"
    "hab_ano_nascimento,comp_sem_biometria,modelo_urna,tipo_urna,tipo_arquivo,"
    "n_cargas,fase,pleito,codigo_carga"
)


def identidade_no_log(r: dict, bu: dict) -> dict:
    """Número interno e código de carga do BU contra o que o próprio log registra.

    ``None`` quando o BU não traz o campo (BU suplementar) ou o log não registra
    código de carga para a urna do BU (o registro é da cerimônia de carga)."""
    urna = bu.get("numero_interno_urna")
    alvo = f"{int(urna):08d}" if urna is not None else None
    cargas = r.get("cargas_log", {})
    carga_bu = bu.get("codigo_carga")
    return {
        "urna_bu_no_log": None if alvo is None else alvo in r.get("urnas_log", []),
        "outras_urnas_no_log": [u for u in r.get("urnas_log", []) if u != alvo],
        "carga_bu_no_log": (
            None
            if not carga_bu or alvo not in cargas
            else str(carga_bu) in cargas[alvo]
        ),
    }


def reconciliar(r: dict, bu: dict, pleito: int = 3220) -> dict:
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
    r["identidade_log"] = identidade_no_log(r, bu)
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
        "fase_ou_pleito_incompativel": bu.get("fase") == 2
        and bu.get("pleito") == pleito,
        "menos_de_30_ciclos": r["tempo_voto"]["n"] >= 30,
    }
    r["motivos_tempo"] = [k for k, ok in requisitos.items() if not ok]
    r["elegivel_tempo"] = not r["motivos_tempo"]
    return r


def processar(tarefa: tuple) -> tuple:
    key, raw, sha, bu, pleito, dia, pacote = tarefa
    try:
        if pacote is not None:
            if pacote["sha256_zip"] != sha:
                raise ValueError("Hash do original não confere")
            arquivos, omitidas = ler_para_analise(pacote)
            r = analisar_textos(arquivos, bu, dia, omitidas)
            r["guarda"] = pacote["formato"]
        else:
            if hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError("Hash do original não confere")
            r = analisar(raw, bu, dia)
        r = reconciliar(r, bu, pleito)
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


def carregar_bus(pleito: Pleito) -> dict:
    src = sqlite3.connect(f"file:{pleito.origem}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    bu = {
        tuple(r[k] for k in CHAVES): dict(r)
        for r in src.execute(f"SELECT {CAMPOS_BU} FROM bu")
    }
    src.close()
    for chave, r in carregar_complementos(pleito).items():
        if chave in bu:
            assert all(
                bu[chave][k] == v for k, v in r["bu"].items() if v is not None
            ), "BU suplementar diverge do banco histórico"
        else:
            bu[chave] = r["bu"]
    return bu


def executar(
    raw_path: Path | None = None,
    output: Path | None = None,
    workers: int = 4,
    acompanhar: bool = False,
    pleito: Pleito = PRIMEIRO,
    ufs: list[str] | None = None,
    limite: int = 0,
):
    """Padrões do 1º turno intocados; ``pleito`` troca origem, originais e métricas."""
    raw_path = raw_path or pleito.raw
    output = output or pleito.metricas
    bu = carregar_bus(pleito)
    output.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(output)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS metricas (
      uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, sha256 TEXT, versao TEXT,
      status TEXT, resumo TEXT, PRIMARY KEY(uf,mun,zona,secao)
    ) WITHOUT ROWID""")
    raw = sqlite3.connect(f"file:{raw_path}?mode=ro", uri=True)
    tem_compacto = bool(
        raw.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='compacto'"
        ).fetchone()
    )
    filtro = " AND uf IN (" + ",".join("?" for _ in ufs) + ")" if ufs else ""
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
                + filtro,
                ufs or [],
            ).fetchall()
            ids = [r for r in ids if tuple(r) not in feitos and tuple(r[:4]) in bu]
            if limite:
                ids = ids[:limite]
            for ini in range(0, len(ids), 200):
                tarefas = []
                for r in ids[ini : ini + 200]:
                    key = tuple(r[:4])
                    blob = raw.execute(
                        "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                        key,
                    ).fetchone()[0]
                    pacote = (
                        ler_compacto(raw, key)
                        if blob is None and tem_compacto
                        else None
                    )
                    tarefas.append(
                        (key, blob, r[4], bu[key], pleito.numero, pleito.dia, pacote)
                    )
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
