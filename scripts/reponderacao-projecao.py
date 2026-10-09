"""Adapter do motor nacional do 1º turno para a cédula binária pós-04/10.

Reutiliza recência, inclinação encolhida com efeitos fixos e o núcleo Monte
Carlo. Não transporta preferências, inclinações ou validação do primeiro turno.
"""

import hashlib
import importlib
import json
from datetime import date
from pathlib import Path

import numpy as np
from predicao_2026.base import latest, sloped_central
from predicao_2026.motor import DEFF, target_draws
from predicao_2026.recencia import NATIONAL_HALF_LIFE, age, decay, weights

ROOT = Path(__file__).resolve().parents[1]
FIRST_ROUND = "2026-10-04"
ELECTION = date(2026, 10, 25)
KEYS = ("flavio", "lula", "indecisos", "branco_nulo")
RUNS, SEED = 2000, 20261009


def four(vector):
    values = np.asarray(vector, float)[[1, 0, 3, 4]]
    values *= 100 / values.sum()
    return dict(zip(KEYS, values.tolist(), strict=True))


def five(values):
    return [values[k] / 100 for k in ("lula", "flavio")] + [
        0.0,
        values["indecisos"] / 100,
        values["branco_nulo"] / 100,
    ]


def observation(source, preferences, today):
    pub = source["publicado"]["2t"]
    if not {"flavio", "lula"} <= pub.keys():
        raise ValueError("Placar binário incompleto")
    allowed = {
        "flavio",
        "lula",
        "indecisos",
        "nao_sabe",
        "ns_nr",
        "branco_nulo",
        "nenhum",
        "nao_vai_votar",
    }
    if any(v > 0 for k, v in pub.items() if k not in allowed):
        raise ValueError("Cédula contém outra candidatura")
    if source.get("n", 0) <= 0:
        raise ValueError("Base amostral ausente")
    adjusted = (
        source.get("turnos", {})
        .get("2t", {})
        .get("cenarios", {})
        .get("pessoas16_efetivo", {})
        .get("ajustado")
    )
    published = preferences(pub, pub)
    pnad = preferences(adjusted, pub) if adjusted is not None else published
    return {
        "id": source["id"],
        "instituto": source["instituto"],
        "campo": source["campo"],
        "divulgacao": source["divulgacao"],
        "n": source["n"],
        "published": published,
        "pnad": pnad,
        "income_available": adjusted is not None,
        "publicado_vetor": five(published),
        "previsao_vetor": five(pnad),
        "peso_recencia": decay(age(source["campo"], today), NATIONAL_HALF_LIFE),
    }


def trend(observations, selected, today, kind):
    rows = [{**p, "previsao_vetor": p[kind]} for p in observations]
    chosen = [{**p, "previsao_vetor": p[kind]} for p in selected]
    # Pelo menos duas casas e variação dentro de casa: não estimar o tempo
    # pela diferença de níveis de institutos com uma única observação cada.
    houses = {p["instituto"] for p in rows}
    usable = len(houses) >= 2 and len(rows) - len(houses) - 1 >= 3
    result = sloped_central(chosen, rows if usable else [], today, election=ELECTION)
    result["available"] = bool(result["inclinacoes_brutas_validos_pp_dia"])
    result["status"] = (
        "Inclinação encolhida estimada apenas em ondas posteriores a 04/10."
        if result["available"]
        else "Série pós-04/10 insuficiente para tendência com efeito fixo de casa: projeção constante, sem inclinação estimada."
    )
    return result


