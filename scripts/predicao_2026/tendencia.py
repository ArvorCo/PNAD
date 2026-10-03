"""Modelo dinâmico com tendência local: nível, inclinação e efeitos de casa.

Estado de cada uma das quatro categorias livres (Lula, Flávio, demais e
indecisos; branco/nulo é o complemento): o nível mu e a inclinação beta, em
tempo contínuo,

    d mu   = beta dt + sigma_l dW1
    d beta = -kappa beta dt + sigma_b dW2

Com kappa = 0 e sigma_b > 0 é o passeio aleatório integrado (tendência local);
com sigma_b = 0 e kappa = 0, inclinação constante na janela; com kappa > 0, a
inclinação é amortecida e a projeção converge para um patamar (Gardner e
McKenzie, 1985; Harvey, 1989). As covariâncias de evolução usam a mesma forma
multinomial do DLM de nível, então a soma das cinco partes continua um.

Efeitos de casa, observação, phi e soma zero são os de `dinamico`. A âncora
publicada é o estado PROJETADO para a data da eleição, com a incerteza da
projeção; o nível na data do corte fica registrado para comparação.
"""

from __future__ import annotations

from datetime import date

import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2, norm

from . import dinamico
from .dinamico import CATEGORIES, FREE, PRIOR_SD, _house_cov, _prepare, _valid_margin
from .recencia import midpoint

SLOPE_PRIOR_SD = 0.005  # 0,5 pp por dia: informação fraca sobre a inclinação inicial.
BOUNDS_QL = (1e-9, 1e-3)
BOUNDS_QB = (1e-12, 1e-3)
BOUNDS_KAPPA = (1e-3, 2.0)
BOUNDS_S = dinamico.BOUNDS_S
BOUNDS_PHI = dinamico.BOUNDS_PHI
# Variantes: inclinação constante, passeio integrado e inclinação amortecida.
VARIANTS = {
    "constante": {"slope_noise": False, "damped": False},
    "integrada": {"slope_noise": True, "damped": False},
    "amortecida": {"slope_noise": True, "damped": True},
}
MAIN = "amortecida"
STARTS = (
    (1e-5, 1e-7, 0.1, 0.015, 2.0),
    (1e-6, 1e-8, 0.3, 0.03, 4.0),
    (1e-4, 1e-6, 0.03, 0.008, 1.0),
)


def transition(dt, q_level, q_slope, kappa):
    """Transição exata (g, e) e covariância 2×2 de evolução para um passo dt.

    g = (1 − e^(−kappa dt)) / kappa, e = e^(−kappa dt). As integrais usam série
    de Taylor quando kappa·dt é pequeno, para não perder precisão no limite
    kappa → 0 (passeio integrado: dt³/3, dt²/2, dt).
    """
    dt = float(dt)
    if dt <= 0:
        return 0.0, 1.0, np.zeros((2, 2))
    x = kappa * dt
    if x < 1e-3:
        g = dt * (1 - x / 2 + x * x / 6)
        e = np.exp(-x)
        i11 = dt**3 * (1 / 3 - x / 4 + 7 * x * x / 60)
        i12 = dt**2 * (1 / 2 - x / 2 + 7 * x * x / 24)
        i22 = dt * (1 - x + 2 * x * x / 3)
    else:
        e1, e2 = -np.expm1(-x), -np.expm1(-2 * x)
        g, e = e1 / kappa, 1 - e1
        i11 = (dt - 2 * e1 / kappa + e2 / (2 * kappa)) / kappa**2
        i12 = (e1 - e2 / 2) / kappa**2
        i22 = e2 / (2 * kappa)
    m = q_slope * np.array([[i11, i12], [i12, i22]])
    m[0, 0] += q_level * dt
    return g, e, m


def _advance(a, P, dt, par, shape):
    g, e, m = transition(dt, par["q_level"], par["q_slope"], par["kappa"])
    if dt <= 0:
        return a, P
    a = a.copy()
    a[:FREE] = a[:FREE] + g * a[FREE : 2 * FREE]
    a[FREE : 2 * FREE] *= e
    T = np.eye(2 * FREE)
    T[:FREE, FREE : 2 * FREE] = g * np.eye(FREE)
    T[FREE:, FREE:] = e * np.eye(FREE)
    P = P.copy()
    # O BLAS do macOS sinaliza exceções espúrias em matmul; a finitude é
    # conferida no fim do filtro.
    with np.errstate(all="ignore"):
        P[: 2 * FREE, :] = T @ P[: 2 * FREE, :]
        P[:, : 2 * FREE] = P[:, : 2 * FREE] @ T.T
    P[: 2 * FREE, : 2 * FREE] += np.kron(m, shape)
    return a, (P + P.T) / 2


