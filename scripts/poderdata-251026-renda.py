#!/usr/bin/env python3
"""PoderData final: renda ponderada atual e presença documental da própria onda."""

import importlib
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
INCOME = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-25"


def poll():
    note = (
        "Íntegra de 27 páginas, campo 23–24/10, 4.000 entrevistas em 914 municípios, "
        "BR-02828/2026. P. 2 declara ponderação por sexo, idade, instrução, renda, "
        "resultado do primeiro turno e região. P. 4 identifica expressamente o perfil "
        "46/33/21 como percentuais ponderados; não transportar essa confirmação às "
        "ondas anteriores. Totais F/L/BN/NS 49/47/3/1 na p. 6; válidos oficiais "
        "51/49 na p. 11, separados da normalização dos inteiros. Renda p. 9 e sexo "
        "p. 7 conferidos visualmente e por recomposição. Presença certa por voto "
        "atual p. 19: 96/94/52/56 (F/L/BN/NS), somente na série documental desta "
        "onda. Autodeclaração não substitui o comparecimento nem os ajustes das centrais."
    )
    p = INCOME.base(
        "poderdata_2026-10-24",
        "PoderData",
        "BR-02828/2026",
        ("2026-10-23", "2026-10-24"),
        DAY,
        4000,
        "telefônico automatizado IVR/URA",
        "poderdata_102026_25",
        {
            "metodologia": 2,
            "perfil_renda": 4,
            "2t_topline": 6,
            "2t_validos": 11,
            "2t_renda": 9,
            "sexo": 7,
            "presenca_por_voto": 19,
        },
        27,
        [49, 47, 3, 1],
        note,
    )
    p["fonte"]["conferido_em"] = DAY
    p["fonte"]["url_publica"] = "https://brasil.arvor.co/fontes/poderdata_25102026.pdf"
    INCOME.income(
        p,
        [2, 5, None],
        [46, 33, 21],
        [[42, 54, 4, 0], [56, 40, 3, 1], [52, 44, 3, 1]],
        [[56, 41, 3, 1], [42, 53, 4, 0]],
        [47, 53],
        note,
    )
    p["publicado_validos"] = {"2t": {"flavio": 51, "lula": 49}}
    return p


def main():
    p = poll()
    COMMON.write(ROOT / f"analysis/reponderacao/pesquisas/{p['id']}.json", p)
    audit = {
        "data": DAY,
        "consultado_em": COMMON.read(
            ROOT / "data/originals/poderdata_102026_25/fonte.json"
        )["consultado_em"],
        "pesquisas": [p],
        "regra": "Substitui a onda PoderData de 21/10 uma vez em cada central. Perfil ponderado atual explícito. Mantém o likely voter Quaest sem reaplicar presença e preserva snapshots publicados.",
    }
    for rel in [
        "analysis/reponderacao/auditoria_poderdata_20261025.json",
        "docs/assets/reponderacao_poderdata_20261025.json",
    ]:
        COMMON.write(ROOT / rel, audit)
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    presence["conferido_em"] = DAY
    rule = (
        "Seleção por 'Com certeza vai votar', por voto atual (p. 19). "
        "Autodeclaração, não probabilidade calibrada; aplicar à PNAD supõe "
        "estabilidade dentro de cada eleitorado. Renda × voto × presença não "
        "publicada. Apenas série documental, sem mudar as centrais."
    )
    presence["ondas"][p["id"]] = {
        "tipo": "direto",
        "taxas": {"flavio": 0.96, "lula": 0.94, "indecisos": 0.56},
        "regra": rule,
        "fonte": {k: p["fonte"][k] for k in ["arquivo", "sha256", "url"]}
        | {"paginas": [15, 19]},
    }
    presence["auditoria_ultima_onda"] = [
        row
        for row in presence["auditoria_ultima_onda"]
        if row["instituto"] != "PoderData"
    ] + [
        {
            "instituto": "PoderData",
            "id": p["id"],
            "tipo": "direto",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": rule,
        }
    ]
    COMMON.write(path, presence)


if __name__ == "__main__":
    main()
