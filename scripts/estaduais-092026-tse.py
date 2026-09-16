#!/usr/bin/env python3
"""Agrega o resultado de 2022 por municipio para o atlas estadual de setembro de 2026.

Le os arquivos oficiais do TSE em modo streaming e escreve tres derivados:

  data/outputs/estaduais2026/presidente_2022_municipios.csv
      Presidente, 1o e 2o turno, por municipio de todo o pais.
  data/outputs/estaduais2026/carregadores_2022.csv
      Voto nominal de governador e senador em 2022, por municipio, para os seis
      nomes mais votados de cada cargo nos estados da rota.
  data/outputs/estaduais2026/municipios.csv
      Uniao do voto presidencial com o eleitorado de 2026 e a chave de rota.

Reproducao:
    python3 scripts/estaduais-092026-tse.py
"""

from __future__ import annotations

import collections
import csv
import io
import sys
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
ELEITORADO = ROOT / "data/outputs/tse_eleitorado_municipios.csv"
OUT = ROOT / "data/outputs/estaduais2026"

# Estados da rota: Norte e Nordeste inteiros, onde esta a pergunta do atlas.
ROTA = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "MA",
    "PA",
    "PB",
    "PE",
    "PI",
    "RN",
    "RO",
    "RR",
    "SE",
    "TO",
]
NUMEROS = {"13": "lula", "22": "bolsonaro", "12": "ciro", "15": "tebet"}

# Municipios do MATOPIBA por UF, na delimitacao oficial da Embrapa/MDA.
# Guardamos so os de eleitorado relevante para a rota; a lista completa por
# codigo IBGE nao muda a leitura agregada e engordaria o arquivo sem ganho.
MATOPIBA_CERRADO_BA = {
    "LUÍS EDUARDO MAGALHÃES",
    "BARREIRAS",
    "SÃO DESIDÉRIO",
    "FORMOSA DO RIO PRETO",
    "CORREN TINA",
    "CORRENTINA",
    "RIACHÃO DAS NEVES",
    "COCOS",
    "JABORANDI",
    "BAIANÓPOLIS",
    "SANTA MARIA DA VITÓRIA",
    "SANTA RITA DE CÁSSIA",
    "BOM JESUS DA LAPA",
}
MATOPIBA_MA = {
    "BALSAS",
    "RIACHÃO",
    "TASSO FRAGOSO",
    "SÃO RAIMUNDO DAS MANGABEIRAS",
    "ALTO PARNAÍBA",
    "LORETO",
    "SAMBAÍBA",
    "CAROLINA",
    "FORTALEZA DOS NOGUEIRAS",
}
MATOPIBA_PI = {
    "URUÇUÍ",
    "BOM JESUS",
    "BAIXA GRANDE DO RIBEIRO",
    "SANTA FILOMENA",
    "RIBEIRO GONÇALVES",
    "CURRAIS",
    "GILBUÉS",
    "CORRENTE",
}
MATOPIBA_TO = {
    "PALMAS",
    "PORTO NACIONAL",
    "GURUPI",
    "PEDRO AFONSO",
    "CAMPOS LINDOS",
    "MATEIROS",
    "FORMOSO DO ARAGUAIA",
    "LAGOA DA CONFUSÃO",
    "PARAÍSO DO TOCANTINS",
}


def strip_accents(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    )


def rows(zf: zipfile.ZipFile, member: str):
    with zf.open(member) as handle:
        stream = io.TextIOWrapper(handle, encoding="latin-1", newline="")
        yield from csv.DictReader(stream, delimiter=";")


def presidente(zf: zipfile.ZipFile) -> dict:
    """Voto presidencial por municipio, somando as zonas eleitorais."""
    data: dict[tuple[str, str], dict] = {}
    for row in rows(zf, "votacao_candidato_munzona_2022_BR.csv"):
        if row["DS_CARGO"] != "Presidente":
            continue
        key = (row["SG_UF"], row["NM_MUNICIPIO"])
        entry = data.setdefault(
            key,
            {
                "uf": row["SG_UF"],
                "municipio": row["NM_MUNICIPIO"],
                "codigo_tse": row["CD_MUNICIPIO"],
                "lula_1t": 0,
                "bolsonaro_1t": 0,
                "ciro_1t": 0,
                "tebet_1t": 0,
                "validos_1t": 0,
                "lula_2t": 0,
                "bolsonaro_2t": 0,
            },
        )
        votes = int(row["QT_VOTOS_NOMINAIS"])
        turno = row["NR_TURNO"]
        name = NUMEROS.get(row["NR_CANDIDATO"])
        if turno == "1":
            entry["validos_1t"] += votes
            if name:
                entry[f"{name}_1t"] += votes
        elif turno == "2" and name in ("lula", "bolsonaro"):
            entry[f"{name}_2t"] += votes
    return data


