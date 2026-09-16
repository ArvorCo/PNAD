#!/usr/bin/env python3
"""Monta a base do atlas estadual de setembro de 2026.

Junta tres materiais:

1. A transcricao das pesquisas estaduais Quaest de agosto e setembro. Os PDFs
   sao imagem, entao cada tabela foi lida pagina a pagina e esta declarada aqui
   com o numero da pagina ao lado, como manda o metodo da casa. O extrator
   `estaduais-092026-extract.py` faz a leitura de maquina em paralelo e serve de
   conferencia: o teste compara as duas e falha quando divergem.
2. O resultado de 2022 por municipio, produzido por `estaduais-092026-tse.py`.
3. A agenda declarada da campanha, com veiculo, data e link, coletada na
   imprensa dos proprios estados.

Escreve `docs/assets/estaduais_092026_data.json` e dois CSVs de apoio.

Reproducao:
    python3 scripts/estaduais-092026-tse.py
    python3 scripts/estaduais-092026-data.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSE = ROOT / "data/outputs/estaduais2026"
ASSETS = ROOT / "docs/assets"
DERIV = ROOT / "derivados"

PDF_BASE = "https://quaest.com.br/wp-content/uploads"

# ---------------------------------------------------------------- transcricao
# Cada bloco foi lido na pagina indicada. `pres` e o 1o turno presidencial,
# `gov` a melhor medicao estadual disponivel na mesma amostra, `aliado` a
# pergunta sobre o campo do futuro governador, `problema` o tema mais citado e
# `lula` a aprovacao do governo federal no estado.
POLLS = [
    {
        "uf": "BA",
        "nome": "Bahia",
        "arquivo": "2026/08/QUAEST1BA2708.pdf",
        "campo": "2026-08-26",
        "pres": {
            "pagina": 75,
            "Lula": 53,
            "Flávio": 16,
            "Cury": 3,
            "Caiado": 3,
            "Marçal": 2,
            "Pimenta": 1,
            "Renan": 1,
            "Zema": 1,
            "Indecisos": 13,
            "Branco/nulo": 7,
        },
        "gov": {
            "pagina": 28,
            "turno": 2,
            "direita": ["ACM Neto", "União", 44],
            "esquerda": ["Jerônimo Rodrigues", "PT", 41],
            "serie": [["Abr/26", 41, 38], ["Jul/26", 43, 39], ["Ago/26", 44, 41]],
        },
        "aliado": {
            "pagina": 41,
            "Lula": 49,
            "Independente": 30,
            "Flávio": 16,
            "NS/NR": 5,
        },
        "problema": {
            "pagina": 113,
            "Violência": 38,
            "Saúde": 32,
            "Desemprego": 6,
            "Educação": 4,
            "Economia": 3,
            "Corrupção": 2,
            "Pobreza": 2,
            "Infraestrutura": 1,
            "Outros": 3,
            "Nenhum": 1,
            "NS/NR": 8,
        },
        "lula": {"pagina": 92, "aprova": 59, "desaprova": 36},
    },
    {
        "uf": "PE",
        "nome": "Pernambuco",
        "arquivo": "2026/09/QUAEST2PE0809.pdf",
        "campo": "2026-09-07",
        "pres": {
            "pagina": 54,
            "Lula": 54,
            "Flávio": 20,
            "Cury": 5,
            "Renan": 2,
            "Caiado": 2,
            "Marçal": 1,
            "Indecisos": 9,
            "Branco/nulo": 7,
        },
        "pres_2t": {
            "pagina": 72,
            "Lula": 57,
            "Flávio": 26,
            "Branco/nulo": 11,
            "Indecisos": 6,
        },
        "gov": {
            "pagina": 19,
            "turno": 2,
            "direita": ["Raquel Lyra", "PSD", 45],
            "esquerda": ["João Campos", "PSB", 39],
            "serie": [
                ["Abr/26", 38, 46],
                ["Jul/26", 45, 39],
                ["Ago/26", 47, 37],
                ["Set/26", 45, 39],
            ],
        },
        "aliado": {
            "pagina": 33,
            "Lula": 50,
            "Independente": 29,
            "Flávio": 17,
            "NS/NR": 4,
        },
        "problema": {
            "pagina": 105,
            "Saúde": 33,
            "Violência": 21,
            "Corrupção": 5,
            "Desemprego": 5,
            "Educação": 5,
            "Infraestrutura": 4,
            "Economia": 3,
            "Pobreza": 3,
            "Enchentes": 2,
            "Outros": 8,
            "Nenhum": 1,
            "NS/NR": 10,
        },
        "lula": {"pagina": 84, "aprova": 62, "desaprova": 31},
        "nota": (
            "Aliado, problema e aprovacao vem da onda de 24/08 "
            "(QUAEST1PE2508.pdf, p. 33, 105 e 84); presidente e governador, da onda de 07/09."
        ),
    },
    {
        "uf": "CE",
        "nome": "Ceará",
        "arquivo": "2026/09/QUAEST1CE0409.pdf",
        "campo": "2026-09-03",
        "pres": {
            "pagina": 67,
            "Lula": 51,
            "Flávio": 16,
            "Cury": 9,
            "Renan": 2,
            "Marçal": 2,
            "Caiado": 1,
            "Indecisos": 11,
            "Branco/nulo": 8,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Ciro Gomes", "PSDB", 49],
            "esquerda": ["Elmano de Freitas", "PT", 36],
            "serie": [["Abr/26", 46, 35], ["Jul/26", 48, 35], ["Set/26", 49, 36]],
        },
        "aliado": {
            "pagina": 33,
            "Lula": 46,
            "Independente": 36,
            "Flávio": 15,
            "NS/NR": 3,
        },
        "problema": {
            "pagina": 105,
            "Violência": 54,
            "Saúde": 15,
            "Corrupção": 4,
            "Desemprego": 4,
            "Economia": 4,
            "Pobreza": 3,
            "Educação": 2,
            "Infraestrutura": 1,
            "Outros": 2,
            "Nenhum": 1,
            "NS/NR": 10,
        },
        "lula": {"pagina": 84, "aprova": 60, "desaprova": 34},
    },
    {
        "uf": "MA",
        "nome": "Maranhão",
        "arquivo": "2026/08/QUAEST1MA2408.pdf",
        "campo": "2026-08-23",
        "pres": {
            "pagina": 58,
            "Lula": 57,
            "Flávio": 20,
            "Renan": 2,
            "Caiado": 1,
            "Marçal": 1,
            "Cury": 1,
            "Hertz": 1,
            "Indecisos": 12,
            "Branco/nulo": 5,
        },
        "gov": {
            "pagina": 8,
            "turno": 1,
            "direita": ["Eduardo Braide", "PSD", 44],
            "esquerda": ["Felipe Camarão", "PT", 6],
            "terceiro": ["Orleans Brandão", "MDB", 25],
        },
        "aliado": {
            "pagina": 24,
            "Lula": 54,
            "Independente": 25,
            "Flávio": 16,
            "NS/NR": 5,
        },
        "problema": {
            "pagina": 96,
            "Saúde": 28,
            "Infraestrutura": 21,
            "Violência": 11,
            "Desemprego": 6,
            "Pobreza": 5,
            "Economia": 4,
            "Corrupção": 4,
            "Educação": 4,
            "Outros": 5,
            "Nenhum": 3,
            "NS/NR": 9,
        },
        "lula": {"pagina": 75, "aprova": 66, "desaprova": 27},
    },
    {
        "uf": "PA",
        "nome": "Pará",
        "arquivo": "2026/08/QUAEST1PAR012908.pdf",
        "campo": "2026-08-28",
        "pres": {
            "pagina": 67,
            "Lula": 39,
            "Flávio": 28,
            "Cury": 5,
            "Renan": 3,
            "Caiado": 2,
            "Marçal": 2,
            "Samara": 1,
            "Indecisos": 15,
            "Branco/nulo": 5,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Dr. Daniel", "Podemos", 36],
            "esquerda": ["Hana Ghassan", "MDB", 36],
            "serie": [["Abr/26", 34, 29], ["Jul/26", 35, 36], ["Ago/26", 36, 36]],
        },
        "aliado": {
            "pagina": 33,
            "Lula": 34,
            "Independente": 31,
            "Flávio": 29,
            "NS/NR": 6,
        },
        "problema": {
            "pagina": 105,
            "Saúde": 35,
            "Violência": 12,
            "Infraestrutura": 10,
            "Desemprego": 7,
            "Economia": 5,
            "Corrupção": 5,
            "Educação": 3,
            "Enchentes": 2,
            "Pobreza": 2,
            "Outros": 6,
            "NS/NR": 13,
        },
        "lula": {"pagina": 84, "aprova": 47, "desaprova": 46},
    },
    {
        "uf": "AM",
        "nome": "Amazonas",
        "arquivo": "2026/08/QUAEST1AM2508.pdf",
        "campo": "2026-08-28",
        "pres": {
            "pagina": 108,
            "Lula": 38,
            "Flávio": 35,
            "Marçal": 2,
            "Renan": 2,
            "Cury": 1,
            "Caiado": 1,
            "Zema": 1,
            "Indecisos": 12,
            "Branco/nulo": 8,
        },
        "gov": {
            "pagina": 21,
            "turno": 2,
            "direita": ["Omar Aziz", "PSD", 45],
            "esquerda": ["Professora Maria do Carmo", "PL", 44],
            "nota": "Os dois finalistas sao do campo governista estadual; a candidata do PL e a segunda.",
        },
        "aliado": {
            "pagina": 74,
            "Lula": 34,
            "Independente": 33,
            "Flávio": 28,
            "NS/NR": 5,
        },
        "problema": {
            "pagina": 146,
            "Saúde": 32,
            "Violência": 17,
            "Infraestrutura": 9,
            "Educação": 7,
            "Corrupção": 6,
            "Desemprego": 5,
            "Economia": 3,
            "Pobreza": 2,
            "Enchentes": 1,
            "Outros": 9,
            "Nenhum": 1,
            "NS/NR": 8,
        },
        "lula": {"pagina": 125, "aprova": 54, "desaprova": 43},
    },
    {
        "uf": "AL",
        "nome": "Alagoas",
        "arquivo": "2026/08/QUAEST1AL2408.pdf",
        "campo": "2026-08-24",
        "pres": {
            "pagina": 67,
            "Lula": 45,
            "Flávio": 30,
            "Renan": 2,
            "Marçal": 1,
            "Cury": 1,
            "Indecisos": 11,
            "Branco/nulo": 10,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["JHC", "PSDB", 42],
            "esquerda": ["Renan Filho", "MDB", 42],
        },
        "aliado": {
            "pagina": 33,
            "Lula": 42,
            "Independente": 30,
            "Flávio": 22,
            "NS/NR": 6,
        },
        "problema": {
            "pagina": 105,
            "Saúde": 41,
            "Violência": 16,
            "Desemprego": 8,
            "Educação": 4,
            "Economia": 3,
            "Corrupção": 3,
            "Pobreza": 2,
            "Infraestrutura": 1,
            "Outros": 4,
            "Nenhum": 2,
            "NS/NR": 16,
        },
        "lula": {"pagina": 84, "aprova": 52, "desaprova": 40},
    },
    {
        "uf": "TO",
        "nome": "Tocantins",
        "arquivo": "2026/08/QUAEST1TO2508.pdf",
        "campo": "2026-08-25",
        "pres": {
            "pagina": 108,
            "Lula": 39,
            "Flávio": 32,
            "Caiado": 7,
            "Marçal": 4,
            "Renan": 2,
            "Cury": 1,
            "Indecisos": 11,
            "Branco/nulo": 4,
        },
        "gov": {
            "pagina": 21,
            "turno": 2,
            "direita": ["Professora Dorinha", "União", 46],
            "esquerda": ["Vicentinho Júnior", "PSDB", 38],
            "nota": "Os dois finalistas sao do campo de direita; nao ha candidatura do PT no 2o turno medido.",
        },
        "aliado": {
            "pagina": 74,
            "Lula": 35,
            "Flávio": 33,
            "Independente": 28,
            "NS/NR": 4,
        },
        "problema": {
            "pagina": 146,
            "Saúde": 41,
            "Violência": 8,
            "Infraestrutura": 7,
            "Corrupção": 6,
            "Economia": 6,
            "Desemprego": 5,
            "Educação": 5,
            "Pobreza": 1,
            "Outros": 3,
            "Nenhum": 2,
            "NS/NR": 16,
        },
        "lula": {"pagina": 125, "aprova": 49, "desaprova": 44},
    },
    {
        "uf": "PB",
        "nome": "Paraíba",
        "arquivo": "2026/08/QUAEST1PB2508.pdf",
        "campo": "2026-08-25",
        "pres": {
            "pagina": 86,
            "Lula": 55,
            "Flávio": 22,
            "Renan": 2,
            "Caiado": 2,
            "Cury": 2,
            "Zema": 1,
            "Marçal": 1,
            "Indecisos": 6,
            "Branco/nulo": 9,
        },
        "gov": {
            "pagina": 23,
            "turno": 2,
            "direita": ["Lucas Ribeiro", "PP", 47],
            "esquerda": ["Efraim Filho", "PL", 33],
            "nota": "Os dois finalistas sao do campo de direita.",
        },
        "aliado": {
            "pagina": 52,
            "Lula": 53,
            "Independente": 25,
            "Flávio": 20,
            "NS/NR": 2,
        },
        "problema": {
            "pagina": 124,
            "Saúde": 31,
            "Violência": 23,
            "Desemprego": 6,
            "Economia": 5,
            "Corrupção": 4,
            "Infraestrutura": 4,
            "Pobreza": 4,
            "Educação": 3,
            "Outros": 8,
            "Nenhum": 2,
            "NS/NR": 10,
        },
        "lula": {"pagina": 103, "aprova": 61, "desaprova": 35},
    },
    {
        "uf": "RN",
        "nome": "Rio Grande do Norte",
        "arquivo": "2026/08/QUAEST1RN2408.pdf",
        "campo": "2026-08-24",
        "pres": {
            "pagina": 84,
            "Lula": 56,
            "Flávio": 19,
            "Caiado": 1,
            "Renan": 1,
            "Marçal": 1,
            "Cury": 1,
            "Indecisos": 10,
            "Branco/nulo": 11,
        },
        "gov": {
            "pagina": 21,
            "turno": 2,
            "direita": ["Allyson Bezerra", "União", 35],
            "esquerda": ["Cadu de Lula", "PT", 34],
        },
        "aliado": {
            "pagina": 50,
            "Lula": 40,
            "Independente": 36,
            "Flávio": 17,
            "NS/NR": 7,
        },
        "problema": {
            "pagina": 122,
            "Saúde": 38,
            "Violência": 20,
            "Corrupção": 9,
            "Infraestrutura": 5,
            "Educação": 5,
            "Desemprego": 5,
            "Economia": 3,
            "Pobreza": 3,
            "Outros": 4,
            "Nenhum": 1,
            "NS/NR": 7,
        },
        "lula": {"pagina": 101, "aprova": 60, "desaprova": 35},
    },
    {
        "uf": "AP",
        "nome": "Amapá",
        "arquivo": "2026/08/QUAEST1AP2508.pdf",
        "campo": "2026-08-25",
        "pres": {
            "pagina": 67,
            "Lula": 36,
            "Flávio": 32,
            "Renan": 3,
            "Marçal": 2,
            "Cury": 2,
            "Caiado": 2,
            "Zema": 1,
            "Pimenta": 1,
            "Indecisos": 14,
            "Branco/nulo": 7,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Dr. Furlan", "PSD", 54],
            "esquerda": ["Clécio Luís", "União", 36],
            "nota": "Os dois finalistas sao do campo governista estadual.",
        },
        "aliado": {
            "pagina": 33,
            "Lula": 34,
            "Independente": 31,
            "Flávio": 30,
            "NS/NR": 5,
        },
        "problema": {
            "pagina": 105,
            "Saúde": 43,
            "Desemprego": 10,
            "Infraestrutura": 9,
            "Corrupção": 6,
            "Violência": 6,
            "Economia": 4,
            "Educação": 4,
            "Pobreza": 2,
            "Outros": 8,
            "NS/NR": 8,
        },
        "lula": {"pagina": 84, "aprova": 46, "desaprova": 47},
    },
    {
        "uf": "AC",
        "nome": "Acre",
        "arquivo": "2026/08/QUAEST1AC2708.pdf",
        "campo": "2026-08-27",
        "pres": {
            "pagina": 108,
            "Flávio": 44,
            "Lula": 24,
            "Caiado": 5,
            "Marçal": 3,
            "Cury": 1,
            "Renan": 1,
            "Zema": 1,
            "Indecisos": 14,
            "Branco/nulo": 7,
        },
        "gov": {
            "pagina": 21,
            "turno": 2,
            "direita": ["Alan Rick", "Republicanos", 42],
            "esquerda": ["Mailza Assis", "PP", 35],
            "nota": "Os dois finalistas sao do campo de direita.",
        },
        "aliado": {
            "pagina": 74,
            "Flávio": 41,
            "Independente": 33,
            "Lula": 20,
            "NS/NR": 6,
        },
        "problema": {
            "pagina": 146,
            "Saúde": 26,
            "Corrupção": 13,
            "Violência": 11,
            "Desemprego": 8,
            "Infraestrutura": 7,
            "Economia": 4,
            "Educação": 4,
            "Pobreza": 4,
            "Enchentes": 1,
            "Outros": 10,
            "NS/NR": 12,
        },
        "lula": {"pagina": 125, "aprova": 36, "desaprova": 57},
    },
    {
        "uf": "RR",
        "nome": "Roraima",
        "arquivo": "2026/08/QUAEST1RR2708.pdf",
        "campo": "2026-08-27",
        "pres": {
            "pagina": 64,
            "Flávio": 54,
            "Lula": 17,
            "Renan": 4,
            "Marçal": 4,
            "Caiado": 2,
            "Cury": 2,
            "Zema": 1,
            "Indecisos": 11,
            "Branco/nulo": 5,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Arthur Henrique", "PL", 60],
            "esquerda": ["Soldado Sampaio", "Republicanos", 28],
            "nota": "Os dois finalistas sao do campo de direita.",
        },
        "aliado": {
            "pagina": 33,
            "Flávio": 49,
            "Independente": 35,
            "Lula": 12,
            "NS/NR": 4,
        },
        "problema": {
            "pagina": 102,
            "Saúde": 50,
            "Infraestrutura": 7,
            "Economia": 6,
            "Violência": 6,
            "Educação": 5,
            "Corrupção": 4,
            "Desemprego": 3,
            "Imigração": 3,
            "Pobreza": 1,
            "Outros": 5,
            "Nenhum": 1,
            "NS/NR": 9,
        },
        "lula": {"pagina": 81, "aprova": 28, "desaprova": 66},
    },
    {
        "uf": "RO",
        "nome": "Rondônia",
        "arquivo": "2026/08/QUAEST1RO2508.pdf",
        "campo": "2026-08-25",
        "pres": {
            "pagina": 108,
            "Flávio": 46,
            "Lula": 25,
            "Marçal": 2,
            "Zema": 2,
            "Renan": 2,
            "Caiado": 2,
            "Indecisos": 13,
            "Branco/nulo": 8,
        },
        "gov": {
            "pagina": 21,
            "turno": 2,
            "direita": ["Marcos Rogério", "PL", 40],
            "esquerda": ["Adailton Fúria", "PSD", 29],
            "nota": "Os dois finalistas sao do campo de direita.",
        },
        "aliado": {
            "pagina": 74,
            "Flávio": 43,
            "Independente": 30,
            "Lula": 23,
            "NS/NR": 4,
        },
        "problema": {
            "pagina": 146,
            "Saúde": 37,
            "Violência": 13,
            "Infraestrutura": 9,
            "Corrupção": 7,
            "Desemprego": 4,
            "Economia": 4,
            "Educação": 3,
            "Pobreza": 2,
            "Enchentes": 1,
            "Outros": 9,
            "Nenhum": 1,
            "NS/NR": 10,
        },
        "lula": {"pagina": 125, "aprova": 35, "desaprova": 56},
    },
    {
        "uf": "RJ",
        "nome": "Rio de Janeiro",
        "arquivo": "2026/09/QUAEST2RJ0809.pdf",
        "campo": "2026-09-07",
        "pres": {
            "pagina": 62,
            "Flávio": 35,
            "Lula": 33,
            "Cury": 5,
            "Caiado": 2,
            "Renan": 2,
            "Marçal": 1,
            "Zema": 1,
            "Samara": 1,
            "Indecisos": 10,
            "Branco/nulo": 10,
        },
        "pres_2t": {
            "pagina": 81,
            "Flávio": 43,
            "Lula": 37,
            "Branco/nulo": 15,
            "Indecisos": 5,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Eduardo Paes", "PSD", 52],
            "esquerda": ["Douglas Ruas", "PL", 26],
            "nota": "Paes disputa contra o candidato do PL; a comparacao inverte o sinal do vao.",
        },
        "lula": {"pagina": 0, "aprova": 0, "desaprova": 0},
    },
    {
        "uf": "SP",
        "nome": "São Paulo",
        "arquivo": "2026/09/QUAEST2SP0809.pdf",
        "campo": "2026-09-07",
        "pres": {
            "pagina": 53,
            "Flávio": 31,
            "Lula": 30,
            "Cury": 7,
            "Marçal": 4,
            "Caiado": 3,
            "Renan": 2,
            "Zema": 1,
            "Indecisos": 12,
            "Branco/nulo": 10,
        },
        "pres_2t": {
            "pagina": 72,
            "Flávio": 41,
            "Lula": 33,
            "Branco/nulo": 16,
            "Indecisos": 10,
        },
        "gov": {
            "pagina": 19,
            "turno": 2,
            "direita": ["Tarcísio", "Republicanos", 48],
            "esquerda": ["Fernando Haddad", "PT", 31],
        },
        "lula": {"pagina": 0, "aprova": 0, "desaprova": 0},
    },
    {
        "uf": "MG",
        "nome": "Minas Gerais",
        "arquivo": "2026/09/QUAEST2MG0809.pdf",
        "campo": "2026-09-07",
        "pres": {
            "pagina": 93,
            "Lula": 32,
            "Flávio": 28,
            "Cury": 8,
            "Zema": 5,
            "Caiado": 3,
            "Marçal": 2,
            "Renan": 2,
            "Indecisos": 13,
            "Branco/nulo": 7,
        },
        "pres_2t": {
            "pagina": 112,
            "Flávio": 40,
            "Lula": 37,
            "Branco/nulo": 15,
            "Indecisos": 8,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Cleitinho Azevedo", "Republicanos", 49],
            "esquerda": ["Alexandre Kalil", "PDT", 27],
        },
        "lula": {"pagina": 0, "aprova": 0, "desaprova": 0},
    },
    {
        "uf": "DF",
        "nome": "Distrito Federal",
        "arquivo": "2026/09/QUAEST2DF0809.pdf",
        "campo": "2026-09-07",
        "pres": {
            "pagina": 72,
            "Flávio": 32,
            "Lula": 30,
            "Caiado": 10,
            "Cury": 8,
            "Renan": 2,
            "Zema": 1,
            "Marçal": 1,
            "Samara": 1,
            "Indecisos": 9,
            "Branco/nulo": 6,
        },
        "pres_2t": {
            "pagina": 91,
            "Flávio": 45,
            "Lula": 38,
            "Indecisos": 4,
            "Branco/nulo": 13,
        },
        "gov": {
            "pagina": 20,
            "turno": 2,
            "direita": ["Celina Leão", "PP", 47],
            "esquerda": ["Arruda", "PSD", 30],
            "nota": "Os dois finalistas sao do campo de direita.",
        },
        "lula": {"pagina": 0, "aprova": 0, "desaprova": 0},
    },
]

# ------------------------------------------------------------------- agenda
# Roteiro declarado, com veiculo e link. `pre` marca a pre-campanha; `campanha`,
# os atos ja na campanha oficial.
AGENDA = {
    "visitados_pre": [
        "RO",
        "PA",
        "MA",
        "BA",
        "PB",
        "RN",
        "GO",
        "MT",
        "MS",
        "DF",
        "ES",
        "RJ",
        "SP",
        "MG",
        "PR",
        "SC",
        "RS",
    ],
    "nao_visitados_pre": ["AC", "AP", "AM", "RR", "TO", "AL", "CE", "PE", "PI", "SE"],
    "fonte_roteiro": {
        "veiculo": "Revista Fórum",
        "titulo": "Flávio Bolsonaro já foi mais aos EUA do que a 10 estados do Norte e Nordeste",
        "url": "https://revistaforum.com.br/politica/flavio-bolsonaro-eua-nordeste/",
    },
    "fonte_roteiro_2": {
        "veiculo": "BPMoney",
        "titulo": "Flávio Bolsonaro faz sexta viagem aos EUA; dez estados brasileiros seguem fora da pré-campanha",
        "url": "https://bpmoney.com.br/politica/flavio-bolsonaro-sexta-viagem-eua-dez-estados-fora-roteiro-pre-campanha",
    },
    "atos": [
        {
            "uf": "CE",
            "data": "2026-09-15",
            "cidades": ["Fortaleza", "Juazeiro do Norte"],
            "formato": "ato no Conjunto Ceará e carreata no Cariri",
            "veiculo": "O Povo",
            "url": "https://www.opovo.com.br/noticias/politica/eleicoes/2026/09/14/flavio-bolsonaro-no-ceara-veja-agenda-em-fortaleza-e-cariri.html",
        },
        {
            "uf": "PE",
            "data": "2026-09-16",
            "cidades": ["Recife"],
            "formato": "caminhada do Marco Zero ao Cais da Alfândega e comício",
            "veiculo": "Diario de Pernambuco",
            "url": "https://www.diariodepernambuco.com.br/politica/2026/09/11723778-flavio-bolsonaro-confirma-agenda-com-caminhada-e-comicio-no-recife-antigo.html",
            "retirado": "Santa Cruz do Capibaribe",
        },
        {
            "uf": "BA",
            "data": "2026-09-17",
            "cidades": ["Vitória da Conquista"],
            "formato": "carreata e ato no Estádio Lomanto Júnior",
            "veiculo": "A Tarde",
            "url": "https://atarde.com.br/politica/flavio-bolsonaro-fara-primeiro-ato-de-campanha-na-bahia-em-conquista-1401442",
            "trocado": "Salvador",
        },
    ],
}

CAPITAIS = {
    "AC": "RIO BRANCO",
    "AL": "MACEIÓ",
    "AM": "MANAUS",
    "AP": "MACAPÁ",
    "BA": "SALVADOR",
    "CE": "FORTALEZA",
    "MA": "SÃO LUÍS",
    "PA": "BELÉM",
    "PB": "JOÃO PESSOA",
    "PE": "RECIFE",
    "PI": "TERESINA",
    "RN": "NATAL",
    "RO": "PORTO VELHO",
    "RR": "BOA VISTA",
    "SE": "ARACAJU",
    "TO": "PALMAS",
}
NORDESTE = ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]
NORTE = ["AC", "AM", "AP", "PA", "RO", "RR", "TO"]


MINUSCULAS = {"da", "de", "do", "das", "dos", "e", "em", "a", "o"}


def titulo(nome: str) -> str:
    """Caixa de titulo em portugues: conectivo fica minusculo."""
    partes = nome.title().split()
    return " ".join(
        parte if index == 0 or parte.lower() not in MINUSCULAS else parte.lower()
        for index, parte in enumerate(partes)
    )


def load_municipios() -> list[dict]:
    rows = []
    with (TSE / "municipios.csv").open() as handle:
        for row in csv.DictReader(handle):
            for key in (
                "eleitores_2026",
                "lula_1t",
                "bolsonaro_1t",
                "ciro_1t",
                "tebet_1t",
                "validos_1t",
                "lula_2t",
                "bolsonaro_2t",
            ):
                row[key] = int(row[key]) if row[key].isdigit() else 0
            for key in ("bolsonaro_2t_pct", "bolsonaro_1t_pct"):
                row[key] = float(row[key]) if row[key] else 0.0
            rows.append(row)
    return rows


def por_uf(municipios: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in municipios:
        entry = out.setdefault(
            row["uf"],
            {"bolsonaro_2t": 0, "lula_2t": 0, "bolsonaro_1t": 0, "eleitores_2026": 0},
        )
        for key in entry:
            entry[key] += row[key]
    for entry in out.values():
        total = entry["bolsonaro_2t"] + entry["lula_2t"]
        entry["bolsonaro_2t_pct"] = (
            round(100 * entry["bolsonaro_2t"] / total, 2) if total else 0
        )
    return out


def vao(poll: dict) -> dict:
    """Teto enderecavel do estado: melhor medicao da direita menos Flavio."""
    gov = poll["gov"]
    direita = gov["direita"]
    flavio_1t = poll["pres"].get("Flávio", 0)
    base = {
        "uf": poll["uf"],
        "nome": poll["nome"],
        "campo": poll["campo"],
        "candidato": direita[0],
        "partido": direita[1],
        "gov": direita[2],
        "gov_turno": gov["turno"],
        "flavio_1t": flavio_1t,
        "vao_1t": direita[2] - flavio_1t,
        "pagina_gov": gov["pagina"],
        "pagina_pres": poll["pres"]["pagina"],
        "nota": gov.get("nota", ""),
    }
    if "pres_2t" in poll and gov["turno"] == 2:
        flavio_2t = poll["pres_2t"].get("Flávio", 0)
        base["flavio_2t"] = flavio_2t
        base["vao_2t"] = direita[2] - flavio_2t
        base["pagina_pres_2t"] = poll["pres_2t"]["pagina"]
    return base


def concentracao(municipios: list[dict], ufs: list[str]) -> dict:
    sel = sorted(
        (m for m in municipios if m["uf"] in ufs),
        key=lambda m: -m["bolsonaro_2t"],
    )
    total = sum(m["bolsonaro_2t"] for m in sel)
    curva, acumulado = [], 0
    meia = None
    for index, row in enumerate(sel, 1):
        acumulado += row["bolsonaro_2t"]
        if meia is None and acumulado >= total * 0.5:
            meia = index
        if index <= 120 or index % 25 == 0:
            curva.append([index, round(100 * acumulado / total, 3)])
    return {
        "municipios": len(sel),
        "votos": total,
        "metade_em": meia,
        "metade_pct_municipios": round(100 * (meia or 0) / len(sel), 2),
        "curva": curva,
    }


def main() -> None:
    municipios = load_municipios()
    ufs = por_uf(municipios)
    index = {(m["uf"], m["municipio"]): m for m in municipios}

    vaos = [vao(p) for p in POLLS if p["gov"]["direita"][2]]
    vaos.sort(key=lambda v: -v["vao_1t"])

    nao_vis = AGENDA["nao_visitados_pre"]
    estoque_nao_visitado = sum(ufs[u]["bolsonaro_2t"] for u in nao_vis if u in ufs)
    eleitorado_nao_visitado = sum(ufs[u]["eleitores_2026"] for u in nao_vis if u in ufs)

    capitais = []
    for uf, nome in CAPITAIS.items():
        row = index.get((uf, nome))
        if not row:
            continue
        capitais.append(
            {
                "uf": uf,
                "municipio": titulo(nome),
                "bolsonaro_2t": row["bolsonaro_2t"],
                "bolsonaro_2t_pct": row["bolsonaro_2t_pct"],
                "lula_2t": row["lula_2t"],
                "eleitores_2026": row["eleitores_2026"],
                "venceu": row["bolsonaro_2t"] > row["lula_2t"],
                "nao_visitado": uf in nao_vis,
            }
        )
    capitais.sort(key=lambda c: -c["bolsonaro_2t"])

    alvos = sorted(
        (
            m
            for m in municipios
            if m["uf"] in NORDESTE + NORTE and m["eleitores_2026"] >= 40000
        ),
        key=lambda m: -m["bolsonaro_2t"],
    )[:40]
    alvos = [
        {
            "uf": m["uf"],
            "municipio": titulo(m["municipio"]),
            "bolsonaro_2t": m["bolsonaro_2t"],
            "bolsonaro_2t_pct": m["bolsonaro_2t_pct"],
            "eleitores_2026": m["eleitores_2026"],
            "venceu": m["bolsonaro_2t"] > m["lula_2t"],
            "capital": CAPITAIS.get(m["uf"]) == m["municipio"],
            "nao_visitado": m["uf"] in nao_vis,
        }
        for m in alvos
    ]

    mat = [m for m in municipios if m["matopiba"] == "1"]
    matopiba = {
        "municipios": len(mat),
        "bolsonaro_2t": sum(m["bolsonaro_2t"] for m in mat),
        "lula_2t": sum(m["lula_2t"] for m in mat),
        "eleitores_2026": sum(m["eleitores_2026"] for m in mat),
        "cidades": sorted(
            (
                {
                    "uf": m["uf"],
                    "municipio": titulo(m["municipio"]),
                    "bolsonaro_2t": m["bolsonaro_2t"],
                    "bolsonaro_2t_pct": m["bolsonaro_2t_pct"],
                    "eleitores_2026": m["eleitores_2026"],
                }
                for m in mat
            ),
            key=lambda m: -m["bolsonaro_2t"],
        ),
    }
    matopiba["bolsonaro_2t_pct"] = round(
        100
        * matopiba["bolsonaro_2t"]
        / (matopiba["bolsonaro_2t"] + matopiba["lula_2t"]),
        2,
    )

    temas: dict[str, list] = {}
    for poll in POLLS:
        if "problema" not in poll:
            continue
        itens = {
            k: v
            for k, v in poll["problema"].items()
            if k not in ("pagina", "Outros", "Nenhum", "NS/NR")
        }
        temas[poll["uf"]] = sorted(itens.items(), key=lambda kv: -kv[1])

    payload = {
        "meta": {
            "titulo": "Atlas estadual de setembro de 2026",
            "corte": "2026-09-16",
            "institutos": ["Quaest/Globo"],
            "ufs_pesquisadas": [p["uf"] for p in POLLS],
            "sem_pesquisa_estadual": ["PI", "SE"],
            "pdf_base": PDF_BASE,
        },
        "pesquisas": POLLS,
        "agenda": AGENDA,
        "vaos": vaos,
        "ufs": ufs,
        "capitais": capitais,
        "alvos": alvos,
        "matopiba": matopiba,
        "temas": temas,
        "nao_visitados": {
            "ufs": nao_vis,
            "bolsonaro_2t": estoque_nao_visitado,
            "eleitores_2026": eleitorado_nao_visitado,
            "detalhe": sorted(
                (
                    {
                        "uf": u,
                        "bolsonaro_2t": ufs[u]["bolsonaro_2t"],
                        "bolsonaro_2t_pct": ufs[u]["bolsonaro_2t_pct"],
                        "eleitores_2026": ufs[u]["eleitores_2026"],
                        "venceu_2022": ufs[u]["bolsonaro_2t"] > ufs[u]["lula_2t"],
                    }
                    for u in nao_vis
                    if u in ufs
                ),
                key=lambda d: -d["eleitores_2026"],
            ),
        },
        "concentracao": {
            "nordeste": concentracao(municipios, NORDESTE),
            "norte": concentracao(municipios, NORTE),
        },
    }

    ASSETS.mkdir(parents=True, exist_ok=True)
    DERIV.mkdir(parents=True, exist_ok=True)
    (ASSETS / "estaduais_092026_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1)
    )
    with (DERIV / "estaduais-092026-vao.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "uf",
                "nome",
                "campo",
                "candidato",
                "partido",
                "gov",
                "gov_turno",
                "flavio_1t",
                "vao_1t",
                "flavio_2t",
                "vao_2t",
                "pagina_gov",
                "pagina_pres",
                "pagina_pres_2t",
                "nota",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(vaos)
    with (DERIV / "estaduais-092026-alvos.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(alvos[0]))
        writer.writeheader()
        writer.writerows(alvos)

    print(f"pesquisas: {len(POLLS)} estados")
    print(f"vao maximo: {vaos[0]['nome']} {vaos[0]['vao_1t']} pontos")
    print(
        f"nao visitados: {len(nao_vis)} UFs, {estoque_nao_visitado:,} votos Bolsonaro 2022"
    )
    print(
        f"MATOPIBA: {matopiba['bolsonaro_2t']:,} votos ({matopiba['bolsonaro_2t_pct']}%)"
    )
    print("Gerado:", ASSETS / "estaduais_092026_data.json")


if __name__ == "__main__":
    main()
