"""Lê ZIPs oficiais em streaming; preserva seção e não infere voto individual."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/outputs/predicao_2026"
URL_RESULTS = "https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip"
URL_PROFILE = "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2026.zip"
URL_LOCALS = "https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows(z, member):
    with z.open(member) as f:
        yield from csv.DictReader(
            io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"
        )


def key(row):
    return (
        row["SG_UF"],
        str(int(row["CD_MUNICIPIO"])),
        int(row["NR_ZONA"]),
        int(row["NR_SECAO"]),
    )


def age_lower(label):
    numbers = re.findall(r"\d+", label)
    return int(numbers[0]) if numbers else None


def build(kappa=100.0):
    if kappa < 0:
        raise ValueError("kappa precisa ser não negativo")
    OUT.mkdir(parents=True, exist_ok=True)
    result_zip = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
    profile_zip = ROOT / "data/raw/tse_eleitorado/perfil_eleitorado_2026.zip"
    locals_zip = ROOT / "data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip"
    old = {}
    excluded_uninstalled = 0
    with zipfile.ZipFile(result_zip) as z:
        # BR = presidente. BRASIL repete presidente e também contém outros cargos.
        member = "detalhe_votacao_secao_2022_BR.csv"
        for row in rows(z, member):
            if row["NR_TURNO"] != "1" or row["CD_CARGO"] != "1":
                continue
            ident = key(row)
            if ident in old:
                raise ValueError(f"Seção duplicada: {ident}")
            a, c, b = (
                int(row[k]) for k in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")
            )
            usable = True
            if a != c + b:
                if row["ST_SECAO_INSTALADA"] == "Não" and c == b == 0:
                    excluded_uninstalled += a
                    usable = False
                else:
                    raise ValueError(f"Comparecimento não fecha: {ident}")
            blank = int(row["QT_VOTOS_BRANCOS"]) + int(row["QT_VOTOS_NULOS"])
            if c != blank + int(row["QT_VOTOS_NOMINAIS"]) + int(
                row["QT_VOTOS_ANULADOS_APU_SEP"]
            ):
                raise ValueError(f"Votos não fecham: {ident}")
            old[ident] = (a, c, b, blank, row["NM_MUNICIPIO"], usable)
    totals = defaultdict(lambda: [0, 0, 0, 0])
    for ident, values in old.items():
        for i in range(4):
            totals[ident[0]][i] += values[i]
    history = json.loads((ROOT / "analysis/voto_util/tse_2022_uf.json").read_text())
    controls = {u["uf"]: u["t1"] for u in history["ufs"]}
    controls["ZZ"] = json.loads(
        (ROOT / "analysis/predicao_2026/tse_2022_exterior.json").read_text()
    )["t1"]
    checks = []
    for uf, counts in sorted(totals.items()):
        d = controls[uf]
        reference = [
            d["aptos"],
            d["comparecimento"],
            d["abstencao"],
            d["brancos"] + d["nulos"],
        ]
        delta = [x - y for x, y in zip(counts, reference, strict=True)]
        if any(delta):
            raise ValueError(f"Seções e API divergem em {uf}: {delta}")
        checks.append({"uf": uf, "diferencas": delta})
    print(f"2022: {len(old):,} seções; somas oficiais conferidas", flush=True)

    current = {}
    locals_metadata = {}
    with zipfile.ZipFile(locals_zip) as z:
        members = [n for n in z.namelist() if n.endswith(".csv")]
        national = [n for n in members if n.endswith("_BRASIL.csv")]
        for member in national or members:
            for row in rows(z, member):
                if row["NR_TURNO"] != "1":
                    continue
                ident = key(row)
                if ident in current:
                    raise ValueError(f"Seção 2026 duplicada: {ident}")
                # Eleição federal, inclusive trânsito e exterior. Não usar
                # eleição estadual para inferir aptos a presidente.
                current[ident] = int(row["QT_ELEITOR_ELEICAO_FEDERAL"])
                if not locals_metadata:
                    locals_metadata = {
                        k: row[k] for k in ("DT_GERACAO", "HH_GERACAO", "AA_ELEICAO")
                    }
    demographics = defaultdict(lambda: [0, 0, 0, 0, 0])
    metadata = {}
    age_counts = defaultdict(lambda: defaultdict(int))
    with zipfile.ZipFile(profile_zip) as z:
        names = z.namelist()
        # O pacote nacional e os arquivos de UF podem coexistir. Nunca somá-los.
        national = [n for n in names if n.endswith("_BRASIL.csv")]
        members = national or [
            n for n in names if n.endswith(".csv") and not n.endswith("_BR.csv")
        ]
        if not members:
            raise ValueError("Perfil 2026 sem CSV identificado")
        for member in members:
            for row in rows(z, member):
                count = int(row["QT_ELEITORES"])
                lower = age_lower(row["DS_FAIXA_ETARIA"])
                v = demographics[row["SG_UF"]]
                v[0] += count
                v[1] += (
                    count if row["DS_GENERO"].upper() in ("FEMININO", "MULHER") else 0
                )
                v[2] += count if lower is not None and lower >= 70 else 0
                v[3] += count if lower is not None and 16 <= lower <= 17 else 0
                v[4] += count if lower is not None and lower < 16 else 0
                age_counts[row["SG_UF"]][row["DS_FAIXA_ETARIA"]] += count
                if not metadata:
                    metadata = {
                        k: row[k] for k in ("DT_GERACAO", "HH_GERACAO", "AA_ELEICAO")
                    }
            print(f"Perfil: {member}", flush=True)

    uf_data = defaultdict(
        lambda: {
            "eleitorado": 0,
            "mulheres": 0,
            "idade70": 0,
            "idade16_17": 0,
            "menores16": 0,
            "secoes": 0,
            "pareados": 0,
            "pareados_eleitores": 0,
            "comparecimento_estimado": 0.0,
            "branco_nulo_historico": 0.0,
            "bins": defaultdict(lambda: [0, 0, 0.0, 0.0]),
            "top": [],
        }
    )
    db = OUT / "secoes.sqlite"
    with sqlite3.connect(db) as con:
        con.execute("DROP TABLE IF EXISTS secoes")
        con.execute(
            "CREATE TABLE secoes (uf TEXT, municipio TEXT, zona INTEGER, secao INTEGER, "
            "eleitores_2026 INTEGER, aptos_2022 INTEGER, comparecimento_2022 INTEGER, "
            "comparecimento_modelo REAL, mulheres INTEGER, idade70 INTEGER, "
            "idade16_17 INTEGER, pareado INTEGER, PRIMARY KEY(uf,municipio,zona,secao))"
        )
        records = []
        for ident, e in current.items():
            uf = ident[0]
            female = elderly = young = 0  # Não imputar demografia de UF em seção.
            if e == 0:
                continue
            a, c, _, blank = totals[uf]
            mu = c / a
            oldrow = old.get(ident)
            matched = bool(oldrow and oldrow[0] > 0 and oldrow[5])
            oa, oc = oldrow[:2] if matched else (0, 0)
            rate = (oc + kappa * mu) / (oa + kappa) if matched else mu
            # Branco/nulo fica separado do comparecimento e não usa preferência partidária.
            invalid = (
                (oldrow[3] + kappa * blank / c) / (oc + kappa) if matched else blank / c
            )
            u = uf_data[uf]
            u["eleitorado"] += e
            u["secoes"] += 1
            u["pareados"] += int(matched)
            u["pareados_eleitores"] += e if matched else 0
            u["comparecimento_estimado"] += e * rate
            u["branco_nulo_historico"] += e * rate * invalid
            if matched:
                abst = 1 - oc / oa
                band = min(4, int(abst / 0.1))
                bucket = u["bins"][band]
                bucket[0] += 1
                bucket[1] += e
                bucket[2] += e * rate
                bucket[3] += e * abst
                if oa >= 100 and e >= 100:
                    u["top"].append(
                        {
                            "uf": uf,
                            "municipio": oldrow[4],
                            "codigo_tse": ident[1],
                            "zona": ident[2],
                            "secao": ident[3],
                            "aptos_2022": oa,
                            "eleitores_2026": e,
                            "abstencao_2022_pct": 100 * abst,
                        }
                    )
                    if len(u["top"]) > 100:
                        u["top"] = sorted(
                            u["top"],
                            key=lambda r: r["abstencao_2022_pct"],
                            reverse=True,
                        )[:50]
            records.append(
                (*ident, e, oa, oc, rate, female, elderly, young, int(matched))
            )
            if len(records) >= 10000:
                con.executemany(
                    "INSERT INTO secoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", records
                )
                records.clear()
        con.executemany("INSERT INTO secoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", records)

    for uf, u in uf_data.items():
        for field, val in zip(
            ("eleitorado_perfil", "mulheres", "idade70", "idade16_17", "menores16"),
            demographics[uf],
            strict=True,
        ):
            u[field] = val
        u["comparecimento_rate"] = u["comparecimento_estimado"] / u["eleitorado"]
        u["branco_nulo_rate"] = (
            u["branco_nulo_historico"] / u["comparecimento_estimado"]
        )
        u["historico_2022"] = dict(
            zip(
                ("aptos", "comparecimento", "abstencao", "branco_nulo"),
                totals[uf],
                strict=True,
            )
        )
        u["bins"] = [
            {
                "faixa": ["0 a 10%", "10 a 20%", "20 a 30%", "30 a 40%", "40% ou mais"][
                    b
                ],
                "secoes": v[0],
                "eleitores_2026": v[1],
                "comparecimento_rate": v[2] / v[1],
                "abstencao_historica_pct": 100 * v[3] / v[1],
            }
            for b, v in sorted(u["bins"].items())
        ]
        u["top"] = sorted(
            u["top"], key=lambda r: r["abstencao_2022_pct"], reverse=True
        )[:10]
        u["idades"] = dict(age_counts[uf])
    payload = {
        "schema": 1,
        "kappa": kappa,
        "perfil_metadata": metadata,
        "locais_metadata": locals_metadata,
        "aptos_nao_instaladas_excluidos_2022": excluded_uninstalled,
        "fontes": [
            {
                "url": URL_RESULTS,
                "arquivo": str(result_zip.relative_to(ROOT)),
                "sha256": sha(result_zip),
            },
            {
                "url": URL_PROFILE,
                "arquivo": str(profile_zip.relative_to(ROOT)),
                "sha256": sha(profile_zip),
            },
            {
                "url": URL_LOCALS,
                "arquivo": str(locals_zip.relative_to(ROOT)),
                "sha256": sha(locals_zip),
            },
        ],
        "secoes_historicas_2022": len(old),
        "validacao_2022": checks,
        "ufs": dict(sorted(uf_data.items())),
    }
    path = OUT / "tse.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    print(
        f"2026: {sum(u['eleitorado'] for u in uf_data.values()):,} eleitores; {len(current):,} seções",
        flush=True,
    )
    return payload
