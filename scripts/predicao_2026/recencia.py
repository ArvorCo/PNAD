"""Decaimento temporal pelo meio do campo, sem rejuvenescer republicações."""

from datetime import date

import numpy as np

NATIONAL_HALF_LIFE = 3.0
STATE_HALF_LIFE = 7.0


def midpoint(field):
    return (
        date.fromisoformat(field["inicio"]).toordinal()
        + date.fromisoformat(field["fim"]).toordinal()
    ) / 2


def age(field, today):
    return max(0.0, today.toordinal() - midpoint(field))


def decay(days, half_life):
    if not np.isfinite(half_life) or half_life <= 0:
        raise ValueError("Meia-vida precisa ser positiva e finita")
    return float(2 ** (-max(0, days) / half_life))


def weights(polls, *, equal=False):
    w = np.array([1 if equal else p["peso_recencia"] for p in polls], float)
    if not len(w) or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("Pesos temporais inválidos")
    return w / w.sum()


def mean(polls, kind, *, equal=False):
    return np.average(
        [p[kind] for p in polls], axis=0, weights=weights(polls, equal=equal)
    ).tolist()
