#!/usr/bin/env python3
"""Camada 2 do atlas paulista: reponderação por renda, fluxos IPF, o vão
Tarcísio-Flávio, índice dos carregadores e corredores de campanha.

Toda tabela transcrita cita a página do relatório de origem. Toda conta
derivada é provada recompondo o placar publicado antes de ser usada. As
fitas do diagrama de fluxo são estimativa por IPF sobre margens publicadas,
com prior empírica medida pela Atlas no voto de 2022, e são publicadas como
estimativa, nunca como medição.

Saídas:
  docs/assets/sp_092026_camada2.json
  data/pesquisas/estaduais/sp/2026-09/derivados/carregadores-municipais.csv
"""

import csv
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
DERIVED = ROOT / "data/pesquisas/estaduais/sp/2026-09/derivados"
TSE_ZIP = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
DATA = json.loads((ASSETS / "sp_092026_data.json").read_text())
PNAD = json.loads((ASSETS / "sp_092026_pnad.json").read_text())["anual_2025_visita1"]
CITIES = DATA["municipios"]
CITY = {r["id"]: r for r in CITIES}

PNAD_SM3 = [v["pct"] for v in PNAD["renda_domiciliar_16_mais"].values()]
PNAD_BRL5 = [v["pct"] for v in PNAD["renda_brl_abril_2026"].values()]
SM3_LABELS = list(PNAD["renda_domiciliar_16_mais"].keys())
BRL5_LABELS = list(PNAD["renda_brl_abril_2026"].keys())

# ------------------------------------------------------------- transcrições
# Cada bloco cita página e pergunta. Valores em % da coluna.
ATLAS = {
    "fonte": "Atlas/Estadão, campo 26 a 31/08/2026, n = 1.810, SP-06964/2026",
    "pesos_renda": [13.0, 12.7, 23.9, 30.7, 19.8],  # p. 5, perfil da amostra
    "gov1": {
        "pagina": 10,
        "publicado": {"Tarcísio": 51.1, "Haddad": 39.9},
        "renda": {
            "Tarcísio": [64.1, 51.7, 53.8, 53.0, 35.4],
            "Haddad": [10.0, 41.5, 34.0, 45.7, 55.6],
        },
    },
    "gov2": {
        "pagina": 14,
        "publicado": {"Tarcísio": 53.2, "Haddad": 42.6},
        "renda": {
            "Tarcísio": [68.0, 54.5, 55.2, 54.9, 36.5],
            "Haddad": [27.9, 43.4, 37.2, 44.5, 56.4],
        },
    },
    "pres1": {
        "pagina": 18,
        "publicado": {"Flávio": 39.9, "Lula": 36.0},
        "renda": {
            "Flávio": [59.7, 47.8, 41.8, 44.6, 11.5],
            "Lula": [9.2, 40.6, 27.7, 45.5, 44.6],
        },
    },
    "pres2": {
        "pagina": 23,
        "publicado": {"Flávio": 46.8, "Lula": 43.3},
        "renda": {
            "Flávio": [65.7, 49.4, 47.5, 48.2, 28.5],
            "Lula": [27.9, 42.4, 41.3, 46.0, 53.5],
        },
    },
}
QUAEST = {
    "fonte": "Genial/Quaest, campo 21 a 24/08/2026, n = 1.800, SP-06946/2026",
    "pesos_renda": [19, 44, 37],  # p. 9, bases das colunas de renda
    "gov1": {
        "pagina": 9,
        "publicado": {"Tarcísio": 40, "Haddad": 27},
        "renda": {"Tarcísio": [25, 40, 50], "Haddad": [31, 25, 28]},
    },
    "gov2": {
        "pagina": 24,
        "publicado": {"Tarcísio": 47, "Haddad": 30},
        "renda": {"Tarcísio": [30, 47, 54], "Haddad": [38, 28, 29]},
    },
    "pres1": {
        "pagina": 79,
        "publicado": {"Flávio": 30, "Lula": 29},
        "renda": {"Flávio": [22, 32, 38], "Lula": [36, 29, 27]},
        "nota": "Cenário II, sem Marçal. Flávio recompõe em 32,3 contra 30 publicado: resíduo acima de 1 pp, registrado como controle reprovado.",
    },
}
DATAFOLHA = {
    "fonte": "Datafolha, campo 18 e 19/08/2026, n = 1.610, SP-01806/2026",
    "pesos_renda": [609, 689, 257],  # p. 27, base ponderada; 55 sem classificação
    "gov1": {
        "pagina": 27,
        "publicado": {"Tarcísio": 45, "Haddad": 27},
        "renda": {"Tarcísio": [37, 49, 50], "Haddad": [24, 29, 34]},
    },
    "gov2": {
        "pagina": 33,
        "publicado": {"Tarcísio": 54, "Haddad": 35},
        "renda": {"Tarcísio": [50, 57, 58], "Haddad": [35, 34, 38]},
    },
}
REALTIME = {
    "fonte": "Real Time Big Data, campo 19 a 22/08/2026, n = 2.000, telefone, SP-01347/2026 e BR-06537/2026",
    "pesos_renda": [31, 39, 30],  # perfil da amostra, p. 3 dos dois laudos
    "gov1": {
        "pagina": 10,
        "publicado": {"Tarcísio": 52, "Haddad": 35},
        "renda": {"Tarcísio": [42, 52, 62], "Haddad": [46, 35, 23]},
    },
    "pres1": {
        "pagina": 10,
        "publicado": {"Flávio": 38, "Lula": 33},
        "renda": {"Flávio": [34, 40, 40], "Lula": [43, 30, 27]},
        "nota": "Laudo presidencial separado (BR-06537/2026), mesma amostra e mesmo perfil. Cenário com Marçal (7%).",
    },
}
SERIE_QUAEST_GOV2 = {
    "fonte": "Genial/Quaest, p. 20 e 24: 2º turno para governador por renda em três ondas",
    "pesos_renda": [19, 44, 37],
    "nota": "As bases por faixa só estão publicadas na onda de agosto; aplicadas às três ondas, recompõem os placares de abril e julho com resíduo máximo de 0,3 pp.",
    "ondas": [
        {
            "onda": "abr/26",
            "publicado": {"Tarcísio": 49, "Haddad": 32},
            "renda": {"Tarcísio": [35, 50, 55], "Haddad": [35, 32, 30]},
        },
        {
            "onda": "jul/26",
            "publicado": {"Tarcísio": 48, "Haddad": 32},
            "renda": {"Tarcísio": [35, 51, 52], "Haddad": [39, 30, 30]},
        },
        {
            "onda": "ago/26",
            "publicado": {"Tarcísio": 47, "Haddad": 30},
            "renda": {"Tarcísio": [30, 47, 54], "Haddad": [38, 28, 29]},
        },
    ],
}
SERIE_PUBLICADA = {
    "datafolha_gov2": {
        "fonte": "Datafolha, p. 10 do relatório de agosto",
        "ondas": [("mar/26", 52, 37), ("jul/26", 53, 37), ("ago/26", 54, 35)],
    },
    "datafolha_gov1": {
        "fonte": "Datafolha, p. 8 do relatório de agosto; março e julho pelo Poder360",
        "ondas": [("mar/26", 44, 31), ("jul/26", 46, 30), ("ago/26", 45, 27)],
    },
    "realtime_gov1": {
        "fonte": "Real Time Big Data, junho (Exame, 16/06/2026) e agosto (laudo, p. 7)",
        "ondas": [("jun/26", 46, 33), ("ago/26", 52, 35)],
    },
    "quaest_gov2": {
        "fonte": "Genial/Quaest, p. 20",
        "ondas": [("abr/26", 49, 32), ("jul/26", 48, 32), ("ago/26", 47, 30)],
    },
}
# Vão regional medido pela Atlas (p. 14 e 23), por região do próprio instituto.
ATLAS_REGIAO = {
    "capital": {"rotulo": "Cidade de São Paulo", "tarcisio": 48.9, "flavio": 43.7},
    "rm_santos": {
        "rotulo": "RM de São Paulo e Santos",
        "tarcisio": 50.3,
        "flavio": 40.4,
    },
    "campinas_sjc": {
        "rotulo": "Campinas e São José dos Campos",
        "tarcisio": 58.0,
        "flavio": 52.8,
    },
    "norte": {
        "rotulo": "Rio Preto, Ribeirão Preto, Araraquara e Bauru",
        "tarcisio": 48.4,
        "flavio": 42.5,
    },
    "oeste": {
        "rotulo": "Presidente Prudente, Marília, Sorocaba e Araçatuba",
        "tarcisio": 60.8,
        "flavio": 55.3,
    },
}
REGIAO_IBGE_PARA_ATLAS = {
    "São Paulo": "rm_santos",
    "Campinas": "campinas_sjc",
    "São José dos Campos": "campinas_sjc",
    "São José do Rio Preto": "norte",
    "Ribeirão Preto": "norte",
    "Araraquara": "norte",
    "Bauru": "norte",
    "Presidente Prudente": "oeste",
    "Marília": "oeste",
    "Sorocaba": "oeste",
    "Araçatuba": "oeste",
}
CAPITAL_ID = "3550308"
CARRIER_ROWS: dict = {}


def coeficientes_estoque():
    """Fatia de cada eleitorado de 2022 que vota Tarcísio e não vota Flávio (Atlas p. 14 e 23)."""
    out = {}
    for g, rotulo, gov, pres in SEGMENTOS:
        if g == "Voto para governador em 2022, 1º turno" and rotulo in (
            "Tarcísio",
            "Haddad",
            "Rodrigo Garcia",
        ):
            out[rotulo] = round((gov[0] - pres[1]) / 100, 4)
        if g == "Voto para governador em 2022, 2º turno" and rotulo in (
            "Tarcísio",
            "Haddad",
        ):
            out[rotulo + " 2T"] = round((gov[0] - pres[1]) / 100, 4)
    return out


# Perfil de renda declarado no próprio relatório do Datafolha (p. 24):
# 38% até 2 SM, 20% de 2 a 3, 23% de 3 a 5, 12% de 5 a 10, 3% de 10 a 20,
# 1% de 20 a 50, 0% acima de 50, 2% recusa, 1% não sabe.