def _init(data):
    H = len(data["houses"])
    dim = 2 * FREE + FREE * H
    a = np.zeros(dim)
    a[:FREE] = data["mean"][:FREE]
    P = np.zeros((dim, dim))
    P[:FREE, :FREE] = np.eye(FREE) * PRIOR_SD**2
    P[FREE : 2 * FREE, FREE : 2 * FREE] = np.eye(FREE) * SLOPE_PRIOR_SD**2
    return a, P, H


def run(data, par, *, record=None):
    """Filtro de Kalman. Devolve log-verossimilhança, estado no último campo e
    estados diários pedidos em `record` (ordinais)."""
    a, P, H = _init(data)
    P[2 * FREE :, 2 * FREE :] = np.kron(np.eye(H) - 1 / H, _house_cov(par["s"]))
    shape = data["shape"]
    t = data["t"]
    events = [(ti, 0, i) for i, ti in enumerate(t)]
    events += [(float(d), 1, d) for d in record or ()]
    events.sort()
    time, loglik, path = t[0], 0.0, []
    with np.errstate(all="ignore"):
        for when, kind, ident in events:
            if when > time:
                a, P = _advance(a, P, when - time, par, shape)
                time = when
            if kind == 1:
                path.append((ident, a[: 2 * FREE].copy(), P[: 2 * FREE, : 2 * FREE]))
                continue
            lo = 2 * FREE + FREE * data["h"][ident]
            block = slice(lo, lo + FREE)
            innovation = data["y"][ident] - a[:FREE] - a[block]
            PZ = P[:, :FREE] + P[:, block]
            F = PZ[:FREE] + PZ[block] + par["phi"] * data["R"][ident]
            chol = np.linalg.cholesky(F)
            solved = np.linalg.solve(chol, innovation)
            loglik -= 0.5 * (
                2 * np.log(np.diag(chol)).sum()
                + solved @ solved
                + FREE * np.log(2 * np.pi)
            )
            gain = np.linalg.solve(F, PZ.T).T
            a = a + gain @ innovation
            P = P - gain @ PZ.T
            P = (P + P.T) / 2
    if not (np.isfinite(loglik) and np.isfinite(a).all() and np.isfinite(P).all()):
        raise np.linalg.LinAlgError("Filtro de Kalman não finito")
    return loglik, a, P, time, path


def _unpack(theta, variant):
    spec = VARIANTS[variant]
    i = 0
    q_level = float(np.exp(theta[i]))
    i += 1
    q_slope = 0.0
    if spec["slope_noise"]:
        q_slope = float(np.exp(theta[i]))
        i += 1
    kappa = 0.0
    if spec["damped"]:
        kappa = float(np.exp(theta[i]))
        i += 1
    s = np.exp(theta[i : i + len(CATEGORIES)])
    phi = float(np.exp(theta[-1]))
    return {"q_level": q_level, "q_slope": q_slope, "kappa": kappa, "s": s, "phi": phi}


def _bounds(variant):
    spec = VARIANTS[variant]
    out = [tuple(np.log(BOUNDS_QL))]
    if spec["slope_noise"]:
        out.append(tuple(np.log(BOUNDS_QB)))
    if spec["damped"]:
        out.append(tuple(np.log(BOUNDS_KAPPA)))
    out += [tuple(np.log(BOUNDS_S))] * len(CATEGORIES)
    out.append(tuple(np.log(BOUNDS_PHI)))
    return out


def _start(variant, ql, qb, kappa, s, phi):
    spec = VARIANTS[variant]
    x = [np.log(ql)]
    if spec["slope_noise"]:
        x.append(np.log(qb))
    if spec["damped"]:
        x.append(np.log(kappa))
    return np.r_[x, np.full(len(CATEGORIES), np.log(s)), np.log(phi)]


