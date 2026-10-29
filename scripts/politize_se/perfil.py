"""Perfil TSE por seção: histogramas agregados de idade × sexo cadastrado."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pc

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/tse_eleitorado/perfil_eleitor_secao"
OUT = ROOT / "docs/assets/politize_se/perfil"
FAIXAS = [
    "16–17",
    "18–24",
    "25–34",
    "35–44",
    "45–54",
    "55–59",
    "60–64",
    "65–74",
    "75–84",
    "85+",
    "Não informada",
]
IDADE = {
    1600: 0,
    1700: 0,
    1800: 1,
    1900: 1,
    2000: 1,
    2124: 1,
    2529: 2,
    3034: 2,
    3539: 3,
    4044: 3,
    4549: 4,
    5054: 4,
    5559: 5,
    6064: 6,
    6569: 7,
    7074: 7,
    7579: 8,
    8084: 8,
    8589: 9,
    9094: 9,
    9599: 9,
    9999: 9,
}
KEYS = [
    "CD_MUNICIPIO",
    "NR_ZONA",
    "NR_SECAO",
    "NR_LOCAL_VOTACAO",
    "CD_GENERO",
    "CD_FAIXA_ETARIA",
]


def indice(idade: int, sexo: int) -> int:
    return IDADE.get(idade, 10) * 3 + {2: 0, 4: 1}.get(sexo, 2)


def estatisticas(v: list[int]) -> list[int]:
    return [sum(v), sum(v[1::3]), sum(v[:6]), sum(v[18:30]), sum(v[30:]), sum(v[2::3])]


def gravar(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode()
    p.write_bytes(gzip.compress(raw, mtime=0) if p.suffix == ".gz" else raw)


def processar(uf: str) -> dict:
    path = RAW / f"perfil_eleitor_secao_2026_{uf}.zip"
    secoes = {}
    total = 0
    with (
        zipfile.ZipFile(path) as z,
        z.open(next(n for n in z.namelist() if n.endswith(".csv"))) as f,
    ):
        reader = pc.open_csv(
            f,
            read_options=pc.ReadOptions(encoding="latin1", block_size=16 * 1024 * 1024),
            parse_options=pc.ParseOptions(delimiter=";"),
            convert_options=pc.ConvertOptions(include_columns=[*KEYS, "QT_ELEITORES"]),
        )
        for batch in reader:
            tab = (
                pa.Table.from_batches([batch])
                .group_by(KEYS)
                .aggregate([("QT_ELEITORES", "sum")])
            )
            for mun, zona, sec, local, sexo, idade, n in zip(
                *(tab[c].to_pylist() for c in tab.column_names), strict=True
            ):
                assert n >= 0
                key = f"{mun:05d}-{zona}-{sec}"
                if key not in secoes:
                    secoes[key] = [local, [0] * 33]
                assert secoes[key][0] == local, ("seção com dois locais", uf, key)
                secoes[key][1][indice(idade, sexo)] += n
                total += n
    locais = defaultdict(lambda: [0] * 33)
    for key, (local, v) in secoes.items():
        mun, zona, _ = key.split("-")
        lid = f"{uf}-{mun}-{zona}-{local}"
        locais[lid] = [a + b for a, b in zip(locais[lid], v, strict=True)]
    fonte = {
        "arquivo": path.name,
        "sha256": sha256(path),
        "url": "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitor_secao/"
        + path.name,
    }

    meta = {
        "uf": uf,
        "secoes": len(secoes),
        "locais": len(locais),
        "eleitores": total,
        "fonte": fonte,
    }
    gravar(
        OUT / f"{uf}.json.gz",
        {
            "formato": 1,
            "uf": uf,
            "faixas": FAIXAS,
            "sexos": ["Masculino", "Feminino", "Não informado"],
            "secoes": secoes,
            "meta": meta,
        },
    )
    gravar(
        OUT / f"resumos/{uf}.json.gz",
        {
            "formato": 1,
            "uf": uf,
            "colunas": [
                "total",
                "feminino",
                "jovens_16_24",
                "idosos_60_mais",
                "idade_nao_informada",
                "sexo_nao_informado",
            ],
            "locais": {k: estatisticas(v) for k, v in locais.items()},
            "meta": meta,
        },
    )
    print(uf, len(secoes), total, flush=True)
    return meta


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def publicar(ufs: list[str] | None = None) -> None:
    for uf in ufs or [p.stem[-2:] for p in sorted(RAW.glob("*.zip"))]:
        processar(uf)
    metas = [
        json.loads(gzip.decompress(p.read_bytes()))["meta"]
        for p in sorted((OUT / "resumos").glob("*.gz"))
    ]
    gravar(
        OUT / "indice.json",
        {
            "formato": 1,
            "eleicao": 2026,
            "faixas": FAIXAS,
            "sexos": ["Masculino", "Feminino", "Não informado"],
            "ufs": metas,
            "fonte": "https://dadosabertos.tse.jus.br/dataset/eleitorado-2026",
            "nota": "Cadastro eleitoral: inscritos, não perfil dos votantes. Sexo cadastral (CD_GENERO), distinto de identidade de gênero. Não informados preservados; nenhuma preferência eleitoral individual inferida.",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf", nargs="*")
    args = parser.parse_args()
    publicar(args.uf)
