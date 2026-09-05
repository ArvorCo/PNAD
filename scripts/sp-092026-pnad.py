#!/usr/bin/env python3
"""PNAD paulista com pesos e réplicas, adaptação explícita do estimador de MG."""

import json
import math
import sqlite3
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
REPLICATES = 200
Z95 = NormalDist().inv_cdf(0.975)


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
    sql = f'SELECT {",".join(fields)}, {weight}, {",".join(replicas)} FROM "{table}" WHERE UF__unidade_da_federacao=35'
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
        "VD5001__rend_efetivo_domiciliar_202604",
    ]
    (sex, age, income_mw, income_pc, capital, metro, bolsa, income_brl), aw = (
        fetch_pnad("base_anual_visita1_labeled_npv", annual_fields, "V1032")
    )
    all_people = np.ones(len(age), dtype=bool)
    adults = age >= 16
    income_known = adults & np.isfinite(income_mw)
    territories = {
        "São Paulo": capital == 35,
        "RM de São Paulo, sem capital": (metro == 35) & (capital != 35),
        "Fora da RM de São Paulo": metro != 35,
    }
    annual = {
        "renda_brl_abril_2026": {
            label: weighted_ratio(
                aw,
                adults
                & np.isfinite(income_brl)
                & (income_brl > low)
                & (income_brl <= high),
                adults & np.isfinite(income_brl),
            )
            for label, low, high in [
                ("Até 2.000", -1, 2000),
                ("2.000 a 3.000", 2000, 3000),
                ("3.000 a 5.000", 3000, 5000),
                ("5.000 a 10.000", 5000, 10000),
                ("Acima de 10.000", 10000, float("inf")),
            ]
        },
        "amostra_pessoas": len(age),
        "amostra_pessoas_16_mais": int(adults.sum()),
        "renda_nao_informada_16_mais_pct": weighted_ratio(
            aw, adults & ~np.isfinite(income_mw), adults
        ),
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
        "declarantes_recebimento_bolsa_familia_pct": weighted_ratio(
            aw, bolsa == 1, all_people
        ),
        "territorios": {},
    }
    for name, mask in territories.items():
        annual["territorios"][name] = {
            "populacao_pct": weighted_ratio(aw, mask, all_people),
            "renda_pc_media_abril_2026": weighted_mean(aw, income_pc, mask),
            "declarantes_recebimento_bolsa_familia_pct": weighted_ratio(
                aw, mask & (bolsa == 1), mask
            ),
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
        (
            q_age,
            school,
            labor_force,
            employed,
            _position,
            work_income,
            _q_capital,
            _q_metro,
        ),
        qw,
    ) = fetch_pnad("base_labeled_npv", quarter_fields, "V1028")
    q_adults = q_age >= 16
    labor = q_adults & (labor_force == 1)
    occupied = q_adults & (employed == 1)
    quarter = {
        "escolaridade_16_mais": {
            "Até fundamental completo": weighted_ratio(
                qw, q_adults & (school >= 1) & (school <= 3), q_adults
            ),
            "Médio incompleto ou completo": weighted_ratio(
                qw, q_adults & (school >= 4) & (school <= 5), q_adults
            ),
            "Superior incompleto ou completo": weighted_ratio(
                qw, q_adults & (school >= 6), q_adults
            ),
        },
        "participacao_trabalho_16_mais_pct": weighted_ratio(qw, labor, q_adults),
        "ocupacao_16_mais_pct": weighted_ratio(qw, occupied, q_adults),
        "desocupacao_forca_trabalho_pct": weighted_ratio(
            qw, labor & (employed == 2), labor
        ),
        "renda_media_trabalho_ocupados_abril_2026": weighted_mean(
            qw, work_income, occupied
        ),
    }
    return {
        "anual_2025_visita1": annual,
        "trimestral_2026_t1": quarter,
        "metodo": {
            "universo": "São Paulo; indicadores eleitorais e de renda da amostra restritos a 16 anos ou mais quando indicado",
            "pesos": "V1032 na anual 2025 e V1028 no trimestre 2026 T1",
            "incerteza": "IC 95% pelas 200 réplicas oficiais; variância = soma((theta_r-theta)^2)/(R-1)",
            "monetarios": "valores deflacionados para abril de 2026; SM alvo R$ 1.621",
            "bolsa_familia": "Pessoas que declararam receber o benefício; não mede moradores de domicílios beneficiários.",
        },
    }


if __name__ == "__main__":
    result = read_pnad()
    path = ROOT / "docs/assets/sp_092026_pnad.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(path)
