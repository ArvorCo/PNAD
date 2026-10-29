"""Histograma horário público do segundo turno, por seção, sem microdados."""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from apuracao_2t_2026.logs_cadencia import deslocamentos
from politize_se.saida import gravar

ROOT = Path(__file__).resolve().parents[2]
ORIGEM = ROOT / "docs/assets/politize_se/dados/zona"
SAIDA = ROOT / "docs/assets/politize_se/movimento"
DB = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
COLUNAS = ["secao", "horas", "motivo"]


def histograma(r: dict | None, off: int | None, pequena: bool, uf: str) -> tuple:
    """Ausência nunca é uma hora vazia. Sem voto divulgado para seção pequena."""
    if pequena:
        return None, "pequena"
    if uf == "ZZ":
        return None, "exterior"
    if not r or r.get("status") != "ok":
        return None, "sem_log"
    if r.get("relogio_ok") != 1 or r.get("cph_ok") != 1:
        return None, "relogio"
    if r.get("contagem_confere") != 1:
        return None, "contagem"
    if off is None:
        return None, "fuso"
    c = json.loads(r["cph"]) if isinstance(r["cph"], str) else r["cph"]
    if not c:
        return None, "sem_horario"
    horas = [0] * 24
    for h, v in c.items():
        b = int(h) + off
        if not 0 <= b < 24 or not isinstance(v, int) or v < 0:
            return None, "fora_dia"
        horas[b] += v
    assert sum(horas) == r["computados"]
    return horas, ""


def publicar(saida: Path = SAIDA) -> dict:
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as con:
        x = pd.read_sql_query(
            """SELECT upper(uf) uf,mun,zona,secao,status,
          json_extract(resumo,'$.primeiro_computo_s') primeiro_s,
          json_extract(resumo,'$.tempos_validos') relogio_ok,
          json_extract(resumo,'$.computados_por_hora_confiavel') cph_ok,
          json_extract(resumo,'$.contagem_confere') contagem_confere,
          json_extract(resumo,'$.contagens.computados') computados,
          json_extract(resumo,'$.computados_por_hora') cph FROM metricas""",
            con,
        )
    x["mun"] = x.mun.astype(str).str.zfill(5)
    off = {
        (r.uf, r.mun): int(r.off)
        for r in deslocamentos(x[x.status.eq("ok")]).itertuples()
    }
    assert set(off.values()) <= {-1, 0, 1, 2}
    records = {
        (r["uf"], r["mun"], r["zona"], r["secao"]): r for r in x.to_dict("records")
    }
    del x
    meta = {
        "formato": 1,
        "turno": 2,
        "data": "2026-10-25",
        "fuso": "Brasília",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "nota": "Votos computados por hora no dia da eleição; não mede fila, ocupação, previsão ou preferência por candidato. Seções pequenas e logs não utilizáveis ficam fora do histograma.",
        "ufs": {},
        "fonte": {
            "arquivo": str(DB.relative_to(ROOT)),
            "bytes": DB.stat().st_size,
            "mtime_ns": DB.stat().st_mtime_ns,
        },
    }
    nacional = [0] * 24
    total, cobertas = 0, 0
    exclusoes = Counter()
    for folder in sorted(ORIGEM.iterdir()):
        if not folder.is_dir():
            continue
        locais = {}
        hashes = hashlib.sha256()
        counts = Counter()
        votos = 0
        for path in sorted(folder.glob("*.json.gz")):
            raw = path.read_bytes()
            hashes.update(raw)
            d = json.loads(gzip.decompress(raw))
            ls = [
                dict(zip(d["locais"]["colunas"], row, strict=True))
                for row in d["locais"]["linhas"]
            ]
            for row in d["secoes"]["linhas"]:
                s = dict(zip(d["secoes"]["colunas"], row, strict=True))
                mun = str(s["mun_tse"]).zfill(5)
                key = (folder.name, mun, d["zona"], s["secao"])
                hs, motivo = histograma(
                    records.get(key), off.get(key[:2]), bool(s["pequena"]), folder.name
                )
                lid = ls[s["li"]]["local_id"]
                locais.setdefault(lid, []).append([s["secao"], hs, motivo])
                total += 1
                counts[motivo or "coberta"] += 1
                if hs is not None:
                    assert sum(hs) == s["comp2"], key
                    cobertas += 1
                    votos += sum(hs)
                    nacional = [a + b for a, b in zip(nacional, hs, strict=True)]
                else:
                    exclusoes[motivo] += 1
        name = folder.name + ".json.gz"
        size = gravar(
            saida / name,
            {"formato": 1, "uf": folder.name, "colunas": COLUNAS, "locais": locais},
        )
        meta["ufs"][folder.name] = {
            "arquivo": name,
            "bytes": size,
            "secoes": sum(counts.values()),
            "contagens": dict(counts),
            "votos": votos,
            "sha256": hashlib.sha256((saida / name).read_bytes()).hexdigest(),
            "sha256_fragmentos_origem": hashes.hexdigest(),
        }
        print(
            f"{folder.name}: {counts['coberta']} seções, {votos} cômputos", flush=True
        )
    meta.update(
        secoes=total,
        cobertas=cobertas,
        exclusoes=dict(exclusoes),
        horas=nacional,
        votos=sum(nacional),
    )
    gravar(saida / "indice.json", meta)
    return meta