def estimate(data, variant=MAIN, *, start=None):
    """Máxima verossimilhança marginal (L-BFGS-B, várias partidas)."""
    bounds = _bounds(variant)

    def objective(theta):
        try:
            value = -run(data, _unpack(theta, variant))[0]
        except np.linalg.LinAlgError:
            return 1e12
        return value if np.isfinite(value) else 1e12

    starts = [_start(variant, *x) for x in STARTS]
    if start is not None:
        # Partida quente (validação) somada às padrão: a verossimilhança tem
        # um modo degenerado (kappa no teto, inclinação que some em horas) e
        # a partida quente sozinha fica presa nele.
        starts.insert(0, np.clip(start, *np.array(bounds).T))
    best = None
    for x0 in starts:
        result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)
        if best is None or result.fun < best.fun:
            best = result
    if best is None:
        raise ValueError("Estimação da tendência sem ponto de partida")
    return best


def project(a, P, time, target, par, shape):
    """Estado (nível e inclinação) projetado de `time` até o ordinal `target`."""
    return _advance(a, P, max(0.0, target - time), par, shape)


def _five(level4, cov4):
    return dinamico._five(level4, cov4)


def _summary(level4, cov4):
    vector, cov = _five(level4, cov4)
    anchor = dinamico.simplex(vector)
    margin, margin_sd = _valid_margin(vector, cov)
    valid = anchor[:3] / anchor[:3].sum()
    return {
        "vetor": anchor.tolist(),
        "vetor_bruto": vector.tolist(),
        "dp_pp": (100 * np.sqrt(np.maximum(np.diag(cov), 0))).tolist(),
        "validos_pct": dict(zip(CATEGORIES[:3], (100 * valid).tolist(), strict=True)),
        "margem_flavio_lula_validos_pp": margin,
        "dp_margem_pp": margin_sd,
    }


def _slopes(a, P):
    """Inclinações em pp por dia, nas cinco categorias e nos válidos."""
    level, slope = a[:FREE], a[FREE : 2 * FREE]
    vec, _ = _five(level, P[:FREE, :FREE])
    lift = np.vstack([np.eye(FREE), -np.ones(FREE)])
    s5 = lift @ slope
    c5 = lift @ P[FREE : 2 * FREE, FREE : 2 * FREE] @ lift.T
    # Válidos: derivada de x_k / (x_1 + x_2 + x_3) ao longo da inclinação.
    v = vec[:3].sum()
    J = np.zeros((3, len(CATEGORIES)))
    for k in range(3):
        J[k, :3] = -vec[k] / v**2
        J[k, k] += 1 / v
    sv, cv = J @ s5, J @ c5 @ J.T
    return {
        "pp_dia": dict(zip(CATEGORIES, (100 * s5).tolist(), strict=True)),
        "dp_pp_dia": dict(
            zip(
                CATEGORIES,
                (100 * np.sqrt(np.maximum(np.diag(c5), 0))).tolist(),
                strict=True,
            )
        ),
        "validos_pp_dia": dict(zip(CATEGORIES[:3], (100 * sv).tolist(), strict=True)),
        "validos_dp_pp_dia": dict(
            zip(
                CATEGORIES[:3],
                (100 * np.sqrt(np.maximum(np.diag(cv), 0))).tolist(),
                strict=True,
            )
        ),
    }


def filtered(polls, kind="previsao_vetor", *, variant=MAIN, start=None):
    """Estado filtrado no último campo e parâmetros; usado na validação."""
    data = _prepare(polls, kind)
    theta = estimate(data, variant, start=start).x
    par = _unpack(theta, variant)
    _, a, P, time, _ = run(data, par)
    return {"a": a, "P": P, "time": time, "par": par, "shape": data["shape"]}, theta


def vector_at(state, target):
    """Vetor de cinco partes projetado até o ordinal `target` (sem voltar no tempo)."""
    a, _ = project(
        state["a"], state["P"], state["time"], target, state["par"], state["shape"]
    )
    return dinamico.simplex(np.r_[a[:FREE], 1 - a[:FREE].sum()])


