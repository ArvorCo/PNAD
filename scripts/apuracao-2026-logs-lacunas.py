#!/usr/bin/env python3
"""Reconfere os metadados oficiais das seções sem nome de log no catálogo.

Preserva as respostas consultadas e nunca troca o hash do BU silenciosamente.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone

import requests
from apuracao_logs.coleta import BASE, DESTINO, HEADERS, ORIGEM, ROOT

PASTA = ROOT / "data/originals/tse_logs_2026/lacunas"
MANIFESTO = ROOT / "analysis/apuracao_2026/logs_urnas/lacunas.json"


def executar():
    if MANIFESTO.exists():
        print(
            "Reconsulta já preservada. Usando o manifesto existente, sem sobrescrever a evidência histórica."
        )
        return
    PASTA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"file:{DESTINO}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    fonte = sqlite3.connect(f"file:{ORIGEM}?mode=ro", uri=True)
    linhas = []
    with requests.Session() as sessao:
        sessao.headers.update(HEADERS)
        for r in con.execute("SELECT * FROM catalogo WHERE nome IS NULL"):
            uf, mun, z, s = (r[k] for k in ("uf", "mun", "zona", "secao"))
            nome = f"p003220-{uf}-m{mun}-z{z:04d}-s{s:04d}-aux.json"
            url = f"{BASE}/{uf}/{mun}/{z:04d}/{s:04d}/{nome}"
            bu = fonte.execute(
                "SELECT tipo_arquivo FROM bu WHERE uf=? AND mun=? AND zona=? AND secao=?",
                (uf, mun, z, s),
            ).fetchone()
            registro = {
                "uf": uf.upper(),
                "mun": mun,
                "zona": z,
                "secao": s,
                "status_anterior": r["status_aux"],
                "hash_anterior": r["hash"],
                "tipo_arquivo_bu": bu[0] if bu else None,
                "url": url,
                "consultado_em": datetime.now(timezone.utc).isoformat(),
            }
            resposta = sessao.get(url, timeout=(10, 40))
            registro["http"] = resposta.status_code
            if resposta.status_code == 200:
                obj = resposta.json()
                (PASTA / nome).write_bytes(resposta.content)
                registro.update(
                    {
                        "sha256": hashlib.sha256(resposta.content).hexdigest(),
                        "arquivo": str((PASTA / nome).relative_to(ROOT)),
                        "status_atual": obj.get("st"),
                        "hashes_atuais": len(obj.get("hashes", [])),
                    }
                )
                mesmo = [h for h in obj.get("hashes", []) if h["hash"] == r["hash"]]
                registro["hash_anterior_localizado"] = (
                    bool(mesmo) if r["hash"] else None
                )
                registro["logs_mesmo_hash"] = [
                    a["nm"]
                    for h in mesmo
                    for a in h.get("arq", [])
                    if a["nm"].lower().endswith("-log.jez")
                ]
            linhas.append(registro)
            time.sleep(0.25)
    con.close()
    fonte.close()
    obj = {
        "secoes": len(linhas),
        "status_anterior": dict(Counter(r["status_anterior"] for r in linhas)),
        "http_atual": dict(Counter(str(r["http"]) for r in linhas)),
        "logs_localizados_mesmo_hash": sum(
            bool(r.get("logs_mesmo_hash")) for r in linhas
        ),
        "linhas": linhas,
    }
    MANIFESTO.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps({k: v for k, v in obj.items() if k != "linhas"}, ensure_ascii=False)
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    grupo = p.add_mutually_exclusive_group()
    grupo.add_argument("--preparar-bus", action="store_true")
    grupo.add_argument(
        "--aplicar", action="store_true", help="somente com coletor parado"
    )
    a = p.parse_args()
    if a.preparar_bus or a.aplicar:
        from apuracao_logs.complementos import aplicar, preparar

        aplicar() if a.aplicar else preparar()
    else:
        executar()
