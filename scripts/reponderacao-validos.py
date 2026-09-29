"""Current conditional valid-vote forecast; no backdating of the turnout template."""

import csv
import hashlib
import importlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
WINDOW = importlib.import_module("reponderacao-janela")
SCENARIO = "pessoas16_efetivo"
NONCHOICE = {"branco_nulo", "indecisos", "nao_sabe", "nenhum", "nao_vai_votar"}
KEYS = ["lula", "flavio", "cury", "caiado", "renan_santos", "zema", "demais"]
LABELS = dict(
    zip(
        KEYS,
        [
            "Lula",
            "Flávio",
            "Cury",
            "Caiado",
            "Renan Santos",
            "Zema",
            "Demais candidatos",
        ],
        strict=True,
    )
)
MODES = {
    "publicado": "Publicado em válidos",
    "pnad": "PNAD em válidos",
    "modelo": "PNAD + comparecimento",
}
SCENARIOS = {
    "central": "Comparecimento central",
    "idosos60": "Presença de 60+ em 60%",
    "idosos80": "Presença de 60+ em 80%",
    "flavio95": "Presença relativa de Flávio: −5%",
    "flavio105": "Presença relativa de Flávio: +5%",
}


def normalize(values):
    total = sum(values.values())
    if total <= 0 or any(v < 0 for v in values.values()):
        raise ValueError("Invalid vote mass")
    return {k: 100 * v / total for k, v in values.items()}


def allocate(candidates, rates, undecided=0, undecided_rate=1):
    """Expected attendees, then proportional undecided allocation, then valid votes."""
    if undecided < 0 or not 0 <= undecided_rate <= 1:
        raise ValueError("Invalid undecided mass or rate")
    if any(v < 0 for v in candidates.values()) or any(
        not 0 <= rates[k] <= 1 for k in candidates
    ):
        raise ValueError("Invalid candidate mass or turnout rate")
    attending = {k: v * rates[k] for k, v in candidates.items()}
    valid = normalize(attending)
    added = {k: undecided * undecided_rate * v / 100 for k, v in valid.items()}
    final = normalize({k: attending[k] + added[k] for k in attending})
    return {"valid": final, "attending": attending, "allocated": added}


def prepare(poll, ballot):
    if ballot not in poll.get("turnos", {}):
        raise ValueError(
            poll.get("motivo") or "Sem cruzamento de renda deste turno na última onda"
        )
    turn = poll["turnos"][ballot]
    original = poll["publicado"][ballot]
    published = turn["publicado"]
    adjusted = turn["cenarios"][SCENARIO]["ajustado"]
    candidates = set(published) - NONCHOICE
    missing = {
        k for k, v in original.items() if k not in candidates | NONCHOICE and v > 0
    }
    if missing:
        raise ValueError(
            "Candidatos positivos sem cruzamento: " + ", ".join(sorted(missing))
        )
    if not {"lula", "flavio"} <= candidates or "marcal" in candidates:
        raise ValueError("Cédula incompatível")
    if ballot == "2t" and candidates != {"lula", "flavio"}:
        raise ValueError("Segundo turno não binário")
    negatives = {k: adjusted[k] for k in sorted(candidates) if adjusted[k] < 0}
    # An anchored delta can put rounded zero candidates below zero. Remove that
    # nonphysical mass explicitly, before the valid-vote normalization.
    return {
        "id": poll["id"],
        "instituto": poll["instituto"],
        "divulgacao": poll["divulgacao"],
        "campo": poll["campo"],
        "published": {k: published[k] for k in sorted(candidates)},
        "adjusted": {k: max(0, adjusted[k]) for k in sorted(candidates)},
        "negative_mass_removed": negatives,
        "undecided": max(0, adjusted.get("indecisos", adjusted.get("nao_sabe", 0))),
        "undecided_known": "indecisos" in adjusted or "nao_sabe" in adjusted,
        "source": poll["fonte"],
    }


def group(values, ballot, keys=None):
    keys = keys or (KEYS if ballot == "1t" else KEYS[:2])
    out = dict.fromkeys(keys, 0.0)
    for k, v in values.items():
        out[k if k in out else "demais"] += v
    return out


def average(rows, field, ballot, keys=None):
    if keys is None:
        shared = set.intersection(*(set(r[field]) for r in rows))
        keys = [k for k in KEYS[:-1] if k in shared] + (
            ["demais"] if ballot == "1t" else []
        )
    return {
        k: sum(group(r[field], ballot, keys)[k] for r in rows) / len(rows) for k in keys
    }


def candidate_rates(row, nexus, ballot, rates):
    """An aggregate Others must use the same aggregate in the source template."""
    q = {k: rates.get(k, rates.get("outros")) for k in row["adjusted"]}
    pooled = []
    if "outros" in q:
        pooled = [
            k
            for k in rates
            if k not in NONCHOICE and (k == "outros" or k not in row["adjusted"])
        ]
        shares = dict(
            zip(
                nexus["poll"]["publicado"][ballot],
                nexus["turnout"]["central"][ballot]["population_choice_share"],
                strict=True,
            )
        )
        mass = sum(shares[k] for k in pooled)
        if mass <= 0:
            raise ValueError("Empty source aggregate")
        q["outros"] = sum(shares[k] * rates[k] for k in pooled) / mass
    return q, pooled


def template(nexus, ballot, scenario):
    lv = nexus["turnout"]
    if scenario in {"central", "flavio95", "flavio105"}:
        source = lv["central"][ballot]
    else:
        age = {"idosos60": 0.60, "idosos80": 0.80}[scenario]
        source = next(x for x in lv["age_stress"][ballot] if x["older_turnout"] == age)
    keys = list(nexus["poll"]["publicado"][ballot])
    rates = dict(zip(keys, source["choice_turnout"], strict=True))
    if scenario in {"flavio95", "flavio105"}:
        rates["flavio"] *= {"flavio95": 0.95, "flavio105": 1.05}[scenario]
    return rates


