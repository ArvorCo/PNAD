#!/usr/bin/env python3
"""Reponderação por renda da rodada Datafolha de julho/2026 (BR-01166/2026).

O relatório publica a intenção de voto por faixa de renda familiar em salários
mínimos e publica também o perfil de renda da amostra ponderada. Este script
compara esse perfil com a distribuição medida pela PNAD Contínua anual (visita
1 de 2025, rendimento domiciliar deflacionado para abril de 2026 e convertido em
salários mínimos) e recalcula os toplines trocando **apenas** a distribuição
marginal de renda.

É uma análise de sensibilidade, não uma correção: reponderação de uma margem
isolada ignora interações entre renda, região, escolaridade e idade, e "renda
familiar declarada em ponto de fluxo" não é o mesmo conceito que rendimento
domiciliar medido pela PNAD. O resultado responde a uma pergunta específica —
quanto do placar depende de a amostra ser economicamente mais pobre que o país.

Uso:
  python3 scripts/datafolha-072026-renda.py
  python3 scripts/datafolha-072026-renda.py --rebuild-pnad

Saídas:
  analysis/datafolha_072026/renda.json
  docs/assets/datafolha_072026_renda.json
  docs/assets/datafolha_072026_renda.js
  data/outputs/pnad_2025v1_renda_faixas.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "data" / "outputs"
ANALYSIS = ROOT / "analysis" / "datafolha_072026"

PNAD_CSV = OUTPUTS / "base_anual_visita1_labeled_npv.csv"
PNAD_CACHE = OUTPUTS / "pnad_2025v1_renda_faixas.json"
OUT_JSON = ANALYSIS / "renda.json"
OUT_SITE_JSON = ROOT / "docs" / "assets" / "datafolha_072026_renda.json"
OUT_SITE_JS = ROOT / "docs" / "assets" / "datafolha_072026_renda.js"

BANDS = ("ate2", "de2a5", "de5a10", "mais10")
BAND_LABELS = {
    "ate2": "Até 2 SM",
    "de2a5": "Mais de 2 a 5 SM",
    "de5a10": "Mais de 5 a 10 SM",
    "mais10": "Mais de 10 SM",
}

# Colunas do CSV anual rotulado. VD5001 é o rendimento domiciliar efetivo
# (exclusive cartão/tíquete), série usada desde a auditoria de junho; VD5007 é o
# habitual e entra como teste de robustez. Sufixo `_mw` = em salários mínimos,
# já deflacionado para 2026-04 pelo pipeline `npv_deflators.py`.
COLUMNS = {
    "dom_id": "dom_id",
    "idade": "V2009__idade_na_data_de_referencia",
    "peso": "V1032__peso_com_calibracao",
    "condicao": "V2005__condicao_no_domicilio",
    "vd5001": "VD5001__rend_efetivo_domiciliar_mw",
    "vd5007": "VD5007__rend_habitual_domiciliar_mw",
}

# Transcrição das páginas 16 (1º turno) e 18 (2º turno) do relatório de julho.
DATAFOLHA_BASES = {"ate2": 1002, "de2a5": 678, "de5a10": 194, "mais10": 51}

SECOND_ROUND = {
    "ate2": {"lula": 56, "flavio": 36, "branco_nulo": 7, "nao_sabe": 1},
    "de2a5": {"lula": 39, "flavio": 50, "branco_nulo": 10, "nao_sabe": 1},
    "de5a10": {"lula": 38, "flavio": 51, "branco_nulo": 11, "nao_sabe": 0},
    "mais10": {"lula": 45, "flavio": 51, "branco_nulo": 3, "nao_sabe": 0},
}

FIRST_ROUND = {
    "ate2": {"lula": 47, "flavio": 28, "branco_nulo": 8, "nao_sabe": 3},
    "de2a5": {"lula": 31, "flavio": 38, "branco_nulo": 8, "nao_sabe": 2},
    "de5a10": {"lula": 32, "flavio": 37, "branco_nulo": 8, "nao_sabe": 1},
    "mais10": {"lula": 44, "flavio": 34, "branco_nulo": 3, "nao_sabe": 1},
}

# Perfil de renda da amostra ponderada, página 13 do relatório (em %).
DATAFOLHA_PROFILE = {
    "ate2": 50,
    "de2a5": 34,  # "de 2 a 3" (17) + "de 3 a 5" (17)
    "de5a10": 10,
    "mais10": 2,  # 10 a 20 (2) + 20 a 50 (0) + mais de 50 (0)
    "recusa_ou_nao_sabe": 4,
}


class Distribution(NamedTuple):
    """Distribuição percentual pelas quatro faixas, já normalizada em 100."""

    ate2: float
    de2a5: float
    de5a10: float
    mais10: float

    def as_dict(self) -> dict[str, float]:
        return {band: round(getattr(self, band), 2) for band in BANDS}

    def weights(self) -> dict[str, float]:
        return {band: getattr(self, band) / 100 for band in BANDS}


def classify(value: float) -> str:
    if value <= 2:
        return "ate2"
    if value <= 5:
        return "de2a5"
    if value <= 10:
        return "de5a10"
    return "mais10"


def normalize(tally: dict[str, float]) -> Distribution:
    total = sum(tally.values())
    if not total:
        raise ValueError("distribuição vazia")
    return Distribution(*(100 * tally[band] / total for band in BANDS))


def build_pnad() -> dict[str, dict[str, dict[str, float]]]:
    """Percorre o microdado anual uma única vez e devolve as distribuições."""
    if not PNAD_CSV.exists():
        raise SystemExit(
            f"{PNAD_CSV.relative_to(ROOT)} não existe. Rode antes o pipeline "
            "`brasil pipeline-run` para a PNADC anual visita 1."
        )

    with PNAD_CSV.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    index = {key: header.index(name) for key, name in COLUMNS.items()}

    tallies: dict[str, dict[str, dict[str, float]]] = {
        variable: {
            "domicilios": defaultdict(float),
            "pessoas_16": defaultdict(float),
        }
        for variable in ("vd5001", "vd5007")
    }

    csv.field_size_limit(sys.maxsize)
    with PNAD_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            try:
                weight = float(row[index["peso"]] or 0)
                age = int(float(row[index["idade"]]))
            except ValueError:
                continue
            if weight <= 0:
                continue
            # V2005 == 1: pessoa responsável pelo domicílio. Uma linha por
            # domicílio, evitando contar a mesma unidade várias vezes.
            is_reference = row[index["condicao"]] in {"1", "01"}
            for variable in ("vd5001", "vd5007"):
                raw = row[index[variable]]
                if raw in ("", ".", "NA"):
                    continue
                try:
                    band = classify(float(raw))
                except ValueError:
                    continue
                if age >= 16:
                    tallies[variable]["pessoas_16"][band] += weight
                if is_reference:
                    tallies[variable]["domicilios"][band] += weight

    return {
        variable: {
            unit: normalize(counter).as_dict() for unit, counter in units.items()
        }
        for variable, units in tallies.items()
    }


def load_pnad(rebuild: bool) -> dict[str, dict[str, dict[str, float]]]:
    if PNAD_CACHE.exists() and not rebuild:
        return json.loads(PNAD_CACHE.read_text(encoding="utf-8"))
    distributions = build_pnad()
    PNAD_CACHE.write_text(
        json.dumps(distributions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return distributions


def reweight(
    crosstab: dict[str, dict[str, int]], weights: dict[str, float]
) -> dict[str, float]:
    """Aplica pesos marginais de renda ao cruzamento publicado."""
    result: dict[str, float] = {}
    for option in ("lula", "flavio", "branco_nulo", "nao_sabe"):
        result[option] = round(
            sum(weights[band] * crosstab[band][option] for band in BANDS), 2
        )
    result["diferenca_lula_flavio"] = round(result["lula"] - result["flavio"], 2)
    return result


def scenario(
    label: str,
    source: str,
    distribution: Distribution,
    kind: str,
) -> dict[str, object]:
    crosstab = SECOND_ROUND if kind == "segundo_turno" else FIRST_ROUND
    return {
        "cenario": label,
        "fonte": source,
        "distribuicao_pct": distribution.as_dict(),
        "resultado": reweight(crosstab, distribution.weights()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-pnad",
        action="store_true",
        help="recalcula as faixas de renda a partir do microdado anual",
    )
    args = parser.parse_args()

    pnad = load_pnad(args.rebuild_pnad)

    base_total = sum(DATAFOLHA_BASES.values())
    datafolha = Distribution(
        *(100 * DATAFOLHA_BASES[band] / base_total for band in BANDS)
    )
    profile_total = sum(DATAFOLHA_PROFILE[band] for band in BANDS)
    datafolha_profile = Distribution(
        *(100 * DATAFOLHA_PROFILE[band] / profile_total for band in BANDS)
    )
    pnad_households = Distribution(*(pnad["vd5001"]["domicilios"][b] for b in BANDS))
    pnad_people = Distribution(*(pnad["vd5001"]["pessoas_16"][b] for b in BANDS))
    pnad_people_habitual = Distribution(
        *(pnad["vd5007"]["pessoas_16"][b] for b in BANDS)
    )

    universes = [
        ("Datafolha · bases do cruzamento", "relatório, págs. 16 e 18", datafolha),
        ("Datafolha · perfil ponderado", "relatório, pág. 13", datafolha_profile),
        ("PNAD · domicílios", "PNADC anual 2025 visita 1, VD5001", pnad_households),
        (
            "PNAD · pessoas de 16 anos ou mais",
            "PNADC anual 2025 visita 1, VD5001",
            pnad_people,
        ),
        (
            "PNAD · pessoas 16+ (renda habitual)",
            "PNADC anual 2025 visita 1, VD5007",
            pnad_people_habitual,
        ),
    ]

    output = {
        "generated_from": {
            "microdado": str(PNAD_CSV.relative_to(ROOT)),
            "relatorio": "data/originals/datafolha_072026/DataFolhaRelatorio072026.pdf",
            "referencia_monetaria": "rendimento domiciliar deflacionado para 2026-04 e convertido em salários mínimos",
        },
        "faixas": {band: BAND_LABELS[band] for band in BANDS},
        "distribuicoes_pct": {
            "datafolha_bases_do_cruzamento": datafolha.as_dict(),
            "datafolha_perfil_ponderado": datafolha_profile.as_dict(),
            "pnad_domicilios": pnad_households.as_dict(),
            "pnad_pessoas_16": pnad_people.as_dict(),
            "pnad_pessoas_16_habitual": pnad_people_habitual.as_dict(),
        },
        "distancia_ate2_pp": {
            "datafolha_menos_pnad_domicilios": round(
                datafolha.ate2 - pnad_households.ate2, 2
            ),
            "datafolha_menos_pnad_pessoas_16": round(
                datafolha.ate2 - pnad_people.ate2, 2
            ),
        },
        "razao_mais10": {
            "pnad_pessoas_16_sobre_datafolha": round(
                pnad_people.mais10 / datafolha.mais10, 2
            ),
        },
        "segundo_turno": [
            scenario(label, source, dist, "segundo_turno")
            for label, source, dist in universes
        ],
        "primeiro_turno": [
            scenario(label, source, dist, "primeiro_turno")
            for label, source, dist in universes
        ],
        "toplines_publicados": {
            "segundo_turno": {"lula": 48, "flavio": 43},
            "primeiro_turno": {"lula": 40, "flavio": 32},
        },
        "limitacoes": [
            "Reponderação de uma margem isolada: ignora interações entre renda, região, escolaridade, idade e religião.",
            "Renda familiar declarada em ponto de fluxo não é o mesmo conceito que rendimento domiciliar medido pela PNAD, e 3,9% da amostra não declarou renda.",
            "A referência PNAD é a visita 1 de 2025, deflacionada para abril de 2026; o campo do Datafolha é de julho de 2026.",
            "O exercício não produz o 'resultado real' da eleição nem substitui microdados e pesos individuais, que o instituto não publica.",
        ],
    }

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    OUT_JSON.write_text(payload, encoding="utf-8")
    OUT_SITE_JSON.write_text(payload, encoding="utf-8")
    OUT_SITE_JS.write_text(
        "window.__DATAFOLHA_RENDA__ = "
        + json.dumps(output, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    print(f"OK: {OUT_JSON.relative_to(ROOT)}")
    print(f"OK: {OUT_SITE_JS.relative_to(ROOT)}")
    for row in output["segundo_turno"]:
        result = row["resultado"]
        print(
            f'2T · {row["cenario"]:<38} '
            f'Lula {result["lula"]:>5} × Flávio {result["flavio"]:>5} '
            f'({result["diferenca_lula_flavio"]:+.2f})'
        )


if __name__ == "__main__":
    main()
