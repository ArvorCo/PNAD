"""Contas derivadas, controles independentes e proveniência dos dois dossiês."""

from __future__ import annotations

import hashlib
import importlib
import json
import math

from . import nexus
from .extract import HASHES, PDFS, ROOT, datafolha, nexus_catalog

OUTPUT = ROOT / "analysis/dossies_2t_2026"
ASSETS = ROOT / "docs/assets"


def read(path):
    return json.loads((ROOT / path).read_text())


def compact_tables(tables):
    rows = []
    for key, table in tables.items():
        metadata = {k: v for k, v in table.items() if k != "segments"}
        head = json.dumps(metadata, ensure_ascii=False)[:-1]
        items = ",\n".join(
            "      "
            + json.dumps(k, ensure_ascii=False)
            + ": "
            + json.dumps(v, ensure_ascii=False)
            for k, v in table["segments"].items()
        )
        rows.append(
            "  "
            + json.dumps(key)
            + ": "
            + head
            + ', "segments": {\n'
            + items
            + "\n    }}"
        )
    return "{\n" + ",\n".join(rows) + "\n}\n"


def controls(tables, house):
    output = {}
    for key, table in tables.items():
        total = table["segments"]["total"]["responses"]
        groups = (
            nexus.PROFILE
            if house == "nexus"
            else {
                "sexo": {
                    n: table["segments"][n]["base_ponderada"]
                    for n in ["homens", "mulheres"]
                },
                "idade": {
                    n: table["segments"][n]["base_ponderada"]
                    for n in ["16–24", "25–34", "35–44", "45–59", "60+"]
                },
                "regiao": {
                    n: table["segments"][n]["base_ponderada"]
                    for n in ["Sudeste", "Sul", "Nordeste", "CO/Norte"]
                },
            }
        )
        output[key] = {}
        for dimension, weights in groups.items():
            recomposed = {}
            for option, published in total.items():
                cells = [
                    table["segments"][name]["responses"][option] for name in weights
                ]
                if published is None or any(v is None for v in cells):
                    continue
                result = sum(
                    table["segments"][name]["responses"][option] * w
                    for name, w in weights.items()
                ) / sum(weights.values())
                recomposed[option] = {
                    "publicado": published,
                    "recomposto": result,
                    "residuo_pp": result - published,
                }
            residual = max(
                (abs(v["residuo_pp"]) for v in recomposed.values()), default=0
            )
            if residual > 1.5:
                raise ValueError(
                    f"Recomposição divergente: {house}/{key}/{dimension}: {residual}"
                )
            output[key][dimension] = {
                "weights": weights,
                "values": recomposed,
                "max_residual_pp": residual,
            }
    return output


def reweight(ident):
    engine = importlib.import_module("reponderacao-pnad")
    source = read(f"analysis/reponderacao/pesquisas/{ident}.json")
    result = engine.process_poll(source, engine.Benchmark(), engine.load_ipca())
    return {
        "id": ident,
        "profile": result["renda"],
        "turn": result["turnos"]["2t"],
        "source": source["fonte"],
    }


def source(house):
    manifest = read(
        f"data/originals/{'datafolha' if house == 'datafolha' else 'nexus'}_102026_13/fonte.json"
    )
    registry = (
        ROOT
        / f"docs/fontes/{'datafolha_08102026' if house == 'datafolha' else 'nexus_btg_13102026'}_registro.txt"
    )
    return {
        "pdf": str(PDFS[house].relative_to(ROOT)),
        "sha256": HASHES[house],
        "registry_transcript": str(registry.relative_to(ROOT)),
        "registry_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "consulted": "2026-10-13",
        "manifest": manifest,
        "registry_status": "Transcrição dos campos visíveis, não exportação original do TSE.",
        "weighting_first_round": "Não declarada no registro e no relatório consultados; uso interno não identificado.",
    }


