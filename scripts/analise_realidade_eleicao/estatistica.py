"""Associações descritivas; sem tratar municípios vizinhos como amostra IID."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata


def correlacao(x, y, w=None):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 3:
        return None
    w = np.ones(len(x)) if w is None else np.asarray(w, dtype=float)
    x, y = x - np.average(x, weights=w), y - np.average(y, weights=w)
    den = np.sqrt(np.sum(w * x * x) * np.sum(w * y * y))
    return float(np.sum(w * x * y) / den) if den > 0 else None


def dentro_grupos(values, groups):
    values, groups = np.asarray(values, dtype=float), np.asarray(groups)
    result = values.copy()
    for grupo in set(groups):
        mask = groups == grupo
        result[mask] -= values[mask].mean()
    return result


def resumo(rows, campo, grupo="uf"):
    rs = [
        r
        for r in rows
        if r.get(campo) is not None
        and r.get("pct_lula") is not None
        and r.get("completo", True)
        and r["validos"] > 0
    ]
    x, y, w, g = ([r[k] for r in rs] for k in (campo, "pct_lula", "validos", grupo))
    bins = []
    # Empates não são divididos artificialmente entre grupos.
    limites = np.quantile(x, [0.2, 0.4, 0.6, 0.8]) if x else []
    for i in range(5):
        group = [
            r for r in rs if int(np.searchsorted(limites, r[campo], side="left")) == i
        ]
        if not group:
            continue
        f, votos_lula = (sum(r[k] for r in group) for k in ("flavio", "lula"))
        bins.append(
            {
                "faixa": i + 1,
                "min": min(r[campo] for r in group),
                "max": max(r[campo] for r in group),
                "n": len(group),
                "flavio": f,
                "lula": votos_lula,
                "pct_lula": 100 * votos_lula / (f + votos_lula),
            }
        )
    return {
        "campo": campo,
        "n": len(rs),
        "validos": sum(w),
        "pearson": correlacao(x, y),
        "spearman": correlacao(rankdata(x), rankdata(y)),
        "ponderada_validos": correlacao(x, y, w),
        "dentro_grupo": correlacao(dentro_grupos(x, g), dentro_grupos(y, g)),
        "grupo": grupo,
        "faixas": bins,
    }


def analisar(data):
    campos = (
        "renda_ate2",
        "renda_mais5",
        "renda_mediana_brl",
        "superior",
        "ips",
        "homicidios_taxa_100mil",
        "rural_pct",
    )
    return {
        "municipios": {k: resumo(data["municipios"], k) for k in campos},
        "zonas": {k: resumo(data["zonas"], k, "ibge") for k in campos[:4]},
    }