# Atlas, p. 14 (governo 2º turno) e p. 23 (Presidência 2º turno, Lula × Flávio):
# mesma amostra, dois cenários. T, H, BN, NS = Tarcísio, Haddad, branco/nulo, não sei.
# L, F, NE = Lula, Flávio, branco/nulo/não sei.
SEGMENTOS = [
    # grupo, rótulo, [T,H,BN,NS], [L,F,NE]
    ("Sexo", "Homens", [58.1, 35.9, 4.5, 1.5], [35.5, 48.6, 16.0]),
    ("Sexo", "Mulheres", [48.7, 48.6, 1.1, 1.7], [50.4, 44.9, 4.7]),
    ("Idade", "16 a 24", [18.2, 71.3, 10.2, 0.3], [71.9, 14.6, 13.5]),
    ("Idade", "25 a 34", [50.7, 44.8, 4.6, 0.0], [45.3, 39.6, 15.1]),
    ("Idade", "35 a 44", [71.6, 22.7, 0.4, 5.3], [23.8, 60.9, 15.4]),
    ("Idade", "45 a 59", [48.9, 49.9, 1.2, 0.0], [50.0, 43.9, 6.0]),
    ("Idade", "60 ou mais", [61.0, 36.1, 0.8, 2.1], [37.4, 58.4, 4.3]),
    ("Escolaridade", "Superior", [32.5, 61.7, 3.0, 2.8], [62.6, 21.6, 15.9]),
    ("Escolaridade", "Fundamental e médio", [62.8, 33.7, 2.5, 1.0], [34.3, 58.6, 7.1]),
    ("Renda", "Até R$ 2 mil", [68.0, 27.9, 3.5, 0.5], [27.9, 65.7, 6.3]),
    ("Renda", "R$ 2 a 3 mil", [54.5, 43.4, 1.9, 0.2], [42.4, 49.4, 8.1]),
    ("Renda", "R$ 3 a 5 mil", [55.2, 37.2, 1.8, 5.7], [41.3, 47.5, 11.2]),
    ("Renda", "R$ 5 a 10 mil", [54.9, 44.5, 0.6, 0.0], [46.0, 48.2, 5.9]),
    ("Renda", "Acima de R$ 10 mil", [36.5, 56.4, 6.9, 0.2], [53.5, 28.5, 18.0]),
    ("Religião", "Católicos", [60.3, 37.7, 0.7, 1.3], [37.5, 54.1, 8.4]),
    ("Religião", "Evangélicos", [65.2, 29.9, 1.5, 3.3], [32.2, 57.7, 10.1]),
    ("Religião", "Outra religião", [27.9, 69.7, 0.3, 2.1], [64.7, 24.3, 11.0]),
    ("Religião", "Crentes sem religião", [47.4, 45.3, 7.3, 0.0], [51.3, 32.3, 16.4]),
    ("Religião", "Agnósticos e ateus", [17.7, 69.0, 13.4, 0.0], [77.3, 7.7, 15.0]),
    ("Região", "Campinas e SJC", [58.0, 35.8, 4.0, 2.3], [37.3, 52.8, 10.0]),
    ("Região", "Cidade de São Paulo", [48.9, 48.4, 2.7, 0.0], [50.3, 43.7, 6.0]),
    (
        "Região",
        "Rio Preto, Ribeirão e Bauru",
        [48.4, 42.4, 1.8, 7.4],
        [38.7, 42.5, 18.8],
    ),
    (
        "Região",
        "Prudente, Marília e Sorocaba",
        [60.8, 34.5, 4.7, 0.0],
        [34.8, 55.3, 9.8],
    ),
    ("Região", "RM de SP e Santos", [50.3, 48.9, 0.7, 0.0], [51.2, 40.4, 8.4]),
    (
        "Voto para governador em 2022, 1º turno",
        "Tarcísio",
        [99.1, 0.5, 0.3, 0.1],
        [0.7, 94.4, 4.9],
    ),
    (
        "Voto para governador em 2022, 1º turno",
        "Haddad",
        [2.0, 97.9, 0.1, 0.0],
        [98.7, 0.2, 1.1],
    ),
    (
        "Voto para governador em 2022, 1º turno",
        "Rodrigo Garcia",
        [36.5, 52.9, 5.8, 4.8],
        [52.3, 25.0, 22.7],
    ),
    (
        "Voto para governador em 2022, 1º turno",
        "Branco ou nulo",
        [7.1, 40.3, 34.3, 18.3],
        [40.3, 0.4, 59.3],
    ),
    (
        "Voto para governador em 2022, 1º turno",
        "Não votou",
        [47.8, 49.2, 2.8, 0.2],
        [48.3, 31.5, 20.2],
    ),
    (
        "Voto para governador em 2022, 2º turno",
        "Tarcísio",
        [97.0, 2.7, 0.2, 0.0],
        [2.3, 90.7, 7.0],
    ),
    (
        "Voto para governador em 2022, 2º turno",
        "Haddad",
        [3.2, 95.0, 1.3, 0.5],
        [96.8, 0.6, 2.6],
    ),
    (
        "Voto para governador em 2022, 2º turno",
        "Branco ou nulo",
        [22.9, 6.9, 45.4, 24.8],
        [3.1, 0.4, 96.5],
    ),
    (
        "Voto para governador em 2022, 2º turno",
        "Não votou",
        [39.0, 54.8, 2.7, 3.6],
        [57.3, 26.7, 16.0],
    ),
    (
        "Voto para presidente em 2022, 2º turno",
        "Lula",
        [4.8, 91.7, 1.2, 2.3],
        [95.5, 0.8, 3.7],
    ),
    (
        "Voto para presidente em 2022, 2º turno",
        "Bolsonaro",
        [98.0, 0.4, 0.1, 1.5],
        [0.0, 95.1, 4.9],
    ),
    (
        "Voto para presidente em 2022, 2º turno",
        "Branco ou nulo",
        [56.2, 13.9, 29.4, 0.5],
        [8.5, 4.3, 87.2],
    ),
    (
        "Voto para presidente em 2022, 2º turno",
        "Não votou",
        [38.8, 53.8, 7.3, 0.2],
        [51.8, 30.0, 18.2],
    ),
    ("Ideologia declarada", "Bolsonaristas", [99.9, 0.0, 0.1, 0.0], [0.0, 97.8, 2.2]),
    ("Ideologia declarada", "Antipetistas", [99.2, 0.0, 0.7, 0.0], [0.0, 98.9, 1.1]),
    (
        "Ideologia declarada",
        "Antipetistas e antibolsonaristas",
        [51.9, 37.3, 10.3, 0.5],
        [36.6, 8.6, 54.9],
    ),
    (
        "Ideologia declarada",
        "Antibolsonaristas",
        [1.1, 96.0, 2.0, 1.0],
        [97.3, 0.9, 1.8],
    ),
    ("Ideologia declarada", "Petistas", [3.0, 96.9, 0.1, 0.0], [100.0, 0.0, 0.0]),
    (
        "Ideologia declarada",
        "Nem um nem outro",
        [36.4, 52.6, 3.4, 7.6],
        [47.4, 30.0, 22.6],
    ),
]

ESTOQUE = coeficientes_estoque()

# Atlas p. 19: Presidência 1º turno 2026 por voto para governador em 2022 (2º turno).
ATLAS_P19 = {
    "Tarcísio": {
        "Flávio": 78.8,
        "Lula": 0.6,
        "Cury": 6.5,
        "Renan": 7.9,
        "Zema": 3.4,
        "Caiado": 2.4,
        "Outros": 0.1,
        "Não escolha": 0.3,
    },
    "Haddad": {
        "Flávio": 0.0,
        "Lula": 88.3,
        "Cury": 6.1,
        "Renan": 0.9,
        "Zema": 0.0,
        "Caiado": 0.7,
        "Outros": 2.6,
        "Não escolha": 1.4,
    },
    "Branco ou nulo": {
        "Flávio": 0.4,
        "Lula": 2.6,
        "Cury": 37.1,
        "Renan": 24.3,
        "Zema": 0.0,
        "Caiado": 0.1,
        "Outros": 14.0,
        "Não escolha": 21.5,
    },
    "Não votou": {
        "Flávio": 19.2,
        "Lula": 34.1,
        "Cury": 13.3,
        "Renan": 15.2,
        "Zema": 0.0,
        "Caiado": 0.7,
        "Outros": 7.5,
        "Não escolha": 10.0,
    },
}
ATLAS_P19_GOV1 = {
    "Tarcísio": {
        "Flávio": 85.1,
        "Lula": 0.5,
        "Cury": 4.8,
        "Renan": 6.5,
        "Zema": 1.6,
        "Caiado": 0.9,
        "Não escolha": 0.4,
    },
    "Haddad": {
        "Flávio": 0.0,
        "Lula": 95.2,
        "Cury": 1.7,
        "Renan": 0.1,
        "Zema": 0.0,
        "Caiado": 0.8,
        "Não escolha": 0.1,
    },
    "Rodrigo Garcia": {
        "Flávio": 11.0,
        "Lula": 27.0,
        "Cury": 31.9,
        "Renan": 6.7,
        "Zema": 8.2,
        "Caiado": 6.8,
        "Não escolha": 8.5,
    },
    "Não votou": {
        "Flávio": 22.9,
        "Lula": 35.0,
        "Cury": 7.0,
        "Renan": 18.4,
        "Zema": 0.0,
        "Caiado": 0.9,
        "Não escolha": 7.6,
    },
}

# Indicadores estratégicos transcritos, com página.
ESTRATEGIA = {
    "atlas": {
        "aprovacao": {
            "pagina": 26,
            "Lula": [39, 4, 58],
            "Tarcísio": [52, 6, 42],
            "Prefeito da cidade": [38, 9, 53],
        },
        "avaliacao": {"pagina": 28, "Lula": [31, 15, 54], "Tarcísio": [48, 17, 36]},
        "reeleicao_tarcisio": {
            "pagina": 30,
            "merece": 52.4,
            "nao_merece": 42.4,
            "nao_sei": 5.3,
        },
        "imagem": {
            "pagina": 37,
            "valores": {
                "Tarcísio": [52, 6, 42],
                "Jair Bolsonaro": [46, 2, 52],
                "Guilherme Derrite": [43, 20, 36],
                "Marina Silva": [43, 4, 53],
                "Flávio Bolsonaro": [42, 3, 55],
                "Simone Tebet": [40, 8, 53],
                "Lula": [38, 3, 60],
                "Fernando Haddad": [38, 4, 59],
                "Eduardo Bolsonaro": [37, 5, 57],
                "Geraldo Alckmin": [37, 6, 57],
                "Ronaldo Caiado": [33, 20, 47],
                "Márcio França": [32, 26, 42],
                "Ricardo Salles": [32, 27, 41],
                "Ricardo Nunes": [31, 20, 49],
                "Zema": [31, 17, 53],
                "André do Prado": [31, 37, 32],
                "Renan Santos": [17, 16, 68],
            },
        },
        "rejeicao": {
            "pagina": 39,
            "valores": {
                "Lula": 51.8,
                "Flávio Bolsonaro": 48.3,
                "Renan Santos": 48.2,
                "Jair Bolsonaro": 45.0,
                "Fernando Haddad": 44.0,
                "Marina Silva": 44.0,
                "Geraldo Alckmin": 41.1,
                "Simone Tebet": 39.4,
                "Ricardo Nunes": 34.6,
                "Tarcísio": 34.5,
                "Ricardo Salles": 32.3,
                "Ronaldo Caiado": 32.2,
                "Márcio França": 31.1,
                "André do Prado": 30.3,
                "Guilherme Derrite": 30.2,
            },
        },
        "problemas": {
            "pagina": 41,
            "valores": {
                "Criminalidade": 59.4,
                "Qualidade da educação": 35.9,
                "Acesso à saúde": 29.2,
                "Violência contra a mulher": 19.9,
                "Carga tributária": 17.3,
                "Inflação e preços": 15.4,
                "Corrupção": 14.9,
                "Pobreza e desigualdade": 14.3,
                "Violência policial": 12.0,
                "Mobilidade": 11.4,
                "Habitação": 9.2,
                "Saneamento": 8.5,
                "Desemprego": 7.2,
                "Meio ambiente": 4.3,
                "Burocracia": 4.1,
                "Situação financeira do estado": 2.0,
                "Infraestrutura": 1.5,
            },
        },
        "cenarios_2t": {
            "pagina": 21,
            "Flávio": [46.8, 43.3, 9.9],
            "Caiado": [45.4, 41.1, 13.4],
            "Zema": [43.8, 42.7, 13.5],
            "Renan": [33.5, 43.1, 23.4],
        },
    },
    "quaest": {
        "potencial": {
            "pagina": 29,
            "Tarcísio": [50, 13, 37, 13],
            "Haddad": [34, 7, 59, -25],
        },
        "alianca_preferida": {
            "pagina": 33,
            "Independente": 37,
            "Aliado de Flávio Bolsonaro": 33,
            "Aliado de Lula": 26,
            "Não sabe": 4,
        },
        "endosso": {
            "pagina": 34,
            "Flávio Bolsonaro": [24, 45, 29, 2],
            "Lula": [20, 41, 37, 2],
        },
        "aprovacao_tarcisio": {
            "pagina": 36,
            "serie": [
                ("abr/24", 63, 29),
                ("dez/24", 62, 26),
                ("fev/25", 61, 28),
                ("ago/25", 60, 29),
                ("abr/26", 54, 29),
                ("jul/26", 55, 29),
                ("ago/26", 56, 31),
            ],
        },
        "gov2_total": {
            "pagina": 20,
            "Tarcísio": 47,
            "Haddad": 30,
            "Indecisos": 11,
            "Branco ou nulo": 12,
        },
        "pres1_cenario2": {
            "pagina": 75,
            "Flávio": 30,
            "Lula": 29,
            "Caiado": 4,
            "Zema": 3,
            "Renan": 3,
            "Cury": 2,
            "Outros": 4,
            "Indecisos": 13,
            "Branco ou nulo": 12,
        },
        "problemas": {
            "pagina": 105,
            "Violência": 34,
            "Saúde": 22,
            "Economia": 8,
            "Educação": 6,
            "Corrupção": 4,
            "Desemprego": 4,
            "Pobreza e desigualdade": 3,
            "Enchentes": 1,
            "Infraestrutura": 1,
            "Outros": 9,
            "Não sabe": 8,
        },
    },
    "datafolha": {
        "gov2_total": {
            "pagina": 6,
            "Tarcísio": 54,
            "Haddad": 35,
            "Branco ou nulo": 9,
            "Indecisos": 2,
        },
        "pres2_total": {
            "fonte": "Poder360, 22/08/2026, sobre o Datafolha SP",
            "Flávio": 47,
            "Lula": 42,
            "Branco ou nulo": 9,
            "Indecisos": 1,
        },
        "pres1_total": {
            "fonte": "Poder360, 22/08/2026",
            "Flávio": 37,
            "Lula": 33,
            "Renan": 5,
            "Caiado": 4,
            "Zema": 3,
            "Cury": 3,
            "Samara": 2,
            "Branco ou nulo": 7,
            "Indecisos": 3,
        },
        "senado_espontanea_indefinidos": {"pagina": 6, "valor": 79},
    },
}


# ------------------------------------------------------------- reponderação
def recompose(values, weights):
    return sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)


def reweight_block(inst, key, pnad):
    block = inst[key]
    weights = inst["pesos_renda"]
    out = {"pagina": block["pagina"], "candidatos": {}}
    for name, values in block["renda"].items():
        rec = recompose(values, weights)
        rew = recompose(values, pnad)
        pub = block["publicado"][name]
        out["candidatos"][name] = {
            "publicado": pub,
            "recomposto": round(rec, 2),
            "residuo_pp": round(rec - pub, 2),
            "reponderado": round(rew, 2),
            "sensibilidade": round(pub + (rew - rec), 2),
            "delta_pp": round(rew - rec, 2),
            "por_faixa": values,
        }
    names = list(block["renda"])
    a, b = (out["candidatos"][n] for n in names)
    out["diferenca_publicada"] = round(a["publicado"] - b["publicado"], 2)
    out["diferenca_sensibilidade"] = round(a["sensibilidade"] - b["sensibilidade"], 2)
    if "nota" in block:
        out["nota"] = block["nota"]
    return out


