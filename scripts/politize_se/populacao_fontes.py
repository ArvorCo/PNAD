"""Fontes municipais oficiais; cache com URL, data e hash de cada resposta."""

from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/originals/populacao_eleitorado"
UFS = dict(
    zip(
        [
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "31",
            "32",
            "33",
            "35",
            "41",
            "42",
            "43",
            "50",
            "51",
            "52",
            "53",
        ],
        [
            "RO",
            "AC",
            "AM",
            "RR",
            "PA",
            "AP",
            "TO",
            "MA",
            "PI",
            "CE",
            "RN",
            "PB",
            "PE",
            "AL",
            "SE",
            "BA",
            "MG",
            "ES",
            "RJ",
            "SP",
            "PR",
            "SC",
            "RS",
            "MS",
            "MT",
            "GO",
            "DF",
        ],
        strict=True,
    )
)
API = "https://servicodados.ibge.gov.br/api/v3/agregados/"


def ler(p):
    return json.loads(p.read_text(encoding="utf-8"))


def hash_arquivo(p):
    with p.open("rb") as f:
        h = hashlib.sha256()
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
        return h.hexdigest()


def obter(nome, url):
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / nome
    receipt = p.with_suffix(".fonte.json")
    if p.exists() and receipt.exists():
        assert ler(receipt)["sha256"] == hash_arquivo(p)
        return ler(p)
    temp = p.with_suffix(".download")
    subprocess.run(
        [
            "curl",
            "-L",
            "--globoff",
            "--fail",
            "--retry",
            "2",
            "--max-time",
            "90",
            "-sS",
            url,
            "-o",
            str(temp),
        ],
        check=True,
    )
    d = ler(temp)
    if not isinstance(d, (list, dict)) or not d:
        raise ValueError(f"Resposta vazia: {url}")
    temp.replace(p)
    receipt.write_text(
        json.dumps(
            {
                "url": url,
                "obtido_em": datetime.now(timezone.utc).isoformat(),
                "sha256": hash_arquivo(p),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(nome, p.stat().st_size, flush=True)
    return d


def coletar():
    meta = obter("censo_metadados.json", API + "9514/metadados")
    periodos = obter("estimativas_periodos.json", API + "6579/periodos")
    ano = max(int(r["id"]) for r in periodos)
    obter(
        "estimativa.json",
        API + f"6579/periodos/{ano}/variaveis/9324?localidades=N6[all]",
    )
    idade = next(c for c in meta["classificacoes"] if c["id"] == 287)
    cats = [
        str(c["id"])
        for c in idade["categorias"]
        if c["nivel"] in (0, 1)
        or c["nome"] in ["15 anos", "16 anos", "17 anos", "18 anos", "19 anos"]
    ]

    def baixar(item):
        code, uf = item
        return obter(
            f"censo_{uf}.json",
            API
            + "9514/periodos/2022/variaveis/93?localidades=N6[N3["
            + code
            + "]]&classificacao=2[4,5]|287["
            + ",".join(cats)
            + "]|286[113635]",
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(baixar, UFS.items()))
