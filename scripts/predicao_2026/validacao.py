"""Retrospectiva apenas de comparecimento: 2018 prediz 2022, sem usar seu voto."""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict

import numpy as np

from .tse import OUT, ROOT, key, rows, sha


def historical_sections(year):
    path = ROOT / f"data/raw/tse_resultados/detalhe_votacao_secao_{year}.zip"
    result = {}
    with zipfile.ZipFile(path) as z:
        for row in rows(z, f"detalhe_votacao_secao_{year}_BR.csv"):
            if row["NR_TURNO"] != "1" or row["CD_CARGO"] != "1":
                continue
            a, c, absent = (
                int(row[k]) for k in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES")
            )
            if a <= 0 or a != c + absent:
                continue
            ident = key(row)
            if ident in result:
                raise ValueError(f"Duplicata {year}: {ident}")
            result[ident] = (a, c)
    return result


def backtest(kappa=100):
    old, actual = historical_sections(2018), historical_sections(2022)
    totals18 = defaultdict(lambda: [0, 0])
    for ident, values in old.items():
        totals18[ident[0]][0] += values[0]
        totals18[ident[0]][1] += values[1]
    totals = defaultdict(lambda: [0, 0, 0.0, 0.0, 0, 0.0])
    for ident, (a, c) in actual.items():
        if ident[0] == "ZZ":
            continue
        ua, uc = totals18[ident[0]]
        prior = uc / ua
        oa, oc = old.get(ident, (0, 0))
        pred = (oc + kappa * prior) / (oa + kappa) if oa else prior
        t = totals[ident[0]]
        t[0] += a
        t[1] += c
        t[2] += a * pred
        t[3] += a * prior
        t[4] += a if oa else 0
        t[5] += a * (pred - c / a) ** 2
    ufs = [
        {
            "uf": uf,
            "aptos_2022": v[0],
            "comparecimento_real_pct": 100 * v[1] / v[0],
            "previsto_secoes_pct": 100 * v[2] / v[0],
            "previsto_uf_pct": 100 * v[3] / v[0],
            "erro_secoes_pp": 100 * (v[2] - v[1]) / v[0],
            "erro_uf_pp": 100 * (v[3] - v[1]) / v[0],
            "cobertura_pareada_pct": 100 * v[4] / v[0],
            "rmse_secoes_pp": 100 * np.sqrt(v[5] / v[0]),
        }
        for uf, v in sorted(totals.items())
    ]
    aptos = sum(v[0] for v in totals.values())
    weights = np.array([u["aptos_2022"] / aptos for u in ufs])
    metrics = {
        "rmse_ufs_secoes_pp": float(
            np.sqrt(weights @ np.square([u["erro_secoes_pp"] for u in ufs]))
        ),
        "rmse_ufs_constante_pp": float(
            np.sqrt(weights @ np.square([u["erro_uf_pp"] for u in ufs]))
        ),
        "erro_nacional_pp": 100 * sum(v[2] - v[1] for v in totals.values()) / aptos,
        "rmse_secoes_pp": 100 * np.sqrt(sum(v[5] for v in totals.values()) / aptos),
    }
    out = {
        "metodo": "Taxas do 1º turno de 2018, com aptos de 2022 como exposição. Não usa comparecimento nem voto de 2022 para ajustar parâmetros.",
        "kappa": kappa,
        "escopo": "27 UFs, seções com aptos=comparecimento+abstenção; exterior excluído",
        "limite": "Valida somente transporte temporal do comparecimento; não valida preferência, PNAD, voto útil ou probabilidades eleitorais.",
        "metricas": metrics,
        "ufs": ufs,
        "fontes": [
            {
                "arquivo": f"data/raw/tse_resultados/detalhe_votacao_secao_{y}.zip",
                "url": f"https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_{y}.zip",
                "sha256": sha(
                    ROOT / f"data/raw/tse_resultados/detalhe_votacao_secao_{y}.zip"
                ),
            }
            for y in (2018, 2022)
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "validacao.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    )
    return out
