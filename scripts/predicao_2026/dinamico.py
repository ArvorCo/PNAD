"""Modelo dinâmico linear da série nacional: nível local com efeitos de casa.

Estado: o nível das cinco categorias (Lula, Flávio, demais, indecisos e
branco/nulo) segue um passeio aleatório em tempo contínuo; cada casa tem um
efeito constante no tempo, com soma zero entre as casas da janela. A
observação é o vetor da onda no ponto médio do campo, com erro amostral
multinomial inflado pelo fator de desenho convencional. A variância de
evolução e a dispersão dos efeitos de casa saem da máxima verossimilhança
marginal do filtro de Kalman, sem olhar a urna.

O modelo trabalha na escala aditiva. As cinco partes somam um; o filtro usa
as quatro primeiras, e branco/nulo é o complemento. Todas as covariâncias são
construídas no subespaço de soma zero, então a escolha da categoria omitida
não altera a inferência.

A soma zero dos efeitos de casa é a hipótese de identificação: o nível é o
que uma casa média da janela mediria. Se todas as casas errarem na mesma
direção, o modelo não detecta; esse erro comum fica no Monte Carlo.
"""

from __future__ import annotations

from datetime import date

import numpy as np
from scipy.optimize import minimize

from .recencia import midpoint

CATEGORIES = ("lula", "flavio", "outros", "indecisos", "branco_nulo")
FREE = len(CATEGORIES) - 1
DEFF = 1.5  # Mesma convenção de motor.DEFF; conferida no teste.
N_CAP = 2000  # Mesmo teto do bootstrap nacional em motor.simulate.
PRIOR_SD = 0.05  # Nível inicial com 5 pp de desvio: informação fraca.
FLOOR = 0.005  # Piso de 0,5% só para a variância amostral de categorias raras.
BOUNDS_Q = (1e-9, 1e-3)
BOUNDS_S = (5e-4, 0.08)
BOUNDS_PHI = (0.5, 30.0)
STARTS = ((1e-5, 0.015, 2.0), (1e-6, 0.03, 4.0), (1e-4, 0.008, 1.0))


def _prepare(polls, kind):
    rows = sorted(polls, key=lambda p: (midpoint(p["campo"]), p["id"]))
    if len(rows) < 3:
        raise ValueError("Modelo dinâmico exige ao menos três ondas")
    houses = sorted({p["instituto"] for p in rows})
    y = np.array([p[kind] for p in rows], float)
    if not np.isfinite(y).all() or (y < 0).any():
        raise ValueError("Vetor de onda inválido no modelo dinâmico")
    y /= y.sum(axis=1, keepdims=True)
    mean = y.mean(axis=0)
    shape = (np.diag(mean) - np.outer(mean, mean))[:FREE, :FREE]
    noise = []
    for p, v in zip(rows, y, strict=True):
        f = np.maximum(v, FLOOR)
        f /= f.sum()
        noise.append(
            ((np.diag(f) - np.outer(f, f)) * DEFF / min(p["n"], N_CAP))[:FREE, :FREE]
        )
    return {
        "rows": rows,
        "houses": houses,
        "y": y[:, :FREE],
        "t": np.array([midpoint(p["campo"]) for p in rows]),
        "h": np.array([houses.index(p["instituto"]) for p in rows]),
        "R": noise,
        "mean": mean,
        "shape": shape,
    }


def _house_cov(s):
    center = np.eye(len(CATEGORIES)) - 1 / len(CATEGORIES)
    return (center @ np.diag(np.square(s)) @ center)[:FREE, :FREE]


def _run(data, q, s, *, phi=1.0, until=None, record=False):
    """Filtro de Kalman. Devolve log-verossimilhança, estado final e trajetória."""
    H = len(data["houses"])
    dim = FREE * (1 + H)
    a = np.zeros(dim)
    a[:FREE] = data["mean"][:FREE]
    P = np.zeros((dim, dim))
    P[:FREE, :FREE] = np.eye(FREE) * PRIOR_SD**2
    # Prior N(0, S) por casa condicionada a soma zero entre casas.
    P[FREE:, FREE:] = np.kron(np.eye(H) - 1 / H, _house_cov(s))
    Q = q * data["shape"]
    t = data["t"]
    events = [(ti, 0, i) for i, ti in enumerate(t)]
    if record:
        last = until if until is not None else int(np.floor(t[-1]))
        events += [(float(d), 1, d) for d in range(int(np.ceil(t[0])), last + 1)]
    events.sort()
    trajectory = []
    # O BLAS do macOS sinaliza exceções espúrias em matmul; a finitude do
    # resultado é conferida explicitamente no fim.
    with np.errstate(all="ignore"):
        loglik, a, P = _loop(data, events, a, P, Q, phi, trajectory)
    if not (np.isfinite(loglik) and np.isfinite(a).all() and np.isfinite(P).all()):
        raise np.linalg.LinAlgError("Filtro de Kalman não finito")
    time = max(t[-1], trajectory[-1][0] if trajectory else t[-1])
    if until is not None and until > time:
        P[:FREE, :FREE] += (until - time) * Q
    return loglik, a, P, trajectory