def evaluate(rows, nexus, ballot, scenario):
    rates = template(nexus, ballot, scenario)
    evaluated = []
    for row in rows:
        q, pooled = candidate_rates(row, nexus, ballot, rates)
        if any(v is None for v in q.values()):
            raise ValueError("Missing turnout template")
        result = allocate(row["adjusted"], q, row["undecided"], rates["indecisos"])
        evaluated.append(
            {
                **row,
                "publicado": normalize(row["published"]),
                "pnad": normalize(row["adjusted"]),
                "modelo": result["valid"],
                "allocated_undecided": result["allocated"],
                "rates": q,
                "others_template_candidates": pooled,
                "proxy_candidates": [k for k in q if k not in rates],
            }
        )
    aggregate = {mode: average(evaluated, mode, ballot) for mode in MODES}
    common_keys = list(aggregate["modelo"])
    loo = []
    if len(evaluated) > 1:
        for i, row in enumerate(evaluated):
            loo.append(
                {
                    "without": row["instituto"],
                    "valid": average(
                        evaluated[:i] + evaluated[i + 1 :],
                        "modelo",
                        ballot,
                        common_keys,
                    ),
                }
            )
    return {
        "aggregate": aggregate,
        "polls": evaluated,
        "leave_one_out": loo,
        "rates": rates,
    }


def build(data, nexus):
    asof = data["referencia"]
    if nexus["poll"]["divulgacao"] > asof:
        raise ValueError("Turnout source is later than forecast date")
    # Select the latest wave per house and ballot *before* compatibility filtering.
    # Never silently replace an incomplete latest wave by an older one.
    result = {
        "reference": asof,
        "labels": LABELS,
        "modes": MODES,
        "scenario_labels": SCENARIOS,
        "ballots": {},
    }
    for ballot in ["1t", "2t"]:
        latest = WINDOW.select(
            [
                p
                for p in data["pesquisas"] + data.get("nao_reponderaveis", [])
                if ballot in p.get("publicado", {})
            ],
            date.fromisoformat(asof),
        )
        rows, excluded = [], []
        for poll in latest:
            try:
                rows.append(prepare(poll, ballot))
            except ValueError as exc:
                excluded.append(
                    {
                        "id": poll["id"],
                        "instituto": poll["instituto"],
                        "reason": str(exc),
                    }
                )
        if not rows:
            raise ValueError(
                "No complete candidate vector in current window: " + ballot
            )
        result["ballots"][ballot] = {
            "n_houses": len(rows),
            "excluded": excluded,
            "scenarios": {s: evaluate(rows, nexus, ballot, s) for s in SCENARIOS},
        }
    result["method"] = {
        "version": 2,
        "candidate_partition": "Only candidates individually identified in every eligible poll are shown separately; the remainder is pooled, never imputed as zero. The same partition is retained in leave-one-house-out checks.",
        "grouped_turnout": "An Others category pools Nexus candidate attendance rates, weighted by the Nexus PNAD population candidate mass, for candidates not separately reported in that poll.",
        "income_scenario": SCENARIO,
        "window_days": 7,
        "house_weight": "equal; normalize each poll before averaging",
        "turnout_source": nexus["poll"]["id"],
        "turnout_source_release": nexus["poll"]["divulgacao"],
        "conditional_forecast": "Vote preferences held fixed until election; no late swing, useful-vote or campaign model.",
        "transport": "Candidate-conditional attendance rates from the Nexus synthetic income-age-region table are transported to every eligible poll; not directly measured candidate turnout.",
        "undecided": "Allocated among expected attending candidates proportionally, separately inside each poll; cancels in the valid denominator.",
        "nonchoice": "Blank/null/absence are not candidates; no subtraction of national abstention from candidate percentages.",
        "missing_undecided": "No imputation if unpublished by income; the proportional-allocation identity makes the valid share independent of its size.",
        "negative_mass": "Floor negative adjusted candidate shares at zero, disclose amount and renormalize candidate mass.",
        "turnout_anchor": {
            b: nexus["turnout"]["central"][b]["target_turnout"] for b in ["1t", "2t"]
        },
    }
    return result


def write(data):
    source = ASSETS / "nexus_btg_28092026_data.json"
    result = build(data, json.loads(source.read_text()))
    result["sources_sha256"] = {
        "nexus_btg_28092026_data.json": hashlib.sha256(source.read_bytes()).hexdigest(),
        "reponderacao_pnad.json": hashlib.sha256(
            (ASSETS / "reponderacao_pnad.json").read_bytes()
        ).hexdigest(),
    }
    (ASSETS / "reponderacao_validos.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    with (ASSETS / "reponderacao_validos.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "referencia",
                "turno",
                "cenario",
                "modo",
                "candidato",
                "validos",
                "institutos",
                "ondas",
            ]
        )
        for b, block in result["ballots"].items():
            for s, scenario in block["scenarios"].items():
                for mode, values in scenario["aggregate"].items():
                    for k, v in values.items():
                        writer.writerow(
                            [
                                result["reference"],
                                b,
                                s,
                                mode,
                                k,
                                v,
                                block["n_houses"],
                                ";".join(p["id"] for p in scenario["polls"]),
                            ]
                        )
    return result


if __name__ == "__main__":
    result = write(json.loads((ASSETS / "reponderacao_pnad.json").read_text()))
    for ballot, value in result["ballots"].items():
        print(ballot, value["n_houses"], value["scenarios"]["central"]["aggregate"])
