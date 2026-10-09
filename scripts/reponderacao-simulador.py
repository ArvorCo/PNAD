"""Simulador nacional do 2º turno: massas conservadas e hipóteses explícitas.

Espelho do motor em docs/assets/reponderacao_simulador_motor.js. Os percentuais
válidos são normalizados por pesquisa antes da média de peso igual por casa.
"""

import hashlib
import importlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = importlib.import_module("reponderacao-validos")
COUNT = importlib.import_module("reponderacao-contagem")
KEYS = ("flavio", "lula", "indecisos", "branco_nulo")
LIMITS = {
    "presenca_relativa": (-30, 30),
    "comparecimento": (40, 95),
    "branco_nulo_pp": (-10, 20),
    "nulo_diferencial_pp": (-20, 20),
    "indecisos_validos": (0, 100),
    "indecisos_flavio": (0, 100),
    "vies_pp": (-10, 10),
}


def parameters(data, params=None):
    p = {**data["defaults"], **(params or {})}
    if p["modo"] not in ("publicado", "pnad", "modelo"):
        raise ValueError("Modo inválido")
    if p["idade"] not in data["rates"]:
        raise ValueError("Cenário de idade inválido")
    for key, (low, high) in LIMITS.items():
        if key == "indecisos_flavio" and p[key] is None:
            continue
        if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]):
            raise ValueError("Parâmetro inválido: " + key)
        if not low <= p[key] <= high:
            raise ValueError("Parâmetro fora dos limites: " + key)
    return p


def calibrate(masses, rates, target):
    """Escala comum com teto físico de 100%, preservando a presença relativa."""
    low, high = 0.0, 64.0
    for _ in range(64):
        middle = (low + high) / 2
        attendance = sum(masses[k] * min(1, middle * rates[k]) for k in KEYS)
        if attendance < target:
            low = middle
        else:
            high = middle
    return {k: min(1, (low + high) / 2 * rates[k]) for k in KEYS}


def poll_result(row, data, p):
    masses = row["published" if p["modo"] == "publicado" else "pnad"]
    rates = (
        dict(data["rates"][p["idade"]])
        if p["modo"] == "modelo"
        else dict.fromkeys(KEYS, 1.0)
    )
    rates["flavio"] *= 1 + p["presenca_relativa"] / 100
    rates = calibrate(masses, rates, p["comparecimento"])
    attending = {k: masses[k] * rates[k] for k in KEYS}
    f, lula_mass, u, b = (attending[k] for k in KEYS)
    uf = (
        f / (f + lula_mass)
        if p["indecisos_flavio"] is None
        else p["indecisos_flavio"] / 100
    )
    valid_u = u * p["indecisos_validos"] / 100
    f += valid_u * uf
    lula_mass += valid_u * (1 - uf)
    b += u - valid_u
    # A mudança comum de branco/nulo transfere massa, em proporção aos válidos.
    shift = max(
        -b, min(f + lula_mass - 1e-9, p["comparecimento"] * p["branco_nulo_pp"] / 100)
    )
    share = f / (f + lula_mass)
    f -= shift * share
    lula_mass -= shift * (1 - share)
    b += shift
    # Saída extra de um eleitorado para branco/nulo, sem tocar o comparecimento.
    nf = f * max(0, p["nulo_diferencial_pp"]) / 100
    nl = lula_mass * max(0, -p["nulo_diferencial_pp"]) / 100
    f -= nf
    lula_mass -= nl
    b += nf + nl
    valid = f + lula_mass
    share = min(1, max(0, f / valid + p["vies_pp"] / 200))
    return {
        "id": row["id"],
        "instituto": row["instituto"],
        "divulgacao": row["divulgacao"],
        "flavio": 100 * share,
        "lula": 100 * (1 - share),
        "validos": valid,
        "branco_nulo": b,
        "comparecimento": p["comparecimento"],
        "abstencao": 100 - p["comparecimento"],
        "taxas": rates,
    }


def evaluate(data, params=None):
    p = parameters(data, params)
    polls = [poll_result(row, data, p) for row in data["polls"]]
    if not polls:
        raise ValueError("Nenhuma pesquisa elegível no 2º turno")
    out = {
        k: sum(row[k] for row in polls) / len(polls)
        for k in (
            "flavio",
            "lula",
            "validos",
            "branco_nulo",
            "comparecimento",
            "abstencao",
        )
    }
    out["diferenca_flavio_lula"] = out["flavio"] - out["lula"]
    out["por_100_eleitores"] = {
        "flavio": out["validos"] * out["flavio"] / 100,
        "lula": out["validos"] * out["lula"] / 100,
        "branco_nulo": out["branco_nulo"],
        "abstencao": out["abstencao"],
    }
    out["taxas"] = {k: sum(row["taxas"][k] for row in polls) / len(polls) for k in KEYS}
    out["polls"] = polls
    out["parametros"] = p
    return out