def carregadores(zf: zipfile.ZipFile) -> list[dict]:
    """Voto nominal de governador e senador em 2022 nos estados da rota."""
    out = []
    for uf in ROTA:
        member = f"votacao_candidato_munzona_2022_{uf}.csv"
        if member not in zf.namelist():
            continue
        totals: dict[tuple[str, str, str], int] = collections.Counter()
        by_city: dict[tuple[str, str, str, str], int] = collections.Counter()
        for row in rows(zf, member):
            cargo = row["DS_CARGO"]
            if cargo not in ("Governador", "Senador") or row["NR_TURNO"] != "1":
                continue
            who = (cargo, row["NM_URNA_CANDIDATO"], row["SG_PARTIDO"])
            votes = int(row["QT_VOTOS_NOMINAIS"])
            totals[who] += votes
            by_city[(*who, row["NM_MUNICIPIO"])] += votes
        top = {}
        for cargo in ("Governador", "Senador"):
            ranked = sorted(
                ((k, v) for k, v in totals.items() if k[0] == cargo),
                key=lambda item: -item[1],
            )[:6]
            top[cargo] = {k for k, _ in ranked}
        for (cargo, nome, partido, municipio), votes in by_city.items():
            if (cargo, nome, partido) not in top[cargo]:
                continue
            out.append(
                {
                    "uf": uf,
                    "cargo": cargo,
                    "candidato": nome,
                    "partido": partido,
                    "municipio": municipio,
                    "votos": votes,
                    "votos_uf": totals[(cargo, nome, partido)],
                }
            )
        print(
            f"  {uf}: {len(top['Governador'])} gov, {len(top['Senador'])} sen",
            file=sys.stderr,
        )
    return out


def matopiba(uf: str, municipio: str) -> bool:
    table = {
        "BA": MATOPIBA_CERRADO_BA,
        "MA": MATOPIBA_MA,
        "PI": MATOPIBA_PI,
        "TO": MATOPIBA_TO,
    }.get(uf)
    return bool(table and municipio in table)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW) as zf:
        print("presidente...", file=sys.stderr)
        pres = presidente(zf)
        print(f"  {len(pres)} municipios", file=sys.stderr)
        print("carregadores...", file=sys.stderr)
        carr = carregadores(zf)

    eleitorado = {}
    with ELEITORADO.open() as handle:
        for row in csv.DictReader(handle):
            eleitorado[(row["uf"], row["municipio"])] = int(row["eleitores"])

    fields = [
        "uf",
        "municipio",
        "codigo_tse",
        "eleitores_2026",
        "lula_1t",
        "bolsonaro_1t",
        "ciro_1t",
        "tebet_1t",
        "validos_1t",
        "lula_2t",
        "bolsonaro_2t",
        "bolsonaro_2t_pct",
        "bolsonaro_1t_pct",
        "rota",
        "matopiba",
    ]
    with (OUT / "municipios.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for (uf, municipio), entry in sorted(pres.items()):
            total_2t = entry["lula_2t"] + entry["bolsonaro_2t"]
            entry["bolsonaro_2t_pct"] = (
                round(100 * entry["bolsonaro_2t"] / total_2t, 3) if total_2t else ""
            )
            entry["bolsonaro_1t_pct"] = (
                round(100 * entry["bolsonaro_1t"] / entry["validos_1t"], 3)
                if entry["validos_1t"]
                else ""
            )
            entry["eleitores_2026"] = eleitorado.get((uf, municipio), "")
            entry["rota"] = 1 if uf in ROTA else 0
            entry["matopiba"] = 1 if matopiba(uf, municipio) else 0
            writer.writerow({k: entry.get(k, "") for k in fields})

    with (OUT / "carregadores_2022.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "uf",
                "cargo",
                "candidato",
                "partido",
                "municipio",
                "votos",
                "votos_uf",
            ],
        )
        writer.writeheader()
        writer.writerows(
            sorted(carr, key=lambda r: (r["uf"], r["cargo"], -r["votos_uf"]))
        )

    sem_eleitorado = sum(1 for k in pres if k not in eleitorado)
    print(f"municipios.csv: {len(pres)} linhas, {sem_eleitorado} sem eleitorado 2026")
    print(f"carregadores_2022.csv: {len(carr)} linhas")


if __name__ == "__main__":
    main()
