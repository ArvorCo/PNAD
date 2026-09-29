"""Transparent ecological turnout scenarios, never recovered survey microdata.

Construct a maximum-entropy table matching vote x each demographic margin.
Alternative association seeds match the same margins. Change income to PNAD,
keeping age and region margins fixed. Calibrate turnout with one logit intercept.
No turnout probability is fitted to a desired candidate outcome.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, linprog
from scipy.special import expit, logit

ROOT = Path(__file__).resolve().parents[1]
DIMS = ["renda", "idade", "regiao"]
SCORES = {
    "suave": [0.95, 0.80, 0.35, 0.10, 0.50],
    "central": [0.95, 0.65, 0.20, 0.05, 0.50],
    "estrito": [0.95, 0.40, 0.10, 0.01, 0.25],
}


def norm(x):
    x = np.array(x, float)
    return x / x.sum()


def rake(m, targets, axes, tol=1e-11):
    m = np.array(m, float, copy=True)
    for _iteration in range(10000):
        for target, keep in zip(targets, axes, strict=True):
            drop = tuple(i for i in range(m.ndim) if i not in keep)
            cur = m.sum(axis=drop)
            ratio = np.divide(target, cur, out=np.zeros_like(target), where=cur > 0)
            shape = [m.shape[i] if i in keep else 1 for i in range(m.ndim)]
            m *= ratio.reshape(shape)
        error = max(
            np.max(
                abs(
                    m.sum(axis=tuple(i for i in range(m.ndim) if i not in keep))
                    - target
                )
            )
            for target, keep in zip(targets, axes, strict=True)
        )
        if error < tol:
            return m
    raise ValueError(f"Raking failed: {error}")


def joint_table(published, tables, ballot, association=0):
    v = norm(list(published.values()))
    targets = []
    for dim in DIMS:
        t = tables[dim]
        w = norm(t["weights"])
        # Rounded zeros are not structural zeros; epsilon allows compatible balancing.
        seed = np.maximum(np.array(t[ballot], float), 1e-6)
        pair = rake(seed, [w, v], [(0,), (1,)])
        targets.append(pair)
    joint = np.einsum("iv,av,rv,v->iarv", *targets, 1 / v**2)
    if association:
        i, a, r = np.meshgrid(
            np.linspace(-1, 1, 4),
            np.linspace(-1, 1, 4),
            np.linspace(-1, 1, 4),
            indexing="ij",
        )
        joint *= np.exp(association * (i * a + i * r + a * r))[..., None]
        joint = rake(joint, targets, [(0, 3), (1, 3), (2, 3)])
    return joint, targets


def calibrate(log_scores, mass, target):
    offset = brentq(
        lambda b: float((mass * expit(log_scores + b)).sum()) - target, -40, 40
    )
    return expit(log_scores + offset)


def historical():
    path = ROOT / "analysis/voto_util/tse_2022_uf.json"
    data = json.loads(path.read_text())
    assert len(data["ufs"]) == 27 and all(u["uf"] != "ZZ" for u in data["ufs"])
    groups = [["Norte", "Centro-Oeste"], ["Nordeste"], ["Sudeste"], ["Sul"]]
    out = {
        "source": str(path.relative_to(ROOT)),
        "scope": "27 UFs, exterior excluído",
        "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "turns": {},
    }
    for ballot, key in [("1t", "t1"), ("2t", "t2")]:
        rates = []
        current = []
        counts = []
        for names in groups:
            us = [u for u in data["ufs"] if u["regiao"] in names]
            present = sum(u[key]["comparecimento"] for u in us)
            absent = sum(u[key]["abstencao"] for u in us)
            rates.append(present / (present + absent))
            current.append(sum(u["eleitorado_2026"] for u in us))
            counts.append({"comparecimento": present, "abstencao": absent})
        out["turns"][ballot] = {
            "rates": rates,
            "counts": counts,
            "electorate_2026": current,
            "target": float(np.dot(norm(current), rates)),
            "observed_2022": sum(c["comparecimento"] for c in counts)
            / sum(sum(c.values()) for c in counts),
            "urls": [u[key]["fonte"] for u in data["ufs"]],
        }
    return out


def candidate_valid(values):
    values = np.asarray(values, float)
    return (100 * values[:-2] / values[:-2].sum()).tolist()


def scenario(
    joint,
    tables,
    ballot,
    weights,
    target,
    score,
    region_rates=None,
    strength=1,
    older_turnout=None,
):
    pop = rake(joint, [norm(w) for w in weights], [(0,), (1,), (2,)])
    mass = pop.sum(3)
    ls = np.zeros((4, 4, 4))
    for d, dim in enumerate(DIMS):
        rows = np.array(tables[dim]["turnout"], float)
        q = rows @ np.array(score) / rows.sum(1)
        if d == 2 and region_rates is not None:
            q = np.array(region_rates)
        logits = logit(np.clip(q, 0.001, 0.999))
        logits -= np.dot(norm(weights[d]), logits)
        shape = [1, 1, 1]
        shape[d] = 4
        ls += strength * logits.reshape(shape)
    if older_turnout is not None:
        indicator = np.zeros_like(ls)
        indicator[:, 3, :] = 1
        older_mass = mass[:, 3, :].sum()

        def residual(beta):
            rates = calibrate(ls + beta * indicator, mass, target)
            return (
                float((mass[:, 3, :] * rates[:, 3, :]).sum() / older_mass)
                - older_turnout
            )

        beta = brentq(residual, -20, 20)
        ls = ls + beta * indicator
    q = calibrate(ls, mass, target)
    voters = pop * q[..., None]
    before = pop.sum((0, 1, 2))
    after = voters.sum((0, 1, 2))
    segments = {}
    for d, dim in enumerate(DIMS):
        drop = tuple(k for k in range(4) if k != d)
        base = pop.sum(drop)
        present = voters.sum(drop)
        segments[dim] = {
            "turnout": (100 * present / base).tolist(),
            "population_share": (100 * base).tolist(),
            "voter_share": (100 * present / present.sum()).tolist(),
            "absentee_share": (
                100 * (base - present) / (base - present).sum()
            ).tolist(),
        }
    return {
        "target_turnout": 100 * target,
        "achieved_turnout": 100 * float(after.sum()),
        "valid": candidate_valid(after),
        "before_valid": candidate_valid(before),
        "choice_turnout": (after / before).tolist(),
        "population_choice_share": (100 * before).tolist(),
        "share_among_attendees": (100 * after / after.sum()).tolist(),
        "valid_ballots_per_100_electors": 100 * float(after[:-2].sum()),
        "segments": segments,
    }


def frechet_runoff(pair, rates):
    """Sharp bounds of L/(L+F), holding group vote and turnout marginals fixed.

    No sampling error included. Feasible attendance allocations in each income
    group may depend arbitrarily on vote. Linear-fractional optimum by bisection.
    """
    pair = np.asarray(pair, float)
    groups, options = pair.shape
    assert options == 4
    eq = np.zeros((groups, groups * options))
    for i in range(groups):
        eq[i, i * options : (i + 1) * options] = 1
    rhs = pair.sum(1) * np.asarray(rates)
    den = np.tile([1, 1, 0, 0], groups)
    num = np.tile([1, 0, 0, 0], groups)

    def optimum(maximise):
        def f(ratio):
            c = num - ratio * den
            fit = linprog(
                -c if maximise else c,
                A_eq=eq,
                b_eq=rhs,
                bounds=[(0, x) for x in pair.ravel()],
                method="highs",
            )
            if not fit.success:
                raise ValueError(fit.message)
            return float(c @ fit.x)

        return 100 * brentq(f, 0, 1)

    return [optimum(False), optimum(True)]


def analyse(poll, reweight, tables):
    hist = historical()
    central = {}
    age_stress = {}
    scenarios = []
    one_margin = {}
    bounds = None
    proofs = {}
    pn = reweight["renda"]["pnad_pct"]["pessoas16_efetivo"]
    for ballot in ["1t", "2t"]:
        original = [tables[d]["weights"] for d in DIMS]
        weights = [pn, original[1], original[2]]
        h = hist["turns"][ballot]
        joint, targets = joint_table(poll["publicado"][ballot], tables, ballot)
        proofs[ballot] = {
            "max_pair_residual": float(
                max(
                    np.max(
                        abs(
                            joint.sum(tuple(k for k in range(4) if k not in (d, 3))) - t
                        )
                    )
                    for d, t in enumerate(targets)
                )
            ),
            "normalization": float(joint.sum()),
        }
        central[ballot] = scenario(
            joint, tables, ballot, weights, h["target"], SCORES["central"], h["rates"]
        )
        age_stress[ballot] = [
            {
                "older_turnout": rate,
                **scenario(
                    joint,
                    tables,
                    ballot,
                    weights,
                    h["target"],
                    SCORES["central"],
                    h["rates"],
                    older_turnout=rate,
                ),
            }
            for rate in [0.60, 0.70, 0.80]
        ]
        for association in [-1, 0, 1]:
            j, _ = joint_table(poll["publicado"][ballot], tables, ballot, association)
            for total, score_name, region_mode in itertools.product(
                [0.75, h["target"], 0.85], SCORES, ["declarado", "2022"]
            ):
                s = scenario(
                    j,
                    tables,
                    ballot,
                    weights,
                    total,
                    SCORES[score_name],
                    h["rates"] if region_mode == "2022" else None,
                )
                scenarios.append(
                    {
                        "ballot": ballot,
                        "association": association,
                        "score": score_name,
                        "region_mode": region_mode,
                        "target": total,
                        "valid": s["valid"],
                    }
                )
        one_margin[ballot] = {}
        for d, dim in enumerate(DIMS):
            w = norm(weights[d])
            pair = targets[d]
            cond = pair / pair.sum(1)[:, None]
            q = (
                np.array(tables[dim]["turnout"], float)
                @ np.array(SCORES["central"])
                / np.array(tables[dim]["turnout"]).sum(1)
            )
            if dim == "regiao":
                q = np.array(h["rates"])
            q = calibrate(logit(q), w, h["target"])
            votes = (cond * w[:, None] * q[:, None]).sum(0)
            one_margin[ballot][dim] = {
                "valid": candidate_valid(votes),
                "turnout": (100 * q).tolist(),
            }
            if ballot == "2t" and dim == "renda":
                bounds = frechet_runoff(cond * w[:, None], q)
    # Historical-voting columns are direct measurements, not a weighted LV estimate:
    # the PDF omits the sizes and eligibility coding of these three groups.
    history = {
        "page_1t": 23,
        "page_2t": 64,
        "labels": ["Presença nas duas", "Presença em uma", "Abstenção nas duas"],
        "1t": [
            [42, 38, 5, 4, 4, 1, 1, 3, 1],
            [40, 35, 5, 8, 4, 1, 1, 5, 2],
            [38, 27, 9, 3, 7, 0, 2, 9, 4],
        ],
        "2t": [[47, 45, 7, 1], [48, 42, 9, 1], [38, 39, 16, 6]],
        "group_weights": None,
    }
    for ballot in ["1t", "2t"]:
        history[f"{ballot}_valid"] = [candidate_valid(v) for v in history[ballot]]
    envelopes = {
        b: [
            [
                min(s["valid"][i] for s in scenarios if s["ballot"] == b),
                max(s["valid"][i] for s in scenarios if s["ballot"] == b),
            ]
            for i in range(len(central[b]["valid"]))
        ]
        for b in central
    }
    return {
        "central": central,
        "age_stress": age_stress,
        "scenarios": scenarios,
        "envelope": envelopes,
        "one_margin": one_margin,
        "historical": hist,
        "past_voting": history,
        "proofs": proofs,
        "scores": SCORES,
        "income_frechet_lula_runoff": bounds,
        "assumptions": [
            "Matriz sintética de máxima entropia: renda, idade e região independentes condicionalmente ao voto na semente central.",
            "Renda PNAD aplicada preservando margens publicadas de idade e região; isso não recupera os pesos individuais Nexus.",
            "Comparecimento e voto independentes dentro de cada célula sintética; associação não observada pode mudar o resultado.",
            "Probabilidades das cinco respostas são escolhas de cenário, não taxas estimadas ou validadas.",
            "Âncora: taxas regionais TSE 2022 aplicadas ao eleitorado regional 2026, 27 UFs; não previsão de abstenção.",
            "Pergunta de intenção de comparecer refere-se ao primeiro turno; seu uso no segundo é extrapolação explícita.",
            "Faixas de cenários não são intervalos de confiança; não incluem toda a incerteza amostral ou de identificação.",
        ],
    }
