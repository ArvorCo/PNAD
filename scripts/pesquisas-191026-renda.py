#!/usr/bin/env python3
"""Integra Nexus e PoderData de 19/10 com fontes arquivadas e recomposição."""

import importlib
from pathlib import Path

PREVIOUS = importlib.import_module("pesquisas-131026-renda")
COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-19"


def base(house, registry, n, method, pages, count, pub, note):
    poll = PREVIOUS.base(
        f"{house.lower()}_2026-10-18",
        house,
        registry,
        ("2026-10-16", "2026-10-18"),
        DAY,
        n,
        method,
        f"{house.lower()}_102026_19",
        pages,
        count,
        pub,
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    return poll


def nexus():
    note = (
        "18ª rodada, 128 páginas. Divulgação oficial 19/10, campo 16–18/10. "
        "A partir desta onda, percentuais com uma casa decimal (p. 4); série "
        "anterior reexpressa no novo PDF, sem sobrescrever os arquivos históricos. "
        "Perfil atual de renda familiar p. 125: 21/16/40/23, diferente de 19/18/40/23 "
        "em 13/10. Voto atual por renda p. 43 e sexo p. 42. O relatório não "
        "explicita se o perfil foi medido antes ou depois da ponderação: sensibilidade "
        "condicional ao perfil publicado. Sem parcela de renda ausente identificada. "
        "Presença certa ou provável 92,9% na p. 15 é declaração, não comparecimento "
        "observado nem modelo calibrado; não altera a âncora oficial das centrais."
    )
    poll = base(
        "Nexus",
        "BR-04499/2026",
        2002,
        "telefônico CATI; cotas de sexo, idade, escolaridade, tipo de telefonia e DDD",
        {
            "metodologia": 4,
            "perfil_renda": 125,
            "2t_topline": 22,
            "2t_validos": 24,
            "sexo": 42,
            "2t_renda": 43,
            "comparecimento": 15,
        },
        128,
        [46.5, 45.9, 4.7, 2.9],
        note,
    )
    poll["contratante"] = "Banco BTG Pactual"
    poll["publicado_validos"] = {"2t": {"flavio": 50.3, "lula": 49.7}}
    PREVIOUS.income(
        poll,
        [1, 2, 5, None],
        [21, 16, 40, 23],
        [
            [31.4, 59, 2.4, 7.2],
            [36.5, 55.4, 5.4, 2.7],
            [52, 39.7, 6.5, 1.8],
            [56.9, 38.9, 3.1, 1.1],
        ],
        [[53.7, 38.3, 5.8, 2.2], [40.1, 52.6, 3.7, 3.6]],
        [47, 53],
        note,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["comparecimento_publicado"] = {
        "pagina": 15,
        "categorias": [
            "decidiu comparecer",
            "provavelmente comparecerá",
            "provavelmente não comparecerá",
            "decidiu não comparecer",
            "NS/NR",
        ],
        "pct": [85.9, 7, 2.6, 2.9, 1.6],
        "uso": "Declaração, não âncora nem taxa observada por candidato.",
    }
    return poll


def poderdata():
    note = (
        "Íntegra de 33 páginas, campo 16–18/10, divulgação 19/10, BR-02586/2026. "
        "3.000 entrevistas em 695 municípios. Perfil atual p. 4: 46/33/21. "
        "Voto por renda p. 9; sexo p. 7. Topline 49/46/4/2 soma 101 por "
        "arredondamento; válidos divulgados 52/48 preservados separadamente. "
        "Ficha p. 2 mantém ponderação por sexo, idade, instrução, renda, resultado "
        "do 1º turno e região. Perfil publicado sem etapa pré/pós-pesos explícita: "
        "sensibilidade condicional. Nota do PDF admite não resposta como fonte "
        "de diferenças entre totais e cruzamentos, sem quantificar renda ausente."
    )
    poll = base(
        "PoderData",
        "BR-02586/2026",
        3000,
        "telefônico automatizado IVR; discador aleatório, 695 municípios nas 27 UFs",
        {
            "metodologia": 2,
            "perfil_renda": 4,
            "2t_topline": 6,
            "sexo": 7,
            "2t_renda": 9,
            "2t_validos": 11,
        },
        33,
        [49, 46, 4, 2],
        note,
    )
    poll["contratante"] = "Poder360, recursos próprios; divulgação com Aya Bancah"
    poll["publicado_validos"] = {"2t": {"flavio": 52, "lula": 48}}
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [46, 33, 21],
        [[42, 50, 5, 3], [57, 40, 2, 1], [53, 44, 2, 0]],
        [[57, 40, 3, 1], [42, 51, 5, 2]],
        [47, 53],
        note,
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    poll["metodologia_onda"] = {"ponderacao_voto_1t_2026": True, "pagina": 2}
    return poll


def main():
    polls = [nexus(), poderdata()]
    for poll in polls:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
        print(
            poll["id"],
            {k: v["residuo_max_abs"] for k, v in poll["controles"]["2t"].items()},
        )
    COMMON.write(
        ROOT / "analysis/reponderacao/auditoria_20261019.json",
        {
            "data": DAY,
            "pesquisas": polls,
            "conferencia_visual": {
                "nexus": [4, 15, 22, 24, 42, 43, 125],
                "poderdata": [2, 3, 4, 6, 7, 9, 11],
            },
            "regra": "Uma onda nova por casa; preservar fontes e snapshots anteriores.",
        },
    )


if __name__ == "__main__":
    main()
