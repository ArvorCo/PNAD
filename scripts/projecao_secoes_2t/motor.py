"""Motores puros e conservativos; matrizes ecológicas não identificam pessoas."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit

from .fontes import KEYS, PARTS

DEST = ["direita", "esquerda", "bn", "ausentes"]
LABELS = {
    "metade": "Terceira via dividida 50/50",
    "proporcional": "Terceira via proporcional à seção",
    "deslocamento_uf": "Deslocamento histórico por UF",
    "deslocamento_secao": "Deslocamento histórico por seção, encolhido",
    "matriz_uf": "Matriz ecológica por UF",
    "matriz_contexto": "Matriz ecológica por UF e contexto",
}


def fractions(frame, turn=1, parts=PARTS):
    return (
        frame[[f"{p}_{turn}" for p in parts]].to_numpy(float)
        / frame[f"aptos_{turn}"].to_numpy(float)[:, None]
    )


def share(x):
    return np.divide(
        x[:, 0],
        x[:, :2].sum(axis=1),
        out=np.full(len(x), 0.5),
        where=x[:, :2].sum(axis=1) > 0,
    )


def logits(p):
    return logit(np.clip(p, 1e-5, 1 - 1e-5))


def context(x):
    return np.digitize(share(x), [0.35, 0.65])


def matrix_fit(x, y, weights, prior, penalty):
    """MQP não negativo, linhas somando um; penalidade em unidades de aptos."""
    gram = x.T @ (x * weights[:, None])
    cross = x.T @ (y * weights[:, None])
    scale = weights.sum() + penalty
    gram = (gram + penalty * np.eye(x.shape[1])) / scale
    cross = (cross + penalty * prior) / scale

    def fun(flat):
        m = flat.reshape(prior.shape)
        return float(np.sum(m * (gram @ m)) - 2 * np.sum(m * cross))

    def jac(flat):
        return (2 * (gram @ flat.reshape(prior.shape) - cross)).ravel()

    row_constraint = np.kron(np.eye(len(prior)), np.ones((1, prior.shape[1])))
    fit = minimize(
        fun,
        prior.ravel(),
        jac=jac,
        method="SLSQP",
        bounds=[(0, 1)] * prior.size,
        constraints={
            "type": "eq",
            "fun": lambda m: row_constraint @ m - 1,
            "jac": lambda m: row_constraint,
        },
        options={"ftol": 1e-12, "maxiter": 500},
    )
    if not fit.success:
        raise ValueError(f"Matriz não convergiu: {fit.message}")
    matrix = fit.x.reshape(prior.shape)
    return matrix / matrix.sum(axis=1)[:, None]


def fit_matrices(train):
    x, y = fractions(train), fractions(train, 2, DEST)
    w = train.aptos_1.to_numpy(float)
    initial = np.array(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0.5, 0.5, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        float,
    )
    national = matrix_fit(x, y, w, initial, 1)
    regions, contexts = {}, {}
    cluster = context(x)
    for uf in sorted(train.uf.unique()):
        mask = (train.uf == uf).to_numpy()
        regions[uf] = matrix_fit(x[mask], y[mask], w[mask], national, 50_000)
        for c in range(3):
            selected = mask & (cluster == c)
            contexts[(uf, c)] = (
                matrix_fit(x[selected], y[selected], w[selected], regions[uf], 20_000)
                if selected.any()
                else regions[uf]
            )
    return national, regions, contexts


def predict_matrices(train, target):
    national, by_uf, by_context = fit_matrices(train)
    x = fractions(target)
    context_ids = context(x)
    simple, contextual = np.zeros((len(x), 4)), np.zeros((len(x), 4))
    for uf in sorted(target.uf.unique()):
        mask = (target.uf == uf).to_numpy()
        simple[mask] = x[mask] @ by_uf.get(uf, national)
        for c in range(3):
            selected = mask & (context_ids == c)
            contextual[selected] = x[selected] @ by_context.get(
                (uf, c), by_uf.get(uf, national)
            )
    return {"matriz_uf": simple, "matriz_contexto": contextual}, {
        "brasil": national.tolist(),
        "ufs": {uf: m.tolist() for uf, m in by_uf.items()},
        "contextos": {f"{uf}_{c}": m.tolist() for (uf, c), m in by_context.items()},
        "origens": PARTS,
        "destinos": DEST,
    }


def historical_shift(train, target):
    """Transporta diferenças agregadas, não fluxos individuais."""
    x, y, t = fractions(train), fractions(train, 2, DEST), fractions(target)
    delta = logits(share(y)) - logits(share(x))
    w = train[["direita_1", "esquerda_1"]].sum(axis=1).to_numpy(float)
    aux = train[[*KEYS, "local_1"]].copy()
    aux["delta"], aux["weight"] = delta, w
    aux["weighted"] = delta * w
    national = np.average(delta, weights=w)
    states = aux.groupby("uf")[["weighted", "weight"]].sum()
    states["d"] = states.weighted / states.weight
    towns = aux.groupby(["uf", "mun"])[["weighted", "weight"]].sum().reset_index()
    towns["d"] = (towns.weighted + 5000 * towns.uf.map(states.d)) / (
        towns.weight + 5000
    )
    matched = (
        target[[*KEYS, "local_1"]]
        .merge(aux, on=[*KEYS, "local_1"], how="left", validate="one_to_one")
        .merge(
            towns[["uf", "mun", "d"]],
            on=["uf", "mun"],
            how="left",
            validate="many_to_one",
        )
    )
    state_delta = target.uf.map(states.d).fillna(national).to_numpy()
    town_delta = matched.d.fillna(pd.Series(state_delta)).to_numpy()
    section_delta = (matched.weighted.fillna(0).to_numpy() + 500 * town_delta) / (
        matched.weight.fillna(0).to_numpy() + 500
    )
    # Conserva comparecimento e válidos do 1T; a matriz fornece alternativa com mudança.
    mass_valid = t[:, :3].sum(axis=1)
    out = {}
    for name, change in [
        ("deslocamento_uf", state_delta),
        ("deslocamento_secao", section_delta),
    ]:
        p = expit(logits(share(t)) + change)
        out[name] = np.column_stack([mass_valid * p, mass_valid * (1 - p), t[:, 3:]])
    return out, {
        "secoes_com_chave_e_local": int(matched.weight.notna().sum()),
        "secoes_alvo": len(target),
    }


def predict(train, target):
    x = fractions(target)
    half = np.column_stack([x[:, 0] + 0.5 * x[:, 2], x[:, 1] + 0.5 * x[:, 2], x[:, 3:]])
    p = share(x)
    proportional = np.column_stack(
        [x[:, 0] + p * x[:, 2], x[:, 1] + (1 - p) * x[:, 2], x[:, 3:]]
    )
    predictions = {"metade": half, "proporcional": proportional}
    matrices, fit = predict_matrices(train, target)
    shifts, matching = historical_shift(train, target)
    predictions.update(shifts)
    predictions.update(matrices)
    for name, values in predictions.items():
        if (
            not np.isfinite(values).all()
            or (values < -1e-10).any()
            or not np.allclose(values.sum(axis=1), 1, atol=1e-9)
        ):
            raise ValueError(f"Partição projetada inválida: {name}")
    return predictions, {"matrizes": fit, "casamento": matching}


def score(target, predictions):
    truth = target[[f"{p}_2" for p in DEST]].to_numpy(float)
    electorate = target.aptos_1.to_numpy(float)
    result = {}
    for name, prediction in predictions.items():
        counts = prediction * electorate[:, None]
        actual_share, predicted_share = share(truth), share(counts)
        v = truth[:, :2].sum(axis=1)
        errors, weights, rows = [], [], []
        for uf in sorted(target.uf.unique()):
            mask = (target.uf == uf).to_numpy()
            actual, predicted = truth[mask].sum(axis=0), counts[mask].sum(axis=0)
            actual_p, predicted_p = (
                share(actual[None, :])[0],
                share(predicted[None, :])[0],
            )
            error = 100 * (predicted_p - actual_p)
            errors.append(error)
            weights.append(actual[:2].sum())
            rows.append(
                {
                    "uf": uf,
                    "observado_pct": 100 * actual_p,
                    "projetado_pct": 100 * predicted_p,
                    "erro_pp": error,
                    "validos": float(actual[:2].sum()),
                }
            )
        national = 100 * (
            share(counts.sum(axis=0)[None, :])[0] - share(truth.sum(axis=0)[None, :])[0]
        )
        result[name] = {
            "rotulo": LABELS[name],
            "rmse_uf_pp": float(
                np.sqrt(np.average(np.square(errors), weights=weights))
            ),
            "mae_uf_pp": float(np.average(np.abs(errors), weights=weights)),
            "erro_nacional_pp": float(national),
            "rmse_secao_pp": float(
                100
                * np.sqrt(np.average((actual_share - predicted_share) ** 2, weights=v))
            ),
            "ufs": rows,
        }
    return result


def bounds(frame):
    """Limites de Fréchet/Duncan–Davis: terceiros 1T → direita 2T."""
    stable = frame[frame.aptos_1 == frame.aptos_2]
    other, right, total = [
        stable[c].to_numpy(float) for c in ("outros_1", "direita_2", "aptos_1")
    ]
    lower, upper = np.maximum(0, other + right - total), np.minimum(other, right)
    return {
        "secoes": len(stable),
        "terceiros": int(other.sum()),
        "minimo_votos": float(lower.sum()),
        "maximo_votos": float(upper.sum()),
        "minimo_pct": float(100 * lower.sum() / other.sum()),
        "maximo_pct": float(100 * upper.sum() / other.sum()),
        "hipotese": "Mesma população nos dois turnos; igualdade de aptos é condição necessária, insuficiente. Permite todos os demais fluxos.",
    }