def _parameters(par, data, result, variant):
    var_shape = np.r_[np.diag(data["shape"]), data["mean"][-1] * (1 - data["mean"][-1])]
    return {
        "variante": variant,
        "q_nivel": par["q_level"],
        "q_inclinacao": par["q_slope"],
        "kappa_amortecimento_dia": par["kappa"],
        "meia_vida_inclinacao_dias": (
            float(np.log(2) / par["kappa"]) if par["kappa"] > 0 else None
        ),
        "dp_diario_nivel_pp": dict(
            zip(
                CATEGORIES,
                (100 * np.sqrt(par["q_level"] * var_shape)).tolist(),
                strict=True,
            )
        ),
        "dp_diario_inclinacao_pp_dia": dict(
            zip(
                CATEGORIES,
                (100 * np.sqrt(par["q_slope"] * var_shape)).tolist(),
                strict=True,
            )
        ),
        "dp_casa_pp": dict(zip(CATEGORIES, (100 * par["s"]).tolist(), strict=True)),
        "phi_variancia_nao_amostral": par["phi"],
        "deff": dinamico.DEFF,
        "dp_inclinacao_inicial_pp_dia": 100 * SLOPE_PRIOR_SD,
        "dp_nivel_inicial_pp": 100 * PRIOR_SD,
        "otimizador_convergiu": bool(result.success),
        "no_limite": {
            "q_inclinacao_inferior": bool(
                VARIANTS[variant]["slope_noise"]
                and np.isclose(par["q_slope"], BOUNDS_QB[0], rtol=1e-2)
            ),
            "kappa_inferior": bool(
                VARIANTS[variant]["damped"]
                and np.isclose(par["kappa"], BOUNDS_KAPPA[0], rtol=1e-2)
            ),
            "kappa_superior": bool(
                VARIANTS[variant]["damped"]
                and np.isclose(par["kappa"], BOUNDS_KAPPA[1], rtol=1e-2)
            ),
        },
    }


def fit_variant(polls, today, election, kind="previsao_vetor", variant=MAIN):
    data = _prepare(polls, kind)
    result = estimate(data, variant)
    par = _unpack(result.x, variant)
    days = range(int(np.ceil(data["t"][0])), today.toordinal() + 1)
    loglik, a, P, time, _ = run(data, par)
    path = run(data, par, record=days)[-1]
    cut_a, cut_P = project(a, P, time, today.toordinal(), par, data["shape"])
    proj_a, proj_P = project(a, P, time, election.toordinal(), par, data["shape"])
    k = len(result.x)
    return {
        "data": data,
        "par": par,
        "result": result,
        "loglik": loglik,
        "aic": 2 * k - 2 * loglik,
        "k": k,
        "ultimo": (a, P, time),
        "corte": (cut_a, cut_P),
        "projetado": (proj_a, proj_P),
        "path": path,
    }


