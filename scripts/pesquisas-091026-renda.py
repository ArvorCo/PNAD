#!/usr/bin/env python3
"""Integra a Atlas de 09/10 a partir da íntegra conferida, sem buscar dados vivos."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-09"
OPTIONS = ["flavio", "lula", "branco_nulo"]
INCOME = [
    [39.9, 55.0, 5.1],
    [45.3, 52.8, 1.9],
    [57.0, 40.6, 2.4],
    [56.5, 39.9, 3.6],
    [50.3, 47.1, 2.6],
]
SEX = [[57.7, 36.9, 5.4], [45.2, 53.6, 1.3]]
REGION = [
    [54.4, 42.9, 2.7],
    [36.2, 57.6, 6.3],
    [64.5, 34.3, 1.2],
    [65.7, 33.6, 0.7],
    [51.1, 48.5, 0.3],
]
PUBLISHED = dict(zip(OPTIONS, [51.1, 45.7, 3.2], strict=True))


def control(rows, weights):
    """Normaliza os perfis arredondados; testa cada categoria contra o topline."""
    recomposed = {
        key: round(
            sum(row[i] * w for row, w in zip(rows, weights, strict=True))
            / sum(weights),
            4,
        )
        for i, key in enumerate(OPTIONS)
    }
    residual = {k: round(recomposed[k] - PUBLISHED[k], 4) for k in OPTIONS}
    maximum = max(abs(v) for v in residual.values())
    if maximum > 0.15:
        raise ValueError(f"Recomposição Atlas incompatível: {residual}")
    return {
        "pesos": weights,
        "linhas": rows,
        "recomposto": recomposed,
        "residuo": residual,
        "residuo_max_abs": maximum,
    }


def atlas(items):
    source = COMMON.source(items, "relatorio.pdf")
    previous = COMMON.read(
        ROOT / "analysis/reponderacao/pesquisas/atlas_2026-10-02.json"
    )
    income = [19.4, 12.2, 26.3, 26.1, 16.1]
    controls = {
        "renda": control(INCOME, income),
        "sexo": control(SEX, [46.8, 53.2]),
        "regiao": control(REGION, [41.7, 29.5, 14.9, 6.9, 7.0]),
    }
    note = (
        "Íntegra de 20 páginas; perfil desta onda na p. 5 e voto por renda na p. 9. "
        "Campo 03–08/10 atravessa o 1º turno: sensibilidade por renda disponível no "
        "acervo e na série descritiva, excluída da central pós-04/10. Não há recorte "
        "publicado que isole as entrevistas após a votação. Os 3,2% agregam branco, "
        "nulo e não sei; não é possível separar brancos/nulos de indecisos."
    )
    return {
        "id": "atlas_2026-10-08",
        "instituto": "AtlasIntel",
        "contratante": "Bloomberg",
        "metodo": previous["metodo"],
        "n": 5026,
        "campo": {"inicio": "2026-10-03", "fim": "2026-10-08"},
        "divulgacao": DAY,
        "registro_tse": "BR-03663/2026",
        "renda": {
            "unidade": "reais_nominais",
            "mes_precos": "202610",
            "faixas": previous["renda"]["faixas"],
            "amostra_pct": income,
            "perfil_tipo": "perfil_publicado",
            "nota": "Renda familiar desta onda, p. 5, soma arredondada 100,1%, normalizada. "
            "Não reutiliza o perfil da rodada anterior. Cortes nominais de 10/2026; "
            "o motor limita a deflação ao último índice da série arquivada (07/2026), "
            "sem extrapolar a inflação dos meses seguintes.",
        },
        "publicado": {"2t": PUBLISHED},
        "publicado_validos": {"2t": {"flavio": 52.8, "lula": 47.2}},
        "cruzamentos": {
            "2t": {
                "opcoes": OPTIONS,
                "linhas": INCOME,
                "nota": "Transcrição visual da p. 9, na ordem das cinco faixas da p. 5. "
                "Branco/nulo/não sei permanece agregado, sem indecisos imputados. "
                "Recomposição conferida também por sexo e região; maior resíduo <0,15 pp.",
                "controle": controls,
            }
        },
        "controles": {"2t": controls},
        "fonte": {
            **source,
            "pdf": source["arquivo"],
            "tipo": "relatorio",
            "rotulo": "Atlas/Bloomberg: íntegra de 09/10",
            "pagina_instituto": "https://atlasintel.org/poll/brazil-national-2026-10-09",
            "total_paginas": 20,
            "conferido_em": DAY,
            "paginas": {
                "perfil_renda": 5,
                "2t_topline": 7,
                "2t_validos": 8,
                "2t_renda": 9,
                "2t_serie": 10,
            },
            "status": "Íntegra arquivada e conferida; voto por renda disponível.",
            "rotulos_opcoes": {"branco_nulo": "Branco/nulo/não sei (agregado)"},
            "nota": note,
        },
    }


def main():
    poll = atlas(COMMON.archive("atlas_102026_09"))
    COMMON.archive("reponderacao_20261009")
    COMMON.write(ROOT / f"analysis/reponderacao/pesquisas/{poll['id']}.json", poll)
    audit_path = ROOT / "docs/assets/reponderacao_20261009.json"
    audit = COMMON.read(audit_path)
    audit["conferido_utc"] = COMMON.read(
        ROOT / "data/originals/reponderacao_20261009/fonte.json"
    )["conferido_utc"]
    audit["fontes"] = [
        f for f in audit["fontes"] if f.get("pdf") != poll["fonte"]["pdf"]
    ]
    audit["fontes"].append(poll["fonte"])
    audit["controles"] = {poll["id"]: poll["controles"]}
    audit["varredura"] = COMMON.read(
        ROOT / "data/originals/reponderacao_20261009/varredura.json"
    )
    audit["regra"] = (
        "Novas divulgações nacionais de 09/10: Atlas e Vox. Atlas tem cruzamento desta "
        "onda, mas campo misto 03–08/10; Vox não tem voto por renda. Ambas aparecem no "
        "relatório; nenhuma altera a central de campo inteiramente posterior ao 1º turno. "
        "Datafolha e PoderData de 08/10 já estavam incorporadas, sem duplicação."
    )
    COMMON.write(audit_path, audit)
    print(
        json.dumps(
            {
                "id": poll["id"],
                "residuos_max": {
                    k: v["residuo_max_abs"] for k, v in poll["controles"]["2t"].items()
                },
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