def _loop(data, events, a, P, Q, phi, trajectory):
    time, loglik, seen = data["t"][0], 0.0, 0
    for when, kind, ident in events:
        if when > time:
            P[:FREE, :FREE] += (when - time) * Q
            time = when
        if kind == 1:
            trajectory.append((ident, a[:FREE].copy(), P[:FREE, :FREE].copy(), seen))
            continue
        block = slice(FREE * (1 + data["h"][ident]), FREE * (2 + data["h"][ident]))
        innovation = data["y"][ident] - a[:FREE] - a[block]
        PZ = P[:, :FREE] + P[:, block]
        F = PZ[:FREE] + PZ[block] + phi * data["R"][ident]
        chol = np.linalg.cholesky(F)
        solved = np.linalg.solve(chol, innovation)
        loglik -= 0.5 * (
            2 * np.log(np.diag(chol)).sum() + solved @ solved + FREE * np.log(2 * np.pi)
        )
        gain = np.linalg.solve(F, PZ.T).T
        a = a + gain @ innovation
        P = P - gain @ PZ.T
        P = (P + P.T) / 2
        seen += 1
    return loglik, a, P


def _unpack(theta, excess):
    q, s = float(np.exp(theta[0])), np.exp(theta[1 : 1 + len(CATEGORIES)])
    return q, s, float(np.exp(theta[-1])) if excess else 1.0


def estimate(data, *, excess=True, start=None):
    """Máxima verossimilhança marginal de (q, s_k, phi), com várias partidas.

    phi multiplica a variância amostral n/deff. phi = 1 é a convenção pura;
    phi > 1 acomoda erro não amostral de cada onda (Shirani-Mehr et al., 2018).
    """
    bounds = [tuple(np.log(BOUNDS_Q))] + [tuple(np.log(BOUNDS_S))] * len(CATEGORIES)
    if excess:
        bounds.append(tuple(np.log(BOUNDS_PHI)))

    def objective(theta):
        q, s, phi = _unpack(theta, excess)
        with np.errstate(all="ignore"):
            try:
                value = -_run(data, q, s, phi=phi)[0]
            except np.linalg.LinAlgError:
                return 1e12
        return value if np.isfinite(value) else 1e12

    best = None
    starts = []
    for q0, s0, phi0 in STARTS:
        x0 = np.r_[np.log(q0), np.full(len(CATEGORIES), np.log(s0))]
        starts.append(np.r_[x0, np.log(phi0)] if excess else x0)
    # Partida quente (validação): ótimo da origem anterior mais a partida padrão.
    if start is not None:
        starts = [np.clip(start, *np.array(bounds).T), starts[0]]
    for x0 in starts:
        result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
        if best is None or result.fun < best.fun:
            best = result
    if best is None:
        raise ValueError("Estimação do DLM sem ponto de partida")
    return best


def _five(level4, cov4):
    vector = np.r_[level4, 1 - level4.sum()]
    lift = np.vstack([np.eye(FREE), -np.ones(FREE)])
    return vector, lift @ cov4 @ lift.T


def _valid_margin(vector, cov):
    """Diferença F−L nos válidos, em pp, com desvio pelo método delta."""
    valid = vector[:3].sum()
    gap = vector[1] - vector[0]
    grad = np.zeros(len(CATEGORIES))
    grad[0] = 100 * (-1 / valid - gap / valid**2)
    grad[1] = 100 * (1 / valid - gap / valid**2)
    grad[2] = -100 * gap / valid**2
    return 100 * gap / valid, float(np.sqrt(max(grad @ cov @ grad, 0)))


def simplex(vector):
    """Trunca negativos e normaliza, como o adaptador das ondas."""
    x = np.maximum(np.asarray(vector, float), 0)
    if x.sum() <= 0:
        raise ValueError("Estado dinâmico sem massa positiva")
    return x / x.sum()


def level(polls, today, kind="previsao_vetor", *, excess=True, start=None):
    """Só o vetor do nível na data; usado na validação de origem móvel."""
    data = _prepare(polls, kind)
    theta = estimate(data, excess=excess, start=start).x
    q, s, phi = _unpack(theta, excess)
    _, a, _, _ = _run(data, q, s, phi=phi, until=today.toordinal())
    house = {
        name: np.r_[a[FREE * (1 + i) : FREE * (2 + i)], 0.0]
        for i, name in enumerate(data["houses"])
    }
    for effect in house.values():
        effect[-1] = -effect[:FREE].sum()
    return simplex(np.r_[a[:FREE], 1 - a[:FREE].sum()]), house, theta


