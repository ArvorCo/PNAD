"""Auditoria reproduzível da renda, arredondamento e denominadores atuais."""

import importlib
import json
import math

from dossies_2t_2026.audit import controls, reweight
from dossies_2t_2026.extract import ROOT

from .extract import SHA256, tables


def rounding(flavio, lula):
    """Arredondamento usual para inteiros; entradas em porcentagem do total."""
    if min(flavio, lula) < 0 or not 0 < flavio + lula <= 100:
        raise ValueError("Percentuais inválidos")
    valid = 100 * flavio / (flavio + lula)
    return {
        "total": [flavio, lula],
        "total_inteiro": [math.floor(flavio + 0.5), math.floor(lula + 0.5)],
        "validos": [valid, 100 - valid],
        "validos_inteiros": [math.floor(valid + 0.5), math.floor(100 - valid + 0.5)],
    }


def build():
    extracted = tables()
    checks = controls(extracted, "datafolha")
    poll = importlib.import_module("datafolha-221026-renda").completa()
    decision = extracted["decisao"]["segments"]["total"]
    decision_pct = decision["responses"]["Está totalmente decidido a votar"]
    return {
        "slug": "datafolha_22102026",
        "release": "22/10/2026",
        "field": "20–22/10/2026",
        "reviewed": "23/10/2026",
        "n": 2520,
        "municipalities": 154,
        "registry": "BR-09709/2026",
        "source": poll["fonte"],
        "pdf_sha256": SHA256,
        "tables": extracted,
        "controls": checks,
        "reweight": reweight(poll["id"]),
        "reported_valid": {"flavio": 50, "lula": 50},
        "rounding": {
            "from_displayed": rounding(47, 46),
            "hypothetical_example": rounding(46.8, 46.49),
            "hypothetical_other": [5.2, 1.51],
            "unrounded_values_published": False,
            "flavio_valid_envelope_from_totals": [50, 100 * 47.5 / 93],
            "note": "Exemplo de compatibilidade, não recuperação dos percentuais internos. Limites abertos dependem da convenção de arredondamento.",
        },
        "denominators": {
            "valid_presentation": 2347,
            "valid_weighted": 2351,
            "decision_weighted": decision["base_ponderada"],
            "certain_all_pct": decision_pct * decision["base_ponderada"] / 2520,
            "income_weighted": sum(poll["renda"]["bases"]),
            "income_missing": poll["renda"]["nao_publicada_n"],
        },
        "quota": {
            "registry_consulted": "2026-10-22",
            "design": "misto",
            "field_variables": ["gênero", "idade"],
            "male_target_pct": 47,
            "male_weighted_pct": 100 * 1239 / 2520,
            "female_target_pct": 53,
            "female_weighted_pct": 100 * 1281 / 2520,
            "income_field_quota_declared": False,
            "income_factor_planned": 1,
        },
        "difference_aas_margin_pp": 1.96 * math.sqrt((0.93 - 0.01**2) / 2520) * 100,
        "transfer": {
            "page": 5,
            "flavio": 47,
            "lula": 26,
            "branco_nulo": 21,
            "indecisos": 6,
            "base": None,
        },
        "presence": {"page": 5, "validos_entre_votantes_1t": [51, 49], "base": None},
    }


def write():
    from dossies_2t_2026.audit import compact_tables

    output = ROOT / "analysis/datafolha_221026"
    output.mkdir(parents=True, exist_ok=True)
    data = build()
    (output / "tabelas.json").write_text(
        compact_tables(data["tables"]), encoding="utf-8"
    )
    content = (
        "{\n"
        + ",\n".join(
            json.dumps(k)
            + ": "
            + (
                compact_tables(v).strip()
                if k == "tables"
                else json.dumps(v, ensure_ascii=False)
            )
            for k, v in data.items()
        )
        + "\n}\n"
    )
    (output / "auditoria.json").write_text(content, encoding="utf-8")
    (ROOT / "docs/assets/datafolha_22102026_data.json").write_text(
        content, encoding="utf-8"
    )
    return data
