#!/usr/bin/env python3
"""Bound an unpublished joint distribution, preserving rounded published margins."""

from itertools import product

import numpy as np
from scipy.optimize import linprog


def audit(rows, bases):
    """Continuous weighted masses; no reconstruction of individual respondents."""
    outcomes = list(rows)
    income = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM", "Renda nao publicada"]
    regions = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"]
    sexes = ["Masculino", "Feminino"]
    groups = [income, regions, sexes]
    b = dict(bases)
    b[income[-1]] = b["Total"] - sum(b[c] for c in income[:-1])
    cells = list(product(range(4), range(4), range(4), range(2)))
    eq, rhs, upper, bound, design, specs = [], [], [], [], [], []
    for dim, labels in enumerate(groups, 1):
        for g, label in enumerate(labels):
            mask = np.array([int(c[dim] == g) for c in cells], float)
            eq.append(mask)
            rhs.append(b[label])
            design.append(mask)
            if label == income[-1]:
                continue
            for o, outcome in enumerate(outcomes):
                m = mask * np.array([int(c[0] == o) for c in cells])
                pct = rows[outcome][label]
                lo, hi = (
                    max(0, pct - 0.5) * b[label] / 100,
                    min(100, pct + 0.5) * b[label] / 100,
                )
                upper.extend([m, -m])
                bound.extend([hi, -lo])
                design.append(m)
                specs.append((outcome, label, m, lo, hi))
    for o, outcome in enumerate(outcomes):
        m = np.array([int(c[0] == o) for c in cells], float)
        pct = rows[outcome]["Total"]
        lo, hi = (
            max(0, pct - 0.5) * b["Total"] / 100,
            min(100, pct + 0.5) * b["Total"] / 100,
        )
        upper.extend([m, -m])
        bound.extend([hi, -lo])
        design.append(m)
        specs.append((outcome, "Total", m, lo, hi))
    # Lula × income <= 2 minimum wages × Southeast, summed across sex.
    target = np.array(
        [int(c[0] == 0 and c[1] == 0 and c[2] == 0) for c in cells], float
    )
    ae, be, au, bu = map(np.array, [eq, rhs, upper, bound])
    feasibility = linprog(
        np.zeros(len(cells)),
        A_ub=au,
        b_ub=bu,
        A_eq=ae,
        b_eq=be,
        bounds=(0, None),
        method="highs",
    )
    if not feasibility.success:
        raise ValueError(feasibility.message)
    # Fix ALL constrained vote margins to the same feasible interior/corner values.
    # The two extrema now have identical unrounded published projections as well.
    masks = np.array([s[2] for s in specs])
    common = np.einsum("ij,j->i", masks, feasibility.x)
    fixed_a = np.vstack([ae, masks])
    fixed_b = np.concatenate([be, common])
    certificates = []
    for sign in [1, -1]:
        result = linprog(
            sign * target, A_eq=fixed_a, b_eq=fixed_b, bounds=(0, None), method="highs"
        )
        if not result.success:
            raise ValueError(result.message)
        x = result.x
        assert np.max(np.abs(np.einsum("ij,j->i", fixed_a, x) - fixed_b)) < 1e-6
        assert np.max(np.einsum("ij,j->i", au, x) - bu) < 1e-6
        certificates.append(
            {
                "mass": float(target @ x),
                "national_pct": float(target @ x / b["Total"] * 100),
                "cells": x.tolist(),
                "max_equality_error": float(
                    np.max(np.abs(np.einsum("ij,j->i", fixed_a, x) - fixed_b))
                ),
            }
        )
    rank = int(np.linalg.matrix_rank(fixed_a))
    return {
        "question": "Massa ponderada de eleitores de Lula, com renda até 2 SM, no Sudeste",
        "source_page": 42,
        "dimensions": {
            "outcome": outcomes,
            "income": income,
            "region": regions,
            "sex": sexes,
        },
        "cell_indices": cells,
        "n_cells": len(cells),
        "constraint_rank": rank,
        "linear_nullity": len(cells) - rank,
        "certificates": certificates,
        "common_projections": [
            {
                "outcome": s[0],
                "group": s[1],
                "mass": float(v),
                "pct": float(v / b[s[1]] * 100),
            }
            for s, v in zip(specs, common, strict=True)
        ],
        "assumptions": [
            "Bases ponderadas tratadas como exatas; percentuais dentro de ±0,5 pp do inteiro publicado.",
            "Inclui apenas voto no 2º turno × renda, região e sexo da p. 42; não é ajuste de todo o anexo.",
            "Massas contínuas agregadas, não contagens inteiras de pessoas. As duas soluções preservam as mesmas projeções não arredondadas.",
            "Os extremos são limites desta projeção, não estimativas nem intervalos de confiança. Outras restrições poderiam estreitá-los.",
        ],
    }