def fit(polls, today, kind="previsao_vetor", *, window_start=None, excess=True):
    """Ajuste completo para publicação: parâmetros, casas e trajetória diária."""
    data = _prepare(polls, kind)
    result = estimate(data, excess=excess)
    q, s, phi = _unpack(result.x, excess)
    end = today.toordinal()
    loglik, a, P, path = _run(data, q, s, phi=phi, until=end, record=True)
    pure = excess and estimate(data, excess=False)
    vector, cov = _five(a[:FREE], P[:FREE, :FREE])
    margin, margin_sd = _valid_margin(vector, cov)
    houses = {}
    for i, name in enumerate(data["houses"]):
        block = slice(FREE * (1 + i), FREE * (2 + i))
        effect, effect_cov = _five(a[block], P[block, block])
        effect[-1] = -a[block].sum()
        # Efeito na diferença L−F nos válidos, linearizado no nível final.
        valid = vector[:3].sum()
        grad = np.zeros(len(CATEGORIES))
        grad[0], grad[1] = 100 / valid, -100 / valid
        grad[:3] -= 100 * (vector[0] - vector[1]) / valid**2
        houses[name] = {
            "n_ondas": int((data["h"] == i).sum()),
            "efeito_pp": dict(zip(CATEGORIES, (100 * effect).tolist(), strict=True)),
            "dp_pp": dict(
                zip(
                    CATEGORIES,
                    (100 * np.sqrt(np.maximum(np.diag(effect_cov), 0))).tolist(),
                    strict=True,
                )
            ),
            "efeito_margem_lula_flavio_validos_pp": float(grad @ effect),
            "dp_margem_pp": float(np.sqrt(max(grad @ effect_cov @ grad, 0))),
        }
    trajectory = []
    for day, lvl, cov4, seen in path:
        v, c = _five(lvl, cov4)
        gap, gap_sd = _valid_margin(v, c)
        trajectory.append(
            {
                "data": date.fromordinal(day).isoformat(),
                "vetor_pct": (100 * v).tolist(),
                "dp_pp": (100 * np.sqrt(np.maximum(np.diag(c), 0))).tolist(),
                "margem_flavio_lula_validos_pp": gap,
                "dp_margem_pp": gap_sd,
                "ondas_acumuladas": seen,
            }
        )
    anchor = simplex(vector)
    return {
        "modelo": "Nível local (passeio aleatório) nas cinco categorias, efeitos de casa constantes com soma zero, filtro de Kalman",
        "janela_inicio": window_start,
        "vetor_tipo": kind,
        "categorias": list(CATEGORIES),
        "n_ondas": len(data["rows"]),
        "ondas": [p["id"] for p in data["rows"]],
        "casas": data["houses"],
        "parametros": {
            "q_diario": q,
            "dp_diario_nivel_pp": dict(
                zip(
                    CATEGORIES,
                    (
                        100
                        * np.sqrt(
                            q
                            * np.r_[
                                np.diag(data["shape"]),
                                data["mean"][-1] * (1 - data["mean"][-1]),
                            ]
                        )
                    ).tolist(),
                    strict=True,
                )
            ),
            "dp_casa_pp": dict(zip(CATEGORIES, (100 * s).tolist(), strict=True)),
            "deff": DEFF,
            "phi_variancia_nao_amostral": phi,
            "deff_efetivo": DEFF * phi,
            "phi_estimado": excess,
            "log_verossimilhanca_phi_1": -float(pure.fun) if pure else None,
            "n_teto": N_CAP,
            "dp_nivel_inicial_pp": 100 * PRIOR_SD,
            "piso_variancia_amostral": FLOOR,
            "estimacao": "máxima verossimilhança marginal (L-BFGS-B, três partidas)",
            "otimizador_convergiu": bool(result.success),
            "variancia_observacao": "phi × (diag(p) − pp′) × deff / min(n, 2000)",
            "q_no_limite": bool(
                np.isclose(q, BOUNDS_Q[0], rtol=1e-3)
                or np.isclose(q, BOUNDS_Q[1], rtol=1e-3)
            ),
        },
        "log_verossimilhanca": loglik,
        "estado_final": {
            "data": today.isoformat(),
            "vetor": anchor.tolist(),
            "vetor_bruto": vector.tolist(),
            "dp_pp": (100 * np.sqrt(np.maximum(np.diag(cov), 0))).tolist(),
            "validos_pct": dict(
                zip(
                    CATEGORIES[:3],
                    (100 * anchor[:3] / anchor[:3].sum()).tolist(),
                    strict=True,
                )
            ),
            "margem_flavio_lula_validos_pp": margin,
            "dp_margem_pp": margin_sd,
        },
        "efeitos_casa": houses,
        "trajetoria": trajectory,
        "limites": "Mede o nível de uma casa média da janela. Soma zero dos efeitos de casa é hipótese de identificação; erro comum a todas as casas não é detectável aqui e permanece no Monte Carlo. Hiperparâmetros estimados com dados de 2026, sem urna.",
    }
