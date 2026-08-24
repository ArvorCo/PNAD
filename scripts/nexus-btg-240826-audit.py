#!/usr/bin/env python3
"""Rebuild the evidence for the BTG/Nexus poll disclosed on 24 Aug. 2026.

The script keeps three evidentiary layers separate:

* measured: numbers printed in the registered questionnaire and report;
* benchmark: TSE electorate or PNADc 2025, 1st visit, population aged 16+;
* sensitivity: one-margin reweighting and IPF cells not published by Nexus.

It does not infer manipulation from one respondent account. The account is used
to define checks that require paradata, CATI randomisation logs or recordings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "data/pesquisas/nexus_btg/rodada11_2026-08-24"
OUTPUT = ROOT / "docs/assets/nexus_btg_240826_data.json"
PNAD_DB = ROOT / "data/outputs/brasil.sqlite"
TSE_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"
PNAD_TABLE = "base_anual_visita1_labeled_npv"
PNAD_INCOME = "VD5001__rend_efetivo_domiciliar_mw"
WEIGHT = "V1032__peso_com_calibracao"

INTERVIEWS_REPORT = 2006
INTERVIEWS_FILED = 2000
PROFILE = {
    "sex": [53, 47],
    "age": [12, 31, 34, 24],
    "region": [16, 28, 42, 14],
    "income": [19, 18, 40, 23],
}
LABELS = {
    "sex": ["Mulher", "Homem"],
    "age": ["16–24", "25–40", "41–59", "60+"],
    "region": ["Norte/Centro-Oeste", "Nordeste", "Sudeste", "Sul"],
    "income": ["Até 1 SM", "1–2 SM", "2–5 SM", "5+ SM"],
}
TOPLINES = {
    "first": [41, 37, 5, 3, 3, 3, 5, 3],
    "runoff": [46, 45, 8, 1],
    "first_labels": [
        "Lula",
        "Flávio Bolsonaro",
        "Ronaldo Caiado",
        "Renan Santos",
        "Zema",
        "Outros",
        "Nenhum/Branco/Nulo",
        "NS/NR",
    ],
    "runoff_labels": ["Lula", "Flávio Bolsonaro", "Nenhum/Branco/Nulo", "NS/NR"],
}

# Report pp. 29–30 and 53–54. Rows are profile cells, columns follow TOPLINES.
CROSSTABS = {
    "first": {
        "sex": [[48, 31, 4, 1, 2, 5, 6, 3], [34, 43, 5, 5, 3, 3, 3, 3]],
        "age": [
            [49, 23, 2, 10, 0, 11, 4, 1],
            [36, 41, 4, 5, 3, 3, 5, 4],
            [40, 38, 7, 1, 3, 4, 4, 2],
            [47, 35, 4, 0, 3, 3, 5, 3],
        ],
        "region": [
            [31, 40, 14, 4, 1, 4, 2, 2],
            [54, 27, 3, 2, 1, 3, 6, 4],
            [40, 38, 3, 2, 4, 4, 5, 3],
            [33, 45, 2, 7, 2, 5, 3, 2],
        ],
        "income": [
            [55, 26, 2, 0, 1, 5, 8, 4],
            [42, 32, 6, 1, 2, 5, 6, 7],
            [38, 41, 5, 5, 3, 3, 4, 2],
            [36, 41, 5, 6, 4, 5, 2, 1],
        ],
    },
    "runoff": {
        "sex": [[52, 37, 8, 2], [39, 53, 7, 1]],
        "age": [[58, 32, 9, 1], [41, 50, 8, 1], [44, 47, 8, 2], [50, 42, 7, 2]],
        "region": [[38, 53, 8, 1], [57, 35, 7, 1], [46, 44, 9, 1], [37, 54, 7, 2]],
        "income": [[57, 29, 10, 3], [49, 40, 8, 3], [42, 49, 8, 1], [41, 53, 5, 0]],
    },
}

# Report p. 52. Each row is a published measurement, despite rounding to 100 or 101.
TRANSFER_SOURCES = ["Lula", "Flávio", "Caiado", "Renan", "Zema", "Cury", "Samara", "B/N", "NS"]
TRANSFER_ROWS = np.array([41, 37, 5, 3, 3, 2, 1, 5, 3], dtype=float)
TRANSFER_COLS = np.array([46, 45, 8, 1], dtype=float)
TRANSFER_MEASURED = {
    "Caiado": [23, 54, 21, 3],
    "Renan": [8, 51, 41, 0],
    "Zema": [8, 72, 18, 2],
    "Cury": [31, 48, 22, 0],
    "Samara": [66, 7, 27, 0],
}
TRANSFER_PRIOR = {
    "Lula": [98, 0.4, 1.2, 0.4],
    "Flávio": [0.5, 98, 1, 0.5],
    "B/N": [15, 15, 67, 3],
    "NS": [18, 18, 22, 42],
}

# Report pp. 23, 27, 33, 35 and 52. These marginals are published separately.
# Nexus does not publish the three-way cross candidate × certainty × runoff.
USEFUL_VOTE_CANDIDATES = [
    {"candidate": "Renan", "first_round": 3, "can_change": 47, "runoff_lula": 8, "runoff_flavio": 51},
    {"candidate": "Caiado", "first_round": 5, "can_change": 44, "runoff_lula": 23, "runoff_flavio": 54},
    {"candidate": "Zema", "first_round": 3, "can_change": 57, "runoff_lula": 8, "runoff_flavio": 72},
    {"candidate": "Cury", "first_round": 2, "can_change": 69, "runoff_lula": 31, "runoff_flavio": 48},
]

STRATEGIC_RESERVOIRS = {
    "bolsonaristas_convictos": {
        "share_sample": 30,
        "first_round": {"lula": 12, "flavio": 77, "third_way": 8, "nonchoice": 3},
        "can_change": 14,
        "pages": [23, 35],
    },
    "bolsonaro_como_alternativa": {
        "share_sample": 6,
        "first_round": {"lula": 25, "flavio": 34, "third_way": 39, "nonchoice": 3},
        "can_change": 35,
        "pages": [23, 35],
        "rounding_warning": "A linha soma 101% no relatório.",
    },
    "bolsa_familia": {
        "ballot": "first_round",
        "flavio_previous_wave": 20,
        "flavio_current": 27,
        "flavio_change": 7,
        "lula_previous_wave": 65,
        "lula_current": 61,
        "period": "17–24/08/2026",
        "page": 27,
        "warning": "Série ponderada sem bases não ponderadas ou intervalo por subgrupo.",
    },
}

QUESTION_PUBLICATION = [
    {"item": "PF1–PF3", "content": "sexo, idade, escolaridade", "status": "perfil e cruzamentos", "pages": "111; 11–12; 29–30; 53–60; 92–99"},
    {"item": "PF4–PF9", "content": "trabalho, vínculo, CNPJ, inatividade e busca", "status": "só agregado em PEA", "pages": "111"},
    {"item": "PF10–PF11", "content": "UF e município", "status": "só região e condição municipal", "pages": "111"},
    {"item": "P1", "content": "interesse eleitoral", "status": "topline", "pages": "6–7"},
    {"item": "P2", "content": "voto espontâneo", "status": "topline", "pages": "16–17"},
    {"item": "P3", "content": "1º turno, dois cenários", "status": "topline e cruzamentos", "pages": "18–30"},
    {"item": "P4", "content": "certeza do voto", "status": "topline e cruzamentos", "pages": "31–35"},
    {"item": "P5", "content": "quatro cenários de 2º turno", "status": "topline e cruzamentos", "pages": "37–60"},
    {"item": "P6", "content": "potencial e rejeição de cinco nomes", "status": "topline e cruzamentos", "pages": "62–70"},
    {"item": "P7", "content": "preferência por bloco político", "status": "topline e cruzamentos", "pages": "71–73"},
    {"item": "P8–P9", "content": "avaliação e aprovação do governo", "status": "topline e cruzamentos", "pages": "88–99"},
    {"item": "P10", "content": "problemas do Brasil", "status": "topline e cruzamentos", "pages": "101–103"},
    {"item": "P11–P13", "content": "economia atual, retrospectiva e expectativa", "status": "topline e cruzamentos", "pages": "105–109"},
    {"item": "P14–P18", "content": "busca, exposição e identificação de campanha", "status": "topline e cruzamentos", "pages": "75–86"},
    {"item": "P19", "content": "escala 0–10 de comparecimento", "status": "não publicada", "pages": "não se aplica"},
    {"item": "P20", "content": "probabilidade categórica de comparecimento", "status": "topline", "pages": "13–14"},
    {"item": "P21", "content": "comparecimento municipal em 2024", "status": "não publicada", "pages": "não se aplica"},
    {"item": "P22–P23", "content": "comparecimento presidencial em 2022 e 2018", "status": "só índice combinado", "pages": "21; 39; 41; 43; 45"},
    {"item": "P24", "content": "voto Lula/Bolsonaro em 2022", "status": "só cruzamento, base ausente", "pages": "22; 46"},
    {"item": "P25", "content": "Anti-Lula e Anti-Bolsonaro/família", "status": "topline e cluster sem fórmula", "pages": "8–12; 23–28; 35; 47–49; 73; 77; 84"},
    {"item": "PF13", "content": "Bolsa Família", "status": "só cruzamento, base ausente", "pages": "50–51"},
    {"item": "PF14", "content": "renda individual", "status": "não publicada", "pages": "não se aplica"},
    {"item": "PF15", "content": "renda familiar", "status": "perfil e cruzamentos", "pages": "12; 30; 54; 69–70; 93; 99; 111"},
    {"item": "PF16", "content": "religião", "status": "perfil e cruzamentos", "pages": "11; 29; 53; 69–70; 92; 98; 111"},
    {"item": "PF17", "content": "cor ou raça", "status": "não publicada", "pages": "não se aplica"},
]

TESTIMONY_CHECKS = [
    {
        "claim": "Lula foi lido primeiro e Flávio apareceu depois de nomes desconhecidos.",
        "record": "P3 manda apresentar os 12 nomes em ordem aleatória.",
        "finding": "Um relato não testa aleatoriedade; o log de posição dos 2.006 casos testa.",
        "status": "hipótese auditável",
    },
    {
        "claim": "A entrevistadora pediu que a lista inteira fosse ouvida.",
        "record": "P3 diz literalmente: espere eu ler todos os nomes.",
        "finding": "A exigência é padronização correta para reduzir respostas precoces.",
        "status": "compatível",
    },
    {
        "claim": "Depois da certeza do voto, a entrevistadora perguntou se poderia votar em outro.",
        "record": "P4 mede estabilidade temporal; P6 mede potencial/rejeição de cada nome.",
        "finding": "Os construtos são distintos; uma paráfrase de insistência não consta do roteiro.",
        "status": "ambíguo",
    },
    {
        "claim": "Foram testados Lula × Zema, Lula × Flávio e Lula × Caiado, mas não Lula × Renan.",
        "record": "P5 registra quatro cenários, incluindo Lula × Renan; o relatório publica os quatro.",
        "finding": "Se a lembrança for exata, houve omissão de campo. Gravação e trilha CATI resolvem.",
        "status": "divergência",
    },
    {
        "claim": "Só na primeira menção foi lido Flávio Bolsonaro; depois, apenas Flávio.",
        "record": "P3, P5, P6 e P15–P18 registram Flávio Bolsonaro por extenso.",
        "finding": "A abreviação relatada diverge do instrumento e é verificável nas gravações.",
        "status": "divergência",
    },
    {
        "claim": "Avaliação do governo e perfil ficaram para o final.",
        "record": "Sexo, idade, escolaridade, trabalho, UF e município vêm antes do voto; renda, religião e raça ficam no fim. Governo é P8–P9.",
        "finding": "O relato mistura dois blocos. Ainda assim, governo vem depois de sete perguntas eleitorais.",
        "status": "parcial",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def documents() -> list[dict]:
    result = []
    for path in sorted(ROUND.iterdir()):
        if not path.is_file():
            continue
        item = {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(path)
            item["pages"] = len(reader.pages)
            item["text_characters"] = sum(len(page.extract_text() or "") for page in reader.pages)
        result.append(item)
    return result


def tse_targets() -> dict[str, list[float]]:
    with sqlite3.connect(TSE_DB) as connection:
        sex_rows = dict(
            connection.execute(
                "SELECT category,pct_total FROM summary WHERE dimension='genero_atlas_binario' "
                "AND universe LIKE 'Brasil sem exterior%'"
            )
        )
        ages = dict(
            connection.execute(
                "SELECT category,qt_eleitores FROM summary WHERE dimension='idade_raw' "
                "AND universe='Brasil sem exterior'"
            )
        )
        regions = dict(
            connection.execute(
                "SELECT category,pct_total FROM summary WHERE dimension='regiao' "
                "AND universe='Brasil sem exterior'"
            )
        )
    age_counts = [
        sum(ages[name] for name in ("16 anos", "17 anos", "18 anos", "19 anos", "20 anos", "21 a 24 anos")),
        sum(ages[name] for name in ("25 a 29 anos", "30 a 34 anos", "35 a 39 anos")) + ages["40 a 44 anos"] / 5,
        ages["40 a 44 anos"] * 4 / 5 + sum(ages[name] for name in ("45 a 49 anos", "50 a 54 anos", "55 a 59 anos")),
        sum(ages[name] for name in ("60 a 64 anos", "65 a 69 anos", "70 a 74 anos", "75 a 79 anos", "80 a 84 anos", "85 a 89 anos", "90 a 94 anos", "95 a 99 anos", "100 anos ou mais")),
    ]
    age_total = sum(age_counts)
    return {
        "sex": [sex_rows["Mulher"], sex_rows["Homem"]],
        "age": [100 * value / age_total for value in age_counts],
        "region": [
            regions["Norte"] + regions["Centro-Oeste"],
            regions["Nordeste"],
            regions["Sudeste"],
            regions["Sul"],
        ],
    }


def income_target() -> dict:
    bands = [0.0, 0.0, 0.0, 0.0]
    query = f'SELECT {PNAD_INCOME},{WEIGHT} FROM "{PNAD_TABLE}" WHERE V2009__idade_na_data_de_referencia>=16 AND {PNAD_INCOME} IS NOT NULL'
    with sqlite3.connect(PNAD_DB) as connection:
        for value, weight in connection.execute(query):
            if value in (None, ""):
                continue
            value, weight = float(value), float(weight or 0)
            index = 0 if value <= 1 else 1 if value <= 2 else 2 if value <= 5 else 3
            bands[index] += weight
    total = sum(bands)
    return {
        "distribution": [100 * value / total for value in bands],
        "weighted_people": round(total),
        "universe": "Pessoas de 16 anos ou mais, PNAD Contínua anual 2025, 1ª visita",
        "variable": PNAD_INCOME,
        "weight": WEIGHT,
    }


def normalise_rows(cells) -> np.ndarray:
    matrix = np.asarray(cells, dtype=float)
    return matrix / matrix.sum(axis=1, keepdims=True) * 100


def reweight(cells, profile, target, published) -> dict:
    matrix = normalise_rows(cells)
    profile = np.asarray(profile, dtype=float)
    target = np.asarray(target, dtype=float)
    profile /= profile.sum()
    target /= target.sum()
    reproduced = profile @ matrix
    direct = target @ matrix
    anchored = np.asarray(published, dtype=float) + direct - reproduced
    gap = float(anchored[0] - anchored[1])
    published_gap = float(published[0] - published[1])
    return {
        "reproduced": reproduced.round(3).tolist(),
        "direct": direct.round(3).tolist(),
        "anchored": anchored.round(3).tolist(),
        "gap": round(gap, 3),
        "swing": round(gap - published_gap, 3),
        "two_candidate_share": [round(100 * anchored[0] / (anchored[0] + anchored[1]), 3), round(100 * anchored[1] / (anchored[0] + anchored[1]), 3)],
    }


def rounding_interval(cells, profile, target, published, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    gaps = []
    matrix = np.asarray(cells, dtype=float)
    for _ in range(10_000):
        jittered = np.clip(matrix + rng.uniform(-0.5, 0.5, matrix.shape), 0, None)
        gaps.append(reweight(jittered, profile, target, published)["gap"])
    low, median, high = np.quantile(gaps, [0.025, 0.5, 0.975])
    return {"draws": len(gaps), "p2_5": round(float(low), 3), "median": round(float(median), 3), "p97_5": round(float(high), 3)}


def all_reweighting(targets: dict[str, list[float]]) -> dict:
    output = {"first": {}, "runoff": {}}
    for ballot in ("first", "runoff"):
        published = TOPLINES[ballot]
        for index, dimension in enumerate(("sex", "age", "region", "income")):
            result = reweight(CROSSTABS[ballot][dimension], PROFILE[dimension], targets[dimension], published)
            result["rounding"] = rounding_interval(
                CROSSTABS[ballot][dimension], PROFILE[dimension], targets[dimension], published, 240826 + index + (10 if ballot == "runoff" else 0)
            )
            output[ballot][dimension] = result
    for ballot in ("first", "runoff"):
        published_gap = TOPLINES[ballot][0] - TOPLINES[ballot][1]
        additive = published_gap + sum(output[ballot][name]["swing"] for name in output[ballot])
        output[ballot]["additive_all_margins"] = {
            "gap": round(additive, 3),
            "warning": "Soma descritiva das quatro correções univariadas; não é raking nem reponderação multivariada.",
        }
    return output


def transfer_ipf() -> dict:
    index = {name: i for i, name in enumerate(TRANSFER_SOURCES)}
    matrix = np.zeros((len(TRANSFER_SOURCES), 4), dtype=float)
    measured = []
    for name, cells in TRANSFER_MEASURED.items():
        i = index[name]
        shares = np.asarray(cells, dtype=float)
        matrix[i] = shares / shares.sum() * TRANSFER_ROWS[i]
        measured.append(i)
    unknown = [i for i in range(len(TRANSFER_SOURCES)) if i not in measured]
    residual = TRANSFER_COLS - matrix[measured].sum(axis=0)
    sub_rows = TRANSFER_ROWS[unknown]
    sub = np.asarray([TRANSFER_PRIOR[TRANSFER_SOURCES[i]] for i in unknown], dtype=float)
    sub = sub / sub.sum(axis=1, keepdims=True) * sub_rows[:, None]
    for _ in range(10_000):
        sub *= (residual / sub.sum(axis=0))[None, :]
        sub *= (sub_rows / sub.sum(axis=1))[:, None]
        if np.max(np.abs(sub.sum(axis=0) - residual)) < 1e-10:
            break
    matrix[unknown] = sub
    pool_points = float(TRANSFER_ROWS[measured].sum())
    pool = matrix[measured].sum(axis=0)
    lula_gain = float(TRANSFER_COLS[0] - TRANSFER_ROWS[0])
    flavio_gain = float(TRANSFER_COLS[1] - TRANSFER_ROWS[1])
    return {
        "sources": TRANSFER_SOURCES,
        "destinations": ["Lula", "Flávio", "B/N", "NS"],
        "matrix": matrix.round(3).tolist(),
        "row_targets": TRANSFER_ROWS.tolist(),
        "column_targets": TRANSFER_COLS.tolist(),
        "measured_rows": sorted(measured),
        "inferred_rows": unknown,
        "measured_pool": {
            "points": round(pool_points, 3),
            "destinations_points": pool.round(3).tolist(),
            "destinations_pct": (100 * pool / pool.sum()).round(3).tolist(),
            "ratio_flavio_lula": round(float(pool[1] / pool[0]), 3),
            "approx_unweighted_n": round(INTERVIEWS_REPORT * pool_points / 100),
        },
        "consolidation": {"lula_gain": lula_gain, "flavio_gain": flavio_gain, "ratio_flavio_lula": round(flavio_gain / lula_gain, 3)},
        "method": "Cinco linhas são medições da p. 52. As quatro linhas ausentes são fechadas por IPF/RAS contra prior ideológica explícita.",
    }


def _joint_from_odds_ratio(p: float, q: float, odds_ratio: float) -> float:
    """Return P(A and B) from two Bernoulli margins and an odds ratio."""
    lower, upper = max(0.0, p + q - 1), min(p, q)
    if math.isclose(odds_ratio, 1.0):
        return p * q
    a = odds_ratio - 1
    b = (1 - odds_ratio) * (p + q) - 1
    c = odds_ratio * p * q
    roots = np.roots([a, b, c])
    valid = [float(root.real) for root in roots if abs(root.imag) < 1e-10 and lower - 1e-10 <= root.real <= upper + 1e-10]
    if len(valid) != 1:
        raise ValueError("Odds ratio does not yield a unique feasible joint probability")
    return valid[0]


def useful_vote_sensitivity() -> dict:
    """Separate migration, vote potential and their unidentified intersection.

    Page 52 measures the hypothetical runoff destination. Page 33 measures
    willingness to change the first-round choice. Nexus does not publish their
    joint distribution. The point model uses maximum entropy, equivalent to
    conditional independence within each current candidate. NS/NR on page 52
    is imputed in the Lula/Flávio ratio for that origin; blank/null is preserved.
    Fréchet bounds and an odds-ratio sensitivity expose the model dependence.
    """
    rows = []
    total_keys = [
        "potential",
        "migration_lula_printed",
        "migration_lula_normalized",
        "migration_printed",
        "migration_normalized",
        "max_entropy_lula",
        "max_entropy",
        "joint_lower",
        "joint_upper",
        "or_0_5",
        "or_2",
    ]
    totals = {key: 0.0 for key in total_keys}
    for source in USEFUL_VOTE_CANDIDATES:
        candidate = source["candidate"]
        base = source["first_round"]
        potential = source["can_change"] / 100
        migration_printed = source["runoff_flavio"] / 100
        published = np.asarray(TRANSFER_MEASURED[candidate], dtype=float)
        normalized = published / published.sum()
        lula, flavio, blank_null, no_answer = normalized
        decided_finalists = lula + flavio
        imputed_flavio = flavio + no_answer * flavio / decided_finalists
        imputed_lula = lula + no_answer * lula / decided_finalists
        lower = max(0.0, potential + imputed_flavio - 1)
        upper = min(potential, imputed_flavio)
        row = {
            **source,
            "migration_row_published": published.tolist(),
            "migration_row_sum": float(published.sum()),
            "runoff_flavio_normalized": 100 * flavio,
            "runoff_flavio_ns_imputed": 100 * imputed_flavio,
            "runoff_lula_normalized": 100 * lula,
            "runoff_lula_ns_imputed": 100 * imputed_lula,
            "blank_null_preserved": 100 * blank_null,
            "potential_points": base * potential,
            "migration_lula_printed_points": base * source["runoff_lula"] / 100,
            "migration_lula_normalized_points": base * lula,
            "migration_printed_points": base * migration_printed,
            "migration_normalized_points": base * flavio,
            "max_entropy_lula_points": base * potential * imputed_lula,
            "max_entropy_points": base * potential * imputed_flavio,
            "joint_lower_points": base * lower,
            "joint_upper_points": base * upper,
            "or_0_5_points": base * _joint_from_odds_ratio(potential, imputed_flavio, 0.5),
            "or_2_points": base * _joint_from_odds_ratio(potential, imputed_flavio, 2.0),
        }
        for key in total_keys:
            totals[key] += row[f"{key}_points"]
        rows.append({key: round(value, 3) if isinstance(value, float) else value for key, value in row.items()})
    totals = {key: round(value, 3) for key, value in totals.items()}
    baseline = TOPLINES["first"][1]
    scenarios = {
        "baseline_flavio": baseline,
        "baseline_lula": TOPLINES["first"][0],
        "full_migration_using_printed_cells": round(baseline + totals["migration_printed"], 3),
        "full_migration_lula_using_printed_cells": round(TOPLINES["first"][0] + totals["migration_lula_printed"], 3),
        "full_migration_after_row_normalization": round(baseline + totals["migration_normalized"], 3),
        "full_migration_lula_after_row_normalization": round(TOPLINES["first"][0] + totals["migration_lula_normalized"], 3),
        "all_potential_moves_to_flavio": round(baseline + totals["potential"], 3),
        "maximum_entropy_ns_imputed": round(baseline + totals["max_entropy"], 3),
        "maximum_entropy_lula_ns_imputed": round(TOPLINES["first"][0] + totals["max_entropy_lula"], 3),
        "odds_ratio_sensitivity_0_5_to_2": [round(baseline + totals["or_0_5"], 3), round(baseline + totals["or_2"], 3)],
        "partial_identification_range": [round(baseline + totals["joint_lower"], 3), round(baseline + totals["joint_upper"], 3)],
    }
    return {
        "rows": rows,
        "totals": totals,
        "scenarios": scenarios,
        "post_claim": {
            "claimed_gain": 6.22,
            "claimed_total": 43.22,
            "migration_arithmetic_verdict": "Não reproduzido: a página 26 dá 5 pontos a Caiado, não 3. Pelas células impressas, a migração integral soma 7,35 pontos e leva Flávio a 44,35.",
        },
        "model": {
            "estimand": "P(pode mudar no 1º turno e escolheria Flávio no 2º turno | candidato atual)",
            "point_assumption": "Máxima entropia: independência condicional entre abertura à mudança e destino no 2º turno, dentro de cada candidatura.",
            "missing_rule": "Imputa somente NS/NR da migração na proporção Lula/Flávio da própria origem; branco/nulo permanece não escolha.",
            "sensitivity": "Razão de chances entre abertura e destino Flávio de 0,5 a 2, mais limites agnósticos de Fréchet.",
            "warning": "Não é previsão nem intervalo de confiança. As bases não ponderadas dos subgrupos e o cruzamento individual não foram publicados.",
        },
        "interpretation": "Migração integral, potencial de mudança e interseção modelada são três objetos distintos. A interseção é a medida relevante para antecipação estratégica.",
    }


def margin_of_difference() -> dict:
    result = {}
    for ballot in ("first", "runoff"):
        p1, p2 = TOPLINES[ballot][0] / 100, TOPLINES[ballot][1] / 100
        gap = 100 * (p1 - p2)
        se = 100 * math.sqrt((p1 + p2 - (p1 - p2) ** 2) / INTERVIEWS_REPORT)
        moe = NormalDist().inv_cdf(0.975) * se
        result[ballot] = {
            "gap_pp": round(gap, 3),
            "se_srs_pp": round(se, 3),
            "moe95_gap_srs_pp": round(moe, 3),
            "interval95_srs": [round(gap - moe, 3), round(gap + moe, 3)],
            "srs_already_includes_zero": gap <= moe,
            "deff_to_erase_lead": round((gap / moe) ** 2, 3) if gap > moe else None,
            "warning": "SRS multinomial; não incorpora cotas, não resposta ou pesos não publicados.",
        }
    return result


def target_comparison(targets: dict[str, list[float]]) -> dict:
    result = {}
    for dimension in PROFILE:
        poll = np.asarray(PROFILE[dimension], dtype=float)
        poll = 100 * poll / poll.sum()
        target = np.asarray(targets[dimension], dtype=float)
        target = 100 * target / target.sum()
        result[dimension] = {
            "labels": LABELS[dimension],
            "published": poll.round(3).tolist(),
            "target": target.round(3).tolist(),
            "delta_target_minus_poll": (target - poll).round(3).tolist(),
            "weight_factor": (target / poll).round(4).tolist(),
            "total_variation_distance_pp": round(float(np.abs(target - poll).sum() / 2), 3),
        }
    return result


def omissions_summary() -> dict:
    fully_absent = [row for row in QUESTION_PUBLICATION if row["status"] == "não publicada"]
    partial = [row for row in QUESTION_PUBLICATION if row["status"].startswith("só ") or "sem fórmula" in row["status"]]
    return {
        "fully_absent": len(fully_absent),
        "partial_or_non_reproducible": len(partial),
        "fully_absent_items": [row["item"] for row in fully_absent],
        "partial_items": [row["item"] for row in partial],
    }


def build() -> dict:
    targets = tse_targets()
    pnad = income_target()
    targets["income"] = pnad["distribution"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case": {
            "registration": "BR-09028/2026",
            "field": "21–23/08/2026",
            "disclosure": "24/08/2026",
            "interviews_report": INTERVIEWS_REPORT,
            "interviews_filed": INTERVIEWS_FILED,
            "mode": "CATI/RDD com encerramento por cotas",
            "contractor": "Banco BTG Pactual S.A.",
            "value_brl": 164888.89,
        },
        "documents": documents(),
        "toplines": TOPLINES,
        "published_profile": PROFILE,
        "benchmarks": {
            "targets": targets,
            "pnad_income": pnad,
            "tse_source": "TSE Perfil do Eleitorado, competência junho/2026, Brasil sem exterior",
            "age_split": "A faixa TSE 40–44 foi repartida linearmente: 1/5 em 25–40 e 4/5 em 41–59.",
        },
        "target_comparison": target_comparison(targets),
        "reweighting": all_reweighting(targets),
        "margin_of_difference": margin_of_difference(),
        "transfer": transfer_ipf(),
        "useful_vote": useful_vote_sensitivity(),
        "strategic_reservoirs": STRATEGIC_RESERVOIRS,
        "question_publication": QUESTION_PUBLICATION,
        "omissions": omissions_summary(),
        "testimony_checks": TESTIMONY_CHECKS,
        "method_limits": [
            "Sem microdados, pesos e paradata, a análise é sensibilidade ecológica, não recontagem.",
            "As células do relatório são arredondadas; a simulação de arredondamento não cobre efeito de desenho.",
            "O depoimento é um relato de uma entrevista, não uma amostra e não uma prova de intenção institucional.",
            "A matriz de transferência descreve agregados compatíveis com margens publicadas, não trajetórias individuais.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(args.output), "bytes": args.output.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