def fit(
    polls, today, election, kind="previsao_vetor", *, window_start=None, level_fit=None
):
    """Ajuste completo para publicação, com as três variantes e o diagnóstico."""
    fits = {name: fit_variant(polls, today, election, kind, name) for name in VARIANTS}
    main = fits[MAIN]
    data, par = main["data"], main["par"]
    a, P, time = main["ultimo"]
    horizon = election.toordinal() - time
    trajectory = []
    for day, state, cov in main["path"]:
        v, c = _five(state[:FREE], cov[:FREE, :FREE])
        gap, gap_sd = _valid_margin(v, c)
        sl = _slopes(state, cov)
        trajectory.append(
            {
                "data": date.fromordinal(day).isoformat(),
                "vetor_pct": (100 * v).tolist(),
                "margem_flavio_lula_validos_pp": gap,
                "dp_margem_pp": gap_sd,
                "inclinacao_validos_pp_dia": sl["validos_pp_dia"],
                "inclinacao_validos_dp_pp_dia": sl["validos_dp_pp_dia"],
            }
        )
    comparison = {
        name: {
            "log_verossimilhanca": float(f["loglik"]),
            "aic": float(f["aic"]),
            "parametros_livres": f["k"],
            "projetado_validos_pct": _summary(*_level(f["projetado"]))["validos_pct"],
            "margem_projetada_pp": float(
                _summary(*_level(f["projetado"]))["margem_flavio_lula_validos_pp"]
            ),
            "inclinacao_validos_pp_dia": _slopes(*f["ultimo"][:2])["validos_pp_dia"],
            "q_inclinacao": f["par"]["q_slope"],
            "kappa": f["par"]["kappa"],
            "phi": f["par"]["phi"],
        }
        for name, f in fits.items()
    }
    if level_fit is not None:
        comparison["nivel_dlm"] = {
            "log_verossimilhanca": level_fit["log_verossimilhanca"],
            "aic": 2 * 7 - 2 * level_fit["log_verossimilhanca"],
            "parametros_livres": 7,
            "projetado_validos_pct": level_fit["estado_final"]["validos_pct"],
            "margem_projetada_pp": level_fit["estado_final"][
                "margem_flavio_lula_validos_pp"
            ],
            "inclinacao_validos_pp_dia": dict.fromkeys(CATEGORIES[:3], 0.0),
            "phi": level_fit["parametros"]["phi_variancia_nao_amostral"],
        }
    acceleration = {
        "janela_completa": {
            "inicio": window_start,
            **acceleration_test(
                fits["constante"]["loglik"], fits["integrada"]["loglik"]
            ),
            "rv_amortecida_contra_nivel": (
                None
                if level_fit is None
                else max(0.0, 2 * (main["loglik"] - level_fit["log_verossimilhanca"]))
            ),
        },
    }
    cut = today.toordinal()
    recent = [p for p in polls if midpoint(p["campo"]) > cut - 28]
    if len(recent) >= 6:
        const = fit_variant(recent, today, election, kind, "constante")
        integ = fit_variant(recent, today, election, kind, "integrada")
        acceleration["ultimos_28_dias"] = {
            "n_ondas": len(recent),
            **acceleration_test(const["loglik"], integ["loglik"]),
            "inclinacao_constante_validos_pp_dia": _slopes(*const["ultimo"][:2])[
                "validos_pp_dia"
            ],
        }
    acceleration["quadratica_efeitos_fixos"] = {
        str(days): fe_regression(polls, today, days, kind, quadratic=True)
        for days in (28, 14)
    }
    acceleration["inclinacao_por_metade_28d"] = piecewise(polls, today, 28, kind)
    return {
        "modelo": "Tendência local amortecida nas cinco categorias (nível e inclinação em tempo contínuo, inclinação Ornstein-Uhlenbeck), efeitos de casa constantes com soma zero, filtro de Kalman",
        "escolha": "Variante principal: inclinação amortecida. A projeção de 1 a 3 dias quase não depende do amortecimento, mas ele impede que uma inclinação estimada com ruído seja extrapolada sem freio; com kappa no limite inferior a variante coincide com o passeio integrado. A escolha é declarada antes da validação e as três variantes ficam registradas.",
        "janela_inicio": window_start,
        "vetor_tipo": kind,
        "categorias": list(CATEGORIES),
        "n_ondas": len(data["rows"]),
        "casas": data["houses"],
        "parametros": _parameters(par, data, main["result"], MAIN),
        "log_verossimilhanca": float(main["loglik"]),
        "ultimo_campo": {
            "data_ponto_medio": date.fromordinal(int(np.floor(time))).isoformat(),
            "ordinal": time,
            **_summary(a[:FREE], P[:FREE, :FREE]),
        },
        "estado_corte": {"data": today.isoformat(), **_summary(*_level(main["corte"]))},
        "estado_projetado": {
            "data": election.isoformat(),
            "horizonte_dias_desde_ultimo_campo": horizon,
            "horizonte_dias_desde_corte": election.toordinal() - today.toordinal(),
            **_summary(*_level(main["projetado"])),
        },
        "inclinacoes": _slopes(a, P),
        "comparacao_modelos": comparison,
        "regressao_efeitos_fixos": {
            str(days): fe_regression(polls, today, days, kind) for days in (28, 14)
        },
        "aceleracao": acceleration,
        "trajetoria": trajectory,
        "limites": "Inclinação é tendência das pesquisas, não da urna. Projeção curta (dias) com incerteza crescente no horizonte; soma zero dos efeitos de casa continua a hipótese de identificação; erro comum a todas as casas fica no Monte Carlo.",
    }


def _level(state):
    a, P = state
    return a[:FREE], P[:FREE, :FREE]