def reponderacao():
    return {
        "metodo": (
            "Sensibilidade de uma margem: para cada faixa de renda, o voto publicado na "
            "faixa é mantido e só o peso da faixa é trocado pelo peso da PNADC anual 2025 "
            "(pessoas 16+, renda domiciliar, preços de abril de 2026, SM de R$ 1.621). "
            "O resultado é publicado como publicado + (reponderado - recomposto), para "
            "não herdar o resíduo de arredondamento. A ponderação do instituto é conjunta "
            "e não publicada; isto é sensibilidade, nunca voto corrigido."
        ),
        "pnad_sm3": dict(zip(SM3_LABELS, PNAD_SM3, strict=True)),
        "pnad_brl5": dict(zip(BRL5_LABELS, PNAD_BRL5, strict=True)),
        "perfis": {
            "PNAD 2025 (16+)": PNAD_SM3,
            "Datafolha": [round(100 * w / 1610, 2) for w in DATAFOLHA["pesos_renda"]],
            "Quaest": QUAEST["pesos_renda"],
            "Real Time": REALTIME["pesos_renda"],
        },
        "perfil_atlas_brl5": {
            "Atlas": ATLAS["pesos_renda"],
            "PNAD 2025 (16+)": PNAD_BRL5,
        },
        "datafolha": {
            "fonte": DATAFOLHA["fonte"],
            "sem_renda_classificada": 55,
            "gov1": reweight_block(DATAFOLHA, "gov1", PNAD_SM3),
            "gov2": reweight_block(DATAFOLHA, "gov2", PNAD_SM3),
        },
        "quaest": {
            "fonte": QUAEST["fonte"],
            "gov1": reweight_block(QUAEST, "gov1", PNAD_SM3),
            "gov2": reweight_block(QUAEST, "gov2", PNAD_SM3),
            "pres1": reweight_block(QUAEST, "pres1", PNAD_SM3),
        },
        "atlas": {
            "fonte": ATLAS["fonte"],
            "gov1": reweight_block(ATLAS, "gov1", PNAD_BRL5),
            "gov2": reweight_block(ATLAS, "gov2", PNAD_BRL5),
            "pres1": reweight_block(ATLAS, "pres1", PNAD_BRL5),
            "pres2": reweight_block(ATLAS, "pres2", PNAD_BRL5),
        },
        "realtime": {
            "fonte": REALTIME["fonte"],
            "gov1": reweight_block(REALTIME, "gov1", PNAD_SM3),
            "pres1": reweight_block(REALTIME, "pres1", PNAD_SM3),
        },
        "serie": serie_reponderada(),
    }


def serie_reponderada():
    """Série do 2º turno estadual: Quaest reponderada em três ondas; Datafolha com um ponto."""
    quaest = []
    for onda in SERIE_QUAEST_GOV2["ondas"]:
        inst = {
            "pesos_renda": SERIE_QUAEST_GOV2["pesos_renda"],
            "x": {"pagina": 24, "publicado": onda["publicado"], "renda": onda["renda"]},
        }
        r = reweight_block(inst, "x", PNAD_SM3)
        quaest.append(
            {"onda": onda["onda"], **{k: v for k, v in r.items() if k != "pagina"}}
        )
    df = reweight_block(DATAFOLHA, "gov2", PNAD_SM3)
    return {
        "quaest_gov2": {
            "fonte": SERIE_QUAEST_GOV2["fonte"],
            "nota": SERIE_QUAEST_GOV2["nota"],
            "ondas": quaest,
        },
        "datafolha_gov2": {
            "fonte": SERIE_PUBLICADA["datafolha_gov2"]["fonte"],
            "nota": "O cruzamento de renda só existe no relatório completo de agosto; os de março e julho não estão públicos com anexo, por isso a série reponderada do Datafolha tem um ponto.",
            "ondas": [
                {
                    "onda": o,
                    "publicado": {"Tarcísio": t, "Haddad": h},
                    "diferenca_publicada": t - h,
                    "diferenca_sensibilidade": (
                        df["diferenca_sensibilidade"] if o == "ago/26" else None
                    ),
                }
                for o, t, h in SERIE_PUBLICADA["datafolha_gov2"]["ondas"]
            ],
        },
        "publicadas": SERIE_PUBLICADA,
    }


# ---------------------------------------------------------------------- IPF
def ipf(prior, rows, cols, iters=3000):
    m = prior * rows[:, None]
    for _ in range(iters):
        m *= (rows / np.maximum(m.sum(axis=1), 1e-12))[:, None]
        m *= (cols / np.maximum(m.sum(axis=0), 1e-12))[None, :]
    return m


def flow(name, fonte, origem, destino, prior, prior_nota, tipo):
    rows = np.array(list(origem.values()), dtype=float)
    cols = np.array(list(destino.values()), dtype=float)
    rows_scaled = rows * cols.sum() / rows.sum()
    prior = np.array(prior, dtype=float)
    m = ipf(prior, rows_scaled, cols)
    src, dst = list(origem), list(destino)
    matrix = {
        s: {d: round(float(m[i, j]), 2) for j, d in enumerate(dst)}
        for i, s in enumerate(src)
    }
    t = src[0]
    t_total = float(m[0].sum())
    right = dst[0]
    left = dst[1]
    return {
        "nome": name,
        "fonte": fonte,
        "tipo": tipo,
        "origem": origem,
        "destino": destino,
        "matriz": matrix,
        "prior": {
            s: dict(zip(dst, map(float, prior[i]), strict=True))
            for i, s in enumerate(src)
        },
        "prior_nota": prior_nota,
        "robusto": {
            "diferenca_tarcisio_menos_direita_pp": round(origem[t] - destino[right], 2),
            "diferenca_esquerda_menos_haddad_pp": round(
                destino[left] - origem[src[1]], 2
            ),
            "variacao_nao_escolha_pp": round(destino[dst[-1]] - origem[src[-1]], 2),
        },
        "estimado": {
            "tarcisio_para_direita_pct": round(100 * float(m[0, 0]) / t_total, 1),
            "tarcisio_para_esquerda_pct": round(100 * float(m[0, 1]) / t_total, 1),
            "tarcisio_para_nao_escolha_pct": round(100 * float(m[0, -1]) / t_total, 1),
            "tarcisio_para_esquerda_pontos": round(float(m[0, 1]), 2),
            "tarcisio_para_nao_escolha_pontos": round(float(m[0, -1]), 2),
            "haddad_para_esquerda_pct": round(
                100 * float(m[1, 1]) / float(m[1].sum()), 1
            ),
        },
    }


def fluxos():
    p23 = {
        r[1]: r[3]
        for r in SEGMENTOS
        if r[0] == "Voto para governador em 2022, 2º turno"
    }

    # Prior empírica: Atlas p. 23, voto de 2º turno para governador em 2022 cruzado com o
    # 2º turno presidencial de 2026 (Lula × Flávio). Aplicada à intenção de 2026 como prior.
    def row(k):
        lula, flavio, ne = p23[k]
        return [flavio / 100, lula / 100, ne / 100]

    nao_escolha = [
        (row("Branco ou nulo")[i] + row("Não votou")[i]) / 2 for i in range(3)
    ]
    prior_2t = [row("Tarcísio"), row("Haddad"), nao_escolha]
    nota_2t = (
        "Prior empírica: Atlas p. 23, voto de 2022 para governador (2º turno) cruzado com o "
        "2º turno presidencial de 2026. Tarcísio 2022: Flávio 90,7, Lula 2,3, não escolha 7,0. "
        "Haddad 2022: Lula 96,8, Flávio 0,6, não escolha 2,6. Linha da não escolha: média de "
        "brancos/nulos e não votantes de 2022. O IPF ajusta essas proporções até fechar as "
        "margens publicadas de cada instituto."
    )
    out = [
        flow(
            "Datafolha: governo 2º turno para Presidência 2º turno",
            "Datafolha, p. 6 (governo) e Poder360 de 22/08/2026 (Presidência), campo 18 e 19/08",
            {"Tarcísio": 54, "Haddad": 35, "Não escolha": 11},
            {"Flávio": 47, "Lula": 42, "Não escolha": 10},
            prior_2t,
            nota_2t,
            "2T para 2T",
        ),
        flow(
            "Atlas: governo 2º turno para Presidência 2º turno",
            "Atlas/Estadão, p. 12 e 21, campo 26 a 31/08",
            {"Tarcísio": 53.2, "Haddad": 42.6, "Não escolha": 4.2},
            {"Flávio": 46.8, "Lula": 43.3, "Não escolha": 9.9},
            prior_2t,
            nota_2t,
            "2T para 2T",
        ),
    ]
    out.append(
        flow(
            "Real Time: governo 2º turno para Presidência 2º turno",
            "Real Time Big Data, laudo de governo p. 12 e laudo presidencial p. 12, campo 19 a 22/08, telefone",
            {"Tarcísio": 54, "Haddad": 36, "Não escolha": 10},
            {"Flávio": 44, "Lula": 49, "Não escolha": 7},
            prior_2t,
            nota_2t,
            "2T para 2T",
        )
    )
    # Quaest não publica 2º turno presidencial: o destino é o 1º turno, cenário II.
    cols_q = [
        "Flávio",
        "Lula",
        "Caiado",
        "Zema",
        "Renan",
        "Cury",
        "Outros",
        "Não escolha",
    ]

    def row19(k):
        d = ATLAS_P19[k]
        v = [d[c] for c in cols_q]
        s = sum(v)
        return [x / s for x in v]

    ne19 = [
        (row19("Branco ou nulo")[i] + row19("Não votou")[i]) / 2
        for i in range(len(cols_q))
    ]
    q = ESTRATEGIA["quaest"]["pres1_cenario2"]
    out.append(
        flow(
            "Quaest: governo 2º turno para Presidência 1º turno (cenário II)",
            "Genial/Quaest, p. 20 e 75, campo 21 a 24/08",
            {"Tarcísio": 47, "Haddad": 30, "Não escolha": 23},
            {
                c: q[c]
                for c in ["Flávio", "Lula", "Caiado", "Zema", "Renan", "Cury", "Outros"]
            }
            | {"Não escolha": q["Indecisos"] + q["Branco ou nulo"]},
            [row19("Tarcísio"), row19("Haddad"), ne19],
            (
                "Prior empírica: Atlas p. 19, voto de 2022 para governador (2º turno) cruzado com "
                "o 1º turno presidencial de 2026. Tarcísio 2022: Flávio 78,8, Cury 6,5, Renan 7,9, "
                "Zema 3,4, Caiado 2,4, Lula 0,6. Haddad 2022: Lula 88,3, Cury 6,1. A Quaest não "
                "publica 2º turno presidencial no relatório estadual; por isso o destino é o 1º turno."
            ),
            "2T para 1T",
        )
    )
    return out


# ------------------------------------------------------------- o vão
def vao():
    linhas = []
    for grupo, rotulo, gov, pres in SEGMENTOS:
        t, h, bn, ns = gov
        lula, flavio, ne = pres
        linhas.append(
            {
                "grupo": grupo,
                "segmento": rotulo,
                "tarcisio": t,
                "haddad": h,
                "nao_escolha_gov": round(bn + ns, 1),
                "flavio": flavio,
                "lula": lula,
                "nao_escolha_pres": ne,
                "vao_tarcisio_flavio": round(t - flavio, 1),
                "ganho_lula_sobre_haddad": round(lula - h, 1),
                "salto_nao_escolha": round(ne - bn - ns, 1),
            }
        )
    total = {"tarcisio": 53.2, "flavio": 46.8, "haddad": 42.6, "lula": 43.3}
    total["vao"] = round(total["tarcisio"] - total["flavio"], 1)
    return {
        "fonte": "Atlas/Estadão p. 14 e p. 23: mesma amostra, dois cenários de 2º turno",
        "definicao": (
            "Vão = voto em Tarcísio no 2º turno estadual menos voto em Flávio no 2º turno "
            "presidencial, dentro do mesmo recorte e da mesma amostra. Mede quanto do voto "
            "do governador ainda não é voto do candidato a presidente. É teto endereçável, "
            "não previsão: preferir Tarcísio não é estar disponível para Flávio."
        ),
        "total": total,
        "segmentos": linhas,
        "p19_gov2022_2t": ATLAS_P19,
        "p19_gov2022_1t": ATLAS_P19_GOV1,
    }


# ------------------------------------------------------------- carregadores
def norm(s):
    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper(),
    ).strip()
    return {
        "SAO LUIS DO PARAITINGA": "SAO LUIZ DO PARAITINGA",
        "EMBU": "EMBU DAS ARTES",
    }.get(text, text)


