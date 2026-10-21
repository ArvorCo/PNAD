"""Projeções documentais por onda, sem transporte entre casas ou efeito nas centrais."""

import importlib
import json
from functools import lru_cache

from reponderacao_vista.context import ROOT

EVIDENCE = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
PAIR = ("flavio", "lula")
allocate = importlib.import_module("reponderacao-validos").allocate


@lru_cache(maxsize=1)
def evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def rates(poll, entry, mode):
    """Seleção declarada; proxy assume independência voto × presença dentro da renda."""
    if entry["tipo"] == "direto":
        return entry["taxas"]
    if entry["tipo"] != "proxy_renda":
        return dict.fromkeys((*PAIR, "indecisos"), 1.0)
    weights = entry["perfil"] if mode == "placar" else entry["pnad"]
    result = {}
    for key, votes in entry["voto_renda"].items():
        mass = sum(w * v for w, v in zip(weights, votes, strict=True))
        result[key] = (
            sum(
                w * v * q
                for w, v, q in zip(weights, votes, entry["presenca_renda"], strict=True)
            )
            / mass
            if mass
            else 1.0
        )
    return result


def project(poll):
    entry = evidence()["ondas"].get(poll["id"])
    if entry is None:
        entry = {
            "tipo": "neutro",
            "regra": "Presença igual entre candidatos: sem cruzamento de presença incorporado nesta onda. Não é likely voter medido.",
        }
    result = {"evidencia": entry, "modos": {}}
    for mode in ("placar", "pnad"):
        values = poll[mode]
        if values is None:
            result["modos"][mode] = None
            continue
        q = rates(poll, entry, mode)
        only_valid = poll["denominador"] == "validos"
        if only_valid:
            # Keep published valid-only values exactly, without inferring totals.
            result["modos"][mode] = {
                "validos": {c: values[c] for c in PAIR},
                "validos_sem_presenca": {c: values[c] for c in PAIR},
                "taxas": dict.fromkeys(PAIR, 1.0),
                "indecisos": None,
                "transferidos": None,
                "delta_presenca_pp": dict.fromkeys(PAIR, 0.0),
            }
            continue
        candidates = {c: values[c] for c in PAIR}
        undecided = values.get("indecisos", values.get("nao_sabe"))
        calculated = allocate(candidates, q, max(0, undecided or 0), q["indecisos"])
        simple = allocate(candidates, dict.fromkeys(PAIR, 1.0))["valid"]
        result["modos"][mode] = {
            "validos": calculated["valid"],
            "validos_sem_presenca": simple,
            "taxas": q,
            "indecisos": undecided,
            "transferidos": calculated["allocated"] if undecided is not None else None,
            "delta_presenca_pp": {c: calculated["valid"][c] - simple[c] for c in PAIR},
        }
    return result


def projected_row(poll):
    projection = project(poll)
    return {
        **poll,
        "projecao": projection,
        "modo_projecao": True,
        "base_original": poll["denominador"],
        "denominador": "validos",
        **{
            key: (
                projection["modos"][key]["validos"]
                if projection["modos"][key]
                else None
            )
            for key in ("placar", "pnad")
        },
    }
