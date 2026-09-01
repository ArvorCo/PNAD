#!/usr/bin/env python3
"""Segunda camada de auditoria do Datafolha BR-04496/2026.

A primeira auditoria (scripts/datafolha-082026-audit.py) tratou do placar, da
reponderacao por renda, do territorio e das manchetes. Esta camada le o anexo
inteiro de tabelas cruzadas (scripts/datafolha-082026-cruzamentos.py), soma a
ele as duas paginas de divulgacao que ninguem cita, o questionario aplicado e
o registro no TSE, e mede o que o relatorio coletou e nao publicou. A estrela
da auditoria continua sendo a reponderacao por renda, em
scripts/datafolha-082026-audit.py e scripts/datafolha-082026-historico-renda.py.

Uso:
  python3 scripts/datafolha-082026-cruzamentos.py
  python3 scripts/datafolha-082026-aprofundamento.py

Saidas:
  analysis/datafolha_082026/aprofundamento.json
  docs/assets/datafolha_082026_fundo.json
  docs/assets/datafolha_082026_fundo.js
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
ASSETS = ROOT / "docs" / "assets"
CROSSTABS = ANALYSIS / "cruzamentos.json"

OUT_JSON = ANALYSIS / "aprofundamento.json"
OUT_SITE_JSON = ASSETS / "datafolha_082026_fundo.json"
OUT_SITE_JS = ASSETS / "datafolha_082026_fundo.js"

SAMPLE = 2058

# ---------------------------------------------------------------------------
# As duas paginas de divulgacao que a cobertura ignora. Os percentuais sao os
# publicados; a linha de bases do relatorio e reproduzida como consta, sem
# afirmacao sobre ser contagem de campo ou base ponderada.
DECK_DECISION = {
    "page": 12,
    "question": "Em relacao ao seu voto para presidente, voce diria que esta totalmente decidido ou seu voto ainda pode mudar?",
    "base_label": "Entrevistados que citaram alguma opcao de voto na estimulada",
    "total": {"decidido": 72, "pode_mudar": 27, "nao_sabe": 1, "base": 1980},
    "por_candidato": {
        "Lula (PT)": {
            "decidido": 82,
            "pode_mudar": 18,
            "nao_sabe": 0,
            "base": 860,
            "moe": 3,
        },
        "Flavio Bolsonaro (PL)": {
            "decidido": 78,
            "pode_mudar": 21,
            "nao_sabe": 1,
            "base": 612,
            "moe": 4,
        },
        "Ronaldo Caiado (PSD)": {
            "decidido": 57,
            "pode_mudar": 42,
            "nao_sabe": 1,
            "base": 111,
            "moe": 9,
        },
        "Renan Santos (MISSAO)": {
            "decidido": 54,
            "pode_mudar": 46,
            "nao_sabe": 0,
            "base": 74,
            "moe": 12,
        },
        "Zema (NOVO)": {
            "decidido": 29,
            "pode_mudar": 69,
            "nao_sabe": 2,
            "base": 58,
            "moe": 13,
        },
    },
}

DECK_MOTIVATION = {
    "page": 13,
    "question": "E voce votaria em ___ porque ele(a) tem as melhores propostas e e o(a) mais preparado(a) ou para evitar que outro(a) candidato seja eleito?",
    "base_label": "Entrevistados que citaram algum candidato na estimulada",
    "total": {
        "propostas": 61,
        "evitar": 30,
        "outras": 7,
        "nao_sabe": 2,
        "base": 1836,
    },
    "por_candidato": {
        "Renan Santos (MISSAO)": {
            "propostas": 73,
            "evitar": 24,
            "outras": 1,
            "nao_sabe": 2,
            "base": 74,
        },
        "Lula (PT)": {
            "propostas": 68,
            "evitar": 23,
            "outras": 8,
            "nao_sabe": 1,
            "base": 860,
        },
        "Ronaldo Caiado (PSD)": {
            "propostas": 60,
            "evitar": 31,
            "outras": 8,
            "nao_sabe": 1,
            "base": 111,
        },
        "Zema (NOVO)": {
            "propostas": 57,
            "evitar": 37,
            "outras": 5,
            "nao_sabe": 1,
            "base": 58,
        },
        "Flavio Bolsonaro (PL)": {
            "propostas": 56,
            "evitar": 35,
            "outras": 7,
            "nao_sabe": 2,
            "base": 612,
        },
    },
}

# Base ponderada das mesmas perguntas no anexo, paginas 26 e 27 de 29.
WEIGHTED_DECISION_BASE = 1980

# Serie do primeiro turno estimulado, pagina 9 (situacao sem Marcal).
FIRST_ROUND_SERIES = {
    "page": 9,
    "waves": [
        "03-05/03/26",
        "07-09/04/26",
        "12-13/05/26",
        "20-21/05/26",
        "17-18/06/26",
        "22-23/07/26",
        "18-19/08/26",
    ],
    "series": {
        "Lula (PT)": [39, 39, 38, 40, 41, 40, 39],
        "Flavio Bolsonaro (PL)": [33, 35, 35, 31, 31, 32, 33],
        "Ronaldo Caiado (PSD)": [4, 5, 3, 4, 3, 4, 5],
        "Renan Santos (MISSAO)": [3, 2, 2, 3, 3, 3, 4],
        "Zema (NOVO)": [5, 4, 3, 3, 2, 3, 3],
        "Branco/nulo/nenhum": [12, 10, 9, 9, 7, 8, 6],
        "Indecisos": [3, 4, 3, 3, 4, 3, 4],
    },
}

# Serie do segundo turno Lula x Flavio, pagina 15.
RUNOFF_SERIES = {
    "page": 15,
    "waves": [
        "10-11/06/25",
        "29-30/07/25",
        "02-04/12/25",
        "03-05/03/26",
        "07-09/04/26",
        "12-13/05/26",
        "20-21/05/26",
        "17-18/06/26",
        "22-23/07/26",
        "18-19/08/26",
    ],
    "series": {
        "Lula (PT)": [47, 48, 51, 46, 45, 45, 47, 47, 48, 47],
        "Flavio Bolsonaro (PL)": [38, 37, 36, 43, 46, 45, 43, 43, 43, 43],
        "Branco/nulo/nenhum": [14, 13, 12, 10, 8, 9, 9, 8, 9, 9],
        "Indecisos": [1, 1, 1, 1, 1, 1, 2, 1, 1, 2],
    },
}

# Registro BR-04496/2026, campo "Plano amostral e ponderacao".
REGISTRY_TARGETS = {
    "documento": "DatafolhaRegistroTSE082026.pdf, pagina 2",
    "genero": {"Masculino": 47, "Feminino": 53},
    "idade": {"16-24": 12, "25-34": 19, "35-44": 20, "45-59": 25, "60+": 24},
    "escolaridade": {"Ate medio": 76, "Superior": 24},
    "renda": {"Ate 2 SM": 49, "Mais de 2 SM": 47, "NS/recusa": 4},
    "fontes_declaradas": "TSE, IBGE (Censo 2022, PNADC-A 2024 e Estimativa populacional 2025)",
    "fator_de_ponderacao_declarado": "O fator previsto para ponderacao e 1 (resultados obtidos em campo).",
}

ACHIEVED_PROFILE = {
    "documento": "Relatorio completo, anexo, pagina 5 de 29 (p.27 do PDF)",
    "genero": {"Masculino": 48, "Feminino": 52},
    "idade": {"16-24": 13, "25-34": 19, "35-44": 20, "45-59": 25, "60+": 24},
    "escolaridade": {"Ate medio": 75, "Superior": 25},
    "renda": {"Ate 2 SM": 50, "Mais de 2 SM": 46, "NS/recusa": 4},
}

# Cartao de renda do questionario aplicado, pagina 5.
INCOME_CARD = {
    "documento": "DatafolhaQuestionario082026.pdf, pagina 5",
    "faixas_nominais": [
        "de R$ 1,00 ate R$ 1.621,00",
        "de R$ 1.622,00 ate R$ 3.242,00",
        "de R$ 3.243,00 ate R$ 4.863,00",
        "de R$ 4.864,00 ate R$ 8.105,00",
        "de R$ 8.106,00 ate R$ 16.210,00",
        "de R$ 16.211,00 ate R$ 32.420,00",
        "de R$ 32.421,00 ate R$ 81.050,00",
        "R$ 81.051,00 ou mais",
    ],
    "salario_minimo_implicito_brl": 1621.00,
    "ano_do_salario_minimo": 2026,
    "teto_de_dois_salarios_no_cartao_brl": 3242.00,
    "teto_de_dois_salarios_na_pnadc_2024_brl": 2824.00,
    "opcao_sem_renda": "96 Nao tem renda, presente no cartao e ausente do perfil publicado",
}

# Perguntas do questionario aplicado que nao aparecem em nenhuma tabela.
COLLECTED_NOT_PUBLISHED = [
    {
        "id": "VOTOPRES22",
        "pergunta": "Em quem voce votou no segundo turno da eleicao para presidente em 2022?",
        "pagina_questionario": 3,
        "por_que_importa": "E a unica variavel da pesquisa que pode ser conferida contra um resultado real. Se a amostra lembra 2022 fora da proporcao oficial, o desvio fica visivel antes de qualquer ponderacao.",
        "peso": "alto",
    },
    {
        "id": "POSICAO POLITICA",
        "pergunta": "Escala de esquerda a direita, de 1 a 7.",
        "pagina_questionario": 3,
        "por_que_importa": "O relatorio publica so a escala de 1 a 5 entre bolsonarista e petista. A escala ideologica de sete pontos foi coletada na mesma entrevista e nao aparece.",
        "peso": "alto",
    },
    {
        "id": "P.2",
        "pergunta": "Ha chance de outros paises agirem na eleicao brasileira, e isso e um problema?",
        "pagina_questionario": 3,
        "por_que_importa": "Pergunta de soberania eleitoral aplicada a 2.058 eleitores e ausente das 51 paginas do relatorio.",
        "peso": "alto",
    },
    {
        "id": "P.3",
        "pergunta": "Se o voto NAO fosse obrigatorio, voce iria votar?",
        "pagina_questionario": 3,
        "por_que_importa": "Mede intencao de comparecimento. Sem ela, todo percentual do relatorio supoe que o eleitorado que responde e o eleitorado que vota.",
        "peso": "alto",
    },
    {
        "id": "P.4",
        "pergunta": "Qual seu grau de interesse por politica: grande, medio, pequeno ou nenhum?",
        "pagina_questionario": 3,
        "por_que_importa": "Separa opiniao formada de resposta de cortesia. E o filtro classico para ler indeciso e branco/nulo.",
        "peso": "medio",
    },
    {
        "id": "RELIGIAO 2 e 3",
        "pergunta": "Qual o nome da igreja que voce frequenta?",
        "pagina_questionario": 5,
        "por_que_importa": "O questionario lista dezenas de denominacoes, de Assembleia de Deus a IURD. O relatorio publica uma unica coluna, Evangelica.",
        "peso": "medio",
    },
    {
        "id": "ESCOLA_ENTREVISTADO",
        "pergunta": "Ate que ano da escola voce estudou? Oito niveis, de analfabeto a pos-graduacao.",
        "pagina_questionario": 5,
        "por_que_importa": "Oito niveis coletados, tres publicados. Pos-graduacao e analfabetismo somem dentro de Superior e Fundamental.",
        "peso": "medio",
    },
    {
        "id": "AUTORIZACAO",
        "pergunta": "Voce autoriza que o Datafolha armazene seu nome e telefone para pesquisas futuras?",
        "pagina_questionario": 6,
        "por_que_importa": "Constroi painel de recontato. A taxa de aceite nunca e publicada e afeta a comparabilidade entre ondas.",
        "peso": "baixo",
    },
]

QUESTIONNAIRE_NOTES = [
    {
        "titulo": "Quem vota em outra cidade e dispensado",
        "trecho": "CIDADE ONDE VOTA: Voce vota aqui na cidade de ___? 1. Sim (PROSSIGA) 2. Nao (ENCERRE)",
        "pagina": 1,
        "leitura": "A abordagem e em ponto de fluxo. Em regiao metropolitana, boa parte do fluxo e de quem trabalha na capital e vota na periferia. O filtro e correto para o desenho municipal e, ao mesmo tempo, remove sistematicamente o eleitor pendular do ponto onde ele foi encontrado.",
    },
    {
        "titulo": "O genero e anotado, nao perguntado",
        "trecho": "GENERO_PRESENCIAL COTA: Pesquisador anote o genero do entrevistado.",
        "pagina": 1,
        "leitura": "Uma das duas variaveis de cota e observada pelo entrevistador. Isso e pratica comum de campo e vale registrar, porque a cota que fecha a amostra nao passa pela boca do entrevistado.",
    },
    {
        "titulo": "A escala politica tem dois nomes proprios nas pontas",
        "trecho": "Considerando uma escala de 1 a 5, onde 1 e bolsonarista e 5 petista, em qual numero voce se encaixa?",
        "pagina": 3,
        "leitura": "O instrumento pede que o eleitor se localize entre duas pessoas. Quem e liberal, quem e socialista e quem e conservador sem ser bolsonarista caem todos no ponto 3 ou no 'nenhum'. O relatorio junta esses dois grupos diferentes em 'nao alinhados' e nunca publica a escala ideologica de sete pontos que foi perguntada logo em seguida.",
    },
    {
        "titulo": "A rejeicao e provocada ate acabar",
        "trecho": "REJEI: Em quais desses candidatos voce nao votaria de jeito nenhum? (ESTIMULADA E MULTIPLA, EXPLORE: E qual mais?)",
        "pagina": 2,
        "leitura": "A pergunta e multipla, com cartao e com insistencia. Somadas, as rejeicoes dao 223% da amostra: cada eleitor rejeita 2,2 nomes em media. E uma medida de quanto o entrevistado responde, nao so de quanto ele rejeita.",
    },
    {
        "titulo": "Marcal esta no cartao da rejeicao e fora do cenario principal",
        "trecho": "REJEI usa o CARTAO 1A, que inclui Pablo Marcal; a situacao B, divulgada como cenario principal, usa o CARTAO 1B, que nao o inclui.",
        "pagina": 1,
        "leitura": "Marcal aparece com 22% de rejeicao, terceiro lugar do ranking, em um cenario de voto do qual ele foi retirado. Os dois numeros sao corretos e vem de cartoes diferentes; a leitura conjunta so funciona se essa diferenca for dita.",
    },
]

# ---------------------------------------------------------------------------


def load_crosstabs() -> dict[str, object]:
    if not CROSSTABS.exists():
        raise SystemExit(
            "cruzamentos.json ausente. Rode antes: "
            "python3 scripts/datafolha-082026-cruzamentos.py"
        )
    return json.loads(CROSSTABS.read_text(encoding="utf-8"))


def merge(table: dict[str, object]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    bases: dict[str, int] = {}
    for block in table["blocks"].values():
        for label, values in block["rows"].items():
            for column, value in values.items():
                rows.setdefault(column, {})[label] = value
        bases.update(block["base"])
    return rows, bases


DIMENSIONS = {
    "Genero": ["Masculino", "Feminino"],
    "Idade": ["16-24", "25-34", "35-44", "45-59", "60+"],
    "Escolaridade": ["Fundamental", "Medio", "Superior"],
    "Renda familiar": ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"],
    "Ocupacao": ["PEA", "Nao PEA"],
    "Cor": ["Branca", "Preta", "Parda"],
    "Religiao": ["Catolica", "Evangelica"],
    "Regiao": ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"],
    "Natureza do municipio": ["Regiao metropolitana", "Interior"],
    "Identificacao politica": ["Bolsonaristas", "Nao alinhados", "Petistas"],
    "Partido de preferencia": ["PT", "PL", "Outro partido", "Sem partido"],
}


def coverage(bases: dict[str, int]) -> list[dict[str, object]]:
    out = []
    for name, categories in DIMENSIONS.items():
        covered = sum(bases[category] for category in categories)
        out.append(
            {
                "dimensao": name,
                "categorias_publicadas": len(categories),
                "base_coberta": covered,
                "base_total": bases["Total"],
                "cobertura_pct": round(100 * covered / bases["Total"], 1),
                "eleitores_sem_coluna": bases["Total"] - covered,
                "particao_fechada": abs(bases["Total"] - covered) <= 2,
            }
        )
    return sorted(out, key=lambda item: item["cobertura_pct"])


def open_market(crosstabs: dict[str, object]) -> dict[str, object]:
    """Quanto do eleitorado o proprio Datafolha declara em aberto."""
    first, _ = merge(crosstabs["estimulada_b"])
    shares = first["Total"]
    movable_named = 0.0
    detail = []
    for candidate, row in DECK_DECISION["por_candidato"].items():
        share = shares[candidate]
        points = share * row["pode_mudar"] / 100
        movable_named += points
        detail.append(
            {
                "candidato": candidate,
                "voto_pct": share,
                "pode_mudar_pct": row["pode_mudar"],
                "pontos_do_eleitorado": round(points, 2),
                "base": row["base"],
            }
        )

    total_movable = (
        DECK_DECISION["total"]["pode_mudar"] * WEIGHTED_DECISION_BASE / SAMPLE
    )
    undecided = shares["Indecisos"]
    residual = total_movable - movable_named
    return {
        "detalhe_por_candidato": sorted(
            detail, key=lambda item: -item["pontos_do_eleitorado"]
        ),
        "pontos_moveis_nos_cinco_maiores": round(movable_named, 2),
        "pontos_moveis_no_total": round(total_movable, 2),
        "pontos_moveis_nos_demais": round(residual, 2),
        "indecisos_pct": undecided,
        "mercado_aberto_pct": round(total_movable + undecided, 2),
        "voto_cristalizado_pct": round(100 - total_movable - undecided, 2),
        "gap_publicado_1turno": shares["Lula (PT)"] - shares["Flavio Bolsonaro (PL)"],
        "leitura": (
            "Datafolha pergunta a todo eleitor que citou um voto se ele pode mudar. "
            "Somando a resposta com os indecisos, o proprio instituto mede um "
            "eleitorado em aberto muitas vezes maior do que a diferenca do placar."
        ),
    }


def noise_floor(crosstabs: dict[str, object]) -> dict[str, object]:
    """Piso de rejeicao entre nomes sem traccao eleitoral."""
    rejection, bases = merge(crosstabs["rejeicao"])
    first, _ = merge(crosstabs["estimulada_b"])

    unknown = [
        name
        for name, value in first["Total"].items()
        if name in rejection["Total"]
        and value is not None
        and value <= 1
        and name not in {"Branco/nulo/nenhum", "Indecisos"}
    ]
    majors = [
        "Flavio Bolsonaro (PL)",
        "Lula (PT)",
        "Pablo Marcal (PRTB)",
        "Zema (NOVO)",
        "Renan Santos (MISSAO)",
        "Ronaldo Caiado (PSD)",
        "Augusto Cury (AVANTE)",
    ]

    by_segment = []
    for column in rejection:
        values = [
            rejection[column][name]
            for name in unknown
            if rejection[column][name] is not None
        ]
        floor = sum(values) / len(values)
        entry = {
            "recorte": column,
            "piso_pct": round(floor, 2),
            "base": bases[column],
        }
        for name in majors:
            value = rejection[column][name]
            entry[name] = None if value is None else round(value - floor, 2)
        by_segment.append(entry)

    total_floor = next(
        item["piso_pct"] for item in by_segment if item["recorte"] == "Total"
    )
    total_sum = sum(
        value
        for name, value in rejection["Total"].items()
        if value is not None
        and name not in {"Nao rejeita nenhum", "Rejeita todos", "Nao sabe"}
    )

    return {
        "nomes_sem_traccao": unknown,
        "criterio": "candidatos com 1% ou menos na estimulada situacao B",
        "piso_nacional_pct": total_floor,
        "rejeicoes_por_entrevistado": round(total_sum / 100, 2),
        "soma_das_rejeicoes_pct": total_sum,
        "dentro_de_cinco_pontos_do_piso": sum(
            1
            for name, value in rejection["Total"].items()
            if value is not None
            and name not in {"Nao rejeita nenhum", "Rejeita todos", "Nao sabe"}
            and value - total_floor <= 5
        ),
        "abaixo_do_piso": [
            name
            for name in majors
            if rejection["Total"][name] is not None
            and rejection["Total"][name] < total_floor
        ],
        "por_recorte": by_segment,
        "leitura": (
            "Seis candidaturas que quase ninguem sabe nomear recebem entre 8% e "
            "13% de rejeicao. Esse e o piso de ruido do instrumento: o quanto uma "
            "pergunta multipla e insistente produz de recusa contra um nome "
            "desconhecido. Subtrair o piso nao corrige a pesquisa; mostra quanto "
            "de cada rejeicao publicada e opiniao e quanto e estilo de resposta."
        ),
    }


def gap_analysis(crosstabs: dict[str, object]) -> dict[str, object]:
    """O vao: desaprovacao do governo menos voto no adversario, no mesmo recorte."""
    approval, bases = merge(crosstabs["aprovacao"])
    runoff, _ = merge(crosstabs["turno2_flavio"])

    rows = []
    for column in approval:
        disapprove = approval[column]["Desaprova"]
        opposition = runoff[column]["Flavio Bolsonaro (PL)"]
        non_choice = (runoff[column]["Branco/nulo/nenhum"] or 0) + (
            runoff[column]["Indecisos"] or 0
        )
        rows.append(
            {
                "recorte": column,
                "desaprova_pct": disapprove,
                "voto_oposicao_2turno_pct": opposition,
                "vao_pp": round(disapprove - opposition, 2),
                "nao_escolha_pct": non_choice,
                "base": bases[column],
                "eleitores_no_vao": round(
                    bases[column] * (disapprove - opposition) / 100, 1
                ),
            }
        )

    closed = {
        name: categories
        for name, categories in DIMENSIONS.items()
        if abs(bases["Total"] - sum(bases[category] for category in categories)) <= 2
    }
    national = {}
    for name, categories in closed.items():
        total = sum(
            bases[category]
            * (
                approval[category]["Desaprova"]
                - runoff[category]["Flavio Bolsonaro (PL)"]
            )
            for category in categories
        )
        national[name] = round(total / bases["Total"], 2)

    return {
        "definicao": (
            "Desaprovacao do governo menos voto no adversario, dentro do mesmo "
            "recorte e do mesmo relatorio. E teto enderecavel, nao previsao: "
            "desaprovar nao e o mesmo que estar disponivel."
        ),
        "vao_nacional_pp": round(
            approval["Total"]["Desaprova"] - runoff["Total"]["Flavio Bolsonaro (PL)"], 2
        ),
        "vao_nacional_por_particao_fechada": national,
        "por_recorte": sorted(rows, key=lambda item: -item["vao_pp"]),
    }


def substitution(crosstabs: dict[str, object]) -> dict[str, object]:
    """Quatro segundos turnos na mesma amostra: substituicao medida."""
    scenarios = {
        "Flavio Bolsonaro": ("turno2_flavio", "Flavio Bolsonaro (PL)"),
        "Ronaldo Caiado": ("turno2_caiado", "Ronaldo Caiado (PSD)"),
        "Zema": ("turno2_zema", "Zema (NOVO)"),
        "Renan Santos": ("turno2_renan", "Renan Santos (MISSAO)"),
    }
    rows = []
    per_segment: dict[str, dict[str, int]] = {}
    for name, (key, row) in scenarios.items():
        table, bases = merge(crosstabs[key])
        rows.append(
            {
                "adversario": name,
                "lula_pct": table["Total"]["Lula (PT)"],
                "oposicao_pct": table["Total"][row],
                "branco_nulo_pct": table["Total"]["Branco/nulo/nenhum"],
                "indecisos_pct": table["Total"]["Indecisos"],
            }
        )
        for column in table:
            per_segment.setdefault(column, {})[name] = table[column][row]

    lula = [item["lula_pct"] for item in rows]
    opposition = [item["oposicao_pct"] for item in rows]
    blank = [item["branco_nulo_pct"] for item in rows]

    beats_flavio = [
        {
            "recorte": column,
            "flavio": values["Flavio Bolsonaro"],
            "melhor_substituto": max(
                (name for name in values if name != "Flavio Bolsonaro"),
                key=lambda name: values[name],
            ),
            "voto_do_substituto": max(
                values[name] for name in values if name != "Flavio Bolsonaro"
            ),
        }
        for column, values in per_segment.items()
    ]
    beats_flavio = [
        dict(item, vantagem_pp=item["voto_do_substituto"] - item["flavio"])
        for item in beats_flavio
        if item["voto_do_substituto"] > item["flavio"]
    ]

    return {
        "cenarios": rows,
        "amplitude_lula_pp": max(lula) - min(lula),
        "amplitude_oposicao_pp": max(opposition) - min(opposition),
        "amplitude_branco_nulo_pp": max(blank) - min(blank),
        "por_recorte": per_segment,
        "contraponto": sorted(beats_flavio, key=lambda item: -item["vantagem_pp"]),
        "leitura": (
            "O instituto rodou quatro segundos turnos sobre a mesma amostra. "
            "Lula varia um ponto entre eles. A variacao inteira fica no "
            "desafiante e no branco/nulo. E a medida mais direta de voto util "
            "que existe em pesquisa brasileira publicada, e ela corta nos dois "
            "sentidos: Flavio e o adversario mais forte no agregado e, ao mesmo "
            "tempo, o que perde para os proprios substitutos entre nao alinhados."
        ),
    }


def conversion(crosstabs: dict[str, object]) -> dict[str, object]:
    """Quanto cada campo converte do proprio polo."""
    approval, bases = merge(crosstabs["aprovacao"])
    first, _ = merge(crosstabs["estimulada_b"])
    runoff, _ = merge(crosstabs["turno2_flavio"])

    rows = []
    for column in approval:
        approve = approval[column]["Aprova"]
        disapprove = approval[column]["Desaprova"]
        rows.append(
            {
                "recorte": column,
                "base": bases[column],
                "lula_1turno_sobre_aprovacao": (
                    round(100 * first[column]["Lula (PT)"] / approve, 1)
                    if approve
                    else None
                ),
                "flavio_1turno_sobre_desaprovacao": (
                    round(100 * first[column]["Flavio Bolsonaro (PL)"] / disapprove, 1)
                    if disapprove
                    else None
                ),
                "lula_2turno_sobre_aprovacao": (
                    round(100 * runoff[column]["Lula (PT)"] / approve, 1)
                    if approve
                    else None
                ),
                "flavio_2turno_sobre_desaprovacao": (
                    round(100 * runoff[column]["Flavio Bolsonaro (PL)"] / disapprove, 1)
                    if disapprove
                    else None
                ),
            }
        )
    return {
        "definicao": (
            "Voto do candidato dividido pelo tamanho do proprio polo no mesmo "
            "recorte: aprovacao do governo para Lula, desaprovacao para a oposicao."
        ),
        "por_recorte": rows,
    }


def frozen_series() -> dict[str, object]:
    runoff = RUNOFF_SERIES["series"]
    first = FIRST_ROUND_SERIES["series"]
    waves = RUNOFF_SERIES["waves"]

    last_four = slice(-4, None)
    gaps_1t = [
        first["Lula (PT)"][index] - first["Flavio Bolsonaro (PL)"][index]
        for index in range(len(FIRST_ROUND_SERIES["waves"]))
    ]
    gaps_2t = [
        runoff["Lula (PT)"][index] - runoff["Flavio Bolsonaro (PL)"][index]
        for index in range(len(waves))
    ]
    return {
        "segundo_turno": {
            "ondas": waves[last_four],
            "lula": runoff["Lula (PT)"][last_four],
            "flavio": runoff["Flavio Bolsonaro (PL)"][last_four],
            "gap": gaps_2t[-4:],
            "flavio_parado_em": runoff["Flavio Bolsonaro (PL)"][-1],
            "ondas_sem_variacao_do_desafiante": sum(
                1
                for value in runoff["Flavio Bolsonaro (PL)"][-4:]
                if value == runoff["Flavio Bolsonaro (PL)"][-1]
            ),
        },
        "primeiro_turno": {
            "ondas": FIRST_ROUND_SERIES["waves"],
            "lula": first["Lula (PT)"],
            "flavio": first["Flavio Bolsonaro (PL)"],
            "gap": gaps_1t,
            "pico_do_desafiante": max(first["Flavio Bolsonaro (PL)"]),
            "atual_do_desafiante": first["Flavio Bolsonaro (PL)"][-1],
            "queda_do_incumbente_pp": first["Lula (PT)"][4] - first["Lula (PT)"][-1],
            "branco_nulo_inicio": first["Branco/nulo/nenhum"][0],
            "branco_nulo_fim": first["Branco/nulo/nenhum"][-1],
        },
        "para_onde_foi_o_branco_nulo": {
            "queda_do_branco_nulo_pp": first["Branco/nulo/nenhum"][0]
            - first["Branco/nulo/nenhum"][-1],
            "variacao_do_desafiante_pp": first["Flavio Bolsonaro (PL)"][-1]
            - first["Flavio Bolsonaro (PL)"][0],
            "variacao_caiado_pp": first["Ronaldo Caiado (PSD)"][-1]
            - first["Ronaldo Caiado (PSD)"][0],
            "variacao_renan_pp": first["Renan Santos (MISSAO)"][-1]
            - first["Renan Santos (MISSAO)"][0],
            "variacao_zema_pp": first["Zema (NOVO)"][-1] - first["Zema (NOVO)"][0],
            "variacao_lula_pp": first["Lula (PT)"][-1] - first["Lula (PT)"][0],
        },
        "leitura": (
            "A diferenca do primeiro turno caiu de dez para seis pontos entre "
            "junho e agosto. No mesmo intervalo, o segundo turno nao se moveu: o "
            "desafiante marca 43 em quatro ondas seguidas. A convergencia do "
            "primeiro turno e voto util que o segundo turno ja contava."
        ),
    }


def base_consolidation(crosstabs: dict[str, object]) -> dict[str, object]:
    """Quanto cada candidato de oposicao tira da base e quanto tira de fora."""
    scenarios = {
        "Flavio Bolsonaro": ("turno2_flavio", "Flavio Bolsonaro (PL)"),
        "Ronaldo Caiado": ("turno2_caiado", "Ronaldo Caiado (PSD)"),
        "Zema": ("turno2_zema", "Zema (NOVO)"),
        "Renan Santos": ("turno2_renan", "Renan Santos (MISSAO)"),
    }
    rows = []
    for name, (key, row) in scenarios.items():
        table, bases = merge(crosstabs[key])
        base = table["Bolsonaristas"][row]
        floating = table["Nao alinhados"][row]
        reservoir = (table["Nao alinhados"]["Branco/nulo/nenhum"] or 0) + (
            table["Nao alinhados"]["Indecisos"] or 0
        )
        rows.append(
            {
                "candidato": name,
                "na_base_bolsonarista_pct": base,
                "entre_nao_alinhados_pct": floating,
                "abismo_pp": base - floating,
                "nao_escolha_dos_nao_alinhados_pct": reservoir,
                "nacional_reconstruido_pct": round(
                    (
                        base * bases["Bolsonaristas"]
                        + floating * bases["Nao alinhados"]
                        + table["Petistas"][row] * bases["Petistas"]
                    )
                    / (
                        bases["Bolsonaristas"]
                        + bases["Nao alinhados"]
                        + bases["Petistas"]
                    ),
                    2,
                ),
            }
        )
    naligned_share = None
    table, bases = merge(crosstabs["turno2_flavio"])
    naligned_share = round(100 * bases["Nao alinhados"] / bases["Total"], 1)
    return {
        "linhas": rows,
        "peso_dos_nao_alinhados_pct": naligned_share,
        "reservatorio_nacional_pp": round(
            naligned_share
            * (
                (table["Nao alinhados"]["Branco/nulo/nenhum"] or 0)
                + (table["Nao alinhados"]["Indecisos"] or 0)
            )
            / 100,
            2,
        ),
        "leitura": (
            "O desafiante ja tem 90% da propria base. Nao ha ponto a extrair ali. "
            "Todo crescimento restante esta entre nao alinhados, onde ele marca 38 "
            "e onde 30% nao escolhem ninguem."
        ),
    }


def main() -> None:
    crosstabs = load_crosstabs()["tabelas"]
    _, bases = merge(crosstabs["turno2_flavio"])

    payload = {
        "fonte": {
            "registro": "BR-04496/2026",
            "relatorio": "DatafolhaRelatorio082026.pdf, 51 paginas",
            "questionario": "DatafolhaQuestionario082026.pdf, 8 paginas",
            "registro_tse": "DatafolhaRegistroTSE082026.pdf, 3 paginas",
            "anexo_de_cruzamentos": "29 paginas, 14 tabelas, 11 recortes",
        },
        "mercado_aberto": open_market(crosstabs),
        "piso_de_ruido": noise_floor(crosstabs),
        "vao": gap_analysis(crosstabs),
        "substituicao": substitution(crosstabs),
        "conversao": conversion(crosstabs),
        "serie_congelada": frozen_series(),
        "consolidacao_de_base": base_consolidation(crosstabs),
        "cobertura_dos_recortes": coverage(bases),
        "cotas_declaradas": {
            "registro": REGISTRY_TARGETS,
            "perfil_obtido": ACHIEVED_PROFILE,
            "desvios": {
                dimension: {
                    category: ACHIEVED_PROFILE[dimension][category] - value
                    for category, value in REGISTRY_TARGETS[dimension].items()
                }
                for dimension in ("genero", "idade", "escolaridade", "renda")
            },
        },
        "cartao_de_renda": INCOME_CARD,
        "coletado_e_nao_publicado": COLLECTED_NOT_PUBLISHED,
        "notas_do_questionario": QUESTIONNAIRE_NOTES,
        "paginas_da_divulgacao": {
            "decisao": DECK_DECISION,
            "motivacao": DECK_MOTIVATION,
        },
        "series": {
            "primeiro_turno": FIRST_ROUND_SERIES,
            "segundo_turno": RUNOFF_SERIES,
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text + "\n", encoding="utf-8")
    OUT_SITE_JSON.write_text(text + "\n", encoding="utf-8")
    OUT_SITE_JS.write_text(
        "window.DATAFOLHA_082026_FUNDO = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    market = payload["mercado_aberto"]
    print(
        f"mercado aberto: {market['mercado_aberto_pct']} pontos contra gap de {market['gap_publicado_1turno']}"
    )
    print(f"piso de ruido nacional: {payload['piso_de_ruido']['piso_nacional_pct']}%")
    print(f"vao nacional: {payload['vao']['vao_nacional_pp']} pp")
    for row in payload["vao"]["por_recorte"][:5]:
        print(
            f"  vao {row['recorte']}: {row['vao_pp']} pp (nao escolha {row['nao_escolha_pct']}%)"
        )
    print("cobertura mais baixa:", payload["cobertura_dos_recortes"][0])


if __name__ == "__main__":
    main()
