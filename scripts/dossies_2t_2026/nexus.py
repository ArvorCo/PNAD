"""Transcrições conferidas nas figuras e matrizes nativas da 17ª rodada."""

from .extract import nexus_matrix

KEYS = [
    [
        "total",
        "mulheres",
        "homens",
        "16–24",
        "25–40",
        "41–59",
        "60+",
        "fundamental",
        "médio",
        "superior",
        "católica",
        "evangélica",
        "outras religiões",
        "sem religião",
    ],
    [
        "total",
        "até 1 SM",
        "1–2 SM",
        "2–5 SM",
        ">5 SM",
        "PEA formal",
        "PEA informal",
        "desocupados",
        "não PEA",
        "CO/Norte",
        "Nordeste",
        "Sudeste",
        "Sul",
        "capital",
        "RM",
        "interior",
    ],
]
SPECS = {
    "polarizacao": (
        13,
        14,
        [
            "Não polarizados",
            "Lulistas convictos",
            "Lula como alternativa",
            "Bolsonaristas convictos",
            "Bolsonaro como alternativa",
            "Antiambos",
            "NS/NR",
        ],
    ),
    "interesse": (
        8,
        9,
        [
            "Muito interesse",
            "Interesse",
            "Pouco interesse",
            "Nenhum interesse",
            "NS/NR",
        ],
    ),
    "presenca": (
        17,
        18,
        [
            "Decidiu comparecer",
            "Provavelmente comparecerá",
            "Provavelmente não comparecerá",
            "Decidiu não comparecer",
            "NS/NR",
        ],
    ),
    "voto": (40, 41, ["Flávio Bolsonaro", "Lula", "Branco/nulo/nenhum", "NS/NR"]),
    "expectativa": (
        50,
        51,
        ["Acredita que Flávio vencerá", "Acredita que Lula vencerá", "Outro", "NS/NR"],
    ),
    "potencial_lula": (
        63,
        64,
        [
            "Único em quem votaria",
            "Poderia votar",
            "Não votaria",
            "Não conhece",
            "NS/NR",
        ],
    ),
    "potencial_flavio": (
        65,
        66,
        [
            "Único em quem votaria",
            "Poderia votar",
            "Não votaria",
            "Não conhece",
            "NS/NR",
        ],
    ),
    "avaliacao": (78, 79, ["Ótimo", "Bom", "Regular", "Ruim", "Péssimo", "NS/NR"]),
    "aprovacao": (85, 86, ["Aprova", "Desaprova", "NS/NR"]),
}
PROFILE = {
    "sexo": {"mulheres": 53, "homens": 47},
    "idade": {"16–24": 12, "25–40": 31, "41–59": 34, "60+": 24},
    "escolaridade": {"fundamental": 34, "médio": 41, "superior": 25},
    "religiao": {
        "católica": 48,
        "evangélica": 34,
        "outras religiões": 7,
        "sem religião": 11,
    },
    "renda": {"até 1 SM": 19, "1–2 SM": 18, "2–5 SM": 40, ">5 SM": 23},
    "ocupacao": {"PEA formal": 44, "PEA informal": 16, "desocupados": 5, "não PEA": 35},
    "regiao": {"CO/Norte": 16, "Nordeste": 28, "Sudeste": 42, "Sul": 14},
    "municipio": {"capital": 25, "RM": 13, "interior": 62},
}

TITLES = {
    "polarizacao": "Perfis de polarização",
    "interesse": "Interesse nas eleições",
    "presenca": "Comparecimento declarado",
    "voto": "Intenção estimulada",
    "expectativa": "Expectativa de vitória",
    "potencial_lula": "Potencial e rejeição de Lula",
    "potencial_flavio": "Potencial e rejeição de Flávio",
    "avaliacao": "Avaliação do governo",
    "aprovacao": "Aprovação ao trabalho de Lula",
}


def tables():
    output = {}
    for key, (first, second, options) in SPECS.items():
        segments = {}
        for page, keys in zip((first, second), KEYS, strict=True):
            matrix = nexus_matrix(page, len(options))
            if len(matrix["rows"]) != len(keys):
                raise ValueError(f"Página {page}: número de segmentos inesperado")
            for name, row in zip(keys, matrix["rows"], strict=True):
                record = {
                    "responses": dict(zip(options, row["values"], strict=True)),
                    "page": page,
                    "original_label": row["label"],
                }
                if name == "total" and name in segments:
                    if segments[name]["responses"] != record["responses"]:
                        raise ValueError(f"Totais divergentes: {key}")
                else:
                    segments[name] = record
        output[key] = {
            "title": TITLES[key],
            "pages": [first, second],
            "universe": "total da amostra, percentuais dentro de cada segmento",
            "segments": segments,
        }
    return output


