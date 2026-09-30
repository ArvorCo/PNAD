#!/usr/bin/env python3
"""Transcreve oito prints da Futura BR-01122/2026 e testa margens independentes."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/originals/futura_092026_30"
POLL_DIR = ROOT / "analysis/reponderacao/pesquisas"


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def pairs(labels, values):
    return dict(zip(labels.split(), values, strict=True))


# P. 7. Percentuais publicados, sem eliminar NS/NR nem forçar soma 100.
PROFILE = {
    "genero": pairs("feminino masculino", [52.5, 47.5]),
    "regiao": pairs(
        "sudeste nordeste sul norte centro_oeste", [42.1, 28.1, 14.6, 7.7, 7.6]
    ),
    "idade": pairs("16_24 25_34 35_44 45_59 60_mais", [11, 19.3, 20.1, 26.3, 23.5]),
    "escolaridade": pairs("fundamental medio superior", [33.4, 41.5, 25.1]),
    "renda": pairs(
        "ate_1sm 1_2sm 2_5sm 5_10sm mais_10sm ns_nr", [27.7, 23.6, 23.6, 9.9, 5.1, 10]
    ),
    "religiao": pairs(
        "catolica evangelica nenhuma outras ns_nr", [53, 24.2, 14.3, 7.1, 1.5]
    ),
}
SEGMENTS = {
    **{k: list(PROFILE[k]) for k in ["genero", "regiao", "idade"]},
    "posicao_politica": [
        "dividido_cansado",
        "lado_bolsonaro",
        "lado_lula",
        "nao_dividido",
        "ns_nr",
    ],
}
# Cada coluna segue: gênero (2), região (5), idade (5), posição política (5).
FIRST = {
    # P. 23.
    "lula": [
        46,
        32.4,
        35.1,
        51.8,
        30.2,
        36.6,
        32.1,
        33.9,
        30.8,
        34.2,
        43.3,
        45.3,
        24.3,
        1.4,
        91.5,
        56.5,
        50.3,
    ],
    "flavio": [
        35.5,
        49.4,
        42.3,
        33.7,
        54.7,
        47.5,
        47.1,
        38.3,
        47,
        50.5,
        39.7,
        38.3,
        37.9,
        93.1,
        0.5,
        32.7,
        28,
    ],
    "caiado": [
        4.4,
        3.6,
        5.1,
        1.9,
        2.3,
        2.8,
        10.8,
        4,
        1.3,
        4.4,
        3.5,
        5.7,
        8.1,
        2,
        2.1,
        2,
        1.8,
    ],
    "renan_santos": [
        1.2,
        5.3,
        4,
        2.3,
        3.6,
        2.5,
        2.4,
        10.3,
        9,
        1.7,
        0.5,
        1.1,
        7.2,
        0.9,
        0.7,
        1.5,
        2.9,
    ],
    "rui": [0.1, 0.2, 0.1, 0.3, 0, 0, 0, 0, 0, 0.4, 0.2, 0, 0.3, 0, 0.1, 0, 0],
    "edmilson": [0.4, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0.7, 0.6, 0, 0, 0, 0],
    # P. 24.
    "hertz": [0.1, 0.1, 0.1, 0, 0, 0, 0, 0.6, 0, 0, 0, 0, 0.1, 0, 0.1, 0, 0],
    "cury": [
        4,
        3.6,
        3.9,
        4.1,
        4.4,
        2.8,
        2,
        5.6,
        6.1,
        4.9,
        3.9,
        1.2,
        8.5,
        1.3,
        1.5,
        1.8,
        1.4,
    ],
    "zema": [
        1.9,
        1.3,
        2.6,
        1.2,
        0.2,
        1.4,
        1,
        2.2,
        0.7,
        1.4,
        1.2,
        2.4,
        2.7,
        0.5,
        1.5,
        1.3,
        1.4,
    ],
    "samara": [0.2, 0.2, 0.4, 0, 0, 0, 0.3, 0.6, 0.3, 0, 0.3, 0, 0.6, 0, 0, 0, 0],
    "avalanche": [0, 0.3, 0.2, 0, 0, 0.8, 0, 0.8, 0, 0, 0, 0.2, 0, 0.2, 0.3, 0, 0],
    "grassi": [0.2, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0.3, 0, 0.2, 0, 0, 0, 0],
    # P. 25.
    "branco_nulo": [
        2.7,
        2,
        2.9,
        2.3,
        2.2,
        1.1,
        1.4,
        2,
        2.2,
        1.9,
        3.1,
        2.1,
        5.1,
        0.3,
        0,
        2,
        5.8,
    ],
    "indecisos": [
        3.4,
        1.8,
        2.5,
        2.4,
        2.3,
        4.5,
        2.9,
        1.7,
        2.7,
        0.6,
        3.9,
        3,
        4.4,
        0.2,
        1.7,
        2.3,
        8.2,
    ],
}
# P. 30, mesma ordem de segmentos.
SECOND = {
    "lula": [
        49.6,
        36.9,
        41.7,
        54.6,
        31.2,
        37.9,
        36.4,
        42.6,
        34.8,
        36.4,
        46.5,
        49.9,
        30.7,
        0.7,
        95.8,
        62.9,
        55.7,
    ],
    "flavio": [
        41.9,
        56.5,
        48.9,
        38.7,
        63,
        55.3,
        57.9,
        45.6,
        56.4,
        57.1,
        45.9,
        43.9,
        50.4,
        98.4,
        2.4,
        36.2,
        34.7,
    ],
    "branco_nulo": [
        6.7,
        5.7,
        6.8,
        6.1,
        5.5,
        6.5,
        5.4,
        11.8,
        8,
        5.8,
        6.3,
        3.8,
        16,
        0.4,
        1.8,
        0.9,
        5.2,
    ],
    "indecisos": [
        1.7,
        0.9,
        2.7,
        0.5,
        0.4,
        0.4,
        0.3,
        0,
        0.8,
        0.8,
        1.4,
        2.4,
        2.9,
        0.4,
        0,
        0,
        4.3,
    ],
}
TOP = {
    # P. 22, estimulada cenário 1. Clariana não aparece; ausência não vira zero.
    "1t": pairs(
        "flavio lula caiado cury renan_santos zema edmilson samara avalanche rui grassi hertz branco_nulo indecisos",
        [42.2, 39.4, 4, 3.8, 3.2, 1.6, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1, 2.4, 2.6],
    ),
    # P. 29.
    "2t": pairs("flavio lula branco_nulo indecisos", [49, 43.5, 6.2, 1.3]),
}
# P. 20. Separada da estimulada, inclusive menções a Marçal e Jair.
SPONTANEOUS = pairs(
    "lula flavio cury renan_santos caiado zema marcal jair hertz samara outros branco_nulo indecisos",
    [39.6, 38.8, 3.1, 2.8, 2.6, 0.5, 0.2, 0.1, 0, 0, 1.4, 2.8, 8],
)


def crossbreak(columns):
    assert all(len(v) == 17 for v in columns.values())
    result, offset = {}, 0
    for dimension, labels in SEGMENTS.items():
        result[dimension] = {
            label: {k: v[offset + i] for k, v in columns.items()}
            for i, label in enumerate(labels)
        }
        offset += len(labels)
    return result


def main():
    manifest = json.loads((BASE / "manifesto.json").read_text())
    for image in manifest["imagens"]:
        content = (ROOT / image["arquivo"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == image["sha256"]
    tables = {"1t": crossbreak(FIRST), "2t": crossbreak(SECOND)}
    controls = []
    for turn, table in tables.items():
        for dim in ["genero", "regiao", "idade"]:
            weights = PROFILE[dim]
            # Normalização explícita dos arredondamentos de região (100,1) e idade (100,2).
            recomp = {
                c: sum(weights[g] * row[c] for g, row in table[dim].items())
                / sum(weights.values())
                for c in TOP[turn]
            }
            residual = {c: round(recomp[c] - v, 6) for c, v in TOP[turn].items()}
            controls.append(
                {
                    "turno": turn,
                    "dimensao": dim,
                    "soma_pesos_publicados": sum(weights.values()),
                    "recomposto": recomp,
                    "residuos_pp": residual,
                    "residuo_max_pp": max(map(abs, residual.values())),
                }
            )
    data = {
        "registro_tse": "BR-01122/2026",
        "recebido_em": "2026-09-30",
        "fonte": manifest,
        "perfil": {"pagina": 7, "percentuais": PROFILE},
        "publicado": TOP,
        "espontanea": {"pagina": 20, "percentuais": SPONTANEOUS},
        "paginas": {
            "1t_topline": 22,
            "1t_cruzamentos": [23, 24, 25],
            "2t_topline": 29,
            "2t_cruzamentos": 30,
        },
        "cruzamentos_demograficos": tables,
        "controles": controls,
        "limites": [
            "Oito prints, não a íntegra. Não se afirma que páginas não recebidas omitem renda.",
            "Perfil da amostra não foi identificado como bruto ou ponderado nos prints.",
            "A renda soma 99,9%, incluindo 10% NS/NR. Renda conhecida soma 89,9%.",
            "Não há voto por renda nos prints recebidos; cruzamentos demográficos não substituem renda.",
            "Posição política não tem bases nestes prints e não é agregada ao nacional.",
            "Percentuais 0,0 são preservados como arredondamentos publicados, não como impossibilidades estruturais.",
            "Clariana não aparece na estimulada recebida; não foi imputado zero.",
            "Não se inferem propensão a comparecer nem transferências individuais desses cruzamentos.",
            "Recomposição auxiliar por gênero: resíduo máximo 0,165 pp; região: 0,439061 pp; idade: 0,910379 pp. As diferenças maiores não se explicam só por arredondamento a uma decimal. Falta esclarecer a relação entre o perfil publicado e os pesos dos cruzamentos.",
        ],
    }
    dump(BASE / "transcricao.json", data)
    dump(ROOT / "docs/assets/futura_20260930_prints.json", data)
    poll = {
        "id": "futura_2026-09-29",
        "instituto": "Futura",
        "contratante": "Futura/100% Cidades (marcas nos prints)",
        "registro_tse": "BR-01122/2026",
        "campo": {"inicio": "2026-09-25", "fim": "2026-09-29"},
        "divulgacao": "2026-09-30",
        "n": None,
        "metodo": "Ficha técnica não recebida nos prints.",
        "fonte": {
            "tipo": "prints",
            "url": "https://www.futurainteligencia.com.br/pesquisas",
            "arquivo": str((BASE / "manifesto.json").relative_to(ROOT)),
            "paginas": [7, 20, 22, 23, 24, 25, 29, 30],
            "conferido_em": "2026-09-30",
            "nota": "Nova rodada BR-01122/2026 recebida em oito prints. A biblioteca oficial informa campo de 25 a 29/09; ficha técnica ainda não recebida. Os placares vêm das pp. 22 e 29, e não da espontânea da p. 20. A nova onda substitui a de 24/09 na cobertura atual.",
            "complementos": [
                {
                    "url": "assets/futura_20260930_prints.json",
                    "rotulo": "Transcrição integral dos oito prints e controles de recomposição",
                }
            ],
        },
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "mes_precos": "202609",
            "faixas": [
                {"rotulo": label, "max": cut}
                for label, cut in [
                    ("Até 1 SM", 1),
                    ("1 a 2 SM", 2),
                    ("2 a 5 SM", 5),
                    ("5 a 10 SM", 10),
                    ("Mais de 10 SM", None),
                ]
            ],
            "amostra_pct": [27.7, 23.6, 23.6, 9.9, 5.1],
            "nao_declarada_pct": 10,
            "nota": "P. 7: renda familiar; 89,9% nas faixas conhecidas e 10% NS/NR, total 99,9% por arredondamento. Não redistribuímos os não declarantes.",
        },
        "publicado": TOP,
        "espontanea": SPONTANEOUS,
        "cruzamentos": {},
        "ignorar": True,
        "motivo": "Os prints recebidos trazem perfil de renda (p. 7), mas voto cruzado somente por gênero, região, idade e posição política (pp. 23–25 e 30). Falta voto por faixa de renda para reponderar. Dez por cento não declaram renda. A íntegra não foi recebida; não se conclui que o cruzamento esteja ausente de todo o relatório.",
        "notas": "Data de recebimento e disponibilidade: 30/09. Campo conforme catálogo oficial; fontes preliminares citavam início em 24/09, pendente de ficha técnica. Tamanho da amostra não foi copiado de outra onda. Não há perfil de provável comparecimento nos prints.",
    }
    dump(POLL_DIR / f"{poll['id']}.json", poll)
    return poll, data


if __name__ == "__main__":
    main()
    print("Futura: oito prints transcritos; seis controles auxiliares calculados.")
