"""Horários exatos do 2º turno para filtros por seção no mapa, em Brasília."""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from apuracao_2t_2026.logs_cadencia import deslocamentos

ROOT = Path(__file__).resolve().parents[2]
ORIGEM = ROOT / "docs/assets/politize_se/dados/zona"
SAIDA = ROOT / "docs/assets/politize_se_mapa/horarios"
BU = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
LOG = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
CORTE = 62100
COLUNAS = [
    "secao",
    "enc",
    "ultimo",
    "motivo",
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "bn2",
    "bu2",
    "pequena",
    "agreg_igual",
    "escore",
    "log1_atencao",
    "log2_atencao",
    "modelo",
    "trocada",
    "mudou",
    "anomalo",
]


def grupo(segundo: int | None) -> str:
    return "sem" if segundo is None else "ate" if segundo <= CORTE else "apos"


def segundos_brt(hora: str | None, offset: int | None) -> int | None:
    if not hora or offset is None:
        return None
    try:
        d = datetime.fromisoformat(hora)
    except (TypeError, ValueError):
        return None
    if d.date().isoformat() != "2026-10-25":
        return None
    s = d.hour * 3600 + d.minute * 60 + d.second + int(offset) * 3600
    return s if 0 <= s < 86400 else None


def ultimo_util(r: dict) -> tuple[int | None, str]:
    if r.get("uf") == "ZZ":
        return None, "exterior"
    if r.get("status") != "ok":
        return None, "sem_log"
    if r.get("relogio_ok") != 1:
        return None, "relogio"
    if any(pd.isna(r.get(k)) for k in ("ultimo_s", "primeiro_s", "off")):
        return None, "sem_horario"
    if r.get("contagem_confere") != 1 or r.get("computados") != r.get("comparecimento"):
        return None, "contagem"
    if any(r.get(k) != 1 for k in ("urna_confere", "carga_confere", "id_confere")):
        return None, "identidade"
    s = int(r["ultimo_s"] + 3600 * r["off"])
    if not 0 <= s < 86400 or r["ultimo_s"] < r["primeiro_s"]:
        return None, "horario"
    return s, ""


def ler_horarios() -> dict[tuple, tuple]:
    keys = ["uf", "mun", "zona", "secao"]
    with sqlite3.connect(f"file:{LOG}?mode=ro", uri=True) as con:
        logs = pd.read_sql_query(
            """SELECT upper(uf) uf,mun,zona,secao,status,
          json_extract(resumo,'$.primeiro_computo_s') primeiro_s,
          json_extract(resumo,'$.ultimo_computo_s') ultimo_s,
          json_extract(resumo,'$.tempos_validos') relogio_ok,
          json_extract(resumo,'$.contagem_confere') contagem_confere,
          json_extract(resumo,'$.contagens.computados') computados,
          json_extract(resumo,'$.identidade_log.urna_bu_no_log') urna_confere,
          json_extract(resumo,'$.identidade_log.carga_bu_no_log') carga_confere
          FROM metricas""",
            con,
        )
    with sqlite3.connect(f"file:{BU}?mode=ro", uri=True) as con:
        bus = pd.read_sql_query(
            """SELECT upper(uf) uf,mun,zona,secao,abertura,encerramento,
          comparecimento,id_confere FROM bu WHERE pleito=3221""",
            con,
        )
    for frame in (logs, bus):
        frame["mun"] = frame["mun"].astype(str).str.zfill(5)
        assert not frame.duplicated(keys).any()
    off = deslocamentos(logs[logs["status"].eq("ok")])
    # Validação independente do fuso pelo horário modal de abertura do boletim.
    opening = bus[bus.uf.ne("ZZ")].copy()
    opening["h"] = pd.to_datetime(opening.abertura, errors="coerce").dt.hour
    opening = opening.dropna(subset=["h"])
    opening = (
        (8 - opening.groupby(["uf", "mun"]).h.agg(lambda s: s.mode().iloc[0]))
        .rename("off_bu")
        .reset_index()
    )
    check = off.merge(opening, on=["uf", "mun"], validate="one_to_one")
    assert check.off.eq(check.off_bu).all()
    assert off.off.isin([-1, 0, 1, 2]).all()
    x = bus.merge(logs, on=keys, how="left", validate="one_to_one").merge(
        off, on=["uf", "mun"], how="left"
    )
    out = {}
    for r in x.to_dict("records"):
        ultimo, motivo = ultimo_util(r)
        offset = None if pd.isna(r["off"]) or r["uf"] == "ZZ" else int(r["off"])
        enc = segundos_brt(r["encerramento"], offset) if r["id_confere"] == 1 else None
        out[tuple(r[k] for k in keys)] = (enc, ultimo, motivo)
    return out