def acceleration_test(constant, integrated):
    """Razão de verossimilhança: inclinação constante contra inclinação que muda.

    H0: variância da inclinação zero (fronteira). A distribuição nula é a
    mistura 50:50 de qui-quadrado com 0 e 1 grau (Self e Liang, 1987).
    """
    stat = float(max(0.0, 2 * (integrated - constant)))
    p = float(0.5 * chi2.sf(stat, 1)) if stat > 0 else 1.0
    return {
        "estatistica_rv": stat,
        "p_valor_mistura_chi2": p,
        "nula": "inclinação constante na janela (variância de evolução da inclinação igual a zero)",
        "leitura": (
            "inclinação muda ao longo da janela (p < 0,05)"
            if p < 0.05
            else "mudança de inclinação não identificável (p ≥ 0,05)"
        ),
    }


# Regressões de efeitos fixos de casa, nos votos válidos.


def _valid_rows(polls, kind):
    y = np.array([np.asarray(p[kind][:3], float) for p in polls])
    return 100 * y / y.sum(axis=1, keepdims=True)


WINDOW_RULES = {
    "ponto_medio": lambda p: midpoint(p["campo"]),
    "fim_do_campo": lambda p: date.fromisoformat(p["campo"]["fim"]).toordinal(),
    "divulgacao": lambda p: date.fromisoformat(p["divulgacao"]).toordinal(),
}


def fe_regression(
    polls, today, days, kind="previsao_vetor", *, quadratic=False, rule="ponto_medio"
):
    """Mínimos quadrados ponderados com efeito fixo de casa e tendência linear
    (ou quadrática) por categoria dos válidos. Peso min(n, 2000); variância
    residual estimada (inclui erro não amostral); erro-padrão também robusto
    por casa (CR1). `rule` define que data da onda entra na janela; o tempo
    da regressão é sempre o ponto médio do campo."""
    cut = today.toordinal()
    rows = [p for p in polls if WINDOW_RULES[rule](p) > cut - days]
    houses = sorted({p["instituto"] for p in rows})
    t = np.array([midpoint(p["campo"]) - cut for p in rows])
    tc = t - t.mean()
    cols = [tc] + ([tc**2 - (tc**2).mean()] if quadratic else [])
    D = [[1.0 if p["instituto"] == h else 0.0 for p in rows] for h in houses]
    X = np.column_stack(cols + D)
    w = np.array([min(p["n"], dinamico.N_CAP) for p in rows], float)
    Y = _valid_rows(rows, kind)
    n, k = X.shape
    dof = n - k
    if dof < 3:
        raise ValueError("Graus de liberdade insuficientes na regressão")
    with np.errstate(all="ignore"):
        XtWX = X.T @ (w[:, None] * X)
        inv = np.linalg.inv(XtWX)
        B = inv @ X.T @ (w[:, None] * Y)
        resid = Y - X @ B
    out = {}
    hidx = np.array([houses.index(p["instituto"]) for p in rows])
    G = len(houses)
    for j, name in enumerate(CATEGORIES[:3]):
        r = resid[:, j]
        s2 = float((w * r**2).sum() / dof)
        cov = s2 * inv
        meat = np.zeros((k, k))
        with np.errstate(all="ignore"):
            for g in range(G):
                m = hidx == g
                u = (X[m] * (w[m] * r[m])[:, None]).sum(axis=0)
                meat += np.outer(u, u)
            robust = inv @ meat @ inv * G / (G - 1) * (n - 1) / dof
        entry = {
            "inclinacao_pp_dia": float(B[0, j]),
            "ep": float(np.sqrt(cov[0, 0])),
            "ep_robusto_casa": float(np.sqrt(max(robust[0, 0], 0))),
        }
        if quadratic:
            # Aceleração = segunda derivada = 2 × coeficiente do termo quadrático.
            entry["aceleracao_pp_dia2"] = float(2 * B[1, j])
            entry["ep_aceleracao"] = float(2 * np.sqrt(cov[1, 1]))
            entry["ep_aceleracao_robusto_casa"] = float(
                2 * np.sqrt(max(robust[1, 1], 0))
            )
            entry["z_aceleracao"] = entry["aceleracao_pp_dia2"] / entry["ep_aceleracao"]
            entry["p_aceleracao"] = float(2 * norm.sf(abs(entry["z_aceleracao"])))
        out[name] = entry
    lo, fl = (out[k]["inclinacao_pp_dia"] for k in CATEGORIES[:2])
    # Divisão da queda da terceira via: fração de Flávio no ganho conjunto.
    # Erro-padrão pelo método delta com a covariância conjunta das inclinações.
    cov_lf = _joint_slope_cov(X, w, resid, inv, dof)
    gain = lo + fl
    grad = np.array([-fl / gain**2, lo / gain**2])
    share_se = float(np.sqrt(max(grad @ cov_lf @ grad, 0)))
    return {
        "janela_dias": days,
        "regra_janela": rule,
        "n_ondas": n,
        "n_casas": G,
        "graus_liberdade": dof,
        "quadratica": quadratic,
        "categorias": out,
        "fracao_flavio_do_ganho": fl / gain if gain else None,
        "fracao_flavio_dp": share_se,
        "cov_inclinacao_lula_flavio": cov_lf.tolist(),
        "nota": "Válidos = Lula + Flávio + demais. Tendência centrada no ponto médio da janela; peso min(n, 2000) por onda e variância residual estimada, que inclui o erro não amostral.",
    }


