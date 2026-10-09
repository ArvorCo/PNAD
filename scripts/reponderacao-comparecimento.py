"""Transporte 1T→2T: referência observada, retrospectiva e cenários históricos.

Não estima presença por candidato e não confunde eleitores com votos válidos.
A comparação de regras é exploratória: apenas três eleições fora da amostra.
"""

import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "analysis/reponderacao/comparecimento/serie_presidencial.json"
OFFICIAL = ROOT / "analysis/apuracao_2026/dados/presidente.json"
CHECKS = ROOT / "analysis/reponderacao/comparecimento/tse_2018_2022.json"


def retrospectiva(years, minimum=3):
    """Só anos anteriores ao alvo; não trata 27 UFs como 27 eleições."""
    rules = {
        "sem_mudanca": ("Repetir o 1º turno", lambda x: 0.0),
        "ultima": ("Repetir a última variação", lambda x: x[-1]),
        "media_3": ("Média das últimas três variações", lambda x: mean(x[-3:])),
        "media_todas": ("Média de todas as variações anteriores", mean),
    }
    out = []
    for key, (label, predict) in rules.items():
        cases = []
        for i in range(minimum, len(years)):
            past = [r["delta_turnout_pp"] for r in years[:i]]
            expected = predict(past)
            actual = years[i]["delta_turnout_pp"]
            cases.append(
                {
                    "year": years[i]["year"],
                    "training_years": [r["year"] for r in years[:i]],
                    "prediction_delta_pp": expected,
                    "actual_delta_pp": actual,
                    "error_pp": expected - actual,
                }
            )
        out.append(
            {
                "id": key,
                "name": label,
                "mae_pp": mean(abs(r["error_pp"]) for r in cases),
                "bias_pp": mean(r["error_pp"] for r in cases),
                "cases": cases,
            }
        )
    return out


def build():
    content = HISTORY.read_bytes()
    source = json.loads(content)
    years = []
    for row in sorted(source["years"], key=lambda r: r["year"]):
        if row["year"] >= 2026 or not all(
            0 < row[k] <= 100 for k in ("turnout_1_pct", "turnout_2_pct")
        ):
            raise ValueError("Ano ou taxa histórica inválida")
        delta = row["turnout_2_pct"] - row["turnout_1_pct"]
        years.append({**row, "delta_turnout_pp": delta, "delta_absence_pp": -delta})
    if [r["year"] for r in years] != [2002, 2006, 2010, 2014, 2018, 2022]:
        raise ValueError("Série presidencial incompleta ou repetida")
    raw = OFFICIAL.read_bytes()
    official = json.loads(raw)
    domestic = [r for r in official["ufs"] if r["uf"] != "ZZ"]
    if len(domestic) != 27 or len({r["uf"] for r in domestic}) != 27:
        raise ValueError("Apuração exige as 27 UFs, sem duplicatas")
    for r in domestic:
        if r["secoes"] != r["secoes_total"]:
            raise ValueError("Apuração de 2026 ainda não fechada")
        if r["eleitores"] != r["comparecimento"] + r["abstencao"]:
            raise ValueError("Contabilidade do comparecimento de 2026 não fecha")
    total = sum(r["eleitores"] for r in domestic)
    attending = sum(r["comparecimento"] for r in domestic)
    baseline = 100 * attending / total
    comparisons = retrospectiva(years)
    checks = []
    for row in json.loads(CHECKS.read_text()):
        rates = {}
        residuals = {}
        for scope in ("Brasil", "Brasil e exterior"):
            rounds = {r["turno"]: r for r in row["rounds"] if r["scope"] == scope}
            rates[scope] = (
                100 * rounds[2]["QT_COMPARECIMENTO"] / rounds[2]["QT_APTOS"]
                - 100 * rounds[1]["QT_COMPARECIMENTO"] / rounds[1]["QT_APTOS"]
            )
            residuals[scope] = {
                str(t): r["QT_APTOS"] - r["QT_COMPARECIMENTO"] - r["QT_ABSTENCOES"]
                for t, r in rounds.items()
            }
        checks.append(
            {
                "year": row["year"],
                "deltas_pp": rates,
                "scope_difference_pp": rates["Brasil"] - rates["Brasil e exterior"],
                "unreconciled_electors": residuals,
            }
        )
    options = [
        ("central", "Central · repetir o 1º turno", 0.0),
        (
            "media_3",
            "Média recente · 2014–2022",
            mean(r["delta_turnout_pp"] for r in years[-3:]),
        ),
        (
            "media_todas",
            "Média histórica · 2002–2022",
            mean(r["delta_turnout_pp"] for r in years),
        ),
    ] + [
        (f"ano_{r['year']}", f"Como em {r['year']}", r["delta_turnout_pp"])
        for r in years
    ]
    scenarios = [
        {
            "id": key,
            "name": name,
            "delta_turnout_pp": delta,
            "turnout_pct": baseline + delta,
            "absence_pct": 100 - baseline - delta,
            "attendance": total * (baseline + delta) / 100,
            "absence": total * (100 - baseline - delta) / 100,
            "delta_attendance": total * delta / 100,
        }
        for key, name, delta in options
    ]
    return {
        "reference": "2026-10-09",
        "first_round": {
            "electorate": total,
            "attendance": attending,
            "absence": total - attending,
            "turnout_pct": baseline,
            "absence_pct": 100 - baseline,
            "scope": "Brasil, sem exterior",
            "source": str(OFFICIAL.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "source_snapshot": official["meta"]["versao_nacional_snapshot_id"],
        },
        "central_turnout_pct": baseline,
        "central_delta_pp": 0.0,
        "scenarios": scenarios,
        "history": years,
        "history_sha256": hashlib.sha256(content).hexdigest(),
        "retrospective": comparisons,
        "retrospective_minimum_2": retrospectiva(years, minimum=2),
        "scope_checks": checks,
        "observed_delta_range_pp": [
            min(r["delta_turnout_pp"] for r in years),
            max(r["delta_turnout_pp"] for r in years),
        ],
        "method": "Comparecimento do 1º turno de 2026 nas 27 UFs como ponto de partida. Central sem mudança entre turnos: menor MAE nas três retrospectivas recentes (2014, 2018 e 2022), sempre com três ou mais eleições anteriores. Médias e analogias históricas ficam como alternativas explícitas, sem ajuste das preferências dos ausentes.",
        "limits": "Apenas seis eleições; comparação exploratória, sem teste independente da escolha. Com início em 2010 (duas eleições anteriores), a última variação vence: a seleção não é robusta ao corte. A central é referência conservadora, não prova de abstenção constante. O envelope histórico não é intervalo de confiança nem previsão com cobertura validada. A faixa Monte Carlo de votos segue condicional ao comparecimento escolhido; não incorpora automaticamente estes cenários.",
        "scope_note": source["limits"]
        + " Aptos com comparecimento e ausência ambos zero permanecem como resíduo documental, sem recodificá-los como abstenção; a situação de instalação não está informada em todas as linhas de 2018. Em 2026, as 27 UFs fecham exatamente; o exterior é excluído.",
    }