def preferences(values, fallback):
    """NS/NR e nenhum agregados; dados ausentes conservam o publicado explicitamente."""
    f, lula_mass = max(0, values["flavio"]), max(0, values["lula"])
    u_keys = ("indecisos", "nao_sabe", "ns_nr")
    b_keys = ("branco_nulo", "nenhum", "nao_vai_votar")
    u_source = values if any(k in values for k in u_keys) else fallback
    b_source = values if any(k in values for k in b_keys) else fallback
    u = sum(max(0, u_source.get(k, 0)) for k in u_keys)
    b = sum(max(0, b_source.get(k, 0)) for k in b_keys)
    total = f + lula_mass + u + b
    return dict(zip(KEYS, [100 * x / total for x in (f, lula_mass, u, b)], strict=True))


def build(data, forecast, nexus):
    block = forecast["ballots"]["2t"]
    eligible = block["scenarios"]["central"]["polls"]
    raw = {p["id"]: p for p in data["pesquisas"]}
    rows = []
    for row in eligible:
        poll = raw[row["id"]]
        t = poll["turnos"]["2t"]
        adj = t["cenarios"][MODEL.SCENARIO]["ajustado"]
        pub = {**poll["publicado"]["2t"], **t["publicado"]}
        rows.append(
            {
                "id": row["id"],
                "instituto": row["instituto"],
                "campo": row["campo"],
                "divulgacao": row["divulgacao"],
                "published": preferences(pub, pub),
                "pnad": preferences(adj, pub),
                "nonchoice_fallback": [
                    k for k in ("indecisos", "branco_nulo") if k not in adj and k in pub
                ],
                "perfil_tipo": poll["renda"].get("perfil_tipo", "amostra"),
            }
        )
    out = {
        "schema": 1,
        "reference": data["referencia"],
        "electorate": COUNT.electorate(),
        "polls": rows,
        "engine": hashlib.sha256(
            (ROOT / "docs/assets/reponderacao_simulador_motor.js").read_bytes()
        ).hexdigest()[:16],
        "excluded": block["excluded"],
        "defaults": {
            "modo": "modelo",
            "idade": "central",
            "presenca_relativa": 5.0,
            "comparecimento": nexus["turnout"]["central"]["2t"]["target_turnout"],
            "branco_nulo_pp": 0.0,
            "nulo_diferencial_pp": 0.0,
            "indecisos_validos": 100.0,
            "indecisos_flavio": None,
            "vies_pp": 0.0,
        },
        "rates": {
            s: MODEL.template(nexus, "2t", s)
            for s in ("central", "idosos60", "idosos80")
        },
        "limits": LIMITS,
        "method": {
            "selection": "Última onda por casa, divulgada na janela de sete dias; no pós-1º turno, apenas campo iniciado depois de 04/10.",
            "central": "PNAD + propensão Nexus + presença relativa de Flávio +5%, escolha declarada após o 1º turno, não parâmetro aprendido.",
            "attendance": "Comparecimento nacional ancorado no cenário histórico Nexus; escala comum preserva a razão das taxas enquanto nenhuma atinge o teto de 100%.",
            "undecided": "Proporcionais aos candidatos que comparecem; dados de não escolha sem renda conservam o publicado, com indicação na ficha.",
            "aggregation": "Normalizar válidos dentro de cada pesquisa, depois média de peso igual; a contabilidade por 100 eleitores usa a massa válida média e esse mesmo placar.",
            "limits": "Sensibilidade condicional, sem probabilidade de vitória ou intervalo preditivo validado. Nenhum voto ou preferência territorial é imputado.",
        },
    }
    out["central"] = evaluate(out)
    out["version"] = hashlib.sha256(
        json.dumps(out, sort_keys=True).encode()
    ).hexdigest()[:16]
    return out


def write(data, forecast):
    nexus = json.loads((ROOT / "docs/assets/nexus_btg_28092026_data.json").read_text())
    result = build(data, forecast, nexus)
    folder = ROOT / "docs/assets/reponderacao_cenarios"
    folder.mkdir(exist_ok=True)
    engine = ROOT / "docs/assets/reponderacao_simulador_motor.js"
    frozen_engine = folder / f"motor-{result['engine']}.js"
    if frozen_engine.exists() and frozen_engine.read_bytes() != engine.read_bytes():
        raise ValueError("Motor arquivado com conteúdo diferente")
    frozen_engine.write_bytes(engine.read_bytes())
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    snapshot = folder / f"{result['version']}.json"
    if snapshot.exists() and snapshot.read_text() != encoded:
        raise ValueError("Snapshot de cenário já existe com conteúdo diferente")
    snapshot.write_text(encoded)
    (ROOT / "docs/assets/reponderacao_simulador.json").write_text(encoded)
    return result