def _joint_slope_cov(X, w, resid, inv, dof):
    """Covariância das inclinações de Lula e Flávio na mesma regressão."""
    r = resid[:, :2]
    S = (r * w[:, None]).T @ r / dof
    return S * inv[0, 0]


def piecewise(polls, today, days=28, kind="previsao_vetor"):
    """Inclinação na primeira e na segunda metade da janela, mesmo efeito de casa."""
    cut = today.toordinal()
    rows = [p for p in polls if midpoint(p["campo"]) > cut - days]
    houses = sorted({p["instituto"] for p in rows})
    t = np.array([midpoint(p["campo"]) - cut for p in rows])
    knot = -days / 2
    early = np.minimum(t - knot, 0)
    late = np.maximum(t - knot, 0)
    D = [[1.0 if p["instituto"] == h else 0.0 for p in rows] for h in houses]
    X = np.column_stack([early, late, *D])
    w = np.array([min(p["n"], dinamico.N_CAP) for p in rows], float)
    Y = _valid_rows(rows, kind)
    n, k = X.shape
    dof = n - k
    with np.errstate(all="ignore"):
        inv = np.linalg.inv(X.T @ (w[:, None] * X))
        B = inv @ X.T @ (w[:, None] * Y)
        resid = Y - X @ B
    out = {}
    for j, name in enumerate(CATEGORIES[:3]):
        s2 = float((w * resid[:, j] ** 2).sum() / dof)
        cov = s2 * inv
        diff = B[1, j] - B[0, j]
        se = float(np.sqrt(max(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1], 0)))
        out[name] = {
            "primeira_metade_pp_dia": float(B[0, j]),
            "ep_primeira": float(np.sqrt(cov[0, 0])),
            "segunda_metade_pp_dia": float(B[1, j]),
            "ep_segunda": float(np.sqrt(cov[1, 1])),
            "mudanca_pp_dia": float(diff),
            "ep_mudanca": se,
            "p_mudanca": float(2 * norm.sf(abs(diff) / se)) if se > 0 else None,
        }
    return {
        "janela_dias": days,
        "corte_meio": date.fromordinal(int(cut + knot)).isoformat(),
        "n_ondas": n,
        "graus_liberdade": dof,
        "categorias": out,
    }


def shrunk_slopes(polls, today, days, kind="previsao_vetor"):
    """Inclinações dos válidos (pp/dia) da regressão de efeitos fixos, encolhidas
    para zero pelo fator b² / (b² + ep²): uma inclinação com t = 1 vale metade,
    com t = 3 vale 90%. Sem graus de liberdade, inclinação zero."""
    try:
        fitted = fe_regression(polls, today, days, kind)
    except (ValueError, np.linalg.LinAlgError):
        return np.zeros(3), None
    out = []
    for name in CATEGORIES[:3]:
        c = fitted["categorias"][name]
        b, se = c["inclinacao_pp_dia"], c["ep"]
        out.append(b * b * b / (b * b + se * se) if b else 0.0)
    return np.array(out), fitted


def shift_valid(vector, slopes_pp, horizon):
    """Desloca as parcelas dos válidos por inclinação × horizonte, preservando a
    massa válida e as demais categorias; trunca negativos e renormaliza."""
    v = np.asarray(vector, float).copy()
    mass = v[:3].sum()
    shares = 100 * v[:3] / mass + np.asarray(slopes_pp, float) * max(0.0, horizon)
    shares = np.maximum(shares, 0)
    v[:3] = mass * shares / shares.sum()
    return v
