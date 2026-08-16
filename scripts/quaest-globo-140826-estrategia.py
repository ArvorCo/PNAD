#!/usr/bin/env python3
"""Camada estratégica do dossiê Quaest/Globo de 14 de agosto de 2026.

O relatório é composto por imagens. Cada bloco transcrito abaixo carrega a
página de origem ao lado dos valores. Os controles internos recompõem números
já publicados a partir de cruzamentos independentes antes de qualquer conta
derivada.

Consome o relatório da rodada e escreve `docs/assets/quaest_globo_140826_estrategia.json`.
Rode primeiro `scripts/quaest-globo-140826-audit.py`, que produz a base analítica
com a qual esta camada é conferida.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts/quaest-globo-140826-audit.py"
OUTPUT = ROOT / "docs/assets/quaest_globo_140826_estrategia.json"

# Ordem das colunas nas transcrições de primeiro turno.
BALLOT = [
    "Lula",
    "Flávio",
    "Renan",
    "Caiado",
    "Cury",
    "Zema",
    "Samara",
    "Outros",
    "Indeciso",
    "Branco",
]

# Bloco que disputa o mesmo eleitor antilulista de Flávio. Samara Martins (UP)
# fica de fora por ser candidatura de esquerda, e não terceira via.
THIRD_WAY = ("Renan", "Caiado", "Cury", "Zema")

FIRST_ROUND_REGION = {
    "page": 17,
    "moe": {"Nordeste": 4, "Sudeste": 3, "Sul": 6, "Centro-Oeste/Norte": 5},
    "values": {
        "Nordeste": [57, 23, 4, 1, 2, 0, 0, 0, 8, 5],
        "Sudeste": [32, 35, 4, 3, 2, 4, 1, 0, 9, 10],
        "Sul": [25, 40, 5, 3, 2, 2, 1, 0, 16, 6],
        "Centro-Oeste/Norte": [36, 26, 3, 10, 3, 1, 2, 0, 12, 7],
    },
}

FIRST_ROUND_INCOME = {
    "page": 21,
    "moe": {"Até 2 SM": 4, "2 a 5 SM": 3, "Mais de 5 SM": 4},
    "values": {
        "Até 2 SM": [52, 23, 2, 2, 2, 1, 0, 1, 11, 6],
        "2 a 5 SM": [34, 33, 4, 4, 2, 2, 1, 0, 11, 9],
        "Mais de 5 SM": [31, 36, 5, 5, 3, 3, 1, 0, 8, 8],
    },
}

FIRST_ROUND_INTEREST = {
    "page": 25,
    "moe": {"Muito interessado": 4, "Pouco interessado": 3, "Nada interessado": 5},
    "values": {
        "Muito interessado": [47, 37, 4, 3, 1, 2, 0, 0, 4, 2],
        "Pouco interessado": [38, 29, 4, 4, 2, 2, 1, 0, 13, 7],
        "Nada interessado": [26, 24, 3, 5, 3, 2, 1, 1, 14, 21],
    },
}

INTEREST_SHARES = {
    "page": 101,
    "values": {
        "Muito interessado": 36,
        "Pouco interessado": 42,
        "Nada interessado": 21,
        "Não sabe": 1,
    },
}

# Série de cinco ondas da pergunta "sua escolha é definitiva ou pode mudar?".
# Cada par é [é definitiva, pode mudar] na onda correspondente.
VOTE_FIRMNESS = {
    "page": 28,
    "waves": ["Mai/26", "Jun/26", "Jul/26", "05 Ago", "14 Ago"],
    "moe": {"Lula": 3, "Flávio": 4, "Caiado": 12, "Renan": 12, "Zema": 16},
    "definitive": {
        "Lula": [70, 71, 77, 77, 77],
        "Flávio": [66, 70, 62, 68, 70],
        "Caiado": [35, 44, 43, 53, 55],
        "Renan": [40, 37, 35, 55, 57],
        "Zema": [35, 26, 30, 20, 23],
    },
    "mutable": {
        "Lula": [29, 29, 23, 22, 22],
        "Flávio": [34, 30, 37, 32, 30],
        "Caiado": [65, 52, 57, 47, 45],
        "Renan": [60, 63, 65, 45, 43],
        "Zema": [65, 74, 70, 79, 77],
    },
}

# Conhecimento, potencial e rejeição. Cada tripla é
# [conhece e votaria, não conhece, conhece e não votaria].
PROFILE_POSITIONING = {
    "page": 79,
    "moe": {
        "Lulista": 5,
        "Esquerda não lulista": 6,
        "Independente": 4,
        "Direita não bolsonarista": 5,
        "Bolsonarista": 6,
    },
    "values": {
        "Lulista": {
            "Lula": [95, 1, 4],
            "Flávio": [10, 1, 89],
            "Caiado": [7, 54, 39],
            "Zema": [3, 59, 38],
            "Renan": [5, 73, 22],
        },
        "Esquerda não lulista": {
            "Lula": [88, 2, 10],
            "Flávio": [8, 2, 90],
            "Caiado": [12, 38, 50],
            "Zema": [8, 40, 52],
            "Renan": [9, 64, 27],
        },
        "Independente": {
            "Lula": [35, 5, 60],
            "Flávio": [34, 7, 59],
            "Caiado": [16, 56, 28],
            "Zema": [13, 59, 28],
            "Renan": [8, 79, 13],
        },
        "Direita não bolsonarista": {
            "Lula": [8, 2, 90],
            "Flávio": [81, 2, 17],
            "Caiado": [43, 22, 35],
            "Zema": [42, 29, 29],
            "Renan": [28, 45, 27],
        },
        "Bolsonarista": {
            "Lula": [5, 4, 91],
            "Flávio": [91, 2, 7],
            "Caiado": [41, 22, 37],
            "Zema": [35, 34, 31],
            "Renan": [30, 48, 22],
        },
    },
}

PROFILE_REGION = {
    "page": 72,
    "values": {
        "Nordeste": {"Lula": [60, 2, 38], "Flávio": [30, 7, 63]},
        "Sudeste": {"Lula": [40, 3, 57], "Flávio": [44, 5, 51]},
        "Sul": {"Lula": [32, 6, 62], "Flávio": [53, 5, 42]},
        "Centro-Oeste/Norte": {"Lula": [45, 3, 52], "Flávio": [41, 4, 55]},
    },
}

PROFILE_INCOME = {
    "page": 76,
    "values": {
        "Até 2 SM": {"Lula": [59, 4, 37], "Flávio": [30, 8, 62]},
        "2 a 5 SM": {"Lula": [40, 3, 57], "Flávio": [44, 5, 51]},
        "Mais de 5 SM": {"Lula": [36, 3, 61], "Flávio": [48, 3, 49]},
    },
}

EXPECTED_WINNER_REGION = {
    "page": 92,
    "values": {
        "Nordeste": {"Lula": 67, "Flávio": 19, "Não sabe": 13},
        "Sudeste": {"Lula": 54, "Flávio": 29, "Não sabe": 14},
        "Sul": {"Lula": 49, "Flávio": 36, "Não sabe": 13},
        "Centro-Oeste/Norte": {"Lula": 54, "Flávio": 25, "Não sabe": 15},
    },
}

EXPECTED_WINNER_INCOME = {
    "page": 96,
    "values": {
        "Até 2 SM": {"Lula": 61, "Flávio": 18, "Não sabe": 17},
        "2 a 5 SM": {"Lula": 55, "Flávio": 29, "Não sabe": 13},
        "Mais de 5 SM": {"Lula": 53, "Flávio": 32, "Não sabe": 11},
    },
}

EXPECTED_WINNER_POSITIONING = {
    "page": 99,
    "values": {
        "Lulista": {"Lula": 91, "Flávio": 3, "Não sabe": 6},
        "Esquerda não lulista": {"Lula": 87, "Flávio": 2, "Não sabe": 9},
        "Independente": {"Lula": 52, "Flávio": 18, "Não sabe": 25},
        "Direita não bolsonarista": {"Lula": 36, "Flávio": 52, "Não sabe": 8},
        "Bolsonarista": {"Lula": 18, "Flávio": 75, "Não sabe": 5},
    },
}

CONCERNS_POSITIONING = {
    "page": 159,
    "values": {
        "Lulista": {
            "Violência": 37,
            "Problemas sociais": 16,
            "Saúde": 19,
            "Corrupção": 7,
            "Economia": 9,
            "Educação": 5,
        },
        "Esquerda não lulista": {
            "Violência": 30,
            "Problemas sociais": 18,
            "Saúde": 12,
            "Corrupção": 12,
            "Economia": 13,
            "Educação": 10,
        },
        "Independente": {
            "Violência": 35,
            "Problemas sociais": 10,
            "Saúde": 13,
            "Corrupção": 13,
            "Economia": 14,
            "Educação": 9,
        },
        "Direita não bolsonarista": {
            "Violência": 30,
            "Problemas sociais": 9,
            "Saúde": 11,
            "Corrupção": 18,
            "Economia": 23,
            "Educação": 6,
        },
        "Bolsonarista": {
            "Violência": 32,
            "Problemas sociais": 9,
            "Saúde": 13,
            "Corrupção": 22,
            "Economia": 17,
            "Educação": 4,
        },
    },
}

CONCERNS_REGION = {
    "page": 155,
    "values": {
        "Nordeste": {"Violência": 39, "Saúde": 15, "Economia": 14, "Corrupção": 11},
        "Sudeste": {"Violência": 30, "Saúde": 13, "Economia": 14, "Corrupção": 15},
        "Sul": {"Violência": 32, "Saúde": 12, "Economia": 20, "Corrupção": 13},
        "Centro-Oeste/Norte": {
            "Violência": 32,
            "Saúde": 15,
            "Economia": 14,
            "Corrupção": 15,
        },
    },
}

CONCERNS_INCOME = {
    "page": 158,
    "values": {
        "Até 2 SM": {"Violência": 39, "Saúde": 20, "Economia": 10, "Corrupção": 11},
        "2 a 5 SM": {"Violência": 33, "Saúde": 13, "Economia": 17, "Corrupção": 12},
        "Mais de 5 SM": {"Violência": 28, "Saúde": 9, "Economia": 17, "Corrupção": 18},
    },
}

# Segundo turno contra Caiado, por segmento social, no formato [Lula, Caiado].
CAIADO_SEGMENTS = {
    "page": 41,
    "values": {
        "Nordeste": [62, 24],
        "Até 2 SM": [57, 24],
        "Preta": [52, 29],
        "Fundamental": [53, 30],
        "Mulheres": [47, 31],
        "Parda": [48, 32],
        "Católica": [50, 35],
        "60 anos ou mais": [48, 34],
        "16 a 34 anos": [45, 33],
        "Centro-Oeste/Norte": [45, 37],
        "35 a 59 anos": [42, 41],
        "Médio": [39, 39],
        "2 a 5 SM": [41, 41],
        "Sudeste": [38, 40],
        "Homens": [41, 44],
        "Branca": [38, 44],
        "Superior": [36, 47],
        "Mais de 5 SM": [34, 46],
        "Evangélica": [30, 46],
        "Sul": [28, 50],
    },
}

BOLSA_FAMILIA = {"page": 195, "sim": 22, "não": 78}

# Cruzamento entre os eixos do plano de governo registrado e os recortes em que
# a Quaest mede o déficit de Flávio. Cada linha aponta a página do plano.
PLAN = "FLÁVIO BOLSONARO, Para o Brasil vencer o atraso, plano de governo 2026"
PLAN_CROSSWALK = [
    {
        "axis": "Brasil sem Medo",
        "plan_pages": [13, 16],
        "quaest_pages": [154, 155, 158, 159],
        "segments": ["Nordeste", "Até 2 SM", "Mulheres", "Preta", "Fundamental"],
        "evidence": "Violência é a maior preocupação nos cinco blocos políticos, "
        "inclusive entre lulistas, 37%, e é mais alta no Nordeste, 39%, e na "
        "faixa até 2 SM, 39%, exatamente onde Flávio perde o segundo turno "
        "por 35 e por 31 pontos.",
        "kind": "agenda transversal",
    },
    {
        "axis": "Brasil por Elas",
        "plan_pages": [17, 22],
        "quaest_pages": [31, 163],
        "segments": ["Mulheres"],
        "evidence": "Flávio perde entre mulheres por 9 pontos e elas se informam "
        "mais por TV, 38%, do que por redes, 31%. O eixo tem doze programas "
        "com entrega material e canal próprio de atendimento.",
        "kind": "déficit demográfico",
    },
    {
        "axis": "Brasil mais Barato",
        "plan_pages": [29, 33],
        "quaest_pages": [141, 145, 158],
        "segments": ["2 a 5 SM", "Até 2 SM"],
        "evidence": "49% dizem que a economia piorou e 68% viram alimento subir. "
        "Economia é a segunda preocupação na faixa de 2 a 5 SM, 17%, a faixa "
        "em que o primeiro turno está empatado em 34 a 33.",
        "kind": "faixa decisiva",
    },
    {
        "axis": "Brasil que Prepara, saúde e cuidado",
        "plan_pages": [37, 39],
        "quaest_pages": [158, 31],
        "segments": ["Até 2 SM", "60 anos ou mais"],
        "evidence": "Saúde é a segunda preocupação da faixa até 2 SM, 20%, contra "
        "9% no topo da renda. Flávio perde por 31 nessa faixa e por 13 entre "
        "os 60 anos ou mais.",
        "kind": "déficit material",
    },
    {
        "axis": "O lado dos aposentados",
        "plan_pages": [72, 73],
        "quaest_pages": [31, 164],
        "segments": ["60 anos ou mais"],
        "evidence": "Entre 60 anos ou mais, TV é fonte principal para 52% e redes "
        "para 16%. É o recorte de maior distância de canal e o eixo é o de "
        "entrega mais direta, com o pacote antifraude do INSS.",
        "kind": "déficit de canal",
    },
    {
        "axis": "Desenvolvimento regional, Norte e Nordeste",
        "plan_pages": [60, 61],
        "quaest_pages": [17, 31, 92],
        "segments": ["Nordeste", "Centro-Oeste/Norte"],
        "evidence": "O Nordeste é o pior recorte de Flávio, 61 a 26 no segundo "
        "turno, e o de maior expectativa de vitória de Lula, 67%. O eixo trata "
        "água, irrigação, ferrovia e energia, não assistência.",
        "kind": "déficit regional",
    },
    {
        "axis": "Brasil sem Fila",
        "plan_pages": [23, 28],
        "quaest_pages": [154, 158],
        "segments": ["Até 2 SM", "60 anos ou mais", "Mulheres"],
        "evidence": "Saúde e serviço público aparecem como preocupação sobretudo "
        "na baixa renda. O eixo é o único do plano que promete efeito sentido "
        "sem depender de nova despesa visível.",
        "kind": "conversão material",
    },
    {
        "axis": "Brasil que Cumpre a Constituição",
        "plan_pages": [65, 67],
        "quaest_pages": [159],
        "segments": ["Direita não bolsonarista", "Bolsonarista"],
        "evidence": "Corrupção é a segunda preocupação da direita não "
        "bolsonarista, 18%, e dos bolsonaristas, 22%. É agenda de consolidação "
        "do próprio campo, não de expansão.",
        "kind": "consolidação de campo",
    },
]

# Manchetes efetivamente publicadas sobre esta rodada, com o enquadramento
# declarado no título. Coletadas em 16/08/2026.
MEDIA_FRAME = {
    "collected": "2026-08-16",
    "headlines": [
        {
            "outlet": "Poder360",
            "headline": "Lula tem 43% ante 40% de Flávio Bolsonaro no 2º turno, diz Quaest",
            "lead_number": "runoff",
            "url": "https://www.poder360.com.br/poder-eleicoes-2026/lula-tem-43-ante-40-de-flavio-bolsonaro-no-2o-turno-diz-quaest/",
        },
        {
            "outlet": "Estado de Minas",
            "headline": "Quaest: Lula tem 43% contra 40% de Flávio Bolsonaro no 2º turno",
            "lead_number": "runoff",
            "url": "https://www.em.com.br/politica/2026/08/7480474-quaest-lula-tem-43-contra-40-de-flavio-bolsonaro-no-2-turno.html",
        },
        {
            "outlet": "Imirante",
            "headline": "Pesquisa Quaest aponta empate técnico entre Lula e Flávio Bolsonaro no segundo turno",
            "lead_number": "runoff",
            "url": "https://m.imirante.com/noticias/brasil/2026/08/15/ipolitica-pesquisa-quaest-aponta-empate-tecnico-entre-lula-e-flavio-bolsonaro-no-segundo-turno",
        },
        {
            "outlet": "Revista Oeste",
            "headline": "Quaest volta a mostrar empate técnico entre Lula e Flávio no 2º turno",
            "lead_number": "runoff",
            "url": "https://revistaoeste.com/politica/quaest-volta-a-mostrar-empate-tecnico-entre-lula-e-flavio-no-2o-turno/",
        },
        {
            "outlet": "O Cafezinho",
            "headline": "Lula lidera Flávio Bolsonaro em simulação da Quaest",
            "lead_number": "runoff",
            "url": "https://www.ocafezinho.com/2026/08/15/lula-lidera-flavio-bolsonaro-em-simulacao-da-quaest",
        },
        {
            "outlet": "Metrópoles",
            "headline": "Quaest: Lula tem 38% no 1º turno; Flávio, 31%; Caiado, 4%; Renan, 4%; Zema, 2%",
            "lead_number": "first_round",
            "url": "https://www.metropoles.com/brasil/quaest-lula-e-flavio-bolsonaro-1o-turno",
        },
        {
            "outlet": "Gazeta do Povo",
            "headline": "Pesquisa Quaest mostra como está a disputa para presidente",
            "lead_number": "first_round",
            "url": "https://www.gazetadopovo.com.br/eleicoes/2026/pesquisa-eleitoral-2026/quaest-pesquisa-presidente-agosto-2026/",
        },
    ],
    "questions_in_coverage": [
        "intenção de voto no 1º turno",
        "intenção de voto no 2º turno",
        "aprovação do governo",
        "rejeição",
    ],
}

MARCAL = {
    "registered": "2026-08-15",
    "party": "PRTB",
    "ticket": "Brasil Próspero",
    "running_mate": "Leonardo Avalanche",
    "avalanche_in_this_poll_pct": 0,
    "ineligible_until": 2032,
    "ineligibility_basis": "condenação no TRE-SP por uso indevido dos meios de "
    "comunicação na campanha municipal de 2024",
    "enabling_decision": "liminar da 428ª Zona Eleitoral de Santana de Parnaíba "
    "que regularizou a filiação partidária, com recurso possível ao TSE",
    "legal_status_of_votes": "art. 16-A da Lei 9.504/97: o candidato sub judice "
    "mantém o nome na urna e faz campanha; se o indeferimento transitar em "
    "julgado, os votos são computados como anulados",
    "prior_measurement": {
        "institute": "Quaest",
        "field": "2024-09-25/2024-09-29",
        "published": "2024-10-14",
        "scenario": "Lula 32, Marçal 18, Tarcísio 15",
        "note": "cenário de setembro de 2024, sem Bolsonaro e antes da "
        "candidatura de Flávio; dividia a base bolsonarista de 2022 em 33% "
        "para Marçal e 32% para Tarcísio",
    },
    "sp_2024_first_round_pct": 28.14,
}

HISTORIC_CONSOLIDATION = {
    "2018": {
        "third_way_valid_pct": 18.23,
        "detail": "Ciro 12,47 + Alckmin 4,76 + Marina 1,00",
        "leaders_valid_pct": 75.72,
    },
    "2022": {
        "third_way_valid_pct": 7.20,
        "detail": "Tebet 4,16 + Ciro 3,04",
        "leaders_valid_pct": 91.63,
    },
}


def load_audit():
    spec = importlib.util.spec_from_file_location("quaest_globo_140826_audit", AUDIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def as_row(values: list[int]) -> dict[str, int]:
    return dict(zip(BALLOT, values))


def validate(audit) -> None:
    """Fecha cada transcrição antes de qualquer conta derivada."""
    for block in (FIRST_ROUND_REGION, FIRST_ROUND_INCOME, FIRST_ROUND_INTEREST):
        for cut, values in block["values"].items():
            if len(values) != len(BALLOT):
                raise ValueError(f"Linha incompleta em {cut}")
            if sum(values) != 100:
                raise ValueError(f"Transcrição não fecha em 100 para {cut}")
    if sum(INTEREST_SHARES["values"].values()) != 100:
        raise ValueError("Partição de interesse não fecha em 100")
    for wave_set in (VOTE_FIRMNESS["definitive"], VOTE_FIRMNESS["mutable"]):
        for name, series in wave_set.items():
            if len(series) != len(VOTE_FIRMNESS["waves"]):
                raise ValueError(f"Série de firmeza incompleta para {name}")
    for name in VOTE_FIRMNESS["definitive"]:
        last = (
            VOTE_FIRMNESS["definitive"][name][-1] + VOTE_FIRMNESS["mutable"][name][-1]
        )
        if not 99 <= last <= 101:
            raise ValueError(f"Firmeza de {name} não fecha em 100 na última onda")
    for bloc, rows in PROFILE_POSITIONING["values"].items():
        for name, triple in rows.items():
            if sum(triple) != 100:
                raise ValueError(f"Perfil não fecha para {name} em {bloc}")
    for block in (PROFILE_REGION, PROFILE_INCOME):
        for cut, rows in block["values"].items():
            for name, triple in rows.items():
                if sum(triple) != 100:
                    raise ValueError(f"Perfil não fecha para {name} em {cut}")
    if BOLSA_FAMILIA["sim"] + BOLSA_FAMILIA["não"] != 100:
        raise ValueError("Bolsa Família não fecha em 100")
    national = audit.FIRST_ROUND["values"]
    if national["Lula"] != 38 or national["Flávio Bolsonaro"] != 31:
        raise ValueError("Base analítica divergente do topline transcrito")


def rejection_control(audit) -> dict:
    """Recompõe a rejeição nacional a partir do cruzamento por posicionamento."""
    shares = audit.POSITIONING["shares"]
    blocs = PROFILE_POSITIONING["values"]
    known = sum(shares[bloc] for bloc in blocs)
    result = {}
    for name in ("Lula", "Flávio"):
        wasted = sum(
            shares[bloc] * blocs[bloc][name][2] / 100
            for bloc in blocs
            if blocs[bloc][name][2] >= 80
        )
        total = sum(shares[bloc] * blocs[bloc][name][2] / 100 for bloc in blocs)
        result[name] = {
            "recomposed_pct": round(100 * total / known, 1),
            "points_from_hostile_blocs": round(wasted, 2),
            "hostile_share_of_rejection_pct": round(100 * wasted / total, 1),
        }
    published = audit.OTHER_FINDINGS["potential_rejection"]
    result["published"] = {
        "Lula": published["Lula"][1],
        "Flávio": published["Flávio Bolsonaro"][1],
    }
    result["independent_bloc"] = {
        "Lula": blocs["Independente"]["Lula"][2],
        "Flávio": blocs["Independente"]["Flávio"][2],
        "difference": blocs["Independente"]["Flávio"][2]
        - blocs["Independente"]["Lula"][2],
    }
    result["note"] = (
        "A rejeição nacional é maior para Flávio, mas no bloco independente, "
        "que é o maior da amostra, os dois estão empatados dentro do "
        "arredondamento."
    )
    return result


def third_way_geography(audit) -> dict:
    """Onde estão os 12 pontos de terceira via e onde Flávio já está forte."""
    cuts = {}
    partitions = {}
    blocks = (
        (FIRST_ROUND_REGION, "region"),
        (FIRST_ROUND_INCOME, "income"),
    )
    for block, label in blocks:
        shares = audit.SAMPLE_SHARES[label]
        recomposed = 0.0
        friendly = 0.0
        for cut, values in block["values"].items():
            row = as_row(values)
            third = sum(row[name] for name in THIRD_WAY)
            margin = row["Flávio"] - row["Lula"]
            weight = shares[cut] * third / 100
            recomposed += weight
            if margin >= -1:
                friendly += weight
            cuts[cut] = {
                "partition": label,
                "sample_share": shares[cut],
                "Lula": row["Lula"],
                "Flávio": row["Flávio"],
                "flavio_margin": margin,
                "third_way": third,
                "non_choice": row["Indeciso"] + row["Branco"],
                "addressable": third + row["Indeciso"] + row["Branco"],
                "page": block["page"],
            }
        partitions[label] = {
            "recomposed_third_way": round(recomposed, 2),
            "points_where_flavio_leads_or_ties": round(friendly, 2),
            "share_where_flavio_leads_or_ties_pct": round(
                100 * friendly / recomposed, 1
            ),
        }
    return {
        "cuts": cuts,
        "partitions": partitions,
        "published_third_way": 12,
        "note": "A terceira via se concentra nos mesmos recortes em que Flávio "
        "já lidera ou empata o primeiro turno. Consolidá-la não exige converter "
        "um único eleitor de Lula. A soma ponderada de cada partição recompõe "
        "os 12 pontos publicados, o que serve de controle de transcrição.",
    }


def interest_profile() -> dict:
    rows = {
        cut: as_row(values) for cut, values in FIRST_ROUND_INTEREST["values"].items()
    }
    result = {}
    for cut, row in rows.items():
        third = sum(row[name] for name in THIRD_WAY)
        non_choice = row["Indeciso"] + row["Branco"]
        valid = 100 - non_choice
        result[cut] = {
            "Lula": row["Lula"],
            "Flávio": row["Flávio"],
            "lula_lead": row["Lula"] - row["Flávio"],
            "third_way": third,
            "non_choice": non_choice,
            "lula_valid_pct": round(100 * row["Lula"] / valid, 1),
            "flavio_valid_pct": round(100 * row["Flávio"] / valid, 1),
        }
    return {
        "page": FIRST_ROUND_INTEREST["page"],
        "shares": INTEREST_SHARES["values"],
        "cuts": result,
        "counterpoint": "A vantagem de Lula cresce com o interesse: 10 pontos "
        "entre os muito interessados contra 7 no total. Um eleitorado mais "
        "engajado não favorece Flávio automaticamente. O que muda com o "
        "interesse é o tamanho do estoque disponível, não a direção da margem.",
    }


def soft_vote() -> dict:
    """Voto declarado mutável, medido pelo próprio instituto na página 28."""
    audit_values = {"Renan": 4, "Caiado": 4, "Zema": 2, "Cury": 2}
    measured = {}
    for name in ("Renan", "Caiado", "Zema"):
        share = VOTE_FIRMNESS["mutable"][name][-1]
        measured[name] = {
            "points": audit_values[name],
            "mutable_pct": share,
            "mutable_points": round(audit_values[name] * share / 100, 3),
            "moe_pp": VOTE_FIRMNESS["moe"][name],
        }
    measured_points = sum(item["mutable_points"] for item in measured.values())
    covered = sum(item["points"] for item in measured.values())
    rate = measured_points / covered
    third_total = covered + audit_values["Cury"]
    return {
        "page": VOTE_FIRMNESS["page"],
        "third_way_points": third_total,
        "measured": measured,
        "unmeasured": {
            "Cury": audit_values["Cury"],
            "reason": "fora dos cinco " "candidatos exibidos no gráfico do instituto",
        },
        "measured_mutable_points": round(measured_points, 3),
        "measured_mutable_rate_pct": round(100 * rate, 1),
        "extrapolated_mutable_points": round(rate * third_total, 3),
        "own_soft_vote": {
            "Flávio": round(31 * VOTE_FIRMNESS["mutable"]["Flávio"][-1] / 100, 2),
            "Lula": round(38 * VOTE_FIRMNESS["mutable"]["Lula"][-1] / 100, 2),
        },
        "note": "Zema mantém a maior taxa de voto mutável nas cinco ondas, de "
        "65% a 77%. A margem de erro dos candidatos menores é alta, de 12 a 16 "
        "pontos, e a direção é o que sobrevive à incerteza, não o nível.",
    }


def single_round_equation(audit) -> dict:
    """Quanto falta para Flávio vencer no primeiro turno.

    Com Lula parado em 38, terceira via em 12 e votos válidos declarados em 82,
    a condição de maioria absoluta é 12t + d + 0,5g > 10, em que t é a fração da
    terceira via capturada, d são pontos tirados de Lula e g são pontos
    recrutados no bloco de indecisos e brancos que passam a ser voto válido.
    """
    values = audit.FIRST_ROUND["values"]
    lula = values["Lula"]
    flavio = values["Flávio Bolsonaro"]
    third = values["Renan Santos"] + values["Ronaldo Caiado"]
    third += values["Augusto Cury"] + values["Romeu Zema"]
    left_minor = values["Samara Martins"]
    non_choice = values["Indeciso"] + values["Branco, nulo ou não vota"]
    valid = lula + flavio + third + left_minor
    needed = valid / 2 - flavio
    grid = []
    for capture_pct in (25, 50, 75, 83.3, 100):
        captured = third * capture_pct / 100
        remaining = needed - captured
        grid.append(
            {
                "third_way_capture_pct": capture_pct,
                "captured_points": round(captured, 2),
                "still_missing_points": round(max(remaining, 0), 2),
                "non_choice_points_required": round(max(2 * remaining, 0), 2),
                "feasible_with_non_choice": 2 * remaining <= non_choice,
            }
        )
    soft = soft_vote()
    residual = needed - soft["extrapolated_mutable_points"]
    benchmark = {}
    for year, item in HISTORIC_CONSOLIDATION.items():
        squeeze = valid * (item["leaders_valid_pct"] / 100) - (lula + flavio)
        benchmark[year] = {
            "third_way_valid_pct": item["third_way_valid_pct"],
            "detail": item["detail"],
            "leaders_valid_pct": item["leaders_valid_pct"],
            "points_squeezed_if_repeated": round(squeeze, 2),
            "enough_even_if_all_went_to_flavio": squeeze >= needed,
        }
    return {
        "page": audit.FIRST_ROUND["page"],
        "base": {
            "Lula": lula,
            "Flávio": flavio,
            "third_way": third,
            "left_minor": left_minor,
            "non_choice": non_choice,
            "declared_valid": valid,
        },
        "current_valid_pct": {
            "Lula": round(100 * lula / valid, 2),
            "Flávio": round(100 * flavio / valid, 2),
        },
        "equation": "12t + d + 0,5g > 10",
        "points_needed": round(needed, 2),
        "third_way_only_threshold_pct": round(100 * needed / third, 1),
        "lula_only_threshold_points": round(needed, 2),
        "non_choice_only_threshold_points": round(2 * needed, 2),
        "non_choice_route_possible": 2 * needed <= non_choice,
        "grid": grid,
        "soft_vote_route": {
            "mutable_points_available": soft["extrapolated_mutable_points"],
            "residual_points": round(residual, 2),
            "non_choice_points_required": round(2 * residual, 2),
            "non_choice_share_required_pct": round(100 * 2 * residual / non_choice, 1),
        },
        "historic_benchmark": benchmark,
        "label": "aritmética condicional, não previsão",
    }


def inevitability_premium(audit) -> dict:
    """Expectativa de vitória menos intenção de voto, no mesmo recorte."""
    national = {
        "Lula": audit.OTHER_FINDINGS["expected_winner"]["Lula"]
        - audit.FIRST_ROUND["values"]["Lula"],
        "Flávio": audit.OTHER_FINDINGS["expected_winner"]["Flávio Bolsonaro"]
        - audit.FIRST_ROUND["values"]["Flávio Bolsonaro"],
    }
    cuts = {}
    pairs = (
        (EXPECTED_WINNER_REGION, FIRST_ROUND_REGION),
        (EXPECTED_WINNER_INCOME, FIRST_ROUND_INCOME),
    )
    for expected, vote in pairs:
        for cut, winners in expected["values"].items():
            row = as_row(vote["values"][cut])
            cuts[cut] = {
                "lula_premium": winners["Lula"] - row["Lula"],
                "flavio_premium": winners["Flávio"] - row["Flávio"],
                "spread": (winners["Lula"] - row["Lula"])
                - (winners["Flávio"] - row["Flávio"]),
                "unknown": winners["Não sabe"],
                "pages": [expected["page"], vote["page"]],
            }
    bloc = EXPECTED_WINNER_POSITIONING["values"]["Independente"]
    return {
        "definition": "expectativa de vitória menos intenção de voto de primeiro "
        "turno, dentro do mesmo recorte",
        "national": national,
        "national_spread": national["Lula"] - national["Flávio"],
        "cuts": cuts,
        "independents": {
            "expects_Lula": bloc["Lula"],
            "expects_Flávio": bloc["Flávio"],
            "ratio": round(bloc["Lula"] / bloc["Flávio"], 2),
            "unknown": bloc["Não sabe"],
            "page": EXPECTED_WINNER_POSITIONING["page"],
        },
        "note": "Em todos os recortes publicados de região e renda a expectativa "
        "de Flávio fica abaixo do próprio voto, e a de Lula acima. Sem inverter "
        "isso, o pedido de voto útil no primeiro turno não tem a quem convencer.",
    }


def substitution_by_segment(audit) -> dict:
    """Onde o substituto testado bate o candidato preferido."""
    flavio = audit.SEGMENTS["runoff"]
    caiado = CAIADO_SEGMENTS["values"]
    rows = {}
    for segment, (lula_c, caiado_v) in caiado.items():
        lula_f, flavio_v = flavio[segment]
        rows[segment] = {
            "flavio_margin": flavio_v - lula_f,
            "caiado_margin": caiado_v - lula_c,
            "difference": (flavio_v - lula_f) - (caiado_v - lula_c),
        }
    better = sorted(name for name, row in rows.items() if row["difference"] < 0)
    tied = sorted(name for name, row in rows.items() if row["difference"] == 0)
    return {
        "pages": [audit.SEGMENTS["page"], CAIADO_SEGMENTS["page"]],
        "rows": rows,
        "caiado_better_than_flavio": better,
        "tied": tied,
        "note": "Nesta rodada o substituto testado não supera Flávio em nenhum "
        "segmento social publicado. O contraponto que existia na rodada "
        "anterior fechou, e isso é medição, não inferência.",
    }


def media_frame(audit) -> dict:
    published = audit.instrument_payload()["current"]["published_count"]
    covered = len(MEDIA_FRAME["questions_in_coverage"])
    runoff_first = sum(
        1 for item in MEDIA_FRAME["headlines"] if item["lead_number"] == "runoff"
    )
    return {
        "collected": MEDIA_FRAME["collected"],
        "headlines": MEDIA_FRAME["headlines"],
        "sampled": len(MEDIA_FRAME["headlines"]),
        "led_with_runoff": runoff_first,
        "led_with_first_round": len(MEDIA_FRAME["headlines"]) - runoff_first,
        "published_questions": published,
        "questions_in_coverage": covered,
        "compression_ratio": round(published / covered, 1),
        "report_pages": 197,
        "note": "A cobertura reduz 197 páginas e 41 perguntas publicadas a "
        "quatro resultados. Nenhuma manchete da amostra cita a distância entre "
        "expectativa e voto, a firmeza do voto por candidato ou a geografia da "
        "terceira via.",
    }


def build_payload() -> dict:
    audit = load_audit()
    validate(audit)
    return {
        "metadata": {
            "dossier": "Quaest/Globo 14/08/2026, camada estratégica",
            "registry": "BR-06773/2026",
            "report_pages": 197,
            "plan_source": PLAN,
            "warning": "Toda conta derivada é condicional e reprodutível. "
            "Nenhuma delas é previsão de resultado.",
        },
        "first_round_region": {
            "page": FIRST_ROUND_REGION["page"],
            "moe": FIRST_ROUND_REGION["moe"],
            "values": {
                cut: as_row(values)
                for cut, values in FIRST_ROUND_REGION["values"].items()
            },
        },
        "first_round_income": {
            "page": FIRST_ROUND_INCOME["page"],
            "moe": FIRST_ROUND_INCOME["moe"],
            "values": {
                cut: as_row(values)
                for cut, values in FIRST_ROUND_INCOME["values"].items()
            },
        },
        "third_way_geography": third_way_geography(audit),
        "interest": interest_profile(),
        "vote_firmness": VOTE_FIRMNESS,
        "soft_vote": soft_vote(),
        "single_round": single_round_equation(audit),
        "inevitability_premium": inevitability_premium(audit),
        "rejection_control": rejection_control(audit),
        "profile_region": PROFILE_REGION,
        "profile_income": PROFILE_INCOME,
        "expected_winner": {
            "region": EXPECTED_WINNER_REGION,
            "income": EXPECTED_WINNER_INCOME,
            "positioning": EXPECTED_WINNER_POSITIONING,
        },
        "concerns": {
            "positioning": CONCERNS_POSITIONING,
            "region": CONCERNS_REGION,
            "income": CONCERNS_INCOME,
        },
        "substitution": substitution_by_segment(audit),
        "bolsa_familia": BOLSA_FAMILIA,
        "plan_crosswalk": PLAN_CROSSWALK,
        "media_frame": media_frame(audit),
        "marcal": MARCAL,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    single = payload["single_round"]
    summary = {
        "output": str(args.output.relative_to(ROOT)),
        "points_needed": single["points_needed"],
        "third_way_only_threshold_pct": single["third_way_only_threshold_pct"],
        "soft_vote_route": single["soft_vote_route"],
        "national_inevitability_spread": payload["inevitability_premium"][
            "national_spread"
        ],
        "rejection_recomposed": payload["rejection_control"]["Flávio"],
        "caiado_better_than_flavio": payload["substitution"][
            "caiado_better_than_flavio"
        ],
        "compression_ratio": payload["media_frame"]["compression_ratio"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