CHAVES = [
    ("tarcisio", "GOVERNADOR", "TARCISIO", "Tarcísio", "governador 1º turno"),
    ("garcia", "GOVERNADOR", "RODRIGO GARCIA", "Rodrigo Garcia", "governador 1º turno"),
    ("pontes", "SENADOR", "ASTRONAUTA MARCOS PONTES", "Marcos Pontes", "Senado"),
    (
        "derrite",
        "DEPUTADO FEDERAL",
        "CAPITAO DERRITE",
        "Guilherme Derrite",
        "deputado federal",
    ),
    (
        "salles",
        "DEPUTADO FEDERAL",
        "RICARDO SALLES",
        "Ricardo Salles",
        "deputado federal",
    ),
    (
        "carla",
        "DEPUTADO FEDERAL",
        "CARLA ZAMBELLI",
        "Carla Zambelli",
        "deputado federal",
    ),
    (
        "eduardo",
        "DEPUTADO FEDERAL",
        "EDUARDO BOLSONARO",
        "Eduardo Bolsonaro",
        "deputado federal",
    ),
    (
        "prado",
        "DEPUTADO ESTADUAL",
        "ANDRE DO PRADO",
        "André do Prado",
        "deputado estadual",
    ),
    ("gil", "DEPUTADO ESTADUAL", "GIL DINIZ", "Gil Diniz", "deputado estadual"),
]
INDICES = [
    "tarcisio",
    "pontes",
    "derrite",
    "salles",
    "carla",
    "eduardo",
    "prado",
    "gil",
]
NUCLEO = {
    "PL",
    "PP",
    "REPUBLICANOS",
    "NOVO",
    "UNIAO",
    "UNIÃO",
    "PRD",
    "PODE",
    "PATRIOTA",
    "PRTB",
    "DC",
}
DIREITA_AMPLA = NUCLEO | {
    "PSDB",
    "PSD",
    "MDB",
    "AVANTE",
    "SOLIDARIEDADE",
    "PSC",
    "PTB",
    "AGIR",
    "PMB",
    "MOBILIZA",
    "CIDADANIA",
}


def extrai_tse():
    """Votos nominais de 2022 (1º turno) por município para as chaves e perfil dos eleitos."""
    byname = {norm(r["nome"]): r["id"] for r in CITIES}
    votos = defaultdict(lambda: defaultdict(int))  # chave -> id -> votos
    total = defaultdict(lambda: defaultdict(int))  # cargo -> id -> votos nominais
    cand = defaultdict(lambda: defaultdict(int))  # (cargo, sq) -> id -> votos
    info = {}
    chave_por_nome = {(c, n): k for k, c, n, *_ in CHAVES}
    with zipfile.ZipFile(TSE_ZIP) as z:
        member = next(n for n in z.namelist() if n.endswith("_2022_SP.csv"))
        with z.open(member) as raw:
            for row in csv.DictReader(
                io.TextIOWrapper(raw, encoding="latin1"), delimiter=";"
            ):
                if row["NR_TURNO"] != "1":
                    continue
                cargo = row["DS_CARGO"].upper()
                if cargo not in (
                    "GOVERNADOR",
                    "SENADOR",
                    "DEPUTADO FEDERAL",
                    "DEPUTADO ESTADUAL",
                ):
                    continue
                ident = byname[norm(row["NM_MUNICIPIO"])]
                v = int(row["QT_VOTOS_NOMINAIS"])
                total[cargo][ident] += v
                sq = row["SQ_CANDIDATO"]
                cand[(cargo, sq)][ident] += v
                info.setdefault(
                    sq,
                    (
                        row["NM_URNA_CANDIDATO"].strip(),
                        row["SG_PARTIDO"].strip().upper(),
                        row["DS_SIT_TOT_TURNO"].strip(),
                    ),
                )
                k = chave_por_nome.get((cargo, norm(row["NM_URNA_CANDIDATO"])))
                if k:
                    votos[k][ident] += v
    return votos, total, cand, info


def carregadores(corredores_def):
    votos, total, cand, info = extrai_tse()
    cargo_de = {k: c for k, c, *_ in CHAVES}
    estado = {}
    pres1_total = sum(r["2022_PRESIDENTE_1_total"] for r in CITIES)
    bol_state = 100 * sum(r["jair_2022_1"] for r in CITIES) / pres1_total
    estado["bolsonaro_1t"] = round(bol_state, 2)
    for k in [*INDICES, "garcia"]:
        estado[k] = round(
            100 * sum(votos[k].values()) / sum(total[cargo_de[k]].values()), 2
        )
    rows = []
    for r in CITIES:
        i = r["id"]
        bol1 = r["jair_2022_1_pct"]
        base = bol1 / bol_state if bol1 else 0
        d = {
            "id": i,
            "nome": r["nome"],
            "regiao": r["regiao"],
            "eleitorado": r["eleitorado"],
            "bol1": round(bol1, 2),
            "bol2": round(r["jair_2022_2_pct"], 2),
            "tar1": round(r["tarcisio_2022_1_pct"], 2),
            "tar2": round(r["tarcisio_2022_2_pct"], 2),
            "tar1_menos_bol1_pp": round(r["tarcisio_2022_1_pct"] - bol1, 2),
            "tar2_menos_bol2_pp": round(
                r["tarcisio_2022_2_pct"] - r["jair_2022_2_pct"], 2
            ),
            "votos_tarcisio_sem_bolsonaro": round(
                (r["tarcisio_2022_2_pct"] - r["jair_2022_2_pct"])
                / 100
                * r["2022_GOVERNADOR_2_total"]
            ),
            "regiao_atlas": (
                "capital" if i == CAPITAL_ID else REGIAO_IBGE_PARA_ATLAS[r["regiao"]]
            ),
            "garcia1": round(
                100 * votos["garcia"].get(i, 0) / total["GOVERNADOR"][i], 2
            ),
            "margem_pt_2t_pp": round(
                100
                * (r["pt_2022_2"] - r["jair_2022_2"])
                / r["2022_PRESIDENTE_2_total"],
                2,
            ),
            "desloc_18_22_pp": round(r["mudanca_jair_pp"], 2),
            "virada": r["virada"],
            "renda": r["renda"],
        }
        ra = ATLAS_REGIAO[d["regiao_atlas"]]
        d["vao_regional_atlas"] = round(ra["tarcisio"] - ra["flavio"], 1)
        g1 = votos["garcia"].get(i, 0)
        partes = {
            "Tarcísio": ESTOQUE["Tarcísio"] * r["tarcisio_2022_1"],
            "Haddad": ESTOQUE["Haddad"] * r.get("haddad_2022_1", 0),
            "Rodrigo Garcia": ESTOQUE["Rodrigo Garcia"] * g1,
        }
        d["estoque_votos"] = round(sum(partes.values()))
        d["estoque_garcia_votos"] = round(partes["Rodrigo Garcia"])
        d["estoque_pct"] = round(
            100 * sum(partes.values()) / r["2022_GOVERNADOR_1_total"], 2
        )
        e2 = ESTOQUE["Tarcísio 2T"] * r["tarcisio_2022_2"] + ESTOQUE[
            "Haddad 2T"
        ] * r.get("haddad_2022_2", 0)
        d["estoque2t_votos"] = round(e2)
        d["estoque2t_pct"] = round(100 * e2 / r["2022_GOVERNADOR_2_total"], 2)
        for k in INDICES:
            pct = (
                100 * votos[k].get(i, 0) / total[cargo_de[k]][i]
                if total[cargo_de[k]][i]
                else 0
            )
            d[k] = round(pct, 2)
            d["i_" + k] = (
                round(100 * (pct / estado[k]) / base, 1) if base and estado[k] else 0.0
            )
        rows.append(d)
    # perfil territorial dos eleitos de direita para as âncoras por corredor
    membros = {slug: set(ids) for slug, ids in corredores_def.items()}
    perfil = []
    for (cargo, sq), por_cidade in cand.items():
        if cargo not in ("DEPUTADO FEDERAL", "DEPUTADO ESTADUAL"):
            continue
        urna, partido, sit = info[sq]
        if not sit.upper().startswith("ELEITO") or partido not in DIREITA_AMPLA:
            continue
        tot = sum(por_cidade.values())
        if tot < 3000:
            continue
        top = max(por_cidade.items(), key=lambda kv: kv[1])
        conc = {
            slug: round(
                100 * sum(v for i, v in por_cidade.items() if i in ids) / tot, 1
            )
            for slug, ids in membros.items()
        }
        perfil.append(
            {
                "nome": urna,
                "partido": partido,
                "casa": "federal" if cargo == "DEPUTADO FEDERAL" else "estadual",
                "bloco": "nucleo" if partido in NUCLEO else "ampla",
                "votos_sp": tot,
                "cidade_base": CITY[top[0]]["nome"],
                "concentracao": conc,
            }
        )
    perfil.sort(key=lambda p: -p["votos_sp"])
    return estado, rows, perfil, votos, total


# ------------------------------------------------------------- corredores
CORREDORES = [
    (
        "capital",
        "Corredor da Capital",
        "a cidade de São Paulo, 26% do eleitorado",
        ["São Paulo"],
    ),
    (
        "leste",
        "Corredor do ABC, Guarulhos e Alto Tietê",
        "indústria pesada, periferia leste e o berço do PT",
        [
            "São Bernardo do Campo",
            "Santo André",
            "São Caetano do Sul",
            "Diadema",
            "Mauá",
            "Ribeirão Pires",
            "Rio Grande da Serra",
            "Guarulhos",
            "Mogi das Cruzes",
            "Suzano",
            "Itaquaquecetuba",
            "Ferraz de Vasconcelos",
            "Poá",
            "Arujá",
            "Santa Isabel",
            "Guararema",
            "Biritiba Mirim",
            "Salesópolis",
        ],
    ),
    (
        "oeste_metro",
        "Corredor Oeste e Norte da Metrópole",
        "Osasco, Barueri, Guarulhos não: o eixo Castello e o colar norte",
        [
            "Osasco",
            "Barueri",
            "Carapicuíba",
            "Santana de Parnaíba",
            "Cotia",
            "Itapevi",
            "Jandira",
            "Taboão da Serra",
            "Embu das Artes",
            "Itapecerica da Serra",
            "Embu-Guaçu",
            "Vargem Grande Paulista",
            "Pirapora do Bom Jesus",
            "Cajamar",
            "Caieiras",
            "Franco da Rocha",
            "Francisco Morato",
            "Mairiporã",
            "São Lourenço da Serra",
            "Juquitiba",
        ],
    ),
    (
        "porto",
        "Corredor do Porto",
        "Baixada Santista: porto, túnel e periferia litorânea",
        [
            "Santos",
            "São Vicente",
            "Guarujá",
            "Praia Grande",
            "Cubatão",
            "Bertioga",
            "Itanhaém",
            "Mongaguá",
            "Peruíbe",
        ],
    ),
    (
        "tecnologia",
        "Corredor da Tecnologia",
        "Campinas, Jundiaí e Piracicaba: universidade, aeroporto e chão de fábrica",
        [
            "Campinas",
            "Jundiaí",
            "Sumaré",
            "Hortolândia",
            "Indaiatuba",
            "Americana",
            "Santa Bárbara d'Oeste",
            "Piracicaba",
            "Limeira",
            "Paulínia",
            "Valinhos",
            "Vinhedo",
            "Itatiba",
            "Rio Claro",
            "Mogi Guaçu",
            "Mogi Mirim",
            "Várzea Paulista",
            "Campo Limpo Paulista",
            "Itupeva",
            "Louveira",
            "Nova Odessa",
            "Cosmópolis",
            "Artur Nogueira",
            "Monte Mor",
            "Araras",
            "Leme",
            "Bragança Paulista",
            "Atibaia",
            "Amparo",
            "Capivari",
        ],
    ),
    (
        "aeroespacial",
        "Corredor Aeroespacial",
        "Vale do Paraíba e Litoral Norte: Embraer, montadoras e pré-sal",
        [
            "São José dos Campos",
            "Taubaté",
            "Jacareí",
            "Pindamonhangaba",
            "Guaratinguetá",
            "Caçapava",
            "Lorena",
            "Caraguatatuba",
            "Ubatuba",
            "São Sebastião",
            "Ilhabela",
            "Cruzeiro",
            "Tremembé",
            "Campos do Jordão",
            "Aparecida",
            "Cachoeira Paulista",
        ],
    ),
    (
        "sorocaba",
        "Corredor de Sorocaba",
        "a nova casa da Toyota e o sudoeste industrial",
        [
            "Sorocaba",
            "Votorantim",
            "Itu",
            "Salto",
            "Itapetininga",
            "Tatuí",
            "Boituva",
            "Porto Feliz",
            "São Roque",
            "Mairinque",
            "Itapeva",
            "Piedade",
            "Ibiúna",
            "Tietê",
            "Cerquilho",
            "Araçoiaba da Serra",
            "Alumínio",
        ],
    ),
    (
        "cana",
        "Corredor da Cana e do Couro",
        "Ribeirão Preto, Franca, Araraquara e São Carlos",
        [
            "Ribeirão Preto",
            "Franca",
            "Sertãozinho",
            "Araraquara",
            "São Carlos",
            "Barretos",
            "Jaboticabal",
            "Bebedouro",
            "Batatais",
            "Matão",
            "Jardinópolis",
            "Cravinhos",
            "Ituverava",
            "Orlândia",
            "São Joaquim da Barra",
            "Mococa",
            "São João da Boa Vista",
            "Pirassununga",
            "Descalvado",
            "Porto Ferreira",
            "Taquaritinga",
            "Monte Alto",
            "Ibaté",
            "Serrana",
            "Brodowski",
            "Guaíra",
            "Morro Agudo",
        ],
    ),
    (
        "agro_oeste",
        "Corredor do Agro do Oeste",
        "Rio Preto, Araçatuba, Prudente, Marília e Bauru",
        [
            "São José do Rio Preto",
            "Araçatuba",
            "Presidente Prudente",
            "Marília",
            "Bauru",
            "Birigui",
            "Catanduva",
            "Votuporanga",
            "Fernandópolis",
            "Jaú",
            "Lins",
            "Assis",
            "Ourinhos",
            "Tupã",
            "Andradina",
            "Mirassol",
            "Penápolis",
            "Botucatu",
            "Avaré",
            "Lençóis Paulista",
            "Garça",
            "Adamantina",
            "Dracena",
            "Presidente Venceslau",
            "Jales",
            "Olímpia",
            "Novo Horizonte",
            "Barra Bonita",
            "Pederneiras",
            "Agudos",
            "Rancharia",
            "Osvaldo Cruz",
            "Santa Fé do Sul",
            "Ilha Solteira",
            "Pereira Barreto",
            "José Bonifácio",
            "Bariri",
            "Promissão",
            "Paraguaçu Paulista",
            "Regente Feijó",
            "Álvares Machado",
            "Pirajuí",
        ],
    ),
]

