#!/usr/bin/env python3
"""Build compact TSE electorate benchmarks from the monthly current-profile ZIP.

The official CSV is larger than 2 GB. This command reads it directly from the
ZIP, aggregates one row at a time and atomically replaces the compact SQLite,
CSV and JSON outputs used by polling audits.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/raw/tse_eleitorado/perfil_eleitorado_ATUAL.zip"
DEFAULT_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"
DEFAULT_CSV = ROOT / "data/outputs/tse_eleitorado_perfil_summary.csv"
DEFAULT_JSON = ROOT / "data/outputs/tse_eleitorado_perfil_benchmark.json"
SOURCE_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/"
    "perfil_eleitorado_ATUAL.zip"
)
PORTAL_URL = "https://dadosabertos.tse.jus.br/dataset/eleitorado-atual"

REGIONS = {
    "Norte": {"AC", "AP", "AM", "PA", "RO", "RR", "TO"},
    "Nordeste": {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"},
    "Centro-Oeste": {"DF", "GO", "MT", "MS"},
    "Sudeste": {"ES", "MG", "RJ", "SP"},
    "Sul": {"PR", "RS", "SC"},
}
UF_TO_REGION = {uf: region for region, ufs in REGIONS.items() for uf in ufs}

# Historical AtlasIntel targets are retained because the compact database is
# also the evidence source for that dossier. They are not Nexus targets.
ATLAS_TARGETS = {
    "genero_atlas_binario": {"Mulher": 53.2, "Homem": 46.8},
    "idade_atlas": {
        "16-24": 10.9,
        "25-34": 19.4,
        "35-44": 20.4,
        "45-59": 25.9,
        "60-100": 23.3,
    },
    "regiao": {
        "Sudeste": 41.8,
        "Nordeste": 29.0,
        "Sul": 13.8,
        "Norte": 8.1,
        "Centro-Oeste": 7.3,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atlas_age(label: str) -> str | None:
    if label in {"16 anos", "17 anos", "18 anos", "19 anos", "20 anos", "21 a 24 anos"}:
        return "16-24"
    if label in {"25 a 29 anos", "30 a 34 anos"}:
        return "25-34"
    if label in {"35 a 39 anos", "40 a 44 anos"}:
        return "35-44"
    if label in {"45 a 49 anos", "50 a 54 anos", "55 a 59 anos"}:
        return "45-59"
    if label in {
        "60 a 64 anos",
        "65 a 69 anos",
        "70 a 74 anos",
        "75 a 79 anos",
        "80 a 84 anos",
        "85 a 89 anos",
        "90 a 94 anos",
        "95 a 99 anos",
        "100 anos ou mais",
    }:
        return "60-100"
    return None


def aggregate(path: Path) -> tuple[dict[str, str], dict[str, Counter[str]]]:
    counters = {
        "genero_raw_all": Counter(),
        "idade_raw_all": Counter(),
        "genero_atlas_all": Counter(),
        "idade_atlas_all": Counter(),
        "genero_raw": Counter(),
        "idade_raw": Counter(),
        "escolaridade_tse": Counter(),
        "cor_raca": Counter(),
        "uf": Counter(),
        "regiao": Counter(),
        "genero_atlas": Counter(),
        "idade_atlas": Counter(),
    }
    rows = total_all = total_resident = 0
    first: dict[str, str] | None = None

    with zipfile.ZipFile(path) as archive:
        csv_names = [
            name for name in archive.namelist() if name.lower().endswith(".csv")
        ]
        if len(csv_names) != 1:
            raise ValueError(f"expected one CSV in {path}, found {len(csv_names)}")
        with archive.open(csv_names[0]) as binary:
            text = io.TextIOWrapper(binary, encoding="latin-1", newline="")
            for row in csv.DictReader(text, delimiter=";"):
                rows += 1
                if first is None:
                    first = row
                count = int(row["QT_ELEITORES"])
                total_all += count
                uf = row["SG_UF"].strip()
                gender = row["DS_GENERO"].strip()
                age = row["DS_FAIXA_ETARIA"].strip()
                counters["genero_raw_all"][gender] += count
                counters["idade_raw_all"][age] += count
                if gender == "FEMININO":
                    counters["genero_atlas_all"]["Mulher"] += count
                elif gender == "MASCULINO":
                    counters["genero_atlas_all"]["Homem"] += count
                age_band = atlas_age(age)
                if age_band:
                    counters["idade_atlas_all"][age_band] += count
                if uf == "ZZ":
                    continue

                total_resident += count
                counters["genero_raw"][gender] += count
                counters["idade_raw"][age] += count
                counters["escolaridade_tse"][row["DS_GRAU_INSTRUCAO"].strip()] += count
                counters["cor_raca"][row["DS_COR_RACA"].strip()] += count
                counters["uf"][uf] += count
                counters["regiao"][UF_TO_REGION[uf]] += count

                if gender == "FEMININO":
                    counters["genero_atlas"]["Mulher"] += count
                elif gender == "MASCULINO":
                    counters["genero_atlas"]["Homem"] += count

                if age_band:
                    counters["idade_atlas"][age_band] += count

    if first is None:
        raise ValueError(f"empty CSV in {path}")

    counters["genero_atlas_binario"] = counters["genero_atlas"].copy()
    counters["genero_atlas_binario_all"] = counters["genero_atlas_all"].copy()
    metadata = {
        "source_name": "TSE Eleitorado Atual - Perfil do eleitorado por seção eleitoral",
        "source_url": SOURCE_URL,
        "portal_url": PORTAL_URL,
        "dt_geracao": first["DT_GERACAO"],
        "hh_geracao": first["HH_GERACAO"],
        "ano_eleicao": first["ANO_ELEICAO"],
        "rows_processed": str(rows),
        "total_eleitores_all_ufs_incl_exterior": str(total_all),
        "total_eleitores_brasil_sem_exterior": str(total_resident),
        "zip_sha256": sha256(path),
        "notes": (
            "Comparações nacionais excluem SG_UF=ZZ (exterior). Sexo binário usa "
            "denominador Homem/Mulher. Idade usa eleitorado 16+ e exclui 15 anos/"
            "faixa inválida. Totais brutos preservam Não informado."
        ),
    }
    return metadata, counters


def rows_for_summary(counters: dict[str, Counter[str]]) -> list[tuple]:
    rows: list[tuple] = []
    for dimension, values in counters.items():
        denominator = sum(values.values())
        if dimension == "genero_atlas_binario_all":
            universe = (
                "Todos os países/UF, inclusive exterior; exclui gênero não informado"
            )
        elif dimension == "idade_atlas_all":
            universe = "Todos os países/UF, inclusive exterior; eleitorado 16+"
        elif dimension.endswith("_all"):
            universe = "Todos os países/UF, inclusive exterior"
        elif dimension == "genero_atlas_binario":
            universe = "Brasil sem exterior; exclui gênero não informado no denominador"
        elif dimension == "idade_atlas":
            universe = "Brasil sem exterior; eleitorado 16+ em faixas comparáveis"
        else:
            universe = "Brasil sem exterior"
        for category, count in values.most_common():
            rows.append(
                (dimension, category, count, 100 * count / denominator, universe)
            )
    return rows


def write_database(
    path: Path, metadata: dict[str, str], summary_rows: list[tuple]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(handle)
    try:
        with sqlite3.connect(temporary) as connection:
            connection.executescript("""
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE summary (
                    dimension TEXT NOT NULL,
                    category TEXT NOT NULL,
                    qt_eleitores INTEGER NOT NULL,
                    pct_total REAL,
                    universe TEXT NOT NULL
                );
                CREATE INDEX idx_summary_dim_cat ON summary(dimension, category);
                CREATE TABLE atlas_comparison (
                    dimension TEXT NOT NULL,
                    category TEXT NOT NULL,
                    atlas_pct REAL NOT NULL,
                    tse_pct REAL,
                    delta_pct REAL,
                    note TEXT NOT NULL
                );
                """)
            connection.executemany(
                "INSERT INTO metadata VALUES (?, ?)", metadata.items()
            )
            connection.executemany(
                "INSERT INTO summary VALUES (?, ?, ?, ?, ?)", summary_rows
            )
            official = {(d, c): pct for d, c, _, pct, _ in summary_rows}
            comparisons = []
            for dimension, targets in ATLAS_TARGETS.items():
                for category, target in targets.items():
                    tse = official[(dimension, category)]
                    comparisons.append(
                        (
                            dimension,
                            category,
                            target,
                            tse,
                            target - tse,
                            f"Atlas perfil amostral vs TSE Eleitorado Atual {metadata['dt_geracao']}",
                        )
                    )
            connection.executemany(
                "INSERT INTO atlas_comparison VALUES (?, ?, ?, ?, ?, ?)", comparisons
            )
        os.replace(temporary, path)
        os.chmod(path, 0o644)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path: Path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["dimension", "category", "qt_eleitores", "pct_total", "universe"]
        )
        writer.writerows(rows)


def summary_lookup(rows: list[tuple], dimension: str) -> dict[str, dict]:
    return {
        category: {"count": count, "pct": pct}
        for dim, category, count, pct, _ in rows
        if dim == dimension
    }


def write_json(path: Path, metadata: dict[str, str], rows: list[tuple]) -> None:
    payload = {
        "metadata": metadata,
        "dashboard_filter_all_countries": {
            "gender_raw": summary_lookup(rows, "genero_raw_all"),
            "gender_binary": summary_lookup(rows, "genero_atlas_binario_all"),
            "age_raw": summary_lookup(rows, "idade_raw_all"),
            "age_poll_bands": summary_lookup(rows, "idade_atlas_all"),
        },
        "poll_universe_brazil_excluding_exterior": {
            "gender_raw": summary_lookup(rows, "genero_raw"),
            "gender_binary": summary_lookup(rows, "genero_atlas_binario"),
            "age_raw": summary_lookup(rows, "idade_raw"),
            "age_poll_bands": summary_lookup(rows, "idade_atlas"),
        },
        "gender_raw": summary_lookup(rows, "genero_raw"),
        "gender_binary": summary_lookup(rows, "genero_atlas_binario"),
        "age_raw": summary_lookup(rows, "idade_raw"),
        "age_poll_bands": summary_lookup(rows, "idade_atlas"),
        "region": summary_lookup(rows, "regiao"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args()

    metadata, counters = aggregate(args.input)
    rows = rows_for_summary(counters)
    write_database(args.db, metadata, rows)
    write_csv(args.csv, rows)
    write_json(args.json, metadata, rows)
    print(
        json.dumps(
            {
                "generated": f"{metadata['dt_geracao']} {metadata['hh_geracao']}",
                "resident_electors": int(
                    metadata["total_eleitores_brasil_sem_exterior"]
                ),
                "rows_processed": int(metadata["rows_processed"]),
                "db": str(args.db),
                "csv": str(args.csv),
                "json": str(args.json),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
