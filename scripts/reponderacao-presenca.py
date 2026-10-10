"""Ajuste residual equivalente do 1T, sem identificar voto dos ausentes."""

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICTION = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
OFFICIAL = ROOT / "analysis/apuracao_2026/dados/presidente.json"
CLOSE = datetime.fromisoformat("2026-10-04T17:00:00-03:00")
FORECAST_SHA256 = "b0e9261020a48b16e3103ec8e4f77bc93ee69b5245e1bea82dd9382997d6bacc"
SENSITIVITIES = (
    "Recência sem tendência (central anterior)",
    "Indecisos proporcionais às candidaturas",
    "Somente casas com reponderação PNAD",
    "Publicadas, mesmas casas",
    "Sem seleção de eleitor provável",
)


def comparison(predicted, observed):
    """F/L cancela o denominador; o resíduo inclui erro e decisões de voto."""
    for values in (predicted, observed):
        if (
            any(
                not math.isfinite(values[k]) or values[k] <= 0
                for k in ("flavio", "lula", "validos")
            )
            or values["flavio"] + values["lula"] > values["validos"]
        ):
            raise ValueError("Vetor de votos inválido")
    ratio = (observed["flavio"] / observed["lula"]) / (
        predicted["flavio"] / predicted["lula"]
    )
    shares = {k: 100 * predicted[k] / predicted["validos"] for k in ("flavio", "lula")}
    adjusted_total = predicted["validos"] + predicted["flavio"] * (ratio - 1)
    return {
        "predicted_valid_pct": shares,
        "observed_valid_pct": {
            k: 100 * observed[k] / observed["validos"] for k in ("flavio", "lula")
        },
        "multiplier": ratio,
        "equivalent_extra_pct": 100 * (ratio - 1),
        "flavio_vs_all_others_pct": 100
        * (
            (observed["flavio"] / (observed["validos"] - observed["flavio"]))
            / (shares["flavio"] / (100 - shares["flavio"]))
            - 1
        ),
        "after_multiplier_valid_pct": {
            "flavio": 100 * predicted["flavio"] * ratio / adjusted_total,
            "lula": 100 * predicted["lula"] / adjusted_total,
        },
    }


def domestic_forecast(row):
    counts = {k: row["brasil"][k] for k in ("flavio", "lula", "validos")}
    if row["parametros"]["exterior"]:
        exterior = row["regioes"]["Exterior"]
        counts = {k: v - exterior[k] for k, v in counts.items()}
    return counts


def build(forecast, nexus):
    raw = PREDICTION.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FORECAST_SHA256:
        raise ValueError("A predição difere da versão publicada antes da eleição")
    prediction = json.loads(raw)
    generated = datetime.fromisoformat(prediction["gerado_em"])
    if generated.tzinfo is None or generated >= CLOSE:
        raise ValueError("A predição de referência precisa anteceder a urna")
    official_raw = OFFICIAL.read_bytes()
    official = json.loads(official_raw)
    ufs = [r for r in official["ufs"] if r["uf"] != "ZZ"]
    if len(ufs) != 27 or len({r["uf"] for r in ufs}) != 27:
        raise ValueError("Exige 27 UFs distintas")
    if any(r["secoes"] != r["secoes_total"] for r in ufs):
        raise ValueError("Apuração incompleta")
    observed = {
        **{k: sum(r["votos"][k] for r in ufs) for k in ("flavio", "lula")},
        "validos": sum(r["validos"] for r in ufs),
    }
    central = comparison(domestic_forecast(prediction["central"]), observed)
    first = forecast["ballots"]["1t"]
    if first["reference"] != "2026-10-04":
        raise ValueError("A média precisa usar o corte fechado do primeiro turno")
    mean = first["scenarios"]["central"]

    def mean_comparison(vector):
        return comparison(
            {**{k: vector[k] for k in ("flavio", "lula")}, "validos": 100}, observed
        )

    houses = [
        {
            "id": r["id"],
            "instituto": r["instituto"],
            "campo": r["campo"],
            **mean_comparison(r["modelo"]),
        }
        for r in mean["polls"]
    ]
    alternatives = [
        {
            "name": "Média PNAD + propensões Nexus",
            **mean_comparison(mean["aggregate"]["modelo"]),
        },
        {
            "name": "Média PNAD sem propensões",
            **mean_comparison(mean["aggregate"]["pnad"]),
        },
    ] + [
        {
            "name": name,
            **comparison(
                domestic_forecast(prediction["sensibilidades"][name]), observed
            ),
        }
        for name in SENSITIVITIES
    ]
    keys = list(nexus["poll"]["publicado"]["2t"])
    rates = dict(
        zip(keys, nexus["turnout"]["central"]["2t"]["choice_turnout"], strict=True)
    )
    first_rates = dict(
        zip(
            nexus["poll"]["publicado"]["1t"],
            nexus["turnout"]["central"]["1t"]["choice_turnout"],
            strict=True,
        )
    )
    extra = round(central["equivalent_extra_pct"], 1)
    return {
        "reference": "2026-10-09",
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Brasil, sem exterior, na previsão e na urna",
        "central_extra_pct": extra,
        "central": central,
        "forecast_generated_at": prediction["gerado_em"],
        "forecast_model_hash": prediction["hash_modelo"],
        "forecast_published_commit": "1688f007",
        "observed_votes": observed,
        "predicted_votes": domestic_forecast(prediction["central"]),
        "alternatives": alternatives,
        "houses": houses,
        "house_range_pct": [
            min(r["equivalent_extra_pct"] for r in houses),
            max(r["equivalent_extra_pct"] for r in houses),
        ],
        "nexus_2t_base_ratio": rates["flavio"] / rates["lula"],
        "nexus_1t_base_ratio": first_rates["flavio"] / first_rates["lula"],
        "sources_sha256": {
            str(PREDICTION.relative_to(ROOT)): hashlib.sha256(raw).hexdigest(),
            str(OFFICIAL.relative_to(ROOT)): hashlib.sha256(official_raw).hexdigest(),
            "first_round_mean": hashlib.sha256(
                json.dumps(first, sort_keys=True).encode()
            ).hexdigest(),
        },
        "formula": "100 × [(votos F / votos L na urna) / (votos F / votos L na predição) − 1]",
        "decision": "Referência compartilhada: resíduo equivalente da predição publicada antes da eleição, arredondado a uma casa decimal. O transporte de +3,8% ao 2T é hipótese explícita, não taxa de presença medida ou estimador validado.",
        "limits": "O resíduo mistura comparecimento, erro de pesquisa, voto útil, indecisos e escolhas finais. Não identifica a presença dos que preferiam cada candidato. Ajustar F/L não recompõe todas as candidaturas. Casas e âncoras dão números diferentes; sua faixa não é IC. As pesquisas pós-urna podem já absorver parte do erro anterior, portanto o transporte pode repetir esse ajuste. Zero permanece alternativa. A incerteza deste transporte não entra automaticamente no Monte Carlo.",
        "method_source": "https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/",
    }