def build(data, preferences):
    today = date.fromisoformat(data["referencia"])
    if today > ELECTION:
        raise ValueError("Projeção pré-eleitoral exige corte até 25/10/2026")
    sources = data["pesquisas"] + data.get("nao_reponderaveis", [])
    candidates, excluded = [], []
    for p in sources:
        if "2t" not in p.get("publicado", {}) or not p.get("divulgacao"):
            continue
        if p["divulgacao"] > today.isoformat() or p["campo"]["fim"] > today.isoformat():
            continue
        if p["campo"]["inicio"] <= FIRST_ROUND:
            excluded.append(
                {
                    "id": p["id"],
                    "instituto": p["instituto"],
                    "reason": "Campo anterior ao fim do 1º turno ou atravessa a eleição",
                }
            )
            continue
        candidates.append(p)
    dedup = {
        (p["instituto"], p["campo"]["inicio"], p["campo"]["fim"]): p
        for p in sorted(candidates, key=lambda p: (p["divulgacao"], p["id"]))
    }
    candidates = list(dedup.values())
    selected_ids = {p["id"] for p in latest(candidates, today)}
    observations = []
    for p in candidates:
        try:
            observations.append(observation(p, preferences, today))
        except ValueError as exc:
            if p["id"] in selected_ids:
                excluded.append(
                    {"id": p["id"], "instituto": p["instituto"], "reason": str(exc)}
                )
    selected = sorted(
        (p for p in observations if p["id"] in selected_ids),
        key=lambda p: p["instituto"],
    )
    if not selected:
        raise ValueError("Nenhuma casa elegível na projeção pós-1º turno")
    for p, w in zip(selected, weights(selected), strict=True):
        p["weight"] = float(w)
    trends, anchors, draws = {}, {}, {}
    for label, kind in (("pnad", "previsao_vetor"), ("published", "publicado_vetor")):
        fitted = trend(observations, selected, today, kind)
        trends[label] = fitted
        anchors[label] = four(fitted["vetor"])
        polls = [{**p, "previsao_vetor": p[kind]} for p in selected]
        inclusive = np.average(
            [p[kind] for p in selected], axis=0, weights=weights(selected)
        ).tolist()
        national = {
            "selecionadas": polls,
            "alvos": {"inclusivo": inclusive, "central_inclinacao": fitted["vetor"]},
            "incerteza_projecao_pp": {
                "central_inclinacao": fitted["dp_margem_projecao_pp"]
            },
        }
        targets, _, _, _ = target_draws(
            national, "central_inclinacao", RUNS, np.random.default_rng(SEED)
        )
        draws[label] = [[round(row[k], 8) for k in KEYS] for row in map(four, targets)]
    return {
        "name": "Central Projeção Arvor",
        "election": ELECTION.isoformat(),
        "election_source": "https://www.tse.jus.br/comunicacao/noticias/2026/Marco/eleicoes-2026-confira-as-principais-datas-do-calendario-eleitoral",
        "half_life_days": NATIONAL_HALF_LIFE,
        "selected": selected,
        "excluded": excluded,
        "anchors": anchors,
        "trend": trends,
        "mc": {
            "runs": RUNS,
            "seed": SEED,
            "deff": DEFF,
            "n_cap": 2000,
            "common_sd_pp": 2.0,
            "draws": draws,
        },
        "undecided": "Proporcionais: não há rejeição comparável pós-04/10 incorporada; não transportamos a disponibilidade medida antes do 1º turno.",
        "states": importlib.import_module("reponderacao-estaduais").build(today),
        "shared_sources": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in [
                "scripts/predicao_2026/base.py",
                "scripts/predicao_2026/recencia.py",
                "scripts/predicao_2026/tendencia.py",
                "scripts/predicao_2026/motor.py",
            ]
        },
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "method": "Última onda por casa na semana, peso pelo ponto médio do campo (meia-vida 3 dias); PNAD onde existe e publicado onde falta; âncora projetada a 25/10 por inclinação de 28 dias encolhida, estimada só após 04/10 quando identificável. Monte Carlo: bootstrap bayesiano por casa, Dirichlet com n efetivo e choque comum Student t (dp 2 pp), mais incerteza da inclinação em quadratura.",
        "limits": "Adaptação nacional do motor do 1º turno, sem ML supervisionado ou informação nova criada pelo Monte Carlo. Não transfere validação contra pesquisas nem preferências territoriais do 1º turno. Pesos PNAD são sensibilidade de uma margem; propensões Nexus e presença relativa +5% continuam hipóteses. Os intervalos são condicionais, sem cobertura validada contra a urna; com tendência indisponível supõem estabilidade até 25/10.",
    }


def encode(data):
    """Snapshot legível e compacto: sorteios agrupados, em vez de 24 mil linhas."""
    clone = {
        **data,
        "projection": {
            **data["projection"],
            "mc": {**data["projection"]["mc"], "draws": "__DRAWS__"},
        },
    }
    draws = data["projection"]["mc"]["draws"]
    clone["projection"]["selected"] = "__SELECTED__"
    clone["polls"] = "__POLLS__"
    clone["projection"]["uncertainty"] = "__UNCERTAINTY__"
    clone["projection"]["states"] = "__STATES__"
    clone["central_projection"] = "__CENTRAL_PROJECTION__"
    if "turnout_model" in clone:
        clone["turnout_model"] = "__TURNOUT__"
    fields = []
    for key, rows in draws.items():
        blocks = [
            json.dumps(rows[i : i + 25], separators=(",", ":"))[1:-1]
            for i in range(0, len(rows), 25)
        ]
        fields.append(
            f'      "{key}": [\n        ' + ",\n        ".join(blocks) + "\n      ]"
        )
    compact = "{\n" + ",\n".join(fields) + "\n    }"
    selected = (
        "[\n      "
        + ",\n      ".join(
            json.dumps(row, ensure_ascii=False)
            for row in data["projection"]["selected"]
        )
        + "\n    ]"
    )
    return (
        json.dumps(clone, ensure_ascii=False, indent=2)
        .replace('"__DRAWS__"', compact)
        .replace('"__SELECTED__"', selected)
        .replace('"__POLLS__"', json.dumps(data["polls"], ensure_ascii=False))
        .replace(
            '"__STATES__"', json.dumps(data["projection"]["states"], ensure_ascii=False)
        )
        .replace(
            '"__UNCERTAINTY__"',
            json.dumps(data["projection"]["uncertainty"], ensure_ascii=False),
        )
        .replace(
            '"__CENTRAL_PROJECTION__"',
            json.dumps(data["central_projection"], ensure_ascii=False),
        )
        .replace(
            '"__TURNOUT__"', json.dumps(data.get("turnout_model"), ensure_ascii=False)
        )
        + "\n"
    )