def special():
    return {
        "transfer_1t": {
            "page": 25,
            "options": ["Flávio", "Lula", "Branco/nulo", "NS/NR"],
            "rows": {
                "Flávio no 1º turno": [98, 2, 0, 0],
                "Lula no 1º turno": [1, 98, 0, 1],
                "Outras candidaturas no 1º turno": [45, 32, 19, 3],
                "Não compareceu no 1º turno": [49, 41, 6, 3],
            },
            "universe": "voto lembrado de 04/10 dentro da mesma entrevista; bases de cada grupo não publicadas",
        },
        "transfer_detail": {
            "page": 26,
            "options": ["Flávio", "Lula", "Branco/nulo", "NS/NR"],
            "rows": {
                "Zema": [80, 0, 12, 8],
                "Caiado": [55, 27, 11, 7],
                "Cury": [43, 41, 13, 4],
                "Renan Santos": [37, 30, 33, 0],
                "Demais candidaturas": [0, 100, 0, 0],
            },
            "limit": "Zeros correspondem à ausência de barra na figura, não a precisão infinita. Bases não divulgadas; 100% no residual não sustenta generalização nacional.",
        },
        "transfer_2022": {
            "page": 24,
            "rows": {
                "Lula em 2022": [6, 90, 3, 2],
                "Jair Bolsonaro em 2022": [91, 6, 1, 2],
            },
            "limit": "Recordação de voto, sem painel longitudinal e sem bases publicadas; não somar aos fluxos de 2026.",
        },
        "decision": {
            "page": 33,
            "total": [92, 7, 1],
            "labels": ["Não pretende mudar", "Pode mudar", "NS/NR"],
            "cross_page": 34,
            "by_vote": {
                "Flávio": [95, 4, 0],
                "Lula": [95, 5, 0],
                "Branco/nulo": [79, 19, 2],
                "NS/NR": [20, 58, 22],
            },
            "limit": "A barra de Flávio publica 95% firme e 4% pode mudar, sem barra NS/NR. Não completar a soma de 99% com 1% de indecisão inventada; o zero descreve a ausência de barra.",
        },
        "bolsa_familia": {
            "pages": [31, 32],
            "rows": {
                "Há Bolsa Família no domicílio": [23, 68, 4, 6],
                "Não há Bolsa Família": [52, 41, 5, 2],
            },
            "universe": "Pergunta se o respondente ou alguém que mora em sua casa recebe; não se restringe ao titular individual do benefício.",
            "limit": "Bases e pesos dos dois grupos não são publicados. É associação com voto, sem efeito causal identificado do programa; não converter em pontos nacionais.",
        },
        "decision_time": {
            "page": 43,
            "rows": {
                "Antes de 04/10": 83,
                "Depois de 04/10": 8,
                "Pode mudar": 7,
                "NS/NR": 1,
            },
            "limit": "Partes arredondadas somam 99%; p. 42 restringe a base aos 92% decididos, p. 43 reexpressa no total.",
        },
        "second_option": {
            "page": 38,
            "rows": {"Lula": 20, "Flávio": 16, "Branco/nulo": 52, "NS/NR": 12},
            "universe": "os 7% que dizem poder mudar; não são percentuais nacionais",
            "limit": "Não adicionar os 2% de indecisos aos 7%: o cruzamento da p. 34 mostra sobreposição. O texto do filtro cita candidato anterior; as bases efetivas dos caminhos não são abertas.",
        },
        "floors": {
            "page": 39,
            "flavio": [46, 48, 49],
            "lula": [43, 45, 46],
            "labels": ["Piso declarado", "Intenção", "Teto declarado"],
            "limit": "Contas descritivas do instituto com certeza e segunda opção, não intervalos de confiança nem limites da urna.",
        },
        "motivation": {
            "pages": [55, 56, 59],
            "labels": ["Melhor candidato", "Derrotar adversário", "NS/NR"],
            "flavio": [71, 23, 6],
            "lula": [81, 15, 4],
            "universe": "eleitores atuais de cada candidato",
            "reported_national_negative": 18,
        },
        "nonchoice": {
            "page": 57,
            "pool_pct": 7,
            "rows": {
                "Rejeita só Lula": 10,
                "Rejeita só Flávio": 5,
                "Rejeita ambos": 28,
                "Nenhum representa": 35,
                "NS/NR": 22,
            },
        },
        "polarization": {
            "page": 52,
            "rows": {
                "Confortável": 13,
                "Indiferente": 13,
                "Cansado/desconfortável": 38,
                "Discorda da polarização": 23,
                "NS/NR": 13,
            },
            "limit": "Pergunta estimulada introduz a avaliação de analistas e filtra sentimento entre quem concorda; 38% é do total, não dos indecisos.",
        },
        "cluster_vote": {
            "page": 27,
            "rows": {
                "Bolsonaristas convictos": [87, 11, 2, 0],
                "Bolsonaro como alternativa": [82, 11, 7, 0],
                "Antiambos": [37, 50, 13, 1],
                "Não polarizados": [37, 44, 14, 5],
                "Lulistas convictos": [13, 87, 0, 1],
                "Lula como alternativa": [12, 81, 3, 3],
            },
            "limit": "Categorias derivadas das escalas anti-Lula e anti-Bolsonaro/família, não da pergunta de voto; seus nomes não determinam uma escolha. Bases não publicadas.",
        },
        "joint_rejection": {
            "page": 67,
            "rows": {
                "Aceita Flávio, rejeita Lula": 46,
                "Aceita Lula, rejeita Flávio": 43,
                "Rejeita ambos": 4,
                "Aceita ambos": 4,
                "Não conhece um ou os dois": 2,
                "NS/NR": 1,
            },
            "limit": "Aceita = exclusivo + poderia votar. Não é intenção atual; os 4% que aceitam ambos não são necessariamente indecisos.",
        },
        "government_vote": {
            "page": 74,
            "rows": {
                "Ótimo/bom": [2, 95, 1, 2],
                "Regular": [24, 59, 11, 5],
                "Ruim/péssimo": [93, 2, 5, 0],
            },
        },
        "approval_vote": {
            "page": 82,
            "rows": {"Aprova": [3, 93, 1, 3], "Desaprova": [91, 3, 6, 1]},
        },
        "problems": {
            "page": 88,
            "cross_page": 90,
            "options": ["Primeira menção", "Segunda menção", "Duas menções"],
            "rows": {
                "Segurança pública": [19, 14, 33],
                "Saúde": [12, 17, 29],
                "Corrupção": [13, 5, 18],
                "Educação": [6, 10, 16],
                "Classe política": [7, 7, 14],
                "Inflação/custo de vida": [6, 6, 12],
                "Crescimento econômico": [6, 4, 10],
                "Desemprego": [4, 5, 9],
                "Impostos": [6, 3, 9],
                "Desigualdade/pobreza": [5, 3, 8],
            },
            "by_vote": {
                "Segurança pública": [34, 32],
                "Saúde": [26, 31],
                "Corrupção": [24, 12],
                "Educação": [12, 20],
                "Inflação/custo de vida": [14, 9],
                "Crescimento econômico": [15, 6],
                "Impostos": [14, 4],
            },
            "limit": "Duas respostas espontâneas por entrevistado. Menções não formam partição de 100%; não medir importância causal para o voto. Cruzamento: Flávio, Lula.",
        },
        "economy": {
            "current": {
                "page": 92,
                "country": [17, 31, 51, 2],
                "personal": [34, 45, 20, 1],
                "labels": ["Ótima/boa", "Regular", "Ruim/péssima", "NS/NR"],
            },
            "past": {
                "page": 94,
                "country": [38, 13, 44, 5],
                "personal": [43, 21, 32, 4],
                "labels": ["Melhor que governo anterior", "Igual", "Pior", "NS/NR"],
            },
            "future": {
                "page": 96,
                "country": [54, 17, 12, 16],
                "personal": [51, 29, 7, 13],
                "labels": ["Melhorará", "Igual", "Piorará", "NS/NR"],
                "previous_country": [46, 20, 19, 15],
                "previous_date": "28/09/2026",
            },
            "current_vote": {
                "page": 93,
                "country": {
                    "Ótima/boa": [3, 96, 1, 0],
                    "Regular": [25, 69, 3, 3],
                    "Ruim/péssima": [78, 14, 7, 2],
                },
                "personal": {
                    "Ótima/boa": [31, 64, 4, 1],
                    "Regular": [53, 39, 5, 2],
                    "Ruim/péssima": [63, 28, 4, 6],
                },
            },
            "future_vote": {
                "page": 97,
                "country": {
                    "Melhorará": [52, 43, 2, 2],
                    "Igual": [38, 57, 5, 1],
                    "Piorará": [48, 34, 15, 2],
                },
            },
        },
    }
