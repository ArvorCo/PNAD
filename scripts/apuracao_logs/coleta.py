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


def base_do_pleito(pleito: int) -> str:
    """Raiz dos dados por seção do pleito (3220 no 1º turno, 3221 no 2º)."""
    return f"https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna/{pleito}/dados"


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
CREATE TABLE IF NOT EXISTS compacto (
 uf TEXT, mun TEXT, zona INTEGER, secao INTEGER, formato TEXT,
 sha256_zip TEXT, bytes_zip INTEGER, diretorio TEXT, sha256_prefixo TEXT,
 sha256_zip_1t TEXT, linhas_prefixo_omitidas INTEGER, sha256_blob TEXT, blob BLOB,
 PRIMARY KEY(uf,mun,zona,secao)
) WITHOUT ROWID;
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


def url(r: dict, base: str = BASE) -> str:
    return (
        f"{base}/{r['uf']}/{r['mun']}/{r['zona']:04d}/{r['secao']:04d}/"
        f"{r['hash']}/{r['nome']}"
    )


class Cliente:
    def __init__(self, rps: float, base: str = BASE):
        self.base = base
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
                res = self.local.session.get(url(r, self.base), timeout=(10, 40))
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


def linha_compacta(chave: tuple, pacote: dict) -> tuple:
    return (
        *chave,
        pacote["formato"],
        pacote["sha256_zip"],
        pacote["bytes_zip"],
        (
            json.dumps(pacote["diretorio"], ensure_ascii=False)
            if pacote["diretorio"]
            else None
        ),
        pacote.get("sha256_prefixo"),
        pacote.get("sha256_zip_1t"),
        pacote.get("linhas_prefixo_omitidas", 0),
        hashlib.sha256(pacote["blob"]).hexdigest(),
        pacote["blob"],
    )


def ler_compacto(con: sqlite3.Connection, chave: tuple) -> dict | None:
    r = con.execute(
        "SELECT formato,sha256_zip,bytes_zip,diretorio,sha256_prefixo,sha256_zip_1t,"
        "linhas_prefixo_omitidas,sha256_blob,blob FROM compacto "
        "WHERE uf=? AND mun=? AND zona=? AND secao=?",
        chave,
    ).fetchone()
    if r is None:
        return None
    pacote = dict(
        zip(
            (
                "formato",
                "sha256_zip",
                "bytes_zip",
                "diretorio",
                "sha256_prefixo",
                "sha256_zip_1t",
                "linhas_prefixo_omitidas",
                "sha256_blob",
                "blob",
            ),
            r,
            strict=True,
        )
    )
    if hashlib.sha256(pacote["blob"]).hexdigest() != pacote["sha256_blob"]:
        raise ValueError("Pacote compacto não confere com o hash gravado")
    pacote["diretorio"] = (
        json.loads(pacote["diretorio"]) if pacote["diretorio"] else None
    )
    return pacote


class Compactador:
    """Empacota no próprio worker (o xz libera o GIL), lendo o ZIP do 1º turno."""

    def __init__(self, referencia: Path | None):
        self.referencia = referencia
        self.local = threading.local()

    def zip_1t(self, r: dict) -> bytes | None:
        if self.referencia is None or not self.referencia.exists():
            return None
        if not hasattr(self.local, "con"):
            self.local.con = sqlite3.connect(
                f"file:{self.referencia}?mode=ro", uri=True, check_same_thread=False
            )
        row = self.local.con.execute(
            "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=? AND status='ok'",
            (r["uf"], r["mun"], r["zona"], r["secao"]),
        ).fetchone()
        return row[0] if row else None


def coletar(
    path: Path,
    limite: int,
    workers: int,
    rps: float,
    ufs: list[str],
    origem: Path = ORIGEM,
    base: str = BASE,
    guardar: str = "zip",
    referencia: Path | None = None,
) -> None:
    """``guardar='compacto'`` grava o log em ``compacto`` (ver compacto.py) e deixa
    ``arquivos.zip`` nulo; o SHA-256 do ZIP original continua em ``arquivos``."""
    if guardar not in ("zip", "compacto"):
        raise ValueError("guardar: zip ou compacto")
    con = abrir(path)
    catalogar(con, origem)
    con.execute("INSERT OR IGNORE INTO meta VALUES (?,?)", ("origem", str(origem)))
    con.execute("INSERT OR IGNORE INTO meta VALUES (?,?)", ("base", base))
    con.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", ("guardar", guardar))
    if referencia is not None:
        con.execute(
            "INSERT OR REPLACE INTO meta VALUES (?,?)",
            ("referencia_1t", str(referencia)),
        )
    con.commit()
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
    cliente = Cliente(rps, base)
    compactador = Compactador(referencia) if guardar == "compacto" else None

    def tarefa(r: dict) -> tuple:
        res = cliente.obter(r)
        if compactador is None or res[5] != "ok":
            return res, None
        from .compacto import empacotar

        pacote = empacotar(res[-1], compactador.zip_1t(r))
        return (*res[:-1], None), linha_compacta(res[:4], pacote)

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
                    pendentes.add(pool.submit(tarefa, dict(r)))
            if not pendentes:
                break
            prontos, pendentes = wait(pendentes, return_when=FIRST_COMPLETED)
            for p in prontos:
                r, compacta = p.result()
                if compacta is not None:
                    con.execute(
                        "INSERT OR REPLACE INTO compacto VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        compacta,
                    )
                con.execute(
                    "INSERT OR REPLACE INTO arquivos VALUES (?,?,?,?,?,?,?,?,?,?)", r
                )
                feitos += 1
                bons += r[5] == "ok"
                tamanho += len(r[-1] or (compacta[-1] if compacta else b""))
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
