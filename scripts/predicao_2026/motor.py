"""Pooling territorial, calibração entrópica e cenários que conservam eleitores."""

from __future__ import annotations

import numpy as np

from .base import GROUPS, UF_REGION, midpoint, normalize, read
from .recencia import STATE_HALF_LIFE, age, decay
from .recencia import weights as temporal_weights
from .tse import ROOT

DEFF = 1.5
HALF_LIFE = STATE_HALF_LIFE
POOL_STRENGTH = 350.0
# Âncora central: recência + inclinação encolhida de 28 dias, projetada a
# 04/10 (validada por origem móvel). O destino central dos indecisos é a
# disponibilidade, resolvida para número no build e gravada em
# central.parametros; aqui fica None para o motor seguir puramente numérico.
DEFAULTS = {
    "base": "central_inclinacao",
    "voto_lula": 0.0,
    "voto_flavio": 0.0,
    "indecisos_validos": 1.0,
    "indecisos_flavio": None,
    "comparecimento_pp": 0.0,
    "branco_nulo_pp": 0.0,
    "diferencial_pp": 0.0,
    "vies_pp": 0.0,
    "secoes_abstencao_pp": 0.0,
    "eleitor_provavel": True,
    "exterior": True,
    "comparecimento_modelo": "uf",
    "regioes": {},
    "ufs": {},
}


def rake(seed, electorate, target, *, tolerance=1e-10):
    """Mínima entropia cruzada sob margens UF e categoria. Positividade explícita."""
    q = np.maximum(np.asarray(seed, float), 1e-9)
    q /= q.sum(axis=1, keepdims=True)
    weights = normalize(electorate)
    t = normalize(target)
    for iteration in range(1000):
        current = weights @ q
        q *= np.divide(t, current, out=np.zeros_like(t), where=current > 0)
        q /= q.sum(axis=1, keepdims=True)
        if np.max(abs(weights @ q - t)) < tolerance:
            return q, iteration + 1
    raise ValueError("Calibração nacional não convergiu")