def linha(s: dict, horario: tuple) -> list:
    enc, ultimo, motivo = horario
    v = dict(
        s,
        enc=enc,
        ultimo=ultimo,
        motivo=motivo,
        bn2=None
        if s.get("brancos2") is None or s.get("nulos2") is None
        else s["brancos2"] + s["nulos2"],
        modelo=s.get("modelo2") if s.get("bu2") else s.get("modelo1"),
        trocada=int(
            bool(s.get("bu2"))
            and s.get("urna_situacao") not in (None, "mesma", "mesma_recarga", "sem_1t")
        ),
        mudou=int(bool((s.get("mudanca") or {}).get("real"))),
        anomalo=s.get("ml_anomalo"),
    )
    # Mantém a proteção dos fragmentos de origem: não reintroduz voto oculto.
    if s.get("pequena"):
        for k in ("comp1", "flavio1", "lula1", "comp2", "flavio2", "lula2", "bn2"):
            v[k] = None
    return [v.get(k) for k in COLUNAS]


def publicar(saida: Path = SAIDA) -> dict:
    times = ler_horarios()
    saida.mkdir(parents=True, exist_ok=True)
    meta = {
        "formato": 1,
        "turno": 2,
        "corte_s": CORTE,
        "fuso": "Brasília",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "ufs": {},
        "nota": "Horários classificam seções; os placares somam todo o dia. Exterior sem classificação. Último voto exige relógio, identidade e contagem coerentes com o boletim.",
    }
    counts = {"enc": Counter(), "ultimo": Counter()}
    motivos = Counter()
    seen = set()
    for folder in sorted(ORIGEM.iterdir()):
        if not folder.is_dir():
            continue
        locais = defaultdict(list)
        for p in sorted(folder.glob("*.json.gz")):
            with gzip.open(p, "rt") as f:
                z = json.load(f)
            locs = [
                dict(zip(z["locais"]["colunas"], row, strict=True))
                for row in z["locais"]["linhas"]
            ]
            for row in z["secoes"]["linhas"]:
                s = dict(zip(z["secoes"]["colunas"], row, strict=True))
                key = (
                    folder.name,
                    str(s["mun_tse"]).zfill(5),
                    int(p.name.split(".")[0]),
                    s["secao"],
                )
                assert key not in seen
                seen.add(key)
                horario = times.get(key, (None, None, "sem_boletim"))
                loc = locs[s["li"]]["local_id"]
                locais[loc].append(linha(s, horario))
                for i, name in enumerate(("enc", "ultimo")):
                    counts[name][grupo(horario[i])] += 1
                if horario[2]:
                    motivos[horario[2]] += 1
        doc = {"formato": 1, "uf": folder.name, "colunas": COLUNAS, "locais": locais}
        raw = gzip.compress(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
        name = f"{folder.name}.json.gz"
        (saida / name).write_bytes(raw)
        meta["ufs"][folder.name] = {
            "arquivo": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "secoes": sum(map(len, locais.values())),
        }
    meta["contagens"] = counts
    meta["motivos_log"] = motivos
    meta["secoes_bu_fora_do_mapa"] = len(set(times) - seen)
    meta["fontes"] = [
        {
            "arquivo": str(p.relative_to(ROOT)),
            "bytes": p.stat().st_size,
            "mtime_ns": p.stat().st_mtime_ns,
        }
        for p in (BU, LOG)
    ]
    (saida / "indice.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    )
    return meta