PAUTA = {
    "capital": {
        "agenda": "Segurança de bairro e trem que anda. O eleitor da capital mede o governo pela catraca e pela esquina, não pelo discurso nacional.",
        "palanque": "Tarcísio e Ricardo Nunes com Flávio, na ordem estadual primeiro. Na Atlas, Tarcísio tem 52% de imagem positiva e Nunes 31% contra 49% negativa (p. 37): o prefeito soma máquina, não soma imagem.",
        "frase": "Quem manda no trem e na polícia já mostrou o que faz. Agora é a vez do país.",
        "fatos": [
            (
                "O governo estadual removeu barreiras físicas marcadas com a sigla do PCC em Paraisópolis, trocou o comando da PM após a suspeita de oito policiais da Rota de vazar informação à facção por R$ 5 milhões, e o programa SP Mobile recuperou 383 celulares em abril. Só o distrito de Pinheiros registrou 2.061 roubos e furtos no primeiro trimestre.",
                "Gazeta do Povo",
                "06/05/2026",
                "https://www.gazetadopovo.com.br/sao-paulo/tarcisio-reage-com-operacao-contra-barreiras-do-pcc-troca-na-pm-e-acoes-antirroubo-de-celulares/",
            ),
            (
                "A paralisação da CPTM em 4 de agosto interrompeu deslocamentos na metrópole. É o serviço estadual mais visível da capital e o mais sensível a greve.",
                "UOL",
                "04/08/2026",
                "https://noticias.uol.com.br/cotidiano/ultimas-noticias/2026/08/04/operacao-greve-cptm.ghtm",
            ),
            (
                "A tarifa municipal de ônibus passou de R$ 5,00 para R$ 5,30 em 6 de janeiro de 2026, e a tarifa básica do sistema metroferroviário, de R$ 5,20 para R$ 5,40.",
                "Prefeitura de São Paulo, SMT",
                "06/01/2026",
                "https://prefeitura.sp.gov.br/web/mobilidade/w/institucional/sptrans/acesso_a_informacao/227887",
            ),
        ],
        "eventos": [
            "Agenda de segurança com o governador em base comunitária da zona leste ou zona sul, com o comandante local presente e com número de ocorrências do distrito no telão, não com bandeira.",
            "Caminhada de feira em Itaquera, São Mateus e Capão Redondo em sábado de manhã, com Derrite: é o nome com melhor saldo de imagem da direita paulista na Atlas, +7.",
            "Culto e evento de igreja na periferia, onde a Atlas mede 65,2% para Tarcísio e 57,7% para Flávio entre evangélicos: o vão de 7,5 pontos está justamente aí.",
            "Motociata não cabe no centro expandido. Cabe na marginal com concentração na zona norte, e só se a prefeitura garantir a operação de trânsito.",
        ],
        "alerta": "Não tratar a capital como bloco bolsonarista. Bolsonaro caiu de 3,69 milhões para 3,19 milhões de votos entre 2018 e 2022, e a Atlas mede Tarcísio 48,9 × Haddad 48,4 na cidade, quase empate. O que rende aqui é serviço, não identidade.",
        "juizo": "É o maior eleitorado do país numa só urna e o lugar onde o vão Tarcísio-Flávio na Atlas é 5,2 pontos. A campanha ganha mais transferindo a credibilidade do serviço estadual do que repetindo o discurso nacional.",
    },
    "leste": {
        "agenda": "Emprego industrial e trem. É o berço do PT e o lugar onde a montadora demite ou contrata em manchete.",
        "palanque": "Tarcísio no comando com Flávio ao lado; Marcos Pontes, que fez 10,7 milhões de votos em 2022, como voz técnica em fábrica. Nenhum carregador do PL domina o ABC, e o rosto estadual vale mais que o federal.",
        "frase": "Emprego não tem partido. Tem fábrica aberta ou fechada.",
        "fatos": [
            (
                "São Bernardo realizou em 28 de agosto um feirão com 7.000 vagas de 60 empresas, entre elas Shopee, Mercado Livre e Rede D'Or, com salários de R$ 1.621 a R$ 8.500.",
                "Diário do Grande ABC",
                "27/08/2026",
                "https://www.dgabc.com.br/Noticia/4343492/sao-bernardo-promove-feirao-de-emprego-com-7-000-vagas-e-salarios-de-ate-r$-8-500",
            ),
            (
                "O Grande ABC começou 2026 com saldo negativo de empregos com carteira assinada.",
                "Diário do Grande ABC",
                "03/03/2026",
                "https://www.dgabc.com.br/Noticia/4288466/regiao-inicia-2026-com-saldo-negativo-de-empregos-de-carteira-assinada",
            ),
            (
                "A Volkswagen aprovou o plano que corta cerca de 50 mil empregos no mundo até 2030. Até o momento não há indicação de que as quatro fábricas brasileiras estejam entre os alvos, e a empresa mantém R$ 16 bilhões de investimento previstos no Brasil até 2028.",
                "Agência GBC",
                "05/09/2026",
                "https://agenciagbc.com/2026/09/05/maior-plano-da-historia-da-volkswagen-confirma-50-mil-demissoes-mas-montadora-prepara-grande-mudanca/",
            ),
        ],
        "eventos": [
            "Portaria de fábrica na troca de turno em São Bernardo e Guarulhos, com pauta de tarifa de importação e custo de energia, competência federal direta.",
            "Reunião separada com o comércio de Santo André e São Caetano, as duas cidades do ABC onde Bolsonaro venceu em 2022.",
            "Agenda de trilhos em Mogi das Cruzes e Suzano, com a nova fase da concessão das Linhas 11, 12 e 13 (Trivia, desde julho de 2026) como prova de entrega estadual.",
            "Não fazer comício em Diadema ou São Bernardo. O evento de rua dá plateia hostil e imagem de invasão.",
        ],
        "alerta": "Não chamar o ABC de reduto perdido nem de reduto conquistado. Santo André e São Caetano votaram Bolsonaro, Diadema e São Bernardo votaram Lula, e Guarulhos ficou no fio. O corredor é uma fronteira, não um bloco.",
        "juizo": "É o segundo maior eleitorado do estado e o mais sensível a emprego industrial. A pauta de comércio exterior e energia é federal, e é onde o candidato a presidente fala com autoridade própria.",
    },
    "oeste_metro": {
        "agenda": "Trem que descarrila e cidade que cresce sem serviço. Osasco e Barueri são a metrópole que deu certo economicamente e ainda assim vê a Linha 8 parar duas vezes na mesma semana.",
        "palanque": "Tarcísio com Flávio, e o prefeito local no palco. É o corredor onde a direita já é maioria e onde a cobrança de serviço recai sobre a concessão estadual.",
        "frase": "Cidade que paga a conta tem direito a trem que chega.",
        "fatos": [
            (
                "Um trem da Linha 8-Diamante descarrilou perto da estação Osasco em 14 de agosto, segundo dia consecutivo com descarrilamento na linha da ViaMobilidade, e os passageiros caminharam pelos trilhos.",
                "Correio Paulista",
                "14/08/2026",
                "https://correiopaulista.com/trem-descarrila-na-linha-8-diamante-em-osasco-e-passageiros-caminham-pelos-trilhos/",
            ),
            (
                "Em 18 de agosto a Linha 8 operou em via única, com intervalos maiores entre 9h30 e 15h30, por manutenção da via permanente.",
                "Visão Oeste",
                "18/08/2026",
                "https://visaooeste.com.br/linha-8-tem-operacao-por-via-unica-e-maiores-intervalos-nesta-terca-feira-18/",
            ),
            (
                "Em 3 de agosto um trem da mesma linha foi evacuado em Carapicuíba após superaquecimento, sem feridos.",
                "Giro S.A.",
                "03/08/2026",
                "https://girosa.com.br/linha-8-diamante-trem-evacuado-carapicuiba/",
            ),
        ],
        "eventos": [
            "Vistoria pública na Linha 8 com o governador, exigindo da concessionária o cronograma de troca de via, com data. Assumir o problema antes que o adversário o use.",
            "Motociata Osasco, Barueri e Santana de Parnaíba pela Castello Branco: frota alta, avenida larga e eleitorado que votou Bolsonaro em 2022.",
            "Café com pequena indústria e logística em Cajamar, polo de centros de distribuição, com pauta de custo de frete e pedágio.",
            "Caminhada em Francisco Morato e Franco da Rocha, o colar norte pobre, com pauta de trem e saúde, sem palanque montado.",
        ],
        "alerta": "Não celebrar Alphaville como vitrine. O eleitor de Carapicuíba e Itapevi usa o mesmo trem e não mora no condomínio. A fala que serve em Barueri não serve em Francisco Morato.",
        "juizo": "É o corredor de menor custo por voto da metrópole: direita majoritária, cobrança concentrada num serviço estadual visível e prefeituras aliadas. A entrega do trem é o teste.",
    },
    "porto": {
        "agenda": "O porto no limite e o túnel que sai do papel. A Baixada tem a maior obra federal-estadual do estado em andamento e a fila de navios como métrica diária.",
        "palanque": "Tarcísio e Flávio juntos, com o túnel Santos-Guarujá como prova de que os dois níveis de governo podem trabalhar juntos. É a única pauta da Baixada em que o adversário federal também tem crédito.",
        "frase": "O túnel foi assinado. Falta quem faça a fila de navios andar.",
        "fatos": [
            (
                "Entre janeiro e julho de 2026 o Porto de Santos movimentou 109,5 milhões de toneladas, alta de 3,6%, e 3,47 milhões de TEU. O porto opera perto do limite, com fila crônica de navios, a taxa de manuseio de contêiner passou de US$ 70 a 100 para cerca de US$ 500 por TEU desde 2019, e o Tecon 10, que acrescentaria 3,5 milhões de TEU, foi adiado nove vezes desde 2022.",
                "Portogente",
                "25/08/2026",
                "https://portogente.com.br/noticias/transporte-logistica/118049-porto-de-santos-bate-109-5-milhoes-de-toneladas-em-2026-mas-o-crescimento-esconde-um-porto-no-limite",
            ),
            (
                "A concessionária TSG assinou o termo de transferência inicial e avançou com o túnel Santos-Guarujá em 7 de julho de 2026. Projeto executivo, início de obras e entrega são marcos distintos.",
                "Concessionária TSG",
                "07/07/2026",
                "https://tsgp.com.br/2026/07/07/tsg-concessionaria-assina-tti-e-avanca-com-o-tunel-santos-guaruja/",
            ),
            (
                "O Porto de Santos fechou 2025 com R$ 4 bilhões em caixa e movimentação recorde de cerca de 190 milhões de toneladas; a Mota-Engil assinaria em fevereiro de 2026 o contrato do túnel de R$ 6,8 bilhões, com conclusão prevista para meados de 2030.",
                "NeoFeed",
                "26/12/2025",
                "https://neofeed.com.br/negocios/no-porto-de-santos-r-4-bilhoes-em-caixa-e-o-novo-prazo-para-a-construcao-do-tunel-santos-guaruja/en/",
            ),
        ],
        "eventos": [
            "Visita ao canteiro do túnel em Santos com o governador, com cronograma no painel e sem promessa de data que a concessionária não assinou.",
            "Mesa com operadores portuários e caminhoneiros em Cubatão e Guarujá sobre o Tecon 10 e a fila de navios: pauta federal, e a mais concreta do corredor.",
            "Caminhada de orla em Praia Grande e São Vicente, as duas maiores cidades pobres da Baixada, com pauta de saúde e segurança.",
            "Motociata Santos, São Vicente e Praia Grande pela orla, formato consolidado na região.",
        ],
        "alerta": "Não reivindicar o túnel como obra de um lado só. O financiamento envolve as duas esferas e o eleitor sabe. A posição defensável é cobrar do governo federal o leilão do Tecon 10, adiado nove vezes, que é o gargalo que o túnel não resolve.",
        "juizo": "É onde a pauta federal mais concreta do estado encontra uma obra estadual visível. Raro caso em que o candidato a presidente pode prometer algo que só o presidente entrega: o leilão do terminal.",
    },
    "tecnologia": {
        "agenda": "Indústria que muda de cidade e mobilidade que chega tarde. Campinas perdeu a Toyota de Indaiatuba para Sorocaba e espera o trem intercidades desde a década passada.",
        "palanque": "Tarcísio no comando: é o corredor onde ele mais supera Flávio entre os polos do interior, 58,0 × 52,8 na região Atlas de Campinas e SJC. Flávio como convidado da agenda de emprego.",
        "frase": "Fábrica que fecha aqui não pode virar fábrica que abre em outro país.",
        "fatos": [
            (
                "A Toyota encerrou a produção em Indaiatuba em 30 de junho de 2026, fábrica que operava desde 1998 e produziu mais de um milhão de veículos, e transfere a linha do Corolla para a segunda planta de Sorocaba.",
                "Cruzeiro do Sul",
                "01/06/2026",
                "https://www.jornalcruzeiro.com.br/sorocaba/noticias/2026/06/761053-toyota-inaugura-nova-fabrica-em-sorocaba-em-novembro.html",
            ),
            (
                "A Hyundai abriu 21 vagas em Piracicaba em julho de 2026, entre estágio e produção; o município criou 2.344 empregos formais de janeiro a maio.",
                "Piranot",
                "07/07/2026",
                "https://www.piranot.com.br/2026/07/07/noticias/brasil/estado-sao-paulo/interior/rmp/piracicaba-noticias/hyundai-21-vagas-piracicaba-pat-cursos/",
            ),
            (
                "A Ares-PCJ publicou interrupção programada da Sanasa em Campinas para 18 de agosto. Manutenção anunciada não é colapso hídrico; a questão é informação e continuidade do serviço.",
                "Ares-PCJ",
                "08/2026",
                "https://www.arespcj.com.br/conteudo/sanasa-campinas-interrupcao-programada1098",
            ),
        ],
        "eventos": [
            "Chão de fábrica em Piracicaba e Sumaré com pauta de custo de energia e importação, e visita à planta fechada de Indaiatuba como símbolo do que não pode se repetir.",
            "Encontro com startups e pesquisadores ligados à Unicamp: o corredor tem o eleitor de ensino superior onde o vão Tarcísio-Flávio é 10,9 pontos na Atlas.",
            "Agenda de trilhos em Jundiaí e Campinas com o cronograma do trem intercidades, e cobrança pública da parte federal em Viracopos.",
            "Cavalgada e festa de peão em Americana e Mogi Guaçu, formato consolidado no interior próximo.",
        ],
        "alerta": "Não repetir discurso de desindustrialização genérico numa região que sabe qual fábrica fechou e em que mês. A imprecisão custa mais que o silêncio.",
        "juizo": "Segundo maior eleitorado do interior, direita majoritária e o maior eleitorado universitário fora da capital. É onde a campanha precisa conquistar o eleitor de Tarcísio que ainda não é de Flávio, e onde ele existe em número.",
    },
    "aeroespacial": {
        "agenda": "Tarifa americana e emprego de engenheiro. O Vale exporta avião e importa a conta de qualquer briga comercial.",
        "palanque": "Flávio com autoridade própria: comércio exterior é competência federal. Tarcísio fecha com a pauta de Tamoios e Litoral Norte.",
        "frase": "Quem exporta avião não pode ser refém de tarifa. Isso se resolve em Brasília e em Washington.",
        "fatos": [
            (
                "A Embraer pagou US$ 80 milhões em tarifas impostas pelos Estados Unidos e monitora a Justiça americana para tentar recuperar o valor; cerca de 85% do impacto ficou na aviação executiva, e a cobrança cessou em 24 de março.",
                "Vale 360 News",
                "06/03/2026",
                "https://www.vale360news.com.br/tarifas-embraer-eua-empresa-pagou-us-80-milhoes-e-monitora-decisao-da-justica-para-reaver-o-dinheiro/",
            ),
            (
                "A Embraer abriu dezenas de vagas e bancos de talentos em São José dos Campos em agosto. Anúncio evidencia demanda de recrutamento; banco de talentos não é contratação.",
                "Notícias SJC",
                "26/08/2026",
                "https://noticiassjc.com.br/embraer-abre-dezenas-de-vagas-de-emprego-e-bancos-de-talentos-em-sao-jose/",
            ),
            (
                "O pedágio eletrônico da Tamoios em Caraguatatuba registrou mais de 31 mil passagens não pagas entre janeiro e março de 2026, com mais de 2 milhões de veículos até 20 de agosto e tarifa básica de R$ 5,90.",
                "Rota 55",
                "08/2026",
                "https://www.rota55.com.br/brasil/2026/08/pedagio-free-flow-da-tamoios-registra-31-mil-passagens-nao-pagas-cnh-do-brasil-passa-a-exibir-cobrancas/",
            ),
        ],
        "eventos": [
            "Encontro com engenheiros e fornecedores da cadeia aeroespacial em São José dos Campos, formato de mesa técnica, com a conta da tarifa no telão.",
            "Portaria de fábrica em Taubaté na troca de turno, com pauta de energia e importação.",
            "Agenda de Litoral Norte em Caraguatatuba e São Sebastião com pedágio eletrônico e royalties do pré-sal, pauta estadual e federal ao mesmo tempo.",
            "Romaria em Aparecida, o maior ativo simbólico católico do estado, com cuidado de não transformar o santuário em palanque.",
        ],
        "alerta": "Não prometer que a tarifa cai por afinidade pessoal com governo estrangeiro. O eleitor do Vale leu que a Embraer pagou US$ 80 milhões e quer saber o mecanismo, não a amizade.",
        "juizo": "Direita consolidada, renda acima da média e a pauta federal mais nítida do estado. O corredor não precisa de conversão, precisa de mobilização e de resposta técnica.",
    },
    "sorocaba": {
        "agenda": "A fábrica que veio. Sorocaba ganhou a segunda planta da Toyota e 2.000 empregos, e o sudoeste industrial quer saber quem garante o próximo ciclo.",
        "palanque": "Tarcísio abre, Flávio fecha. A atração da Toyota é crédito do governo estadual e a região é a mais bolsonarista dos grandes polos: 60,8% para Tarcísio e 55,3% para Flávio na região Atlas de Prudente, Marília e Sorocaba.",
        "frase": "A fábrica veio porque aqui tem quem trabalhe e quem governe.",
        "fatos": [
            (
                "A Toyota inaugura em novembro de 2026 a segunda fábrica de Sorocaba, dentro de R$ 11 bilhões de investimento no Brasil até 2030, com cerca de 2.000 novos empregos.",
                "Cruzeiro do Sul",
                "01/06/2026",
                "https://www.jornalcruzeiro.com.br/sorocaba/noticias/2026/06/761053-toyota-inaugura-nova-fabrica-em-sorocaba-em-novembro.html",
            ),
            (
                "A Toyota abriu 100 vagas em Sorocaba em agosto, com seleção sem exigência de experiência.",
                "Canal Estado SP",
                "25/08/2026",
                "https://www.canalestadosp.com.br/noticia/toyota-tem-100-vagas-abertas-em-sorocaba-e-selecao-nao-exige-experiencia-a3809c8b",
            ),
            (
                "Os pedágios da Castello Branco e da Raposo Tavares subiram em março de 2026: a praça de Itu passou de R$ 12,60 para R$ 13,20 e o Castelinho, em Sorocaba, de R$ 7,10 para R$ 7,50.",
                "Fato e Notícia",
                "30/03/2026",
                "https://fatoenoticia.com.br/2026/03/30/pedagios-da-castello-branco-e-raposo-tavares-ficam-mais-caros-veja-os-novos-valores/",
            ),
        ],
        "eventos": [
            "Inauguração da segunda fábrica da Toyota em novembro é o evento do corredor; a campanha deve estar na cidade na semana, não no dia, para não confundir ato empresarial com comício.",
            "Comício de praça em Sorocaba e Itu, onde a direita já é maioria confortável e o custo é baixo.",
            "Cavalgada e comitiva em Itapetininga, Tatuí e Itapeva, onde a cultura de montaria é consolidada.",
            "Motociata Sorocaba e Votorantim, avenida larga e frota alta.",
        ],
        "alerta": "Não prometer isenção de pedágio. O contrato é estadual e o eleitor sabe quem assinou. A pauta defensável é obra em troca de tarifa, com data.",
        "juizo": "É o corredor onde o palanque estadual empurra o nacional sem esforço, e onde a foto conjunta soma. Custo baixo, retorno de mobilização.",
    },
    "cana": {
        "agenda": "Etanol que cai na usina e não cai na bomba, tarifa americana no sapato de Franca. A pauta é preço, e preço é federal.",
        "palanque": "Flávio com os deputados de base própria da região e com Tarcísio na pauta de rodovia. Nenhum carregador estadual domina o nordeste paulista; o crédito local vale mais que o nome estadual.",
        "frase": "A usina baixou 23%. A bomba baixou 10%. Alguém ficou com a diferença.",
        "fatos": [
            (
                "O etanol hidratado na usina em Ribeirão Preto caiu 23% entre 2 de março e 17 de maio de 2026, de R$ 3,60 para R$ 2,77 por litro, enquanto a queda média nos postos do estado foi de 10%, de R$ 4,44 para R$ 3,99.",
                "Cana Online",
                "01/06/2026",
                "https://www.canaonline.com.br/conteudo/queda-do-etanol-nas-usinas-nao-chega-ao-consumidor-e-acende-alerta-no-setor-sucroenergetico.html",
            ),
            (
                "A safra 2026/27 começou com moagem de 19,56 milhões de toneladas, alta de 19,17%, e mais de dois terços da cana vai para etanol; a projeção é de 709,1 milhões de toneladas e recorde de 40,69 bilhões de litros.",
                "CBN Ribeirão",
                "08/05/2026",
                "https://cbnribeirao.com.br/setor-sucroenergetico-amplia-foco-em-eficiencia-operacional-na-safra-2026-27/",
            ),
            (
                "A tarifa adicional de 25% dos Estados Unidos entrou em vigor em 22 de julho de 2026 e a Abicalçados passou a projetar queda de 7,1% nas exportações de calçados até o fim do ano.",
                "O Tempo",
                "16/07/2026",
                "https://www.otempo.com.br/economia/2026/7/16/setores-afetados-pelo-tarifaco-como-textil-calcadista-e-de-maquinas-temem-demissoes-e-prejuizos",
            ),
            (
                "Franca é o segundo polo calçadista do estado, com 28,7% da produção. O presidente do sindicato dos sapateiros diz que a tarifa não provoca demissão imediata e que o problema da cidade é falta de mão de obra especializada, que migrou para a construção.",
                "Agência Pública",
                "22/07/2026",
                "https://apublica.org/2026/07/tarifaco-divide-trabalhadores-e-empresarios-do-setor-de-calcados/",
            ),
        ],
        "eventos": [
            "Mesa com usineiros, fornecedores de cana e donos de posto em Ribeirão Preto e Sertãozinho sobre a diferença entre preço na usina e preço na bomba: pauta federal de tributo e distribuição.",
            "Chão de fábrica de calçado em Franca, com o sindicato dos sapateiros convidado, sobre tarifa e mão de obra.",
            "Encontro com pesquisadores em São Carlos e Araraquara, o bolsão universitário do corredor, onde o eleitor de ensino superior está e o vão é maior.",
            "Festa de peão em Barretos é o maior palco popular do corredor, e a campanha deve estar lá sem tomar o palco dos organizadores.",
        ],
        "alerta": "Não entrar como advogado da usina. Nestas cidades a usina é empregadora e é quem baixou o preço que não chegou ao consumidor. A posição defensável é a do consumidor e do fornecedor de cana.",
        "juizo": "Direita consolidada, renda média alta e uma pauta de preço que só o governo federal resolve. Corredor de mobilização, e o único onde a economia agrícola tem número diário na TV local.",
    },
    "agro_oeste": {
        "agenda": "Emprego que cresce e serviço que falta. O oeste está gerando emprego formal e ainda depende de voo, hospital regional e água que o município não entrega sozinho.",
        "palanque": "Tarcísio e Flávio com os deputados de base concentrada no oeste; é o maior corredor bolsonarista do estado em número de municípios e onde a política se faz por polo regional.",
        "frase": "O oeste sustenta o estado. O estado precisa chegar ao oeste.",
        "fatos": [
            (
                "O Emprega Prudente ofereceu 237 vagas em 3 de agosto de 2026, 149 delas em serviços.",
                "Prefeitura de Presidente Prudente",
                "03/08/2026",
                "https://www.presidenteprudente.sp.gov.br/site/noticia/67263",
            ),
            (
                "Araçatuba gerou 1.019 empregos formais nos cinco primeiros meses de 2026, alta de 37% sobre 2025, com serviços à frente, seguidos de indústria e construção.",
                "Prefeitura de Araçatuba",
                "02/07/2026",
                "https://aracatuba.sp.gov.br/noticias/araatuba-cria-1019-empregos-formais-em-cinco-meses-com-destaque-para-servios-indstria-e-construo",
            ),
            (
                "Rio Preto retomou em 2 de setembro os voos diretos para Brasília, três vezes por semana pela Latam, com previsão de voo diário a partir de novembro e cerca de 2.000 passageiros por mês.",
                "TH Mais",
                "01/09/2026",
                "https://thmais.com.br/cidades/sao-jose-rio-preto/rio-preto-retoma-voos-diretos-para-brasilia-a-partir-de-2-de-setembro",
            ),
            (
                "A Defesa Civil alertou para umidade crítica e calor extremo no interior em 28 de agosto. Alerta é previsão e orientação preventiva, não balanço de danos.",
                "Folha",
                "28/08/2026",
                "https://www1.folha.uol.com.br/cotidiano/2026/08/defesa-civil-alerta-para-umidade-critica-e-calor-extremo-no-interior-de-sp.shtml",
            ),
            (
                "Desde 1º de agosto de 2026 a Companhia de Saneamento de Bauru assumiu água, esgoto e contas na cidade.",
                "JCNET",
                "08/2026",
                "https://sampi.net.br/bauru/noticias/3001839/geral/2026/08/dae-bauru-informa-canais-de-atendimento-de-agua-esgoto-e-contas",
            ),
        ],
        "eventos": [
            "Comício de praça em Rio Preto, Araçatuba e Presidente Prudente: os três polos onde a direita é maioria ampla e o público é garantido.",
            "Visita a hospital regional em Bauru ou Marília com pauta de fila de especialidade e transporte sanitário, a queixa real do interior profundo.",
            "Cavalgada e festa de peão em Jales, Fernandópolis e Andradina, cultura consolidada e custo baixo.",
            "Mesa com produtores de laranja, cana e gado em Catanduva e Lins sobre crédito, seguro rural e estiagem.",
        ],
        "alerta": "Não fazer promessa de aeroporto ou hospital sem fonte e prazo. O eleitor do oeste já viu voo anunciado e cancelado, e a imprecisão pesa mais aqui que na capital.",
        "juizo": "É a base de sustentação da direita paulista fora da metrópole e o corredor mais barato de mobilizar. O risco não é perder voto; é deixar de convertê-lo em comparecimento.",
    },
}