def build():
    df, nx = datafolha(), nexus.tables()
    df_vote = df["voto"]["segments"]["total"]["responses"]
    table = df["decisao"]["segments"]["total"]
    mot = df["motivacao"]["segments"]["total"]
    pool = 100 * table["base_ponderada"] / 2520
    undecided_exact = 100 - pool
    data = {
        "date": "2026-10-13",
        "datafolha": {
            "slug": "datafolha_08102026",
            "field": "06–07/10/2026",
            "release": "08/10/2026",
            "n": 2520,
            "source": source("datafolha"),
            "tables": df,
            "controls": controls(df, "datafolha"),
            "reweight": reweight("datafolha_2026-10-08"),
            "reported_valid": {"flavio": 52, "lula": 48},
            "transfer": {
                "page": 5,
                "flavio": 46,
                "lula": 32,
                "invalid": 15,
                "unreported_residual": 7,
                "certain": 77,
                "could_change": 22,
                "universe": "quem declara voto em Cury, Renan, Caiado ou Zema no 1º turno; tamanho da base não publicado",
            },
            "motivation_candidates": {
                "page": 11,
                "flavio": [69, 25, 4, 2],
                "lula": [83, 13, 3, 1],
            },
            "denominators": {
                "decision_base": table["base_ponderada"],
                "candidate_base": mot["base_ponderada"],
                "certain_all_pct": table["responses"][
                    "Está totalmente decidido a votar"
                ]
                * pool
                / 100,
                "open_all_pct": table["responses"]["Seu voto ainda pode mudar"]
                * pool
                / 100
                + undecided_exact,
                "motivation_positive_all_pct": mot["responses"][
                    "É, na sua opinião, o melhor candidato a presidente"
                ]
                * mot["base_ponderada"]
                / 2520,
                "motivation_negative_all_pct": mot["responses"][
                    "Porque você quer derrotar o ____"
                ]
                * mot["base_ponderada"]
                / 2520,
            },
            "income_history": {
                "prior_id": "datafolha_2026-10-01",
                "prior": reweight("datafolha_2026-10-01")["profile"],
                "prior_bases": [1209, 856, 344],
                "prior_n": 2523,
                "current_bases": [1187, 874, 337],
                "current_n": 2520,
                "declared_target": [49, 47, 4],
                "declared_income_factor": 1,
                "source_old_registry": "docs/fontes/datafolha_21092026_registro.txt",
            },
            "editorial_checks": [
                "A apresentação traz bases 2.489/2.378 nas pp. 10/11, enquanto o anexo declara bases ponderadas 2.488/2.366 nas pp. 31/32; a natureza das primeiras não está explicitada. Não tratá-las como composição política da amostra.",
                "Texto da p. 5 informa decisão 96%/97% entre eleitores dos candidatos, enquanto o gráfico da p. 10 exibe 94%/94%. Sem identificação inequívoca da mesma base, conservar as versões e não fundir os valores.",
                "A p. 7 tem título de espontânea e subtítulo de estimulada. O anexo da p. 25 identifica intenção espontânea; a p. 26 identifica a estimulada com nomes. A tabela usada e sua página são explicitadas.",
                "A p. 6 generaliza a motivação 76%/19% para brasileiros; a p. 32 restringe a base aos eleitores que escolheram uma candidatura. Reexpressão no total é conta derivada, não topline publicado.",
            ],
        },
        "nexus": {
            "slug": "nexus_btg_13102026",
            "field": "10–12/10/2026",
            "release": "13/10/2026",
            "n": 2002,
            "source": source("nexus"),
            "tables": nx,
            "controls": controls(nx, "nexus"),
            "profile": nexus.PROFILE,
            "profile_page": 99,
            "special": nexus.special(),
            "catalog": nexus_catalog(),
            "reported_valid": {"flavio": 52, "lula": 48},
            "reweight": reweight("nexus_2026-10-12"),
            "income_history": {
                "prior_id": "nexus_2026-09-27",
                "prior": reweight("nexus_2026-09-27")["profile"],
                "source_old_registry": "docs/fontes/nexus_btg_28092026/registro-metodologia.txt",
            },
        },
    }
    for house, payload in data.items():
        if house not in ("datafolha", "nexus"):
            continue
        vote = payload["reweight"]["turn"]["publicado"]
        f, lula = vote["flavio"] / 100, vote["lula"] / 100
        payload["difference_margin_aas"] = (
            1.959963984540054
            * math.sqrt((f + lula - (f - lula) ** 2) / payload["n"])
            * 100
        )
        payload["calculated_valid"] = {
            "flavio": 100 * f / (f + lula),
            "lula": 100 * lula / (f + lula),
        }
    assert df_vote["Flavio Bolsonaro (PL)"] == 49
    return data


def write():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = build()
    for house in ("datafolha", "nexus"):
        record = data[house]
        (OUTPUT / f"{house}_tabelas.json").write_text(compact_tables(record["tables"]))
        # O dado completo usa uma linha por pergunta para manter o arquivo compacto.
        body = {k: v for k, v in record.items() if k not in ("tables", "catalog")}
        body["tables"] = record["tables"]
        if "catalog" in record:
            body["catalog"] = record["catalog"]
        path = ASSETS / (record["slug"] + "_data.json")
        path.write_text(
            "{\n"
            + ",\n".join(
                "  " + json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False)
                for k, v in body.items()
            )
            + "\n}\n"
        )
    (OUTPUT / "nexus_perguntas.json").write_text(
        json.dumps(data["nexus"]["catalog"], ensure_ascii=False, indent=2) + "\n"
    )
    return data
