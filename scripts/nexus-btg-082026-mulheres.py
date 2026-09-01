#!/usr/bin/env python3
"""Retrato socioeconômico das mulheres brasileiras para o dossiê BTG/Nexus 03/08/2026.

Leitura em streaming de duas bases já publicadas em data/outputs/brasil.sqlite:

* ``base_anual_visita1_labeled_npv`` (PNAD Contínua anual 2025, 1ª visita, peso
  V1032 e 200 réplicas) para domicílio, renda domiciliar, Bolsa Família,
  pirâmide etária e recorte regional. É a mesma base que o dossiê usa.
* ``base_labeled_npv`` (PNAD Contínua trimestral 2026 T1, peso V1028 e 200
  réplicas) para o mercado de trabalho, porque o rendimento individual do
  trabalho (VD4020) e a escolaridade detalhada (VD3004, VD3005) só existem lá.

Valores monetários estão deflacionados para abril de 2026 (sufixo _202604) ou
expressos em salários mínimos (sufixo _mw), como no resto do repositório.

A PNAD não mede voto, religião nem persuasibilidade. Tudo aqui é descritivo.

Uso: python3 scripts/nexus-btg-082026-mulheres.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/outputs/brasil.sqlite"
TSE_DB = ROOT / "data/outputs/tse_eleitorado_perfil.sqlite"
OUTPUT = ROOT / "docs/assets/nexus_btg_082026_1_mulheres.json"

ANNUAL = "base_anual_visita1_labeled_npv"
QUARTER = "base_labeled_npv"
CHUNK = 20000
REPLICATES = 200
LEVEL = 0.95
WEEKS_PER_MONTH = 4.345

WARNING = (
    "A PNAD Contínua não mede intenção de voto, religião, aprovação de governo "
    "nem persuasibilidade. Todo número deste arquivo é descritivo: descreve o "
    "universo social em que a pesquisa foi a campo, nunca a preferência "
    "eleitoral de quem vive nele. Aproximar um recorte social de um resultado "
    "publicado é contexto, não é causa."
)

SEXES = {"mulheres": 2, "homens": 1}
# Faixas etárias que a Nexus realmente usa, conferidas no relatório de 03/08/2026,
# páginas 11, 28, 52 e 113: 16 a 24, 25 a 40, 41 a 59, 60 ou mais.
AGE_BANDS = ("16-24", "25-40", "41-59", "60+")
# Faixas alternativas, usadas por outros institutos e pelo restante do dossiê.
AGE_BANDS_ALT = ("16-24", "25-44", "45-59", "60+")
INCOME_BANDS = ("Até 1 SM", "1-2 SM", "2-5 SM", "5+ SM")
EDUCATION_BANDS = ("Fundamental", "Médio", "Superior")
HOUR_BANDS = ("Até 14h", "15-39h", "40-44h", "45-48h", "49h ou mais")
REGIONS = ("Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste")
REGION_BY_DIGIT = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}
RACE_LABELS = {1: "Branca", 2: "Preta", 3: "Amarela", 4: "Parda", 5: "Indígena"}
ARRANGEMENTS = (
    "Com cônjuge, com menor",
    "Com cônjuge, sem menor",
    "Sem cônjuge, com menor",
    "Sem cônjuge, sem menor",
)

# Posição na ocupação (VD4009). Sem carteira é o núcleo estrito da informalidade;
# conta própria e trabalhador familiar auxiliar entram na definição ampla.
NO_CONTRACT_POSITIONS = (2, 4, 6)
INFORMAL_POSITIONS = (2, 4, 6, 9, 10)
DOMESTIC_POSITIONS = (3, 4)
PUBLIC_POSITIONS = (5, 6, 7)

# Percentuais publicados pela Nexus/BTG na rodada de 3 de agosto de 2026,
# transcritos do relatório com a página ao lado. Entram aqui só como referência
# de leitura: são resultado de pesquisa, não de PNAD.
NEXUS = {
    "first_labels": [
        "Lula",
        "Flávio",
        "Caiado",
        "Renan",
        "Zema",
        "Outros",
        "B/N",
        "NS",
    ],
    "runoff_labels": ["Lula", "adversário", "B/N", "NS"],
    "first": {
        "total": [41, 37, 5, 4, 3, 3, 4, 3],
        "mulheres": [48, 29, 4, 1, 2, 6, 6, 4],
        "homens": [34, 45, 5, 7, 4, 1, 2, 2],
        "pagina": 28,
    },
    "runoff_cenarios": {
        "Lula x Flávio Bolsonaro": {
            "total": [46, 45, 8, 2],
            "mulheres": [54, 37, 7, 3],
            "homens": [37, 53, 9, 1],
            "pagina": 52,
        },
        "Lula x Romeu Zema": {
            "total": [46, 40, 10, 3],
            "mulheres": [54, 31, 11, 4],
            "homens": [37, 51, 9, 3],
            "pagina": 54,
        },
        "Lula x Ronaldo Caiado": {
            "total": [46, 42, 10, 3],
            "mulheres": [54, 32, 11, 3],
            "homens": [37, 53, 8, 3],
            "pagina": 56,
        },
        "Lula x Renan Santos": {
            "total": [47, 37, 13, 3],
            "mulheres": [54, 29, 13, 3],
            "homens": [38, 45, 14, 3],
            "pagina": 58,
        },
    },
    "aprovacao_do_governo": {
        "labels": ["Aprova", "Desaprova", "NS/NR"],
        "total": [47, 48, 5],
        "mulheres": [54, 39, 7],
        "homens": [39, 58, 3],
        "pagina": 85,
    },
    "avaliacao_do_governo": {
        "labels": ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo", "NS/NR"],
        "total": [16, 21, 18, 8, 35, 2],
        "mulheres": [19, 23, 21, 7, 28, 2],
        "homens": [13, 19, 15, 9, 42, 1],
        "pagina": 79,
    },
    "potencial_de_voto": {
        "mulheres": {"Lula": 59, "Flávio": 39},
        "homens": {"Lula": 39, "Flávio": 56},
        "pagina": 69,
    },
    "rejeicao": {
        "mulheres": {"Lula": 40, "Flávio": 56},
        "homens": {"Lula": 59, "Flávio": 42},
        "pagina": 70,
    },
    "income_labels": ["Até 1 SM", "1-2 SM", "2-5 SM", "5+ SM"],
    "income_first_lula_flavio": [[54, 26], [37, 44], [38, 39], [39, 38]],
    "income_runoff_lula_flavio": [[58, 32], [43, 49], [42, 47], [43, 50]],
    "perfil_da_amostra": {
        "sexo": {"Feminino": 53, "Masculino": 47},
        "idade": {"16 a 24": 12, "25 a 40": 30, "41 a 59": 34, "60 ou mais": 24},
        "escolaridade": {"Fundamental": 36, "Médio": 41, "Superior": 23},
        "renda_familiar": {"Até 1 SM": 22, "1 a 2 SM": 18, "2 a 5 SM": 40, "5+ SM": 21},
        "pea": {"Formal": 43, "Informal": 17, "Desocupados": 5, "Não PEA": 35},
        "regiao": {"Norte/Centro-Oeste": 16, "Nordeste": 28, "Sudeste": 42, "Sul": 14},
        "municipio": {"Capital": 27, "RM": 12, "Interior": 60},
        "religiao": {
            "Católicos": 48,
            "Evangélicos": 30,
            "Outras religiões": 9,
            "Sem religião": 12,
        },
        "pagina": 113,
    },
    "margem_por_perfil_pp": {"Feminino": 3, "Masculino": 3, "pagina": 114},
    "entrevistas": 2002,
    "referencia_declarada": (
        "O relatório declara, na página 4, que a amostra foi construída com a "
        "PNAD Contínua, suplemento anual acumulado da 1ª visita de 2024, e com "
        "dados do Tribunal Superior Eleitoral. A PNAD anual de 2025 já estava "
        "publicada quando esta rodada foi a campo."
    ),
    "nota": (
        "Sexo é o único recorte por sexo divulgado. Não há cruzamento publicado "
        "de sexo com renda, idade, escolaridade, religião, PEA ou região, e é "
        "justamente nesses cruzamentos que a diferença entre mulheres e homens "
        "poderia ser explicada. As páginas 69 e 70 vêm em blocos de duas colunas "
        "no PDF; a ordem entre Lula e Flávio foi conferida contra os recortes de "
        "sexo e de renda das páginas 28 e 52."
    ),
}


class Sums:
    """Somas ponderadas por chave, com o peso base e as 200 réplicas ao lado."""

    def __init__(self) -> None:
        self.data: dict[tuple, np.ndarray] = {}

    def add(self, key: tuple, block: np.ndarray) -> None:
        current = self.data.get(key)
        self.data[key] = block if current is None else current + block

    def get(self, key: tuple) -> np.ndarray:
        return self.data.get(key, np.zeros(REPLICATES + 1))


def to_float(values) -> np.ndarray:
    """Converte coluna do SQLite em float, tratando NULL e string vazia."""
    return np.array(
        [np.nan if value in (None, "") else float(value) for value in values],
        dtype=np.float64,
    )


def to_int(values) -> np.ndarray:
    """Converte coluna do SQLite em inteiro, com -1 para ausente."""
    return np.array(
        [-1 if value in (None, "") else int(value) for value in values],
        dtype=np.int64,
    )


def wsum(weights: np.ndarray, mask: np.ndarray, values: np.ndarray | None = None):
    """Soma o peso, e cada réplica, das linhas marcadas; opcionalmente ponderado.

    A redução usa ``einsum`` e não o produto de matrizes: o BLAS Accelerate do
    macOS levanta sinalizadores de ponto flutuante espúrios em ``@``, e silenciar
    o aviso esconderia também um estouro real.
    """
    factor = mask.astype(np.float64)
    if values is not None:
        factor = factor * np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    return np.einsum("i,ij->j", factor, weights)


def replicate_ci(theta: float, values: np.ndarray, digits: int, key: str) -> dict:
    variance = float(np.sum((values - theta) ** 2) / (len(values) - 1))
    moe = NormalDist().inv_cdf(0.5 + LEVEL / 2) * math.sqrt(variance)
    return {
        key: round(theta, digits),
        "moe": round(moe, digits),
        "low": round(theta - moe, digits),
        "high": round(theta + moe, digits),
    }


def ratio_ci(num, den, scale: float = 100.0, digits: int = 4, key: str = "pct"):
    """Razão num/den vezes a escala, com margem de erro pelas réplicas."""
    if not den[0]:
        return None
    theta = scale * num[0] / den[0]
    mask = den[1:] != 0
    return replicate_ci(theta, scale * num[1:][mask] / den[1:][mask], digits, key)


def gap_ci(num_a, den_a, num_b, den_b, digits: int = 4, key: str = "razao"):
    """Razão entre duas médias, (a/b), com incerteza pelas mesmas réplicas."""
    if not den_a[0] or not den_b[0] or not num_b[0]:
        return None
    theta = (num_a[0] / den_a[0]) / (num_b[0] / den_b[0])
    mask = (den_a[1:] != 0) & (den_b[1:] != 0) & (num_b[1:] != 0)
    values = (num_a[1:][mask] / den_a[1:][mask]) / (num_b[1:][mask] / den_b[1:][mask])
    return replicate_ci(theta, values, digits, key)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if not len(values):
        return float("nan")
    order = np.argsort(values, kind="stable")
    ordered, cumulative = values[order], np.cumsum(weights[order])
    if not cumulative[-1]:
        return float("nan")
    return float(ordered[int(np.searchsorted(cumulative, cumulative[-1] / 2))])


def age_band_masks(age: np.ndarray) -> dict[str, np.ndarray]:
    """Faixas da Nexus: 16 a 24, 25 a 40, 41 a 59, 60 ou mais."""
    return {
        "16-24": (age >= 16) & (age <= 24),
        "25-40": (age >= 25) & (age <= 40),
        "41-59": (age >= 41) & (age <= 59),
        "60+": age >= 60,
    }


def age_band_masks_alt(age: np.ndarray) -> dict[str, np.ndarray]:
    """Faixas alternativas, para quem compara com outros institutos."""
    return {
        "16-24": (age >= 16) & (age <= 24),
        "25-44": (age >= 25) & (age <= 44),
        "45-59": (age >= 45) & (age <= 59),
        "60+": age >= 60,
    }


def band_of_year(year: int) -> str:
    return (
        "16-24"
        if year <= 24
        else "25-40" if year <= 40 else "41-59" if year <= 59 else "60+"
    )


def tse_age_shares(category: str) -> list[tuple[str, float]]:
    """Reparte uma faixa etária bruta do TSE nas faixas usadas pela Nexus.

    As faixas do TSE são quinquenais e a da Nexus corta dentro de 40 a 44 anos.
    A repartição supõe distribuição uniforme dentro da faixa quinquenal, o que
    coloca um quinto de 40 a 44 em 25-40 e quatro quintos em 41-59.
    """
    numbers = [int(value) for value in re.findall(r"\d+", category)]
    if not numbers:
        return []
    start = numbers[0]
    end = numbers[1] if len(numbers) > 1 else (120 if "mais" in category else start)
    years = range(max(start, 16), end + 1)
    counts = Counter(band_of_year(year) for year in years)
    total = sum(counts.values())
    return [(band, value / total) for band, value in counts.items()] if total else []


def tse_electorate_by_age() -> dict:
    """Eleitorado 16+ residente no Brasil, nas faixas etárias da Nexus."""
    if not TSE_DB.exists():
        return {}
    query = (
        "SELECT category, qt_eleitores FROM summary "
        "WHERE dimension = 'idade_raw' AND universe = 'Brasil sem exterior'"
    )
    totals: dict[str, float] = {band: 0.0 for band in AGE_BANDS}
    with sqlite3.connect(f"file:{TSE_DB}?mode=ro", uri=True) as connection:
        for category, voters in connection.execute(query):
            for band, share in tse_age_shares(category):
                totals[band] += share * voters
    grand = sum(totals.values())
    return {
        "eleitores_16_mais": round(grand),
        "distribuicao_pct": {
            band: round(100 * value / grand, 3) for band, value in totals.items()
        },
        "fonte": "TSE, perfil do eleitorado atual, gerado em 01/07/2026",
        "nota": (
            "Faixas quinquenais do TSE repartidas com hipótese de distribuição "
            "uniforme dentro da faixa, porque o corte da Nexus cai no meio do "
            "grupo de 40 a 44 anos. Exclui eleitores no exterior e menores de 16."
        ),
    }


def income_band_masks(value: np.ndarray) -> dict[str, np.ndarray]:
    known = ~np.isnan(value)
    return {
        "Até 1 SM": known & (value <= 1),
        "1-2 SM": known & (value > 1) & (value <= 2),
        "2-5 SM": known & (value > 2) & (value <= 5),
        "5+ SM": known & (value > 5),
    }


def education_masks(level: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "Fundamental": (level >= 1) & (level <= 3),
        "Médio": (level >= 4) & (level <= 5),
        "Superior": level >= 6,
    }


def chunks(connection: sqlite3.Connection, sql: str, n_dims: int):
    """Percorre a consulta em blocos: colunas de dimensão e matriz de pesos."""
    cursor = connection.execute(sql)
    while True:
        rows = cursor.fetchmany(CHUNK)
        if not rows:
            return
        columns = list(zip(*(row[:n_dims] for row in rows)))
        weights = np.array([row[n_dims:] for row in rows], dtype=np.float64)
        yield columns, weights


def household_flags(connection: sqlite3.Connection) -> dict[str, tuple]:
    """Um registro por domicílio: menor de 18, cônjuge, Bolsa Família, sexo do chefe."""
    query = f"""
        SELECT dom_id,
               MAX(CASE WHEN V2009__idade_na_data_de_referencia < 18 THEN 1 ELSE 0 END),
               MAX(CASE WHEN V2005__condicao_no_domicilio IN (2, 3) THEN 1 ELSE 0 END),
               MAX(CASE WHEN V5002A__recebeu_bolsa_familia = 1 THEN 1 ELSE 0 END),
               MAX(CASE WHEN V2005__condicao_no_domicilio = 1
                        THEN V2007__sexo ELSE 0 END)
        FROM "{ANNUAL}" GROUP BY dom_id
    """
    return {row[0]: tuple(row[1:]) for row in connection.execute(query)}


ANNUAL_COLUMNS = [
    "V2007__sexo",
    "V2009__idade_na_data_de_referencia",
    "V2005__condicao_no_domicilio",
    "VD5001__rend_efetivo_domiciliar_mw",
    "VD5002__rend_efetivo_domiciliar_per_capita_202604",
    "UF__unidade_da_federacao",
    "VD4002__condicao_de_ocupacao",
    "V5002A__recebeu_bolsa_familia",
    "V2010__cor_ou_raca",
    "VD2003__numero_de_componentes_do_domic",
    "dom_id",
]

QUARTER_COLUMNS = [
    "V2007__sexo",
    "V2009__idade_na_data_de_referencia",
    "VD3004__nivel_de_instrucao_mais_elevado_alcancado_5_anos_ou_mais_de_idade",
    "VD3005__anos_de_estudo_5_anos_ou_mais_de_idade_para_fundamental_de_9_anos",
    "VD4020__rendim_efetivo_qq_trabalho_202604",
    "VD4013__faixa_hrs_habituais_em_todos_trab",
    "V4039__hrs_habituais_no_trab_princ",
    "V4009__quantos_trabalhos_tinhana_semana",
    "VD4001__condicao_em_relacao_forca_d_trab",
    "VD4002__condicao_de_ocupacao",
    "VD4009__posicao_na_ocupacao_trab_princ",
]


def scan_annual(connection: sqlite3.Connection) -> tuple[Sums, dict]:
    """Passe único sobre a anual 2025: domicílio, renda domiciliar, região."""
    flags = household_flags(connection)
    replicas = [f"V1032{i:03d}__peso_replicado_{i}" for i in range(1, REPLICATES + 1)]
    fields = ",".join(f'"{name}"' for name in ANNUAL_COLUMNS)
    sql = (
        f"SELECT {fields}, V1032__peso_com_calibracao, "
        f'{",".join(replicas)} FROM "{ANNUAL}"'
    )
    acc = Sums()
    medians: dict[str, list] = {}
    for columns, block in chunks(connection, sql, len(ANNUAL_COLUMNS)):
        sex = to_int(columns[0])
        age = to_int(columns[1])
        position = to_int(columns[2])
        household_sm = to_float(columns[3])
        per_capita = to_float(columns[4])
        uf = to_int(columns[5])
        occupied = to_int(columns[6])
        bolsa_person = to_int(columns[7])
        race = to_int(columns[8])
        residents = to_float(columns[9])
        marks = np.array(
            [flags.get(key, (0, 0, 0, 0)) for key in columns[10]], dtype=np.int64
        )
        minor, spouse, bolsa_home, head_sex = (marks[:, i] for i in range(4))
        region = np.where(uf > 0, uf // 10, -1)
        adult = age >= 16
        known = ~np.isnan(per_capita)
        bands = income_band_masks(household_sm)
        ages = age_band_masks(age)
        ages_alt = age_band_masks_alt(age)

        acc.add(("adults",), wsum(block, adult))
        acc.add(("minors",), wsum(block, age < 18))
        acc.add(
            ("minors_female_lone",),
            wsum(block, (age < 18) & (head_sex == 2) & (spouse == 0)),
        )
        for band, mask in bands.items():
            acc.add(("band_all", band), wsum(block, adult & mask))
        for tag, code in SEXES.items():
            same = sex == code
            base = adult & same
            acc.add(("base", tag), wsum(block, base))
            acc.add(("pc_sum", tag), wsum(block, base & known, per_capita))
            acc.add(("pc_n", tag), wsum(block, base & known))
            acc.add(("sm_sum", tag), wsum(block, base, household_sm))
            acc.add(("bolsa_home", tag), wsum(block, base & (bolsa_home == 1)))
            acc.add(("bolsa_person", tag), wsum(block, base & (bolsa_person == 1)))
            for band, mask in bands.items():
                acc.add(("band", tag, band), wsum(block, base & mask))
            for band, mask in ages.items():
                acc.add(("age", tag, band), wsum(block, base & mask))
            for band, mask in ages_alt.items():
                acc.add(("age_alt", tag, band), wsum(block, base & mask))
            for value, label in RACE_LABELS.items():
                acc.add(("race", tag, label), wsum(block, base & (race == value)))
            for digit, label in REGION_BY_DIGIT.items():
                here = base & (region == digit)
                acc.add(("region", tag, label), wsum(block, here))
                acc.add(
                    ("reg_pc_sum", tag, label), wsum(block, here & known, per_capita)
                )
                acc.add(("reg_pc_n", tag, label), wsum(block, here & known))
                acc.add(("reg_low", tag, label), wsum(block, here & bands["Até 1 SM"]))
                acc.add(
                    ("reg_bolsa", tag, label), wsum(block, here & (bolsa_home == 1))
                )
                acc.add(("reg_occ", tag, label), wsum(block, here & (occupied == 1)))
            head = same & (position == 1)
            acc.add(("head", tag), wsum(block, head))
            layout = {
                "Com cônjuge, com menor": head & (spouse == 1) & (minor == 1),
                "Com cônjuge, sem menor": head & (spouse == 1) & (minor == 0),
                "Sem cônjuge, com menor": head & (spouse == 0) & (minor == 1),
                "Sem cônjuge, sem menor": head & (spouse == 0) & (minor == 0),
            }
            for label, mask in layout.items():
                acc.add(("hh", tag, label), wsum(block, mask))
                acc.add(
                    ("hh_pc_sum", tag, label), wsum(block, mask & known, per_capita)
                )
                acc.add(("hh_pc_n", tag, label), wsum(block, mask & known))
                acc.add(("hh_size", tag, label), wsum(block, mask, residents))
                acc.add(("hh_bolsa", tag, label), wsum(block, mask & (bolsa_home == 1)))
            keep = base & known
            medians.setdefault(f"pc_{tag}", []).append(per_capita[keep])
            medians.setdefault(f"pcw_{tag}", []).append(block[keep, 0])
    acc.add(("households",), sum(acc.get(("head", tag)) for tag in SEXES))
    return acc, medians


def scan_quarter(connection: sqlite3.Connection) -> tuple[Sums, dict]:
    """Passe único sobre a trimestral 2026 T1: trabalho, renda do trabalho, escola."""
    replicas = [f"V1028{i:03d}__peso_replicado_{i}" for i in range(1, REPLICATES + 1)]
    fields = ",".join(f'"{name}"' for name in QUARTER_COLUMNS)
    sql = (
        f"SELECT {fields}, V1028__peso_com_calibracao, {','.join(replicas)} "
        f'FROM "{QUARTER}" WHERE V2009__idade_na_data_de_referencia >= 16'
    )
    acc = Sums()
    medians: dict[str, list] = {}
    for columns, block in chunks(connection, sql, len(QUARTER_COLUMNS)):
        sex = to_int(columns[0])
        age = to_int(columns[1])
        level = to_int(columns[2])
        years = to_float(columns[3])
        income = to_float(columns[4])
        hour_band = to_int(columns[5])
        hours = to_float(columns[6])
        jobs = to_int(columns[7])
        force = to_int(columns[8])
        occupied = to_int(columns[9])
        position = to_int(columns[10])
        ages = age_band_masks(age)
        schooling = education_masks(level)
        earning = (occupied == 1) & ~np.isnan(income) & (income > 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            hourly = income / (WEEKS_PER_MONTH * np.where(hours > 0, hours, np.nan))
        for tag, code in SEXES.items():
            same = sex == code
            work = same & (occupied == 1)
            acc.add(("base", tag), wsum(block, same))
            acc.add(("in_force", tag), wsum(block, same & (force == 1)))
            acc.add(("working_age", tag), wsum(block, same & (force >= 1)))
            acc.add(("occupied", tag), wsum(block, work))
            acc.add(("unemployed", tag), wsum(block, same & (occupied == 2)))
            acc.add(
                ("informal", tag),
                wsum(block, work & np.isin(position, INFORMAL_POSITIONS)),
            )
            acc.add(
                ("no_contract", tag),
                wsum(block, work & np.isin(position, NO_CONTRACT_POSITIONS)),
            )
            acc.add(("family_worker", tag), wsum(block, work & (position == 10)))
            acc.add(("employer", tag), wsum(block, work & (position == 8)))
            acc.add(
                ("domestic", tag),
                wsum(block, work & np.isin(position, DOMESTIC_POSITIONS)),
            )
            acc.add(("domestic_informal", tag), wsum(block, work & (position == 4)))
            acc.add(
                ("public", tag), wsum(block, work & np.isin(position, PUBLIC_POSITIONS))
            )
            acc.add(("formal_private", tag), wsum(block, work & (position == 1)))
            acc.add(("own_account", tag), wsum(block, work & (position == 9)))
            acc.add(("school_n", tag), wsum(block, same & (level >= 1)))
            acc.add(("degree", tag), wsum(block, same & (level == 7)))
            acc.add(("years_sum", tag), wsum(block, same & ~np.isnan(years), years))
            acc.add(("years_n", tag), wsum(block, same & ~np.isnan(years)))
            for label, mask in schooling.items():
                acc.add(("school", tag, label), wsum(block, same & mask))
            for band, mask in ages.items():
                acc.add(
                    ("school_age_n", tag, band), wsum(block, same & mask & (level >= 1))
                )
                acc.add(
                    ("degree_age", tag, band), wsum(block, same & mask & (level == 7))
                )
            earn = same & earning
            acc.add(("earn_n", tag), wsum(block, earn))
            acc.add(("earn_sum", tag), wsum(block, earn, income))
            for index, band in enumerate(HOUR_BANDS, start=1):
                here = earn & (hour_band == index)
                acc.add(("hour_n", tag, band), wsum(block, here))
                acc.add(("hour_sum", tag, band), wsum(block, here, income))
            for label, mask in schooling.items():
                here = earn & mask
                acc.add(("earn_school_n", tag, label), wsum(block, here))
                acc.add(("earn_school_sum", tag, label), wsum(block, here, income))
            single = earn & (jobs == 1) & ~np.isnan(hourly)
            acc.add(("hourly_n", tag), wsum(block, single))
            acc.add(("hourly_sum", tag), wsum(block, single, hourly))
            worked = earn & (hours > 0)
            acc.add(("hours_n", tag), wsum(block, worked))
            acc.add(("hours_sum", tag), wsum(block, worked, hours))
            medians.setdefault(f"income_{tag}", []).append(income[earn])
            medians.setdefault(f"incomew_{tag}", []).append(block[earn, 0])
            told = same & ~np.isnan(years)
            medians.setdefault(f"years_{tag}", []).append(years[told])
            medians.setdefault(f"yearsw_{tag}", []).append(block[told, 0])
    return acc, medians


def stack(medians: dict, key: str) -> np.ndarray:
    return np.concatenate(medians.get(key) or [np.zeros(0)])


def block_income_gap(acc: Sums, medians: dict) -> dict:
    rows = {}
    for tag in SEXES:
        count = acc.get(("earn_n", tag))
        rows[tag] = {
            "media_brl": ratio_ci(acc.get(("earn_sum", tag)), count, 1.0, 2, "valor"),
            "mediana_brl": round(
                weighted_median(
                    stack(medians, f"income_{tag}"), stack(medians, f"incomew_{tag}")
                ),
                2,
            ),
            "media_horas_trabalho_principal": ratio_ci(
                acc.get(("hours_sum", tag)), acc.get(("hours_n", tag)), 1.0, 2, "valor"
            ),
            "media_brl_por_hora": ratio_ci(
                acc.get(("hourly_sum", tag)),
                acc.get(("hourly_n", tag)),
                1.0,
                2,
                "valor",
            ),
            "pessoas": round(float(count[0])),
        }
    by_hours = {}
    for band in HOUR_BANDS:
        by_hours[band] = {
            **{
                tag: ratio_ci(
                    acc.get(("hour_sum", tag, band)),
                    acc.get(("hour_n", tag, band)),
                    1.0,
                    2,
                    "valor",
                )
                for tag in SEXES
            },
            "razao_mulher_homem": gap_ci(
                acc.get(("hour_sum", "mulheres", band)),
                acc.get(("hour_n", "mulheres", band)),
                acc.get(("hour_sum", "homens", band)),
                acc.get(("hour_n", "homens", band)),
            ),
        }
    by_school = {}
    for label in EDUCATION_BANDS:
        by_school[label] = {
            **{
                tag: ratio_ci(
                    acc.get(("earn_school_sum", tag, label)),
                    acc.get(("earn_school_n", tag, label)),
                    1.0,
                    2,
                    "valor",
                )
                for tag in SEXES
            },
            "razao_mulher_homem": gap_ci(
                acc.get(("earn_school_sum", "mulheres", label)),
                acc.get(("earn_school_n", "mulheres", label)),
                acc.get(("earn_school_sum", "homens", label)),
                acc.get(("earn_school_n", "homens", label)),
            ),
            "composicao_pct": {
                tag: ratio_ci(
                    acc.get(("earn_school_n", tag, label)), acc.get(("earn_n", tag))
                )
                for tag in SEXES
            },
        }
    return {
        "rotulo": "Rendimento efetivo de todos os trabalhos, por sexo",
        "universo": (
            "Pessoas de 16 anos ou mais, ocupadas e com rendimento de trabalho "
            "declarado maior que zero. PNAD Contínua trimestral, 1º trimestre de "
            "2026. Valores a preços de abril de 2026 pelo IPCA."
        ),
        "por_sexo": rows,
        "razao_media_mulher_homem": gap_ci(
            acc.get(("earn_sum", "mulheres")),
            acc.get(("earn_n", "mulheres")),
            acc.get(("earn_sum", "homens")),
            acc.get(("earn_n", "homens")),
        ),
        "razao_mediana_mulher_homem": round(
            rows["mulheres"]["mediana_brl"] / rows["homens"]["mediana_brl"], 4
        ),
        "razao_hora_mulher_homem": gap_ci(
            acc.get(("hourly_sum", "mulheres")),
            acc.get(("hourly_n", "mulheres")),
            acc.get(("hourly_sum", "homens")),
            acc.get(("hourly_n", "homens")),
        ),
        "por_faixa_de_horas": by_hours,
        "por_escolaridade": by_school,
        "limite": (
            "A razão por hora usa só quem tem um único trabalho, para que o "
            "rendimento de todos os trabalhos e as horas do trabalho principal "
            "descrevam a mesma jornada. A base não mede trabalho doméstico não "
            "remunerado, então a jornada total das mulheres está subestimada por "
            "construção. Nada aqui identifica discriminação: é diferença "
            "observada, não efeito causal isolado."
        ),
    }


def block_labour(acc: Sums) -> dict:
    rows = {}
    for tag in SEXES:
        base = acc.get(("working_age", tag))
        force = acc.get(("in_force", tag))
        work = acc.get(("occupied", tag))
        rows[tag] = {
            "taxa_de_participacao": ratio_ci(force, base),
            "nivel_de_ocupacao": ratio_ci(work, base),
            "taxa_de_desocupacao": ratio_ci(acc.get(("unemployed", tag)), force),
            "fora_da_forca_de_trabalho": ratio_ci(base - force, base),
            "sem_carteira_conta_propria_ou_familiar": ratio_ci(
                acc.get(("informal", tag)), work
            ),
            "sem_carteira_estrito": ratio_ci(acc.get(("no_contract", tag)), work),
            "empregado_privado_com_carteira": ratio_ci(
                acc.get(("formal_private", tag)), work
            ),
            "setor_publico_ou_militar": ratio_ci(acc.get(("public", tag)), work),
            "conta_propria": ratio_ci(acc.get(("own_account", tag)), work),
            "empregador": ratio_ci(acc.get(("employer", tag)), work),
            "trabalhador_familiar_auxiliar": ratio_ci(
                acc.get(("family_worker", tag)), work
            ),
            "trabalho_domestico": ratio_ci(acc.get(("domestic", tag)), work),
            "composicao_do_universo_adulto": {
                "denominador": "pessoas de 16 anos ou mais em idade de trabalhar",
                "ocupado_formal_amplo": ratio_ci(
                    work - acc.get(("informal", tag)), base
                ),
                "ocupado_informal_amplo": ratio_ci(acc.get(("informal", tag)), base),
                "ocupado_sem_carteira_estrito": ratio_ci(
                    acc.get(("no_contract", tag)), base
                ),
                "desocupado": ratio_ci(acc.get(("unemployed", tag)), base),
                "fora_da_forca": ratio_ci(base - force, base),
            },
            "pessoas_16_mais": round(float(acc.get(("base", tag))[0])),
            "ocupados": round(float(work[0])),
        }
    total = sum(acc.get(("domestic", tag)) for tag in SEXES)
    informal = sum(acc.get(("domestic_informal", tag)) for tag in SEXES)
    return {
        "rotulo": "Força de trabalho, ocupação e informalidade, por sexo",
        "universo": (
            "Pessoas de 16 anos ou mais. PNAD Contínua trimestral, 1º trimestre "
            "de 2026. Denominador da participação e do nível de ocupação: "
            "pessoas em idade de trabalhar com condição de força de trabalho "
            "conhecida."
        ),
        "por_sexo": rows,
        "trabalho_domestico": {
            "mulheres_no_total": ratio_ci(acc.get(("domestic", "mulheres")), total),
            "sem_carteira_no_total": ratio_ci(informal, total),
            "pessoas": round(float(total[0])),
        },
        "perfil_pea_da_nexus_pct": NEXUS["perfil_da_amostra"]["pea"],
        "limite": (
            "Informalidade tem duas leituras aqui. A estrita é só quem não tem "
            "carteira assinada (posições 2, 4 e 6 da VD4009). A ampla soma conta "
            "própria e trabalhador familiar auxiliar. A base extraída não traz o "
            "CNPJ do negócio, então na leitura ampla toda conta própria entra "
            "como informal e a taxa fica acima da definição oficial do IBGE. A "
            "comparação entre sexos, que é o objeto aqui, sobrevive às duas. O "
            "perfil de PEA da Nexus é autodeclarado pelo entrevistado e não "
            "reproduz nenhuma das duas definições: serve para comparar ordem de "
            "grandeza, não para calibrar."
        ),
    }


def block_schooling(acc: Sums, medians: dict) -> dict:
    rows = {}
    for tag in SEXES:
        known = acc.get(("school_n", tag))
        rows[tag] = {
            "distribuicao": {
                label: ratio_ci(acc.get(("school", tag, label)), known)
                for label in EDUCATION_BANDS
            },
            "superior_completo": ratio_ci(acc.get(("degree", tag)), known),
            "media_anos_de_estudo": ratio_ci(
                acc.get(("years_sum", tag)), acc.get(("years_n", tag)), 1.0, 2, "valor"
            ),
            "mediana_anos_de_estudo": weighted_median(
                stack(medians, f"years_{tag}"), stack(medians, f"yearsw_{tag}")
            ),
        }
    by_age = {}
    for band in AGE_BANDS:
        pair = {
            tag: ratio_ci(
                acc.get(("degree_age", tag, band)), acc.get(("school_age_n", tag, band))
            )
            for tag in SEXES
        }
        by_age[band] = {
            **pair,
            "diferenca_pp": round(pair["mulheres"]["pct"] - pair["homens"]["pct"], 4),
        }
    return {
        "rotulo": "Escolaridade por sexo",
        "universo": (
            "Pessoas de 16 anos ou mais com nível de instrução conhecido. PNAD "
            "Contínua trimestral, 1º trimestre de 2026. Os três grupos seguem a "
            "convenção da casa: fundamental (VD3004 1 a 3), médio (4 e 5) e "
            "superior (6 e 7), comparáveis à quota de escolaridade da Nexus."
        ),
        "por_sexo": rows,
        "superior_completo_diferenca_pp": round(
            rows["mulheres"]["superior_completo"]["pct"]
            - rows["homens"]["superior_completo"]["pct"],
            4,
        ),
        "superior_completo_por_idade": by_age,
        "limite": (
            "A mediana de anos de estudo é ponto, sem intervalo: mediana "
            "ponderada não herda intervalo das réplicas neste cálculo. "
            "Escolaridade é atributo da pessoa, não preferência."
        ),
    }


def block_households(acc: Sums) -> dict:
    households = acc.get(("households",))
    rows = {}
    for tag in SEXES:
        arrangements = {}
        for label in ARRANGEMENTS:
            count = acc.get(("hh", tag, label))
            arrangements[label] = {
                "domicilios_pct": ratio_ci(count, households),
                "renda_per_capita_brl": ratio_ci(
                    acc.get(("hh_pc_sum", tag, label)),
                    acc.get(("hh_pc_n", tag, label)),
                    1.0,
                    2,
                    "valor",
                ),
                "moradores_media": ratio_ci(
                    acc.get(("hh_size", tag, label)), count, 1.0, 2, "valor"
                ),
                "bolsa_familia_pct": ratio_ci(acc.get(("hh_bolsa", tag, label)), count),
                "domicilios": round(float(count[0])),
            }
        rows[tag] = {
            "chefia_pct": ratio_ci(acc.get(("head", tag)), households),
            "arranjos": arrangements,
        }
    lone_mother = acc.get(("hh", "mulheres", "Sem cônjuge, com menor"))
    lone_father = acc.get(("hh", "homens", "Sem cônjuge, com menor"))
    return {
        "rotulo": "Chefia de domicílio e arranjo familiar",
        "universo": (
            "Domicílios particulares da PNAD Contínua anual 2025, 1ª visita, um "
            "registro por domicílio, com o peso da pessoa responsável. Menor = "
            "morador com menos de 18 anos. Cônjuge = presença de cônjuge ou "
            "companheiro no domicílio."
        ),
        "por_sexo_do_responsavel": rows,
        "responsavel_mulher_sem_conjuge_com_menor": {
            "domicilios_pct": ratio_ci(lone_mother, households),
            "razao_sobre_o_arranjo_masculino": gap_ci(
                lone_mother, households, lone_father, households
            ),
        },
        "menores_de_18_com_responsavel_mulher_sem_conjuge": ratio_ci(
            acc.get(("minors_female_lone",)), acc.get(("minors",))
        ),
        "domicilios": round(float(households[0])),
        "limite": (
            "O peso do domicílio é o peso da pessoa responsável, aproximação "
            "usual quando a base não traz peso domiciliar próprio. A calibração "
            "da PNAD é por sexo e idade, então moradores do mesmo domicílio "
            "podem ter pesos diferentes e o total de domicílios é estimativa, "
            "não contagem."
        ),
    }


def block_income_bands(acc: Sums, medians: dict) -> dict:
    rows = {}
    for tag in SEXES:
        base = acc.get(("base", tag))
        rows[tag] = {
            "distribuicao": {
                band: ratio_ci(acc.get(("band", tag, band)), base)
                for band in INCOME_BANDS
            },
            "pessoas_por_faixa": {
                band: round(float(acc.get(("band", tag, band))[0]))
                for band in INCOME_BANDS
            },
            "renda_per_capita_media_brl": ratio_ci(
                acc.get(("pc_sum", tag)), acc.get(("pc_n", tag)), 1.0, 2, "valor"
            ),
            "renda_per_capita_mediana_brl": round(
                weighted_median(
                    stack(medians, f"pc_{tag}"), stack(medians, f"pcw_{tag}")
                ),
                2,
            ),
            "renda_domiciliar_media_sm": ratio_ci(
                acc.get(("sm_sum", tag)), base, 1.0, 3, "valor"
            ),
            "pessoas_16_mais": round(float(base[0])),
        }
    share = {
        band: ratio_ci(acc.get(("band", "mulheres", band)), acc.get(("band_all", band)))
        for band in INCOME_BANDS
    }
    overall = ratio_ci(acc.get(("base", "mulheres")), acc.get(("adults",)))
    return {
        "rotulo": "Renda domiciliar em salários mínimos, por sexo",
        "universo": (
            "Pessoas de 16 anos ou mais. PNAD Contínua anual 2025, 1ª visita. "
            "Renda efetiva do domicílio (VD5001) em salários mínimos, nas mesmas "
            "quatro faixas do dossiê e da quota de renda da Nexus."
        ),
        "por_sexo": rows,
        "mulheres_no_total_da_faixa": share,
        "mulheres_no_total_de_adultos": overall,
        "excesso_feminino_na_faixa_mais_baixa_pp": round(
            share["Até 1 SM"]["pct"] - overall["pct"], 4
        ),
        "limite": (
            "Renda do domicílio, não da pessoa: descreve o domicílio em que a "
            "mulher vive, não o que ela recebe. A faixa é a mesma da quota da "
            "pesquisa, o que permite comparar composição, nunca intenção."
        ),
    }


def block_bolsa(acc: Sums) -> dict:
    rows = {}
    for tag in SEXES:
        base = acc.get(("base", tag))
        rows[tag] = {
            "vive_em_domicilio_beneficiario": ratio_ci(
                acc.get(("bolsa_home", tag)), base
            ),
            "recebe_pessoalmente": ratio_ci(acc.get(("bolsa_person", tag)), base),
        }
    recipients = sum(acc.get(("bolsa_person", tag)) for tag in SEXES)
    return {
        "rotulo": "Bolsa Família entre adultos, por sexo",
        "universo": (
            "Pessoas de 16 anos ou mais. PNAD Contínua anual 2025, 1ª visita. "
            "Domicílio beneficiário = pelo menos um morador declarou ter "
            "recebido Bolsa Família."
        ),
        "por_sexo": rows,
        "mulheres_entre_quem_recebe": ratio_ci(
            acc.get(("bolsa_person", "mulheres")), recipients
        ),
        "adultos_que_recebem": round(float(recipients[0])),
        "limite": (
            "Declaração do morador, não registro administrativo do CadÚnico. O "
            "titular preferencial do programa é a mulher, então a diferença por "
            "sexo em quem recebe é desenho do programa, não comportamento."
        ),
    }


def block_pyramid(acc: Sums) -> dict:
    def distribution(prefix: str, bands: tuple[str, ...]) -> dict:
        rows = {
            tag: {
                band: ratio_ci(acc.get((prefix, tag, band)), acc.get(("base", tag)))
                for band in bands
            }
            for tag in SEXES
        }
        share = {}
        for band in bands:
            total = sum(acc.get((prefix, tag, band)) for tag in SEXES)
            share[band] = ratio_ci(acc.get((prefix, "mulheres", band)), total)
        return {"por_sexo": rows, "mulheres_no_total_da_faixa": share}

    electorate = tse_electorate_by_age()
    quota = NEXUS["perfil_da_amostra"]["idade"]
    desvio = None
    if electorate:
        published = list(quota.values())
        target = list(electorate["distribuicao_pct"].values())
        desvio = {
            band: round(published[i] - target[i], 3) for i, band in enumerate(AGE_BANDS)
        }
    return {
        "rotulo": "Pirâmide etária adulta nas faixas da pesquisa",
        "universo": (
            "Pessoas de 16 anos ou mais. PNAD Contínua anual 2025, 1ª visita. "
            "Faixas 16 a 24, 25 a 40, 41 a 59 e 60 ou mais, que são as faixas "
            "efetivamente usadas pela Nexus, conferidas nas páginas 11, 28, 52 e "
            "113 do relatório de 03/08/2026."
        ),
        "faixas_nexus": distribution("age", AGE_BANDS),
        "faixas_alternativas": {
            **distribution("age_alt", AGE_BANDS_ALT),
            "nota": (
                "Corte 25-44 e 45-59, usado por outros institutos. Não é o corte "
                "da Nexus e não deve ser comparado com a quota publicada por ela."
            ),
        },
        "quota_nexus_idade_pct": quota,
        "quota_nexus_sexo_pct": NEXUS["perfil_da_amostra"]["sexo"],
        "eleitorado_tse_nas_faixas_nexus": electorate,
        "desvio_quota_menos_eleitorado_pp": desvio,
        "limite": (
            "A quota da pesquisa é do eleitorado, a PNAD é da população "
            "residente. As duas não precisam coincidir: o eleitorado exclui quem "
            "não se alistou e inclui quem mora fora do país. Comparar a quota da "
            "Nexus com um recorte etário diferente do dela produz desvio "
            "aparente onde não há desvio nenhum. Margem de erro zero em algumas "
            "faixas não é precisão infinita: a PNAD calibra os pesos, e as 200 "
            "réplicas, contra projeções de população por sexo e idade, de modo "
            "que a composição por sexo dentro de uma faixa que coincide com o "
            "grupo de calibração é fixa por construção."
        ),
    }


def block_regions(acc: Sums) -> dict:
    rows = {}
    for region in REGIONS:
        base = acc.get(("region", "mulheres", region))
        rows[region] = {
            "mulheres_16_mais_pct": ratio_ci(base, acc.get(("base", "mulheres"))),
            "renda_per_capita_media_brl": ratio_ci(
                acc.get(("reg_pc_sum", "mulheres", region)),
                acc.get(("reg_pc_n", "mulheres", region)),
                1.0,
                2,
                "valor",
            ),
            "ate_1_sm_pct": ratio_ci(acc.get(("reg_low", "mulheres", region)), base),
            "bolsa_familia_pct": ratio_ci(
                acc.get(("reg_bolsa", "mulheres", region)), base
            ),
            "ocupadas_pct": ratio_ci(acc.get(("reg_occ", "mulheres", region)), base),
            "mulheres": round(float(base[0])),
        }
    return {
        "rotulo": "Mulheres de 16 anos ou mais por região",
        "universo": (
            "Mulheres de 16 anos ou mais. PNAD Contínua anual 2025, 1ª visita. "
            "Renda per capita do domicílio a preços de abril de 2026."
        ),
        "por_regiao": rows,
        "nordestinas_entre_as_mulheres_ate_1_sm": ratio_ci(
            acc.get(("reg_low", "mulheres", "Nordeste")),
            sum(acc.get(("reg_low", "mulheres", region)) for region in REGIONS),
        ),
        "limite": (
            "Recorte de residência, não de origem. A região descreve composição "
            "de renda, não preferência política."
        ),
    }


def block_race(acc: Sums) -> dict:
    rows = {
        tag: {
            label: ratio_ci(acc.get(("race", tag, label)), acc.get(("base", tag)))
            for label in RACE_LABELS.values()
        }
        for tag in SEXES
    }
    return {
        "rotulo": "Cor ou raça declarada, adultos por sexo",
        "universo": "Pessoas de 16 anos ou mais. PNAD Contínua anual 2025, 1ª visita.",
        "por_sexo": rows,
        "limite": (
            "Autodeclaração no momento da entrevista. A Nexus não publica quota "
            "nem recorte de cor ou raça nesta rodada, então não há comparação "
            "possível com a pesquisa."
        ),
    }


def build() -> dict:
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as connection:
        annual, annual_medians = scan_annual(connection)
        quarter, quarter_medians = scan_quarter(connection)
    return {
        "generated_at": "2026-08-04",
        "warning": WARNING,
        "fontes": {
            "domicilio_renda_regiao": {
                "tabela": ANNUAL,
                "pesquisa": "PNAD Contínua anual 2025, 1ª visita",
                "peso": "V1032__peso_com_calibracao",
                "replicas": REPLICATES,
                "adultos_16_mais": round(float(annual.get(("adults",))[0])),
            },
            "trabalho_renda_escolaridade": {
                "tabela": QUARTER,
                "pesquisa": "PNAD Contínua trimestral, 1º trimestre de 2026",
                "peso": "V1028__peso_com_calibracao",
                "replicas": REPLICATES,
                "adultos_16_mais": round(
                    float(sum(quarter.get(("base", tag))[0] for tag in SEXES))
                ),
            },
            "nivel_de_confianca": LEVEL,
            "deflator": "IPCA, preços de abril de 2026",
        },
        "nexus_referencia": NEXUS,
        "renda_do_trabalho": block_income_gap(quarter, quarter_medians),
        "forca_de_trabalho": block_labour(quarter),
        "escolaridade": block_schooling(quarter, quarter_medians),
        "chefia_domiciliar": block_households(annual),
        "renda_domiciliar_por_faixa": block_income_bands(annual, annual_medians),
        "bolsa_familia": block_bolsa(annual),
        "piramide_etaria": block_pyramid(annual),
        "regiao": block_regions(annual),
        "cor_raca": block_race(annual),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(args.output), "bytes": args.output.stat().st_size},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