def softmax(logs, axis=-1):
    e = np.exp(logs - np.max(logs, axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)


def territory(polls, national, tse, today, half_life=STATE_HALF_LIFE):
    hist = {
        u["uf"]: u for u in read(ROOT / "analysis/voto_util/tse_2022_uf.json")["ufs"]
    }
    target = np.array(national["alvos"]["todas"])
    historical = np.array(
        [
            sum(u["t1"][k] for u in hist.values())
            for k in ("lula", "bolsonaro", "validos")
        ],
        float,
    )
    historical[2] -= historical[0] + historical[1]
    historical = normalize(historical)
    target_valid = normalize(target[:3])
    correction = target_valid / historical
    minor_names = ("renan_santos", "cury", "caiado", "zema")
    minor_polls = [
        p
        for p in national["selecionadas"]
        if all(k in p["previsao_opcoes"] for k in minor_names)
    ]
    minor_vectors = []
    for p in minor_polls:
        v = p["previsao_opcoes"]
        named = [max(0, v[k]) for k in minor_names]
        remaining = sum(
            max(0, x)
            for k, x in v.items()
            if k not in (*minor_names, "lula", "flavio", "indecisos", "branco_nulo")
        )
        minor_vectors.append(normalize([*named, remaining]))
    minor_prior = (
        np.average(minor_vectors, axis=0, weights=temporal_weights(minor_polls))
        if minor_vectors
        else normalize([1, 1, 1, 1, 1])
    )
    states = []
    for uf, t in tse["ufs"].items():
        observations = [p for p in polls if p["uf"] == uf]
        if uf == "ZZ":
            h = read(ROOT / "analysis/predicao_2026/tse_2022_exterior.json")["t1"]
            prior_valid = normalize(
                [
                    h["lula"],
                    h["bolsonaro"],
                    h["validos"] - h["lula"] - h["bolsonaro"],
                ]
            )
        else:
            h = hist[uf]["t1"]
            prior_valid = normalize(
                [h["lula"], h["bolsonaro"], h["validos"] - h["lula"] - h["bolsonaro"]]
            )
        prior_valid = normalize(prior_valid * correction)
        prior = np.r_[prior_valid * target[:3].sum(), target[3:]]
        logs = [np.log(np.maximum(prior, 1e-6))]
        corrected_logs = logs.copy()
        weights = [POOL_STRENGTH]
        details, reserves, source_weights = [], [], []
        for p in observations:
            field_age = age(p["campo"], today)
            w = min(p["n"], 1500) / DEFF * decay(field_age, half_life)
            q = np.array(p["vetor"])
            # Atualiza o nível antigo pelo movimento nacional contemporâneo.
            peers = [
                n
                for n in national["pesquisas"]
                if abs(midpoint(n["campo"]) - midpoint(p["campo"])) <= 7
            ]
            by_house = {}
            for n in sorted(
                peers,
                key=lambda n: abs(midpoint(n["campo"]) - midpoint(p["campo"])),
                reverse=True,
            ):
                by_house[n["instituto"]] = n
            contemporaneous = (
                np.average(
                    [n["publicado_vetor"] for n in by_house.values()],
                    axis=0,
                    weights=[
                        decay(
                            abs(midpoint(n["campo"]) - midpoint(p["campo"])),
                            national["meia_vida_dias"],
                        )
                        for n in by_house.values()
                    ],
                )
                if by_house
                else target
            )
            drift = target / np.maximum(contemporaneous, 0.001)
            q = normalize(q * drift)
            logq = np.log(np.maximum(q, 1e-6))
            contrast = (
                national["efeitos_casa"]
                .get(p["instituto"], {})
                .get("contraste", [0, 0, 0])
            )
            corrected = logq.copy()
            corrected[:3] -= contrast
            logs.append(logq)
            corrected_logs.append(corrected)
            weights.append(w)
            reserves.append(p["reserva"])
            source_weights.append(w)
            details.append(
                {
                    **p,
                    "idade_dias": field_age,
                    "peso_recencia": decay(field_age, half_life),
                    "peso_modelo": w,
                    "movimento_nacional": drift.tolist(),
                    "casas_contemporaneas": len(by_house),
                }
            )
        seed = softmax(np.average(logs, axis=0, weights=weights))
        corrected = softmax(np.average(corrected_logs, axis=0, weights=weights))
        signals = [p["comparecimento"] for p in observations if p["comparecimento"]]
        lv = signals[0]["fatores"] if signals else [1, 1, 1]
        reserve = (
            np.average(reserves, axis=0, weights=source_weights).tolist()
            if reserves
            else [0, 0]
        )
        minor_rows, minor_weights = [minor_prior], [POOL_STRENGTH]
        for p in observations:
            # Usa só listas que realmente discriminam os quatro nomes.
            raw = read(ROOT / p["arquivo"])
            if "quaest/" in p["arquivo"]:
                from .base import module

                B = module("voto_util_base")
                vals = B.pres_1t_quaest(raw)["valores"]
            else:
                vals = raw["pres_1t"]["valores"]
            keys = ("Renan", "Cury", "Caiado", "Zema")
            if not all(isinstance(vals.get(k), (int, float)) for k in keys):
                continue
            pieces = [max(0, vals[k]) for k in keys]
            rest = sum(
                max(0, v)
                for k, v in vals.items()
                if k not in (*keys, "Lula", "Flávio", "Indecisos", "Branco/nulo")
                and isinstance(v, (int, float))
            )
            if sum(pieces) + rest:
                minor_rows.append(normalize([*pieces, rest]))
                minor_weights.append(
                    next(
                        d["peso_modelo"]
                        for d in details
                        if d["arquivo"] == p["arquivo"]
                    )
                )
        minor = normalize(np.average(minor_rows, axis=0, weights=minor_weights))
        states.append(
            {
                "uf": uf,
                "regiao": UF_REGION[uf],
                "eleitorado": t["eleitorado"],
                "comparecimento": t["historico_2022"]["comparecimento"]
                / t["historico_2022"]["aptos"],
                "comparecimento_secoes": t["comparecimento_rate"],
                "branco_nulo": t["branco_nulo_rate"],
                "semente": seed.tolist(),
                "semente_casas": corrected.tolist(),
                "eleitor_provavel_fatores": lv,
                "sinal_comparecimento": signals[0] if signals else None,
                "reserva": reserve,
                "n_efetivo_assumido": sum(weights[1:]),
                "peso_prior": weights[0] / sum(weights),
                "pesquisas": details,
                "sem_pesquisa": not observations,
                "tse": t,
            }
        )
        states[-1]["outros_composicao"] = minor.tolist()
        states[-1]["outros_n_fontes"] = len(minor_rows) - 1
    domestic = [s for s in states if s["uf"] != "ZZ"]
    weights = [s["eleitorado"] for s in domestic]
    iterations = {}
    for name, target_vector in national["alvos"].items():
        q, niter = rake([s["semente"] for s in domestic], weights, target_vector)
        iterations[name] = niter
        for s, vector in zip(domestic, q, strict=True):
            s.setdefault("bases", {})[name] = vector.tolist()
    q, niter = rake(
        [s["semente_casas"] for s in domestic], weights, national["alvos"]["inclusivo"]
    )
    iterations["casas"] = niter
    for s, vector in zip(domestic, q, strict=True):
        s["bases"]["casas"] = vector.tolist()
    for s in states:
        if s["uf"] == "ZZ":
            # Exterior sem pesquisa. Mudança nacional já aplicada à prior.
            s["bases"] = dict.fromkeys((*national["alvos"], "casas"), s["semente"])
    minor_q, minor_iterations = rake(
        [s["outros_composicao"] for s in domestic],
        [s["eleitorado"] * s["bases"]["inclusivo"][2] for s in domestic],
        minor_prior,
    )
    for s, vector in zip(domestic, minor_q, strict=True):
        s["outros_composicao"] = vector.tolist()
    iterations["demais_candidatos"] = minor_iterations
    return states, iterations


def attendance_rates(mass, target, differential):
    """Deslocamento mínimo de intercepto; comparecimento total fica fixo."""
    if not -1 <= differential <= 1:
        raise ValueError("Diferencial de comparecimento fora dos limites")
    offsets = np.array([-differential / 2, differential / 2, 0, 0])
    lo, hi = -1.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        rates = np.clip(target + offsets + mid, 0, 1)
        if mass @ rates < target:
            lo = mid
        else:
            hi = mid
    return np.clip(target + offsets + (lo + hi) / 2, 0, 1)


def state_scenario(s, params, *, vector=None, turnout=None):
    p = {**DEFAULTS, **params}
    up = p["ufs"].get(s["uf"], {})
    for k in ("voto_lula", "voto_flavio", "indecisos_validos"):
        if not 0 <= p[k] <= 1:
            raise ValueError(f"{k} precisa estar em [0,1]")
    q = np.array(vector if vector is not None else s["bases"][p["base"]])
    pi = normalize(q[:3])
    if p["eleitor_provavel"]:
        pi = normalize(pi * s["eleitor_provavel_fatores"])
    local_useful = [up.get(k, p[k]) for k in ("voto_lula", "voto_flavio")]
    if not all(0 <= x <= 1 for x in local_useful):
        raise ValueError("Voto útil da UF precisa estar em [0,1]")
    requested = np.array(local_useful) * s["reserva"]
    moved = (
        requested * min(1.0, pi[2] / requested.sum())
        if requested.sum() > 0
        else requested
    )
    pi[:2] += moved
    pi[2] = max(0.0, pi[2] - moved.sum())
    indecisos = q[3] / max(1e-9, 1 - q[4])
    destination = pi.copy()
    if p["indecisos_flavio"] is not None:
        f = p["indecisos_flavio"]
        if not 0 <= f <= 1:
            raise ValueError("Destino dos indecisos fora de [0,1]")
        destination = np.array([1 - f, f, 0.0])
    pi = normalize(
        (1 - indecisos) * pi + indecisos * p["indecisos_validos"] * destination
    )
    bias = p["vies_pp"] / 200  # +2 pp na diferença F-L = +1 F e -1 L.
    transfer = float(np.clip(bias, -pi[1], pi[0]))
    pi[0] -= transfer
    pi[1] += transfer
    rp = p["regioes"].get(s["regiao"], {})
    up = p["ufs"].get(s["uf"], {})
    high = (
        sum(
            b["eleitores_2026"]
            for b in s["tse"]["bins"]
            if b["abstencao_historica_pct"] >= 30
        )
        / s["eleitorado"]
    )
    base_tau = (
        s["comparecimento_secoes"]
        if p["comparecimento_modelo"] == "secoes"
        else s["comparecimento"]
    )
    tau = float(
        np.clip(
            (base_tau if turnout is None else turnout)
            + (
                p["comparecimento_pp"]
                + rp.get("comparecimento_pp", 0)
                + up.get("comparecimento_pp", 0)
                + high * p["secoes_abstencao_pp"]
            )
            / 100,
            0,
            1,
        )
    )
    invalid = float(
        np.clip(
            s["branco_nulo"]
            + (p["branco_nulo_pp"] + up.get("branco_nulo_pp", 0)) / 100,
            0,
            1,
        )
    )
    invalid += (1 - invalid) * indecisos * (1 - p["indecisos_validos"])
    mass = np.r_[pi * (1 - invalid), invalid]
    diff = (p["diferencial_pp"] + up.get("diferencial_pp", 0)) / 100
    rates = attendance_rates(mass, tau, diff) if diff else np.repeat(tau, 4)
    ballots = s["eleitorado"] * mass * rates
    result = {
        "uf": s["uf"],
        "regiao": s["regiao"],
        "eleitorado": s["eleitorado"],
        "lula": float(ballots[0]),
        "flavio": float(ballots[1]),
        "outros": float(ballots[2]),
        "branco_nulo": float(ballots[3]),
        "comparecimento": float(ballots.sum()),
        "abstencao": float(s["eleitorado"] - ballots.sum()),
        "taxas_por_preferencia": rates.tolist(),
        "transferencias": (moved * s["eleitorado"] * tau * (1 - invalid)).tolist(),
    }
    result["demais"] = dict(
        zip(
            ("renan_santos", "cury", "caiado", "zema", "restantes"),
            (ballots[2] * np.array(s["outros_composicao"])).tolist(),
            strict=True,
        )
    )
    return result


def undecided_mix(pi, undecided, share_flavio, valid_share):
    """(1 − u)·π + u·v·destino, normalizado; destino proporcional ou fixo.

    `pi` tem as três parcelas válidas no último eixo; `undecided` é u com a
    forma de pi sem esse eixo (ou escalar). Espelha state_scenario.
    """
    u = np.asarray(undecided, float)[..., None]
    if share_flavio is None:
        destination = pi
    else:
        destination = np.broadcast_to(
            np.array([1 - share_flavio, share_flavio, 0.0]), pi.shape
        )
    mixed = (1 - u) * pi + u * valid_share * destination
    return mixed / mixed.sum(axis=-1, keepdims=True)


def summarize(rows):
    keys = (
        "eleitorado",
        "comparecimento",
        "abstencao",
        "branco_nulo",
        "lula",
        "flavio",
        "outros",
    )
    result = {k: sum(r[k] for r in rows) for k in keys}
    result["validos"] = sum(result[k] for k in GROUPS[:3])
    result["percentuais"] = {
        k: 100 * result[k] / result["validos"] if result["validos"] else 0
        for k in GROUPS[:3]
    }
    result["margem_flavio_lula"] = (
        result["percentuais"]["flavio"] - result["percentuais"]["lula"]
    )
    result["demais"] = {
        k: sum(r["demais"][k] for r in rows)
        for k in ("renan_santos", "cury", "caiado", "zema", "restantes")
    }
    return result


def scenario(states, params=None):
    params = {**DEFAULTS, **(params or {})}
    rows = [
        state_scenario(s, params)
        for s in states
        if params["exterior"] or s["uf"] != "ZZ"
    ]
    regions = {
        name: summarize([r for r in rows if r["regiao"] == name])
        for name in sorted({r["regiao"] for r in rows})
    }
    return {
        "parametros": params,
        "brasil": summarize(rows),
        "regioes": regions,
        "ufs": rows,
    }


# Parâmetros que a simulação reproduz; os demais precisam ficar no default.
SIMULATED = ("base", "indecisos_flavio", "indecisos_validos", "eleitor_provavel")
# Âncoras com extrapolação além do nível: recebem o desvio da projeção.
PROJECTED = ("central_inclinacao", "tendencia")


def bootstrap_design(national, base):
    """Casas, vetor e pesos do bootstrap de cada âncora, e o recentramento.

    Âncoras de modelo calculadas sobre as mesmas casas centrais (dinâmica,
    tendência, central com inclinação) reutilizam o bootstrap da central e são
    recentradas pelo deslocamento alvos[base] − alvos.inclusivo. Espelho exato
    de Prediction2026.simulate.
    """
    paired = base in ("pnad", "publicado")
    polls = national["pareadas"] if paired else national["selecionadas"]
    kind = (
        "pnad_vetor"
        if base == "pnad"
        else "publicado_vetor" if base in ("publicado", "todas") else "previsao_vetor"
    )
    alvos = national["alvos"]
    shift = None
    if kind == "previsao_vetor" and base in alvos and base != "sem_recencia":
        shift = np.asarray(alvos[base], float) - np.asarray(alvos["inclusivo"], float)
    return polls, kind, shift


def projection_sd(national, base):
    """Desvio da projeção na diferença F−L, em pp, para âncoras projetadas."""
    if base not in PROJECTED:
        return 0.0
    return float(national.get("incerteza_projecao_pp", {}).get(base, 0.0))


def target_draws(national, base, runs, rng, common_sd_pp=2.0):
    """Núcleo nacional compartilhado pelos dois turnos; sem sorteios territoriais."""
    ps, kind, shift = bootstrap_design(national, base)
    # Bootstrap Bayesiano por casa + multinomial com n/deff, uma onda por casa.
    sample = np.stack(
        [
            rng.dirichlet(np.maximum(q[kind], 1e-6) * min(q["n"], 2000) / DEFF, runs)
            for q in ps
        ],
        axis=1,
    )
    house_weights = rng.dirichlet(
        len(ps) * temporal_weights(ps, equal=base == "sem_recencia"), runs
    )
    targets = np.einsum("rh,rhk->rk", house_weights, sample)
    if shift is not None:
        targets = np.maximum(targets + shift[None, :], 1e-6)
        targets /= targets.sum(axis=1, keepdims=True)
    # Student t, df=5, escalada para o desvio padrão declarado, em pontos
    # da DIFERENÇA F-L (cada candidato recebe metade com sinal contrário).
    # A incerteza da projeção soma-se em quadratura ao erro comum.
    extra_sd = projection_sd(national, base)
    total_sd = float(np.hypot(common_sd_pp, extra_sd))
    shock = rng.standard_t(5, runs) * np.sqrt(3 / 5) * total_sd / 200
    transfer = np.clip(
        shock * targets[:, :3].sum(axis=1), -targets[:, 1], targets[:, 0]
    )
    targets[:, 0] -= transfer
    targets[:, 1] += transfer
    return targets, extra_sd, total_sd, shift


def simulate(
    states, national, params=None, *, runs=6000, seed=20261003, common_sd_pp=2.0
):
    """Distribuição preditiva condicional. Parâmetros de erro não calibrados em 2026."""
    if runs < 100 or common_sd_pp < 0:
        raise ValueError("Simulação requer ao menos 100 sorteios e erro não negativo")
    p = {**DEFAULTS, **(params or {})}
    unsupported = [k for k in DEFAULTS if k not in SIMULATED and p[k] != DEFAULTS[k]]
    if unsupported:
        raise ValueError(f"Simulação Python não reproduz: {', '.join(unsupported)}")
    base = p["base"]
    f = p["indecisos_flavio"]
    if f is not None and not 0 <= f <= 1:
        raise ValueError("Destino dos indecisos fora de [0,1]")
    if not 0 <= p["indecisos_validos"] <= 1:
        raise ValueError("indecisos_validos precisa estar em [0,1]")
    rng = np.random.default_rng(seed)
    targets, extra_sd, total_sd, shift = target_draws(
        national, base, runs, rng, common_sd_pp
    )
    domestic = [s for s in states if s["uf"] != "ZZ"]
    weights = normalize([s["eleitorado"] for s in domestic])
    q = np.stack(
        [
            rng.dirichlet(
                np.maximum(s["bases"][base], 1e-6) * max(s["n_efetivo_assumido"], 150),
                runs,
            )
            for s in domestic
        ],
        axis=1,
    )
    # Raking simultâneo por réplica: a incerteza de cada UF não cria um
    # segundo conjunto independente de observações do nacional.
    for _ in range(1000):
        current = np.einsum("s,rsk->rk", weights, q)
        q *= (targets / current)[:, None, :]
        q /= q.sum(axis=2, keepdims=True)
        if np.max(abs(np.einsum("s,rsk->rk", weights, q) - targets)) < 1e-8:
            break
    else:
        raise ValueError("Calibração Monte Carlo não convergiu")
    pi = q[:, :, :3].copy()
    if p["eleitor_provavel"]:
        lv = np.array([s["eleitor_provavel_fatores"] for s in domestic])
        pi *= lv[None, :, :]
    pi /= pi.sum(axis=2, keepdims=True)
    region_order = sorted({s["regiao"] for s in domestic})
    r_idx = np.array([region_order.index(s["regiao"]) for s in domestic])
    # Erro de preferência regional permanece após a calibração nacional.
    region_vote = rng.normal(0, 0.01, (runs, len(region_order)))
    d = region_vote[:, r_idx] / 2
    d = np.clip(d, -pi[:, :, 1], pi[:, :, 0])
    pi[:, :, 0] -= d
    pi[:, :, 1] += d
    # Destino dos indecisos, na mesma ordem de state_scenario.
    undecided = q[:, :, 3] / np.maximum(1e-9, 1 - q[:, :, 4])
    pi = undecided_mix(pi, undecided, f, p["indecisos_validos"])
    tau = np.array([s["comparecimento"] for s in domestic])[None, :]
    tau = np.clip(
        tau
        + rng.normal(0, 0.01, (runs, 1))
        + rng.normal(0, 0.015, (runs, len(region_order)))[:, r_idx]
        + rng.normal(0, 0.01, (runs, len(domestic))),
        0,
        1,
    )
    invalid = np.clip(
        np.array([s["branco_nulo"] for s in domestic])[None, :]
        + rng.normal(0, 0.008, (runs, 1)),
        0,
        1,
    )
    invalid = invalid + (1 - invalid) * undecided * (1 - p["indecisos_validos"])
    e = np.array([s["eleitorado"] for s in domestic])
    counts = e[None, :, None] * tau[:, :, None] * (1 - invalid[:, :, None]) * pi
    total = counts.sum(axis=1)
    exterior = next((s for s in states if s["uf"] == "ZZ"), None)
    if exterior:
        xb = np.asarray(exterior["bases"][base], float)
        ep = rng.dirichlet(np.maximum(xb[:3], 1e-6) * 60, runs)
        et = np.clip(exterior["comparecimento"] + rng.normal(0, 0.05, runs), 0, 1)
        if p["eleitor_provavel"]:
            ep = ep * np.asarray(exterior["eleitor_provavel_fatores"], float)
            ep /= ep.sum(axis=1, keepdims=True)
        xu = xb[3] / max(1e-9, 1 - xb[4])
        ep = undecided_mix(ep, xu, f, p["indecisos_validos"])
        xi = exterior["branco_nulo"]
        xi = xi + (1 - xi) * xu * (1 - p["indecisos_validos"])
        total += ep * (exterior["eleitorado"] * et * (1 - xi))[:, None]
    pct = 100 * total / total.sum(axis=1, keepdims=True)
    gap = pct[:, 1] - pct[:, 0]

    def quantiles(x):
        return dict(
            zip(
                ("p05", "p50", "p95"),
                np.quantile(x, [0.05, 0.5, 0.95]).tolist(),
                strict=True,
            )
        )

    return {
        "sorteios": runs,
        "seed": seed,
        "base": base,
        "indecisos_flavio": f,
        "indecisos_validos": p["indecisos_validos"],
        "recentramento_validos_pp": (
            None
            if shift is None
            else dict(zip(GROUPS, (100 * shift).tolist(), strict=True))
        ),
        "erro_comum_sd_pp": common_sd_pp,
        "erro_projecao_sd_pp": extra_sd,
        "erro_comum_total_sd_pp": total_sd,
        "candidatos": {
            k: {"percentual": quantiles(pct[:, i]), "votos": quantiles(total[:, i])}
            for i, k in enumerate(GROUPS[:3])
        },
        "margem": quantiles(gap),
        "p_flavio_a_frente_de_lula": float(np.mean(gap > 0)),
        "p_lula_maioria": float(np.mean(pct[:, 0] > 50)),
        "p_flavio_maioria": float(np.mean(pct[:, 1] > 50)),
        "distribuicao_margem": np.histogram(gap, bins=36)[0].tolist(),
        "limites_histograma": np.histogram(gap, bins=36)[1].tolist(),
        "regioes": {
            name: {
                k: {"votos": quantiles(counts[:, r_idx == j, i].sum(axis=1))}
                for i, k in enumerate(GROUPS[:3])
            }
            for j, name in enumerate(region_order)
        },
    }
