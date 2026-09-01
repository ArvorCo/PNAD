#!/usr/bin/env python3
"""Constrói a base auditável do dossiê Minas Gerais, agosto de 2026.

O script combina apenas fontes públicas ou relatórios preservados no projeto:

* TSE: votação nominal municipal de 2018 e 2022 e eleitorado de julho de 2026;
* IBGE: Censo 2022, PIB municipal 2023, divisões regionais e malha municipal;
* PNAD Contínua: anual 2025 (renda domiciliar) e 2026 T1 (trabalho/escola);
* Quaest e Real Time Big Data: tabelas transcritas com página de origem.

Os fluxos eleitorais não são trajetórias de pessoas. Este script entrega as
margens observadas; a camada de visualização estima matrizes por IPF/RAS e as
rotula como inferência agregada.

Uso: python3 scripts/mg-082026-data.py
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import math
import os
import re
import sqlite3
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/pesquisas/estaduais/mg/2026-08"
RAW = BASE / "dados-brutos"
DERIVED = BASE / "derivados"
PUBLIC = ROOT / "docs/assets"
TSE_RESULTS = ROOT / "data/raw/tse_resultados"
TSE_PROFILE = ROOT / "data/raw/tse_eleitorado/perfil_eleitorado_ATUAL.zip"
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
PIB_ZIP = ROOT / "data/originals/ibge_pib_municipios/base_de_dados_2010_2023_xlsx.zip"

IBGE_URLS = {
    "localidades": "https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios",
    "renda": (
        "https://apisidra.ibge.gov.br/values/t/10295/n6/in%20n3%2031/"
        "v/13431,13534,13604/p/2022?formato=json"
    ),
    "populacao": (
        "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%2031/"
        "v/93/p/2022?formato=json"
    ),
    "malha": (
        "https://servicodados.ibge.gov.br/api/v3/malhas/estados/31?"
        "formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
    ),
}

REPLICATES = 200
CI_LEVEL = 0.95
Z95 = NormalDist().inv_cdf(0.5 + CI_LEVEL / 2)


def normalize(value: str) -> str:
    """Normaliza nomes para junções entre TSE e IBGE sem apagar o original."""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()
    aliases = {
        "BARAO DE MONTE ALTO": "BARAO DO MONTE ALTO",
        "DONA EUSEBIA": "DONA EUZEBIA",
        "SAO THOME DAS LETRAS": "SAO TOME DAS LETRAS",
    }
    return aliases.get(text, text)


def decode_http(payload: bytes) -> bytes:
    return gzip.decompress(payload) if payload[:2] == b"\x1f\x8b" else payload


def cached_json(name: str, url: str):
    path = RAW / "ibge" / f"{name}.json"
    if not path.exists():
        request = Request(url, headers={"User-Agent": "Arvor-PNAD/1.0"})
        payload = decode_http(urlopen(request, timeout=180).read())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return json.loads(path.read_text(encoding="utf-8"))


# Materiais recebidos de terceiros nao ficam no repositorio. Ficam num cofre
# fora do git, e o manifesto publica apenas nome, tamanho e SHA-256, o que
# preserva a auditabilidade sem redistribuir o arquivo.
FONTES_RECEBIDAS = Path(
    os.environ.get(
        "MG_FONTES_RECEBIDAS",
        Path.home() / "arvor/campanhas/flaviobolsonaro/data/raw/mg_2026",
    )
).expanduser()


def source_manifest() -> dict:
    import hashlib

    files = [
        (BASE / "fontes/quaest-mg-2026-08-25.pdf", False),
        (BASE / "fontes/real-time-big-data-mg-2026-08-25.pdf", False),
        (FONTES_RECEBIDAS / "mg-municipios-2018x2022.pdf", True),
        (FONTES_RECEBIDAS / "mg-amarelos-votos-2018x2022.pdf", True),
        (FONTES_RECEBIDAS / "mapa-tese-recebido-2018x2022.png", True),
        (TSE_RESULTS / "votacao_candidato_munzona_2018.zip", False),
        (TSE_RESULTS / "votacao_candidato_munzona_2022.zip", False),
        (TSE_PROFILE, False),
        (PIB_ZIP, False),
    ]
    records = []
    for path, externo in files:
        if externo and not path.exists():
            print(f"aviso: material recebido ausente do cofre, {path}")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        record = {
            "path": (
                f"cofre-externo/{path.name}" if externo else str(path.relative_to(ROOT))
            ),
            "bytes": path.stat().st_size,
            "sha256": digest.hexdigest(),
        }
        if externo:
            record["nota"] = (
                "Material recebido de terceiro. Fica fora do repositório; "
                "publicamos o hash para conferência, não o arquivo."
            )
        records.append(record)
    return {
        "generated": "2026-08-31",
        "files": records,
        "urls": IBGE_URLS
        | {
            "tse_resultados_2018": "https://dadosabertos.tse.jus.br/dataset/resultados-2018",
            "tse_resultados_2022": "https://dadosabertos.tse.jus.br/dataset/resultados-2022",
            "tse_eleitorado": "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_ATUAL.zip",
            "ibge_pib": "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produtointerno-bruto-dos-municipios.html",
        },
    }


def read_ibge() -> tuple[dict, dict]:
    localities = cached_json("localidades", IBGE_URLS["localidades"])
    income = cached_json("censo-2022-renda", IBGE_URLS["renda"])[1:]
    population = cached_json("censo-2022-populacao", IBGE_URLS["populacao"])[1:]
    geometry = cached_json("malha-municipal-minima", IBGE_URLS["malha"])

    municipalities: dict[str, dict] = {}
    for item in localities:
        immediate = item["regiao-imediata"]
        intermediate = immediate["regiao-intermediaria"]
        micro = item.get("microrregiao") or {}
        meso = micro.get("mesorregiao") or {}
        code = str(item["id"])
        municipalities[code] = {
            "codigo_ibge": code,
            "municipio": item["nome"],
            "municipio_norm": normalize(item["nome"]),
            "regiao_imediata": immediate["nome"],
            "regiao_intermediaria": intermediate["nome"],
            "microrregiao": micro.get("nome"),
            "mesorregiao": meso.get("nome"),
        }
    income_fields = {
        "13431": "renda_pc_media_2022",
        "13534": "renda_pc_mediana_2022",
        "13604": "moradores_cobertos_renda_2022",
    }
    for item in income:
        code, field = item["D1C"], income_fields[item["D2C"]]
        municipalities[code][field] = float(item["V"])
    for item in population:
        municipalities[item["D1C"]]["populacao_2022"] = int(item["V"])

    with zipfile.ZipFile(PIB_ZIP) as archive:
        payload = archive.read(archive.namelist()[0])
    frame = pd.read_excel(io.BytesIO(payload), sheet_name="PIB dos Municípios")
    mg = frame[
        (frame["Sigla da Unidade da Federação"] == "MG")
        & (frame["Ano"].isin([2021, 2023]))
    ]
    pib_col = next(
        col
        for col in frame
        if col.startswith("Produto Interno Bruto,") and "per capita" not in col
    )
    pc_col = next(
        col for col in frame if col.startswith("Produto Interno Bruto per capita")
    )
    sector_cols = {
        "agro": next(
            col
            for col in frame
            if col.startswith("Valor adicionado bruto da Agropecuária")
        ),
        "industria": next(
            col
            for col in frame
            if col.startswith("Valor adicionado bruto da Indústria")
        ),
        "servicos": next(
            col
            for col in frame
            if col.startswith("Valor adicionado bruto dos Serviços")
        ),
        "administracao": next(
            col
            for col in frame
            if col.startswith("Valor adicionado bruto da Administração")
        ),
    }
    for row in mg.to_dict("records"):
        code = str(int(row["Código do Município"]))
        if int(row["Ano"]) == 2023:
            municipalities[code]["pib_2023_mil_reais"] = round(float(row[pib_col]), 3)
            municipalities[code]["pib_pc_2023"] = round(float(row[pc_col]), 2)
        else:
            total = sum(float(row[col]) for col in sector_cols.values())
            for key, col in sector_cols.items():
                municipalities[code][f"vab_{key}_2021_mil_reais"] = round(
                    float(row[col]), 3
                )
                municipalities[code][f"participacao_{key}_2021_pct"] = round(
                    100 * float(row[col]) / total, 3
                )
            municipalities[code]["atividade_principal_2021"] = row[
                "Atividade com maior valor adicionado bruto"
            ]

    geometry_by_code = {
        feature["properties"]["codarea"]: feature for feature in geometry["features"]
    }
    return municipalities, geometry_by_code


def age_band(label: str) -> str | None:
    value = normalize(label)
    numbers = [int(x) for x in re.findall(r"\d+", value)]
    if not numbers:
        return None
    low = numbers[0]
    if low < 16:
        return None
    if low <= 34:
        return "16-34"
    if low <= 59:
        return "35-59"
    return "60+"


def education_band(code: str) -> str | None:
    value = int(code) if str(code).isdigit() else -1
    if 1 <= value <= 4:
        return "Fundamental"
    if 5 <= value <= 6:
        return "Médio"
    if 7 <= value <= 8:
        return "Superior"
    return None


def read_tse_electorate() -> tuple[dict, dict]:
    by_city = defaultdict(
        lambda: {"total": 0, "gender": Counter(), "age": Counter(), "school": Counter()}
    )
    state = {
        "total": 0,
        "gender": Counter(),
        "age": Counter(),
        "school": Counter(),
        "mandatory": Counter(),
    }
    with zipfile.ZipFile(TSE_PROFILE) as archive:
        member = next(
            name for name in archive.namelist() if name.lower().endswith(".csv")
        )
        with archive.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
            for row in csv.DictReader(text, delimiter=";"):
                if row["SG_UF"] != "MG":
                    continue
                count = int(row["QT_ELEITORES"])
                city = normalize(row["NM_MUNICIPIO"])
                gender = row["DS_GENERO"].title()
                age = age_band(row["DS_FAIXA_ETARIA"])
                school = education_band(row["CD_GRAU_INSTRUCAO"])
                by_city[city]["total"] += count
                by_city[city]["gender"][gender] += count
                state["total"] += count
                state["gender"][gender] += count
                state["mandatory"][row["TP_OBRIGATORIEDADE_VOTO"].title()] += count
                if age:
                    by_city[city]["age"][age] += count
                    state["age"][age] += count
                if school:
                    by_city[city]["school"][school] += count
                    state["school"][school] += count

    def summarize(record: dict) -> dict:
        total = record["total"]
        return {
            "eleitores_2026": total,
            "mulheres_pct": round(100 * record["gender"].get("Feminino", 0) / total, 3),
            "idade_pct": {
                key: round(100 * value / total, 3)
                for key, value in record["age"].items()
            },
            "escolaridade_pct": {
                key: round(100 * value / total, 3)
                for key, value in record["school"].items()
            },
        }

    state_summary = summarize(state)
    state_summary["obrigatoriedade_pct"] = {
        key: round(100 * value / state["total"], 3)
        for key, value in state["mandatory"].items()
    }
    return {key: summarize(value) for key, value in by_city.items()}, state_summary


def election_members(archive: zipfile.ZipFile, year: int) -> tuple[str, str]:
    names = archive.namelist()
    mg = next(name for name in names if name.endswith(f"_{year}_MG.csv"))
    br = next(name for name in names if name.endswith(f"_{year}_BR.csv"))
    return mg, br


def scan_elections() -> tuple[list[dict], dict]:
    totals = defaultdict(Counter)
    municipal = defaultdict(Counter)
    parties: dict[tuple, str] = {}
    for year in (2018, 2022):
        path = TSE_RESULTS / f"votacao_candidato_munzona_{year}.zip"
        with zipfile.ZipFile(path) as archive:
            mg_member, br_member = election_members(archive, year)
            state_offices = {"GOVERNADOR", "SENADOR"}
            if year == 2022:
                state_offices.add("DEPUTADO FEDERAL")
            for member, offices in (
                (mg_member, state_offices),
                (br_member, {"PRESIDENTE"}),
            ):
                with archive.open(member) as raw:
                    text = io.TextIOWrapper(raw, encoding="latin-1", newline="")
                    for row in csv.DictReader(text, delimiter=";"):
                        office_raw = row["DS_CARGO"].upper()
                        if row["SG_UF"] != "MG" or office_raw not in offices:
                            continue
                        office = office_raw.title()
                        turn = int(row["NR_TURNO"])
                        candidate = row["NM_URNA_CANDIDATO"].title()
                        city = normalize(row["NM_MUNICIPIO"])
                        votes = int(row["QT_VOTOS_NOMINAIS_VALIDOS"])
                        key = (year, turn, office)
                        totals[key][candidate] += votes
                        city_key = (year, turn, office, city)
                        if office_raw == "DEPUTADO FEDERAL":
                            municipal[city_key]["__TOTAL_VALIDOS__"] += votes
                            if normalize(candidate) == "NIKOLAS FERREIRA":
                                municipal[city_key][candidate] += votes
                        else:
                            municipal[city_key][candidate] += votes
                        parties[(year, office, candidate)] = row["SG_PARTIDO"]

    rows = []
    for (year, turn, office, city), candidates in sorted(municipal.items()):
        for candidate, votes in candidates.items():
            rows.append(
                {
                    "ano": year,
                    "turno": turn,
                    "cargo": office,
                    "municipio_norm": city,
                    "candidato": candidate,
                    "partido": parties.get((year, office, candidate), ""),
                    "votos": votes,
                }
            )
    state = {}
    for (year, turn, office), candidates in sorted(totals.items()):
        ordered = candidates.most_common()
        valid = sum(candidates.values())
        state[f"{year}_{turn}_{office.lower()}"] = {
            "votos_validos": valid,
            "candidatos": [
                {
                    "nome": name,
                    "partido": parties.get((year, office, name), ""),
                    "votos": votes,
                    "pct_validos": round(100 * votes / valid, 5),
                }
                for name, votes in ordered
            ],
        }
    return rows, state


def numpy_column(values) -> np.ndarray:
    return np.array(
        [np.nan if value in (None, "") else float(value) for value in values],
        dtype=float,
    )


def replicate_stat(
    theta: float, replicas: np.ndarray, digits: int = 2, key: str = "valor"
) -> dict:
    variance = float(np.sum((replicas - theta) ** 2) / (len(replicas) - 1))
    moe = Z95 * math.sqrt(variance)
    return {
        key: round(theta, digits),
        "moe": round(moe, digits),
        "low": round(theta - moe, digits),
        "high": round(theta + moe, digits),
    }


def weighted_ratio(
    weights: np.ndarray, mask: np.ndarray, universe: np.ndarray, key: str = "pct"
) -> dict:
    num = np.einsum("i,ij->j", mask.astype(float), weights)
    den = np.einsum("i,ij->j", universe.astype(float), weights)
    values = 100 * num / den
    return replicate_stat(float(values[0]), values[1:], 2, key)


def weighted_mean(
    weights: np.ndarray, values: np.ndarray, universe: np.ndarray, key: str = "media"
) -> dict:
    known = universe & np.isfinite(values)
    num = np.einsum("i,ij->j", np.where(known, values, 0.0), weights)
    den = np.einsum("i,ij->j", known.astype(float), weights)
    result = num / den
    return replicate_stat(float(result[0]), result[1:], 2, key)


def fetch_pnad(table: str, fields: list[str], weight_prefix: str):
    replicas = [
        f"{weight_prefix}{index:03d}__peso_replicado_{index}"
        for index in range(1, REPLICATES + 1)
    ]
    weight = f"{weight_prefix}__peso_com_calibracao"
    sql = f'SELECT {",".join(fields)}, {weight}, {",".join(replicas)} FROM "{table}" WHERE UF__unidade_da_federacao=31'
    with sqlite3.connect(f"file:{PNAD_DB}?mode=ro", uri=True) as connection:
        rows = connection.execute(sql).fetchall()
    dims = [
        numpy_column(column)
        for column in zip(*(row[: len(fields)] for row in rows), strict=False)
    ]
    weights = np.array([row[len(fields) :] for row in rows], dtype=float)
    return dims, weights


def read_pnad() -> dict:
    annual_fields = [
        "V2007__sexo",
        "V2009__idade_na_data_de_referencia",
        "VD5001__rend_efetivo_domiciliar_mw",
        "VD5002__rend_efetivo_domiciliar_per_capita_202604",
        "Capital__municipio_da_capital",
        "RM_RIDE__reg_metr_e_reg_adm_int_des",
        "V5002A__recebeu_bolsa_familia",
    ]
    (sex, age, income_mw, income_pc, capital, metro, bolsa), aw = fetch_pnad(
        "base_anual_visita1_labeled_npv", annual_fields, "V1032"
    )
    all_people = np.ones(len(age), dtype=bool)
    adults = age >= 16
    income_known = adults & np.isfinite(income_mw)
    territories = {
        "Belo Horizonte": capital == 31,
        "RM de Belo Horizonte, sem capital": (metro == 31) & (capital != 31),
        "Interior, fora da RM": metro != 31,
    }
    annual = {
        "populacao_total": round(float(np.sum(aw[:, 0]))),
        "populacao_16_mais": round(float(np.sum(aw[adults, 0]))),
        "sexo_16_mais": {
            "Mulheres": weighted_ratio(aw, adults & (sex == 2), adults),
            "Homens": weighted_ratio(aw, adults & (sex == 1), adults),
        },
        "idade_16_mais": {
            "16-34": weighted_ratio(aw, (age >= 16) & (age <= 34), adults),
            "35-59": weighted_ratio(aw, (age >= 35) & (age <= 59), adults),
            "60+": weighted_ratio(aw, age >= 60, adults),
        },
        "renda_domiciliar_16_mais": {
            "Até 2 SM": weighted_ratio(
                aw, income_known & (income_mw <= 2), income_known
            ),
            "Mais de 2 a 5 SM": weighted_ratio(
                aw, income_known & (income_mw > 2) & (income_mw <= 5), income_known
            ),
            "Mais de 5 SM": weighted_ratio(
                aw, income_known & (income_mw > 5), income_known
            ),
        },
        "renda_pc_media_todos_abril_2026": weighted_mean(aw, income_pc, all_people),
        "bolsa_familia_pessoas_pct": weighted_ratio(aw, bolsa == 1, all_people),
        "territorios": {},
    }
    for name, mask in territories.items():
        annual["territorios"][name] = {
            "populacao_pct": weighted_ratio(aw, mask, all_people),
            "renda_pc_media_abril_2026": weighted_mean(aw, income_pc, mask),
            "bolsa_familia_pct": weighted_ratio(aw, mask & (bolsa == 1), mask),
        }

    quarter_fields = [
        "V2009__idade_na_data_de_referencia",
        "VD3004__nivel_de_instrucao_mais_elevado_alcancado_5_anos_ou_mais_de_idade",
        "VD4001__condicao_em_relacao_forca_d_trab",
        "VD4002__condicao_de_ocupacao",
        "VD4009__posicao_na_ocupacao_trab_princ",
        "VD4020__rendim_efetivo_qq_trabalho_202604",
        "Capital__municipio_da_capital",
        "RM_RIDE__reg_metr_e_reg_adm_int_des",
    ]
    (
        q_age,
        school,
        labor_force,
        employed,
        position,
        work_income,
        _q_capital,
        _q_metro,
    ), qw = fetch_pnad("base_labeled_npv", quarter_fields, "V1028")
    q_adults = q_age >= 16
    labor = q_adults & (labor_force == 1)
    occupied = q_adults & (employed == 1)
    informal = occupied & np.isin(position, [2, 4, 6, 9, 10])
    quarter = {
        "escolaridade_16_mais": {
            "Fundamental": weighted_ratio(
                qw, q_adults & (school >= 1) & (school <= 3), q_adults
            ),
            "Médio": weighted_ratio(
                qw, q_adults & (school >= 4) & (school <= 5), q_adults
            ),
            "Superior": weighted_ratio(qw, q_adults & (school >= 6), q_adults),
        },
        "participacao_trabalho_16_mais_pct": weighted_ratio(qw, labor, q_adults),
        "ocupacao_16_mais_pct": weighted_ratio(qw, occupied, q_adults),
        "desocupacao_forca_trabalho_pct": weighted_ratio(
            qw, labor & (employed == 2), labor
        ),
        "informalidade_ocupados_pct": weighted_ratio(qw, informal, occupied),
        "renda_media_trabalho_ocupados_abril_2026": weighted_mean(
            qw, work_income, occupied
        ),
    }
    return {
        "anual_2025_visita1": annual,
        "trimestral_2026_t1": quarter,
        "metodo": {
            "universo": "Minas Gerais; indicadores eleitorais e de renda da amostra restritos a 16 anos ou mais quando indicado",
            "pesos": "V1032 na anual 2025 e V1028 no trimestre 2026 T1",
            "incerteza": "IC 95% pelas 200 réplicas oficiais; variância = soma((theta_r-theta)^2)/(R-1)",
            "monetarios": "valores deflacionados para abril de 2026",
        },
    }


QUAEST = {
    "instituto": "Quaest",
    "registro": ["MG-04060/2026", "BR-09818/2026"],
    "campo": "21–24/08/2026",
    "entrevistas": 1506,
    "margem_erro_pp": 3,
    "governador_1t": {
        "pagina": 8,
        "valores": {
            "Cleitinho Azevedo": 29,
            "Patrus Ananias": 11,
            "Alexandre Kalil": 10,
            "Mateus Simões": 7,
            "Gabriel Azevedo": 5,
            "Flávio Roscoe": 3,
            "Ben Mendes": 2,
            "Túlio Lopes": 1,
            "Rafael Duda": 1,
            "Indira Xavier": 0,
            "Henrique Áreas": 0,
            "Indecisos": 19,
            "Branco/nulo/não vai votar": 12,
        },
    },
    "governador_1t_sexo": {
        "pagina": 9,
        "perfil": {"Feminino": 52, "Masculino": 48},
        "valores": {
            "Feminino": [23, 11, 10, 6, 6, 3, 1, 1, 1, 0, 0, 25, 13],
            "Masculino": [36, 10, 11, 7, 4, 3, 3, 1, 1, 0, 0, 13, 11],
        },
    },
    "governador_1t_renda": {
        "pagina": 12,
        "perfil": {"Até 2 SM": 27, "Mais de 2 a 5 SM": 46, "Mais de 5 SM": 27},
        "valores": {
            "Até 2 SM": [26, 9, 9, 7, 5, 2, 1, 1, 1, 0, 0, 23, 16],
            "Mais de 2 a 5 SM": [32, 10, 11, 8, 4, 4, 2, 1, 1, 0, 0, 20, 9],
            "Mais de 5 SM": [31, 13, 11, 4, 5, 5, 5, 2, 1, 0, 0, 14, 14],
        },
    },
    "segundos_turnos": {
        "pagina": 20,
        "cenarios": {
            "Cleitinho × Kalil": [48, 27, 15, 10],
            "Cleitinho × Patrus": [51, 26, 12, 11],
            "Cleitinho × Mateus": [49, 17, 17, 17],
            "Kalil × Patrus": [42, 18, 15, 25],
            "Kalil × Mateus": [32, 30, 17, 21],
            "Patrus × Mateus": [35, 31, 15, 19],
        },
        "ordem": ["candidato 1", "candidato 2", "indecisos", "branco/nulo"],
    },
    "decisao_governador": {
        "pagina": 17,
        "definitiva": 54,
        "pode_mudar": 45,
        "ns_nr": 1,
    },
    "potencial_rejeicao_governador": {
        "pagina": 70,
        "valores": {
            "Cleitinho Azevedo": [46, 34, 20],
            "Mateus Simões": [31, 53, 16],
            "Alexandre Kalil": [29, 30, 41],
            "Patrus Ananias": [24, 36, 40],
            "Flávio Roscoe": [17, 69, 14],
            "Gabriel Azevedo": [15, 68, 17],
        },
    },
    "preferencia_alinhamento_governador": {
        "pagina": 74,
        "Lula": 34,
        "Independente": 31,
        "Flávio Bolsonaro": 30,
        "NS/NR": 5,
    },
    "impacto_apoio": {
        "pagina": 75,
        "valores": {
            "Lula": [23, 38, 36, 3],
            "Flávio Bolsonaro": [27, 40, 28, 5],
            "Zema": [26, 49, 21, 4],
        },
        "ordem": ["aumentaria", "não mudaria", "diminuiria", "ns/nr"],
    },
    "governo_mateus": {
        "aprovacao_pagina": 77,
        "aprova": 37,
        "desaprova": 27,
        "ns_nr": 36,
        "avaliacao_pagina": 86,
        "positivo": 30,
        "regular": 30,
        "negativo": 16,
        "ns_nr_avaliacao": 24,
    },
    "mudanca": {
        "pagina": 95,
        "continuar": 16,
        "mudar_so_ruim": 43,
        "mudar_totalmente": 37,
        "ns_nr": 4,
    },
    "zema_sucessor": {"pagina": 97, "merece": 40, "nao_merece": 47, "ns_nr": 13},
    "senado": {
        "pagina": 102,
        "combinado": {
            "Marília Campos": 15,
            "Carlos Viana": 8,
            "Domingos Sávio": 8,
            "Marcelo Aro": 6,
            "Áurea Carolina": 2,
            "Marco Antônio Superman": 2,
            "Carlin Moura": 2,
            "Gustavo Galassi": 1,
            "Marcelo Heringer": 1,
            "Ana Luiza do MLB": 1,
            "Manoel Carvalho": 1,
            "Juiz Ramon Moreira": 1,
            "Indecisos": 31,
            "Branco/nulo/não vai votar": 21,
        },
        "primeiro": {
            "Marília Campos": 19,
            "Carlos Viana": 10,
            "Domingos Sávio": 10,
            "Marcelo Aro": 6,
            "Áurea Carolina": 1,
            "Indecisos": 28,
            "Branco/nulo/não vai votar": 18,
        },
        "segundo": {
            "Marília Campos": 10,
            "Carlos Viana": 6,
            "Domingos Sávio": 6,
            "Marcelo Aro": 6,
            "Áurea Carolina": 3,
            "Indecisos": 34,
            "Branco/nulo/não vai votar": 24,
        },
    },
    "decisao_senado": {"pagina": 104, "definitiva": 48, "pode_mudar": 52},
    "presidente": {
        "cenario_1_pagina": 108,
        "cenario_1": {
            "Lula": 31,
            "Flávio Bolsonaro": 31,
            "Zema": 6,
            "Pablo Marçal": 3,
            "Renan Santos": 3,
            "Ronaldo Caiado": 2,
            "Augusto Cury": 1,
            "Indecisos": 16,
            "Branco/nulo/não vai votar": 7,
        },
        "cenario_2_pagina": 116,
        "cenario_2": {
            "Flávio Bolsonaro": 31,
            "Lula": 30,
            "Zema": 7,
            "Ronaldo Caiado": 3,
            "Renan Santos": 3,
            "Augusto Cury": 1,
            "Indecisos": 17,
            "Branco/nulo/não vai votar": 8,
        },
    },
    "decisao_presidente": {
        "pagina": 143,
        "definitiva": 71,
        "pode_mudar": 29,
        "por_candidato_pagina": 144,
        "Lula": [81, 19],
        "Flávio Bolsonaro": [74, 26],
        "Zema": [49, 51],
    },
    "governo_lula": {
        "aprovacao_pagina": 125,
        "aprova": 41,
        "desaprova": 52,
        "ns_nr": 7,
        "avaliacao_pagina": 134,
        "positivo": 30,
        "regular": 24,
        "negativo": 45,
        "ns_nr_avaliacao": 1,
    },
    "problemas": {
        "pagina": 146,
        "valores": {
            "Saúde": 28,
            "Violência": 13,
            "Economia": 10,
            "Educação": 9,
            "Corrupção": 7,
            "Infraestrutura": 7,
            "Pobreza/desigualdade": 4,
            "Desemprego": 2,
            "Enchentes": 1,
            "Outros": 7,
            "Nenhum": 1,
            "NS/NR": 11,
        },
    },
    "midia": {
        "pagina": 148,
        "valores": {
            "Redes sociais": 35,
            "TV": 32,
            "Amigos/familiares": 10,
            "Sites e portais": 8,
            "WhatsApp/Telegram": 3,
            "Rádio": 2,
            "Chat com IA": 1,
            "Jornais impressos": 1,
            "Não se informa": 7,
            "NS/NR": 1,
        },
    },
    "identificacao": {
        "pagina": 150,
        "valores": {
            "Lulista": 20,
            "Esquerda não lulista": 12,
            "Independente": 29,
            "Direita não bolsonarista": 18,
            "Bolsonarista": 17,
            "NS/NR": 4,
        },
    },
    "perfil": {
        "paginas": [152, 153, 154, 155, 156],
        "sexo": {"Feminino": 52, "Masculino": 48},
        "idade": {"16-34": 29, "35-59": 45, "60+": 26},
        "escolaridade": {"Fundamental": 44, "Médio": 38, "Superior": 18},
        "raca": {"Parda": 47, "Branca": 40, "Preta": 13},
        "renda": {"Até 2 SM": 27, "Mais de 2 a 5 SM": 46, "Mais de 5 SM": 27},
    },
}


REALTIME = {
    "instituto": "Real Time Big Data",
    "registro": ["MG-07972/2026"],
    "campo": "22–26/08/2026",
    "entrevistas": 2000,
    "margem_erro_pp": 2,
    "perfil": {
        "pagina": 3,
        "sexo": {"Homem": 47, "Mulher": 53},
        "idade": {"16-34": 29, "35-59": 45, "60+": 26},
        "escolaridade": {
            "Até fundamental completo": 41,
            "Até médio completo": 44,
            "Superior incompleto ou mais": 15,
        },
        "renda": {"Até 2 SM": 45, "2 a 5 SM": 35, "Mais de 5 SM": 20},
    },
    "governador_1t": {
        "pagina": 7,
        "valores": {
            "Cleitinho Azevedo": 33,
            "Patrus Ananias": 15,
            "Alexandre Kalil": 13,
            "Mateus Simões": 11,
            "Gabriel Azevedo": 7,
            "Flávio Roscoe": 5,
            "Ben Mendes": 3,
            "Indira Xavier": 1,
            "Outros": 1,
            "Branco/nulo": 5,
            "NS/NR": 6,
        },
    },
    "segundos_turnos": {
        "paginas": [12, 13, 14, 15, 16, 17],
        "cenarios": {
            "Cleitinho × Kalil": [46, 35, 8, 11],
            "Kalil × Mateus": [35, 35, 17, 13],
            "Kalil × Patrus": [38, 38, 12, 12],
            "Cleitinho × Mateus": [46, 31, 11, 12],
            "Cleitinho × Patrus": [45, 40, 6, 9],
            "Patrus × Mateus": [37, 33, 18, 12],
        },
        "ordem": ["candidato 1", "candidato 2", "ns/nr", "branco/nulo"],
    },
    "rejeicao": {
        "pagina": 19,
        "valores": {
            "Cleitinho Azevedo": 43,
            "Patrus Ananias": 42,
            "Alexandre Kalil": 40,
            "Flávio Roscoe": 26,
            "Mateus Simões": 25,
            "Ben Mendes": 19,
            "Gabriel Azevedo": 18,
            "Túlio Lopes": 18,
            "Indira Xavier": 17,
            "Rafael Duda": 16,
            "Henrique Áreas": 11,
        },
    },
    "votabilidade": {
        "paginas": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
        "ordem": [
            "votaria com certeza",
            "considera",
            "conhece e não votaria",
            "não conhece suficiente",
        ],
        "valores": {
            "Alexandre Kalil": [9, 36, 44, 11],
            "Ben Mendes": [1, 18, 21, 60],
            "Cleitinho Azevedo": [19, 28, 47, 6],
            "Flávio Roscoe": [2, 28, 29, 41],
            "Gabriel Azevedo": [4, 36, 24, 36],
            "Henrique Áreas": [0, 7, 14, 79],
            "Indira Xavier": [1, 17, 26, 56],
            "Mateus Simões": [7, 37, 32, 24],
            "Patrus Ananias": [10, 29, 46, 15],
            "Túlio Lopes": [0, 10, 26, 64],
            "Rafael Duda": [0, 14, 26, 60],
        },
    },
    "governo_mateus": {
        "pagina": 33,
        "aprova": 56,
        "desaprova": 40,
        "ns_nr": 4,
        "otimo_bom": 28,
        "regular": 41,
        "ruim_pessimo": 28,
        "ns_nr_avaliacao": 3,
    },
    "senado": {
        "paginas": [36, 37],
        "consolidado": {
            "Marília Campos": 24,
            "Carlos Viana": 13,
            "Domingos Sávio": 13,
            "Marcelo Aro": 12,
            "Áurea Carolina": 9,
            "Marco Antônio Superman": 4,
            "Branco/nulo": 8,
            "NS/NR": 11,
        },
        "primeiro": {
            "Marília Campos": 31,
            "Carlos Viana": 16,
            "Domingos Sávio": 12,
            "Marcelo Aro": 11,
            "Áurea Carolina": 7,
            "Marco Antônio Superman": 3,
            "Branco/nulo": 6,
            "NS/NR": 10,
        },
        "segundo": {
            "Marília Campos": 17,
            "Carlos Viana": 10,
            "Domingos Sávio": 14,
            "Marcelo Aro": 12,
            "Áurea Carolina": 10,
            "Marco Antônio Superman": 5,
            "Outros": 4,
            "Branco/nulo": 10,
            "NS/NR": 12,
        },
    },
}


def validate_polls() -> dict:
    labels = list(QUAEST["governador_1t"]["valores"])
    general = np.array(list(QUAEST["governador_1t"]["valores"].values()), dtype=float)
    checks = {}
    for dimension in ("governador_1t_sexo", "governador_1t_renda"):
        block = QUAEST[dimension]
        weights = np.array(list(block["perfil"].values()), dtype=float) / 100
        matrix = np.array(list(block["valores"].values()), dtype=float)
        recomposed = weights @ matrix
        errors = recomposed - general
        checks[dimension] = {
            "pagina": block["pagina"],
            "max_erro_arredondamento_pp": round(float(np.max(np.abs(errors))), 3),
            "recomposto": {
                label: round(float(value), 3)
                for label, value in zip(labels, recomposed, strict=False)
            },
        }
    return checks


def index_elections(rows: list[dict]):
    return {
        (
            row["ano"],
            row["turno"],
            row["cargo"],
            row["municipio_norm"],
            row["candidato"],
        ): row["votos"]
        for row in rows
    }


def candidate_name(state: dict, key: str, party: str) -> str:
    return next(
        item["nome"] for item in state[key]["candidatos"] if item["partido"] == party
    )


def enrich_municipalities(
    municipalities: dict, electorate: dict, election_rows: list[dict], state: dict
) -> list[dict]:
    lookup = index_elections(election_rows)
    finalist = {
        (2018, "Presidente", "right"): candidate_name(
            state, "2018_2_presidente", "PSL"
        ),
        (2018, "Presidente", "left"): candidate_name(state, "2018_2_presidente", "PT"),
        (2022, "Presidente", "right"): candidate_name(state, "2022_2_presidente", "PL"),
        (2022, "Presidente", "left"): candidate_name(state, "2022_2_presidente", "PT"),
    }
    nikolas = next(
        item["nome"]
        for item in state["2022_1_deputado federal"]["candidatos"]
        if normalize(item["nome"]) == "NIKOLAS FERREIRA"
    )
    out = []
    for record in municipalities.values():
        city = record["municipio_norm"]
        voter = electorate.get(city)
        if voter is None:
            raise KeyError(f"Município sem eleitorado TSE: {record['municipio']}")
        item = record | voter
        item["nikolas_2022_votos"] = lookup.get(
            (2022, 1, "Deputado Federal", city, nikolas), 0
        )
        deputado_valid = lookup.get(
            (2022, 1, "Deputado Federal", city, "__TOTAL_VALIDOS__"), 0
        )
        item["deputado_federal_2022_votos_validos"] = deputado_valid
        item["nikolas_2022_pct_validos_deputado"] = round(
            100 * item["nikolas_2022_votos"] / deputado_valid if deputado_valid else 0,
            4,
        )
        shares = {}
        for year in (2018, 2022):
            right = lookup.get(
                (year, 2, "Presidente", city, finalist[(year, "Presidente", "right")]),
                0,
            )
            left = lookup.get(
                (year, 2, "Presidente", city, finalist[(year, "Presidente", "left")]), 0
            )
            valid = right + left
            shares[year] = {
                "right": right,
                "left": left,
                "valid": valid,
                "left_share": left / valid if valid else 0,
            }
            item[f"pres_{year}_direita_votos"] = right
            item[f"pres_{year}_esquerda_votos"] = left
            item[f"pres_{year}_esquerda_pct_validos"] = round(
                100 * shares[year]["left_share"], 4
            )
            item[f"pres_{year}_margem_esquerda_pp"] = round(
                100 * (2 * shares[year]["left_share"] - 1), 4
            )
        item["pres_virada"] = (
            "Direita→esquerda"
            if shares[2018]["left_share"] < 0.5 <= shares[2022]["left_share"]
            else (
                "Esquerda→direita"
                if shares[2018]["left_share"] >= 0.5 > shares[2022]["left_share"]
                else (
                    "Direita nas duas"
                    if shares[2022]["left_share"] < 0.5
                    else "Esquerda nas duas"
                )
            )
        )
        item["pres_deslocamento_esquerda_pp"] = round(
            100 * (shares[2022]["left_share"] - shares[2018]["left_share"]), 4
        )
        item["eleitores_por_100_habitantes"] = round(
            100 * item["eleitores_2026"] / item["populacao_2022"], 2
        )
        closeness = max(0.0, 1 - abs(item["pres_2022_margem_esquerda_pp"]) / 25)
        movement = min(abs(item["pres_deslocamento_esquerda_pp"]) / 15, 1)
        item["indice_pivotal_bruto"] = (
            item["eleitores_2026"] * (0.4 + 0.6 * closeness) * (0.5 + 0.5 * movement)
        )
        out.append(item)
    maximum = max(item["indice_pivotal_bruto"] for item in out)
    for item in out:
        item["indice_pivotal"] = round(
            100 * item.pop("indice_pivotal_bruto") / maximum, 2
        )
    return sorted(out, key=lambda item: item["municipio"])


def aggregate_regions(municipalities: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for item in municipalities:
        groups[item["regiao_intermediaria"]].append(item)
    out = []
    for name, items in groups.items():
        electors = sum(item["eleitores_2026"] for item in items)
        population = sum(item["populacao_2022"] for item in items)
        pib = sum(item["pib_2023_mil_reais"] for item in items)
        left18 = sum(item["pres_2018_esquerda_votos"] for item in items)
        right18 = sum(item["pres_2018_direita_votos"] for item in items)
        left22 = sum(item["pres_2022_esquerda_votos"] for item in items)
        right22 = sum(item["pres_2022_direita_votos"] for item in items)
        covered = sum(item["moradores_cobertos_renda_2022"] for item in items)
        mean_income = (
            sum(
                item["renda_pc_media_2022"] * item["moradores_cobertos_renda_2022"]
                for item in items
            )
            / covered
        )
        sectors = {
            key: sum(item[f"vab_{key}_2021_mil_reais"] for item in items)
            for key in ("agro", "industria", "servicos", "administracao")
        }
        sector_total = sum(sectors.values())
        nikolas_votes = sum(item["nikolas_2022_votos"] for item in items)
        deputy_valid = sum(
            item["deputado_federal_2022_votos_validos"] for item in items
        )
        out.append(
            {
                "regiao_intermediaria": name,
                "municipios": len(items),
                "populacao_2022": population,
                "eleitores_2026": electors,
                "pib_2023_mil_reais": round(pib, 3),
                "pib_pc_aproximado_2023": round(1000 * pib / population, 2),
                "renda_pc_media_2022": round(mean_income, 2),
                "nikolas_2022_votos": nikolas_votes,
                "nikolas_2022_pct_validos_deputado": round(
                    100 * nikolas_votes / deputy_valid, 3
                ),
                "vab_2021_pct": {
                    key: round(100 * value / sector_total, 3)
                    for key, value in sectors.items()
                },
                "esquerda_2018_pct_validos": round(
                    100 * left18 / (left18 + right18), 3
                ),
                "esquerda_2022_pct_validos": round(
                    100 * left22 / (left22 + right22), 3
                ),
                "deslocamento_esquerda_pp": round(
                    100 * left22 / (left22 + right22)
                    - 100 * left18 / (left18 + right18),
                    3,
                ),
            }
        )
    total_pib = sum(item["pib_2023_mil_reais"] for item in out)
    total_electors = sum(item["eleitores_2026"] for item in out)
    for item in out:
        item["pib_mg_pct"] = round(100 * item["pib_2023_mil_reais"] / total_pib, 3)
        item["eleitorado_mg_pct"] = round(
            100 * item["eleitores_2026"] / total_electors, 3
        )
    return sorted(out, key=lambda item: item["eleitores_2026"], reverse=True)


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    municipalities, geometry = read_ibge()
    electorate, electorate_state = read_tse_electorate()
    election_rows, election_state = scan_elections()
    municipal = enrich_municipalities(
        municipalities, electorate, election_rows, election_state
    )
    regions = aggregate_regions(municipal)
    pnad = read_pnad()
    checks = validate_polls()

    write_csv(DERIVED / "votos-municipais-tse-2018-2022.csv", election_rows)
    flat = []
    nested = {"idade_pct", "escolaridade_pct"}
    for row in municipal:
        flat.append(
            {
                key: json.dumps(value, ensure_ascii=False) if key in nested else value
                for key, value in row.items()
            }
        )
    write_csv(DERIVED / "municipios.csv", flat)
    write_csv(DERIVED / "regioes-intermediarias.csv", regions)

    top = sorted(municipal, key=lambda item: item["indice_pivotal"], reverse=True)[:20]
    public_keys = [
        "codigo_ibge",
        "municipio",
        "regiao_imediata",
        "regiao_intermediaria",
        "populacao_2022",
        "eleitores_2026",
        "renda_pc_media_2022",
        "renda_pc_mediana_2022",
        "pib_2023_mil_reais",
        "pib_pc_2023",
        "atividade_principal_2021",
        "participacao_agro_2021_pct",
        "participacao_industria_2021_pct",
        "participacao_servicos_2021_pct",
        "participacao_administracao_2021_pct",
        "nikolas_2022_votos",
        "nikolas_2022_pct_validos_deputado",
        "deputado_federal_2022_votos_validos",
        "pres_2018_esquerda_pct_validos",
        "pres_2022_esquerda_pct_validos",
        "pres_2018_margem_esquerda_pp",
        "pres_2022_margem_esquerda_pp",
        "pres_deslocamento_esquerda_pp",
        "pres_virada",
        "indice_pivotal",
    ]
    geo_features = []
    by_code = {item["codigo_ibge"]: item for item in municipal}
    for code, feature in geometry.items():
        feature["properties"] = {key: by_code[code].get(key) for key in public_keys}
        geo_features.append(feature)

    payload = {
        "meta": {
            "generated": "2026-08-31",
            "warning": "Resultados municipais e margens são observados; matrizes de transferência exibidas no dossiê são estimativas agregadas por IPF, não trajetórias individuais.",
            "indice_pivotal": "eleitorado × (0,4 + 0,6×proximidade de 50% em 2022) × (0,5 + 0,5×movimento 2018–2022), reescalado para 0–100",
        },
        "eleitorado_tse_2026": electorate_state,
        "pnad": pnad,
        "eleicoes": election_state,
        "pesquisas": {
            "quaest": QUAEST,
            "real_time": REALTIME,
            "validacao_quaest": checks,
        },
        "regioes": regions,
        "top_20_pivotais": [
            {key: item.get(key) for key in public_keys} for item in top
        ],
    }
    (DERIVED / "auditoria.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = source_manifest()
    (DERIVED / "fontes.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (PUBLIC / "mg_082026_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (PUBLIC / "mg_082026_fontes.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (PUBLIC / "mg_082026_municipios.geojson").write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": geo_features},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "municipios": len(municipal),
                "eleitores_2026": electorate_state["eleitores_2026"],
                "regioes_intermediarias": len(regions),
                "viradas": Counter(item["pres_virada"] for item in municipal),
                "top_20": [item["municipio"] for item in top],
                "validacao_quaest": checks,
            },
            ensure_ascii=False,
            indent=2,
            default=dict,
        )
    )


if __name__ == "__main__":
    main()
