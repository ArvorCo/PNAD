"""Agregador histórico em válidos, fechado antes da urna; sem recalibração."""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
from datetime import date, timedelta
from pathlib import Path
from statistics import fmean

from apuracao_2026.pesquisas import NAO_ESCOLHA, validos
from reponderacao_vista.urna_dados import ELECTION, OFFICIAL

ROOT = Path(__file__).resolve().parents[2]
WINDOW = importlib.import_module("reponderacao-janela")
KEYS = ("flavio", "lula", "demais")
MODES = ("publicado", "pnad")


def blocks(vector):
    normalized, audit = validos(vector)
    return {
        "flavio": normalized["flavio"],
        "lula": normalized["lula"],
        "demais": 100 - normalized["flavio"] - normalized["lula"],
    }, audit


def build(data):
    """Mesmas casas da série principal, normalizadas onda a onda, antes da média."""
    scenario = data["benchmark"]["cenario_principal"]
    rows, exclusions = [], []
    for poll in data["pesquisas"]:
        turn = poll.get("turnos", {}).get("1t")
        if not turn:
            continue
        release = poll.get("divulgacao")
        if (
            not release
            or release > ELECTION
            or poll["campo"]["fim"] > ELECTION
            or poll.get("substituida")
            or poll.get("primeiro_turno_com_marcal")
        ):
            exclusions.append(poll["id"])
            continue
        published = poll["publicado"]["1t"]
        delta = turn["cenarios"][scenario]["ajustado"]
        row = {
            "id": poll["id"],
            "instituto": poll["instituto"],
            "campo": poll["campo"],
            "divulgacao": release,
            "perfil_renda": poll["renda"].get("perfil_tipo", "perfil_publicado"),
        }
        # Votos sem cruzamento preservam o publicado, inclusive candidaturas
        # menores: não viram zero nem recebem preferência de renda inventada.
        for mode, vector in (
            ("publicado", published),
            ("pnad", {**published, **delta}),
        ):
            row[mode], row[f"auditoria_{mode}"] = blocks(vector)
        row["sem_cruzamento"] = sorted(
            k
            for k, v in published.items()
            if v > 0 and k not in delta and k not in NAO_ESCOLHA
        )
        rows.append(row)
    if not rows:
        raise ValueError("Sem ondas elegíveis para a série do primeiro turno")
    cutoff = max(row["divulgacao"] for row in rows)
    start = date.fromisoformat(min(row["divulgacao"] for row in rows))
    end = date.fromisoformat(cutoff)
    series = []
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        selected = WINDOW.select(rows, day)
        series.append(
            {
                "data": day.isoformat(),
                "n_institutos": len(selected),
                "ondas": [row["id"] for row in selected],
                **{
                    mode: (
                        {k: fmean(row[mode][k] for row in selected) for k in KEYS}
                        if selected
                        else None
                    )
                    for mode in MODES
                },
            }
        )
    selected = WINDOW.select(rows, end)
    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    votes = official["nacional"]["votos"]
    valid_votes = official["nacional"]["validos"]
    # A fonte tem também "terceiros", um subtotal que não pode ser somado
    # de novo às candidaturas. O denominador é o total oficial de válidos.
    urn_votes = {
        "flavio": votes["flavio"],
        "lula": votes["lula"],
        "demais": valid_votes - votes["flavio"] - votes["lula"],
    }
    if urn_votes["demais"] < 0:
        raise ValueError("Votos dos líderes excedem os válidos oficiais")
    urn = {
        "data": ELECTION,
        "validos_votos": valid_votes,
        "validos": blocks(urn_votes)[0],
    }
    final = {
        **series[-1],
        "inicio_janela": (end - timedelta(days=6)).isoformat(),
        "institutos": [row["instituto"] for row in selected],
        "pesquisas": selected,
        "urna_menos_media_pp": {
            mode: {k: urn["validos"][k] - series[-1][mode][k] for k in KEYS}
            for mode in MODES
        },
    }
    return {
        "eleicao": ELECTION,
        "corte_pesquisas": cutoff,
        "cenario_renda": scenario,
        "regra": "Média móvel de 7 dias pela divulgação (D−6 a D), última onda por instituto, peso igual. Somente casas com cruzamento de renda do agregador principal; publicado e PNAD usam as mesmas ondas. Cada vetor completo de candidaturas é normalizado em válidos antes da média; indecisos e branco/nulo ficam fora, sem transferência ou ajuste de comparecimento.",
        "limite": "Histórico recalculado com os documentos hoje disponíveis, sem usar a urna nos cálculos. As candidaturas da cédula variam nas ondas antigas; demais inclui todas além de Flávio e Lula. PNAD troca somente a margem de renda; nomes sem cruzamento mantêm o publicado. Resíduos negativos são truncados antes da normalização e registrados na auditoria. Não é arquivo de previsões publicadas em cada data.",
        "excluidas": exclusions,
        "serie": series,
        "final": final,
        "urna": urn,
        "fontes_sha256": {
            "docs/assets/reponderacao_pnad.json": hashlib.sha256(
                (ROOT / "docs/assets/reponderacao_pnad.json").read_bytes()
            ).hexdigest(),
            str(OFFICIAL.relative_to(ROOT)): hashlib.sha256(
                OFFICIAL.read_bytes()
            ).hexdigest(),
        },
    }


def write(data):
    result = build(data)
    assets = ROOT / "docs/assets"
    lines = []
    for key, value in result.items():
        encoded = json.dumps(value, ensure_ascii=False)
        if key == "serie":
            encoded = (
                "[\n"
                + ",\n".join(
                    "    " + json.dumps(row, ensure_ascii=False) for row in value
                )
                + "\n  ]"
            )
        lines.append("  " + json.dumps(key) + ": " + encoded)
    (assets / "reponderacao_urna_serie_1t.json").write_text(
        "{\n" + ",\n".join(lines) + "\n}\n", encoding="utf-8"
    )
    with (assets / "reponderacao_urna_serie_1t.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["data", "tipo", "n_institutos", "ondas"]
            + [f"{mode}_{key}_validos_pct" for mode in MODES for key in KEYS]
        )
        for row in result["serie"]:
            writer.writerow(
                [row["data"], "media", row["n_institutos"], ";".join(row["ondas"])]
                + [
                    row[mode][key] if row[mode] is not None else ""
                    for mode in MODES
                    for key in KEYS
                ]
            )
        writer.writerow(
            [ELECTION, "urna", "", ""]
            + [result["urna"]["validos"][key] for _ in MODES for key in KEYS]
        )
    return result
