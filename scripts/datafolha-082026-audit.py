#!/usr/bin/env python3
"""Auditoria reproduzivel do Datafolha nacional de agosto de 2026.

O script combina quatro camadas publicas:

1. transcricao dos cruzamentos do relatorio completo BR-04496/2026;
2. perfil oficial do eleitorado no TSE para sexo, idade e regiao;
3. PNAD Continua 1T/2026 para sexo, idade e escolaridade e anual 2025,
   visita 1, para renda domiciliar das pessoas de 16 anos ou mais;
4. anexo territorial das ondas de maio a agosto.

As reponderacoes trocam uma margem por vez. A combinada usa um modelo de
efeitos principais ajustado por IPF a todos os cruzamentos publicados. Ambas
sao analises de sensibilidade, nao correcoes da pesquisa e nao estimativas do
resultado real sem os microdados e pesos individuais do instituto.

Uso:
  python3 scripts/datafolha-082026-audit.py

Saidas:
  analysis/datafolha_082026/audit.json
  docs/assets/datafolha_082026_data.json
  docs/assets/datafolha_082026_data.js
  data/outputs/datafolha_bairros_082026_compare.csv
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / "data" / "originals"
OUTPUTS = ROOT / "data" / "outputs"
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
SITE_ASSETS = ROOT / "docs" / "assets"

SOURCE_DIR = ORIGINALS / "datafolha_082026"
REPORT = SOURCE_DIR / "DatafolhaRelatorio082026.pdf"
PNAD_DB = OUTPUTS / "brasil.sqlite"
TSE_DB = OUTPUTS / "tse_eleitorado_perfil.sqlite"

ROUNDS = {
    "2026-05": ORIGINALS / "datafolha_052026" / "BairrosDatafolha052026.pdf",
    "2026-06": ORIGINALS / "datafolha_062026" / "bairrosdatafolha062026.pdf",
    "2026-07": ORIGINALS / "datafolha_072026" / "BairrosDatafolha072026.pdf",
    "2026-08": SOURCE_DIR / "DatafolhaBairros082026.pdf",
}

OUT_JSON = ANALYSIS / "audit.json"
OUT_SITE_JSON = SITE_ASSETS / "datafolha_082026_data.json"
OUT_SITE_JS = SITE_ASSETS / "datafolha_082026_data.js"
OUT_TERRITORY = OUTPUTS / "datafolha_bairros_082026_compare.csv"

VOTE_KEYS = ("lula", "flavio", "branco_nulo", "indecisos")
PUBLISHED_RUNOFF = np.array([47.0, 43.0, 9.0, 2.0])

# Pagina 22 do relatorio completo. Cada linha soma 99 a 101 por arredondamento.
RUNOFF_CROSSTABS = {
    "sexo": {
        "page": 22,
        "rows": {
            "Masculino": [43, 48, 8, 1],
            "Feminino": [51, 38, 9, 2],
        },
        "bases": {"Masculino": 982, "Feminino": 1076},
    },
    "idade": {
        "page": 22,
        "rows": {
            "16-24": [46, 45, 7, 3],
            "25-34": [45, 44, 10, 2],
            "35-44": [42, 47, 10, 1],
            "45-59": [49, 40, 9, 2],
            "60+": [51, 40, 7, 1],
        },
        "bases": {"16-24": 263, "25-34": 382, "35-44": 403, "45-59": 522, "60+": 488},
    },
    "escolaridade": {
        "page": 22,
        "rows": {
            "Fundamental": [59, 35, 4, 2],
            "Medio": [40, 49, 10, 2],
            "Superior": [45, 42, 12, 2],
        },
        "bases": {"Fundamental": 617, "Medio": 926, "Superior": 514},
    },
    "renda": {
        "page": 22,
        "rows": {
            "Ate 2 SM": [55, 35, 8, 1],
            "2 a 5 SM": [37, 51, 10, 2],
            "Mais de 5 SM": [39, 54, 7, 0],
        },
        "bases": {"Ate 2 SM": 1031, "2 a 5 SM": 704, "Mais de 5 SM": 249},
    },
    "regiao": {
        "page": 22,
        "rows": {
            "Sudeste": [43, 46, 9, 2],
            "Sul": [38, 50, 9, 3],
            "Nordeste": [61, 30, 8, 2],
            "Centro-Oeste/Norte": [42, 49, 8, 1],
        },
        "bases": {
            "Sudeste": 862,
            "Sul": 304,
            "Nordeste": 569,
            "Centro-Oeste/Norte": 323,
        },
    },
}

FIRST_ROUND = {
    "Lula (PT)": 39,
    "Flavio Bolsonaro (PL)": 33,
    "Ronaldo Caiado (PSD)": 5,
    "Renan Santos (MISSAO)": 4,
    "Zema (NOVO)": 3,
    "Augusto Cury (AVANTE)": 2,
    "Samara (UP)": 1,
    "Rui Costa Pimenta (PCO)": 1,
    "Edmilson Costa (PCB)": 1,
    "Wilson Grassi (DEMOCRATA)": 1,
    "Clariana Barao (DC)": 0,
    "Hertz Dias (PSTU)": 0,
    "Branco/nulo/nenhum": 6,
    "Indecisos": 4,
}

RUNOFF_ALTERNATIVES = {
    "Flavio Bolsonaro": {"lula": 47, "oposicao": 43, "branco_nulo": 9, "indecisos": 2},
    "Ronaldo Caiado": {"lula": 47, "oposicao": 40, "branco_nulo": 11, "indecisos": 3},
    "Zema": {"lula": 48, "oposicao": 38, "branco_nulo": 12, "indecisos": 2},
    "Renan Santos": {"lula": 47, "oposicao": 37, "branco_nulo": 14, "indecisos": 2},
}

DATAFOLHA_PROFILE = {
    "sexo": {"Masculino": 48, "Feminino": 52},
    "idade": {"16-24": 13, "25-34": 19, "35-44": 20, "45-59": 25, "60+": 24},
    "escolaridade": {"Fundamental": 30, "Medio": 45, "Superior": 25},
    "renda": {"Ate 2 SM": 50, "2 a 5 SM": 34, "Mais de 5 SM": 12, "NS/recusa": 4},
    "regiao": {"Sudeste": 42, "Sul": 15, "Nordeste": 28, "Centro-Oeste/Norte": 16},
}

# Bases ponderadas de cada recorte, linha final das tabelas do anexo,
# paginas 9 a 29 de 29. Nao sao contagens de entrevistas: o proprio anexo as
# rotula como "Base ponderada". As unicas contagens de campo publicadas estao
# nas paginas 12 e 13 da divulgacao e sao tratadas em
# scripts/datafolha-082026-aprofundamento.py.
WEIGHTED_BASES = {
    "sexo": {"Masculino": 982, "Feminino": 1076},
    "idade": {"16-24": 263, "25-34": 382, "35-44": 403, "45-59": 522, "60+": 488},
    "escolaridade": {"Fundamental": 617, "Medio": 926, "Superior": 514},
    "renda": {"Ate 2 SM": 1031, "2 a 5 SM": 704, "Mais de 5 SM": 249},
    "regiao": {"Sudeste": 862, "Sul": 304, "Nordeste": 569, "Centro-Oeste/Norte": 323},
}

HEADLINES = [
    {
        "vehicle": "Datafolha/report",
        "title": "Lula lidera no 1o turno e tem vantagem de quatro pontos sobre Flavio Bolsonaro no 2o turno",
        "url": None,
        "assessment": "Titulo do relatorio, pagina 2. A lideranca do primeiro turno e sustentada; no segundo, quatro pontos sao vantagem numerica sem lideranca identificada a 95%.",
    },
    {
        "vehicle": "G1",
        "title": "Datafolha - 2o turno: Lula, 47%; Flavio Bolsonaro, 43%",
        "url": "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/noticia/2026/08/21/datafolha-segundo-turno-21-agosto.ghtml",
        "assessment": "Placar fiel, mas sem a hipotese 'se fosse hoje' nem a incerteza da diferenca.",
    },
    {
        "vehicle": "G1",
        "title": "Datafolha - 1o turno: Lula, 39%; Flavio, 33%; Caiado, 5%",
        "url": "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/noticia/2026/08/21/datafolha-primeiro-turno-21-agosto.ghtml",
        "assessment": "Placar fiel e sem verbo causal; omite a margem da diferenca.",
    },
    {
        "vehicle": "G1",
        "title": "Datafolha: 50% desaprovam governo Lula, e 47% aprovam",
        "url": "https://g1.globo.com/politica/eleicoes/2026/pesquisa-eleitoral/noticia/2026/08/21/datafolha-aprova-desaprova-governo-21-agosto.ghtml",
        "assessment": "Reproduz a pergunta direta de aprovacao, sem projetar causa.",
    },
    {
        "vehicle": "Band",
        "title": "Datafolha: Lula lidera disputa com 39% das intencoes; Flavio registra 33%",
        "url": "https://www.band.com.br/politica/eleicoes/2026/datafolha-divulga-1-pesquisa-presidencial-apos-inicio-oficial-de-campanhas-202608211834",
        "assessment": "Lidera no titulo se refere ao primeiro turno, cuja diferenca permanece positiva ate deff 2. O corpo chama 47 a 43 de lideranca no segundo turno, sem suporte a 95%.",
    },
    {
        "vehicle": "RED",
        "title": "Datafolha: Lula mantem lideranca e oscilacoes de um ponto nao indicam mudanca na disputa",
        "url": "https://red.org.br/noticias/datafolha-lula-mantem-lideranca-e-oscilacoes-de-um-ponto-nao-indicam-mudanca-na-disputa-por-benedito-tadeu-cesar/",
        "assessment": "Lideranca se refere ao primeiro turno; a ressalva sobre oscilacoes de um ponto e estatisticamente adequada.",
    },
    {
        "vehicle": "CNN Brasil",
        "title": "Datafolha: Lula lidera entre mulheres e pobres; Flavio, entre evangelicos",
        "url": "https://www.cnnbrasil.com.br/eleicoes/datafolha-lula-lidera-entre-mulheres-e-pobres-flavio-entre-evangelicos/",
        "assessment": "Lidera descreve segmentos, nao o placar nacional; cada recorte exige sua propria margem.",
    },
    {
        "vehicle": "Folha",
        "title": "Datafolha: Lula marca 39% no 1o turno, e Flavio Bolsonaro tem 33%",
        "url": "https://www1.folha.uol.com.br/poder/2026/08/datafolha-lula-marca-39-no-1o-turno-e-flavio-bolsonaro-tem-33.shtml",
        "assessment": "O titulo e numerico; o texto chama 47 a 43 de lideranca, embora o intervalo de 95% da diferenca inclua zero.",
    },
    {
        "vehicle": "Folha",
        "title": "Datafolha: Avaliacao negativa de Lula vai de 38% para 41%",
        "url": "https://www1.folha.uol.com.br/poder/2026/08/datafolha-avaliacao-negativa-de-lula-vai-de-38-para-41.shtml",
        "assessment": "Direcao cravada no titulo; o proprio subtitulo admite que a variacao esta dentro da margem.",
    },
    {
        "vehicle": "Folha",
        "title": "Datafolha: Popularidade de Lula derrapa e mantem disputa com Flavio equilibrada",
        "url": "https://www1.folha.uol.com.br/poder/2026/08/datafolha-popularidade-de-lula-derrapa-e-mantem-disputa-com-flavio-equilibrada.shtml",
        "assessment": "Equilibrio e suportado; 'derrapa' e interpretacao sobre oscilacoes de uma onda.",
    },
    {
        "vehicle": "UOL",
        "title": "Pesquisa Datafolha para presidente: veja novos numeros atualizados",
        "url": "https://noticias.uol.com.br/eleicoes/2026/08/21/pesquisa-datafolha-para-presidente-veja-novos-numeros-atualizados.amp.htm",
        "assessment": "Titulo neutro; o texto informa 39 a 33 e 47 a 43.",
    },
    {
        "vehicle": "UOL",
        "title": "Toledo: Datafolha mostra que Lula e Flavio tem dificuldades em crescer",
        "url": "https://noticias.uol.com.br/politica/ultimas-noticias/2026/08/21/toledo-datafolha-mostra-que-lula-e-flavio-tem-dificuldades-em-crescer.amp.htm",
        "assessment": "A analise explicita estabilidade e recusa significado a oscilacoes de um ponto.",
    },
    {
        "vehicle": "UOL/Reuters",
        "title": "Lula tem 47% e Flavio Bolsonaro soma 43% no 2o turno",
        "url": "https://noticias.uol.com.br/ultimas-noticias/reuters/2026/08/21/lula-tem-47-e-flavio-bolsonaro-soma-43-no-2-turno-mostra-datafolha.htm",
        "assessment": "O titulo e numerico; o texto acerta ao descrever o cenario como limite do empate tecnico.",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value: object) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def normalize_dict(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    return {key: 100 * value / total for key, value in values.items()}


def extract_locations(path: Path, wave: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables():
                for cells in table:
                    if len(cells) < 6:
                        continue
                    if len(cells) >= 7:
                        region, uf, city, neighborhood, _upt, sector, interviews = map(
                            clean, cells[:7]
                        )
                    else:
                        region, uf, city, neighborhood, sector, interviews = map(
                            clean, cells[:6]
                        )
                    joined = clean(f"{neighborhood} {sector}")
                    digits = "".join(ch if ch.isdigit() else " " for ch in joined)
                    candidates = [item for item in digits.split() if len(item) == 15]
                    if not candidates or not interviews.isdigit():
                        continue
                    sector = candidates[-1]
                    neighborhood = clean(joined.rsplit(sector, 1)[0])
                    rows.append(
                        {
                            "wave": wave,
                            "page": page_number,
                            "region": region,
                            "uf": uf,
                            "municipality": city,
                            "municipality_code": sector[:7],
                            "neighborhood": neighborhood,
                            "sector": sector,
                            "interviews": int(interviews),
                        }
                    )
    if not rows:
        raise RuntimeError(f"Nenhuma linha territorial extraida de {path}")
    return rows


def overlap(current: set[str], previous: set[str]) -> dict[str, object]:
    repeated = current & previous
    return {
        "repeated": len(repeated),
        "current_total": len(current),
        "previous_total": len(previous),
        "share_of_current_pct": round(100 * len(repeated) / len(current), 2),
    }


def sql_distribution(
    connection: sqlite3.Connection,
    table: str,
    weight: str,
    category_sql: str,
    where_sql: str,
) -> dict[str, float]:
    query = f"""
        WITH x AS (
          SELECT {category_sql} AS category, {weight} AS weight
          FROM {table}
          WHERE {where_sql} AND {weight} IS NOT NULL
        )
        SELECT category, SUM(weight) FROM x
        WHERE category IS NOT NULL GROUP BY category
    """
    values = {
        str(category): float(total) for category, total in connection.execute(query)
    }
    return normalize_dict(values)


def pnad_benchmarks() -> dict[str, object]:
    with sqlite3.connect(PNAD_DB) as connection:
        sex = sql_distribution(
            connection,
            "base_labeled_npv",
            "V1028__peso_com_calibracao",
            "CASE V2007__sexo WHEN 1 THEN 'Masculino' WHEN 2 THEN 'Feminino' END",
            "V2009__idade_na_data_de_referencia >= 16",
        )
        age = sql_distribution(
            connection,
            "base_labeled_npv",
            "V1028__peso_com_calibracao",
            """CASE
              WHEN V2009__idade_na_data_de_referencia BETWEEN 16 AND 24 THEN '16-24'
              WHEN V2009__idade_na_data_de_referencia BETWEEN 25 AND 34 THEN '25-34'
              WHEN V2009__idade_na_data_de_referencia BETWEEN 35 AND 44 THEN '35-44'
              WHEN V2009__idade_na_data_de_referencia BETWEEN 45 AND 59 THEN '45-59'
              ELSE '60+' END""",
            "V2009__idade_na_data_de_referencia >= 16",
        )
        education = sql_distribution(
            connection,
            "base_labeled_npv",
            "V1028__peso_com_calibracao",
            """CASE
              WHEN VD3004__nivel_de_instrucao_mais_elevado_alcancado_5_anos_ou_mais_de_idade BETWEEN 1 AND 3 THEN 'Fundamental'
              WHEN VD3004__nivel_de_instrucao_mais_elevado_alcancado_5_anos_ou_mais_de_idade BETWEEN 4 AND 5 THEN 'Medio'
              WHEN VD3004__nivel_de_instrucao_mais_elevado_alcancado_5_anos_ou_mais_de_idade BETWEEN 6 AND 7 THEN 'Superior'
              END""",
            "V2009__idade_na_data_de_referencia >= 16",
        )
        income = sql_distribution(
            connection,
            "base_anual_visita1_labeled_npv",
            "V1032__peso_com_calibracao",
            """CASE
              WHEN VD5001__rend_efetivo_domiciliar_mw <= 2 THEN 'Ate 2 SM'
              WHEN VD5001__rend_efetivo_domiciliar_mw <= 5 THEN '2 a 5 SM'
              ELSE 'Mais de 5 SM' END""",
            "V2009__idade_na_data_de_referencia >= 16 AND VD5001__rend_efetivo_domiciliar_mw IS NOT NULL",
        )
        periods = {
            "quarterly": connection.execute(
                "SELECT MAX(Ano__ano_de_referencia || '-T' || Trimestre__trimestre_de_referencia) FROM base_labeled_npv"
            ).fetchone()[0],
            "annual": connection.execute(
                "SELECT MAX(Ano__ano_de_referencia) FROM base_anual_visita1_labeled_npv"
            ).fetchone()[0],
        }
    return {
        "source": "PNAD Continua",
        "universe": "pessoas de 16 anos ou mais",
        "periods": periods,
        "sexo": sex,
        "idade": age,
        "escolaridade": education,
        "renda": income,
        "income_note": "Rendimento domiciliar efetivo VD5001, visita 1, em salarios minimos do mes-alvo do pipeline.",
    }


def tse_benchmarks() -> dict[str, object]:
    with sqlite3.connect(TSE_DB) as connection:
        metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        sex_raw = dict(
            connection.execute(
                "SELECT category,qt_eleitores FROM summary WHERE dimension='genero_atlas_binario'"
            )
        )
        age_raw = dict(
            connection.execute(
                "SELECT category,qt_eleitores FROM summary WHERE dimension='idade_raw'"
            )
        )
        region_raw = dict(
            connection.execute(
                "SELECT category,qt_eleitores FROM summary WHERE dimension='regiao'"
            )
        )

    sex = normalize_dict({"Masculino": sex_raw["Homem"], "Feminino": sex_raw["Mulher"]})
    age_keys = {
        "16-24": [
            "16 anos",
            "17 anos",
            "18 anos",
            "19 anos",
            "20 anos",
            "21 a 24 anos",
        ],
        "25-34": ["25 a 29 anos", "30 a 34 anos"],
        "35-44": ["35 a 39 anos", "40 a 44 anos"],
        "45-59": ["45 a 49 anos", "50 a 54 anos", "55 a 59 anos"],
        "60+": [
            "60 a 64 anos",
            "65 a 69 anos",
            "70 a 74 anos",
            "75 a 79 anos",
            "80 a 84 anos",
            "85 a 89 anos",
            "90 a 94 anos",
            "95 a 99 anos",
            "100 anos ou mais",
        ],
    }
    age = normalize_dict(
        {key: sum(age_raw[item] for item in items) for key, items in age_keys.items()}
    )
    region = normalize_dict(
        {
            "Sudeste": region_raw["Sudeste"],
            "Sul": region_raw["Sul"],
            "Nordeste": region_raw["Nordeste"],
            "Centro-Oeste/Norte": region_raw["Centro-Oeste"] + region_raw["Norte"],
        }
    )
    return {
        "source": metadata["source_name"],
        "generated": f"{metadata['dt_geracao']} {metadata['hh_geracao']}",
        "universe": "eleitorado residente no Brasil; exterior excluido",
        "resident_electors": int(metadata["total_eleitores_brasil_sem_exterior"]),
        "sexo": sex,
        "idade": age,
        "regiao": region,
    }


def row_matrix(dimension: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    block = RUNOFF_CROSSTABS[dimension]
    categories = list(block["rows"])
    matrix = np.array([block["rows"][category] for category in categories], dtype=float)
    bases = np.array([block["bases"][category] for category in categories], dtype=float)
    return categories, matrix, bases


def margin_topline(matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    rows = matrix / matrix.sum(axis=1, keepdims=True)
    weights = weights / weights.sum()
    return (weights[:, None] * rows).sum(axis=0) * 100


def single_reweight(dimension: str, target: dict[str, float]) -> dict[str, object]:
    categories, matrix, bases = row_matrix(dimension)
    target_weights = np.array(
        [target[category] for category in categories], dtype=float
    )
    reproduced = margin_topline(matrix, bases)
    counterfactual = margin_topline(matrix, target_weights)
    result = PUBLISHED_RUNOFF + (counterfactual - reproduced)
    return {
        "dimension": dimension,
        "page": RUNOFF_CROSSTABS[dimension]["page"],
        "categories": categories,
        "published_profile_from_bases": {
            key: round(value, 3)
            for key, value in zip(
                categories, normalize_dict(dict(zip(categories, bases))).values()
            )
        },
        "target_profile": {key: round(target[key], 3) for key in categories},
        "reproduced_from_published_cells": dict(
            zip(VOTE_KEYS, np.round(reproduced, 3))
        ),
        "result": dict(zip(VOTE_KEYS, np.round(result, 3))),
        "gap_lula_minus_flavio": round(float(result[0] - result[1]), 3),
    }


def combined_reweight(
    targets: dict[str, dict[str, float]], iterations: int = 80
) -> dict[str, object]:
    dimensions = list(RUNOFF_CROSSTABS)
    matrices: dict[str, np.ndarray] = {}
    source_weights: dict[str, np.ndarray] = {}
    target_weights: dict[str, np.ndarray] = {}
    for dimension in dimensions:
        categories, matrix, bases = row_matrix(dimension)
        matrices[dimension] = matrix / matrix.sum(axis=1, keepdims=True)
        source_weights[dimension] = bases / bases.sum()
        raw_target = np.array(
            [targets[dimension][key] for key in categories], dtype=float
        )
        target_weights[dimension] = raw_target / raw_target.sum()

    seed = source_weights[dimensions[0]]
    for dimension in dimensions[1:]:
        seed = np.multiply.outer(seed, source_weights[dimension])
    joint = seed[..., None] * (PUBLISHED_RUNOFF / PUBLISHED_RUNOFF.sum())

    for _ in range(iterations):
        row_mass = joint.sum(axis=-1)
        joint *= np.divide(
            seed, row_mass, out=np.ones_like(row_mass), where=row_mass > 0
        )[..., None]
        for axis, dimension in enumerate(dimensions):
            for index in range(len(source_weights[dimension])):
                selector: list[int | slice] = [slice(None)] * (len(dimensions) + 1)
                selector[axis] = index
                block = joint[tuple(selector)]
                sum_axes = tuple(range(block.ndim - 1))
                current = block.sum(axis=sum_axes)
                desired = source_weights[dimension][index] * matrices[dimension][index]
                scale = np.divide(
                    desired, current, out=np.ones_like(current), where=current > 0
                )
                joint[tuple(selector)] = block * scale

    cell_mass = joint.sum(axis=-1)
    conditional = joint / np.where(cell_mass > 0, cell_mass, 1.0)[..., None]
    source_top = (seed[..., None] * conditional).sum(axis=tuple(range(len(dimensions))))

    target_seed = target_weights[dimensions[0]]
    for dimension in dimensions[1:]:
        target_seed = np.multiply.outer(target_seed, target_weights[dimension])
    target_top = (target_seed[..., None] * conditional).sum(
        axis=tuple(range(len(dimensions)))
    )
    delta = (target_top - source_top) * 100
    result = PUBLISHED_RUNOFF + delta
    return {
        "method": "IPF de efeitos principais sobre os cruzamentos unidimensionais publicados",
        "dimensions": dimensions,
        "result": dict(zip(VOTE_KEYS, np.round(result, 3))),
        "gap_lula_minus_flavio": round(float(result[0] - result[1]), 3),
        "limitation": "Sem microdados, interacoes demograficas alem dos efeitos principais nao sao identificadas.",
    }


def rounding_sensitivity(
    dimension: str,
    target: dict[str, float],
    draws: int = 10_000,
    seed: int = 20260825,
) -> dict[str, object]:
    categories, matrix, bases = row_matrix(dimension)
    target_weights = np.array(
        [target[category] for category in categories], dtype=float
    )
    generator = random.Random(seed)
    gaps = []
    for _ in range(draws):
        perturbed = np.array(
            [
                [max(0.0, value + generator.uniform(-0.5, 0.5)) for value in row]
                for row in matrix
            ]
        )
        reproduced = margin_topline(perturbed, bases)
        counterfactual = margin_topline(perturbed, target_weights)
        result = PUBLISHED_RUNOFF + (counterfactual - reproduced)
        gaps.append(float(result[0] - result[1]))
    gaps.sort()

    def pick(q: float) -> float:
        return gaps[min(draws - 1, max(0, int(q * (draws - 1))))]

    return {
        "dimension": dimension,
        "draws": draws,
        "cell_rounding": "uniforme no intervalo impresso +/-0,5 pp; linhas renormalizadas",
        "gap_lula_minus_flavio_p2_5": round(pick(0.025), 3),
        "gap_lula_minus_flavio_median": round(pick(0.5), 3),
        "gap_lula_minus_flavio_p97_5": round(pick(0.975), 3),
        "share_flavio_ahead": round(sum(gap < 0 for gap in gaps) / draws, 4),
    }


def difference_margin(p_a: float, p_b: float, n: int, deff: float = 1.0) -> float:
    variance = ((p_a + p_b) - (p_a - p_b) ** 2) / n
    return 100 * 1.96 * math.sqrt(variance * deff)


def margin_scenarios(p_a: float, p_b: float, n: int) -> dict[str, object]:
    gap = 100 * (p_a - p_b)
    scenarios = []
    for deff in (1.0, 1.5, 2.0):
        margin = difference_margin(p_a, p_b, n, deff)
        scenarios.append(
            {
                "deff": deff,
                "difference_moe": round(margin, 3),
                "gap_ci": [round(gap - margin, 3), round(gap + margin, 3)],
                "effective_n": round(n / deff),
            }
        )
    return {"gap": round(gap, 3), "scenarios": scenarios}


def territory_audit() -> tuple[dict[str, object], list[dict[str, object]]]:
    locations = {wave: extract_locations(path, wave) for wave, path in ROUNDS.items()}
    sectors = {
        wave: {str(row["sector"]) for row in rows} for wave, rows in locations.items()
    }
    cities = {
        wave: {str(row["municipality_code"]) for row in rows}
        for wave, rows in locations.items()
    }
    neighborhoods = {
        wave: {
            f'{row["municipality_code"]}|{str(row["neighborhood"]).upper()}'
            for row in rows
        }
        for wave, rows in locations.items()
    }
    counts = Counter(str(row["sector"]) for row in locations["2026-08"])
    duplicates = [
        {"sector": sector, "occurrences": count}
        for sector, count in counts.items()
        if count > 1
    ]
    august_rows = locations["2026-08"]
    july_cities = cities["2026-07"]
    august_interviews = sum(int(row["interviews"]) for row in august_rows)
    interviews_in_july_cities = sum(
        int(row["interviews"])
        for row in august_rows
        if str(row["municipality_code"]) in july_cities
    )
    cluster_distribution = Counter(int(row["interviews"]) for row in august_rows)
    report = {
        "rounds": {
            wave: {
                "rows": len(rows),
                "unique_sectors": len(sectors[wave]),
                "unique_municipalities": len(cities[wave]),
                "interviews": sum(int(row["interviews"]) for row in rows),
            }
            for wave, rows in locations.items()
        },
        "july_to_august": {
            "sectors": overlap(sectors["2026-08"], sectors["2026-07"]),
            "municipalities": overlap(cities["2026-08"], cities["2026-07"]),
            "neighborhood_labels": overlap(
                neighborhoods["2026-08"], neighborhoods["2026-07"]
            ),
            "interviews_in_repeated_municipalities": interviews_in_july_cities,
            "share_interviews_in_repeated_municipalities": round(
                interviews_in_july_cities / august_interviews, 6
            ),
        },
        "june_to_august": {
            "sectors": overlap(sectors["2026-08"], sectors["2026-06"]),
            "municipalities": overlap(cities["2026-08"], cities["2026-06"]),
        },
        "all_four": {
            "sectors": len(set.intersection(*(sectors[wave] for wave in ROUNDS))),
            "municipalities": len(set.intersection(*(cities[wave] for wave in ROUNDS))),
        },
        "duplicate_sectors_august": duplicates,
        "august_document_check": {
            "municipalities_declared_in_report": 128,
            "municipality_codes_in_annex": len(cities["2026-08"]),
            "difference": len(cities["2026-08"]) - 128,
            "interviews_per_sector": {
                "mean": round(august_interviews / len(sectors["2026-08"]), 3),
                "distribution": {
                    str(size): occurrences
                    for size, occurrences in sorted(cluster_distribution.items())
                },
            },
        },
    }
    flattened = [row for wave in ROUNDS for row in locations[wave]]
    return report, flattened


def write_territory_csv(rows: list[dict[str, object]]) -> None:
    waves = list(ROUNDS)
    sector_sets = {
        wave: {str(row["sector"]) for row in rows if row["wave"] == wave}
        for wave in waves
    }
    fieldnames = [
        "wave",
        "page",
        "region",
        "uf",
        "municipality",
        "municipality_code",
        "neighborhood",
        "sector",
        "interviews",
        *[f"sector_in_{wave}" for wave in waves],
    ]
    with OUT_TERRITORY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            sector = str(row["sector"])
            writer.writerow(
                {
                    **row,
                    **{
                        f"sector_in_{wave}": int(sector in sector_sets[wave])
                        for wave in waves
                    },
                }
            )


def main() -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    SITE_ASSETS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    pnad = pnad_benchmarks()
    tse = tse_benchmarks()
    targets = {
        "sexo": tse["sexo"],
        "idade": tse["idade"],
        "escolaridade": pnad["escolaridade"],
        "renda": pnad["renda"],
        "regiao": tse["regiao"],
    }
    single = {
        dimension: single_reweight(dimension, target)
        for dimension, target in targets.items()
    }
    combined = combined_reweight(targets)
    rounding = rounding_sensitivity("renda", targets["renda"])
    territory, rows = territory_audit()
    write_territory_csv(rows)

    income_profile_nonmissing = normalize_dict(
        {
            key: value
            for key, value in DATAFOLHA_PROFILE["renda"].items()
            if key != "NS/recusa"
        }
    )
    pnad_income = pnad["renda"]
    observed_gap = 4.0
    reweighted_gap = float(single["renda"]["gap_lula_minus_flavio"])
    tipping = observed_gap / (observed_gap - reweighted_gap)

    manifest = [
        {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(SOURCE_DIR.glob("*.pdf"))
    ]

    output = {
        "poll": {
            "registration": "BR-04496/2026",
            "field_report": "2026-08-18/2026-08-19",
            "field_registry": "2026-08-18/2026-08-20",
            "sample": 2058,
            "municipalities": 128,
            "method": "presencial em pontos de fluxo, estratificacao e cotas",
            "report_headline": "Lula lidera no 1o turno e tem vantagem de quatro pontos sobre Flavio Bolsonaro no 2o turno",
            "published_individual_moe": 2,
            "cost_brl": 307641.60,
            "cost_per_interview_brl": round(307641.60 / 2058, 2),
            "contractors": {
                "Folha": 153820.80,
                "TV Globo": 153820.80,
                "group_relationship": "UOL integra o Grupo Folha e deve ser analisado no mesmo ecossistema jornalistico.",
                "note": "Cada nota fiscal atribui 50% da rodada nacional ao contratante formal. UOL nao aparece como contratante juridico separado nem como pagador em nota fiscal; isso nao elimina seu vinculo com o Grupo Folha.",
            },
            "first_round": FIRST_ROUND,
            "runoff": dict(zip(VOTE_KEYS, PUBLISHED_RUNOFF.tolist())),
            "runoff_alternatives": RUNOFF_ALTERNATIVES,
            "profiles": DATAFOLHA_PROFILE,
            "weighted_bases": WEIGHTED_BASES,
        },
        "benchmarks": {"pnad": pnad, "tse": tse},
        "profile_deltas": {
            dimension: [
                {
                    "category": category,
                    "datafolha": DATAFOLHA_PROFILE[dimension][category],
                    "official": round(targets[dimension][category], 3),
                    "delta": round(
                        DATAFOLHA_PROFILE[dimension][category]
                        - targets[dimension][category],
                        3,
                    ),
                }
                for category in targets[dimension]
            ]
            for dimension in targets
        },
        "reweighting": {
            "single_margin": single,
            "combined_main_effects": combined,
            "income_rounding_sensitivity": rounding,
            "income_tipping_point": {
                "share_of_path_datafolha_to_pnad": round(tipping, 4),
                "datafolha_nonmissing_profile": {
                    key: round(value, 3)
                    for key, value in income_profile_nonmissing.items()
                },
                "pnad_profile": {
                    key: round(value, 3) for key, value in pnad_income.items()
                },
                "excess_up_to_2_sm_pp_weighted_profile": round(
                    DATAFOLHA_PROFILE["renda"]["Ate 2 SM"] - pnad_income["Ate 2 SM"], 3
                ),
                "interview_equivalent": round(
                    2058
                    * (DATAFOLHA_PROFILE["renda"]["Ate 2 SM"] - pnad_income["Ate 2 SM"])
                    / 100
                ),
            },
            "limitations": [
                "Margem unica ignora interacoes entre renda, escolaridade, idade, regiao e religiao.",
                "Renda familiar declarada em ponto de fluxo nao e identica ao rendimento domiciliar medido pela PNAD.",
                "A combinada supoe apenas efeitos principais porque os microdados do instituto nao sao publicos.",
                "Nenhum cenario produz o resultado real; todos medem dependencia do placar em relacao a uma regua.",
            ],
        },
        "uncertainty": {
            "runoff_gap": margin_scenarios(0.47, 0.43, 2058),
            "first_round_gap": margin_scenarios(0.39, 0.33, 2058),
            "note": "Margem da diferenca usa a covariancia multinomial sob AAS; deff real nao e publicado.",
        },
        "territory": territory,
        "headlines": HEADLINES,
        "questionnaire_semantics": {
            "order": "Voto espontaneo e estimulado precedem rejeicao, governo, partido, ideologia, escolaridade e renda.",
            "rotation": "Cartoes, situacoes de segundo turno e nomes dentro de cada situacao tem rodizio declarado.",
            "motivation_problem": "A alternativa 'melhores propostas e mais preparado' junta duas virtudes e concorre com a formulacao negativa 'evitar que outro seja eleito'.",
            "hypothetical": "A pergunta diz 'se a eleicao fosse hoje'; o numero e fotografia condicional, nao previsao.",
            "foreign_interference": "A pergunta sobre acao de outros paises vem depois de voto, rejeicao e governo; nao pode ter induzido os toplines.",
        },
        "strategic_findings": {
            "substitution": {
                "lula_range": [47, 48],
                "opposition_loss_vs_flavio": {"Caiado": 3, "Zema": 5, "Renan": 6},
                "reading": "Trocar o lider da oposicao quase nao move Lula; reduz o adversario e aumenta a nao escolha.",
            },
            "unaligned": {
                "first_round": {
                    "lula": 19,
                    "flavio": 21,
                    "caiado": 8,
                    "renan": 11,
                    "zema": 6,
                    "blank": 17,
                    "undecided": 8,
                },
                "runoff": {"lula": 33, "flavio": 38, "blank": 26, "undecided": 4},
                "vote_can_change": 49,
            },
            "no_party": {
                "share": 47,
                "first_round": {"lula": 24, "flavio": 34, "blank": 12, "undecided": 7},
                "runoff": {"lula": 35, "flavio": 47, "blank": 15, "undecided": 3},
                "vote_can_change": 40,
                "votes_to_avoid_other": 39,
            },
            "municipality_nature": {
                "metro": {"share": 40, "lula": 49, "flavio": 41},
                "interior": {"share": 60, "lula": 46, "flavio": 44},
                "metro_share_of_national_gap_pct": round(
                    (0.40 * 8) / (0.40 * 8 + 0.60 * 2) * 100, 1
                ),
            },
        },
        "source_manifest": manifest,
        "evidence_levels": {
            "fact": "Toplines, cruzamentos, perfil, questionario, registro, notas e anexo territorial.",
            "inference": "Reponderacoes, margem da diferenca, IPF de transferencia e leitura semantica.",
            "not_supported": "Fraude, intencao editorial coordenada ou resultado eleitoral verdadeiro.",
        },
    }

    payload = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    OUT_JSON.write_text(payload, encoding="utf-8")
    OUT_SITE_JSON.write_text(payload, encoding="utf-8")
    OUT_SITE_JS.write_text(
        "window.__DATAFOLHA_082026__="
        + json.dumps(output, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    print(f"OK: {OUT_JSON.relative_to(ROOT)}")
    print(f"OK: {OUT_TERRITORY.relative_to(ROOT)}")
    for dimension, item in single.items():
        result = item["result"]
        print(
            f"{dimension:14s} Lula {result['lula']:5.2f} x Flavio {result['flavio']:5.2f} "
            f"(gap {item['gap_lula_minus_flavio']:+.2f})"
        )
    print(
        "combinada      "
        f"Lula {combined['result']['lula']:.2f} x Flavio {combined['result']['flavio']:.2f} "
        f"(gap {combined['gap_lula_minus_flavio']:+.2f})"
    )


if __name__ == "__main__":
    main()
