"""Coleta retomável do log associado ao mesmo hash do BU já arquivado.

Um escritor SQLite, downloads limitados, hashes conferidos e originais preservados.
Não altera o banco da apuração. O catálogo registra também a ausência de log.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
ORIGEM = ROOT / "apuracao/data/secoes_2026.sqlite"
DESTINO = ROOT / "data/raw/tse_logs_2026/logs.sqlite"
BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3220/dados"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS catalogo (
 uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, hash TEXT, nome TEXT,
 sha256_esperado TEXT, bytes_esperados INTEGER, status_aux TEXT,
 PRIMARY KEY(uf,mun,zona,secao)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS arquivos (
 uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, sha256 TEXT,
 status TEXT, http INTEGER, obtido_em TEXT, erro TEXT, zip BLOB,
 PRIMARY KEY(uf,mun,zona,secao)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
"""


def abrir(path: Path = DESTINO) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def catalogar(con: sqlite3.Connection, origem: Path = ORIGEM) -> None:
    if con.execute("SELECT 1 FROM catalogo LIMIT 1").fetchone():
        return
    src = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
    cur = src.execute(
        "SELECT uf,mun,zona,secao,hash,log_nome,log_sha256,log_bytes,status_aux "
        "FROM secao WHERE nsp IS NULL OR nsp=0 OR nsp=secao"
    )
    with con:
        con.executemany("INSERT INTO catalogo VALUES (?,?,?,?,?,?,?,?,?)", cur)
        con.execute(
            "INSERT OR REPLACE INTO meta VALUES (?,?)",
            ("catalogado_em", datetime.now(timezone.utc).isoformat()),
        )
    src.close()


def url(r: dict) -> str:
    return (
        f"{BASE}/{r['uf']}/{r['mun']}/{r['zona']:04d}/{r['secao']:04d}/"
        f"{r['hash']}/{r['nome']}"
    )


class Cliente:
    def __init__(self, rps: float):
        self.intervalo = 1 / rps
        self.proxima = 0.0
        self.lock = threading.Lock()
        self.local = threading.local()

    def ficha(self) -> None:
        with self.lock:
            agora = time.monotonic()
            alvo = max(agora, self.proxima)
            self.proxima = alvo + self.intervalo
        time.sleep(max(0, alvo - time.monotonic()))

    def obter(self, r: dict) -> tuple:
        if not hasattr(self.local, "session"):
            self.local.session = requests.Session()
            self.local.session.headers.update(HEADERS)
        status, codigo, erro, corpo = "erro", None, None, None
        for tentativa in range(4):
            self.ficha()
            try:
                res = self.local.session.get(url(r), timeout=(10, 40))
                codigo = res.status_code
                if codigo == 200:
                    corpo = res.content
                    digest = hashlib.sha256(corpo).hexdigest()
                    if not corpo.startswith(b"PK"):
                        status, erro = "formato_invalido", "Resposta não é ZIP"
                    elif r["sha256_esperado"] and digest != r["sha256_esperado"]:
                        status, erro = "hash_divergente", "Difere da coleta do BU"
                    else:
                        status = "ok"
                    break
                if codigo == 404:
                    status = "http_404"
                    break
                erro = f"HTTP {codigo}"
                if codigo in (403, 429):
                    try:
                        pausa = float(res.headers.get("Retry-After", "30"))
                    except ValueError:
                        pausa = 30
                    with self.lock:
                        self.proxima = max(
                            self.proxima, time.monotonic() + min(300, pausa)
                        )
                elif codigo < 500:
                    break
            except requests.RequestException as exc:
                erro = type(exc).__name__
            time.sleep(min(20, 2**tentativa))
        return (
            r["uf"],
            r["mun"],
            r["zona"],
            r["secao"],
            hashlib.sha256(corpo).hexdigest() if corpo else None,
            status,
            codigo,
            datetime.now(timezone.utc).isoformat(),
            erro,
            corpo,
        )


def coletar(path: Path, limite: int, workers: int, rps: float, ufs: list[str]) -> None:
    con = abrir(path)
    catalogar(con)
    # Um índice de metadados evita visitar as páginas dos ZIPs em cada retomada.
    con.execute(
        "CREATE INDEX IF NOT EXISTS arquivos_estado ON arquivos(status,uf,mun,zona,secao,sha256)"
    )
    feitos_antes = {
        tuple(r)
        for r in con.execute(
            "SELECT uf,mun,zona,secao FROM arquivos WHERE status != 'erro'"
        )
    }
    # Intercalar as UFs dá cobertura inicial de todos os estratos, sem escolher
    # seção pelo resultado eleitoral. Ao fim, todo o catálogo elegível é percorrido.
    filtro = " AND c.uf IN (" + ",".join("?" for _ in ufs) + ")" if ufs else ""
    rows = con.execute(
        "SELECT c.* FROM catalogo c WHERE c.nome IS NOT NULL AND c.hash IS NOT NULL "
        + filtro
        + " ORDER BY c.secao,c.zona,c.mun,c.uf",
        ufs,
    ).fetchall()
    rows = [
        r
        for r in rows
        if tuple(r[k] for k in ("uf", "mun", "zona", "secao")) not in feitos_antes
    ]
    if limite:
        rows = rows[:limite]
    print(
        json.dumps({"pendentes": len(rows), "rps": rps, "workers": workers}), flush=True
    )
    it = iter(rows)
    cliente = Cliente(rps)
    inicio = time.monotonic()
    feitos, bons, tamanho = 0, 0, 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pendentes = set()
        esgotado = False
        while pendentes or not esgotado:
            while len(pendentes) < workers * 2 and not esgotado:
                r = next(it, None)
                if r is None:
                    esgotado = True
                else:
                    pendentes.add(pool.submit(cliente.obter, dict(r)))
            if not pendentes:
                break
            prontos, pendentes = wait(pendentes, return_when=FIRST_COMPLETED)
            for p in prontos:
                r = p.result()
                con.execute(
                    "INSERT OR REPLACE INTO arquivos VALUES (?,?,?,?,?,?,?,?,?,?)", r
                )
                feitos += 1
                bons += r[5] == "ok"
                tamanho += len(r[-1] or b"")
                if feitos % 100 == 0:
                    con.commit()
                if feitos % 500 == 0:
                    con.execute("PRAGMA wal_checkpoint(PASSIVE)")
                    print(
                        json.dumps(
                            {
                                "feitos": feitos,
                                "ok": bons,
                                "MB": round(tamanho / 1e6),
                                "segundos": round(time.monotonic() - inicio),
                            }
                        ),
                        flush=True,
                    )
                    if shutil.disk_usage(path.parent).free < 15 * 1024**3:
                        raise RuntimeError(
                            "Coleta interrompida: reserva de disco abaixo de 15 GiB"
                        )
    con.commit()
    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    con.close()
    print(json.dumps({"concluido": feitos, "ok": bons}), flush=True)
