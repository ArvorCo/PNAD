#!/usr/bin/env python3
"""Audit the complete 21 September Datafolha release and state comparison."""

import csv
import hashlib
import importlib.util
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
FOLDER = ROOT / "data/pesquisas/datafolha/2026-09-17"
SLUG = "datafolha_21092026"
BANDS = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
CEN = "pessoas16_efetivo"


def module(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / f"scripts/{name}.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


old = module("datafolha-14092026-audit")
flat = old.flat


def poll_record(tables):
    p = json.loads(
        (ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-09-10.json").read_text()
    )
    p.update(
        id="datafolha_2026-09-17",
        registro_tse="BR-04029/2026",
        campo={"inicio": "2026-09-15", "fim": "2026-09-17"},
        divulgacao="2026-09-17",
        n=2001,
        dossie=f"{SLUG}.html",
    )
    p["fonte"] = {
        "pdf": str((FOLDER / "relatorio.pdf").relative_to(ROOT)),
        "url": f"https://brasil.arvor.co/fontes/{SLUG}.pdf",
        "relatorio_completo": "2026-09-21",
        "paginas": {"perfil_renda": 30, "1t_renda": 35, "2t_renda": 42},
        "nota": "Relatório completo de 50 páginas publicado em 21/09; resultados divulgados em 17/09. O registro prevê 2.002 entrevistas; o relatório e o anexo territorial somam 2.001.",
    }
    p["renda"]["bases"] = [992, 655, 266]
    p["renda"][
        "nota"
    ] = "Bases ponderadas da intenção de voto, pp. 35 e 42. Somam 1.913; 88 casos não aparecem no cruzamento de renda. Normalização entre renda declarada e delta ancorado no placar nacional; não identifica o voto dos casos sem renda publicada."
    names = [
        "lula",
        "flavio",
        "cury",
        "caiado",
        "renan_santos",
        "zema",
        "samara",
        "rui",
        "edmilson",
        "clariana",
        "hertz",
        "grassi",
        "branco_nulo",
        "indecisos",
    ]
    for t, key, options in [
        ("1t", "estimulada_b", names),
        ("2t", "turno2_flavio", ["lula", "flavio", "branco_nulo", "indecisos"]),
    ]:
        rows, _ = flat(tables[key])
        labels = list(rows)
        expected = (
            [
                "Lula",
                "Flavio",
                "Cury",
                "Caiado",
                "Renan",
                "Zema",
                "Samara",
                "Rui",
                "Edmilson",
                "Clariana",
                "Dias",
                "Grassi",
                "Em branco",
                "Indecisos",
            ]
            if t == "1t"
            else ["Lula", "Flavio", "Em branco", "Indecisos"]
        )
        assert all(
            e in label for e, label in zip(expected, labels, strict=True)
        ), labels
        p["publicado"][t] = dict(
            zip(options, [r["Total"] for r in rows.values()], strict=True)
        )
        p["cruzamentos"][t] = {
            "opcoes": options,
            "linhas": [[r[c] for r in rows.values()] for c in BANDS],
            "nota": f"Extração automática, {key}. Traço convertido em zero apenas na conta. Inteiros mantidos sem normalização; cenário B no primeiro turno.",
        }
    return p


def territory():
    out = []
    with fitz.open(FOLDER / "bairros.pdf") as pdf:
        for page in pdf:
            tok = [s.strip() for s in page.get_text().splitlines() if s.strip()]
            for i, s in enumerate(tok):
                if re.fullmatch(r"\d{15}", s):
                    j = i - 1
                    while j >= 0 and not (
                        tok[j] in {"CO", "N", "NE", "S", "SE"}
                        and re.fullmatch(r"[A-Z]{2}", tok[j + 1])
                        and tok[j + 2] not in {"CO", "N", "NE", "S", "SE"}
                    ):
                        j -= 1
                    assert j >= 0 and tok[i + 1].isdigit()
                    out.append(
                        {
                            "pagina": page.number + 1,
                            "regiao": tok[j],
                            "uf": tok[j + 1],
                            "municipio": tok[j + 2],
                            "setor": s,
                            "entrevistas": int(tok[i + 1]),
                        }
                    )
    uf = Counter()
    regions = Counter()
    for r in out:
        uf[r["uf"]] += r["entrevistas"]
        regions[r["regiao"]] += r["entrevistas"]
    assert sum(uf.values()) == 2001
    assert regions == {"CO": 154, "N": 168, "NE": 545, "S": 294, "SE": 840}, regions
    assert all(re.fullmatch(r"[A-Z]{2}", k) for k in uf)
    return {
        "rows": out,
        "uf": dict(uf),
        "regions": dict(regions),
        "n": sum(uf.values()),
        "municipalities": len({r["setor"][:7] for r in out}),
        "sectors": len({r["setor"] for r in out}),
        "date_discrepancy": "O rodapé territorial informa 14–16/09; registro e relatório informam 15–17/09. Divergência documental, sem conclusão sobre a data efetiva.",
    }


def geography(tables, terr):
    extract = module("datafolha-21092026-extract")
    states = []
    statepdf = ROOT / "data/pesquisas/datafolha/2026-09-10-estaduais/relatorio.pdf"
    with fitz.open(statepdf) as pdf:
        for uf, page, n, moe, reg in [
            ("SP", 58, 1610, 2, "BR-03904/2026"),
            ("RJ", 76, 1204, 3, "BR-06361/2026"),
            ("MG", 94, 1204, 3, "BR-03022/2026"),
        ]:
            parts = re.split(r"Bloco ([123]) de 3,[^\n]*\n", pdf[page - 1].get_text())
            block = extract.block(parts[2], 1, page)
            rows = block["rows"]
            base = block["base"]["Total"]
            assert base == n
            states.append(
                {
                    "uf": uf,
                    "page": page,
                    "n": n,
                    "moe": moe,
                    "registry": reg,
                    "lula": rows["Lula (PT)"]["Total"],
                    "flavio": rows["Flavio Bolsonaro (PL)"]["Total"],
                    "blank": rows["Em branco/nulo/nenhum"]["Total"],
                    "unknown": rows["Não sabe"]["Total"],
                }
            )
    with (ROOT / "data/outputs/tse_eleitorado_perfil_summary.csv").open() as f:
        voters = {
            r["category"]: int(r["qt_eleitores"])
            for r in csv.DictReader(f)
            if r["dimension"] == "uf" and r["category"] in ["SP", "RJ", "MG", "ES"]
        }
    assert len(voters) == 4, voters
    total = sum(voters.values())
    weights = {k: v / total for k, v in voters.items()}
    known = {
        k: sum(weights[s["uf"]] * s[k] for s in states)
        for k in ["lula", "flavio", "blank", "unknown"]
    }
    for s in states:
        s["voters"] = voters[s["uf"]]
        s["southeast_weight"] = weights[s["uf"]]
        s["national_field_n"] = terr["uf"][s["uf"]]
    oldtab = json.loads((ASSETS / "datafolha_14092026_cruzamentos.json").read_text())[
        "tabelas"
    ]["turno2_flavio"]
    comparisons = []
    for date, tab in [("08–10/09", oldtab), ("15–17/09", tables["turno2_flavio"])]:
        rows, bases = flat(tab)
        values = dict(
            zip(
                ["lula", "flavio", "blank", "unknown"],
                [r["Sudeste"] for r in rows.values()],
                strict=True,
            )
        )
        implied = {k: (v - known[k]) / weights["ES"] for k, v in values.items()}
        # Separate candidate feasibility from four rounded toplines summing to 101.
        comparisons.append(
            {
                "field": date,
                "regional": values,
                "base": bases["Sudeste"],
                "implied_es_candidates": {k: implied[k] for k in ["lula", "flavio"]},
                "feasible_candidates": implied["lula"] >= 0
                and implied["flavio"] >= 0
                and implied["lula"] + implied["flavio"] <= 100,
            }
        )
    con = sqlite3.connect(ROOT / "data/outputs/tse_eleitorado_perfil.sqlite")
    meta = dict(con.execute("SELECT * FROM metadata"))
    con.close()
    return {
        "states": states,
        "field": "08–10/09/2026",
        "weights": weights,
        "voters": voters,
        "tse_metadata": meta,
        "known_contribution": known,
        "known_conditional": {k: v / (1 - weights["ES"]) for k, v in known.items()},
        "es_status": "Não localizado no relatório estadual nem na busca no acervo público do Datafolha até 21/09/2026; não equivale a prova de inexistência.",
        "es_search": {
            "date": "2026-09-21",
            "index": "https://datafolha.folha.uol.com.br/eleicoes/",
            "queries": [
                'site:datafolha.folha.uol.com.br "Espírito Santo" "2026" "setembro"',
                'site:datafolha.folha.uol.com.br "Lula" "Espírito Santo" "2026"',
            ],
        },
        "comparisons": comparisons,
        "bounds": {
            k: [known[k], known[k] + 100 * weights["ES"]] for k in ["lula", "flavio"]
        },
        "gap_bounds": [
            known["lula"] - known["flavio"] - 100 * weights["ES"],
            known["lula"] - known["flavio"] + 100 * weights["ES"],
        ],
    }


def transfer(poll):
    a, b = poll["publicado"]["1t"], poll["publicado"]["2t"]
    keys = ["lula", "flavio", "cury", "caiado", "renan_santos", "zema", "samara"]
    raw = [a[k] for k in keys] + [
        sum(a[k] for k in ["rui", "edmilson", "clariana", "hertz", "grassi"]),
        a["branco_nulo"],
        a["indecisos"],
    ]
    cols = np.array([b["lula"], b["flavio"], b["branco_nulo"] + b["indecisos"]], float)
    mass = np.array(raw) * cols.sum() / sum(raw)
    fixed = np.array(
        [
            [mass[0], 0, 0],
            [0, mass[1], 0],
            mass[2] * np.array([0.32, 0.44, 0.24]),
            mass[3] * np.array([0.27, 0.42, 0.31]),
        ]
    )
    prior = [
        [0.03, 0.68, 0.29],
        [0.02, 0.8, 0.18],
        [0.85, 0.01, 0.14],
        [0.8, 0.01, 0.19],
        [0.15, 0.25, 0.6],
        [0.4, 0.4, 0.2],
    ]
    matrix = np.vstack([fixed, old.ras(prior, mass[4:], cols - fixed.sum(axis=0))])
    assert np.allclose(matrix.sum(axis=0), cols) and np.allclose(
        matrix.sum(axis=1), mass
    )
    gains = cols[:2] - mass[:2]
    return {
        "sources": [
            "Lula",
            "Flávio",
            "Cury",
            "Caiado",
            "Renan",
            "Zema",
            "Samara",
            "Outros",
            "Branco/nulo",
            "Indecisos",
        ],
        "destinations": ["Lula", "Flávio", "Não escolha"],
        "matrix": matrix.tolist(),
        "row_targets": mass.tolist(),
        "column_targets": cols.tolist(),
        "measured_rows": [2, 3],
        "consolidated_rows": [0, 1],
        "estimated_rows": [4, 5, 6, 7, 8, 9],
        "measured_page": 7,
        "measured_percentages": {"Cury": [32, 44, 24], "Caiado": [27, 42, 31]},
        "gains": gains.tolist(),
        "ratio_flavio_lula": float(gains[1] / gains[0]),
        "normalization": {
            "origin_sum": sum(raw),
            "target_sum": float(cols.sum()),
            "factor": float(cols.sum() / sum(raw)),
        },
    }


def main():
    tables = json.loads((ASSETS / f"{SLUG}_cruzamentos.json").read_text())["tabelas"]
    poll = poll_record(tables)
    engine = module("reponderacao-pnad")
    bench = engine.Benchmark()
    ipca = engine.load_ipca()
    dump(ROOT / f"analysis/reponderacao/pesquisas/{poll['id']}.json", poll)
    reweight = engine.process_poll(poll, bench, ipca)
    rows, bases = flat(tables["turno2_flavio"])
    dims = {
        "sexo": ["Masculino", "Feminino"],
        "idade": ["16-24", "25-34", "35-44", "45-59", "60+"],
        "escolaridade": ["Fundamental", "Medio", "Superior"],
        "renda": BANDS,
        "ocupacao": ["PEA", "Nao PEA"],
        "cor": ["Branca", "Preta", "Parda"],
        "religiao": ["Catolica", "Evangelica"],
        "regiao": ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"],
        "natureza": ["Regiao metropolitana", "Interior"],
        "partido": ["PT", "PL", "Outro partido", "Nao tem"],
    }
    coverage = [
        {
            "dimension": k,
            "base": sum(bases[c] for c in v),
            "missing": 2001 - sum(bases[c] for c in v),
        }
        for k, v in dims.items()
    ]
    proofs = []
    for key in ["estimulada_b", "turno2_flavio"]:
        rr, bb = flat(tables[key])
        for dim in ["sexo", "regiao"]:
            for name in ["Lula (PT)", "Flavio Bolsonaro (PL)"]:
                val = sum(rr[name][c] * bb[c] for c in dims[dim]) / sum(
                    bb[c] for c in dims[dim]
                )
                assert abs(val - rr[name]["Total"]) < 1
                proofs.append(
                    {
                        "table": key,
                        "dimension": dim,
                        "candidate": name,
                        "recomposed": val,
                        "published": rr[name]["Total"],
                    }
                )
    history = []
    for path in sorted(
        (ROOT / "analysis/reponderacao/pesquisas").glob("datafolha_*.json")
    ):
        p = json.loads(path.read_text())
        r = engine.process_poll(p, bench, ipca)
        history.append({"id": p["id"], "field": p["campo"], "turnos": r["turnos"]})
    alternatives = []
    for key in [
        "turno2_flavio",
        "turno2_caiado",
        "turno2_zema",
        "turno2_renan",
        "turno2_cury",
    ]:
        rr, _ = flat(tables[key])
        names = list(rr)
        alternatives.append(
            {
                "name": names[1],
                "lula": rr[names[0]]["Total"],
                "opponent": rr[names[1]]["Total"],
                "nonchoice": sum(rr[k]["Total"] for k in names[2:]),
                "page": tables[key]["blocks"]["bloco1"]["pdf_page"],
            }
        )
    terr = territory()
    geo = geography(tables, terr)
    identification = module("datafolha-21092026-identificacao").audit(rows, bases)
    dump(ASSETS / f"{SLUG}_identificacao.json", identification)
    provenance = {}
    for name, suffix in [
        ("relatorio.pdf", ".pdf"),
        ("registro.txt", "_registro.txt"),
        ("questionario.pdf", "_questionario.pdf"),
        ("bairros.pdf", "_bairros.pdf"),
    ]:
        payload = (FOLDER / name).read_bytes()
        (ROOT / "docs/fontes" / f"{SLUG}{suffix}").write_bytes(payload)
        provenance[name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    payload = (
        ROOT / "data/pesquisas/datafolha/2026-09-10-estaduais/relatorio.pdf"
    ).read_bytes()
    (ROOT / "docs/fontes" / f"{SLUG}_estaduais.pdf").write_bytes(payload)
    provenance["estaduais.pdf"] = {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    provenance["official_report_url"] = (
        "https://media.folha.uol.com.br/datafolha/2026/09/21/o-v6ubgsdepw9o9eavou7i7zs8omcuwywo2bwf3ufws.pdf"
    )
    provenance["official_states_url"] = (
        "https://media.folha.uol.com.br/datafolha/2026/09/14/rznlwqnkqpsigdu5ebkhvayhjahixydaxkm48dylkto.pdf"
    )
    missing = {
        t: {
            k: v
            + 1913 / 2001 * (reweight["turnos"][t]["cenarios"][CEN]["ajustado"][k] - v)
            for k, v in poll["publicado"][t].items()
        }
        for t in ["1t", "2t"]
    }
    data = {
        "poll": poll,
        "reweight": reweight,
        "proofs": proofs,
        "coverage": coverage,
        "history": history,
        "alternatives": alternatives,
        "transfer": transfer(poll),
        "territory": terr,
        "geography": geo,
        "identification_summary": {
            k: v
            for k, v in identification.items()
            if k not in ["cell_indices", "certificates", "common_projections"]
        },
        "identification_range": [
            c["national_pct"] for c in identification["certificates"]
        ],
        "missing_share_preserved": missing,
        "provenance": provenance,
    }
    dump(ASSETS / f"{SLUG}_data.json", data)
    print(
        json.dumps(
            {
                "reweighted": {
                    t: r["cenarios"][CEN]["ajustado"]
                    for t, r in reweight["turnos"].items()
                },
                "states": geo["known_conditional"],
                "comparison": geo["comparisons"],
                "identification_range": data["identification_range"],
                "territory": {k: v for k, v in terr.items() if k != "rows"},
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