def agrega(sel, eleitorado_sp, votos_extra):
    e = sum(r["eleitorado"] for r in sel)
    ids = {r["id"] for r in sel}
    tot = {
        k: sum(v for i, v in votos_extra["total"][c].items() if i in ids)
        for k, c in votos_extra["cargo"].items()
    }
    cs = [CITY[i] for i in ids]
    pres1 = sum(c["2022_PRESIDENTE_1_total"] for c in cs)
    pres2 = sum(c["2022_PRESIDENTE_2_total"] for c in cs)
    bol1 = 100 * sum(c["jair_2022_1"] for c in cs) / pres1
    bol2 = 100 * sum(c["jair_2022_2"] for c in cs) / pres2
    pt2 = 100 * sum(c["pt_2022_2"] for c in cs) / pres2
    j18 = (
        100
        * sum(c["jair_2018_2"] for c in cs)
        / sum(c["2018_PRESIDENTE_2_total"] for c in cs)
    )
    out = {
        "municipios": len(sel),
        "eleitores": e,
        "share_sp": round(100 * e / eleitorado_sp, 2),
        "bol1": round(bol1, 2),
        "bol2": round(bol2, 2),
        "margem_pt_2t_pp": round(pt2 - bol2, 2),
        "desloc_18_22_pp": round(bol2 - j18, 2),
        "viradas": sum(1 for r in sel if r["virada"] == "Jair → PT"),
        "renda": round(
            sum(r["renda"] * CITY[r["id"]]["populacao"] for r in sel)
            / sum(CITY[r["id"]]["populacao"] for r in sel),
            2,
        ),
    }
    base = bol1 / votos_extra["estado"]["bolsonaro_1t"]
    for k in [*INDICES, "garcia"]:
        share = (
            100
            * sum(v for i, v in votos_extra["votos"][k].items() if i in ids)
            / tot[k]
            if tot[k]
            else 0
        )
        out[k] = round(share, 2)
        if k in INDICES:
            out["i_" + k] = (
                round(100 * (share / votos_extra["estado"][k]) / base) if base else 0
            )
    out["tar1_menos_bol1_pp"] = round(out["tarcisio"] - bol1, 2)
    gov2 = sum(c["2022_GOVERNADOR_2_total"] for c in cs)
    tar2 = 100 * sum(c["tarcisio_2022_2"] for c in cs) / gov2
    out["tar2"] = round(tar2, 2)
    out["tar2_menos_bol2_pp"] = round(tar2 - bol2, 2)
    out["votos_tarcisio_sem_bolsonaro"] = sum(
        CARRIER_ROWS[c["id"]]["votos_tarcisio_sem_bolsonaro"] for c in cs
    )
    out["estoque_votos"] = sum(CARRIER_ROWS[c["id"]]["estoque_votos"] for c in cs)
    out["estoque2t_votos"] = sum(CARRIER_ROWS[c["id"]]["estoque2t_votos"] for c in cs)
    out["estoque_pct"] = round(
        100 * out["estoque_votos"] / sum(c["2022_GOVERNADOR_1_total"] for c in cs), 2
    )
    return out


