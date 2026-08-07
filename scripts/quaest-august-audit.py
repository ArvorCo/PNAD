#!/usr/bin/env python3
"""Build the evidence ledger for the August 2026 Genial/Quaest audit.

The script reads the archived PDFs, compares the July and August territorial
annexes, and writes reproducible JSON/CSV artifacts for the public dossier.
Editorial judgments stay in the HTML. No respondent-level outcome is inferred
from census-sector geography.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from statistics import NormalDist

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/pesquisas/quaest/2026-08"
JULY_SOURCE = ROOT / "data/pesquisas/quaest/2026-07"
OUTPUT = ROOT / "docs/assets/quaest_082026_data.json"
TERRITORY_OUTPUT = ROOT / "docs/assets/quaest_082026_territory.json"
AUGUST_CSV = SOURCE / "quaest_bairros_0826.csv"
REFERENCE = (
    ROOT
    / "data/originals/censo_2022_setores_censitarios"
    / "quaest_sector_reference_2026-08-07.json"
)
PNAD_INCOME_CANDIDATES = (
    ROOT / "data/outputs/base_anual_visita1_labeled_npv.csv",
    Path.home() / "arvor/PNAD/data/outputs/base_anual_visita1_labeled_npv.csv",
)

PUBLISHED_QUESTIONS = {
    2,
    3,
    4,
    6,
    8,
    *range(9, 29),
    *range(44, 61),
    64,
    67,
    69,
    *range(74, 78),
    *range(79, 82),
    99,
    *range(103, 108),
}

UNPUBLISHED_GROUPS = [
    {
        "name": "Operacionais",
        "questions": [1, 5, 7],
        "note": "Elegibilidade, ocupação e consentimento de gravação.",
    },
    {
        "name": "Resultado desejado e vencedor esperado",
        "questions": [29, 30],
        "note": "Que campo deveria vencer e quem o eleitor espera que vença.",
    },
    {
        "name": "Religião, vice, Senado e decisão",
        "questions": list(range(31, 44)),
        "note": "Treze itens eleitorais, incluindo cinco nomes para vice.",
    },
    {
        "name": "Estados Unidos e apoio de Trump",
        "questions": [61, 62, 63, 65, 66, 68],
        "note": "Favorabilidade, alinhamento, endosso, dano e reação ao tarifaço.",
    },
    {
        "name": "Milei e vídeo de Jair por IA",
        "questions": [70, 71, 72, 73],
        "note": "Conhecimento e efeito de endosso, além de vídeo artificial.",
    },
    {
        "name": "Conflito e reconciliação Michelle-Flávio",
        "questions": [78, 82],
        "note": "O relatório mostra as pazes, mas omite o conflito e o efeito no voto.",
    },
    {
        "name": "Confiança em 16 instituições e pessoas",
        "questions": list(range(83, 99)),
        "note": "Bloco completo de confiança ficou fora do relatório.",
    },
    {
        "name": "Ideologia e afetos políticos",
        "questions": [100, 101, 102],
        "note": "Esquerda-centro-direita, PT e Jair Bolsonaro.",
    },
    {
        "name": "Validação eleitoral",
        "questions": [108, 109],
        "note": "Voto recordado em 2022 e comparecimento declarado em 2024.",
    },
]

VOTE = {
    "first_round": {
        "dates": ["jun/26", "jul/26", "ago/26"],
        "Lula": [39, 40, 39],
        "Flávio Bolsonaro": [29, 28, 30],
        "gap": [10, 12, 9],
        "august": {
            "Lula": 39,
            "Flávio Bolsonaro": 30,
            "Renan Santos": 4,
            "Ronaldo Caiado": 4,
            "Romeu Zema": 2,
            "Cabo Daciolo": 1,
            "Augusto Cury": 1,
            "Samara Martins": 1,
            "indecisos": 10,
            "branco_nulo_nao_vota": 8,
        },
    },
    "runoff": {
        "dates": ["jun/26", "jul/26", "ago/26"],
        "Lula": [44, 45, 44],
        "Flávio Bolsonaro": [38, 37, 39],
        "gap": [6, 8, 5],
        "blank": [14, 14, 13],
        "undecided": [4, 4, 4],
    },
    "definitive": {
        "overall": {"july": 65, "august": 69},
        "Lula": {"july": 77, "august": 77},
        "Flávio Bolsonaro": {"july": 62, "august": 68},
    },
    "candidate_image": {
        "Lula": {
            "potential": {"july": 47, "august": 45},
            "rejection": {"july": 50, "august": 52},
        },
        "Flávio Bolsonaro": {
            "potential": {"july": 38, "august": 41},
            "rejection": {"july": 57, "august": 54},
        },
    },
    "succession": {
        "lula_deserves_four_more": {"july": 45, "august": 41},
        "lula_does_not_deserve": {"july": 51, "august": 55},
        "fear_bolsonaro_family": {"july": 46, "august": 44},
        "fear_lula": {"july": 38, "august": 41},
        "government_approval": {"july": 48, "august": 48},
        "government_disapproval": {"july": 47, "august": 47},
    },
    "positioning": {
        "right_non_bolsonarist_flavio": {"july": 74, "august": 81},
        "bolsonarist_flavio": {"july": 91, "august": 95},
        "independent": {
            "Lula": {"july": 40, "august": 33},
            "Flávio Bolsonaro": {"july": 27, "august": 30},
            "blank": {"july": 26, "august": 29},
            "undecided": {"july": 7, "august": 8},
        },
    },
    "first_round_segments": {
        "Nordeste": [59, 20],
        "Sudeste": [31, 33],
        "Sul": [25, 43],
        "Centro-Oeste + Norte": [35, 29],
        "Mulheres": [38, 26],
        "Homens": [37, 34],
        "16-34": [36, 23],
        "35-59": [39, 35],
        "60+": [44, 28],
        "Até 2 SM": [51, 23],
        "2-5 SM": [37, 32],
        "5+ SM": [31, 35],
        "Católicos": [44, 29],
        "Evangélicos": [28, 35],
    },
    "runoff_segments": {
        "Nordeste": [64, 25],
        "Sudeste": [38, 40],
        "Sul": [29, 56],
        "Centro-Oeste + Norte": [40, 44],
        "Mulheres": [47, 35],
        "Homens": [40, 44],
        "16-34": [44, 38],
        "35-59": [42, 42],
        "60+": [48, 34],
        "Até 2 SM": [54, 30],
        "2-5 SM": [41, 43],
        "5+ SM": [36, 44],
        "Pretos": [61, 22],
        "Brancos": [36, 46],
        "Católicos": [49, 37],
        "Evangélicos": [33, 48],
        "Bolsa Família": [62, 26],
        "Sem Bolsa Família": [39, 42],
    },
    "campaign_blocks": {
        "reconciliation_known": 41,
        "reconciliation_positive": 59,
        "michelle_increases_chances": {"july": 38, "august": 46},
        "visit_ban_wrong": 52,
        "patriotism": {"Lula": 46, "Flávio Bolsonaro": 38},
        "ambassador_statement_effect": {"increase": 15, "none": 54, "decrease": 26},
    },
}

# ---------------------------------------------------------------------------
# Transcrições do relatório de agosto. Todo número tem página de origem: as
# tabelas do PDF são imagens, sem camada de texto, e foram lidas página a
# página. Nada aqui é estimado; o que é conta nossa vive nas funções abaixo.
# ---------------------------------------------------------------------------

BLOC_SHARES = {
    "Lulista": 19,
    "Esquerda não lulista": 14,
    "Independente": 32,
    "Direita não bolsonarista": 21,
    "Bolsonarista": 12,
    "NS/NR": 2,
}

FIRST_ROUND_BY_BLOC = {
    "Lulista": {
        "Lula": 95,
        "Flávio": 0,
        "Renan": 0,
        "Caiado": 0,
        "Zema": 0,
        "outros": 0,
        "indecisos": 4,
        "branco_nulo": 1,
    },
    "Esquerda não lulista": {
        "Lula": 81,
        "Flávio": 1,
        "Renan": 0,
        "Caiado": 3,
        "Zema": 0,
        "outros": 2,
        "indecisos": 10,
        "branco_nulo": 4,
    },
    "Independente": {
        "Lula": 24,
        "Flávio": 18,
        "Renan": 6,
        "Caiado": 5,
        "Zema": 4,
        "outros": 5,
        "indecisos": 21,
        "branco_nulo": 17,
    },
    "Direita não bolsonarista": {
        "Lula": 4,
        "Flávio": 66,
        "Renan": 10,
        "Caiado": 6,
        "Zema": 4,
        "outros": 2,
        "indecisos": 2,
        "branco_nulo": 6,
    },
    "Bolsonarista": {
        "Lula": 3,
        "Flávio": 82,
        "Renan": 0,
        "Caiado": 6,
        "Zema": 1,
        "outros": 1,
        "indecisos": 4,
        "branco_nulo": 3,
    },
}

RUNOFF_BY_BLOC = {
    "Lulista": {"Lula": 97, "Flávio": 1, "nao_vota": 1, "indecisos": 0},
    "Esquerda não lulista": {"Lula": 91, "Flávio": 4, "nao_vota": 1, "indecisos": 4},
    "Independente": {"Lula": 33, "Flávio": 30, "nao_vota": 29, "indecisos": 8},
    "Direita não bolsonarista": {
        "Lula": 5,
        "Flávio": 81,
        "nao_vota": 9,
        "indecisos": 5,
    },
    "Bolsonarista": {"Lula": 3, "Flávio": 95, "nao_vota": 2, "indecisos": 0},
}

# p. 36: conhece e votaria / não conhece / conhece e não votaria (agosto).
LEADER_IMAGE = {
    "Lula": [45, 3, 52],
    "Flávio Bolsonaro": [41, 5, 54],
    "Ronaldo Caiado": [22, 44, 34],
    "Romeu Zema": [19, 49, 32],
    "Renan Santos": [15, 65, 20],
    "Augusto Cury": [10, 74, 16],
    "Cabo Daciolo": [8, 64, 28],
    "Samara Martins": [3, 85, 12],
}

# p. 37: mesma bateria, só "conhece e votaria", por posicionamento.
POTENTIAL_BY_BLOC = {
    "Flávio Bolsonaro": {
        "Lulista": 3,
        "Esquerda não lulista": 7,
        "Independente": 31,
        "Direita não bolsonarista": 82,
        "Bolsonarista": 91,
    },
    "Ronaldo Caiado": {
        "Lulista": 5,
        "Esquerda não lulista": 12,
        "Independente": 15,
        "Direita não bolsonarista": 47,
        "Bolsonarista": 36,
    },
    "Romeu Zema": {
        "Lulista": 4,
        "Esquerda não lulista": 6,
        "Independente": 12,
        "Direita não bolsonarista": 45,
        "Bolsonarista": 31,
    },
    "Renan Santos": {
        "Lulista": 3,
        "Esquerda não lulista": 4,
        "Independente": 7,
        "Direita não bolsonarista": 36,
        "Bolsonarista": 34,
    },
}

# Quatro cenários de 2º turno na mesma amostra, pp. 20, 23, 26 e 29.
RUNOFF_SCENARIOS = [
    {
        "scenario": "Cenário 1",
        "challenger": "Flávio Bolsonaro",
        "page": 20,
        "lula": 44,
        "challenger_pct": 39,
        "blank": 13,
        "undecided": 4,
    },
    {
        "scenario": "Cenário 3",
        "challenger": "Ronaldo Caiado",
        "page": 23,
        "lula": 45,
        "challenger_pct": 37,
        "blank": 14,
        "undecided": 4,
    },
    {
        "scenario": "Cenário 4",
        "challenger": "Renan Santos",
        "page": 29,
        "lula": 45,
        "challenger_pct": 35,
        "blank": 16,
        "undecided": 4,
    },
    {
        "scenario": "Cenário 2",
        "challenger": "Romeu Zema",
        "page": 26,
        "lula": 46,
        "challenger_pct": 34,
        "blank": 16,
        "undecided": 4,
    },
]

# Segmentos presentes nos quatro cenários (pp. 21, 24, 27 e 30). Só entram os
# recortes em que o relatório imprime o valor dos quatro desafiantes.
SCENARIO_SEGMENTS = {
    "Sul": {"Flávio": 56, "Ronaldo Caiado": 46, "Renan Santos": 45, "Romeu Zema": 43},
    "Evangélica": {
        "Flávio": 48,
        "Ronaldo Caiado": 45,
        "Renan Santos": 47,
        "Romeu Zema": 42,
    },
    "Branca": {
        "Flávio": 46,
        "Ronaldo Caiado": 40,
        "Renan Santos": 37,
        "Romeu Zema": 39,
    },
    "Superior": {
        "Flávio": 45,
        "Ronaldo Caiado": 46,
        "Renan Santos": 41,
        "Romeu Zema": 43,
    },
    "5+ SM": {"Flávio": 44, "Ronaldo Caiado": 48, "Renan Santos": 41, "Romeu Zema": 43},
    "Masculino": {
        "Flávio": 44,
        "Ronaldo Caiado": 46,
        "Renan Santos": 41,
        "Romeu Zema": 40,
    },
    "Centro-Oeste/Norte": {
        "Flávio": 44,
        "Ronaldo Caiado": 46,
        "Renan Santos": 43,
        "Romeu Zema": 38,
    },
    "Sem Bolsa Família": {
        "Flávio": 42,
        "Ronaldo Caiado": 40,
        "Renan Santos": 37,
        "Romeu Zema": 37,
    },
    "Sudeste": {
        "Flávio": 40,
        "Ronaldo Caiado": 38,
        "Renan Santos": 35,
        "Romeu Zema": 39,
    },
    "Católica": {
        "Flávio": 37,
        "Ronaldo Caiado": 35,
        "Renan Santos": 30,
        "Romeu Zema": 33,
    },
    "Feminino": {
        "Flávio": 35,
        "Ronaldo Caiado": 29,
        "Renan Santos": 29,
        "Romeu Zema": 29,
    },
    "Outras raças": {
        "Flávio": 35,
        "Ronaldo Caiado": 23,
        "Renan Santos": 29,
        "Romeu Zema": 29,
    },
    "60+ anos": {
        "Flávio": 34,
        "Ronaldo Caiado": 35,
        "Renan Santos": 30,
        "Romeu Zema": 32,
    },
    "Sem religião": {
        "Flávio": 32,
        "Ronaldo Caiado": 31,
        "Renan Santos": 31,
        "Romeu Zema": 27,
    },
    "Fundamental": {
        "Flávio": 30,
        "Ronaldo Caiado": 28,
        "Renan Santos": 26,
        "Romeu Zema": 27,
    },
    "Até 2 SM": {
        "Flávio": 30,
        "Ronaldo Caiado": 27,
        "Renan Santos": 27,
        "Romeu Zema": 26,
    },
    "Bolsa Família": {
        "Flávio": 26,
        "Ronaldo Caiado": 24,
        "Renan Santos": 23,
        "Romeu Zema": 22,
    },
    "Nordeste": {
        "Flávio": 25,
        "Ronaldo Caiado": 25,
        "Renan Santos": 23,
        "Romeu Zema": 20,
    },
    "Preta": {"Flávio": 22, "Ronaldo Caiado": 20, "Renan Santos": 23, "Romeu Zema": 20},
}

# Fidelidade declarada do voto de 1º turno, por candidato (p. 34).
VOTE_FIRMNESS = {
    "Lula": {"definitiva": 77, "pode_mudar": 22},
    "Flávio Bolsonaro": {"definitiva": 68, "pode_mudar": 32},
    "Ronaldo Caiado": {"definitiva": 47, "pode_mudar": 53},
    "Renan Santos": {"definitiva": 55, "pode_mudar": 45},
    "Romeu Zema": {"definitiva": 20, "pode_mudar": 79},
}

# Aprovação do governo Lula por recorte (pp. 43 a 51) e voto de 2º turno nos
# mesmos recortes (p. 21). As duas metades permitem medir conversão.
APPROVAL_BY_SEGMENT = {
    "Nordeste": [66, 29],
    "Sudeste": [42, 52],
    "Sul": [35, 58],
    "Centro-Oeste/Norte": [47, 50],
    "Feminino": [52, 42],
    "Masculino": [44, 52],
    "16 a 34 anos": [47, 48],
    "35 a 59 anos": [47, 48],
    "60+ anos": [52, 41],
    "Fundamental": [57, 36],
    "Médio": [43, 53],
    "Superior": [39, 58],
    "Até 2 SM": [59, 35],
    "2 a 5 SM": [46, 48],
    "5+ SM": [38, 58],
    "Católica": [53, 42],
    "Evangélica": [38, 57],
    "Bolsa Família": [66, 28],
    "Sem Bolsa Família": [44, 51],
}

RUNOFF_BY_SEGMENT = {
    "Nordeste": [64, 25],
    "Sudeste": [38, 40],
    "Sul": [29, 56],
    "Centro-Oeste/Norte": [40, 44],
    "Feminino": [47, 35],
    "Masculino": [40, 44],
    "16 a 34 anos": [44, 38],
    "35 a 59 anos": [42, 42],
    "60+ anos": [48, 34],
    "Fundamental": [55, 30],
    "Médio": [42, 42],
    "Superior": [34, 45],
    "Até 2 SM": [54, 30],
    "2 a 5 SM": [41, 43],
    "5+ SM": [36, 44],
    "Católica": [49, 37],
    "Evangélica": [33, 48],
    "Bolsa Família": [62, 26],
    "Sem Bolsa Família": [39, 42],
}

# Partição de renda: as três faixas somam 100% da amostra (p. 107).
INCOME_SHARES = {"Até 2 SM": 31, "2 a 5 SM": 42, "5+ SM": 27}

# Bloco econômico, pp. 56 a 75. Cada série termina em agosto de 2026.
ECONOMY = {
    "direction": {
        "question": "O Brasil está indo na direção certa ou errada?",
        "page": 56,
        "errada": 55,
        "certa": 38,
        "series_errada": [57, 58, 56, 58, 56, 55, 58, 58, 53, 55, 51, 55],
    },
    "economy_12m": {
        "question": "Nos últimos 12 meses, a economia do Brasil...",
        "page": 60,
        "piorou": 43,
        "igual": 35,
        "melhorou": 19,
        "melhorou_series": [22, 21, 21, 24, 28, 24, 24, 24, 21, 22, 20, 20, 19],
    },
    "food_prices": {
        "question": "O preço dos alimentos no último mês",
        "page": 61,
        "subiu": 68,
        "igual": 21,
        "caiu": 9,
        "subiu_series": [60, 61, 63, 58, 57, 58, 56, 58, 72, 69, 69, 66, 68],
    },
    "purchasing_power": {
        "question": "Poder de compra comparado a um ano atrás",
        "page": 62,
        "menor": 69,
        "igual": 20,
        "maior": 10,
        "maior_series": [16, 14, 15, 16, 19, 18, 15, 14, 11, 11, 13, 10, 10],
    },
    "jobs": {
        "question": "Está mais fácil ou mais difícil conseguir emprego",
        "page": 63,
        "dificil": 48,
        "facil": 41,
    },
    "expectation_12m": {
        "question": "Expectativa para a economia nos próximos 12 meses",
        "page": 64,
        "melhorar": 46,
        "igual": 25,
        "piorar": 24,
        "melhorar_series": [40, 40, 43, 42, 44, 48, 43, 41, 40, 40, 39, 39, 46],
    },
    "affordability": {
        "question": "Renda da família contra o aumento de preços",
        "page": 66,
        "renda_nao_aumentou": 32,
        "aumentou_menos_que_custo": 23,
        "aumentou_igual_ao_custo": 33,
        "aumentou_mais_que_custo": 10,
    },
    "debt": {
        "question": "Você tem muitas, poucas ou nenhuma dívida?",
        "page": 71,
        "muitas": 22,
        "poucas": 47,
        "nao_tem": 31,
    },
    "tariffs": {
        "question": "Resposta de Lula ao tarifaço",
        "page": 90,
        "mal": 43,
        "bem": 38,
        "nem_bem_nem_mal": 4,
        "ns_nr": 15,
        "knew_news": 63,
    },
}

# Os dois programas econômicos que o governo mais divulga (pp. 68, 69, 72-75).
PROGRAMS = [
    {
        "name": "Isenção do IRPF até R$ 5 mil",
        "pages": [68, 69],
        "reached": 30,
        "not_reached": 68,
        "felt_a_lot": 21,
        "felt_a_little": 32,
        "felt_nothing": 46,
    },
    {
        "name": "Desenrola 2.0",
        "pages": [72, 74, 75],
        "heard_of": 67,
        "good_idea": 47,
        "bad_idea": 23,
        "helps_a_little": 25,
        "reached": 10,
        "not_reached": 88,
        "felt_a_lot": 26,
        "felt_a_little": 35,
        "felt_nothing": 37,
    },
]

# Agenda e canal (pp. 98 e 100 a 102).
AGENDA = {
    "page": 98,
    "violencia": 29,
    "problemas_sociais": 18,
    "corrupcao": 15,
    "saude": 15,
    "economia": 13,
    "educacao": 6,
}

MEDIA = {
    "page": 100,
    "total": {
        "redes": 35,
        "tv": 35,
        "sites": 10,
        "outros": 8,
        "nao_se_informa": 7,
        "radio": 3,
    },
    "by_age": {
        "16 a 34 anos": {"redes": 50, "tv": 20, "sites": 13},
        "35 a 59 anos": {"redes": 36, "tv": 36, "sites": 10},
        "60+ anos": {"redes": 17, "tv": 57, "sites": 5},
    },
    "by_income": {
        "Até 2 SM": {"redes": 31, "tv": 41, "sites": 5},
        "2 a 5 SM": {"redes": 36, "tv": 36, "sites": 10},
        "5+ SM": {"redes": 40, "tv": 30, "sites": 18},
    },
}

# Bloco de estímulos de campanha, pp. 77 a 96.
CAMPAIGN = {
    "reconciliation": {"knew": 41, "positive": 59, "negative": 25, "ns_nr": 16},
    "michelle_helps": {"july": 38, "august": 46, "no": 45, "ns_nr": 9},
    "michelle_helps_by_bloc": {
        "Lulista": 22,
        "Esquerda não lulista": 37,
        "Independente": 37,
        "Direita não bolsonarista": 70,
        "Bolsonarista": 79,
    },
    "visit_ban": {"knew": 53, "wrong": 52, "right": 41, "ns_nr": 7, "pages": [84, 86]},
    "visit_ban_by_bloc": {
        "Lulista": {"certa": 70, "errada": 25},
        "Esquerda não lulista": {"certa": 73, "errada": 21},
        "Independente": {"certa": 39, "errada": 50},
        "Direita não bolsonarista": {"certa": 15, "errada": 83},
        "Bolsonarista": {"certa": 7, "errada": 92},
    },
    "patriotism": {"Lula": 46, "Flávio Bolsonaro": 38, "nenhum": 9, "page": 91},
    "ambassadors": {
        "knew": 32,
        "increase": 15,
        "none": 54,
        "decrease": 26,
        "pages": [93, 95],
    },
    "ambassadors_by_bloc": {
        "Lulista": {"aumentam": 4, "nao_afetam": 49, "diminuem": 44},
        "Esquerda não lulista": {"aumentam": 3, "nao_afetam": 37, "diminuem": 57},
        "Independente": {"aumentam": 8, "nao_afetam": 65, "diminuem": 21},
        "Direita não bolsonarista": {"aumentam": 27, "nao_afetam": 60, "diminuem": 10},
        "Bolsonarista": {"aumentam": 45, "nao_afetam": 49, "diminuem": 4},
    },
}

# Voto espontâneo, p. 8. A pergunta vem antes de qualquer lista de nomes.
SPONTANEOUS = {
    "page": 8,
    "dates": ["mai/26", "jun/26", "jul/26", "ago/26"],
    "Lula": [22, 23, 26, 25],
    "Flávio Bolsonaro": [14, 17, 14, 18],
    "Jair Bolsonaro": [2, 1, 1, 1],
    "indecisos": [57, 56, 54, 51],
}

COMPARATORS = [
    {
        "poll": "Quaest",
        "field": "31/07-03/08",
        "mode": "presencial domiciliar",
        "n": 2004,
        "first": [39, 30],
        "runoff": [44, 39],
        "nonchoice_first": 18,
        "nonchoice_runoff": 17,
        "registry": "BR-06591/2026",
    },
    {
        "poll": "Nexus/BTG",
        "field": "31/07-02/08",
        "mode": "CATI com RDD",
        "n": 2002,
        "first": [41, 37],
        "runoff": [46, 45],
        "nonchoice_first": 7,
        "nonchoice_runoff": 10,
        "registry": "BR-02874/2026",
    },
    {
        "poll": "Datafolha",
        "field": "22-24/07",
        "mode": "pontos de fluxo",
        "n": 2004,
        "first": [40, 32],
        "runoff": [48, 43],
        "nonchoice_first": 11,
        "nonchoice_runoff": 10,
        "registry": "BR-01166/2026",
    },
    {
        "poll": "Atlas/Bloomberg",
        "field": "22-27/07",
        "mode": "recrutamento digital não probabilístico",
        "n": 5021,
        "first": [44.9, 35.8],
        "runoff": [49.2, 42.9],
        "nonchoice_first": 1.6,
        "nonchoice_runoff": 7.9,
        "registry": "BR-08602/2026",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def manifest() -> list[dict]:
    rows = []
    for path in sorted(SOURCE.iterdir()):
        if path.is_file() and path.name not in {"README.md", AUGUST_CSV.name}:
            rows.append(
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "used": path.name != "detalhes-demograficos-cidade.csv",
                }
            )
    return rows


def questionnaire_diagnostics() -> dict:
    path = SOURCE / "questionario.pdf"
    text = pdf_text(path)
    collapsed = re.sub(r"\s+", " ", text.upper())
    words = len(re.findall(r"\b[\wÀ-ÿ]+\b", text))
    scenarios = []
    for spoken_share in (0.25, 0.40, 0.60):
        spoken_words = round(words * spoken_share)
        reading_minutes = spoken_words / 130
        seconds_per_answer = max(0, (20 - reading_minutes) * 60 / 109)
        scenarios.append(
            {
                "share_of_pdf_spoken": spoken_share,
                "spoken_words": spoken_words,
                "reading_minutes_at_130_wpm": round(reading_minutes, 1),
                "seconds_left_per_numbered_item": round(seconds_per_answer, 1),
            }
        )
    return {
        "pages": len(PdfReader(path).pages),
        "numbered_items": 109,
        "pdf_words": words,
        "promised_minutes": 20,
        "gross_seconds_per_numbered_item": round(20 * 60 / 109, 1),
        "showcards": 10,
        "candidate_rows": 12,
        "trust_rows": 16,
        "template_residue": {
            "trazer_item_aqui": collapsed.count("TRAZER ITEM AQUI"),
            "trazer_opcao_aqui": collapsed.count("TRAZER OPÇÃO AQUI"),
        },
        "duration_scenarios": scenarios,
        "paradata_printed": ["horário de início", "horário do fim"],
        "paradata_unpublished": [
            "duração por entrevista",
            "duração por bloco",
            "tentativas de contato",
            "horário e dia por entrevista",
            "recusas e substituições",
            "não resposta por item e posição",
            "efeito de entrevistador",
        ],
        "field_days": [
            {"date": "2026-07-31", "weekday": "sexta-feira"},
            {"date": "2026-08-01", "weekday": "sábado"},
            {"date": "2026-08-02", "weekday": "domingo"},
            {"date": "2026-08-03", "weekday": "segunda-feira"},
        ],
        "interpretation": (
            "The scenarios are arithmetic stress tests, not measured completion times. "
            "Only the unpublished start/end paradata can establish the actual duration."
        ),
    }


def publication_coverage() -> dict:
    all_questions = set(range(1, 110))
    unpublished = sorted(all_questions - PUBLISHED_QUESTIONS)
    grouped = sorted(q for group in UNPUBLISHED_GROUPS for q in group["questions"])
    if unpublished != grouped:
        raise ValueError("unpublished question grouping is inconsistent")
    return {
        "august": {
            "total": 109,
            "published": len(PUBLISHED_QUESTIONS),
            "unpublished": len(unpublished),
            "published_pct": round(100 * len(PUBLISHED_QUESTIONS) / 109, 1),
            "published_ids": sorted(PUBLISHED_QUESTIONS),
            "unpublished_ids": unpublished,
            "groups": UNPUBLISHED_GROUPS,
        },
        "july": {
            "total": 101,
            "initial_deck_published": 65,
            "eventual_published_after_supplement": 73,
            "initial_pct": round(100 * 65 / 101, 1),
            "eventual_pct": round(100 * 73 / 101, 1),
        },
        "method": "manual page-by-page reconciliation against the public report",
    }


def margin_scenarios(lula: float, flavio: float, n: int = 2004) -> dict:
    z = NormalDist().inv_cdf(0.975)
    gap = 100 * (lula - flavio)
    variance = (lula + flavio - (lula - flavio) ** 2) / n
    rows = []
    for deff in (1.0, 1.5, 2.0):
        margin = 100 * z * math.sqrt(variance * deff)
        rows.append(
            {
                "deff": deff,
                "difference_moe": round(margin, 2),
                "gap_low": round(gap - margin, 2),
                "gap_high": round(gap + margin, 2),
                "effective_n": round(n / deff),
            }
        )
    deff_zero = (gap / rows[0]["difference_moe"]) ** 2
    return {
        "gap": round(gap, 1),
        "srs_individual_worst_case_moe": round(100 * z * math.sqrt(0.25 / n), 2),
        "scenarios": rows,
        "deff_to_include_zero": round(deff_zero, 3),
        "rho_if_only_six_person_clusters": round((deff_zero - 1) / 5, 3),
    }


def pnad_age_scope_check() -> dict:
    """Confirm how excluding under-16s changes the PNAD income benchmark."""
    source = next((path for path in PNAD_INCOME_CANDIDATES if path.exists()), None)
    if source is None:
        raise FileNotFoundError(
            "PNAD annual visit-1 CSV not found in the project or canonical data checkout"
        )
    groups = {
        "all_ages": {"label": "Todas as idades", "bands": [0.0, 0.0, 0.0], "rows": 0},
        "age_16_plus": {
            "label": "16 anos ou mais",
            "bands": [0.0, 0.0, 0.0],
            "rows": 0,
        },
        "age_17_plus": {
            "label": "17 anos ou mais",
            "bands": [0.0, 0.0, 0.0],
            "rows": 0,
        },
    }
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        age_index = header.index("V2009__idade_na_data_de_referencia")
        weight_index = header.index("V1032__peso_com_calibracao")
        income_index = header.index("VD5001__rend_efetivo_domiciliar_mw")
        for row in reader:
            try:
                age = int(float(row[age_index]))
                weight = float(row[weight_index])
                income = float(row[income_index])
            except (IndexError, ValueError):
                continue
            band = 0 if income <= 2 else 1 if income <= 5 else 2
            for key, include in (
                ("all_ages", True),
                ("age_16_plus", age >= 16),
                ("age_17_plus", age > 16),
            ):
                if include:
                    groups[key]["bands"][band] += weight
                    groups[key]["rows"] += 1
    for group in groups.values():
        total = sum(group["bands"])
        group["weighted_people"] = round(total)
        group["bands_pct"] = [
            round(100 * value / total, 3) for value in group.pop("bands")
        ]
    return {
        "source": "data/outputs/base_anual_visita1_labeled_npv.csv",
        "age_variable": "V2009__idade_na_data_de_referencia",
        "published_rule": ">= 16",
        "interpretation": (
            "The 16+ line is the matching electoral universe. The all-ages and 17+ "
            "lines are diagnostics and are not used in the report sensitivity analysis."
        ),
        "groups": groups,
    }


def income_benchmark() -> dict:
    prior = json.loads((ROOT / "docs/assets/quaest_0726_data.json").read_text())
    benchmark = prior["benchmarks"]["pnad_income"]
    scope_check = pnad_age_scope_check()
    verified_16_plus = scope_check["groups"]["age_16_plus"]["bands_pct"]
    stored_16_plus = [item["estimate"] for item in benchmark["bands"]]
    if any(
        abs(current - stored) > 0.002
        for current, stored in zip(verified_16_plus, stored_16_plus)
    ):
        raise ValueError(
            "Stored PNAD benchmark does not reproduce the V2009 >= 16 filter"
        )
    target = [item["estimate"] / 100 for item in benchmark["bands"]]
    quaest = [0.31, 0.42, 0.27]
    lula = [0.51, 0.37, 0.31]
    flavio = [0.23, 0.32, 0.35]

    def weighted(shares: list[float], weights: list[float]) -> float:
        return 100 * sum(a * b for a, b in zip(shares, weights))

    published_mix = [weighted(lula, quaest), weighted(flavio, quaest)]
    pnad_mix = [weighted(lula, target), weighted(flavio, target)]
    return {
        "benchmark": benchmark,
        "age_scope_check": scope_check,
        "quaest_target": [31, 42, 27],
        "deltas_pp": [round(100 * (q - t), 3) for q, t in zip(quaest, target)],
        "first_round_income_shares": {"Lula": [51, 37, 31], "Flávio": [23, 32, 35]},
        "published_mix_reconstructed": [round(x, 3) for x in published_mix],
        "pnad_marginal_sensitivity": [round(x, 3) for x in pnad_mix],
        "gap_change_pp": round(
            (pnad_mix[0] - pnad_mix[1]) - (published_mix[0] - published_mix[1]), 3
        ),
        "warning": (
            "Single-margin sensitivity analysis. Quaest uses joint weighting and MRP, "
            "whose final weights and model specification were not published."
        ),
    }


def tse_benchmark() -> dict:
    prior = json.loads((ROOT / "docs/assets/quaest_0726_data.json").read_text())
    result = prior["benchmarks"]["tse"]
    for row in result["age"]:
        if row["category"] == "16-34":
            row.update({"quaest": 31, "delta": round(31 - row["official"], 3)})
        elif row["category"] == "60+":
            row.update({"quaest": 24, "delta": round(24 - row["official"], 3)})
    return result


def load_territory_module():
    path = ROOT / "scripts/quaest-territory-audit.py"
    spec = importlib.util.spec_from_file_location("quaest_territory", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def territory_payload(refresh: bool) -> dict:
    module = load_territory_module()
    july = module.parse_pdf(
        JULY_SOURCE / "Quaest_Bairros_072026.pdf", "julho/2026", "BR-07181/2026"
    )
    august = module.parse_pdf(
        SOURCE / "anexo-territorial.pdf", "agosto/2026", "BR-06591/2026"
    )
    reference = module.load_or_refresh_reference([*july, *august], REFERENCE, refresh)
    comparison = module.compare_rounds(july, august)
    payload = {
        "metadata": {
            "july_registry": "BR-07181/2026",
            "august_registry": "BR-06591/2026",
            "sampling_unit": "setor censitário IBGE 2022",
            "comparison_key": "geocódigo de 15 dígitos",
            "warning": (
                "The annex has no vote, inclusion probabilities or respondent weights. "
                "Territory cannot support ecological inference about candidate vote."
            ),
        },
        "rounds": {
            "july": module.round_summary(july, reference),
            "august": module.round_summary(august, reference),
        },
        "comparison": comparison,
        "capitals": {
            "july": module.capital_rows(july),
            "august": module.capital_rows(august),
        },
        "ibge_validation": {
            "retrieved": reference["retrieved"],
            "errors": reference.get("errors", {}),
            "reference_file": str(REFERENCE.relative_to(ROOT)),
        },
        "design": {
            "clusters": 334,
            "interviews_per_cluster": 6,
            "cluster_deff": [
                {"rho": rho, "deff": round(1 + 5 * rho, 2)}
                for rho in (0.05, 0.10, 0.20)
            ],
        },
    }
    module.write_csv(AUGUST_CSV, august, reference)
    TERRITORY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TERRITORY_OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def bloc_reconstruction() -> dict:
    """Rebuild the national topline from the positioning crosstab.

    The check has one purpose: proving the transcription is arithmetically
    consistent with the published headline before any of it is used to argue
    strategy. Residual is the NS/NR bloc, whose vote the report does not print.
    """
    rows = []
    for candidate in ("Lula", "Flávio"):
        total = sum(
            BLOC_SHARES[bloc] * FIRST_ROUND_BY_BLOC[bloc][candidate] / 100
            for bloc in FIRST_ROUND_BY_BLOC
        )
        published = 39 if candidate == "Lula" else 30
        rows.append(
            {
                "candidate": candidate,
                "reconstructed": round(total, 2),
                "published": published,
                "residual": round(published - total, 2),
            }
        )
    runoff = []
    for candidate in ("Lula", "Flávio"):
        total = sum(
            BLOC_SHARES[bloc] * RUNOFF_BY_BLOC[bloc][candidate] / 100
            for bloc in RUNOFF_BY_BLOC
        )
        published = 44 if candidate == "Lula" else 39
        runoff.append(
            {
                "candidate": candidate,
                "reconstructed": round(total, 2),
                "published": published,
                "residual": round(published - total, 2),
            }
        )
    return {
        "first_round": rows,
        "runoff": runoff,
        "bloc_shares": BLOC_SHARES,
        "note": (
            "Os 2% de NS/NR na escala de posicionamento não têm voto publicado; "
            "é essa a origem do resíduo."
        ),
    }


def useful_vote_map() -> dict:
    """Locate every point that is neither Lula's nor Flávio's in round one.

    Nothing here forecasts transfer. It measures where the non-Lula, non-Flávio
    vote physically sits, in national points, so that a claim about the useful
    vote can be checked against the size of the pool it depends on.
    """
    rows = []
    for bloc, share in BLOC_SHARES.items():
        if bloc == "NS/NR":
            continue
        vote = FIRST_ROUND_BY_BLOC[bloc]
        third_way = vote["Renan"] + vote["Caiado"] + vote["Zema"] + vote["outros"]
        parked = vote["indecisos"] + vote["branco_nulo"]
        potential = POTENTIAL_BY_BLOC["Flávio Bolsonaro"][bloc]
        rows.append(
            {
                "bloc": bloc,
                "share": share,
                "flavio_vote": vote["Flávio"],
                "flavio_potential": potential,
                "slack_pp": potential - vote["Flávio"],
                "slack_national": round(share * (potential - vote["Flávio"]) / 100, 2),
                "third_way_pp": third_way,
                "third_way_national": round(share * third_way / 100, 2),
                "parked_pp": parked,
                "parked_national": round(share * parked / 100, 2),
                "lula_pp": vote["Lula"],
            }
        )
    right = [row for row in rows if row["bloc"].startswith(("Direita", "Bolsonar"))]
    return {
        "rows": rows,
        "third_way_total": round(sum(row["third_way_national"] for row in rows), 2),
        "third_way_inside_right": round(
            sum(row["third_way_national"] for row in right), 2
        ),
        "parked_total": round(sum(row["parked_national"] for row in rows), 2),
        "slack_inside_right": round(sum(row["slack_national"] for row in right), 2),
        "ceiling_note": (
            "Somar o pool inteiro ao candidato é teto aritmético, não previsão. "
            "A pesquisa não acompanha eleitores entre perguntas."
        ),
    }


def soft_third_way() -> dict:
    """How much of the third-way vote its own voters call changeable (p. 34)."""
    august = VOTE["first_round"]["august"]
    rows = []
    for name, key in (
        ("Ronaldo Caiado", "Ronaldo Caiado"),
        ("Renan Santos", "Renan Santos"),
        ("Romeu Zema", "Romeu Zema"),
    ):
        share = august[key]
        soft = VOTE_FIRMNESS[name]["pode_mudar"]
        rows.append(
            {
                "candidate": name,
                "first_round_pct": share,
                "changeable_pct": soft,
                "soft_national": round(share * soft / 100, 2),
                "definitive_pct": VOTE_FIRMNESS[name]["definitiva"],
                "unknown_pct": LEADER_IMAGE[name][1],
                "rejection_pct": LEADER_IMAGE[name][2],
            }
        )
    return {
        "rows": rows,
        "soft_total": round(sum(row["soft_national"] for row in rows), 2),
        "flavio_definitive": VOTE_FIRMNESS["Flávio Bolsonaro"]["definitiva"],
        "lula_definitive": VOTE_FIRMNESS["Lula"]["definitiva"],
    }


def substitution_ledger() -> dict:
    """Compare the four runoff scenarios measured in the same sample."""
    base = RUNOFF_SCENARIOS[0]
    rows = []
    for item in RUNOFF_SCENARIOS:
        rows.append(
            {
                **item,
                "gap": item["lula"] - item["challenger_pct"],
                "non_choice": item["blank"] + item["undecided"],
                "cost_vs_flavio": item["challenger_pct"] - base["challenger_pct"],
                "lula_delta": item["lula"] - base["lula"],
            }
        )
    segments = []
    for segment, values in SCENARIO_SEGMENTS.items():
        flavio = values["Flávio"]
        others = {k: v for k, v in values.items() if k != "Flávio"}
        best_other = max(others.items(), key=lambda pair: pair[1])
        segments.append(
            {
                "segment": segment,
                "flavio": flavio,
                "best_alternative": best_other[0],
                "best_alternative_pct": best_other[1],
                "gap_to_best": flavio - best_other[1],
                "all": values,
            }
        )
    lula_values = [item["lula"] for item in RUNOFF_SCENARIOS]
    return {
        "scenarios": rows,
        "segments": segments,
        "lula_range": [min(lula_values), max(lula_values)],
        "reading": (
            "Trocar o adversário move o adversário, não Lula: a faixa de Lula é de "
            f"{min(lula_values)} a {max(lula_values)} nos quatro cenários, enquanto o "
            "desafiante varia de 34 a 39. O que sobra vai para branco, nulo e indecisão."
        ),
    }


def conversion_ledger() -> dict:
    """Disapproval of Lula minus Flávio's runoff vote, segment by segment.

    Disapproval is not availability: someone can disapprove and still vote Lula.
    The difference is therefore an addressable ceiling, not a forecast, and it is
    only comparable inside the same segment, where both numbers come from the
    same published crosstab.
    """
    rows = []
    for segment, (_, disapproval) in APPROVAL_BY_SEGMENT.items():
        runoff = RUNOFF_BY_SEGMENT.get(segment)
        if not runoff:
            continue
        lula_runoff, flavio_runoff = runoff
        rows.append(
            {
                "segment": segment,
                "disapproval": disapproval,
                "flavio_runoff": flavio_runoff,
                "unconverted": disapproval - flavio_runoff,
                "lula_runoff": lula_runoff,
                "non_choice": 100 - lula_runoff - flavio_runoff,
                "share": INCOME_SHARES.get(segment),
            }
        )
    rows.sort(key=lambda row: row["unconverted"], reverse=True)
    income_rows = [row for row in rows if row["share"]]
    national = sum(row["share"] * row["unconverted"] / 100 for row in income_rows)
    return {
        "rows": rows,
        "income_partition": {
            "rows": income_rows,
            "national_unconverted": round(national, 2),
            "runoff_gap": 5,
            "note": (
                "As três faixas de renda somam 100% da amostra, então a soma "
                "ponderada é uma estimativa nacional legítima do teto endereçável."
            ),
        },
        "limits": (
            "Desaprovar não é estar disponível. O número mede o espaço entre "
            "rejeição ao governo e voto no adversário dentro do mesmo recorte."
        ),
    }


def program_reach() -> dict:
    """Effective reach of the two economic programs the government advertises."""
    rows = []
    for program in PROGRAMS:
        reached = program["reached"]
        felt = program["felt_a_lot"]
        rows.append(
            {
                "program": program["name"],
                "pages": program["pages"],
                "reached_pct": reached,
                "not_reached_pct": program["not_reached"],
                "felt_a_lot_pct_of_reached": felt,
                "felt_nothing_pct_of_reached": program["felt_nothing"],
                "felt_a_lot_national": round(reached * felt / 100, 2),
                "felt_nothing_national": round(
                    reached * program["felt_nothing"] / 100, 2
                ),
            }
        )
    return {
        "rows": rows,
        "reading": (
            "Os dois programas econômicos mais divulgados pelo governo chegam, "
            "com efeito sentido na renda, a menos de sete em cada cem eleitores."
        ),
    }


def media_asymmetry() -> dict:
    """Where Flávio is behind against which channel reaches that segment."""
    rows = []
    pairs = (
        ("60+ anos", MEDIA["by_age"]["60+ anos"]),
        ("16 a 34 anos", MEDIA["by_age"]["16 a 34 anos"]),
        ("35 a 59 anos", MEDIA["by_age"]["35 a 59 anos"]),
        ("Até 2 SM", MEDIA["by_income"]["Até 2 SM"]),
        ("2 a 5 SM", MEDIA["by_income"]["2 a 5 SM"]),
        ("5+ SM", MEDIA["by_income"]["5+ SM"]),
    )
    for segment, channels in pairs:
        lula, flavio = RUNOFF_BY_SEGMENT[segment]
        rows.append(
            {
                "segment": segment,
                "tv": channels["tv"],
                "redes": channels["redes"],
                "channel_gap": channels["redes"] - channels["tv"],
                "flavio_margin": flavio - lula,
            }
        )
    return {
        "rows": rows,
        "reading": (
            "O canal em que a direita é forte alcança melhor exatamente os "
            "recortes em que ela já vence, e alcança pior os recortes em que perde."
        ),
    }


def strategy_swot() -> dict:
    """The four quadrants, each tied to the number that sustains it."""
    return {
        "forcas": [
            {
                "claim": "Base própria intacta e mais firme",
                "evidence": "95% dos bolsonaristas no 2º turno (p. 22); 68% dizem que o voto é definitivo, contra 62% em julho (p. 34).",
            },
            {
                "claim": "Único da direita que compete",
                "evidence": "Cenário 1 termina 44 × 39; Caiado 45 × 37, Renan 45 × 35, Zema 46 × 34, na mesma amostra (pp. 20, 23, 26, 29).",
            },
            {
                "claim": "Voto espontâneo em máxima da série",
                "evidence": "18% citam Flávio sem lista de nomes, contra 14% em julho; a distância espontânea cai de 12 para 7 (p. 8).",
            },
            {
                "claim": "Evangélicos e Sul consolidados",
                "evidence": "48 × 33 entre evangélicos e 56 × 29 no Sul; nenhum substituto chega perto nesses dois recortes (pp. 21, 24, 27, 30).",
            },
        ],
        "fraquezas": [
            {
                "claim": "Rejeição ainda é maioria",
                "evidence": "54% conhecem e não votariam, contra 52% de Lula (p. 36).",
            },
            {
                "claim": "Muro feminino",
                "evidence": "35 × 47 entre mulheres; 44 × 40 entre homens. Diferença de 16 pontos no mesmo cenário (p. 21).",
            },
            {
                "claim": "Independentes rejeitam os dois",
                "evidence": "60% não votariam em Flávio e 62% não votariam em Lula dentro do maior bloco do eleitorado, 32% (p. 37).",
            },
            {
                "claim": "O pico foi em março, não agora",
                "evidence": "Série de 1º turno: 33% em março, 28% em julho, 30% em agosto (p. 10).",
            },
        ],
        "oportunidades": [
            {
                "claim": "Voto útil dentro da própria direita",
                "evidence": "Terceira via e voto estacionado somam pontos nacionais mensuráveis dentro dos blocos de direita, e 82% da direita não bolsonarista já declara que votaria em Flávio, contra 66% que votam hoje (pp. 18, 37).",
            },
            {
                "claim": "Terceira via é voto frouxo e desconhecida",
                "evidence": "79% do voto de Zema e 53% do de Caiado podem mudar; 65% não conhecem Renan, 49% não conhecem Zema, 44% não conhecem Caiado (pp. 34, 36).",
            },
            {
                "claim": "A faixa que decide é a de 2 a 5 salários",
                "evidence": "42% do eleitorado, aprovação 46 × 48 e 2º turno 41 × 43. É exatamente a faixa alvo da isenção do IRPF, e 68% dizem não ter sido alcançados (pp. 49, 21, 68).",
            },
            {
                "claim": "A proibição de visitas une a direita inteira",
                "evidence": "52% acham a decisão errada; 83% da direita não bolsonarista e 92% dos bolsonaristas concordam; entre independentes, 50 × 39 (pp. 86, 87).",
            },
        ],
        "ameacas": [
            {
                "claim": "Lula recupera onde Flávio precisa crescer",
                "evidence": "Aprovação entre evangélicos sobe de 28% para 38% em cinco meses; no Nordeste, de 63% para 66%; entre beneficiários do Bolsa Família, de 59% para 66% (pp. 50, 45, 51).",
            },
            {
                "claim": "A expectativa econômica virou",
                "evidence": "46% esperam melhora nos próximos 12 meses, melhor marca desde janeiro, mesmo com 69% dizendo que o poder de compra caiu (pp. 64, 62).",
            },
            {
                "claim": "Renan Santos cresce dentro da direita",
                "evidence": "Potencial de voto sobe de 6% para 15% e ele já tem 10% da direita não bolsonarista; no cenário 4, saiu de 24 em janeiro para 35 em agosto (pp. 36, 18, 29).",
            },
            {
                "claim": "A agenda dominante não é a do debate",
                "evidence": "Violência é a maior preocupação para 29%, contra 13% para economia; o relatório não cruza preocupação com voto (p. 98).",
            },
        ],
    }


def normalize_comparators() -> list[dict]:
    rows = []
    for item in COMPARATORS:
        row = dict(item)
        row["first_valid"] = [
            round(100 * value / (100 - item["nonchoice_first"]), 2)
            for value in item["first"]
        ]
        row["runoff_valid"] = [
            round(100 * value / (100 - item["nonchoice_runoff"]), 2)
            for value in item["runoff"]
        ]
        rows.append(row)
    return rows


def build_payload(refresh_ibge: bool) -> dict:
    return {
        "generated": date.today().isoformat(),
        "metadata": {
            "registry": "BR-06591/2026",
            "registered": "2026-07-30",
            "field": "31/07-03/08/2026",
            "release": "05/08/2026",
            "sample": 2004,
            "mode": "presencial domiciliar",
            "sponsor": "Banco Genial S.A.",
            "cost_brl": 433255.92,
            "institute": "Quaest Pesquisa e Consultoria Ltda.",
            "statistician": "Margarida Maria de Mendonça, CONRE 6731",
            "quality_control": "30% dos áudios e checagem de geolocalização declarados",
        },
        "manifest": manifest(),
        "questionnaire": questionnaire_diagnostics(),
        "publication_coverage": publication_coverage(),
        "vote": VOTE,
        "report": {
            "spontaneous": SPONTANEOUS,
            "bloc_shares": BLOC_SHARES,
            "first_round_by_bloc": FIRST_ROUND_BY_BLOC,
            "runoff_by_bloc": RUNOFF_BY_BLOC,
            "leader_image": LEADER_IMAGE,
            "potential_by_bloc": POTENTIAL_BY_BLOC,
            "runoff_scenarios": RUNOFF_SCENARIOS,
            "scenario_segments": SCENARIO_SEGMENTS,
            "vote_firmness": VOTE_FIRMNESS,
            "approval_by_segment": APPROVAL_BY_SEGMENT,
            "runoff_by_segment": RUNOFF_BY_SEGMENT,
            "income_shares": INCOME_SHARES,
            "economy": ECONOMY,
            "programs": PROGRAMS,
            "agenda": AGENDA,
            "media": MEDIA,
            "campaign": CAMPAIGN,
            "transcription": (
                "As tabelas do relatório são imagens sem camada de texto. Todos os "
                "números foram lidos página a página e cada bloco cita a página."
            ),
        },
        "strategy": {
            "reconstruction": bloc_reconstruction(),
            "useful_vote": useful_vote_map(),
            "soft_third_way": soft_third_way(),
            "substitution": substitution_ledger(),
            "conversion": conversion_ledger(),
            "programs": program_reach(),
            "media": media_asymmetry(),
            "swot": strategy_swot(),
        },
        "uncertainty": {
            "first_round": margin_scenarios(0.39, 0.30),
            "runoff": margin_scenarios(0.44, 0.39),
        },
        "benchmarks": {"tse": tse_benchmark(), "income": income_benchmark()},
        "territory": territory_payload(refresh_ibge),
        "comparators": normalize_comparators(),
        "limits": [
            "Microdados, pesos finais, variância dos pesos e n efetivo não foram publicados.",
            "A fórmula e as interações do MRP não foram publicadas.",
            "O anexo territorial não contém voto por setor nem probabilidade de inclusão.",
            "O pagador está documentado; interferência editorial ou compra de resultado não está.",
            "Variações de uma onda não identificam sozinhas um evento causal.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--refresh-ibge", action="store_true")
    args = parser.parse_args()
    payload = build_payload(args.refresh_ibge)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "published_questions": payload["publication_coverage"]["august"][
                    "published"
                ],
                "unpublished_questions": payload["publication_coverage"]["august"][
                    "unpublished"
                ],
                "common_municipalities": payload["territory"]["comparison"][
                    "common_municipalities"
                ],
                "common_exact_sectors": payload["territory"]["comparison"][
                    "common_exact_sectors"
                ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
