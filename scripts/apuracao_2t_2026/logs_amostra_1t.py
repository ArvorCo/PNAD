"""Amostra do 1º turno relida com o leitor atual, só para a cadência horária.

As métricas do 1º turno (``data/outputs/logs_urnas_2026.sqlite``) foram geradas
antes de o leitor guardar ``computados_por_hora`` e ``partidas_dia``. Em vez de
reescrever esse banco (que é publicado e não deve mudar), relemos os originais
de uma amostra determinística de seções (uma em cada ``PASSO``, pelo SHA-256 da
chave) com ``processamento.processar`` e guardamos só a cadência e as partidas
num cache local (``data/outputs/logs_2t_capitulo/amostra_1t.jsonl``, ignorado
pelo Git). O banco do 1º turno e os originais ficam intocados (somente leitura).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from apuracao_logs.pleito import PLEITOS, ROOT
from apuracao_logs.processamento import carregar_bus, processar

CACHE = ROOT / "data/outputs/logs_2t_capitulo"
SAIDA = CACHE / "amostra_1t.jsonl"
PASSO = 5  # uma seção em cada cinco (20%)


def sorteada(uf: str, mun: str, zona: int, secao: int, passo: int = PASSO) -> bool:
    k = f"{uf.lower()}-{mun}-{int(zona)}-{int(secao)}".encode()
    return int(hashlib.sha256(k).hexdigest()[:8], 16) % passo == 0


def _compacta(linha: tuple) -> dict | None:
    uf, mun, zona, secao, _sha, _v, status, txt = linha
    if status != "ok":
        return None
    r = json.loads(txt)
    return {
        "uf": uf,
        "mun": mun,
        "zona": zona,
        "secao": secao,
        "cph": r.get("computados_por_hora"),
        "cph_ok": r.get("computados_por_hora_confiavel"),
        "primeiro_s": r.get("primeiro_computo_s"),
        "ultimo_s": r.get("ultimo_computo_s"),
        "computados": (r.get("contagens") or {}).get("computados"),
        "partidas": [p for p in r.get("partidas_dia") or [] if p["fase"] == "votacao"],
    }


def executar(workers: int = 8, passo: int = PASSO, saida: Path = SAIDA) -> int:
    pl = PLEITOS[3220]
    feitos = set()
    if saida.exists():
        for ln in saida.read_text(encoding="utf-8").splitlines():
            d = json.loads(ln)
            feitos.add((d["uf"], d["mun"], d["zona"], d["secao"]))
    bu = carregar_bus(pl)
    raw = sqlite3.connect(f"file:{pl.raw}?mode=ro", uri=True)
    ids = [
        r
        for r in raw.execute(
            "SELECT uf,mun,zona,secao,sha256 FROM arquivos WHERE status='ok'"
        )
        if sorteada(*r[:4], passo=passo)
        and tuple(r[:4]) in bu
        and tuple(r[:4]) not in feitos
    ]
    saida.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with ProcessPoolExecutor(max_workers=workers) as pool, saida.open("a") as out:
        for ini in range(0, len(ids), 400):
            tarefas = []
            for r in ids[ini : ini + 400]:
                key = tuple(r[:4])
                blob = raw.execute(
                    "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                    key,
                ).fetchone()[0]
                tarefas.append((key, blob, r[4], bu[key], pl.numero, pl.dia, None))
            for linha in pool.map(processar, tarefas, chunksize=8):
                d = _compacta(linha)
                if d is not None:
                    out.write(json.dumps(d, separators=(",", ":")) + "\n")
                    total += 1
            out.flush()
            print(json.dumps({"lidas": ini + len(tarefas), "de": len(ids)}), flush=True)
    raw.close()
    return total


if __name__ == "__main__":
    import sys

    sys.exit(0 if executar() >= 0 else 1)