def main():
    DERIVED.mkdir(parents=True, exist_ok=True)
    byname = {r["nome"]: r["id"] for r in CITIES}
    corredores_def = {}
    for slug, _, _, nomes in CORREDORES:
        faltando = [n for n in nomes if n not in byname]
        if faltando:
            raise SystemExit(f"município não encontrado em {slug}: {faltando}")
        corredores_def[slug] = [byname[n] for n in nomes]
    estado, rows, perfil, votos, total = carregadores(corredores_def)
    cargo_de = {k: c for k, c, *_ in CHAVES}
    extra = {"votos": votos, "total": total, "cargo": cargo_de, "estado": estado}
    eleitorado_sp = sum(r["eleitorado"] for r in rows)
    byid = {r["id"]: r for r in rows}
    CARRIER_ROWS.update(byid)
    corredores = []
    for slug, nome, sub, nomes in CORREDORES:
        sel = [byid[byname[n]] for n in nomes]
        ids = set(corredores_def[slug])
        ancoras = sorted(
            [p for p in perfil if p["concentracao"][slug] >= 40],
            key=lambda p: -p["votos_sp"],
        )[:6]
        corredores.append(
            {
                "slug": slug,
                "nome": nome,
                "sub": sub,
                "resumo": agrega(sel, eleitorado_sp, extra),
                "pauta": PAUTA[slug],
                "ancoras": [
                    {
                        "nome": p["nome"],
                        "partido": p["partido"],
                        "casa": p["casa"],
                        "votos_sp": p["votos_sp"],
                        "concentracao_pct": p["concentracao"][slug],
                        "base": p["cidade_base"],
                    }
                    for p in ancoras
                ],
                "cidades": sorted(sel, key=lambda r: -r["eleitorado"]),
                "ids": sorted(ids),
            }
        )
    # índice por região intermediária
    regioes = []
    for reg in sorted({r["regiao"] for r in rows}):
        sel = [r for r in rows if r["regiao"] == reg]
        regioes.append({"regiao": reg} | agrega(sel, eleitorado_sp, extra))
    regioes.sort(key=lambda r: -r["eleitores"])
    complementares = sorted(
        [r for r in rows if r["eleitorado"] >= 40000 and r["tar2_menos_bol2_pp"] > 0],
        key=lambda r: -r["votos_tarcisio_sem_bolsonaro"],
    )
    acima = [r for r in rows if r["tar2_menos_bol2_pp"] > 0]
    trabalho = sorted(
        [r for r in rows if r["eleitorado"] >= 30000],
        key=lambda r: -r["estoque_votos"],
    )
    densidade = sorted(
        [r for r in rows if r["eleitorado"] >= 40000], key=lambda r: -r["estoque_pct"]
    )
    contrarios = sorted(
        [r for r in rows if r["eleitorado"] >= 40000 and r["tar2_menos_bol2_pp"] < 0],
        key=lambda r: r["votos_tarcisio_sem_bolsonaro"],
    )
    gov2_total = sum(r["2022_GOVERNADOR_2_total"] for r in CITIES)
    micro = {
        "definicao": (
            "Diferença local = Tarcísio menos Bolsonaro no 2º turno de 2022, em pontos, no mesmo "
            "universo de eleitores. Votos de Tarcísio sem Bolsonaro = essa diferença aplicada aos "
            "votos válidos para governador da cidade. Potencial = eleitorado de 2026 vezes a soma do "
            "vão regional medido pela Atlas (Tarcísio 2º turno menos Flávio 2º turno na região do "
            "instituto, p. 14 e 23) com a diferença local de 2022. É estimativa, não medição: a "
            "Atlas mede cinco regiões, e a diferença local vem de outra eleição."
        ),
        "definicao_estoque": (
            "Estoque localizado = fatia medida pela Atlas (p. 14 e 23) de cada eleitorado do 1º turno "
            "de 2022 para governador que hoje vota Tarcísio no 2º turno e não vota Flávio no 2º turno, "
            "aplicada aos votos de 2022 de cada município. Coeficientes: Tarcísio 2022 "
            f"{ESTOQUE['Tarcísio'] * 100:.1f}%, Haddad 2022 {ESTOQUE['Haddad'] * 100:.1f}%, Rodrigo Garcia "
            f"2022 {ESTOQUE['Rodrigo Garcia'] * 100:.1f}%. Não inclui quem votou branco, nulo ou não votou "
            "em 2022, porque o TSE não fornece esses grupos por município nesta base, nem os eleitores "
            "de Poit e Elvis Cezar, não medidos pela Atlas. É a metade localizável do vão."
        ),
        "coeficientes": ESTOQUE,
        "estado": {
            "tar2": round(
                100 * sum(r["tarcisio_2022_2"] for r in CITIES) / gov2_total, 2
            ),
            "bol2": round(
                100
                * sum(r["jair_2022_2"] for r in CITIES)
                / sum(r["2022_PRESIDENTE_2_total"] for r in CITIES),
                2,
            ),
            "municipios_tarcisio_acima": len(acima),
            "eleitores_tarcisio_acima": sum(r["eleitorado"] for r in acima),
            "votos_tarcisio_sem_bolsonaro_acima": sum(
                r["votos_tarcisio_sem_bolsonaro"] for r in acima
            ),
            "estoque_votos_total": sum(r["estoque_votos"] for r in rows),
            "estoque_garcia_total": sum(r["estoque_garcia_votos"] for r in rows),
            "estoque2t_votos_total": sum(r["estoque2t_votos"] for r in rows),
            "estoque_pct": round(
                100
                * sum(r["estoque_votos"] for r in rows)
                / sum(r["2022_GOVERNADOR_1_total"] for r in CITIES),
                2,
            ),
        },
        "regioes_atlas": ATLAS_REGIAO,
        "trabalho": trabalho[:30],
        "densidade": densidade[:15],
        "acima_top": sorted(acima, key=lambda r: -r["votos_tarcisio_sem_bolsonaro"])[
            :10
        ],
        "contrarios": contrarios[:12],
    }
    payload = {
        "meta": {
            "gerado_por": "scripts/sp-092026-camada2.py",
            "corte": "2026-09-05",
            "definicao_indice": (
                "O índice divide o desempenho do nome no município pela participação estadual "
                "dele, divide o mesmo cálculo feito com Bolsonaro no 1º turno de 2022 e multiplica "
                "por cem. Todos os percentuais são sobre votos nominais do próprio cargo. Cem "
                "significa render o mesmo que o topo da chapa rendeu ali."
            ),
        },
        "reponderacao": reponderacao(),
        "fluxos": fluxos(),
        "fluxos3": fluxos_tres_niveis(),
        "vao": vao(),
        "estrategia": ESTRATEGIA,
        "micro": micro,
        "carregadores": {
            "estado": estado,
            "chaves": [
                {"chave": k, "cargo": cargo, "nome": nome, "descricao": desc}
                for k, cargo, _, nome, desc in CHAVES
            ],
            "regioes": regioes,
            "complementares_tarcisio": complementares[:25],
            "municipios": [
                {
                    k: r[k]
                    for k in (
                        "id",
                        "tar1_menos_bol1_pp",
                        "tar2_menos_bol2_pp",
                        "votos_tarcisio_sem_bolsonaro",
                        "estoque_votos",
                        "estoque_pct",
                        "estoque2t_votos",
                        "estoque2t_pct",
                        "garcia1",
                        "tar1",
                        *tuple("i_" + x for x in INDICES),
                    )
                }
                for r in rows
            ],
        },
        "corredores": corredores,
        "eleitorado_sp": eleitorado_sp,
    }
    (ASSETS / "sp_092026_camada2.json").write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    fields = list(rows[0].keys())
    with (DERIVED / "carregadores-municipais.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    rp = payload["reponderacao"]
    print("estado", estado)
    for inst in ("datafolha", "quaest", "atlas"):
        for q, b in rp[inst].items():
            if isinstance(b, dict) and "candidatos" in b:
                print(
                    inst,
                    q,
                    {
                        n: (c["publicado"], c["recomposto"], c["sensibilidade"])
                        for n, c in b["candidatos"].items()
                    },
                )
    for f in payload["fluxos"]:
        print(f["nome"], f["robusto"], f["estimado"])
    print("vão total", payload["vao"]["total"])
    for c in corredores:
        print(
            c["slug"],
            c["resumo"]["eleitores"],
            c["resumo"]["share_sp"],
            c["resumo"]["bol1"],
            c["resumo"]["i_tarcisio"],
            c["resumo"]["i_derrite"],
            [a["nome"] for a in c["ancoras"]],
        )


# ------------------------------------------------------------- três níveis
# Atlas p. 10: intenção de 2026 para governador por voto de 2022 (1º turno).
ATLAS_P10_POR_2022 = {
    "Tarcísio": {"Tarcísio": 98.0, "Haddad": 0.4, "Outros": 0.0, "Não escolha": 1.5},
    "Haddad": {"Tarcísio": 0.3, "Haddad": 97.3, "Outros": 2.1, "Não escolha": 0.2},
    "Rodrigo Garcia": {
        "Tarcísio": 36.5,
        "Haddad": 50.9,
        "Outros": 2.0,
        "Não escolha": 10.6,
    },
    "Branco ou nulo": {
        "Tarcísio": 0.3,
        "Haddad": 7.7,
        "Outros": 46.2,
        "Não escolha": 45.7,
    },
    "Não votou": {"Tarcísio": 43.6, "Haddad": 43.6, "Outros": 2.8, "Não escolha": 9.9},
}
# Atlas p. 19: 1º turno presidencial de 2026 por voto de 2022 para governador (1º turno).
ATLAS_P19_COMPLETO = {
    "Tarcísio": {
        "Flávio": 85.1,
        "Lula": 0.5,
        "Cury": 4.8,
        "Renan": 6.5,
        "Zema": 1.6,
        "Caiado": 0.9,
        "Outros": 0.1,
        "Não escolha": 0.4,
    },
    "Haddad": {
        "Flávio": 0.0,
        "Lula": 95.2,
        "Cury": 1.7,
        "Renan": 0.1,
        "Zema": 0.0,
        "Caiado": 0.8,
        "Outros": 2.0,
        "Não escolha": 0.1,
    },
    "Rodrigo Garcia": {
        "Flávio": 11.0,
        "Lula": 27.0,
        "Cury": 31.9,
        "Renan": 6.7,
        "Zema": 8.2,
        "Caiado": 6.8,
        "Outros": 0.0,
        "Não escolha": 8.5,
    },
    "Outro": {
        "Flávio": 9.4,
        "Lula": 47.3,
        "Cury": 24.5,
        "Renan": 7.9,
        "Zema": 0.0,
        "Caiado": 0.0,
        "Outros": 9.9,
        "Não escolha": 0.9,
    },
    "Branco ou nulo": {
        "Flávio": 0.4,
        "Lula": 7.8,
        "Cury": 33.7,
        "Renan": 25.1,
        "Zema": 0.0,
        "Caiado": 0.1,
        "Outros": 16.4,
        "Não escolha": 16.5,
    },
    "Não votou": {
        "Flávio": 22.9,
        "Lula": 35.0,
        "Cury": 7.0,
        "Renan": 18.4,
        "Zema": 0.0,
        "Caiado": 0.9,
        "Outros": 8.2,
        "Não escolha": 7.6,
    },
}
# Peso de cada grupo de 2022 no eleitorado paulista: votos do TSE (1º turno para
# governador) e comparecimento. Brancos/nulos e abstenção aproximados pela
# diferença entre eleitorado, comparecimento e válidos.
PESO_2022 = {
    "Tarcísio": 0.285,
    "Haddad": 0.240,
    "Rodrigo Garcia": 0.124,
    "Outro": 0.024,
    "Branco ou nulo": 0.115,
    "Não votou": 0.212,
}
PRES1 = [
    "Flávio",
    "Lula",
    "Cury",
    "Renan",
    "Zema",
    "Caiado",
    "Marçal",
    "Outros",
    "Não escolha",
]
PRES2 = ["Flávio", "Lula", "Não escolha"]
# Prior do 2º estágio, declarada. Calibrada nos saltos medidos pela Atlas por grupo de
# 2022 entre p. 19 e p. 23: entre eleitores de Garcia, a terceira via de 1º turno (53,6)
# termina 47% em Lula, 26% em Flávio e 27% na não escolha; entre eleitores de Tarcísio
# 2022 (13,8), 67% em Flávio, 0% em Lula e 33% na não escolha. Cury é o favorito do
# eleitor de Garcia; Renan, do não votante e do branco de 2022.


def prior_estagio1():
    """Prior gov 2026 -> pres 1º turno, composta pela origem de 2022 (Atlas p. 10 e p. 19)."""
    destinos = ["Tarcísio", "Haddad", "Outros", "Não escolha"]
    p10 = dict(ATLAS_P10_POR_2022)
    p10["Outro"] = {
        "Tarcísio": 10.0,
        "Haddad": 60.0,
        "Outros": 20.0,
        "Não escolha": 10.0,
    }
    prior = {}
    composicao = {}
    for d in destinos:
        pesos = {g: PESO_2022[g] * p10[g][d] / 100 for g in PESO_2022}
        tot = sum(pesos.values())
        comp = {g: w / tot for g, w in pesos.items()}
        composicao[d] = {g: round(v, 3) for g, v in comp.items()}
        row = dict.fromkeys(PRES1, 0.0)
        for g, share in comp.items():
            for c, v in ATLAS_P19_COMPLETO[g].items():
                row[c] += share * v / 100
        row["Marçal"] = 0.0
        prior[d] = [row[c] for c in PRES1]
    return prior, composicao


def prior_destino(origem, via):
    """Prior do destino de 2º turno condicionada à origem estadual e ao candidato intermediário."""
    if via == "Flávio":
        return [0.99, 0.005, 0.005]
    if via == "Lula":
        return [0.005, 0.99, 0.005]
    if via == "Outros":
        return [0.02, 0.88, 0.10]
    if via == "Não escolha":
        return {"Tarcísio": [0.35, 0.10, 0.55], "Haddad": [0.05, 0.40, 0.55]}.get(
            origem, [0.15, 0.30, 0.55]
        )
    # terceira via: Cury, Renan, Zema, Caiado, Marçal
    return {
        "Tarcísio": [0.67, 0.03, 0.30],
        "Haddad": [0.10, 0.70, 0.20],
        "Outros": [0.10, 0.65, 0.25],
    }.get(origem, [0.26, 0.47, 0.27])


def ipf3(prior, celulas, cols, iters=3000):
    """Ajusta o cubo origem x via x destino: soma em destino = célula do estágio 1; soma em (origem, via) = margem do 2º turno."""
    m = prior * celulas[:, :, None]
    for _ in range(iters):
        m *= (celulas / np.maximum(m.sum(axis=2), 1e-12))[:, :, None]
        m *= (cols / np.maximum(m.sum(axis=(0, 1)), 1e-12))[None, None, :]
    return m


def flow3(nome, fonte, gov1, pres1, pres2, prior1):
    origens = list(gov1)
    p1 = [c for c in PRES1 if pres1.get(c, 0) > 0]
    rows = np.array([gov1[o] for o in origens], dtype=float)
    cols1 = np.array([pres1[c] for c in p1], dtype=float)
    pr1 = np.array(
        [
            [
                prior1[o][PRES1.index(c)]
                + (0.02 if c == "Marçal" and o in ("Tarcísio", "Não escolha") else 0.0)
                for c in p1
            ]
            for o in origens
        ]
    )
    m1 = ipf(pr1, rows * cols1.sum() / rows.sum(), cols1)
    cols2 = np.array([pres2[c] for c in PRES2], dtype=float)
    celulas = m1 * cols2.sum() / m1.sum()
    pr2 = np.array([[prior_destino(o, c) for c in p1] for o in origens])
    cubo = ipf3(pr2, celulas, cols2)
    est1 = {
        o: {c: round(float(m1[i, j]), 2) for j, c in enumerate(p1)}
        for i, o in enumerate(origens)
    }
    est2 = {
        c: {d: round(float(cubo[:, j, k].sum()), 2) for k, d in enumerate(PRES2)}
        for j, c in enumerate(p1)
    }
    est2_tarcisio = {
        c: {d: round(float(cubo[0, j, k]), 2) for k, d in enumerate(PRES2)}
        for j, c in enumerate(p1)
    }
    caminhos = []
    for j, c in enumerate(p1):
        t_c = float(cubo[0, j].sum())
        caminhos.append(
            {
                "via": c,
                "tarcisio_para_via": round(t_c, 2),
                "via_para_lula_pct": round(
                    100 * float(cubo[:, j, 1].sum() / max(cubo[:, j].sum(), 1e-9)), 1
                ),
                "tarcisio_via_lula": round(float(cubo[0, j, 1]), 2),
                "tarcisio_via_flavio": round(float(cubo[0, j, 0]), 2),
                "tarcisio_via_nao_escolha": round(float(cubo[0, j, 2]), 2),
            }
        )
    terceira = [
        k for k in caminhos if k["via"] in ("Cury", "Renan", "Zema", "Caiado", "Marçal")
    ]
    t_total = float(cubo[0].sum())
    return {
        "nome": nome,
        "fonte": fonte,
        "niveis": {"gov1": gov1, "pres1": {c: pres1[c] for c in p1}, "pres2": pres2},
        "estagio1": est1,
        "estagio2": est2,
        "estagio2_origem_tarcisio": est2_tarcisio,
        "caminhos": caminhos,
        "resumo": {
            "tarcisio_total_2t": round(t_total, 2),
            "tarcisio_para_flavio_total": round(float(cubo[0, :, 0].sum()), 2),
            "tarcisio_para_lula_total": round(float(cubo[0, :, 1].sum()), 2),
            "tarcisio_para_nao_escolha_total": round(float(cubo[0, :, 2].sum()), 2),
            "tarcisio_para_lula_direto_1t": round(
                float(cubo[0, p1.index("Lula")].sum()), 2
            ),
            "tarcisio_para_terceira_via": round(
                sum(k["tarcisio_para_via"] for k in terceira), 2
            ),
            "terceira_via_para_lula": round(
                sum(k["tarcisio_via_lula"] for k in terceira), 2
            ),
            "terceira_via_para_flavio": round(
                sum(k["tarcisio_via_flavio"] for k in terceira), 2
            ),
            "terceira_via_para_nao_escolha": round(
                sum(k["tarcisio_via_nao_escolha"] for k in terceira), 2
            ),
            "maior_via_terceira": max(terceira, key=lambda k: k["tarcisio_para_via"])[
                "via"
            ],
            "maior_via_para_lula": max(terceira, key=lambda k: k["tarcisio_via_lula"])[
                "via"
            ],
            "retencao_flavio_pct": round(100 * float(cubo[0, :, 0].sum()) / t_total, 1),
        },
    }


def fluxos_tres_niveis():
    prior1, composicao = prior_estagio1()
    out = [
        flow3(
            "Atlas: governador 1º turno, presidente 1º turno, presidente 2º turno",
            "Atlas/Estadão p. 8, 17 e 21",
            {"Tarcísio": 51.1, "Haddad": 39.9, "Outros": 3.5, "Não escolha": 5.5},
            {
                "Flávio": 39.9,
                "Lula": 36.0,
                "Cury": 8.6,
                "Renan": 6.8,
                "Zema": 1.6,
                "Caiado": 1.5,
                "Outros": 2.8,
                "Não escolha": 2.8,
            },
            {"Flávio": 46.8, "Lula": 43.3, "Não escolha": 9.9},
            prior1,
        ),
        flow3(
            "Datafolha: governador 1º turno, presidente 1º turno, presidente 2º turno",
            "Datafolha p. 8 e Poder360 de 22/08/2026",
            {"Tarcísio": 45, "Haddad": 27, "Outros": 13, "Não escolha": 15},
            {
                "Flávio": 37,
                "Lula": 33,
                "Cury": 3,
                "Renan": 5,
                "Zema": 3,
                "Caiado": 4,
                "Outros": 5,
                "Não escolha": 10,
            },
            {"Flávio": 47, "Lula": 42, "Não escolha": 10},
            prior1,
        ),
        flow3(
            "Real Time: governador 1º turno, presidente 1º turno, presidente 2º turno",
            "Real Time Big Data, laudo de governo p. 7 e laudo presidencial p. 7 e 12",
            {"Tarcísio": 52, "Haddad": 35, "Outros": 2, "Não escolha": 11},
            {
                "Flávio": 38,
                "Lula": 33,
                "Cury": 1,
                "Renan": 7,
                "Zema": 3,
                "Caiado": 4,
                "Marçal": 7,
                "Outros": 1,
                "Não escolha": 6,
            },
            {"Flávio": 44, "Lula": 49, "Não escolha": 7},
            prior1,
        ),
    ]
    return {
        "metodo": (
            "Dois estágios de IPF encadeados. Estágio 1 (governador 1º turno para presidente 1º turno): "
            "a prior de cada candidato a governador é a mistura, pela composição do seu eleitorado por "
            "voto de 2022 (Atlas p. 10, pesos do TSE 2022), das linhas da Atlas p. 19 que dão o voto "
            "presidencial de cada grupo de 2022. Estágio 2 (presidente 1º para 2º turno): prior declarada, "
            "condicionada à origem estadual e ao candidato intermediário, calibrada nos saltos medidos "
            "pela Atlas por grupo de 2022 entre p. 19 e p. 23: eleitor de Tarcísio em 2022 que escolheu "
            "terceira via termina 67% em Flávio, 0% em Lula e 33% na não escolha; eleitor de Garcia, 26%, "
            "47% e 27%. O cubo origem x via x destino é ajustado para fechar as células do estágio 1 e a "
            "margem do 2º turno, sem supor independência dentro do candidato intermediário. Nós são "
            "medição; fitas e caminhos são estimativa."
        ),
        "composicao_gov2026_por_2022": composicao,
        "prior_estagio1": {
            o: dict(zip(PRES1, [round(v, 3) for v in prior1[o]], strict=True))
            for o in prior1
        },
        "prior_estagio2": {
            "terceira via, origem Tarcísio": prior_destino("Tarcísio", "Cury"),
            "terceira via, origem Haddad": prior_destino("Haddad", "Cury"),
            "terceira via, outras origens": prior_destino("Não escolha", "Cury"),
            "não escolha, origem Tarcísio": prior_destino("Tarcísio", "Não escolha"),
        },
        "pesos_2022": PESO_2022,
        "fluxos": out,
    }


if __name__ == "__main__":
    main()
