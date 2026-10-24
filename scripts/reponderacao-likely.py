"""Combina observações já condicionadas ao comparecimento sem refazer sua seleção."""

import numpy as np
from predicao_2026.motor import DEFF


def summary(selected):
    rows = [
        {
            "id": p["id"],
            "instituto": p["instituto"],
            "weight": p["weight"],
            **p["official_valids"],
        }
        for p in selected
        if p.get("official_valids")
    ]
    weight = sum(p["weight"] for p in rows)
    return {
        "rows": rows,
        "weight": weight,
        "flavio": sum(p["weight"] * p["flavio"] for p in rows) / weight,
        "regra": "Modelo oficial em votos válidos, combinado após os ajustes das demais casas. "
        "Sem PNAD, presença Nexus, adicional relativo ou conversão dos indecisos da amostra completa. "
        "Para contabilizar votos por eleitor, a fração de válidos entre presentes vem do cenário das demais casas; "
        "é hipótese comum de contabilidade, não dado do likely voter. Sem extrapolar tendência entre universos diferentes.",
        "draws": {},
    }


def draws(selected, kind, fitted, runs, seed):
    """Bootstrap conjunto; erro comum compartilhado pelos dois universos."""
    rng = np.random.default_rng(seed)
    is_official = np.array([bool(p.get("official_valids")) for p in selected])
    samples = []
    for p in selected:
        values = (
            [
                p["official_valids"]["lula"] / 100,
                p["official_valids"]["flavio"] / 100,
                0,
                0,
                0,
            ]
            if p.get("official_valids")
            else p[kind]
        )
        samples.append(
            rng.dirichlet(np.maximum(values, 1e-6) * min(p["n"], 2000) / DEFF, runs)
        )
    samples = np.stack(samples, axis=1)
    weights = rng.dirichlet(
        len(selected) * np.array([p["weight"] for p in selected]), runs
    )
    official_weight = weights[:, is_official].sum(axis=1)
    regular = np.einsum(
        "rh,rhk->rk", weights[:, ~is_official], samples[:, ~is_official]
    )
    regular /= regular.sum(axis=1, keepdims=True)
    central = np.average(
        [p[kind] for p in selected if not p.get("official_valids")],
        axis=0,
        weights=[p["weight"] for p in selected if not p.get("official_valids")],
    )
    regular = np.maximum(regular + np.asarray(fitted["vetor"]) - central, 1e-6)
    regular /= regular.sum(axis=1, keepdims=True)
    official = np.einsum("rh,rhk->rk", weights[:, is_official], samples[:, is_official])
    official_share = official[:, 1] / official[:, :2].sum(axis=1)
    common = rng.standard_t(5, runs) * np.sqrt(3 / 5) * 2 / 200
    trend = (
        rng.standard_t(5, runs) * np.sqrt(3 / 5) * fitted["dp_margem_projecao_pp"] / 200
    )
    transfer = np.clip(
        (common + trend) * regular[:, :3].sum(axis=1), -regular[:, 1], regular[:, 0]
    )
    regular[:, 0] -= transfer
    regular[:, 1] += transfer
    official_share = np.clip(official_share + common, 0, 1)
    return regular, [
        [round(w, 10), round(100 * f, 8)]
        for w, f in zip(official_weight, official_share, strict=True)
    ]
